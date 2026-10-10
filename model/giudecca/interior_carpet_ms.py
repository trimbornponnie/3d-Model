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
      landing, south bedroom to the W5 wall at Y 14.936 -> 15.064;
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
end walls 0.37, joint leaves 0.185) with the insulated lining (55) on cold
faces and plaster (15) on interior masonry; the axis and party walls (W5),
the core spine (W4), partitions (W7), cellar partitions (W8) and the two
row-dividing walls are separate layered objects.  Floors F1 / F2 / F3 / F4
per room on one structural slab per storey; R1 under the tiles, R2 under the
core vaults (the copper lens cut to a 2 mm skin), R3 on the notch terraces,
the M/S joint deck and the campo strip.  The wall linings are built with the
window openings (and their joinery pockets) left out, so no boolean is
needed on them.

Windows E / E1 of these bodies use the joinery engine without its sill board
and lintel (types EM / E1M): one lintel, one sill block and one board span
both lights of a two-light (the engine's per-light blocks overlapped under the
mullion) and the board stands 2 mm above the sill block (window_extras), which
removes the engine's coplanar faces there; the radiator niches under the
finestre tipo get plastered jambs and top and the parquet runs into them.

Stairs (as interior_carpet_north): RC flights with oak treads and risers, PL
inside the band, plaster under the soffits, a plastered string on the open
side and a plate on the top end under the upper hall's ceiling; the slab
edges round the wells are plastered (corridor edge, spine strip, open end
edges) with the parquet run over them (HouseBase.flight, well_edges).

Deviations from the 1:50 plans, all to keep the verified exterior: the roof
planes (tile top T + 2.68 at the low wall) give ceilings about 0.2 lower than
the drawn T + 2.53 + 0.34 s; the middle row's end wall toward the campo stays
at E 35.5 / 48.5 (rooms 0.32 narrower than drawn); the campo strip's north
wall stays at Y 15.0 (the campo houses' L1 joint rooms 0.24 shorter); the
cantine front is 0.28 at Y 7.98 -> 8.15 (drawn 7.92 -> 8.09); the bay walls
are W7 wet throughout (drawn RC in the joint strips); the core vault soffit
is the model's (R 5.69 from the exterior's crown), so the beams over the
core openings sit at T + 2.12 and the south-row landing door is 2.05 high.

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
import os
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
                     NOTCH_HALF, PASSAGE_M, ROOF_HIGH, ROOF_LOW, ROWS, SLAB, WALL)

M = MODULE
WM = WALL / M                       # W1 masonry 0.395 in modules
LIN = BU.LINING_T                   # 0.055 insulated lining
PL = 0.015                          # plaster on interior masonry
EW = C.END_WALL                     # 0.37 block-end / slot / campo end walls (as the exterior's hollows)
LEAF = C.GAP / 2 + 0.185            # 0.23: joint line -> face of the joint leaf (W6)
EPS = 0.02
Z0, Z1, Z2 = FLOORS[0], FLOORS[1], FLOORS[2]
S1, S2 = Z1 - SLAB, Z2 - SLAB       # raw soffits 2.71 / 5.72
SOFF = {Z0: S1, Z1: S2}
GF = BU.GF_SOFFIT                   # -0.32: ground-floor slab soffit (F3, SE 63)
GF_TOP = GF + 0.20                  # -0.12: its top
TM, TS = ROWS['M']['T'], ROWS['S']['T']

# ------------------------------------------------------------ plan (modules)
MN0, MN1 = ROWS['M']['npav']        # 7.776, 10.224
MS0, MS1 = ROWS['M']['spav']        # 12.776, 15.224
SN0, SN1 = ROWS['S']['npav']        # 15.776, 18.224
SS0, SS1 = ROWS['S']['spav']        # 20.776, 23.224
MNI0, MNI1 = MN0 + WM, MN1 - WM     # masonry faces 8.015, 9.985
MSI0, MSI1 = MS0 + WM, MS1 - WM     # 13.015, 14.985
SNI0, SNI1 = SN0 + WM, SN1 - WM     # 16.015, 17.985
SSI0, SSI1 = SS0 + WM, SS1 - WM     # 21.015, 22.985
JN0, JN1 = C.JOINTS['NM'][0], C.JOINTS['NM'][1]     # 7.224, 7.776
JS0, JS1 = C.JOINTS['MS'][0], C.JOINTS['MS'][1]     # 15.224, 15.776
DECK = C.JOINTS['MS'][2]            # 6.15
LF = LIN / M                        # lining in modules
# middle row
Y_DIVN0 = 6.906                     # L1 dividing wall to the north row (interior_carpet_north L1_SOUTH)
Y_DIVN1 = Y_DIVN0 + 0.21 / M        # 7.033
Y_FRONT = C.CORRIDOR_NM[1]          # 7.98: cantine front (the exterior's corridor face)
Y_CELL = Y_FRONT + 0.28 / M         # 8.150: cells (front wall 0.28, n42 SE 56)
Y_THIN = 10.08                      # thin wall middle cell | core (n11, n18)
Y_TOPM = 10.145                     # top risers of flights A and B (n10, n67)
Y_BATHM = 8.82                      # L1 bath | hall partition (W7 wet), n67
LM0, LM1 = C.LANDING_M              # 8.95, 9.132: L2 cross wall terrace | hall (core body)
Y_LPM = MSI0 + LF                   # 13.048: L1 landing | south bedroom partition, south face
Y_DIVS = 15.0                       # L1 dividing wall middle | south row, centre (n67 14.94 -> 15.06)
Y_DIVS0, Y_DIVS1 = Y_DIVS - 0.105 / M, Y_DIVS + 0.105 / M
Y_KDOOR_M = 9.66                    # L2 kitchen door centre (n10 9.40 -> 9.87)
Y_BDOOR_M = 9.66                    # L1 north bedroom door centre (n67 9.42 -> 9.90)
# south row
Y_CEL0, Y_CEL1 = 15.26, 15.90       # cellars (n11, n76)
Y_STEP = (SN0, SN0 + 0.18, SN0 + 0.36)     # porch -> vestibule risers, 3 x 0.15 (n11 15.82 / 16.00 / 16.18)
Y_DW0 = 17.0                        # door wall, vestibule side (n11)
Y_DWM = Y_DW0 + 0.26 / M            # 17.158: its masonry face on the lobby side (W3: 26 brick + lining, SE 65)
Y_FOOTS = 18.20                     # first riser of the south flight (n11, n18)
Y_BATHS = 16.845                    # L1 bath | hall partition (n67 16.80 -> 16.86)
Y_LPS = SSI0 + LF                   # 21.048: L1 landing | south bedroom partition, south face
Y_KDOOR_S = 17.66                   # L0 kitchen door centre (n11 17.45 -> 17.92)
Y_BDOOR_S = 17.64                   # L1 north bedroom door centre (n67 17.40 -> 17.88)
CS0, CS1 = C.CAMPO_SOUTH['y']       # 15.0, 15.776: campo south strip
CSI = CS0 + WM                      # 15.239: its L1 north wall, masonry face
CS_ARC = CS0 + C.CAMPO_SOUTH['arcade_t'] / M     # 15.182: L0 arcade wall, inner face
CS_PAR = CS0 + C.CAMPO_SOUTH['parapet_t'] / M    # 15.152: deck parapet, inner face
# across (metres from the house axis)
D_AX = 0.105                        # axis wall half thickness (W5 0.21 / spine)
D_CORE = C.CORE_W / 2 - 0.28        # 1.77: core wall masonry face (render 0.02 + brick 0.26)
D_BAND = 0.87                       # flight | corridor (n30 "1,65" = flight + corridor)
D_KIT = NOTCH_HALF + WALL           # 1.88: L2 kitchen side / notch side wall face (as interior_carpet_north)
D_BAY = 1.91                        # L1 bay wall centre (W7 wet 1.835 -> 1.985, n67 1.84 -> 1.98)
T_WET = BU.total(BU.PARTITION_WET)  # 0.15
T_PART = BU.total(BU.PARTITION)     # 0.11
D_PORCH = 1.50                      # porch / vestibule half width (n76)
D_CELL_S = 1.97                     # south-row cellar, axis side (porch side wall 0.47)
D_KM = 1.915                        # vestibule side wall, kitchen-side masonry face; lobby | kitchen partition centre
D_KF = D_KM + LIN                   # 1.97: kitchen face (n11)
D_PARTY = 3 * M                     # 4.95
D_FACE = 3.22 * M                   # 5.313: block end / slot face
D_PIER = 0.26                       # porch axis pier half width (n76 "52")
D_PORCHO = 1.48                     # porch -> vestibule openings 0.26 -> 1.48 (n76 "1,22")
Z_BEAM_M = TM + 2.12                # L2 opening core -> living, beam soffit (at the vault springing, SE 59)
Z_BEAM_S = TS + 2.12                # L1 openings core <-> pavilions, beam soffit
Z_CELL = -0.32                      # cellar floor (F4, SE 63)

# doors: opening = leaf + 2 x 0.025 casing (bath leaf 0.70 "70/210", rooms 0.80, n67)
DOOR_ROOM, DOOR_BATH, DOOR_HEAD = 0.85, 0.75, 2.10
PARK_DEG = 60.0                     # doors hinged next to a court window: parked clear of the glazing
DOOR_HEAD_S = 2.05                  # south row L1 landing | bedroom door, under the beam at T + 2.12 (n30 ~5.14)
D_BATHDOOR = 1.305                  # bath doors, centre (n67 +0.91 -> +1.70)
D_SDOOR = 1.22                      # south bedroom doors, centre (n67, n49 +0.91 -> +1.70; 6 cm toward the
                                    # axis so the architrave clears the core wall's lining)
PORT = dict(d=(0.305, 1.215), h=2.07)          # portoncino 0.91 x 2.07 (SE 65, n11)
CELLAR = dict(w=0.775, z0=-0.32, z1=1.73)      # porte cantine "77,5/205" (SE 56, SE 65)
CWIN = dict(d=(0.145, 0.92), z0=1.18, z1=1.73)  # finestre cantine "77,5/55" (n42)
CDOORS = ((2.38, 3.155), (3.445, 4.22))        # outer-cell doors (n42 2.365 -> 3.17 / 3.43 -> 4.235)
CELL_DOOR = (0.25, 0.93)            # middle cell <- core door, thin wall (n11 "70/2,10")
TER_M = dict(d=(0.58, 1.32), h=2.05)           # L2 hall -> notch terrace door (n10)
PASS_STEPS = dict(d=1.80, y=(13.40, 13.58, 13.76))   # landing + 3 steps in the passage (n11, n18)

# flights (15 risers per storey, 14 goings: n10 / n67 / n11, n18)
N_RISERS = 15
TREAD_MAT = 'M_DoorLeaf'             # oak stair treads, matching the parquet (layers.md S1; as towers / schiera)
FL_WAIST, FL_TREAD, FL_NOSE, FL_RISER = 0.16, 0.03, 0.02, 0.015   # waist, oak tread / nosing / riser (S1)
FL_GAP = 0.003                      # flight 3 mm off the spine face (no coplanar faces)
GOING_M = 2.0 * M / 14              # 0.2357
GOING_S = 0.235
Y_FOOTM = Y_TOPM + 14 * GOING_M / M     # 12.145
Y_TOPS = Y_FOOTS + 14 * GOING_S / M     # 20.194
PARQ = BU.FLOOR_INT[0][2]           # 0.015 parquet

# stacks
SPINE = [('Plaster', 'M_PlasterInt', 0.015), ('RC', 'M_Structure', 0.18), ('Plaster', 'M_PlasterInt', 0.015)]
FL_INT = BU.FLOOR_INT[:-1]          # parquet / screed / fill on the slab (F1)
FL_OPEN = BU.FLOOR_OPEN[:-1]        # parquet / screed / insulation (F2, over unheated or open air)
FL_GF = BU.FLOOR_GF[:-1]            # F3 on the ground slab
FL_HALL = [('HallStone', 'M_Stone', 0.03), ('HallScreed', 'M_Screed', 0.09)]   # shared vestibule
PLASTER = [('Plaster', 'M_PlasterInt', PL)]
TERR = BU.TERRACE[:-1]              # R3 layers on the slab, finish z_f + 0.13


# ------------------------------------------------------------ joinery types
def _register_types() -> None:
    """Local opening types (added to joinery.TYPES; the engine is not edited):
    PM the portoncino in the 0.26-0.37 walls of the cores and the vestibule
    (frame behind the reveal, no W1 lintel), DM the glazed garden / terrace
    doors in the 0.28-0.30 core walls (plain jamb, frame inside the wall)."""
    J.TYPES.setdefault('PM', dict(J.TYPES['P'], lintel=False))
    J.TYPES.setdefault('DM', dict(jamb='plain', door=True, leaves=1, bottom_rail=0.150, board=False,
                                  lintel=False, niche=False, frame_at=0.10))
    # windows E / E1 of these rows: the engine's joinery without the sill board and the lintel,
    # which are built here (one lintel over both lights of a two-light, the board 2 mm proud of
    # the sill block: no coplanar faces), see Run.prepare / window_extras
    J.TYPES.setdefault('EM', dict(J.TYPES['E'], board=False, lintel=False))
    J.TYPES.setdefault('E1M', dict(J.TYPES['E1'], board=False, lintel=False))


MY_BODIES = ('SM_Carpet_NorthPavM_', 'SM_Carpet_SouthPavM_', 'SM_Carpet_NorthPavS_', 'SM_Carpet_SouthPavS_',
             'SM_Carpet_CampoSouth')
FRAME_D = J.BASE['frame'][1]        # 0.065


def _has_niche(r):
    k = J.classify(r)
    return k is not None and r['kind'] == 'rect' and J.spec_for(k)['niche']


