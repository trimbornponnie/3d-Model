"""Carpet middle row (Tipo B1) and south row (Tipo B) interiors, the middle
row's L0 cantine / corridor / passage and the campo houses' south strip
(research report carpet_middle_south.md, build-ups layers.md, joinery
windows.md; docs/INTERIORS.md).

Each H-house holds two mirror-image dwellings either side of the house axis
(d = metres from the axis, + = west for s = +1; the east one mirrored by code).

Middle row (duplex L1 + L2, entered at L0):
  L0  six cantina cells behind a 0.28 front wall on the N/M corridor (W8
      partitions, F4 at -0.32, cellar doors / windows), the middle cell
      private and entered from the core; the core: entrance hall from the
      covered passage (portoncino 0.91 x 2.07), corridor, garden door,
      flight A rising north; landing and three steps in the passage;
  L1  bath and north bedroom across the N/M joint to the W5 wall at
      Y 6.906 -> 7.033, hall at the top of flight A, core corridor, south
      landing, south bedroom to the W5 wall at Y 14.937 -> 15.064;
  L2  kitchen, hall under the copper vault with the door to the notch
      terrace (R3, 6.15), corridor, landing open to the living-dining room,
      French doors onto the M/S joint terrace (R3, 6.15).
South row (duplex L0 + L1):
  L0  shared porch off the passage (or the campo), three steps into the
      shared vestibule, the two portoncini, lobby, kitchen, core with the
      flight rising south, living-dining room; a cellar each in the joint;
  L1  bath and north bedroom across the M/S joint, hall, corridor, landing,
      south bedroom; ceilings flat under the joint deck, sloped under R1.

Walls: the exterior masonry stays in the bodies (W1 0.395, core W2 0.28,
end walls 0.37, joint leaves 0.185) with the insulated lining (55) on warm
faces and plaster (15) on interior masonry; the axis and party walls (W5),
the core spine (W4), partitions (W7), cellar partitions (W8) and the two
row-dividing walls are separate layered objects.  Floors F1 / F2 / F3 / F4
per room on one structural slab per storey; R1 under the tiles, R2 under the
core vaults (the copper lens cut to a 2 mm skin), R3 on the notch terraces,
the M/S joint deck and the campo strip.

Boundary with interior_carpet_north (read its docstring): north of Y 6.906
at L1 and everything in JointNM above z 5.72 is the north row's; the L1
dividing wall Y 6.906 -> 7.033 and the middle-row rooms south of it are
built here (in SouthPavN's void, on its slab 2.71 -> 2.91); NorthPavM's
north wall (Y 7.776 -> 8.015) stays solid at L2 as the wall between the
middle-row kitchens and the north-row baths.

Everything here runs only with geo.THROUGH set (build.py --interiors).
"""
from __future__ import annotations

import math
import time

import bmesh
import bpy
from mathutils import Vector

from . import buildups as BU
from . import carpet as C
from . import geo
from . import interior as I
from . import joinery as J
from .common import xE, yY
from .params import (BLOCKS, CAMPO, CAMPO_HOUSES, COPING_H, CORE_CROWN, CORE_VAULT_R, FLOORS, MODULE,
                     NOTCH_HALF, ROOF_HIGH, ROOF_LOW, ROWS, SLAB, WALL)

M = MODULE
WM = WALL / M                       # W1 masonry 0.395 in modules
LIN = BU.LINING_T                   # 0.055 insulated lining
PL = 0.015                          # plaster on interior masonry
EW = C.END_WALL                     # 0.37 block-end / slot / campo end walls (as the exterior's hollows)
LEAF = C.GAP / 2 + 0.185            # 0.23: joint line -> face of the joint leaf (W6)
EPS = 0.02
Z0, Z1, Z2 = FLOORS[0], FLOORS[1], FLOORS[2]
SOFF = {Z0: Z1 - SLAB, Z1: Z2 - SLAB}       # raw soffits 2.71 / 5.72
TM, TS = ROWS['M']['T'], ROWS['S']['T']

