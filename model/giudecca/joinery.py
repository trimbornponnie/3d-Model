"""Joinery (docs/INTERIORS.md section 3; SE 51, 53, 56, 65, n3, photo n24):
frames, leaves, glass, handles, interior window boards, reveal plaster,
thresholds, lintels and radiator niches for every window and door registered
in geo.OPENINGS while the exterior was cut. With geo.THROUGH set those
openings go right through the walls and carry no glass of their own.

Geometry is built in each opening's face frame: u along the face (world y
for an x-facing wall, world x for a y-facing one), z up, and d = depth behind
the outer face (into the wall). Each record gets an opening TYPE (classify();
a part module may set rec['type'] itself), whose spec in TYPES gives the jamb
(stop = Italian "mazzetta": the frame sits behind a 0.26 brick reveal in a
pocket 0.07 wider each side; plain = straight reveal), the frame position and
the leaves.

Per body, the part modules
  - add pockets(rec) to the hollowing cutter (frame rebates, lintels, inner
    sill blocks, radiator niches: the brick they replace),
  - cut the wall linings with lining_cutter(recs),
  - call build_openings(kit, recs) for the joinery itself.
Mirrored copies (the west towers) mirror the joinery objects with the rest.
"""
from __future__ import annotations

from typing import Sequence

import bmesh

from . import geo
from .interior import Kit, ccw, clean, offset
from .params import FLOORS

WALL = 0.395                 # face-brick masonry at the openings (SE 50, 53)
LIN = 0.055                  # insulated lining -> finished face at d = 0.45
STOP = 0.26                  # brick reveal depth in front of the frame (stop jambs)
MAZ = 0.07                   # pocket widening per side behind the stop ("7", SE 53)
FINISH = WALL + LIN

# ------------------------------------------------------------------ types
BASE = dict(
    jamb='stop',              # 'stop' (mazzetta) | 'plain'
    frame=(0.060, 0.065),     # outer frame ("telaio"): face width "6" (SE 51), depth
    sash=(0.055, 0.056),      # leaf stiles / top rail: face, depth
    bottom_rail=0.070,        # leaf bottom rail (windows)
    leaves=2,                 # side-hung casements across the width
    glass=0.018,              # double glazing 4/10/4 ("termopane", SE 51)
    door=False,               # French window / door: threshold instead of a sill board
    board=True,               # interior window board (cream timber, n24)
    niche=False,              # radiator niche under the sill (finestre tipo only, SE 53)
    lintel=True,              # RC L-lintel over the opening (SE 53, SE 54 det. 3)
    handle=True,
    frame_mat='M_Joinery', leaf_mat='M_Joinery', glass_mat='M_Glass',
)

TYPES: dict[str, dict] = {
    # finestre tipo 1.04 x 1.41, sill z_f+0.94: two casements, niche under the sill (SE 53 E)
    'E': dict(niche=True),
    # single-leaf windows of the same family: two-light lights 0.91-0.995, tower pairs 0.93 / 0.92
    'E1': dict(leaves=1),
    # finestre schiera e torri 0.91 x 0.92, sill z_f+1.43: plain jamb, frame in the lining plane (SE 53 F)
    'F': dict(jamb='plain', leaves=1, lintel=True, board=False),
    # porte-finestre 1.04 / 1.14 (C), 0.775-0.91 (D): full-height leaves, RC threshold 0.45 deep (SE 53 C/D)
    'C': dict(door=True, bottom_rail=0.150, board=False),
    'D': dict(door=True, leaves=1, bottom_rail=0.150, board=False),
    # trifora: fixed side lights, two casements in the centre, frame in the lining plane (SE 51)
    'T': dict(jamb='plain', door=False, lintel=False, niche=False),
    # stair window 60 x 60: metal frame flush with the outer face, one sash (n3)
    'K': dict(jamb='plain', leaves=1, frame=(0.040, 0.050), sash=(0.035, 0.040), bottom_rail=0.035,
              glass=0.014, board=False, lintel=False, handle=False,          # sealed unit ~4/6/4 (n3)
              frame_mat='M_Steel', leaf_mat='M_Steel', frame_at=0.0),
    # dwelling entrance door ("portoncino", SE 65): 4 raised panels, frame behind the jamb
    'P': dict(jamb='plain', door=True, leaves=1, panel_leaf=True, board=False, lintel=True,
              frame_at=STOP),
    # tower street door 1.25 x 2.33: door 0.92 x 2.04 with fixed glass above and beside (n7)
    'PT': dict(jamb='plain', door=True, leaves=1, panel_leaf=True, board=False, lintel=False,
               frame_at=0.30, street=True),
    # cellar door / window (SE 56, SE 65): flush leaf, wired glass, grey
    'CD': dict(jamb='plain', door=True, leaves=1, flush_leaf=True, board=False, lintel=False,
               frame_at=STOP, frame_mat='M_CellarJoinery', leaf_mat='M_CellarJoinery', handle=False),
    'CW': dict(jamb='plain', leaves=1, board=False, glass=0.006, lintel=False,
               frame_at=STOP, frame_mat='M_CellarJoinery', leaf_mat='M_CellarJoinery', handle=False),
    # arched glazed screens into unheated spaces (cellar band, passage): fixed frame and glass
    'AS': dict(jamb='plain', leaves=0, board=False, lintel=False, niche=False, handle=False,
               frame_at=0.12),
    # oculus: fixed glass in a steel ring at the inner face (schiera O60); O90 is open (no record)
    'O': dict(jamb='plain', board=False, lintel=False, handle=False, frame=(0.03, 0.04),
              frame_mat='M_Steel', frame_at=None),
}