def window_pockets(r):
    """(u0, u1, z0, z1, d0, d1) of the brick the E-family windows' sill block
    and lintel replace (as joinery.pockets for E / E1), once per group of
    lights (the record flagged ms_lintel_build), and the radiator niche sunk
    PARQ below the floor for the parquet that runs into it."""
    if 'ms_lintel' not in r:
        return []
    u0, u1, z0, z1 = J.dims(r)
    zf = J.floor_of(z0)
    out = []
    if _has_niche(r):
        out.append((u0 - J.MAZ, u1 + J.MAZ, zf - PARQ, zf, J.STOP, J.FINISH + 0.05))
    if not r.get('ms_lintel_build'):
        return out
    U0, U1 = r['ms_lintel']
    if z0 - zf > 0.5:
        out.append((U0 - 0.12, U1 + 0.12, z0 - 0.13, z0, 0.115, J.FINISH + 0.05))
    out.append((U0 - 0.12, U1 + 0.12, z1, z1 + 0.13, 0.05, J.FINISH + 0.05))
    return out


def window_extras(kit, recs):
    """Sill blocks, window boards and lintels of the E-family windows (the
    engine's geometry for a stop jamb; the board 2 mm higher), one of each
    per group of lights: the pieces under the frames of neighbouring lights
    butt at the mullion (the engine's per-light blocks overlapped 0.10)."""
    STOP, MAZ, WALL_, FIN = J.STOP, J.MAZ, J.WALL, J.FINISH
    for r in recs:
        if not r.get('ms_lintel_build'):
            continue
        u0, u1, z0, z1 = J.dims(r)
        U0, U1 = r['ms_lintel']
        lights = r['ms_run']
        if z0 - J.floor_of(z0) > 0.5:
            sb = kit('SillBlocks', 'M_Concrete')
            I.face_box(sb, r, U0 - 0.12, U1 + 0.12, z0 - 0.13, z0, 0.115, STOP)
            I.face_box(sb, r, U0 - 0.12, U0 - MAZ, z0 - 0.13, z0, STOP, WALL_)
            I.face_box(sb, r, U1 + MAZ, U1 + 0.12, z0 - 0.13, z0, STOP, WALL_)
            for i, (a0, a1) in enumerate(lights):
                la = a0 - MAZ if i == 0 else max(a0 - MAZ, (lights[i - 1][1] + a0) / 2)
                lb_ = a1 + MAZ if i == len(lights) - 1 else min(a1 + MAZ, (a1 + lights[i + 1][0]) / 2)
                I.face_box(sb, r, la, lb_, z0 - 0.13, z0 - 0.025, STOP, WALL_)       # under the frame
                if i + 1 < len(lights):
                    nb = max(lights[i + 1][0] - MAZ, (a1 + lights[i + 1][0]) / 2)
                    if nb > lb_ + 1e-6:
                        I.face_box(sb, r, lb_, nb, z0 - 0.13, z0, STOP, WALL_)        # under the mullion
            I.face_box(kit('WindowBoards', 'M_Joinery'), r, U0 - MAZ - 0.02, U1 + MAZ + 0.02, z0 - 0.023, z0 + 0.002,
                       STOP + FRAME_D, FIN + 0.02)
        lb = kit('Lintels', 'M_Structure')
        I.face_box(lb, r, U0 - 0.12, U1 + 0.12, z1, z1 + 0.13, 0.05, STOP)
        I.face_box(lb, r, U0 - 0.12, U1 + 0.12, z1 + MAZ, z1 + 0.13, STOP, WALL_)
        I.face_box(lb, r, U0 - 0.12, U0 - MAZ, z1, z1 + MAZ, STOP, WALL_)
        I.face_box(lb, r, U1 + MAZ, U1 + 0.12, z1, z1 + MAZ, STOP, WALL_)


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


def _clip(poly, a, b, c):
    """Convex polygon (s, z) clipped to the half-plane a*s + b*z <= c."""
    out = []
    for i, P in enumerate(poly):
        Q = poly[(i + 1) % len(poly)]
        fp, fq = a * P[0] + b * P[1] - c, a * Q[0] + b * Q[1] - c
        if fp <= 1e-12:
            out.append(P)
        if (fp < -1e-12 and fq > 1e-12) or (fp > 1e-12 and fq < -1e-12):
            t = fp / (fp - fq)
            out.append((P[0] + t * (Q[0] - P[0]), P[1] + t * (Q[1] - P[1])))
    clean = []
    for q in out:
        if not clean or abs(q[0] - clean[-1][0]) > 1e-7 or abs(q[1] - clean[-1][1]) > 1e-7:
            clean.append(q)
    if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 1e-7 and abs(clean[0][1] - clean[-1][1]) < 1e-7:
        clean.pop()
    return clean


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


def outer(kind):
    """(d of the outer room boundary, side type) of a dwelling: the face of the
    party wall object (W), the plastered joint leaf (P) or the lined end wall
    (L); toward the campo the middle row has an exterior end wall, the south
    row an ordinary party wall."""
    if kind == 'end':
        return D_FACE - EW, 'L'
    if kind == 'joint':
        return D_PARTY - LEAF, 'P'
    if kind == 'campo':
        return D_PARTY - EW, 'L'
    return D_PARTY - D_AX, 'W'


def bound(k, E, inward, mode):
    """E of a part end. k: 'face' (block end / slot), 'campo' (the middle
    row's exterior end wall on the campo line), 'joint', 'abut' (continuous:
    the south row's joint zone on the campo line, a party wall). Modes:
    'room' storey cuts (masonry face; beyond the end at abutments), 'slab'
    slab objects (the end-wall face, the body end at joints / abutments),
    'cut' slab-zone cuts (beyond the body end at joints / abutments), 'wall'
    the dividing walls (the room face; the body end at abutments)."""
    if k in ('face', 'campo'):
        return E + inward * EW / M
    if k == 'joint':
        if mode in ('room', 'wall'):
            return E + inward * LEAF / M
        b = E + inward * C.GAP / 2 / M
        return b if mode == 'slab' else b - inward * EPS
    if mode in ('slab', 'wall'):
        return E
    return E - inward * EPS


def rng(p, mode, campo='campo'):
    k = lambda v: campo if v == 'campo' else v
    return bound(k(p.k0), p.E0, 1, mode), bound(k(p.k1), p.E1, -1, mode)


def ER(E0, E1, Y0, Y1):
    return I.rect(xE(E0), xE(E1), yY(Y0), yY(Y1))


def rec_rects(r):
    """(u0, u1, z0, z1) rectangles an opening takes out of the wall linings
    (as joinery.lining_cutter): the opening, joinery.lining_boxes (reveal
    pocket, niche, threshold; the lintel and the inner sill block stay behind
    the lining), the window board built here (window_extras) and the local
    thresholds (door_sills)."""
    kind = J.classify(r)
    if kind is None and r.get('through') is None:
        return []
    u0, u1, z0, z1 = J.dims(r)
    out = [(u0, u1, z0, z1)] + J.lining_boxes(r, kind, board=False)
    if 'ms_lintel' in r and z0 - J.floor_of(z0) > 0.5:
        U0, U1 = r['ms_lintel']                          # one board per group of lights (window_extras)
        out.append((U0 - J.MAZ - 0.02, U1 + J.MAZ + 0.02, z0 - 0.023, z0 + 0.002))
    if 'ms_lintel' in r and _has_niche(r):               # the parquet runs into the niche (plain_reveals)
        out.append((u0 - J.MAZ, u1 + J.MAZ, J.floor_of(z0) - PARQ, J.floor_of(z0)))
    th = sill_of(r, kind)
    if th is not None:
        out.append((u0, u1, th[0], z0))
    return out


# plain-jamb openings whose frame sits forward in the wall: depth of the
# finished inner face behind the outer face (masonry + lining)
REVEAL_T = PL                       # plaster return on the reveals


def reveal_depth(r, kind):
    """Finished-face depth behind the outer face for the plain-jamb openings
    whose reveal behind the frame would show bare brick: the stair windows K
    and the garden doors DM in the 0.28 core walls, the terrace doors DM in
    the 0.30 cross wall, the middle row's portoncini PM in the W1 passage
    wall; None for the others (the south row's PM frame stands at the
    finished face of its 0.26 door wall)."""
    t = r.get('target') or ''
    if kind == 'K' and t.startswith(('SM_Carpet_CoresM_', 'SM_Carpet_CoresS_')):
        return C.CORE_W / 2 - D_CORE + LIN
    if kind == 'DM':
        return (C.CORE_W / 2 - D_CORE if r['axis'] == 'x' else (LM1 - LM0) * M) + LIN
    if kind == 'PM' and t.startswith('SM_Carpet_SouthPavM_'):
        return abs(r['coord'] - yY(MS0)) + LIN          # the passage face is Y 13.0: wall 0.37
    return None


def sill_of(r, kind):
    """(z bottom, depth, material) of the threshold built here under a door
    whose floor would otherwise be the wall's bare top: the garden doors DM
    (RC soglia over the 10 cm step to the court, SE 53 C/D), the middle
    row's portoncini PM (stone, as the south row's) - both from the outer
    face to the finished inner face; the south row's PM (stone, the lobby's
    slab top up, to the finished face); the terrace doors DM (RC, from the
    hall's slab to the terrace level, built in HouseM.terrace)."""
    t = r.get('target') or ''
    u0, u1, z0, z1 = J.dims(r)
    if kind == 'DM' and r['axis'] == 'x':
        return z0 - 0.10, reveal_depth(r, kind), 'M_Concrete'
    if kind == 'DM':
        return Z2 - 0.10, reveal_depth(r, kind), None
    if kind == 'PM' and t.startswith('SM_Carpet_SouthPavM_'):
        return z0 - 0.03, reveal_depth(r, kind), 'M_Stone'
    if kind == 'PM':
        return GF_TOP, None, None
    return None


def door_sills(kit, recs):
    """The thresholds of sill_of() that are built from the record (the
    others belong to HouseM.terrace / HouseS.porch)."""
    for r in recs:
        kind = J.classify(r)
        th = sill_of(r, kind)
        if th is None or th[2] is None:
            continue
        u0, u1, z0, z1 = J.dims(r)
        I.face_box(kit('Thresholds', th[2]), r, u0, u1, th[0], z0, 0.0, th[1])


def sill_pockets(r):
    """Brick the thresholds of door_sills replace (hollowing cutter); under
    the garden doors 1 cm deeper, inside the court slab that runs under the
    core wall (no pocket floor coplanar with the court's top at -0.10)."""
    kind = J.classify(r)
    th = sill_of(r, kind)
    if th is None or th[2] is None:
        return []
    u0, u1, z0, z1 = J.dims(r)
    zb = th[0] - (0.01 if kind == 'DM' else 0.0)
    return [(u0, u1, zb, z0, -0.02, th[1] + 0.01)]


def plain_reveals(kit, recs):
    """Plaster returns (15) on the inner reveals of the plain-jamb openings
    of reveal_depth(): jambs and head from the back of the frame to the
    finished wall face (they also close the lining's cut edges), and the
    sill of the stair windows K (layers.md W2: reveals plastered; the 45 deg
    splay of the drawings is not modelled)."""
    bm = kit('WindowReveals', 'M_PlasterInt')
    t = REVEAL_T
    for r in recs:
        kind = J.classify(r)
        if 'ms_lintel' in r and _has_niche(r):
            # radiator niche under the finestre tipo: plaster on the side jambs and on the
            # niche top (the sill block's underside and the lining's cut edge) from the
            # joinery's back lining to the finished face; the parquet runs into the niche
            # (as interior_carpet_north / interior_towers)
            u0, u1, z0, z1 = J.dims(r)
            zf = J.floor_of(z0)
            da, db = J.STOP + LIN, J.FINISH
            a0, a1 = u0 - J.MAZ, u1 + J.MAZ
            for ua, ub in ((a0, a0 + t), (a1 - t, a1)):
                I.face_box(bm, r, ua, ub, zf, z0 - 0.13, da, db)
            I.face_box(bm, r, a0 + t, a1 - t, z0 - 0.13 - t, z0 - 0.13, da, db)
            I.face_box(kit('FloorParquet', 'M_Parquet', uv_rotate=45.0), r, a0, a1, zf - PARQ, zf, J.STOP, db)
            continue
        db = reveal_depth(r, kind)
        if db is None:
            continue
        sp = J.spec_for(kind)
        u0, u1, z0, z1 = J.dims(r)
        da = J._frame_depth(r, sp) + sp['frame'][1] + 0.002
        I.face_box(bm, r, u0, u0 + t, z0, z1, da, db)                 # jambs
        I.face_box(bm, r, u1 - t, u1, z0, z1, da, db)
        I.face_box(bm, r, u0 + t, u1 - t, z1 - t, z1, da, db)         # head
        if kind == 'K':
            I.face_box(bm, r, u0 + t, u1 - t, z0, z0 + t, da, db)     # sill


def _x_extent(o):
    xs = [v.co.x for v in o.data.vertices]
    return 36.0 - max(xs) / M, 36.0 - min(xs) / M          # E range


def _uniq(recs):
    """The records once each (by identity, order kept)."""
    seen, out = set(), []
    for r in recs:
        if id(r) not in seen:
            seen.add(id(r))
            out.append(r)
    return out