# ------------------------------------------------------------ plan (modules)
MN0, MN1 = ROWS['M']['npav']        # 7.776, 10.224
MS0, MS1 = ROWS['M']['spav']        # 12.776, 15.224
SN0, SN1 = ROWS['S']['npav']        # 15.776, 18.224
SC0, SC1 = ROWS['S']['core']        # 18.224, 20.776
SS0, SS1 = ROWS['S']['spav']        # 20.776, 23.224
MNI0, MNI1 = MN0 + WM, MN1 - WM     # masonry faces 8.015, 9.985
MSI0, MSI1 = MS0 + WM, MS1 - WM     # 13.015, 14.985
SNI0, SNI1 = SN0 + WM, SN1 - WM     # 16.015, 17.985
SSI0, SSI1 = SS0 + WM, SS1 - WM     # 21.015, 22.985
JN0, JN1 = C.JOINTS['NM'][0], C.JOINTS['NM'][1]     # 7.224, 7.776
JS0, JS1 = C.JOINTS['MS'][0], C.JOINTS['MS'][1]     # 15.224, 15.776
LF = LIN / M                        # lining in modules
# middle row
Y_DIVN0 = 6.906                     # L1 dividing wall to the north row (interior_carpet_north L1_SOUTH)
Y_DIVN1 = Y_DIVN0 + 0.21 / M        # 7.033
Y_FRONT = C.CORRIDOR_NM[1]          # 7.98: cantine front (the exterior's corridor face)
Y_CELL = Y_FRONT + 0.28 / M         # 8.150: cells (front wall 0.28, n42 SE 56)
Y_THIN = 10.08                      # thin wall middle cell | core (n11, n18)
Y_TOPM = 10.145                     # top risers of flights A and B (n10, n67)
Y_BATHM = 8.82                      # L1 bath | hall partition (W7 wet), n67
Y_XW0, Y_XW1 = C.LANDING_M          # 8.95, 9.132: L2 cross wall terrace | hall (core body)
Y_LPM = MSI0 + LF                   # 13.048: L1 landing | south bedroom partition, south face
Y_DIVS = 15.0                       # L1 dividing wall middle | south row, centre (n67 14.94 -> 15.06)
Y_DIVS0, Y_DIVS1 = Y_DIVS - 0.105 / M, Y_DIVS + 0.105 / M
Y_KDOOR_M = 9.66                    # L2 kitchen door centre (n10 9.40 -> 9.87)
Y_BDOOR_M = 9.66                    # L1 north bedroom door centre (n67 9.42 -> 9.90)
# south row
Y_PORCH = 15.0                      # porch front on the passage (n11, n76)
Y_CEL0, Y_CEL1 = 15.26, 15.90       # cellars (n11, n76)
Y_STEP = (SN0, SN0 + 0.18, SN0 + 0.36)     # porch -> vestibule risers, 3 x 0.15 (n11 15.82 / 16.00 / 16.18)
Y_DW0 = 17.0                        # door wall, vestibule side (n11)
Y_DW1 = Y_DW0 + 0.315 / M           # 17.191 (W3: 26 brick + lining, SE 65)
Y_FOOTS = 18.20                     # first riser of the south flight (n11, n18)
Y_BATHS = 16.845                    # L1 bath | hall partition (n67 16.80 -> 16.86)
Y_LPS = SSI0 + LF                   # 21.048: L1 landing | south bedroom partition, south face
Y_KDOOR_S = 17.66                   # L0 kitchen door centre (n11 17.45 -> 17.92)
Y_BDOOR_S = 17.64                   # L1 north bedroom door centre (n67 17.40 -> 17.88)
# across (metres from the house axis)
D_AX = 0.105                        # axis wall half thickness (W5 0.21 / spine)
D_CORE = C.CORE_W / 2 - 0.28        # 1.77: core wall masonry face (render 0.02 + brick 0.26)
D_BAND = 0.87                       # flight | corridor (n30 "1,65" = flight + corridor)
D_NOTCH = NOTCH_HALF                # 1.485
D_KIT = NOTCH_HALF + WALL           # 1.88: L2 kitchen side / notch side wall face (as interior_carpet_north)
D_BAY = 1.91                        # L1 bay wall centre (W7 wet 1.835 -> 1.985, n67 1.84 -> 1.98)
D_PORCH = 1.50                      # porch / vestibule half width (n76)
D_CELL_S = 1.97                     # south-row cellar, axis side (porch side wall 0.47)
D_SIDE = 1.825                      # vestibule | kitchen wall, kitchen-side masonry face
D_PARTY = 3 * M                     # 4.95
D_FACE = 3.22 * M                   # 5.313: block end / slot face
D_PIER = 0.26                       # porch axis pier half width (n76 "52")
D_PORCHO = 1.48                     # porch -> vestibule openings 0.26 -> 1.48 (n76 "1,22")
Z_BEAM_M = 8.10                     # L2 opening core -> living, beam soffit (vault springing)
Z_BEAM_S = 5.10                     # L1 openings core <-> pavilions, beam soffit
Z_CELL = -0.32                      # cellar floor (F4, SE 63)