def spec_for(kind: str) -> dict:
    s = dict(BASE)
    s.update(TYPES.get(kind, {}))
    return s


def floor_of(z: float) -> float:
    """Finished floor of the storey an opening at z0 = z belongs to."""
    c = [f for f in FLOORS if f <= z + 0.16]
    return c[-1] if c else -0.32


def dims(rec: dict) -> tuple[float, float, float, float]:
    us = [p[0] for p in rec['outline']]
    zs = [p[1] for p in rec['outline']]
    return min(us), max(us), min(zs), max(zs)


def classify(rec: dict) -> str | None:
    """Opening type of a record (key of TYPES), or None for openings that get
    no joinery (open arcades, passages, cut-through arches). A part module
    may set rec['type'] itself (None = no joinery)."""
    if 'type' in rec:
        return rec['type']
    if rec.get('through') is not None or rec.get('keep_recess'):
        return None
    if rec['kind'] == 'round':
        return 'O'
    if rec['kind'] == 'poly':
        return 'T'
    u0, u1, z0, z1 = dims(rec)
    w, h = u1 - u0, z1 - z0
    sill = z0 - floor_of(z0)
    if rec['kind'] == 'arch':
        return 'AS'
    if w <= 0.62 and h <= 0.62:
        return 'K'
    if abs(w - 0.91) < 0.01 and abs(h - 0.92) < 0.01:
        return 'F'
    if h < 1.6:
        return 'E' if w >= 1.0 else 'E1'
    if rec.get('recess', 0) >= 0.29 and w > 1.2:
        return 'PT'
    if sill < 0.05 and h < 2.10 and w < 0.95:
        return 'P'
    return 'C' if w >= 1.0 else 'D'


# -------------------------------------------------------------- face frame
class Frame3:
    """Maps (u, z, d) of an opening's face to world (x, y, z)."""

    def __init__(self, rec: dict):
        self.axis, self.coord, self.out = rec['axis'], rec['coord'], rec['out']

    def w(self, u: float, z: float, d: float) -> tuple[float, float, float]:
        c = self.coord - self.out * d
        return (c, u, z) if self.axis == 'x' else (u, c, z)


def _slab(bm, fr: Frame3, outline_uz: Sequence[tuple[float, float]], d0: float, d1: float) -> None:
    """Prism of a (u, z) outline between depths d0 and d1."""
    pts = ccw(outline_uz)
    a = [bm.verts.new(fr.w(u, z, d0)) for u, z in pts]
    b = [bm.verts.new(fr.w(u, z, d1)) for u, z in pts]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[j], a[i], b[i], b[j]))


def _box(bm, fr, u0, u1, z0, z1, d0, d1):
    if u1 - u0 > 1e-4 and z1 - z0 > 1e-4 and abs(d1 - d0) > 1e-4:
        _slab(bm, fr, _rect(u0, u1, z0, z1), d0, d1)