# ======================================================================= run
class Run:
    def __init__(self, ctx):
        self.ctx = ctx
        self.cut: dict[str, bmesh.types.BMesh] = {}
        self.body_recs: dict[str, list] = {}
        self.segs: list = []

    def obj(self, name):
        o = bpy.data.objects.get(name)
        return o if o is not None and o.type == 'MESH' else None

    def cutter(self, name):
        if name not in self.cut:
            self.cut[name] = bmesh.new()
        return self.cut[name]

    def cbox(self, name, x0, x1, y0, y1, z0, z1):
        if self.obj(name) is not None and abs(x1 - x0) > 1e-5 and abs(y1 - y0) > 1e-5 and z1 - z0 > 1e-5:
            geo.add_box(self.cutter(name), x0, x1, y0, y1, z0, z1)

    def cEY(self, name, E0, E1, Y0, Y1, z0, z1):
        self.cbox(name, xE(E0), xE(E1), yY(Y0), yY(Y1), z0, z1)

    def cprism(self, name, poly, z0, top):
        if self.obj(name) is not None:
            I.prism(self.cutter(name), poly, z0, top)

    def recs(self, name):
        if name not in self.body_recs:
            self.body_recs[name] = I.openings_of(name) if self.obj(name) is not None else []
        return self.body_recs[name]

    # ------------------------------------------------------------- prepare
    def prepare(self):
        """Opening types the classifier cannot know: the portoncini off the
        passage (PM), the court-garden doors in the middle-row cores (DM),
        the campo cellar doors (CD); the blind arches and recessed cellar
        fronts are keep_recess records (no joinery)."""
        y_pass = yY(PASSAGE_M[0])
        for r in geo.OPENINGS:
            t = r.get('target') or ''
            if t.startswith('SM_Carpet_SouthPavM_') and r['kind'] == 'rect' and r['axis'] == 'y' \
                    and abs(r['coord'] - y_pass) < 1e-6:
                r['type'] = 'PM'
            elif t.startswith('SM_Carpet_CoresM_') and r['kind'] == 'rect' and J.dims(r)[2] < 0.01:
                r['type'] = 'DM'
            elif t == 'SM_Carpet_CampoSouth' and r['kind'] == 'rect' and r['axis'] == 'x':
                r['type'] = 'CD'
        groups = {}
        for r in geo.OPENINGS:
            t = r.get('target') or ''
            if not t.startswith(MY_BODIES) or r.get('done'):
                continue
            k = J.classify(r)
            if k in ('E', 'E1') and r['kind'] == 'rect':
                r['type'] = 'EM' if k == 'E' else 'E1M'
                u0, u1, z0, z1 = J.dims(r)
                key = (t, r['axis'], round(r['coord'], 4), r['out'], round(z0, 3), round(z1, 3))
                groups.setdefault(key, []).append(r)
        for rs in groups.values():
            rs.sort(key=lambda r: J.dims(r)[0])
            runs, cur = [], [rs[0]]
            for r in rs[1:]:
                if J.dims(r)[0] - J.dims(cur[-1])[1] < 0.20:      # the lights of a two-light (0.14 mullion)
                    cur.append(r)
                else:
                    runs.append(cur)
                    cur = [r]
            runs.append(cur)
            for run in runs:
                span = (J.dims(run[0])[0], J.dims(run[-1])[1])
                lights = [J.dims(r)[:2] for r in run]
                for i, r in enumerate(run):
                    r['ms_lintel'] = span
                    r['ms_lintel_build'] = i == 0
                    r['ms_run'] = lights

    # --------------------------------------------------------------- vaults
    def vault_skin(self, block, row):
        """Cut the copper lens of the core vaults down to a 2 mm skin; the R2
        layers are built under it per house."""
        name = f'SM_Carpet_Vaults{row}_{block.capitalize()}'
        if self.obj(name) is None:
            return
        bm = self.cutter(name)
        T = TM if row == 'M' else TS
        z_lo = T + C.CORE_EAVE - 0.15
        ya, yb = (LM1 - 0.05, MS0 + 0.05) if row == 'M' else (SN1 - 0.05, SS0 + 0.05)
        for a in C.block_axes(block, row):
            xc = xE(a)
            arc = I._arc_band(xc, VAULT_ZC[row], VAULT_R0, VAULT_R0 - 0.1, D_CORE, 24)[:25]
            w = D_CORE + 0.005
            ze = VAULT_ZC[row] + math.sqrt(VAULT_R0 ** 2 - w * w)
            prof = [(xc - w, z_lo), (xc + w, z_lo), (xc + w, ze)] + list(reversed(arc)) + [(xc - w, ze)]
            geo.add_prism_y(bm, prof, yY(yb), yY(ya))

    # -------------------------------------------------------------- finish
    def hollow_all(self):
        for name, bm in self.cut.items():
            o = self.obj(name)
            if o is None:
                bm.free()
                continue
            recs = self.recs(name)
            J.add_pockets(bm, recs)
            for r in recs:
                for u0, u1, z0, z1, d0, d1 in window_pockets(r) + sill_pockets(r):
                    I.face_box(bm, r, u0, u1, z0, z1, d0, d1)
            _hollow(self.ctx, o, bm)
        self.cut = {}

    def finish(self):
        for S in self.segs:
            S.finish()


# =================================================================== segments
class SegBase:
    """Common parts of a row segment: kit, records, lining holes, finish."""
    row = '?'

    def __init__(self, R, seg):
        self.R, self.seg = R, seg
        self.kit = I.Kit(R.ctx, 'Carpet', f'{self.row}{seg.tag}', seg.col)
        self.new_recs: list = []
        self._lin = None

    def bodies(self):
        return []

    def core_name(self):
        return f'SM_Carpet_Cores{self.row}_{self.seg.block.capitalize()}'

    def all_recs(self):
        """Records of this segment: its bodies, the cores of its houses, the
        records registered here (each once: a record registered on a core
        before Run.recs cached that core's list is in both)."""
        R = self.R
        recs = [r for n in self.bodies() for r in R.recs(n)]
        xs = [xE(h.a) for h in self.houses]
        for r in R.recs(self.core_name()):
            c = r['coord'] if r['axis'] == 'x' else sum(J.dims(r)[:2]) / 2
            if any(abs(c - x) < 3.5 for x in xs):
                recs.append(r)
        return _uniq(recs + self.new_recs)

    def wall_holes(self, h, s, along, c, inward, l0, l1):
        """Opening rectangles (strip coordinates) on the wall whose masonry
        face is the strip's plane: along 'd' (plane Y = c, layers toward +Y if
        inward > 0) or 'Y' (plane d = c, layers toward +d)."""
        if self._lin is None:
            self._lin = self.all_recs()
        if along == 'd':
            axis, face, room = 'y', yY(c), -inward
        else:
            axis, face, room = 'x', h.X(s, c), -s * inward
        out = []
        for r in self._lin:
            if r['axis'] != axis or r['out'] != -room:
                continue
            dd = (r['coord'] - face) * r['out']
            if not 0.15 < dd < 0.62:
                continue
            for u0, u1, z0, z1 in rec_rects(r):
                if along == 'd':
                    a, b = sorted(((h.xa - u0) * s, (h.xa - u1) * s))
                else:
                    a, b = sorted((15.5 - u0 / M, 15.5 - u1 / M))
                if b > l0 and a < l1:
                    out.append((a, b, z0, z1))
        return out

    def register(self, face, u0, u1, z0, z1, target, kind):
        rec = geo.register(face, [(u0, z0), (u1, z0), (u1, z1), (u0, z1)], 'rect', u=(u0 + u1) / 2, z0=z0,
                           width=u1 - u0, height=z1 - z0, through=None, recess=0.0)
        rec['target'], rec['type'] = target, kind
        self.new_recs.append(rec)
        self._lin = None
        return rec

    def finish(self):
        t0 = time.time()
        recs = self.all_recs()
        todo = [r for r in recs if not r.get('done')]
        n = J.build_openings(self.kit, recs)
        window_extras(self.kit, todo)
        plain_reveals(self.kit, todo)
        door_sills(self.kit, todo)
        self.kit.flush()
        print(f'[carpet ms] {self.row}{self.seg.tag}: {n} openings, joinery + flush {time.time() - t0:.1f} s')


class SegM(SegBase):
    """The middle row of one segment (its normal part): NorthPavM, SouthPavM,
    JointNM below 5.72, the JointMS deck, the cores."""
    row = 'M'

    def __init__(self, R, seg, part):
        super().__init__(R, seg)
        self.p = part
        t = seg.tag
        self.np, self.sp = f'SM_Carpet_NorthPavM_{t}', f'SM_Carpet_SouthPavM_{t}'
        self.jn, self.jm = f'SM_Carpet_JointNM_{t}', f'SM_Carpet_JointMS_{t}'
        self.core = self.core_name()
        self.houses = [HouseM(self, a) for a in part.axes]

    def bodies(self):
        return [self.np, self.sp]

    def party_lines(self):
        p = self.p
        return [E for E in C.PARTY if p.E0 + 1e-6 < E < p.E1 - 1e-6 and not any(abs(E - j) < 1e-6 for j in C.JOINT_E)]

    def build(self):
        self.cantine()
        self.l1()
        self.l2()
        self.deck()
        self.passage_beam()
        for h in self.houses:
            h.build()
        self.walls()

    def passage_beam(self):
        """Fair-faced downstand beam along the passage's south side under the
        L1 slab (n11, n18: Y 14.75 -> 14.95; 0.36 deep as the portico beams,
        SE 56), the lintel of the south row's porches."""
        b0, b1 = rng(self.p, 'slab')
        I.prism(self.kit('PassageBeam', 'M_Concrete'), ER(b0, b1, 14.75, PASSAGE_M[1]), S1 - 0.36, S1)

    # ------------------------------------------------------------ cantine
    def cantine(self):
        """L0 cells behind the 0.28 front wall on the N/M corridor (n11, n42
        SE 56): 120 brick partitions on dE 0, +-1.65, +-3.30 and the party
        lines, F4 at -0.32, plastered ceilings under the L1 slab."""
        R, kit, p = self.R, self.kit, self.p
        lo, hi = rng(p, 'room')
        y0, y1 = Y_CELL, MNI1
        R.cEY(self.np, lo, hi, y0, y1, -0.75, S1)
        walls = sorted([a + d / M for a in p.axes for d in (-3.30, -1.65, 0.0, 1.65, 3.30)] + self.party_lines())
        walls = [w for w in walls if lo + 0.5 / M < w < hi - 0.5 / M]
        for w in walls:
            I.prism(kit('CellarBrick', 'M_Brick'), ER(w - 0.06 / M, w + 0.06 / M, y0, y1), Z_CELL - 0.32, S1)
        edges = [lo] + [v for w in walls for v in (w - 0.06 / M, w + 0.06 / M)] + [hi]
        for i in range(0, len(edges), 2):
            poly = ER(edges[i], edges[i + 1], y0, y1)
            I.floor_stack(kit, poly, Z_CELL, BU.FLOOR_CELLAR, prefix='')
            I.prism(kit('CeilingPlaster', 'M_PlasterInt'), poly, S1 - 0.01, S1)

    # ----------------------------------------------------------------- L1
    def l1(self):
        """L1 storey (2.71 -> 5.72) of the pavilions and of JointNM: slab zone
        (through the body ends at joints) and rooms; the rooms run across the
        N/M joint to the dividing wall and in SouthPavM to Y 15.0 (the south
        row cuts on from there)."""
        R, kit, p = self.R, self.kit, self.p
        lo, hi = rng(p, 'room')
        t0, t1 = rng(p, 'cut')
        b0, b1 = rng(p, 'slab')
        jn = R.obj(self.jn)
        if jn is not None:
            n0, n1 = _x_extent(jn)
            c0 = lo if lo > n0 + 1e-4 else n0 - EPS
            c1 = hi if hi < n1 - 1e-4 else n1 + EPS
            R.cEY(self.jn, n0 - EPS, n1 + EPS, JN0 - EPS, JN1 + EPS, S1 - 0.01, Z1 - 0.10)
            R.cEY(self.jn, c0, c1, JN0 - EPS, JN1 + EPS, Z1 - 0.10, S2)
            I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(n0, n1, JN0, JN1), S1, Z1 - 0.10)
        R.cEY(self.np, t0, t1, MN0 - EPS, MNI1, S1, Z1 - 0.10)
        R.cEY(self.np, lo, hi, MN0 - EPS, MNI1, Z1 - 0.10, S2)
        I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(b0, b1, MN0, MNI1), S1, Z1 - 0.10)
        R.cEY(self.sp, t0, t1, MSI0, Y_DIVS, S1, Z1 - 0.10)
        R.cEY(self.sp, lo, hi, MSI0, Y_DIVS, Z1 - 0.10, S2)
        I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(b0, b1, MSI0, Y_DIVS), S1, Z1 - 0.10)

    # ----------------------------------------------------------------- L2
    def l2(self):
        """L2: kitchens between the notches (NorthPavM) and the living rooms
        (SouthPavM) from the slab zone up to the tiles, their slabs and the R1
        layers under the tiles."""
        R, kit, p = self.R, self.kit, self.p
        lo, hi = rng(p, 'room')
        for g0, g1 in C.notch_gaps(lo, hi, p.axes, half=D_KIT):
            poly = ER(g0, g1, MNI0, MNI1)
            R.cprism(self.np, poly, S2, roof_under('MN'))
            I.prism(kit('FloorSlab', 'M_Structure'), poly, S2, Z2 - 0.10)
            I.sloped_stack(kit, poly, roof_under('MN'), BU.ROOF_TILE_UNDER, prefix='Roof', slope=ROOF['MN'][1])
        poly = ER(lo, hi, MSI0, MSI1)
        R.cprism(self.sp, poly, S2, roof_under('MS'))
        I.prism(kit('FloorSlab', 'M_Structure'), poly, S2, Z2 - 0.10)
        I.sloped_stack(kit, poly, roof_under('MS'), BU.ROOF_TILE_UNDER, prefix='Roof', slope=ROOF['MS'][1])

    # --------------------------------------------------------------- deck
    def deck(self):
        """M/S joint deck (R3, 6.15) over the south row's L1 rooms: slab 5.72
        -> 5.92 and the terrace layers between the end parapets, split by a
        low divider on each house axis (n10)."""
        R, kit, p = self.R, self.kit, self.p
        jm = R.obj(self.jm)
        if jm is None:
            return
        m0, m1 = _x_extent(jm)
        d0 = m0 + EW / M if p.k0 in ('face', 'campo') else m0
        d1 = m1 - EW / M if p.k1 in ('face', 'campo') else m1
        R.cEY(self.jm, d0 if d0 > m0 else m0 - EPS, d1 if d1 < m1 else m1 + EPS, JS0 - EPS, JS1 + EPS, S2, DECK + 0.20)
        I.prism(kit('FloorSlab', 'M_Structure'), ER(d0, d1, JS0, JS1), S2, Z2 - 0.10)
        dv = [(a - 0.10 / M, a + 0.10 / M) for a in p.axes]
        for g0, g1 in C.minus_ranges(d0, d1, dv):
            I.floor_stack(kit, ER(g0, g1, JS0, JS1), DECK, TERR, prefix='Terrace')
        for a in p.axes:
            I.prism(kit('TerraceWall', 'M_Brick'), ER(a - 0.10 / M, a + 0.10 / M, JS0, JS1), Z2 - 0.10, DECK + 0.83)
            I.prism(kit('TerraceCoping', 'M_Concrete'), ER(a - 0.12 / M, a + 0.12 / M, JS0, JS1), DECK + 0.83,
                    DECK + 0.95)

    # -------------------------------------------------------------- walls
    def walls(self):
        """Party walls (W5) at L1 and L2, the L1 dividing wall to the north
        row (W5, Y 6.906 -> 7.033)."""
        kit, p = self.kit, self.p
        lo, hi = rng(p, 'wall')
        for E in self.party_lines():
            x = xE(E)
            wall(kit, BU.WALL_SEP, (x, yY(Y_DIVN1)), (x, yY(MNI1)), Z1 - 0.10, S2, prefix='Sep')
            wall(kit, BU.WALL_SEP, (x, yY(MSI0)), (x, yY(Y_DIVS0)), Z1 - 0.10, S2, prefix='Sep')
            wall(kit, BU.WALL_SEP, (x, yY(MNI0)), (x, yY(MNI1)), Z2 - 0.10, roof_ceiling('MN'), prefix='Sep')
            wall(kit, BU.WALL_SEP, (x, yY(MSI0)), (x, yY(MSI1)), Z2 - 0.10, roof_ceiling('MS'), prefix='Sep')
        yc = (Y_DIVN0 + Y_DIVN1) / 2
        wall(kit, BU.WALL_SEP, (xE(lo), yY(yc)), (xE(hi), yY(yc)), Z1 - 0.10, S2, prefix='Sep')