# doors: opening = leaf + 2 x 0.025 casing (bath leaf 0.70 "70/210", rooms 0.80, n67)
DOOR_ROOM, DOOR_BATH, DOOR_HEAD = 0.85, 0.75, 2.10
PORT = dict(d=(0.305, 1.215), h=2.07)          # portoncino 0.91 x 2.07 (SE 65, n11)
CELLAR = dict(w=0.775, z0=-0.32, z1=1.73)      # porte cantine "77,5/205" (SE 56, SE 65)
CWIN = dict(d=(0.145, 0.92), z0=1.18, z1=1.73)  # finestre cantine "77,5/55" (n42)
CDOORS = ((2.38, 3.155), (3.445, 4.22))        # outer-cell doors (n42 2.365 -> 3.17 / 3.43 -> 4.235)
TER_M = dict(d=(0.58, 1.32), h=2.05)           # L2 hall -> notch terrace door (n10)

# flights (15 risers per storey, 14 goings: n10 / n67 / n11, n18)
N_RISERS = 15
GOING_M = 2.0 * M / 14              # 0.2357
GOING_S = 0.235
Y_FOOTM = Y_TOPM + 14 * GOING_M / M     # 12.145
Y_TOPS = Y_FOOTS + 14 * GOING_S / M     # 20.194

# stacks
SPINE = [('Plaster', 'M_PlasterInt', 0.015), ('RC', 'M_Structure', 0.18), ('Plaster', 'M_PlasterInt', 0.015)]
FL_INT = BU.FLOOR_INT[:-1]          # parquet / screed / fill on the slab (F1)
FL_OPEN = BU.FLOOR_OPEN[:-1]        # parquet / screed / insulation (F2, over unheated or open air)
FL_GF = BU.FLOOR_GF[:-1]            # F3 on the ground slab
FL_HALL = [('HallStone', 'M_Stone', 0.03), ('HallScreed', 'M_Screed', 0.09)]   # shared vestibule / campo porch
FL_CELL = BU.FLOOR_CELLAR[:1]       # F4 concrete (the gravel lies in the site plate)
PLASTER = [('Plaster', 'M_PlasterInt', PL)]
TERR = BU.TERRACE                   # R3 incl. the slab, 0.43 -> finish z_f + 0.13


# ------------------------------------------------------------ joinery types
def _register_types() -> None:
    """Local opening types (added to joinery.TYPES; the engine is not edited):
    PM the portoncino in the 0.26-0.37 walls of the cores and the vestibule
    (frame behind the reveal, no W1 lintel), DM the glazed garden / terrace
    doors in the 0.28-0.30 core walls (plain jamb, frame inside the wall)."""
    J.TYPES.setdefault('PM', dict(J.TYPES['P'], lintel=False))
    J.TYPES.setdefault('DM', dict(jamb='plain', door=True, leaves=1, bottom_rail=0.150, board=False,
                                  lintel=False, niche=False, frame_at=0.10))


# ------------------------------------------------------------ roof / vault
def roof_plane(T, Y_low, Y_high):
    """Tile top plane z(y) of a pavilion as the exterior builds it
    (common.pavilion_section, wall 0.37, 0.10 under the copings), and its slope."""
    yl, yh = yY(Y_low), yY(Y_high)
    s = 1.0 if yh > yl else -1.0
    H, L = T + ROOF_HIGH - COPING_H - 0.10, T + ROOF_LOW - COPING_H - 0.10
    y1, y2 = yl + s * C.PW, yh - s * C.PW
    k = (H - L) / (y2 - y1)
    return (lambda y: L + (y - y1) * k), abs(k)


PAVS = {'MN': (TM, MN1, MN0), 'MS': (TM, MS0, MS1), 'SN': (TS, SN1, SN0), 'SS': (TS, SS0, SS1)}
ROOF = {k: roof_plane(*v) for k, v in PAVS.items()}
TILE = 0.090
UNDER = BU.total(BU.ROOF_TILE_UNDER)        # 0.260


def roof_under(p):
    """Underside of the tiles (top of the R1 layers) z(x, y) of pavilion p."""
    f, k = ROOF[p]
    kk = math.sqrt(1 + k * k)
    return lambda x, y: f(y) - TILE * kk


def roof_ceiling(p):
    """Finished sloped ceiling (bottom of the R1 lining) z(x, y)."""
    f, k = ROOF[p]
    kk = math.sqrt(1 + k * k)
    return lambda x, y: f(y) - (TILE + UNDER) * kk


VAULT_R0 = CORE_VAULT_R - 0.002                          # copper skin 2 mm
VAULT_RIN = VAULT_R0 - BU.total(BU.ROOF_VAULT_UNDER)     # finished soffit radius
VAULT_ZC = {'M': TM + CORE_CROWN - CORE_VAULT_R, 'S': TS + CORE_CROWN - CORE_VAULT_R}