def _ring(bm, fr: Frame3, outer_uz, width: float, d0: float, d1: float, bottom: float | None = None):
    """Profile ring `width` wide inside a (u, z) outline, between depths d0 and
    d1 (bottom member `bottom` wide if given, rectangles only); returns the
    inner outline."""
    o = clean(outer_uz)
    if bottom is not None and len(o) == 4:
        u0, u1 = min(p[0] for p in o), max(p[0] for p in o)
        z0, z1 = min(p[1] for p in o), max(p[1] for p in o)
        i = _rect(u0 + width, u1 - width, z0 + bottom, z1 - width)
    else:
        i = offset(o, width)
    oa = [bm.verts.new(fr.w(u, z, d0)) for u, z in o]
    ob = [bm.verts.new(fr.w(u, z, d1)) for u, z in o]
    ia = [bm.verts.new(fr.w(u, z, d0)) for u, z in i]
    ib = [bm.verts.new(fr.w(u, z, d1)) for u, z in i]
    n = len(o)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((oa[k], oa[j], ob[j], ob[k]))
        bm.faces.new((ia[j], ia[k], ib[k], ib[j]))
        bm.faces.new((oa[j], oa[k], ia[k], ia[j]))
        bm.faces.new((ob[k], ob[j], ib[j], ib[k]))
    return i


def _rect(u0, u1, z0, z1):
    return [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]


def _frame_depth(rec, spec) -> float:
    if spec.get('frame_at') is not None:
        return spec['frame_at']
    if spec['jamb'] == 'stop':
        return STOP
    if rec['kind'] == 'round':
        return WALL - 0.04
    return WALL            # plain jambs: frame in the lining plane (SE 51 trifora, SE 53 F)


# -------------------------------------------------------------- pockets
def pockets(rec: dict, kind: str | None = None) -> list[tuple[float, float, float, float, float, float]]:
    """Boxes (u0, u1, z0, z1, d0, d1) of brick to cut out of the body for this
    opening: the frame pocket behind a stop jamb (and its head rebate), the
    lintel, the inner part of the RC sill and the radiator niche. The joinery
    fills them (frame, lintel, sill block, niche lining)."""
    kind = kind or classify(rec)
    if kind is None:
        return []
    s = spec_for(kind)
    u0, u1, z0, z1 = dims(rec)
    zf = floor_of(z0)
    out = []
    if s['jamb'] == 'stop' and rec['kind'] == 'rect':
        out.append((u0 - MAZ, u1 + MAZ, z0, z1 + MAZ, STOP, FINISH + 0.05))
    if s['lintel'] and rec['kind'] == 'rect':
        out.append((u0 - 0.12, u1 + 0.12, z1, z1 + 0.13, 0.05, FINISH + 0.05))
    if not s['door'] and s['board'] and rec['kind'] == 'rect' and z0 - zf > 0.5:
        out.append((u0 - 0.12, u1 + 0.12, z0 - 0.13, z0, 0.115, FINISH + 0.05))       # RC sill, inner part
    if s['niche'] and rec['kind'] == 'rect':
        out.append((u0 - MAZ, u1 + MAZ, zf, z0 - 0.13, STOP, FINISH + 0.05))
    if s['door'] and kind in ('C', 'D') and z0 - zf > 0.01:
        out.append((u0 - MAZ, u1 + MAZ, zf - 0.02, z0, 0.0, FINISH + 0.05))           # threshold
    return out


def add_pockets(bm, recs: Sequence[dict]) -> None:
    """Pocket boxes of these openings into a hollowing cutter bmesh."""
    for r in recs:
        fr = Frame3(r)
        for u0, u1, z0, z1, d0, d1 in pockets(r):
            _box(bm, fr, u0, u1, z0, z1, d0, d1)