class SegS(SegBase):
    """The south row of one segment: NorthPavS, SouthPavS, the cores, the
    L1 joint zone (SouthPavM's south wall, JointMS) and, in the campo
    houses, the campo south strip."""
    row = 'S'

    def __init__(self, R, seg):
        super().__init__(R, seg)
        self.p = seg.part()
        self.mp = C.middle_part(seg)
        _, self.cp = seg.split_campo()
        t = seg.tag
        self.ns, self.ss = f'SM_Carpet_NorthPavS_{t}', f'SM_Carpet_SouthPavS_{t}'
        self.sp, self.jm = f'SM_Carpet_SouthPavM_{t}', f'SM_Carpet_JointMS_{t}'
        self.cs = 'SM_Carpet_CampoSouth'
        self.core = self.core_name()
        self.houses = [HouseS(self, a) for a in self.p.axes]

    def bodies(self):
        return [self.ns, self.ss]

    def all_recs(self):
        recs = super().all_recs()
        xs = [xE(h.a) for h in self.houses if h.campo]
        for r in self.R.recs(self.cs):
            c = r['coord'] if r['axis'] == 'x' else sum(J.dims(r)[:2]) / 2
            if any(abs(c - x) < 5.4 for x in xs):
                recs.append(r)
        return _uniq(recs)

    def party_lines(self):
        p = self.p
        return [E for E in C.PARTY if p.E0 + 1e-6 < E < p.E1 - 1e-6 and not any(abs(E - j) < 1e-6 for j in C.JOINT_E)]

    def build(self):
        self.l0()
        self.l1()
        self.joint()
        for h in self.houses:
            h.build()
        self.walls()

    # ----------------------------------------------------------------- L0
    def l0(self):
        """L0 kitchens (NorthPavS beside the vestibules) and living rooms
        (SouthPavS): rooms from the ground slab's soffit (-0.32) to 2.71, the
        slab (F3) on the same footprint."""
        R, kit, p = self.R, self.kit, self.p
        lo, hi = rng(p, 'room')
        for g0, g1 in C.minus_ranges(lo, hi, [(a - D_KM / M, a + D_KM / M) for a in p.axes]):
            R.cEY(self.ns, g0, g1, SNI0, SNI1, GF, S1)
            I.prism(kit('FloorSlab', 'M_Structure'), ER(g0, g1, SNI0, SNI1), GF, GF_TOP)
        R.cEY(self.ss, lo, hi, SSI0, SSI1, GF, S1)
        I.prism(kit('FloorSlab', 'M_Structure'), ER(lo, hi, SSI0, SSI1), GF, GF_TOP)

    # ----------------------------------------------------------------- L1
    def l1(self):
        """L1 of both pavilions up to the tiles, the north wall zone of
        NorthPavS to the deck slab (5.72), slabs and the R1 layers."""
        R, kit, p = self.R, self.kit, self.p
        lo, hi = rng(p, 'room')
        t0, t1 = rng(p, 'cut')
        b0, b1 = rng(p, 'slab')
        for name, y0, y1, pav in ((self.ns, SNI0, SNI1, 'SN'), (self.ss, SSI0, SSI1, 'SS')):
            R.cEY(name, t0, t1, y0, y1, S1, Z1 - 0.10)
            poly = ER(lo, hi, y0, y1)
            R.cprism(name, poly, Z1 - 0.10, roof_under(pav))
            if pav == 'SN':
                # the shared vestibules' soffit fair-faced, as the porch in front (FloorSlabExposed)
                ves = [(a - D_PORCH / M, a + D_PORCH / M) for a in p.axes]
                for g0, g1 in C.minus_ranges(b0, b1, ves):
                    I.prism(kit('FloorSlab', 'M_Structure'), ER(g0, g1, y0, Y_DW0), S1, Z1 - 0.10)
                for v0, v1 in ves:
                    I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(v0, v1, y0, Y_DW0), S1, Z1 - 0.10)
                I.prism(kit('FloorSlab', 'M_Structure'), ER(b0, b1, Y_DW0, y1), S1, Z1 - 0.10)
            else:
                I.prism(kit('FloorSlab', 'M_Structure'), ER(b0, b1, y0, y1), S1, Z1 - 0.10)
            I.sloped_stack(kit, poly, roof_under(pav), BU.ROOF_TILE_UNDER, prefix='Roof', slope=ROOF[pav][1])
        R.cEY(self.ns, t0, t1, SN0 - EPS, SNI0, S1, Z1 - 0.10)
        R.cEY(self.ns, lo, hi, SN0 - EPS, SNI0, Z1 - 0.10, S2)
        I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(b0, b1, SN0, SNI0), S1, Z1 - 0.10)

    # -------------------------------------------------------------- joint
    def joint(self):
        """L1 across the M/S joint: in the middle part SouthPavM's south wall
        zone from the dividing wall (W5 on Y 15.0) and JointMS; in the campo
        houses the campo south strip to its north wall (W1), and its deck."""
        R, kit = self.R, self.kit
        if self.mp is not None:
            p = self.mp
            lo, hi = rng(p, 'room', 'abut')
            t0, t1 = rng(p, 'cut', 'abut')
            b0, b1 = rng(p, 'slab', 'abut')
            # at a campo end the middle row's end wall (E 35.5 / 48.5) faces the campo north
            # of the strip's north wall (Y 15.0): the dividing wall's zone is cut, and the
            # wall ends, at the party wall's room face (E +- 0.105), 0.105 of brick staying
            # on the facade; the joint zone south of the wall abuts the strip as before
            w0 = p.E0 + D_AX / M if p.k0 == 'campo' else bound(p.k0, p.E0, 1, 'wall')
            w1 = p.E1 - D_AX / M if p.k1 == 'campo' else bound(p.k1, p.E1, -1, 'wall')
            R.cEY(self.sp, t0, t1, Y_DIVS, MS1 + EPS, S1, Z1 - 0.10)
            R.cEY(self.sp, w0 if p.k0 == 'campo' else lo, w1 if p.k1 == 'campo' else hi, Y_DIVS0, Y_DIVS1,
                  Z1 - 0.10, S2)
            R.cEY(self.sp, lo, hi, Y_DIVS1, MS1 + EPS, Z1 - 0.10, S2)
            I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(b0, b1, Y_DIVS, MS1), S1, Z1 - 0.10)
            jm = R.obj(self.jm)
            if jm is not None:
                m0, m1 = _x_extent(jm)
                c0 = t0 if p.k0 == 'face' else m0 - EPS
                c1 = t1 if p.k1 == 'face' else m1 + EPS
                R.cEY(self.jm, c0, c1, JS0 - EPS, JS1 + EPS, S1, Z1 - 0.10)
                R.cEY(self.jm, lo if p.k0 == 'face' else m0 - EPS, hi if p.k1 == 'face' else m1 + EPS,
                      JS0 - EPS, JS1 + EPS, Z1 - 0.10, S2)
                e0 = b0 if p.k0 == 'face' else m0
                e1 = b1 if p.k1 == 'face' else m1
                I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(e0, e1, JS0, JS1), S1, Z1 - 0.10)
            wall(kit, BU.WALL_SEP, (xE(w0), yY(Y_DIVS)), (xE(w1), yY(Y_DIVS)), Z1 - 0.10, S2, prefix='Sep')
        if self.cp is not None and R.obj(self.cs) is not None:
            p = self.cp
            lo, hi = rng(p, 'room', 'abut')
            b0, b1 = rng(p, 'slab', 'abut')
            R.cEY(self.cs, lo, hi, CSI, CS1 + EPS, S1, S2)
            I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(b0, b1, CSI, CS1), S1, Z1 - 0.10)
            # deck R3 between the campo parapet, the slot-end parapet and JointMS's end parapet
            d0 = p.E0 + EW / M if p.k0 == 'face' else p.E0
            d1 = p.E1 - EW / M if p.k1 == 'face' else p.E1
            R.cEY(self.cs, d0 if p.k0 == 'face' else d0 - EPS, d1 if p.k1 == 'face' else d1 + EPS,
                  CS_PAR, CS1 + EPS, S2, DECK + 0.20)
            I.prism(kit('FloorSlab', 'M_Structure'), ER(d0, d1, CS_PAR, CS1), S2, Z2 - 0.10)
            I.floor_stack(kit, ER(d0, d1, CS_PAR, CS1), DECK, TERR, prefix='Terrace')

    # -------------------------------------------------------------- walls
    def walls(self):
        """Party walls (W5): L0 kitchens and living rooms, L1 from the
        dividing wall (or the campo strip) to the facades."""
        kit = self.kit
        for E in self.party_lines():
            x = xE(E)
            campo = any(abs(E - c) < 1e-6 for c in CAMPO['e'])
            wall(kit, BU.WALL_SEP, (x, yY(SNI0)), (x, yY(SNI1)), GF_TOP, S1, prefix='Sep')
            wall(kit, BU.WALL_SEP, (x, yY(SSI0)), (x, yY(SSI1)), GF_TOP, S1, prefix='Sep')
            y_n = Y_DIVS1
            if campo and self.R.obj(self.cs) is not None:
                # the half of the party wall on the campo house's side cuts into the strip's north wall
                inward = 1 if any(abs(E - c) < 1e-6 for c in (CAMPO['e'][0],)) else -1
                self.R.cEY(self.cs, E - EPS if inward > 0 else E - 0.105 / M - EPS,
                           E + 0.105 / M + EPS if inward > 0 else E + EPS, Y_DIVS1, CSI + EPS, Z1 - 0.10, S2)
            wall(kit, BU.WALL_SEP, (x, yY(y_n)), (x, yY(SNI0)), Z1 - 0.10, S2, prefix='Sep')
            wall(kit, BU.WALL_SEP, (x, yY(SNI0)), (x, yY(SNI1)), Z1 - 0.10, roof_ceiling('SN'), prefix='Sep')
            wall(kit, BU.WALL_SEP, (x, yY(SSI0)), (x, yY(SSI1)), Z1 - 0.10, roof_ceiling('SS'), prefix='Sep')