class _Vault:
    """Finished vault soffit z(x, y), curved across x."""
    curved = True

    def __init__(self, xc, row):
        self.xc, self.zc = xc, VAULT_ZC[row]

    def __call__(self, x, y):
        return self.zc + math.sqrt(max(VAULT_RIN ** 2 - (x - self.xc) ** 2, 0.0))


def _bar(bm, p, q, d):
    """Square bar of side d from p to q."""
    p, q = Vector(p), Vector(q)
    ax = q - p
    if ax.length < 1e-6:
        return
    n = ax.normalized()
    ref = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    u = n.cross(ref).normalized() * (d / 2)
    v = n.cross(u).normalized() * (d / 2)
    cs = [-u - v, u - v, u + v, -u + v]
    a = [bm.verts.new(p + c) for c in cs]
    b = [bm.verts.new(q + c) for c in cs]
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))


def wall(kit, layers, A, B, z0, top, doors=(), prefix='Wall', offset=0.0):
    """Straight layered wall on the plan line A -> B (centre line, shifted
    `offset` m to the left), from z0 to `top` (a level, or z(x, y) at both
    ends: a sloping top along the wall); doors [(s, w, head)] leave openings
    centred s m from A. Layers from the left face (A -> B) to the right."""
    A, B = Vector(A), Vector(B)
    L = (B - A).length
    if L < 1e-4:
        return
    ta, tb = (top(A.x, A.y), top(B.x, B.y)) if callable(top) else (top, top)
    out = [(0.0, z0)]
    for s_c, w, head in sorted(doors):
        out += [(s_c - w / 2, z0), (s_c - w / 2, head), (s_c + w / 2, head), (s_c + w / 2, z0)]
    out += [(L, z0), (L, tb), (0.0, ta)]
    t_left = sum(t for _, _, t in layers) / 2 + offset
    for elem, mat, t in layers:
        if mat is not None:
            I.oprism(kit(f'{prefix}{elem}', mat), A, B, out, t_left - t, t_left)
        t_left -= t


def rect_minus(l0, l1, z0, holes):
    """Pieces (u0, u1, za, zb | None = up to the top) of the strip [l0, l1] x
    [z0, top] minus the hole rectangles (u0, u1, za, zb)."""
    hs = [(max(u0, l0), min(u1, l1), za, zb) for u0, u1, za, zb in holes if min(u1, l1) - max(u0, l0) > 1e-4]
    xs = sorted({l0, l1} | {h[0] for h in hs} | {h[1] for h in hs})
    cols = []
    for ua, ub in zip(xs[:-1], xs[1:]):
        if ub - ua < 1e-5:
            continue
        mid = (ua + ub) / 2
        iv = sorted((za, zb) for u0, u1, za, zb in hs if u0 < mid < u1)
        merged = []
        for za, zb in iv:
            if merged and za <= merged[-1][1] + 1e-6:
                merged[-1] = (merged[-1][0], max(merged[-1][1], zb))
            else:
                merged.append((za, zb))
        segs, cur = [], z0
        for za, zb in merged:
            if zb <= cur + 1e-6:
                continue
            if za > cur + 1e-5:
                segs.append((round(cur, 6), round(za, 6)))
            cur = max(cur, zb)
        segs.append((round(cur, 6), None))
        if cols and abs(cols[-1][1] - ua) < 1e-6 and cols[-1][2] == segs:
            cols[-1][1] = ub
        else:
            cols.append([ua, ub, segs])
    return [(ua, ub, za, zb) for ua, ub, segs in cols for za, zb in segs]


def _hollow(ctx, body, volumes):
    """interior.hollow with the cutter's touching shells kept apart (no merge
    by distance: welded coincident vertices make the cutter non-manifold)."""
    if not len(volumes.faces):
        volumes.free()
        return
    cutter = geo.object_from_bmesh(volumes, f'{body.name}_CutIntMS', ctx.cutters, merge=False)
    mod = body.modifiers.new('Bool_Interior', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.use_self = True
    mod.object = cutter
    geo.apply_modifiers(body)
    geo.cleanup(body, dist=1e-6, recalc=False)


def side_kind(a, s):
    """What bounds dwelling side s of house a: 'end' (block end / slot face),
    'joint', 'campo' (party wall E 35.5 / 48.5) or 'party'."""
    for b in BLOCKS.values():
        if any(abs(a + s * 3.22 - f) < 1e-6 for f in b['faces']):
            return 'end'
    E = a + 3 * s
    if any(abs(E - j) < 1e-6 for j in C.JOINT_E):
        return 'joint'
    if any(abs(E - c) < 1e-6 for c in CAMPO['e']):
        return 'campo'
    return 'party'