def lining_boxes(rec: dict, kind: str | None = None, board: bool | None = None
                 ) -> list[tuple[float, float, float, float]]:
    """Rectangles (u0, u1, z0, z1) the joinery passes through the wall lining
    besides the opening itself: the frame pocket behind a stop jamb (reveal
    plaster), the window board (`board` overrides the type's flag, for part
    modules that build their own boards), the radiator niche and the
    threshold. The lintel and the inner sill block stay behind the lining -
    cutting their pockets too left bands of bare concrete and cut insulation
    round every window."""
    kind = kind or classify(rec)
    if kind is None:
        return []
    s = spec_for(kind)
    u0, u1, z0, z1 = dims(rec)
    zf = floor_of(z0)
    stop = s['jamb'] == 'stop' and rec['kind'] == 'rect'
    out = []
    if stop:
        out.append((u0 - MAZ, u1 + MAZ, z0, z1 + MAZ))
    if (s['board'] if board is None else board) and not s['door'] and rec['kind'] == 'rect' and z0 - zf > 0.5:
        out.append((u0 - MAZ - 0.02, u1 + MAZ + 0.02, z0 - 0.025, z0) if stop else (u0 - 0.02, u1 + 0.02, z0 - 0.025, z0))
    if s['niche'] and rec['kind'] == 'rect':
        out.append((u0 - MAZ, u1 + MAZ, zf, z0 - 0.13))
    if s['door'] and kind in ('C', 'D') and z0 - zf > 0.01:
        out.append((u0 - MAZ, u1 + MAZ, zf - 0.02, z0))
    return out


def lining_cutter(recs: Sequence[dict]) -> bmesh.types.BMesh:
    """Cutter for the wall linings round these openings: the opening and
    lining_boxes(), from 0.3 m in front of the wall to 1.2 m behind it."""
    bm = bmesh.new()
    for r in recs:
        kind = classify(r)
        if kind is None and r.get('through') is None:
            continue
        fr = Frame3(r)
        geo.Face(r['axis'], r['coord'], r['out']).solid(bm, r['outline'], 1.2, outside=0.3)
        for u0, u1, z0, z1 in lining_boxes(r, kind):
            _box(bm, fr, u0, u1, z0, z1, WALL - 0.02, 1.2)
    return bm