# ===================================================================== houses
class HouseBase:
    """Per-house helpers (s = +1 west, -1 east; d = metres from the axis)."""

    def __init__(self, S, a):
        self.S, self.R, self.kit, self.a = S, S.R, S.kit, a
        self.xa = xE(a)

    def X(self, s, d):
        return self.xa - s * d

    def rect(self, s, d0, d1, Y0, Y1):
        return I.rect(self.X(s, d0), self.X(s, d1), yY(Y0), yY(Y1))

    def cut(self, name, s, d0, d1, Y0, Y1, z0, z1):
        self.R.cbox(name, self.X(s, d0), self.X(s, d1), yY(Y0), yY(Y1), z0, z1)

    def P(self, s, d, Y):
        return (self.X(s, d), yY(Y))

    def prism(self, elem, mat, s, d0, d1, Y0, Y1, z0, z1):
        I.prism(self.kit(elem, mat), self.rect(s, d0, d1, Y0, Y1), z0, z1)

    def jamb_return(self, s, Y_w, z0, top):
        """Corner block d D_CORE-LIN..D_CORE, Y Y_w..Y_w+LF where the opening's jamb lining
        (facing -d) meets the end of the room's lining on the wall at Y = Y_w:
        adhesive and insulation stacked like the jamb lining, the board wrapped
        round both faces (jamb face and the room-side face at Y_w + LF)."""
        bd = BU.LINING[-1][2] / M
        self.strip(s, 'Y', D_CORE, -1, Y_w, Y_w + LF - bd, z0, top, BU.LINING)
        self.strip(s, 'Y', D_CORE, -1, Y_w + LF - bd, Y_w + LF, z0, top, [('LiningBoard', 'M_PlasterInt', LIN)])

    # -------------------------------------------------------------- rooms
    def cell(self, s, d0, d1, Y0, Y1, zf, sides, floor, ceil, gaps=None, z0=None, soff=None):
        """A room (or part of one): floor layers inside the finished faces,
        linings ('L') / plaster ('P') on its masonry sides ('W' a wall object,
        'O' open; (type, z) a finish from z up only), ceiling plaster
        ('flat'). ceil: 'flat', 'roof<pav>', 'vault', ('beam', z) or None
        (the strips then run to the raw soffit)."""
        kit = self.kit
        gaps = gaps or {}
        z0 = zf - 0.10 if z0 is None else z0
        soff = SOFF.get(zf, zf + BU.RAW_SOFFIT) if soff is None else soff

        def typ(k):
            v = sides[k]
            return (v, None) if isinstance(v, str) else v

        def ins(k):
            t, zfrom = typ(k)
            if zfrom is not None:
                return 0.0
            return LIN if t == 'L' else (PL if t == 'P' else 0.0)
        fd0, fd1 = d0 + ins('A'), d1 - ins('O')
        fY0, fY1 = Y0 + ins('N') / M, Y1 - ins('S') / M
        poly = self.rect(s, fd0, fd1, fY0, fY1)
        if floor is not None:
            I.floor_stack(kit, poly, zf, floor)
        if ceil == 'flat':
            I.prism(kit('CeilingPlaster', 'M_PlasterInt'), poly, soff - 0.01, soff)
        elif isinstance(ceil, tuple) and ceil[0] == 'beam':
            I.prism(kit('CeilingPlaster', 'M_PlasterInt'), poly, ceil[1] - 0.01, ceil[1])
        if isinstance(ceil, str) and ceil.startswith('roof'):
            top = roof_ceiling(ceil[4:])
        elif ceil == 'vault':
            top = _Vault(self.xa, self.S.row)
        elif isinstance(ceil, tuple):
            top = ceil[1]
        else:
            top = soff
        th = {k: (LIN if typ(k)[0] == 'L' else PL) for k in 'NSAO'}
        lay = lambda k: BU.LINING if typ(k)[0] == 'L' else PLASTER
        has = lambda k: typ(k)[0] in ('L', 'P')
        for k in 'NS':
            if not has(k):
                continue
            t, zfrom = typ(k)
            yA = Y0 if k == 'N' else Y1
            inward = 1 if k == 'N' else -1
            l0, l1 = d0, d1
            if zfrom is not None:           # a finish from a level runs between the side finishes
                l0 += th['A'] if has('A') and typ('A')[1] is None else 0.0
                l1 -= th['O'] if has('O') and typ('O')[1] is None else 0.0
            self.strip(s, 'd', yA, inward, l0, l1, zfrom if zfrom is not None else z0, top, lay(k), gaps.get(k, ()))
        for k in 'AO':
            if not has(k):
                continue
            t, zfrom = typ(k)
            dA = d0 if k == 'A' else d1
            inward = 1 if k == 'A' else -1
            ya = Y0 + (th['N'] / M if has('N') and typ('N')[1] is None else 0.0)
            yb = Y1 - (th['S'] / M if has('S') and typ('S')[1] is None else 0.0)
            self.strip(s, 'Y', dA, inward, ya, yb, zfrom if zfrom is not None else z0, top, lay(k), gaps.get(k, ()))

    def strip(self, s, along, c, inward, l0, l1, z0, top, layers, gaps=()):
        """Wall finish on a masonry face: along 'd' (face at Y = c, layers
        toward +Y if inward > 0) or along 'Y' (face at d = c, toward +d);
        from l0 to l1 (d metres or Y modules); the openings of the wall and
        the door gaps [(g0, g1, head)] are left out. Tops follow `top` (a level
        or z(x, y)); strips under the vault are split into short pieces."""
        kit = self.kit
        holes = [(g0, g1, z0 - 1.0, head) for g0, g1, head in gaps]
        holes += self.S.wall_holes(self, s, along, c, inward, l0, l1)
        pieces = rect_minus(l0, l1, z0, holes)
        vault = getattr(top, 'curved', False) and along == 'd'
        step = 0.25 if along == 'd' else 0.25 / M
        off = 0.0
        for elem, mat, t in layers:
            if mat is None:
                off += t
                continue
            bm = kit(f'Wall{elem}', mat)
            if along == 'd':
                a0, a1 = c + inward * off / M, c + inward * (off + t) / M
            else:
                a0, a1 = c + inward * off, c + inward * (off + t)
            a0, a1 = sorted((a0, a1))
            for ua, ub, za, zb in pieces:
                n = max(1, int(math.ceil(abs(ub - ua) / step))) if vault else 1
                for i in range(n):
                    q0, q1 = ua + (ub - ua) * i / n, ua + (ub - ua) * (i + 1) / n
                    poly = self.rect(s, q0, q1, a0, a1) if along == 'd' else self.rect(s, a0, a1, q0, q1)
                    if callable(top):
                        tmin = min(top(x, y) for x, y in poly)
                        if zb is not None and zb <= tmin:
                            zt = zb
                        else:
                            zt = top
                    else:
                        zt = top if zb is None else min(zb, top)
                    if callable(zt):
                        if za >= tmin - 1e-4:
                            continue
                    elif za >= zt - 1e-4:
                        continue
                    I.prism(bm, poly, za, zt)
            off += t

    def door_floor(self, s, along, c, pos, w, t, zf, layers):
        """Floor layers in a door opening (between the two rooms' floors)."""
        if along == 'Y':
            poly = self.rect(s, c - t / 2, c + t / 2, pos - w / 2 / M, pos + w / 2 / M)
        else:
            poly = self.rect(s, pos - w / 2, pos + w / 2, c - t / 2 / M, c + t / 2 / M)
        I.floor_stack(self.kit, poly, zf, layers)

    def balustrade(self, pts, zf, height=1.00):
        bm = self.kit('BalustradeRails', 'M_Steel')
        (x0, y0), (x1, y1) = pts
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(math.ceil(L / 1.0)))
        for zr, d in ((height, 0.04), (height / 2, 0.02), (0.10, 0.02)):
            _bar(bm, (x0, y0, zf + zr), (x1, y1, zf + zr), d)
        for i in range(n + 1):
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            _bar(bm, (x, y, zf), (x, y, zf + height), 0.025)

    def corridor_floor(self, s, Y0, Y1, zf):
        """F1 of a corridor beside the stair well: the parquet to the well
        edge, screed and fill PL short of it (well_edges plasters the edge)."""
        I.floor_stack(self.kit, self.rect(s, D_BAND, D_CORE - LIN, Y0, Y1), zf, FL_INT[:1])
        I.floor_stack(self.kit, self.rect(s, D_BAND + PL, D_CORE - LIN, Y0, Y1), zf - PARQ, FL_INT[1:])

    def well_edges(self, s, Y_a, Y_b, floors, foot_under=None):
        """Plaster (PL) on the slab edges round the stair well D_AX..D_BAND x
        Y_a..Y_b: the corridor edge (d = D_BAND, inside the corridor's slab,
        which stops PL short - the parquet runs over it), the spine strip's
        side (the slab's RC core is PL narrower than the spine wall's, whose
        plaster this continues), and the open end edges in `floors` [(Y, zf)]
        (in the well, PL proud of the slab, from the ceiling plaster below to
        the parquet, which runs over them); `foot_under` = (Y, zf, z_top): the
        edge under the foot of a flight whose foot plaster starts at z_top."""
        kit, h = self.kit, self
        pl = kit('StairPlaster', 'M_PlasterInt')
        pq = kit('FloorParquet', 'M_Parquet', uv_rotate=45.0)
        for zf in {zf for _, zf in floors} | ({foot_under[1]} if foot_under else set()):
            I.prism(pl, h.rect(s, D_BAND, D_BAND + PL, Y_a, Y_b), zf - SLAB, zf - PARQ)
            I.prism(pl, h.rect(s, D_AX - PL, D_AX, Y_a, Y_b), zf - SLAB, zf - 0.10)
        for Y, zf in floors:
            Y0, Y1 = (Y - PL / M, Y) if Y > (Y_a + Y_b) / 2 else (Y, Y + PL / M)
            I.prism(pl, h.rect(s, D_AX, D_BAND, Y0, Y1), zf - SLAB - 0.01, zf - PARQ)
            I.prism(pq, h.rect(s, D_AX, D_BAND, Y0, Y1), zf - PARQ, zf)
        if foot_under is not None:
            Y, zf, z_top = foot_under
            Y0, Y1 = (Y - PL / M, Y) if Y > (Y_a + Y_b) / 2 else (Y, Y + PL / M)
            I.prism(pl, h.rect(s, D_AX, D_BAND, Y0, Y1), zf - SLAB - 0.01, z_top)

    def flight(self, s, Y_foot, ydir, zf, rise, going, z_ceil):
        """One flight of 15 risers against the spine (FL_GAP off its plaster),
        PL inside the band, rising from Y_foot in the world y direction ydir
        from the finished level zf, with its finishes (flight_finishes) and
        rails (flight_rails). Returns the plaster underside at the foot."""
        I.flight(self.kit, self.P(s, D_AX + FL_GAP, Y_foot), (0, ydir), D_BAND - D_AX - FL_GAP - PL, N_RISERS - 1,
                 rise, going, zf, waist=FL_WAIST, side=s * ydir, tread_top_last=True, tread_t=FL_TREAD,
                 nosing=FL_NOSE, tread_mat=TREAD_MAT)
        self.flight_rails(s, Y_foot, ydir, zf, rise, going)
        return self.flight_finishes(s, Y_foot, ydir, zf, rise, going, z_ceil)

    def flight_finishes(self, s, Y_foot, ydir, zf, rise, going, z_ceil):
        """Finishes of one flight (interior.flight's profile, as the north
        row's): oak risers (layers.md S1: tread 30 + riser 15; the top one
        closes the upper floor's edge), plaster (PL) under the soffit and the
        flat foot, a plastered string on the open side (the PL the flight
        stands inside the band) and a plaster plate on the top end where it
        hangs below the upper slab, up to the ceiling plaster at z_ceil. A
        flight standing on its floor (zf = Z0) has no finishes below it."""
        kit, h = self.kit, self
        n, g = N_RISERS - 1, going
        zt = zf - FL_TREAD
        slope = rise / g
        cos_a = math.cos(math.atan(slope))
        w_v = FL_WAIST / cos_a
        s_hit, s_top = w_v / slope, n * g
        pv = PL / cos_a                                  # the soffit plaster, vertically
        z_up = zf + N_RISERS * rise                      # upper finished floor
        y = lambda sv: yY(Y_foot) + ydir * sv
        da, db, dc = D_AX + FL_GAP, D_BAND - PL, D_BAND
        # region kept: half-planes a*s + b*z <= c: above the plaster's underside (and the floor)
        under = [(0.0, -1.0, -(zt - pv)), (slope, -1.0, slope * s_hit - zt + pv)]
        if zf == Z0:
            under.append((0.0, -1.0, -zf))

        def put(bm, poly, d0, d1):
            q = poly
            for a, b, c in under:
                q = _clip(q, a, b, c)
                if len(q) < 3:
                    return
            if abs(I.area(q)) > 1e-7:
                x0, x1 = sorted((h.X(s, d0), h.X(s, d1)))
                geo.add_prism_x(bm, I.ccw([(y(sv), z) for sv, z in q]), x0, x1)

        pl = kit('StairPlaster', 'M_PlasterInt')
        lo = zt - 1.0
        # soffit plaster (flat foot + slope), between the spine and the string
        put(pl, [(0.0, lo), (s_hit, lo), (s_hit, zt), (0.0, zt)], da, db)
        put(pl, [(s_hit, lo), (s_top, lo), (s_top, zt + slope * s_top - w_v), (s_hit, zt)], da, db)
        # string: one column per tread (to the tread top, under the nosing)
        for k in range(n):
            a = 0.0 if k == 0 else k * g - FL_NOSE
            b = s_top if k == n - 1 else (k + 1) * g - FL_NOSE
            put(pl, [(a, lo), (b, lo), (b, zf + (k + 1) * rise), (a, zf + (k + 1) * rise)], db, dc)
        # top end below the upper slab, into the upper hall (to its ceiling plaster)
        Y_top = Y_foot - ydir * s_top / M
        Ya, Yb = (Y_top - PL / M, Y_top) if ydir > 0 else (Y_top, Y_top + PL / M)
        I.prism(pl, h.rect(s, D_AX, dc, Ya, Yb), zt + slope * s_top - w_v - pv, z_ceil)
        # oak risers: 15 under each tread, the top one on the last tread up to the upper floor
        rb = kit('StairRisers', TREAD_MAT)
        for k in range(n):
            I.prism(rb, I.rect(h.X(s, da), h.X(s, db), y(k * g - FL_RISER), y(k * g)),
                    zf + k * rise, zf + (k + 1) * rise - FL_TREAD)
        I.prism(rb, I.rect(h.X(s, D_AX), h.X(s, dc), y(s_top - FL_RISER), y(s_top)), zf + n * rise, z_up)
        return zt - pv

    def flight_rails(self, s, Y_foot, ydir, zf, rise, going):
        """Raked balustrade on the open edge (D_BAND) and a handrail on the
        spine of a flight rising from Y_foot in the world y direction ydir."""
        rails = self.kit('BalustradeRails', 'M_Steel')
        s_end = (N_RISERS - 1) * going
        for d, posts in ((D_BAND - 0.025, True), (D_AX + 0.055, False)):
            def pt(sv, dz):
                z = zf + rise * (1 + (sv + 0.02) / going) + dz
                return (self.X(s, d), yY(Y_foot) + ydir * sv, z)
            _bar(rails, pt(-0.02, 0.90), pt(s_end, 0.90), 0.04)
            if posts:
                _bar(rails, pt(-0.02, 0.45), pt(s_end, 0.45), 0.02)
                for k in (0, 4, 8, 12):
                    sv = k * going + going / 2
                    zt = zf + (k + 1) * rise
                    _bar(rails, (self.X(s, d), yY(Y_foot) + ydir * sv, zt), pt(sv, 0.90), 0.025)
            else:
                for sv in (0.3, s_end - 0.3):        # wall brackets
                    q = pt(sv, 0.90)
                    _bar(rails, q, (self.X(s, D_AX + 0.003), q[1], q[2]), 0.015)


