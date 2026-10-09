"""Joinery (docs/INTERIORS.md section 3): frames, sashes, glazing bars, glass,
interior sills and shutters for every window and door registered in
geo.OPENINGS while the exterior was cut (with geo.THROUGH set, those openings
go right through the walls and carry no glass of their own).

Geometry is built in each opening's face frame: u along the face (world y
for an x-facing wall, world x for a y-facing one), z up, and d = depth behind
the outer face (into the wall). One record gets one opening TYPE (see
classify()), whose SPEC gives the frame position and profiles, the leaf
division, glazing bars and sills.

The part modules call build_openings() for the records of their own bodies
(so that mirrored copies - the west towers - can be mirrored with the rest);
build() is the final pass over whatever is left.
"""
from __future__ import annotations

import math
from typing import Sequence

import bmesh

from . import geo
from .interior import Kit, ccw, offset

# -------------------------------------------------------------- default spec
# Overridden per type in TYPES (filled from the drawings, docs/INTERIORS.md 3).
DEFAULT = dict(
    set_back=0.12,        # outer face of the frame behind the wall face
    frame=(0.065, 0.068),  # outer frame: face width, depth
    sash=(0.075, 0.060),   # leaf (sash) profile: face width, depth
    leaves=2,             # side-hung leaves across the width
    transom=None,         # height of a transom above the sill (fixed light above), or None
    bars=(0, 0),          # glazing bars per leaf: (vertical, horizontal)
    bar=0.03,             # glazing bar width
    glass=0.020,          # glass unit thickness (double glazing 4/12/4)
    door_panel=None,      # opaque lower panel height (French windows / doors)
    solid_leaf=False,     # opaque door leaf (entrance, cellar)
    sill_in=(0.03, 0.025),  # interior sill board: thickness, projection past the wall's inner face
    wall=0.395,           # wall depth at the opening (masonry + lining)
    frame_mat='M_Frame', glass_mat='M_Glass', sill_mat='M_Stone', leaf_mat='M_Frame',
)

TYPES: dict[str, dict] = {}


def spec_for(kind: str) -> dict:
    s = dict(DEFAULT)
    s.update(TYPES.get(kind, {}))
    return s


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


def _ring(bm, fr: Frame3, outer_uz, width: float, d0: float, d1: float) -> list[tuple[float, float]]:
    """Profile ring `width` wide inside a (u, z) outline, between depths d0
    and d1; returns the inner outline."""
    o = ccw(outer_uz)
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