# -------------------------------------------------------------- one opening
def opening(kit: Kit, rec: dict, kind: str, prefix: str = 'Window') -> None:
    """All joinery of one opening of type `kind`."""
    s = spec_for(kind)
    fr = Frame3(rec)
    u0, u1, z0, z1 = dims(rec)
    zf = floor_of(z0)
    fw, fd = s['frame']
    sw, sd = s['sash']
    d0 = _frame_depth(rec, s)
    fbm = kit(f'{prefix}Frames', s['frame_mat'])
    lbm = kit(f'{prefix}Leaves', s['leaf_mat'])
    gbm = kit(f'{prefix}Glass', s['glass_mat'])
    if rec['kind'] == 'round':
        inner = _ring(fbm, fr, rec['outline'], fw, d0, d0 + fd)
        _glass(gbm, fr, inner, d0 + fd / 2, 0.006)
        return
    if kind == 'T':
        _trifora(kit, fr, rec, s, d0, prefix)
        return
    if rec['kind'] == 'arch' or kind == 'AS':
        inner = _ring(fbm, fr, rec['outline'], fw, d0, d0 + fd)
        _glass(gbm, fr, inner, d0 + fd / 2, s['glass'])
        return
    stop = s['jamb'] == 'stop'
    # outer frame: behind a stop jamb it laps 6 cm behind the brick on the
    # sides and head, so only the leaves show from outside (SE 53 E)
    fo = _rect(u0 - fw, u1 + fw, z0, z1 + fw) if stop else _rect(u0, u1, z0, z1)
    fi = _ring(fbm, fr, fo, fw, d0, d0 + fd, bottom=fw)
    iu0, iu1 = min(p[0] for p in fi), max(p[0] for p in fi)
    iz0, iz1 = min(p[1] for p in fi), max(p[1] for p in fi)
    ds = d0 + (fd - sd) / 2
    if kind == 'PT':
        _street_door(kit, fr, s, iu0, iu1, iz0, iz1, ds, zf, prefix)
    elif s.get('panel_leaf') or s.get('flush_leaf'):
        _door_leaf(kit, fr, s, iu0, iu1, iz0, iz1, ds, zf, prefix)
    else:
        n = max(1, s['leaves'])
        lw = (iu1 - iu0) / n
        for k in range(n):
            a, b = iu0 + k * lw, iu0 + (k + 1) * lw
            gl = _ring(lbm, fr, _rect(a, b, iz0, iz1), sw, ds, ds + sd, bottom=s['bottom_rail'])
            _glass(gbm, fr, gl, ds + sd / 2, s['glass'])
        if s['handle']:
            hb = kit(f'{prefix}Handles', 'M_Steel')
            uh = (iu0 + iu1) / 2 if n == 2 else iu1 - sw / 2
            # windows: mid-sash (floor + 1.05 fell on the bottom rail of the
            # finestre tipo and under the sash of the high-sill windows)
            zh = (iz0 + iz1) / 2 if not s['door'] else zf + 1.05
            _box(hb, fr, uh - 0.012, uh + 0.012, zh - 0.07, zh + 0.07, ds + sd, ds + sd + 0.012)
            _box(hb, fr, uh - 0.012, uh + 0.012, zh - 0.10, zh + 0.012, ds + sd + 0.012, ds + sd + 0.06)
    # reveal plaster behind a stop jamb: pocket jambs and head, frame -> finished face
    if stop:
        rp = kit(f'{prefix}Reveals', 'M_PlasterInt')
        da, db = d0 + fd, FINISH
        t = MAZ - fw                     # flush with the frame's outer side
        _box(rp, fr, u0 - MAZ, u0 - MAZ + t, z0, z1 + MAZ, da, db)
        _box(rp, fr, u1 + MAZ - t, u1 + MAZ, z0, z1 + MAZ, da, db)
        _box(rp, fr, u0 - MAZ, u1 + MAZ, z1 + MAZ - t, z1 + MAZ, da, db)
    # lintel: RC L, outer leg 0.26 x 0.13 behind the façade band, inner leg 0.135 x 0.06 (SE 54 det. 3)
    if s['lintel']:
        lb = kit('Lintels', 'M_Structure')
        if stop:
            _box(lb, fr, u0 - 0.12, u1 + 0.12, z1, z1 + 0.13, 0.05, STOP)
            _box(lb, fr, u0 - 0.12, u1 + 0.12, z1 + MAZ, z1 + 0.13, STOP, WALL)
            _box(lb, fr, u0 - 0.12, u0 - MAZ, z1, z1 + MAZ, STOP, WALL)
            _box(lb, fr, u1 + MAZ, u1 + 0.12, z1, z1 + MAZ, STOP, WALL)
        else:
            _box(lb, fr, u0 - 0.12, u1 + 0.12, z1, z1 + 0.13, 0.05, WALL)
    if not s['door'] and s['board'] and z0 - zf > 0.5:
        # inner part of the RC sill, and the cream timber window board on it (n24)
        # (the side pieces stop at the board's ends, the piece under the board at
        # its underside: no coplanar tops, no overlap)
        sb = kit('SillBlocks', 'M_Concrete')
        ub0, ub1 = (u0 - MAZ - 0.02, u1 + MAZ + 0.02) if stop else (u0 - 0.02, u1 + 0.02)
        _box(sb, fr, u0 - 0.12, u1 + 0.12, z0 - 0.13, z0, 0.115, d0 if stop else WALL)
        if stop:
            _box(sb, fr, u0 - 0.12, ub0, z0 - 0.13, z0, d0, WALL)
            _box(sb, fr, ub1, u1 + 0.12, z0 - 0.13, z0, d0, WALL)
            _box(sb, fr, ub0, ub1, z0 - 0.13, z0 - 0.025, d0, WALL)
        wb = kit(f'{prefix}Boards', 'M_Joinery')
        _box(wb, fr, ub0, ub1, z0 - 0.025, z0, (d0 + fd) if stop else WALL + 0.06, FINISH + 0.02)
    if s['niche']:
        # radiator niche: the inner brick stops under the sill; the lining runs on its back
        nb = kit('NicheLining', 'M_PlasterInt')
        _box(nb, fr, u0 - MAZ, u1 + MAZ, zf, z0 - 0.13, STOP, STOP + LIN)
    if s['door'] and kind in ('C', 'D') and z0 - zf > 0.01:
        th = kit('Thresholds', 'M_Concrete')
        _box(th, fr, u0 - MAZ, u1 + MAZ, zf - 0.02, z0, 0.0, FINISH)


def _glass(bm, fr: Frame3, outline_uz, d_mid: float, t: float) -> None:
    _slab(bm, fr, outline_uz, d_mid - t / 2, d_mid + t / 2)