# ------------------------------------------------------------- middle row
class HouseM(HouseBase):
    """One H-house of the middle row: two mirrored Tipo B1 duplexes."""

    def __init__(self, S, a):
        super().__init__(S, a)
        self.kind = {s: side_kind(a, s) for s in (-1, 1)}

    def build(self):
        self.cuts()
        self.slabs()
        self.terrace()                 # registers the terrace doors (before the linings)
        for s in (-1, 1):
            self.cantina(s)
            self.cells(s)
            self.walls(s)
            self.doors(s)
            self.stairs(s)
        self.axis_walls()
        self.passage()
        I.vault_stack(self.kit, self.xa, VAULT_ZC['M'], VAULT_R0, D_CORE, yY(MS0), yY(LM1), BU.ROOF_VAULT_UNDER,
                      prefix='Vault', segments=24)

    # ------------------------------------------------------------ hollows
    def cuts(self):
        S, R, h = self.S, self.R, self
        core, np_, sp = S.core, S.np, S.sp
        D = D_CORE
        T = TM
        # the core: one void per house from the ground slab to the vault; its
        # L2 landing part in the N-pav notch (hall under the vault)
        h.cut(core, 1, -D, D, MN1 - EPS, MS0 + EPS, GF, T + 3.5)
        h.cut(core, 1, -D, D, LM1, MN1 + EPS, S2, T + 3.5)
        # N-pav court wall in the core width: L0 from the thin wall (9.985 -> 10.08
        # stays), L1 open to the hall, L2 hall up to the vault's outer surface
        h.cut(np_, 1, -D, D, Y_THIN, MN1 + EPS, GF, S1)
        h.cut(np_, 1, -D, D, MNI1, MN1 + EPS, S1, S2)
        arc = I._arc_band(self.xa, VAULT_ZC['M'], VAULT_R0, VAULT_R0 - 0.1, D, 24)[:25]
        prof = [(self.xa - D, S2), (self.xa + D, S2)] + list(reversed(arc))
        geo.add_prism_y(R.cutter(np_), prof, yY(MN1 + EPS), yY(LM1))
        # notch terrace deck zone (the notch above 6.15 is the exterior's)
        h.cut(np_, 1, -NOTCH_HALF, NOTCH_HALF, MNI0, LM0, S2, C.NOTCH_TERRACE + 0.20)
        # S-pav court wall in the core width: L1 open to the landing, L2 up to the beam
        h.cut(sp, 1, -D, D, MS0 - EPS, MSI0, S1, S2)
        h.cut(sp, 1, -D, D, MS0 - EPS, MSI0, S2, Z_BEAM_M)
        for s in (-1, 1):
            # middle cell door through the thin wall
            h.cut(np_, s, CELL_DOOR[0], CELL_DOOR[1], MNI1 - EPS, Y_THIN + EPS, GF_TOP, Z0 + DOOR_HEAD)
            # L2 kitchen door (hall | kitchen wall)
            h.cut(np_, s, D - 0.01, D_KIT + 0.01, Y_KDOOR_M - DOOR_ROOM / 2 / M, Y_KDOOR_M + DOOR_ROOM / 2 / M,
                  Z2 - 0.10, Z2 + DOOR_HEAD)
            # L2 terrace door through the cross wall (and the N-pav under it)
            for name in (np_, core):
                h.cut(name, s, TER_M['d'][0], TER_M['d'][1], LM0 - EPS, LM1 + EPS, Z2 - 0.10,
                      C.NOTCH_TERRACE + TER_M['h'])
            # the core's landing part runs on inside the N-pav beyond the notch
            # (overlapping bodies): the N-pav's masonry alone stays there
            h.cut(core, s, NOTCH_HALF, C.CORE_W / 2 + EPS, LM0 - EPS, MN1, S2 - 0.10, T + 3.5)
        # the cross wall starts 5 cm inside the N-pav's notch floor (6.10 / 6.15): stand it on the floor
        h.cut(core, 1, -NOTCH_HALF - EPS, NOTCH_HALF + EPS, LM0 - EPS, LM1 + EPS, S2 - 0.10, C.NOTCH_TERRACE)

    # -------------------------------------------------------------- slabs
    def slabs(self):
        """Core slabs: L0 ground slab (F3), L1 / L2 hall, corridors and landing
        (the well over the flights left open, the spine strip closed)."""
        kit, h = self.kit, self
        D = D_CORE
        sl = kit('FloorSlab', 'M_Structure')
        I.prism(sl, h.rect(1, -D, D, Y_THIN, MS0), GF, GF_TOP)
        for zf, y_hall in ((Z1, MNI1), (Z2, LM1)):
            zs = zf - SLAB
            I.prism(sl, h.rect(1, -D, D, y_hall, Y_TOPM), zs, zf - 0.10)
            # spine strip and corridors PL short of the well (their plaster: well_edges)
            I.prism(sl, h.rect(1, -D_AX + PL, D_AX - PL, Y_TOPM, Y_FOOTM), zs, zf - 0.10)
            for s in (-1, 1):
                I.prism(sl, h.rect(s, D_BAND + PL, D, Y_TOPM, Y_FOOTM), zs, zf - 0.10)
            I.prism(sl, h.rect(1, -D, D, Y_FOOTM, MSI0), zs, zf - 0.10)

    # ------------------------------------------------------------ cantina
    def cantina(self, s):
        """The cantina front of this dwelling side: doors of the two outer
        cells (CD), window of the middle cell (CW); steps up to the core door
        in the middle cell (n11, n18)."""
        S, R, h, kit = self.S, self.R, self, self.kit
        dN = outer(self.kind[s])[0]
        f = geo.Face('y', yY(Y_FRONT), 1)
        depth = (Y_CELL - Y_FRONT) * M + 0.05
        for d0, d1 in CDOORS:
            if d1 > dN - 0.10:
                continue
            u0, u1 = sorted((self.X(s, d0), self.X(s, d1)))
            S.register(f, u0, u1, CELLAR['z0'], CELLAR['z1'], S.np, 'CD')
            f.solid(R.cutter(S.np), [(u0, -0.60), (u1, -0.60), (u1, CELLAR['z1']), (u0, CELLAR['z1'])], depth,
                    outside=0.05)          # through the body's base: the threshold stands on the paving
            I.prism(kit('Thresholds', 'M_Concrete'), I.rect(u0, u1, yY(Y_FRONT), yY(Y_CELL)), -0.45, CELLAR['z0'])
        u0, u1 = sorted((self.X(s, CWIN['d'][0]), self.X(s, CWIN['d'][1])))
        S.register(f, u0, u1, CWIN['z0'], CWIN['z1'], S.np, 'CW')
        f.solid(R.cutter(S.np), [(u0, CWIN['z0']), (u1, CWIN['z0']), (u1, CWIN['z1']), (u0, CWIN['z1'])], depth,
                outside=0.05)
        st = kit('CellarSteps', 'M_Concrete')
        I.prism(st, h.rect(s, 0.06, 1.59, 9.67, 9.82), Z_CELL, Z_CELL + 0.16)
        I.prism(st, h.rect(s, 0.06, 1.59, 9.82, MNI1), Z_CELL, Z0)

    # -------------------------------------------------------------- cells
    def cells(self, s):
        h, kit = self, self.kit
        dN, tN = outer(self.kind[s])
        D = D_CORE
        cell = self.cell
        tb = T_WET / 2 / M
        # ---- L0 core: entrance hall, corridor, the space under flight A (F3)
        cell(s, D_AX, D, Y_THIN, MS0, Z0, dict(N='L', S='L', A='W', O='L'), FL_GF, None, z0=GF_TOP,
             gaps=dict(N=[(CELL_DOOR[0], CELL_DOOR[1], Z0 + DOOR_HEAD)]))
        cp = kit('CeilingPlaster', 'M_PlasterInt')
        for d0, d1, y0, y1 in ((D_BAND, D - LIN, Y_THIN + LF, Y_FOOTM), (D_AX, D - LIN, Y_FOOTM, MS0 - LF),
                               (D_AX, D_BAND, Y_THIN + LF, Y_TOPM)):
            I.prism(cp, h.rect(s, d0, d1, y0, y1), S1 - 0.01, S1)
        # ---- L1 (F2 over the cantine / corridor / passage, F1 in the core)
        cell(s, D_AX, D_BAY - T_WET / 2, Y_DIVN1, Y_BATHM - tb, Z1, dict(N='W', S='W', A='W', O='W'), FL_OPEN, 'flat')
        cell(s, D_AX, D_BAY - T_WET / 2, Y_BATHM + tb, MNI1, Z1, dict(N='W', S='O', A='W', O='W'), FL_OPEN, 'flat')
        cell(s, D_AX, D, MNI1, Y_TOPM, Z1, dict(N='O', S='O', A='W', O='L'), FL_INT, 'flat')
        cell(s, D_BAND, D, Y_TOPM, Y_FOOTM, Z1, dict(N='O', S='O', A='O', O='L'), None, 'flat')
        self.corridor_floor(s, Y_TOPM, Y_FOOTM, Z1)
        cell(s, D_AX, D, Y_FOOTM, Y_LPM - T_PART / M, Z1, dict(N='O', S='W', A='W', O='L'), FL_INT, 'flat')
        # the bay wall's end at the hall opening: the N-pav wall's cut end (1.77 -> 1.835) and the
        # hall lining's end are closed with a plaster return beside the bedroom door
        self.prism('WallPlaster', 'M_PlasterInt', s, D - LIN, D_BAY - T_WET / 2, MNI1 - PL / M, MNI1, Z1, S2 - 0.01)
        cell(s, D_AX, D, Y_LPM, Y_DIVS0, Z1, dict(N='W', S='W', A='W', O='O'), FL_OPEN, 'flat')
        cell(s, D, dN, MSI0, Y_DIVS0, Z1, dict(N='L', S='W', A='O', O=tN), FL_OPEN, 'flat')
        cell(s, D_BAY + T_WET / 2, dN, Y_DIVN1, MNI1, Z1, dict(N='W', S='L', A='W', O=tN), FL_OPEN, 'flat')
        # ---- L2 (F1)
        kd = (Y_KDOOR_M - DOOR_ROOM / 2 / M, Y_KDOOR_M + DOOR_ROOM / 2 / M, Z2 + DOOR_HEAD)
        cell(s, D_AX, D, LM1, Y_TOPM, Z2, dict(N='L', S='O', A='W', O='P'), FL_INT, 'vault', gaps=dict(O=[kd]))
        cell(s, D_BAND, D, Y_TOPM, Y_FOOTM, Z2, dict(N='O', S='O', A='O', O='L'), None, 'vault')
        self.corridor_floor(s, Y_TOPM, Y_FOOTM, Z2)
        cell(s, D_AX, D, Y_FOOTM, MS0, Z2, dict(N='O', S=('P', Z_BEAM_M), A='W', O='L'), FL_INT, 'vault')
        cell(s, D_AX, D, MS0, MSI0, Z2, dict(N='O', S='O', A='W', O='L'), FL_INT, ('beam', Z_BEAM_M))
        cell(s, D_AX, D, MSI0, MSI1, Z2, dict(N='O', S='L', A='W', O='O'), FL_INT, 'roofMS')
        cell(s, D, dN, MSI0, MSI1, Z2, dict(N='L', S='L', A='O', O=tN), FL_INT, 'roofMS')
        # living | landing opening: the jamb lining returns round the corner over the end of the
        # living room's north lining; the beam's plaster above runs up to that return
        self.jamb_return(s, MSI0, Z2, roof_ceiling('MS'))
        self.strip(s, 'd', MSI0, 1, D_AX, D - LIN, Z_BEAM_M, roof_ceiling('MS'), PLASTER)
        cell(s, D_KIT, dN, MNI0, MNI1, Z2, dict(N='P', S='L', A='L', O=tN), FL_INT, 'roofMN', gaps=dict(A=[kd]))

    # -------------------------------------------------------------- walls
    def walls(self, s):
        kit, h = self.kit, self
        # L1 bay wall (wet, the bath's plumbing), north bedroom door
        wall(kit, BU.PARTITION_WET, h.P(s, D_BAY, Y_DIVN1), h.P(s, D_BAY, MNI1), Z1 - 0.10, S2,
             doors=[((Y_BDOOR_M - Y_DIVN1) * M, DOOR_ROOM, Z1 + DOOR_HEAD)], prefix='Partition')
        # L1 bath | hall (wet)
        wall(kit, BU.PARTITION_WET, h.P(s, D_AX, Y_BATHM), h.P(s, D_BAY - T_WET / 2, Y_BATHM), Z1 - 0.10, S2,
             doors=[(D_BATHDOOR - D_AX, DOOR_BATH, Z1 + DOOR_HEAD)], prefix='Partition')
        # L1 landing | south bedroom
        y = Y_LPM - T_PART / 2 / M
        wall(kit, BU.PARTITION, h.P(s, D_AX, y), h.P(s, D_CORE, y), Z1 - 0.10, S2,
             doors=[(D_SDOOR - D_AX, DOOR_ROOM, Z1 + DOOR_HEAD)], prefix='Partition')

    def doors(self, s):
        kit, h = self.kit, self
        tc = (MNI1 + Y_THIN + LF) / 2          # thin wall + the hall's lining
        t_thin = (Y_THIN + LF - MNI1) * M
        # L0 middle cell <- hall: into the hall (south)
        dc = sum(CELL_DOOR) / 2
        I.door(kit, h.P(s, D_AX, tc), h.P(s, D_CORE, tc), dc - D_AX, CELL_DOOR[1] - CELL_DOOR[0], Z0 + DOOR_HEAD, Z0,
               t_thin - 0.002, hinge='a', swing=s)
        self.door_floor(s, 'd', tc, dc, CELL_DOOR[1] - CELL_DOOR[0], t_thin, Z0, FL_GF)
        # L1 bath: hinge at the bay wall, into the bath (north)
        I.door(kit, h.P(s, D_AX, Y_BATHM), h.P(s, D_BAY - T_WET / 2, Y_BATHM), D_BATHDOOR - D_AX, DOOR_BATH,
               Z1 + DOOR_HEAD, Z1, T_WET - 0.002, hinge='b', swing=-s)
        self.door_floor(s, 'd', Y_BATHM, D_BATHDOOR, DOOR_BATH, T_WET, Z1, FL_OPEN)
        # L1 north bedroom: bay wall, hinge at the S jamb, into the bedroom (parked at
        # PARK_DEG: at 90 deg the leaf stood 8 cm behind the court window's inner light)
        I.door(kit, h.P(s, D_BAY, Y_DIVN1), h.P(s, D_BAY, MNI1), (Y_BDOOR_M - Y_DIVN1) * M, DOOR_ROOM,
               Z1 + DOOR_HEAD, Z1, T_WET - 0.002, hinge='b', swing=-s, open_deg=PARK_DEG)
        self.door_floor(s, 'Y', D_BAY, Y_BDOOR_M, DOOR_ROOM, T_WET, Z1, FL_OPEN)
        # L1 south bedroom: into the bedroom (south)
        y = Y_LPM - T_PART / 2 / M
        I.door(kit, h.P(s, D_AX, y), h.P(s, D_CORE, y), D_SDOOR - D_AX, DOOR_ROOM, Z1 + DOOR_HEAD, Z1,
               T_PART - 0.002, hinge='a', swing=s)
        self.door_floor(s, 'd', y, D_SDOOR, DOOR_ROOM, T_PART, Z1, FL_INT)
        # L2 kitchen: hall | kitchen wall (masonry 1.77 -> 1.88, plaster / lining), into the kitchen
        d0, d1 = D_CORE - PL, D_KIT + LIN
        dk = (d0 + d1) / 2
        I.door(kit, h.P(s, dk, LM1), h.P(s, dk, MNI1), (Y_KDOOR_M - LM1) * M, DOOR_ROOM, Z2 + DOOR_HEAD, Z2,
               d1 - d0 - 0.002, hinge='b', swing=-s)
        self.door_floor(s, 'Y', dk, Y_KDOOR_M, DOOR_ROOM, d1 - d0, Z2, FL_INT)

    # ------------------------------------------------------------- stairs
    def stairs(self, s):
        """Flights A (L0 -> L1) and B (L1 -> L2) superimposed against the
        spine, rising north: 15 x 0.2007, 14 goings 0.236 (n10, n67, n11,
        n18), with their finishes (flight_finishes); balustrades on the open
        edge and round the well; the well's slab edges plastered (well_edges)."""
        h = self
        for zf, ztop, z_ceil in ((Z0, Z1, S1 - 0.01), (Z1, Z2, S2 - 0.01)):
            z_foot = self.flight(s, Y_FOOTM, 1, zf, (ztop - zf) / N_RISERS, GOING_M, z_ceil)
        # well edges: corridors and spine strip, the L2 landing's edge, the L1 edge under flight B's foot
        self.well_edges(s, Y_TOPM, Y_FOOTM, [(Y_FOOTM, Z2)], foot_under=(Y_FOOTM, Z1, z_foot))
        for zf in (Z1, Z2):
            self.balustrade([h.P(s, D_BAND + 0.03, Y_TOPM + 0.02 / M), h.P(s, D_BAND + 0.03, Y_FOOTM - 0.02 / M)], zf)
        self.balustrade([h.P(s, D_AX + 0.03, Y_FOOTM + 0.03 / M), h.P(s, D_BAND + 0.03, Y_FOOTM + 0.03 / M)], Z2)

    # ---------------------------------------------------------- axis walls
    def axis_walls(self):
        """Wall between the two dwellings: the RC spine in the core (W4), W5
        in the pavilions, per storey."""
        kit = self.kit
        P = lambda Y: (self.xa, yY(Y))
        wall(kit, SPINE, P(Y_THIN), P(MS0), GF_TOP, S1, prefix='Spine')
        wall(kit, BU.WALL_SEP, P(Y_DIVN1), P(MN1), Z1 - 0.10, S2, prefix='Sep')
        wall(kit, SPINE, P(MN1), P(MS0), Z1 - 0.10, S2, prefix='Spine')
        wall(kit, BU.WALL_SEP, P(MS0), P(Y_DIVS0), Z1 - 0.10, S2, prefix='Sep')
        zc = VAULT_ZC['M'] + VAULT_RIN + 0.002            # 2 mm into the vault lining board at the crown
        wall(kit, SPINE, P(LM1), P(MS0), Z2 - 0.10, zc, prefix='Spine')
        wall(kit, SPINE, P(MS0), P(MSI0), Z2 - 0.10, Z_BEAM_M, prefix='Spine')
        wall(kit, BU.WALL_SEP, P(MSI0), P(MSI1), Z2 - 0.10, roof_ceiling('MS'), prefix='Sep')

    # ------------------------------------------------------------ passage
    def passage(self):
        """Landing in front of the two portoncini and three precast steps down
        to the passage (-0.45), n11, n18, n20 "35/13"."""
        st = self.kit('PassageSteps', 'M_Concrete')
        d = PASS_STEPS['d']
        y0 = PASSAGE_M[0]
        for y1, z in zip(PASS_STEPS['y'], (Z0, Z0 - 0.15, Z0 - 0.30)):
            I.prism(st, self.rect(1, -d, d, y0, y1), C.Z_PAVING, z)
            y0 = y1

    # ------------------------------------------------------------ terrace
    def terrace(self):
        """L2 notch terrace (R3, 6.15) over the L1 baths and halls: slab,
        layers either side of the low axis divider, the terrace doors'
        thresholds and joinery (DM)."""
        S, kit, h = self.S, self.kit, self
        h.prism('FloorSlab', 'M_Structure', 1, -NOTCH_HALF, NOTCH_HALF, MNI0, LM0, S2, Z2 - 0.10)
        for s in (-1, 1):
            I.floor_stack(kit, h.rect(s, 0.10, NOTCH_HALF, MNI0, LM0), C.NOTCH_TERRACE, TERR, prefix='Terrace')
        h.prism('TerraceWall', 'M_Brick', 1, -0.10, 0.10, MNI0, LM0, Z2 - 0.10, C.NOTCH_TERRACE + 0.83)
        h.prism('TerraceCoping', 'M_Concrete', 1, -0.12, 0.12, MNI0, LM0, C.NOTCH_TERRACE + 0.83,
                C.NOTCH_TERRACE + 0.95)
        f = geo.Face('y', yY(LM0), 1)
        zs = C.NOTCH_TERRACE
        for s in (-1, 1):
            u0, u1 = sorted((self.X(s, TER_M['d'][0]), self.X(s, TER_M['d'][1])))
            S.register(f, u0, u1, zs, zs + TER_M['h'], S.core, 'DM')
            I.prism(kit('Thresholds', 'M_Concrete'), I.rect(u0, u1, yY(LM0), yY(LM1 + LF)), Z2 - 0.10, zs)