# -------------------------------------------------------------- one opening
def window(kit: Kit, rec: dict, spec: dict, prefix: str = 'Window') -> None:
    """Frame, leaves, glazing bars, glass and interior sill of one opening."""
    fr = Frame3(rec)
    outline = rec['outline']
    us = [p[0] for p in outline]
    zs = [p[1] for p in outline]
    u0, u1, z0, z1 = min(us), max(us), min(zs), max(zs)
    fw, fd = spec['frame']
    sw, sd = spec['sash']
    d0 = spec['set_back']
    fbm = kit(f'{prefix}Frames', spec['frame_mat'])
    gbm = kit(f'{prefix}Glass', spec['glass_mat'])
    lbm = kit(f'{prefix}Leaves', spec['leaf_mat'])
    if rec['kind'] == 'round':
        inner = _ring(fbm, fr, outline, fw, d0, d0 + fd)
        dg = d0 + fd / 2 - spec['glass'] / 2
        _slab(gbm, fr, inner, dg, dg + spec['glass'])
        return
    # outer frame round the whole outline (rect or arched)
    inner = _ring(fbm, fr, outline, fw, d0, d0 + fd)
    iu0, iu1 = u0 + fw, u1 - fw
    iz0 = z0 + fw
    arch = rec.get('arch_rise') or 0.0
    spring = z1 - arch if arch > 1e-6 else None
    top_rect = (spring if spring is not None else z1 - fw)
    # transom: fixed light above (also at the spring of an arch)
    t = spec['transom']
    z_tr = None
    if t is not None:
        z_tr = z0 + t
    elif spring is not None:
        z_tr = spring
    ds0 = d0 + (fd - sd) / 2                      # leaves centred in the frame depth
    if z_tr is not None and z_tr < top_rect + 1e-6:
        _slab(fbm, fr, _rect(iu0, iu1, z_tr - fw / 2, z_tr + fw / 2), d0, d0 + fd)
        # fixed light above the transom
        top_poly = [(u, z) for u, z in inner if z > z_tr + fw / 2 - 1e-6] if arch > 1e-6 else None
        if top_poly and len(top_poly) >= 2:
            fl = [(iu0, z_tr + fw / 2)] + sorted(top_poly, key=lambda p: p[0]) + [(iu1, z_tr + fw / 2)]
            fl = [(u, max(z, z_tr + fw / 2)) for u, z in fl]
        else:
            fl = _rect(iu0, iu1, z_tr + fw / 2, top_rect if arch < 1e-6 else z1 - fw)
        _glass(gbm, fr, fl, d0 + fd / 2, spec['glass'])
        leaf_top = z_tr - fw / 2
    else:
        leaf_top = top_rect if arch < 1e-6 else z1 - fw
    # leaves
    n = max(1, spec['leaves'])
    lw = (iu1 - iu0) / n
    for k in range(n):
        a, b = iu0 + k * lw, iu0 + (k + 1) * lw
        lo = _rect(a, b, iz0, leaf_top)
        if spec['solid_leaf']:
            _slab(lbm, fr, lo, ds0, ds0 + sd)
            continue
        gl = _ring(lbm, fr, lo, sw, ds0, ds0 + sd)
        gz0 = iz0 + sw
        if spec['door_panel']:
            zp = z0 + spec['door_panel']
            _slab(lbm, fr, _rect(a + sw, b - sw, gz0, zp), ds0 + sd / 2 - 0.012, ds0 + sd / 2 + 0.012)
            _slab(lbm, fr, _rect(a + sw, b - sw, zp, zp + sw * 0.8), ds0, ds0 + sd)
            gz0 = zp + sw * 0.8
        ga, gb, gt = a + sw, b - sw, leaf_top - sw
        _glass(gbm, fr, _rect(ga, gb, gz0, gt), ds0 + sd / 2, spec['glass'])
        nv, nh = spec['bars']
        bw = spec['bar']
        for i in range(1, nv + 1):
            uc = ga + (gb - ga) * i / (nv + 1)
            _slab(lbm, fr, _rect(uc - bw / 2, uc + bw / 2, gz0, gt), ds0 + 0.004, ds0 + sd - 0.004)
        for i in range(1, nh + 1):
            zc = gz0 + (gt - gz0) * i / (nh + 1)
            _slab(lbm, fr, _rect(ga, gb, zc - bw / 2, zc + bw / 2), ds0 + 0.003, ds0 + sd - 0.003)
    # interior sill board for windows (not doors)
    if z0 > rec.get('floor', z0 - 0.3) + 0.25 and spec['sill_in']:
        th, proj = spec['sill_in']
        sbm = kit(f'{prefix}SillsIn', spec['sill_mat'])
        _slab(sbm, fr, _rect(u0 - 0.03, u1 + 0.03, z0 - th, z0), d0 + fd - 0.01, spec['wall'] + proj)


def _glass(bm, fr: Frame3, outline_uz, d_mid: float, t: float) -> None:
    _slab(bm, fr, outline_uz, d_mid - t / 2, d_mid + t / 2)


# -------------------------------------------------------------- passes
def classify(rec: dict) -> str | None:
    """Opening type of a record (key of TYPES), or None for openings that get
    no joinery (open arcades, passages, cut-through arches)."""
    if rec.get('through') is not None:
        return None
    return rec.get('type') or 'window'


def build_openings(ctx, kit: Kit, recs: Sequence[dict]) -> int:
    """Joinery for the given records (marks them done); returns the count."""
    n = 0
    for r in recs:
        if r.get('done'):
            continue
        kind = classify(r)
        r['done'] = True
        if kind is None:
            continue
        window(kit, r, spec_for(kind))
        n += 1
    return n


def build(ctx) -> None:
    """Final pass: joinery for registered openings no part module handled."""
    left = [r for r in geo.OPENINGS if not r.get('done')]
    if not left:
        return
    kit = Kit(ctx, 'Joinery', 'Misc', 'Joinery')
    build_openings(ctx, kit, left)
    kit.flush()