def _door_leaf(kit, fr, s, u0, u1, z0, z1, ds, zf, prefix):
    """Entrance leaf with 4 raised panels (SE 65) or a flush cellar leaf."""
    lb = kit(f'{prefix}DoorLeaves', s['leaf_mat'])
    t = 0.050 if s.get('panel_leaf') else 0.044       # "5": two 18 mm skins + insulated core (SE 65)
    if s.get('flush_leaf'):
        _box(lb, fr, u0 + 0.003, u1 - 0.003, z0 + 0.008, z1 - 0.003, ds, ds + t)
        return
    # 4 raised panels (SE 65 measured): lower 0.16-0.90, mid rail 0.90-0.99, upper 0.99-1.92
    st = 0.11                        # stiles
    um = (u0 + u1) / 2
    zl0, zl1, zu0 = zf + 0.16, zf + 0.90, zf + 0.99
    zu1 = min(zf + 1.92, z1 - 0.06)
    frame_o = _rect(u0 + 0.003, u1 - 0.003, z0 + 0.008, z1 - 0.003)
    _ring(lb, fr, frame_o, st, ds, ds + t, bottom=zl0 - z0 - 0.008)
    for c, d in ((zl0, zl1), (zu0, zu1)):                                                  # muntin, split at the lock rail
        _box(lb, fr, um - st / 2, um + st / 2, c, d, ds + 0.001, ds + t - 0.001)
    _box(lb, fr, u0 + st, u1 - st, zl1, zu0, ds + 0.001, ds + t - 0.001)                    # lock rail
    _box(lb, fr, u0 + st, u1 - st, zu1, z1 - 0.003 - st, ds + 0.001, ds + t - 0.001)        # top rail
    pb = kit(f'{prefix}DoorPanels', s['leaf_mat'])
    for a, b in ((u0 + st, um - st / 2), (um + st / 2, u1 - st)):
        for c, d in ((zl0, zl1), (zu0, zu1)):
            _box(pb, fr, a, b, c, d, ds + 0.010, ds + t - 0.010)                            # raised panel
    hb = kit(f'{prefix}Handles', 'M_Steel')
    _box(hb, fr, um - 0.03, um + 0.03, zf + 0.94 - 0.03, zf + 0.94 + 0.03, ds - 0.03, ds + 0.001)  # central knob at ~0.94
    # inside: lever handle on the lock stile at 1.05, on a rose
    uh, zh, di = u1 - st / 2, zf + 1.05, ds + t
    _box(hb, fr, uh - 0.025, uh + 0.025, zh - 0.08, zh + 0.025, di, di + 0.010)
    _box(hb, fr, uh - 0.12, uh + 0.012, zh - 0.011, zh + 0.011, di + 0.010, di + 0.055)


def _street_door(kit, fr, s, u0, u1, z0, z1, ds, zf, prefix):
    """Tower street door: 0.92 x 2.04 leaf, fixed glass above and beside it."""
    fb = kit(f'{prefix}Frames', s['frame_mat'])
    gb = kit(f'{prefix}Glass', s['glass_mat'])
    um = (u0 + u1) / 2
    lw, lh = 0.92, 2.04
    a, b = um - lw / 2, um + lw / 2
    zt = zf + lh
    _box(fb, fr, a - 0.05, a, z0, z1, ds, ds + 0.056)            # posts
    _box(fb, fr, b, b + 0.05, z0, z1, ds, ds + 0.056)
    _box(fb, fr, u0, u1, zt, zt + 0.05, ds, ds + 0.056)          # transom
    for g in (_rect(u0, a - 0.05, z0, z1), _rect(b + 0.05, u1, z0, z1), _rect(a, b, zt + 0.05, z1)):
        if g[1][0] - g[0][0] > 0.02:
            _glass(gb, fr, g, ds + 0.028, s['glass'])
    _door_leaf(kit, fr, s, a, b, z0, zt, ds, zf, prefix)