# -------------------------------------------------------------- south row
class HouseS(HouseBase):
    """One H-house of the south row: two mirrored Tipo B duplexes."""

    def __init__(self, S, a):
        super().__init__(S, a)
        self.campo = a in CAMPO_HOUSES
        self.kind = {s: ('party' if side_kind(a, s) == 'campo' else side_kind(a, s)) for s in (-1, 1)}

    def build(self):
        self.cuts()
        self.slabs()
        self.porch()                   # registers the entrance doors (before the linings)
        for s in (-1, 1):
            self.cellar(s)
            self.cells(s)
            self.walls(s)
            self.doors(s)
            self.stairs(s)
        self.axis_walls()
        I.vault_stack(self.kit, self.xa, VAULT_ZC['S'], VAULT_R0, D_CORE, yY(SS0), yY(SN1), BU.ROOF_VAULT_UNDER,
                      prefix='Vault', segments=24)

    # ------------------------------------------------------------ hollows
    def cuts(self):
        S, h = self.S, self
        core, ns, ss = S.core, S.ns, S.ss
        D = D_CORE
        h.cut(core, 1, -D, D, SN1 - EPS, SS0 + EPS, GF, TS + 3.5)
        # NorthPavS: lobby behind the door wall (Y 17.0 -> 17.158 stays), court
        # wall zone (L0, L1 up to the beam), vestibule, entrance doors
        h.cut(ns, 1, -D_KM, D_KM, Y_DWM, SNI1, GF, S1)
        h.cut(ns, 1, -D, D, SNI1 - EPS, SN1 + EPS, GF, S1)
        h.cut(ns, 1, -D, D, SNI1, SN1 + EPS, S1, Z_BEAM_S)
        h.cut(ns, 1, -D_PORCH, D_PORCH, SNI0, Y_DW0, GF, S1)
        for s in (-1, 1):
            h.cut(ns, s, PORT['d'][0], PORT['d'][1], Y_DW0 - EPS, Y_DWM + EPS, GF_TOP, Z0 + PORT['h'])
            if not self.campo:
                h.cut(ns, s, D_PIER, D_PORCHO, SN0 - EPS, SNI0 + EPS, -0.60, 2.00)
        # SouthPavS court wall zone (L0 open to the living room, L1 up to the beam)
        h.cut(ss, 1, -D, D, SS0 - EPS, SSI0 + EPS, GF, S1)
        h.cut(ss, 1, -D, D, SS0 - EPS, SSI0, S1, Z_BEAM_S)
        # porch through SouthPavM's south wall and JointMS (normal houses)
        if not self.campo:
            h.cut(S.sp, 1, -D_PORCH, D_PORCH, CS0 - EPS, MS1 + EPS, -0.60, S1)
            h.cut(S.jm, 1, -D_PORCH, D_PORCH, JS0 - EPS, JS1 + EPS, -0.60, S1)

    # -------------------------------------------------------------- slabs
    def slabs(self):
        kit, h = self.kit, self
        D = D_CORE
        sl = kit('FloorSlab', 'M_Structure')
        # L0 (F3): lobby, core strip, vestibule (beyond the steps)
        I.prism(sl, h.rect(1, -D_KM, D_KM, Y_DWM, SNI1), GF, GF_TOP)
        I.prism(sl, h.rect(1, -D, D, SNI1, SSI0), GF, GF_TOP)
        y_v = SNI0 if self.campo else Y_STEP[2]
        I.prism(kit('FloorSlabExposed', 'M_Concrete'), h.rect(1, -D_PORCH, D_PORCH, y_v, Y_DW0), GF, GF_TOP)
        # L1: hall in the court wall zone, corridors, spine strip, landing
        zs = S1
        I.prism(sl, h.rect(1, -D, D, SNI1, Y_FOOTS), zs, Z1 - 0.10)
        I.prism(sl, h.rect(1, -D_AX + PL, D_AX - PL, Y_FOOTS, Y_TOPS), zs, Z1 - 0.10)   # PL short: well_edges
        for s in (-1, 1):
            I.prism(sl, h.rect(s, D_BAND + PL, D, Y_FOOTS, Y_TOPS), zs, Z1 - 0.10)
        I.prism(sl, h.rect(1, -D, D, Y_TOPS, SSI0), zs, Z1 - 0.10)

    # ------------------------------------------------------------- cellar
    def cellar(self, s):
        """Cellar of this dwelling in the joint (n11, n76): F4 at -0.32,
        plastered ceiling; door in the porch side wall (SE 65 0.775 x 2.05,
        CD). In the campo houses the strip's cellars behind the arcade, with
        the exterior's doors."""
        S, R, h, kit = self.S, self.R, self, self.kit
        dN = outer(self.kind[s])[0]
        y_n = CS_ARC if self.campo else Y_CEL0
        if self.campo:
            h.cut(S.cs, s, D_CELL_S, dN, y_n, CS1 + EPS, -0.75, S1)
        else:
            h.cut(S.jm, s, D_CELL_S, dN, y_n, JS1 + EPS, -0.75, S1)
        h.cut(S.ns, s, D_CELL_S, dN, SN0 - EPS, Y_CEL1, -0.75, S1)
        poly = h.rect(s, D_CELL_S, dN, y_n, Y_CEL1)
        I.floor_stack(kit, poly, Z_CELL, BU.FLOOR_CELLAR, prefix='')
        I.prism(kit('CeilingPlaster', 'M_PlasterInt'), poly, S1 - 0.01, S1)
        if self.campo:
            return
        f = geo.Face('x', self.X(s, D_PORCH), s)
        yc = (Y_CEL0 + Y_CEL1) / 2
        u0, u1 = sorted((yY(yc) - CELLAR['w'] / 2, yY(yc) + CELLAR['w'] / 2))
        S.register(f, u0, u1, CELLAR['z0'], CELLAR['z1'], S.jm, 'CD')
        for name in (S.jm, S.ns):           # the door runs on into the N-pav's north wall (Y > 15.776)
            f.solid(R.cutter(name), [(u0, -0.60), (u1, -0.60), (u1, CELLAR['z1']), (u0, CELLAR['z1'])],
                    D_CELL_S - D_PORCH + 0.05, outside=0.05)
        y0, y1 = yc - CELLAR['w'] / 2 / M, yc + CELLAR['w'] / 2 / M
        h.prism('Thresholds', 'M_Concrete', s, D_PORCH, D_CELL_S, y0, y1, C.Z_PAVING, CELLAR['z0'])

    # -------------------------------------------------------------- cells
    def cells(self, s):
        h, kit = self, self.kit
        dN, tN = outer(self.kind[s])
        D = D_CORE
        cell = self.cell
        tb = T_WET / 2 / M
        # ---- L0 (F3)
        cell(s, D_KM, dN, SNI0, Y_DWM, Z0, dict(N='L', S='O', A='L', O=tN), FL_GF, 'flat', z0=GF_TOP)       # kitchen
        cell(s, D_KF, dN, Y_DWM, SNI1, Z0, dict(N='O', S='L', A='W', O=tN), FL_GF, 'flat', z0=GF_TOP)       # kitchen
        cell(s, D_AX, D_KM - T_PART / 2, Y_DWM, SNI1, Z0, dict(N='L', S='O', A='W', O='W'), FL_GF, 'flat',
             z0=GF_TOP)                                                                                      # lobby
        cell(s, D_AX, D, SNI1, SSI0, Z0, dict(N='O', S='O', A='W', O='L'), FL_GF, None, z0=GF_TOP)          # core
        cp = kit('CeilingPlaster', 'M_PlasterInt')
        for d0, d1, y0, y1 in ((D_BAND, D - LIN, SNI1, SSI0), (D_AX, D_BAND, SNI1, Y_FOOTS),
                               (D_AX, D_BAND, Y_TOPS, SSI0)):
            I.prism(cp, h.rect(s, d0, d1, y0, y1), S1 - 0.01, S1)
        cell(s, D_AX, D, SSI0, SSI1, Z0, dict(N='O', S='L', A='W', O='O'), FL_GF, 'flat', z0=GF_TOP)       # living
        cell(s, D, dN, SSI0, SSI1, Z0, dict(N='L', S='L', A='O', O=tN), FL_GF, 'flat', z0=GF_TOP)
        # core | living opening: the jamb lining returns round the corner over the end of the
        # living room's north lining
        self.jamb_return(s, SSI0, Z0, S1 - 0.01)
        # ---- L1
        if self.campo:
            y_n, t_n = CSI, 'L'
        else:
            y_n, t_n = Y_DIVS1, 'W'
        cell(s, D_AX, D_BAY - T_WET / 2, y_n, SNI0, Z1, dict(N=t_n, S='O', A='W', O='W'), FL_OPEN, 'flat')    # bath
        cell(s, D_AX, D_BAY - T_WET / 2, SNI0, Y_BATHS - tb, Z1, dict(N=('L', S2), S='W', A='W', O='W'), FL_OPEN,
             'roofSN')
        cell(s, D_AX, D_BAY - T_WET / 2, Y_BATHS + tb, SNI1, Z1, dict(N='W', S=('P', Z_BEAM_S), A='W', O='W'),
             FL_INT, 'roofSN')                                                                                # hall
        cell(s, D_AX, D, SNI1, SN1, Z1, dict(N='O', S='O', A='W', O='L'), None, ('beam', Z_BEAM_S))
        cell(s, D_BAND, D, SN1, Y_TOPS, Z1, dict(N='O', S='O', A='O', O='L'), None, 'vault')               # corridor
        # floors to the well (first riser Y 18.20, 4 cm north of SN1): hall, corridor along the well
        I.floor_stack(kit, h.rect(s, D_AX, D - LIN, SNI1, Y_FOOTS), Z1, FL_INT)
        self.corridor_floor(s, Y_FOOTS, Y_TOPS, Z1)
        # the bay wall's end at the hall opening: plaster return over the N-pav wall's cut end and
        # the opening's lining end, under the beam's plaster
        self.prism('WallPlaster', 'M_PlasterInt', s, D - LIN, D_BAY - T_WET / 2, SNI1 - PL / M, SNI1, Z1, Z_BEAM_S)
        cell(s, D_AX, D, Y_TOPS, SS0, Z1, dict(N='O', S='O', A='W', O='L'), FL_INT, 'vault')               # landing
        cell(s, D_AX, D, SS0, Y_LPS - T_PART / M, Z1, dict(N='O', S='W', A='W', O='L'), FL_INT, ('beam', Z_BEAM_S))
        cell(s, D_AX, D, Y_LPS, SSI1, Z1, dict(N='W', S='L', A='W', O='O'), FL_INT, 'roofSS')              # S bedroom
        cell(s, D, dN, SSI0, SSI1, Z1, dict(N='L', S='L', A='O', O=tN), FL_INT, 'roofSS')
        cell(s, D_BAY + T_WET / 2, dN, y_n, SNI0, Z1, dict(N=t_n, S='O', A='W', O=tN), FL_OPEN, 'flat')     # N bedroom
        cell(s, D_BAY + T_WET / 2, dN, SNI0, SNI1, Z1, dict(N=('L', S2), S='L', A='W', O=tN), FL_INT, 'roofSN')
        # beam skins: core side up to the vault, S bedroom side (lining flush with the partition)
        vt = _Vault(self.xa, 'S')
        self.strip(s, 'd', SN1, 1, D_AX, D, Z_BEAM_S, vt, PLASTER)
        self.strip(s, 'd', SS0, -1, D_AX, D, Z_BEAM_S, vt, PLASTER)
        self.strip(s, 'd', SSI0, 1, D_AX, D, Z_BEAM_S, roof_ceiling('SS'), BU.LINING)

    # -------------------------------------------------------------- walls
    def walls(self, s):
        kit, h = self.kit, self
        y_b = CSI + LF if self.campo else Y_DIVS1
        # L0 lobby | kitchen, kitchen door
        wall(kit, BU.PARTITION, h.P(s, D_KM, Y_DWM), h.P(s, D_KM, SNI1), GF_TOP, S1,
             doors=[((Y_KDOOR_S - Y_DWM) * M, DOOR_ROOM, Z0 + DOOR_HEAD)], prefix='Partition')
        # L1 bay wall (wet): flat part in the joint, sloped part with the north bedroom door
        wall(kit, BU.PARTITION_WET, h.P(s, D_BAY, y_b), h.P(s, D_BAY, SNI0), Z1 - 0.10, S2, prefix='Partition')
        wall(kit, BU.PARTITION_WET, h.P(s, D_BAY, SNI0), h.P(s, D_BAY, SNI1), Z1 - 0.10, roof_ceiling('SN'),
             doors=[((Y_BDOOR_S - SNI0) * M, DOOR_ROOM, Z1 + DOOR_HEAD)], prefix='Partition')
        # L1 bath | hall (wet)
        wall(kit, BU.PARTITION_WET, h.P(s, D_AX, Y_BATHS), h.P(s, D_BAY - T_WET / 2, Y_BATHS), Z1 - 0.10,
             roof_ceiling('SN'), doors=[(D_BATHDOOR - D_AX, DOOR_BATH, Z1 + DOOR_HEAD)], prefix='Partition')
        # L1 landing | south bedroom, under the beam
        y = Y_LPS - T_PART / 2 / M
        wall(kit, BU.PARTITION, h.P(s, D_AX, y), h.P(s, D_CORE, y), Z1 - 0.10, Z_BEAM_S,
             doors=[(D_SDOOR - D_AX, DOOR_ROOM, Z1 + DOOR_HEAD_S)], prefix='Partition')

    def doors(self, s):
        kit, h = self.kit, self
        # L0 kitchen: lobby | kitchen partition, hinge at the S jamb, into the kitchen
        # (parked at PARK_DEG, clear of the court French door)
        I.door(kit, h.P(s, D_KM, Y_DWM), h.P(s, D_KM, SNI1), (Y_KDOOR_S - Y_DWM) * M, DOOR_ROOM, Z0 + DOOR_HEAD, Z0,
               T_PART - 0.002, hinge='b', swing=-s, open_deg=PARK_DEG)
        self.door_floor(s, 'Y', D_KM, Y_KDOOR_S, DOOR_ROOM, T_PART, Z0, FL_GF)
        # L1 bath: into the bath (north), hinge at the bay wall
        I.door(kit, h.P(s, D_AX, Y_BATHS), h.P(s, D_BAY - T_WET / 2, Y_BATHS), D_BATHDOOR - D_AX, DOOR_BATH,
               Z1 + DOOR_HEAD, Z1, T_WET - 0.002, hinge='b', swing=-s)
        self.door_floor(s, 'd', Y_BATHS, D_BATHDOOR, DOOR_BATH, T_WET, Z1, FL_OPEN)
        # L1 north bedroom: bay wall, hinge at the S jamb, into the bedroom (PARK_DEG)
        I.door(kit, h.P(s, D_BAY, SNI0), h.P(s, D_BAY, SNI1), (Y_BDOOR_S - SNI0) * M, DOOR_ROOM, Z1 + DOOR_HEAD, Z1,
               T_WET - 0.002, hinge='b', swing=-s, open_deg=PARK_DEG)
        self.door_floor(s, 'Y', D_BAY, Y_BDOOR_S, DOOR_ROOM, T_WET, Z1, FL_INT)
        # L1 south bedroom: into the bedroom (south)
        y = Y_LPS - T_PART / 2 / M
        I.door(kit, h.P(s, D_AX, y), h.P(s, D_CORE, y), D_SDOOR - D_AX, DOOR_ROOM, Z1 + DOOR_HEAD_S, Z1,
               T_PART - 0.002, hinge='a', swing=s)
        self.door_floor(s, 'd', y, D_SDOOR, DOOR_ROOM, T_PART, Z1, FL_INT)

    # ------------------------------------------------------------- stairs
    def stairs(self, s):
        """One flight L0 -> L1 against the spine rising south (15 x 0.2007,
        14 x 0.235: n11, n18) with its finishes, balustrades on the open edge
        and round the L1 well, the well's slab edges plastered."""
        h = self
        self.flight(s, Y_FOOTS, -1, Z0, (Z1 - Z0) / N_RISERS, GOING_S, S1 - 0.01)
        self.well_edges(s, Y_FOOTS, Y_TOPS, [(Y_FOOTS, Z1)])       # corridor, spine strip, the L1 edge over the foot
        self.balustrade([h.P(s, D_BAND + 0.03, Y_FOOTS + 0.02 / M), h.P(s, D_BAND + 0.03, Y_TOPS - 0.02 / M)], Z1)
        self.balustrade([h.P(s, D_AX + 0.03, Y_FOOTS - 0.03 / M), h.P(s, D_BAND + 0.03, Y_FOOTS - 0.03 / M)], Z1)

    # -------------------------------------------------------------- porch
    def porch(self):
        """Steps from the porch (-0.45) into the vestibule (n11, n76: 3 x 0.15
        inside the two openings either side of the axis pier), the vestibule
        floor (stone on screed, unheated, n11), the entrance doors (PM) in
        the door wall with their stone thresholds."""
        S, kit, h = self.S, self.kit, self
        y_v = SNI0
        if not self.campo:
            st = kit('PorchSteps', 'M_Concrete')
            for s in (-1, 1):
                I.prism(st, h.rect(s, D_PIER, D_PORCHO, SN0, Y_STEP[1]), C.Z_PAVING, Z0 - 0.30)
                I.prism(st, h.rect(s, D_PIER, D_PORCHO, Y_STEP[1], SNI0), C.Z_PAVING, Z0 - 0.15)
            I.prism(st, h.rect(1, -D_PORCH, D_PORCH, SNI0, Y_STEP[2]), GF, Z0 - 0.15)
            y_v = Y_STEP[2]
        I.floor_stack(kit, h.rect(1, -D_PORCH, D_PORCH, y_v, Y_DW0), Z0, FL_HALL)
        f = geo.Face('y', yY(Y_DW0), 1)
        for s in (-1, 1):
            u0, u1 = sorted((self.X(s, PORT['d'][0]), self.X(s, PORT['d'][1])))
            S.register(f, u0, u1, Z0, Z0 + PORT['h'], S.ns, 'PM')
            I.prism(kit('Thresholds', 'M_Stone'), I.rect(u0, u1, yY(Y_DW0), yY(Y_DWM + LF)), GF_TOP, Z0)

    # ---------------------------------------------------------- axis walls
    def axis_walls(self):
        kit = self.kit
        P = lambda Y: (self.xa, yY(Y))
        # L0: spine from the door wall through the core, W5 between the living rooms
        wall(kit, SPINE, P(Y_DWM), P(SS0), GF_TOP, S1, prefix='Spine')
        wall(kit, BU.WALL_SEP, P(SS0), P(SSI1), GF_TOP, S1, prefix='Sep')
        # L1
        y_n = CSI if self.campo else Y_DIVS1
        wall(kit, BU.WALL_SEP, P(y_n), P(SNI0), Z1 - 0.10, S2, prefix='Sep')
        wall(kit, BU.WALL_SEP, P(SNI0), P(SNI1), Z1 - 0.10, roof_ceiling('SN'), prefix='Sep')
        wall(kit, SPINE, P(SNI1), P(SN1), Z1 - 0.10, Z_BEAM_S, prefix='Spine')
        zc = VAULT_ZC['S'] + VAULT_RIN + 0.002
        wall(kit, SPINE, P(SN1), P(SS0), Z1 - 0.10, zc, prefix='Spine')
        wall(kit, SPINE, P(SS0), P(SSI0), Z1 - 0.10, Z_BEAM_S, prefix='Spine')
        wall(kit, BU.WALL_SEP, P(SSI0), P(SSI1), Z1 - 0.10, roof_ceiling('SS'), prefix='Sep')


# ===================================================================== build
def build(ctx) -> None:
    if geo.THROUGH is None:
        return
    t0 = time.time()
    _register_types()
    only = [t for t in os.environ.get('GIUDECCA_MS_ONLY', '').split(',') if t]     # dev: some segments only
    R = Run(ctx)
    R.prepare()
    for seg in C.segments():
        if only and seg.tag not in only:
            continue
        mp = C.middle_part(seg)
        if mp is not None:
            S = SegM(R, seg, mp)
            S.build()
            R.segs.append(S)
        S = SegS(R, seg)
        S.build()
        R.segs.append(S)
    for block in BLOCKS:
        for row in 'MS':
            R.vault_skin(block, row)
    t1 = time.time()
    R.hollow_all()
    t2 = time.time()
    R.finish()
    print(f'[carpet ms] layout {t1 - t0:.1f} s, hollow {t2 - t1:.1f} s, joinery {time.time() - t2:.1f} s')