def _trifora(kit, fr, rec, s, d0, prefix):
    """Trifora (SE 51): one frame round the whole outline; fixed side lights;
    two casements with arched top rails in the 1.04 centre, from 0.66."""
    fw, fd = s['frame']
    sw, sd = s['sash']
    fbm = kit(f'{prefix}Frames', s['frame_mat'])
    lbm = kit(f'{prefix}Leaves', s['leaf_mat'])
    gbm = kit(f'{prefix}Glass', s['glass_mat'])
    inner = _ring(fbm, fr, rec['outline'], fw, d0, d0 + fd)
    u0, u1, z0, z1 = dims(rec)
    uc = (u0 + u1) / 2
    zs_side = min(z for u, z in rec['outline'] if abs(u - u0) < 1e-6)
    post = 0.095
    for sg in (-1, 1):
        # posts between the inner frame faces, 2 mm inside its depth (no coplanar faces)
        up = uc + sg * (0.52 + post / 2)
        ztop = min(_z_on(inner, up - post / 2), _z_on(inner, up + post / 2)) + 0.02
        _box(fbm, fr, up - post / 2, up + post / 2, zs_side + fw - 0.02, ztop, d0 + 0.002, d0 + fd - 0.002)
    # fixed side lights: the inner outline beyond the posts
    for sg in (-1, 1):
        lo = [(u, z) for u, z in inner if sg * (u - uc) >= 0.52 + post - 1e-6]
        cut = uc + sg * (0.52 + post)
        if len(lo) >= 2:
            poly = _side_light(inner, uc, sg, cut, zs_side + fw)
            if poly:
                _glass(gbm, fr, poly, d0 + fd / 2, s['glass'])
    # centre casements 1.04 wide, arched tops (follow the frame's inner arc)
    a, b = uc - 0.52, uc + 0.52
    zc0 = min(p[1] for p in inner if abs(p[0] - uc) < 0.52)
    ds = d0 + (fd - sd) / 2
    for la, lb_ in ((a, uc), (uc, b)):
        top = [(u, z) for u, z in inner if la - 1e-6 <= u <= lb_ + 1e-6 and z > zc0 + 0.5]
        za, zb = _z_on(inner, la), _z_on(inner, lb_)
        out = [(la, zc0), (lb_, zc0), (lb_, zb)] + sorted([p for p in top if la < p[0] < lb_],
                                                          key=lambda p: -p[0]) + [(la, za)]
        gl = offset(out, sw)
        _ring(lbm, fr, out, sw, ds, ds + sd)
        _glass(gbm, fr, gl, ds + sd / 2, s['glass'])
    hb = kit(f'{prefix}Handles', 'M_Steel')
    zh = floor_of(z0) + 1.05
    _box(hb, fr, uc - 0.012, uc + 0.012, zh - 0.07, zh + 0.07, ds + sd, ds + sd + 0.012)


def _z_on(poly, u):
    """Highest z of polygon edges crossing the vertical line at u."""
    best = None
    n = len(poly)
    for i in range(n):
        (ua, za), (ub, zb) = poly[i], poly[(i + 1) % n]
        if (ua - u) * (ub - u) <= 0 and abs(ub - ua) > 1e-9:
            z = za + (zb - za) * (u - ua) / (ub - ua)
            best = z if best is None else max(best, z)
    return best if best is not None else max(p[1] for p in poly)


def _side_light(inner, uc, sg, cut, zb):
    pts = [(u, z) for u, z in inner if sg * (u - cut) > 1e-6]
    if len(pts) < 2:
        return None
    zt = _z_on(inner, cut)
    top = sorted([p for p in pts if p[1] > zb + 1e-6], key=lambda p: sg * p[0])
    far = max(pts, key=lambda p: sg * p[0])[0]
    poly = [(cut, zb), (far, zb)] + list(reversed(top)) + [(cut, zt)] if sg > 0 else \
        [(far, zb), (cut, zb), (cut, zt)] + top
    return ccw(_dedup(poly))


def _dedup(pts):
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


# -------------------------------------------------------------- passes
def build_openings(kit: Kit, recs: Sequence[dict], prefix: str = 'Window') -> int:
    """Joinery for the given records (marks them done); returns the count."""
    n = 0
    for r in recs:
        if r.get('done'):
            continue
        r['done'] = True
        kind = classify(r)
        if kind is None:
            continue
        opening(kit, r, kind, prefix)
        n += 1
    return n


def build(ctx) -> None:
    """Final pass: joinery for registered openings no part module handled."""
    left = [r for r in geo.OPENINGS if not r.get('done')]
    if not left:
        return
    kit = Kit(ctx, 'Joinery', 'Misc', 'Joinery')
    build_openings(kit, left)
    kit.flush()
