"""Schiera interiors (docs/INTERIORS.md): the eight two-storey dwellings "tipo A1"
of the four blocks, their construction layers and joinery.

Research: scratchpad reports schiera.md (rooms, walls, openings, stair; n27 SE 44
L0, n45 SE 45 L1, n5 SE 49 sections, n40 SE 60 core 1:10, n37 published type),
layers.md (build-ups W1/W2/W4/W5/W6/W7, F1/F2/F3, R1/R2/R3) and windows.md
(joinery, joinery.py). Exterior: schiera.py (guarded edits only).

One dwelling (u = metres from the party axis into the dwelling, Y = drawing row
in modules; x = xE(a) - s * u, s = +1 for the dwelling west of the axis;
finished faces u 0.10 / 3.22, Y 29.05 / 34.95):

  L0  kitchen + dining-living, one room (no partition, no door; n27, n37):
      ceiling 2.70 under the L1 slab (raw 2.71), beam B1 (soffit 2.40) under
      the bar's south wall, the double-height void over u 0.95 -> 1.75, beam
      B2 under the terrace's south parapet / oculus panel (legs flush with
      the slab, middle soffit 3.56), sloping ceiling under the lean-to;
      entrance door from the portico (P, threshold 0.11), kitchen window F
      (sill 1.43, full-depth RC sill), two French windows D to the garden,
      lean-to window E with its radiator niche;
  L1  bathroom u 0.10 -> 1.75, Y -> 30.35 (door 0.70, opens into the bath);
      landing open to the core through the bar's south wall (lintel 5.01,
      parapet 3.93 over the void); bedroom u 1.85 -> the end wall / the 0.20
      wall over the portico partition / its own joint leaf (door 0.73, hinge
      at the south jamb); terrace u 2.085 -> 3.30 (R3, finish 3.00 as built);
      bath window F, bedroom window E, terrace door D;
  stair: one straight flight 0.80 wide against the party wall, 15 risers of
      0.2007 and 14 goings of 0.235, foot riser Y 33.194, top riser Y 31.20
      (n5 B, n27, n45), steel balustrade on the void side; RC waist slab
      plastered on its soffit and open side, oak treads 30 and risers 15
      (layers.md S1, matching the parquet);
  core: void and flight under the copper vault (R 6.00 soffit from 5.16 at the
      lining faces, SE 59 / SE 60), lined core walls (W2) and oculus panel;
  party wall: precast flue block at its north end (Y -> 29.40, n27 / n45).

Construction layers: exterior walls W1 = 0.395 face brick + 0.055 insulated
lining (running on over lintels and sill blocks); party wall 0.20 (SE 60 "155
| 20 | 155": double hollow-clay leaf with wool in the bar and lean-to zones,
the RC spine W4 in the core); partitions 0.10 (n45 "10"); floors F3 (L0,
320), F1 / F2 (L1 over the kitchen / the portico, 300); roofs R1 under the
tiles, R2 under the copper; terraces a 0.09 build-up on the slab (finish 3.00
as built, n5 F "2,9x", in the exterior's paving). The roof build-ups follow the exterior tile planes
(bar 36 %, lean-to 39.5 %), so the finished ceilings sit up to 6 cm (bar) /
11 cm (lean-to) off the drawn 34 % line T + 2.47 + 0.34 s.
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

from . import buildups as B
from . import geo
from . import interior as I
from . import joinery as J
from . import schiera as X
from .common import xE, yY
from .params import FLOORS, MODULE as M, SCHIERA as S

PART, COL = 'Schiera', 'Schiera'
T1 = FLOORS[1]                       # 3.01 first floor


def dY(m: float) -> float:
    """Metres -> modules (along E or Y)."""
    return m / M


# ------------------------------------------------------------------ rows (Y, modules)
W1 = B.WALL_EXT_MASONRY              # 0.395 face brick (layers W1)
LIN = B.LINING_T                     # 0.055 insulated lining on warm faces
PL = 0.010                           # plaster on soffits, beams, slab edges
Y_NO, Y_BO, Y_SO = S['y'][0], X.Y_BAR, S['y'][1]      # outer faces: bar N, bar S, lean-to S
Y_NI = Y_NO + dY(W1)                 # 29.019 bar N wall, inner masonry face
Y_BI = Y_BO - dY(W1)                 # 30.981 bar S wall, inner masonry face
Y_SI = Y_SO - dY(W1)                 # 34.981 lean-to S wall, inner masonry face
Y_C = X.Y_CORE                       # 32.93 terrace | lean-to high wall (outer face, as built)
Y_HW = Y_C + dY(X.WALL)              # 33.154 lean-to high wall, inner face
Y_PB = Y_C - dY(X.PANEL_Y[0])        # 32.785 oculus panel, back face
Y_PL = Y_PB - dY(0.08)               # 32.736 panel lining face (SE 60 B-B "8 | 14 | 23")
Y_FLUE = 29.40                       # end of the flue duct in the party wall (n27 / n45 hatch 29.05 -> 29.40)
Y_BATH = 30.38                       # bathroom | landing partition axis (verified: n45 faces 30.35 / 30.41)
Y_BED_DOOR = (30.46, 30.90)          # bedroom door jambs (n45, all 8)
Y_FOOT = 33.194                      # foot riser (n27 33.19, n5 B)
N_RISERS, RISER, GOING = 15, T1 / 15, 0.235          # n5 B: 15 risers; goings n27 / n45
Y_LND = Y_FOOT - dY(N_RISERS * GOING)                 # 31.058 end of the top tread = landing edge
WAIST, TREAD_T, NOSING = 0.15, 0.03, 0.02             # RC waist slab, oak tread 30 with its nosing
RISER_T = 0.015                                       # oak riser board 15 (layers.md L5 S1)
TREAD_MAT = 'M_DoorLeaf'             # oak treads and risers, matching the parquet (layers S1, schiera S.6;
#                                      the towers' private flights use the same, towers.md T.5)

# ------------------------------------------------------------------ bands (u, metres)
U_PW = 0.10                          # party wall half (0.20, SE 60)
U_FL = 0.90                          # flight 0.80 clear (n45 "80 | 5 | 80")
U_VD = 0.95                          # void edge, balustrade line "5"
U_CL = 1.75                          # core lining face (SE 60)
U_CM = X.CORE_IN                     # 1.805 core masonry face (W2)
U_CO = X.CORE_HW                     # 2.085 core outer (render) face
U_PART = (1.75, 1.85)                # bath + landing | bedroom partition 0.10 (n45 written "10", u 1.73-1.87)
U_BATH_DOOR = (0.92, 1.62)           # bathroom door 0.70 ("70/2,10"), hinge jamb u 1.62 (n45 0.97-1.62)
U_BO = X.HALF * M                    # 3.6696 block side wall, outer face
U_BS = U_BO - W1                     # 3.2746 block side wall, inner masonry face (L0)
U_PP = U_BO - X.PARAPET_T            # 3.2996 terrace side parapet, inner face (as built)
JOINT_LEAF = 0.185                   # joint leaf at L1: 0.20 with its plaster (n45 "20 | 9 | 20")
BAY_WALL = 0.17                      # L1 wall over the portico partitions: 0.20 with plaster (n45 "20")

# ------------------------------------------------------------------ levels (m)
GF_SLAB = (B.GF_SOFFIT, B.GF_SOFFIT + 0.20)          # -0.32 -> -0.12
RAW = T1 - B.FLOOR_T                 # 2.71 L1 slab soffit
SLAB_TOP = RAW + 0.20                # 2.91
Z_B1 = 2.40                          # beam B1 soffit (n5 F 2.33, A 2.46, B 2.42)
Z_B2L_TOP = 3.87                     # beam B2 legs: flush with the slab soffit, top 3.87 (SE 60)
B2_LEAF = 0.14                       # ... behind the terrace's 12 face brick + 2 (SE 60 A-A "12 | 2 | 25")
Z_B2M = 3.56                         # beam B2 middle soffit (SE 60 B-B / elevation)
Z_BEAM = X.Z_BEAM                    # 3.98 top of B2 middle under the copertina (as built)
Z_PARAPET = 3.93                     # parapet over the void, L1 + 0.92 (n5 F)
PARAPET_T = 0.10                     # ... in the plane of the bar's S face, Y 31.13-31.22 (n45)
Z_LINTEL = T1 + 2.00                 # 5.01 landing -> core opening head (n5 F, both voids)
Z_TERR = X.TERRACE_Z                 # 3.00 terrace finish (as built; n5 F "2,9x")
DOOR_HEAD = T1 + 2.10                # internal doors 2.10 (SE 14 "70/2,10")

# ------------------------------------------------------------------ stacks
ROOF_STRUCT = [l for l in B.ROOF_TILE_UNDER if not l[0].startswith('Lining')]   # 205 under the tiles
ROOF_STRUCT_T = B.total(ROOF_STRUCT)
VAULT_STRUCT = [('Membrane', 'M_Membrane', 0.005), ('Insulation', 'M_Insulation', 0.040),
                ('Cappa', 'M_Structure', 0.040), ('Slab', 'M_Structure', 0.120)]   # R2, 205
PARTY_SEP = [('Plaster', 'M_PlasterInt', 0.015), ('Leaf', 'M_HollowBrick', 0.075),
             ('Wool', 'M_Insulation', 0.020), ('Leaf', 'M_HollowBrick', 0.075),
             ('Plaster', 'M_PlasterInt', 0.015)]      # W5 adjusted to the written 0.20 (SE 60)
PARTY_SPINE = B.WALL_SPINE                            # W4 200 in the core: the flights bear on it
PARTY_FLUE = [('FluePlaster', 'M_PlasterInt', 0.015), ('Flue', 'M_Structure', 0.170),
              ('FluePlaster', 'M_PlasterInt', 0.015)]  # precast flue block in the party wall (n27 / n45)
TERRACE_THIN = [('Tiles', 'M_Paving', 0.015), ('Bed', 'M_Screed', 0.020), ('Membrane', 'M_Membrane', 0.010),
                ('Insulation', 'M_Insulation', 0.030), ('Falls', 'M_Screed', 0.015)]   # 90 on the slab
#                                    (finish in the exterior's terrace paving, M_Paving: unchanged from outside)
PLASTER = [('Plaster', 'M_PlasterInt', 0.015)]        # on internal masonry (bay walls, joint leaves)
PARTITION_10 = [('Plaster', 'M_PlasterInt', 0.010), ('Core', 'M_HollowBrick', 0.080),
                ('Plaster', 'M_PlasterInt', 0.010)]   # partitions "10" (n45; W7 would be 110)
DOOR_T = B.total(PARTITION_10) - 0.002  # interior.door: architraves then sit on the plaster faces
FIN_INT = B.FLOOR_INT[:3]            # parquet, screed, fill (slab separate)
FIN_OPEN = B.FLOOR_OPEN[:3]          # parquet, screed, insulation (over the porticoes)
FIN_GF = B.FLOOR_GF[:4]              # parquet, screed, insulation, fill

NV = 32                              # vault arc segments: the copper sheet's grid (schiera._copper)


# ------------------------------------------------------------------ roof planes
def _plane(section):
    """Tile underside z(x, y) of a mono-pitch roof from schiera._section."""
    (yl, zl), (yh, zh) = section[5], section[4]
    m = (zh - zl) / (yh - yl)
    return (lambda x, y: zl + m * (y - yl)), abs(m)


TILE_BAR, SLOPE_BAR = _plane(X._section(S['bar_y'][0], X.Y_BAR, X.BAR_ROOF))
TILE_LEAN, SLOPE_LEAN = _plane(X._section(X.LEAN_Y[1], X.LEAN_Y[0], X.LEAN_ROOF))


def _under(tile, slope, d):
    k = math.sqrt(1 + slope * slope)
    return lambda x, y: tile(x, y) - d * k


RAW_BAR = _under(TILE_BAR, SLOPE_BAR, ROOF_STRUCT_T)              # raw soffits (under the slab)
RAW_LEAN = _under(TILE_LEAN, SLOPE_LEAN, ROOF_STRUCT_T)
CEIL_BAR = _under(TILE_BAR, SLOPE_BAR, ROOF_STRUCT_T + LIN)       # finished (lining) ceilings
CEIL_LEAN = _under(TILE_LEAN, SLOPE_LEAN, ROOF_STRUCT_T + LIN)

# vault (R2): finished soffit R 6.00 from T + 2.15 at the lining faces; copper as built
VR = B.VAULT_R_SOFFIT
ZC_IN = T1 + B.VAULT_SPRING - math.sqrt(VR * VR - U_CL * U_CL)    # centre of the soffit arcs
ZC_CU = X.VAULT_CROWN - X.CORE_VAULT_R                            # centre of the copper surface
R_SLAB = VR + LIN                                                 # 6.055 raw soffit
R_TOP = R_SLAB + B.total(VAULT_STRUCT)                            # 6.26 top of the membrane


def _arc(zc, r):
    return lambda dx: zc + math.sqrt(max(r * r - dx * dx, 0.0))


# ------------------------------------------------------------------ dwellings
def bedroom_end(a: float, s: int) -> tuple[float, str]:
    """u of the masonry face closing the bedroom of dwelling (a, s), and its
    kind: 'ext' (bar end wall, W1 + lining) or 'int' (0.25 wall over the
    portico partition, or the joint leaf: plaster only)."""
    e_out = X.E_WEST if s > 0 else X.E_EAST
    walls = [e for e in S['garden_walls_e'] if s * (e - a) > 0]
    e = min(walls, key=lambda e: abs(e - a)) if walls else None
    if e is None or abs(e_out - a) < abs(e - a):
        return abs(e_out - a) * M - W1, 'ext'
    if abs(e - X.JOINT_E) < 1e-6:
        return abs(e - a) * M - X.GAP / 2 - JOINT_LEAF, 'int'
    return abs(e - a) * M - BAY_WALL / 2, 'int'


class Dw:
    """Frame of one dwelling (s = +1 west of the party axis a, -1 east)."""

    def __init__(self, a: float, s: int):
        self.a, self.s, self.xa = a, s, xE(a)
        self.u_end, self.end_kind = bedroom_end(a, s)

    def x(self, u: float) -> float:
        return self.xa - self.s * u

    def p(self, u: float, Y: float) -> tuple[float, float]:
        return (self.x(u), yY(Y))

    def rect(self, u0, u1, Y0, Y1):
        return I.rect(self.x(u0), self.x(u1), yY(Y0), yY(Y1))

    def poly(self, pts):
        return I.clean([self.p(u, Y) for u, Y in pts])

    def box(self, bm, u0, u1, Y0, Y1, z0, z1):
        geo.add_box(bm, self.x(u0), self.x(u1), yY(Y0), yY(Y1), z0, z1)


# ------------------------------------------------------------------ helpers
def _layers_box(kit, prefix, layers, dw, u0, u1, Y0, Y1, z0, top, axis, inward):
    """Wall layers on an axis-aligned masonry face: axis 'u' (face at u = u0,
    layers toward +u if inward > 0) or 'Y' (face at Y = Y0, toward +Y if
    inward > 0); the other range is (u0, u1) or (Y0, Y1). top: level or z(x, y).
    Returns the thickness."""
    d = 0.0
    for elem, mat, t in layers:
        if mat is not None:
            if axis == 'u':
                a, b = u0 + inward * d, u0 + inward * (d + t)
                poly = dw.rect(a, b, Y0, Y1)
            else:
                a, b = Y0 + inward * dY(d), Y0 + inward * dY(d + t)
                poly = dw.rect(u0, u1, a, b)
            I.prism(kit(prefix + elem, mat), poly, z0, top)
        d += t
    return d


def _wall(kit, a, b, outline_sz, layers, prefix, side=0):
    """Wall on the plan line a -> b: each layer an (s, z) outline extruded
    across it; side 0 = layers centred on the line (left face first), +1 /
    -1 = layers stacked from the line to the left / right (first = at the line)."""
    T = sum(t for _, _, t in layers)
    if side == 0:
        t0 = T / 2
        for elem, mat, t in layers:
            if mat is not None:
                I.oprism(kit(prefix + elem, mat), a, b, outline_sz, t0 - t, t0)
            t0 -= t
        return
    d = 0.0
    for elem, mat, t in layers:
        if mat is not None:
            lo, hi = sorted((side * d, side * (d + t)))
            I.oprism(kit(prefix + elem, mat), a, b, outline_sz, lo, hi)
        d += t


def _notched(L, z0, tops, doors=()):
    """(s, z) outline of a wall of length L from z0, top polyline tops
    [(s, z), ...] from s = 0 to s = L, door notches [(s0, s1, head)]."""
    out = [(0.0, z0)]
    for s0, s1, head in sorted(doors):
        out += [(s0, z0), (s0, head), (s1, head), (s1, z0)]
    out.append((L, z0))
    out += list(reversed(tops))
    return out


def _band(bm, f_top, f_bot, xs, y0, y1):
    """Curved band between z = f_top(x) and f_bot(x) over the x samples xs,
    extruded along y (vault layers)."""
    top = [(x, f_top(x)) for x in xs]
    bot = [(x, f_bot(x)) for x in reversed(xs)]
    geo.add_prism_y(bm, top + bot, min(y0, y1), max(y0, y1))


def _grid(xa: float, x0: float, x1: float) -> list[float]:
    """Vault x samples over [x0, x1]: the common grid of the core (+-U_CM about
    xa) plus the end points, so the layers of different widths meet."""
    g = [xa - U_CM + 2 * U_CM * k / NV for k in range(NV + 1)]
    lo, hi = sorted((x0, x1))
    return [lo] + [x for x in g if lo + 1e-4 < x < hi - 1e-4] + [hi]


def _door_cfg(a, b, s_hinge, room):
    """hinge ('a' / 'b') and swing (+1 left of a -> b / -1) of a door hinged at
    s_hinge metres from a and opening into the side of the point `room`."""
    A, Bv = Vector(a), Vector(b)
    e = (Bv - A).normalized()
    n = Vector((-e.y, e.x))
    L = (Bv - A).length
    hinge = 'a' if s_hinge < L / 2 else 'b'
    return hinge, (1 if n.dot(Vector(room) - A) > 0 else -1)


def _register_types() -> None:
    """Opening types of the schiera not in joinery.TYPES: the entrance door
    with its frame at the inner face of the 0.395 jamb, in the lining plane
    (SE 53 A: "frame at d 0.395 -> 0.455", windows.md P schiera), and the
    oculus glass ring inside the panel lining (windows.md O60)."""
    J.TYPES['PS'] = dict(J.TYPES['P'], frame_at=J.WALL)
    J.TYPES.setdefault('OS', dict(J.TYPES['O'], frame_at=0.16))
    # finestre schiera (kitchen, bath; sill 1.43): joinery puts the handle at floor + 1.05,
    # under these high sills, so the handle is built here on the sash (_f_handle)
    J.TYPES['FS'] = dict(J.TYPES['F'], handle=False)


# ------------------------------------------------------------------ extra opening parts
F_SILL = (0.12, 0.13)                # sill F: 1.15 x 0.395 x 0.13, full depth (SE 53 F, windows.md 6)
P_SILL = (0.06, 0.11)                # entrance threshold: (W + 0.12) x 0.46 x 0.11, top 0.00 (SE 53 A)
T_SILL = 0.03                        # terrace-door threshold slab (flush with the bedroom floor, A)


def _extra_parts(r) -> list[tuple]:
    """(u0, u1, z0, z1, d0, d1) of the concrete parts the joinery does not
    build for the schiera's plain-jamb openings: the inner part of the full-
    depth RC sill of the F windows (kitchen, bath; behind the exterior's
    0.115 sill), the concrete threshold of the entrance door, and a flush
    threshold under the terrace doors (sill at floor level: joinery adds
    none, so the wall lining's top showed in the doorway)."""
    kind = J.classify(r)
    if r['kind'] != 'rect' or kind not in ('F', 'FS', 'PS', 'C', 'D'):
        return []
    u0, u1, z0, z1 = J.dims(r)
    if kind in ('F', 'FS'):
        e, h = F_SILL
        return [(u0 - e, u1 + e, z0 - h, z0, 0.115, J.WALL)]
    if kind in ('C', 'D'):
        zf = J.floor_of(z0)
        if z0 - zf > 0.01:
            return []
        return [(u0 - J.MAZ, u1 + J.MAZ, z0 - T_SILL, z0, 0.0, J.FINISH)]
    e, h = P_SILL
    return [(u0 - e, u1 + e, z0 - h, z0, -0.01, J.FINISH)]


def _extra_pockets(r) -> list[tuple]:
    """Their pockets in the hollowing cutter (into the room, like the
    joinery pockets), plus the seat of the exterior's 0.115 F sill (it
    overlapped the brick under the opening)."""
    out = []
    for u0, u1, z0, z1, d0, d1 in _extra_parts(r):
        out.append((u0, u1, z0, z1, -0.01 if d0 <= 0.0 else d0, J.FINISH + 0.05))   # thresholds: from
        #                                                 in front of the face (air), no coplanar cutter face
        if J.classify(r) in ('F', 'FS'):
            uc, w = (u0 + u1) / 2, u1 - u0 - 2 * F_SILL[0]
            out.append((uc - w / 2 - 0.08, uc + w / 2 + 0.08, z1 - 0.06, z1, -0.01, 0.1153))
    return out


# ------------------------------------------------------------------ hollowing
def _cutter(bm, zones, a):
    """Clear volumes of one block (both dwellings, party wall zone included)
    for the hollowing boolean; zones collects the interior ones (x0, x1, y0,
    y1, z0, top) for painting the remaining masonry faces."""
    blk = Dw(a, +1)
    ue_w, ue_e = bedroom_end(a, +1)[0], bedroom_end(a, -1)[0]

    def add(u0, u1, Y0, Y1, z0, z1, paint=True, top=None):
        poly = blk.rect(u0, u1, Y0, Y1)
        I.prism(bm, poly, z0, z1)
        if paint:
            xs, ys = [p[0] for p in poly], [p[1] for p in poly]
            zones.append((min(xs), max(xs), min(ys), max(ys), z0, top if top is not None else z1))

    # The cutter object is welded (geo.object_from_bmesh), so no two prisms may share a
    # corner: the free ends (inside another volume or beyond the body) get distinct levels
    # (0.3 mm steps); the ends that form faces (slab seats, lintel, parapet) are exact.
    add(-U_BS, U_BS, Y_NI, Y_SI, GF_SLAB[0], RAW + 0.005)                 # L0 rooms
    add(-U_BS, U_BS, Y_NI, Y_BO, RAW - 0.0100, SLAB_TOP)                  # L1 slab, bar + B1
    add(-U_PP, U_PP, Y_BO, Y_C, RAW - 0.0097, SLAB_TOP)                   # terrace slab (into the parapets)
    add(-U_BS, U_BS, Y_C, Y_HW, RAW - 0.0094, SLAB_TOP)                   # beam B2 legs
    add(-U_BS, U_BS, Y_NI, Y_BI, RAW - 0.0091, 8.5, top=TILE_BAR)        # bar L1 over the block
    add(U_BS - 0.005, ue_w, Y_NI, Y_BI, RAW, 8.5003, top=TILE_BAR)        # ... over the porticoes,
    add(-ue_e, -(U_BS - 0.005), Y_NI, Y_BI, RAW, 8.5006, top=TILE_BAR)    # from the passage ceiling
    for u0, u1, z0 in ((U_CO, U_PP, 2.9012), (-U_PP, -U_CO, 2.9015)):     # terraces (exterior)
        add(u0, u1, Y_BO, Y_C, z0, Z_TERR + 0.03, paint=False)
    add(-U_CM, U_CM, Y_BO, Y_PB, RAW - 0.0088, 6.2, top=Z_LINTEL)         # core up through the vault
    add(-U_CM, U_CM, Y_PL, Y_HW, RAW - 0.0085, Z_BEAM + 0.07, top=Z_BEAM) # beam B2 middle zone
    add(-U_BS, U_BS, Y_HW, Y_SI, RAW - 0.0082, 4.6, top=TILE_LEAN)        # lean-to
    add(-U_CL, U_CL, Y_BI - 0.003, Y_BO + 0.003, RAW - 0.0079, Z_LINTEL)  # landing opening + spine
    for u0, u1, z0 in ((U_CM, U_BS, 2.9018), (-U_BS, -U_CM, 2.9021)):     # B2 legs inside the high wall
        add(u0, u1, Y_C + dY(B2_LEAF), Y_HW, z0, Z_B2L_TOP, paint=False)


def _pockets(r) -> list[tuple]:
    """joinery.pockets(r), with the stop-jamb pocket reaching 0.5 mm into a
    threshold pocket under it: the two share their corners at the sill, which
    the welded cutter object would turn into non-manifold edges (the union of
    the boxes is unchanged)."""
    # pockets that start on the outer face (thresholds) start 1 cm in front of it
    # instead: a cutter face coplanar with the facade left a double face there
    ps = [(u0, u1, z0, z1, -0.01 if d0 <= 0.0 else d0, d1) for u0, u1, z0, z1, d0, d1 in J.pockets(r)]
    out = []
    for p in ps:
        u0, u1, z0, z1, d0, d1 = p
        for q in ps:
            if q is not p and abs(q[3] - z0) < 1e-9 and abs(q[0] - u0) < 1e-9 and abs(q[1] - u1) < 1e-9 \
                    and q[4] <= d0 + 1e-9 and d1 <= q[5] + 1e-9:
                z0 -= 0.0005
        out.append((u0, u1, z0, z1, d0, d1))
    return out


def _f_handle(kit, r) -> None:
    """Lever of the single casement of an F window at mid-height of the sash,
    on the latch stile (as joinery.opening places it, but not at floor +
    1.05, which is under the 1.43 sill)."""
    sp = J.spec_for('FS')
    fw, fd = sp['frame']
    sw, sd = sp['sash']
    u0, u1, z0, z1 = J.dims(r)
    ds = J.WALL + (fd - sd) / 2
    uh, zh = u1 - fw - sw / 2, (z0 + z1) / 2
    hb = kit('WindowHandles', 'M_Steel')
    I.face_box(hb, r, uh - 0.012, uh + 0.012, zh - 0.07, zh + 0.07, ds + sd, ds + sd + 0.012)
    I.face_box(hb, r, uh - 0.012, uh + 0.012, zh - 0.10, zh + 0.012, ds + sd + 0.012, ds + sd + 0.06)


def _niche_reveals(kit, r) -> None:
    """Plaster returns in the radiator niche under an E window (joinery builds
    its back, NicheLining): 1 cm on both sides and under the sill block, and a
    1 cm plaster upstand on its floor, so the wall lining's cut ends (adhesive,
    insulation, board) do not show round the niche."""
    s = J.spec_for(J.classify(r))
    if not s['niche'] or r['kind'] != 'rect':
        return
    u0, u1, z0, z1 = J.dims(r)
    zf = J.floor_of(z0)
    a, b = u0 - J.MAZ, u1 + J.MAZ
    d0, d1 = J.STOP + J.LIN, J.FINISH
    zt = z0 - 0.13
    bm = kit('NicheLining', 'M_PlasterInt')
    I.face_box(bm, r, a, b, zf, zf + PL, d0, d1)
    I.face_box(bm, r, a, b, zt - PL, zt, d0, d1)
    I.face_box(bm, r, a, a + PL, zf + PL, zt - PL, d0, d1)
    I.face_box(bm, r, b - PL, b, zf + PL, zt - PL, d0, d1)


def _oculus_reveal(kit, r) -> None:
    """Plaster sleeve (10 mm) lining the oculus reveal through the panel
    lining, from the panel's back face to the finished face; the lining is
    cut 10 mm wider round it (_lining_cutter), so its cut insulation does not
    show between the board and the panel."""
    if r['kind'] != 'round':
        return
    d0, d1 = sorted(abs(r['coord'] - yY(Y)) for Y in (Y_PB, Y_PL))
    big = I.offset(I.clean(r['outline']), -PL)
    J._ring(kit('RevealPlaster', 'M_PlasterInt'), J.Frame3(r), big, PL, d0, d1)


def _add_pockets(bm, recs) -> None:
    for r in recs:
        for u0, u1, z0, z1, d0, d1 in _pockets(r) + _extra_pockets(r):
            I.face_box(bm, r, u0, u1, z0, z1, d0, d1)


def _lining_rects(r) -> list[tuple]:
    """(u0, u1, z0, z1) rectangles an opening takes out of the wall linings
    besides its outline: the frame pocket behind a stop jamb (its reveal
    plaster runs to the finished face), the window board, the radiator
    niche, the French-window and entrance thresholds. The linings run on
    over the lintels and sill blocks (joinery.lining_cutter cuts their
    pockets too, which left 55 mm deep bands of bare concrete over and
    under every opening)."""
    kind = J.classify(r)
    if kind is None or r['kind'] != 'rect':
        return []
    s = J.spec_for(kind)
    u0, u1, z0, z1 = J.dims(r)
    zf = J.floor_of(z0)
    maz = J.MAZ
    out = []
    if s['jamb'] == 'stop':
        out.append((u0 - maz, u1 + maz, z0, z1 + maz))
    if not s['door'] and s['board'] and z0 - zf > 0.5:
        e = maz + 0.02 if s['jamb'] == 'stop' else 0.02
        out.append((u0 - e, u1 + e, z0 - 0.025, z0))
    if s['niche']:
        out.append((u0 - maz, u1 + maz, zf, z0 - 0.13))
    if s['door'] and kind in ('C', 'D') and z0 - zf > 0.01:
        out.append((u0 - maz, u1 + maz, zf - 0.02, z0))
    for p0, p1, q0, q1, _, _ in _extra_parts(r):
        if kind != 'FS':
            out.append((p0, p1, q0, q1))           # thresholds through the lining zone
    return out


def _rect_union(rects) -> list[list[tuple[float, float]]]:
    """Outline loops (u, z), counter-clockwise, of the union of axis-aligned
    rectangles (u0, u1, z0, z1): one exact outline per connected group, so
    the lining cutter has no coincident or coplanar overlapping faces (the
    exact boolean failed on overlapping boxes sharing a plane)."""
    us = sorted({v for r in rects for v in r[:2]})
    zs = sorted({v for r in rects for v in r[2:]})
    cov = set()
    for i in range(len(us) - 1):
        um = (us[i] + us[i + 1]) / 2
        for j in range(len(zs) - 1):
            zm = (zs[j] + zs[j + 1]) / 2
            if any(a < um < b and c < zm < d for a, b, c, d in rects):
                cov.add((i, j))
    nxt = {}
    for i, j in cov:
        if (i, j - 1) not in cov:
            nxt.setdefault((i, j), []).append((i + 1, j))
        if (i + 1, j) not in cov:
            nxt.setdefault((i + 1, j), []).append((i + 1, j + 1))
        if (i, j + 1) not in cov:
            nxt.setdefault((i + 1, j + 1), []).append((i, j + 1))
        if (i - 1, j) not in cov:
            nxt.setdefault((i, j + 1), []).append((i, j))
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop, v = [], start
        while True:
            loop.append(v)
            w = nxt[v].pop()
            if not nxt[v]:
                del nxt[v]
            v = w
            if v == start:
                break
        pts = [(us[i], zs[j]) for i, j in loop]
        n = len(pts)
        keep = [p for k, p in enumerate(pts)                       # drop collinear corners
                if not ((pts[k - 1][0] == p[0] == pts[(k + 1) % n][0]) or
                        (pts[k - 1][1] == p[1] == pts[(k + 1) % n][1]))]
        loops.append(keep)
    return loops


def _lining_cutter(recs):
    """Cutter for the wall linings round the openings: per opening one
    solid of the union of its outline and _lining_rects."""
    bm = bmesh.new()
    for r in recs:
        if J.classify(r) is None and r.get('through') is None:
            continue
        f = geo.Face(r['axis'], r['coord'], r['out'])
        rects = _lining_rects(r)
        if r['kind'] == 'round':                   # oculus: room for its reveal sleeve (_oculus_reveal)
            f.solid(bm, I.offset(I.clean(r['outline']), -PL), 1.2, outside=0.3)
            continue
        if not rects:
            f.solid(bm, r['outline'], 1.2, outside=0.3)
            continue
        for loop in _rect_union([J.dims(r)] + rects):
            f.solid(bm, loop, 1.2, outside=0.3)
    return bm


def _pocket_zones(recs) -> list[tuple]:
    """Paint zones for the joinery pockets behind the brick stop (radiator
    niches, frame rebates): their masonry faces show inside the rooms."""
    out = []
    for r in recs:
        for u0, u1, z0, z1, d0, d1 in _pockets(r):
            d0 = max(d0, J.STOP - 0.01)
            if d1 <= d0:
                continue
            c0, c1 = sorted((r['coord'] - r['out'] * d0, r['coord'] - r['out'] * d1))
            if r['axis'] == 'x':
                out.append((c0, c1, u0, u1, z0, z1))
            else:
                out.append((u0, u1, c0, c1, z0, z1))
    return out


def _portico_rects(E0: float, E1: float) -> list[tuple[float, float, float, float]]:
    """World (x0, x1, y0, y1) of the portico passages of a segment, as
    schiera.py cuts them (between the 0.37 walls' inner faces)."""
    y0, y1 = sorted((yY(Y_NO) - X.WALL, yY(Y_BO) + X.WALL))
    out = []
    for p in X.porticoes():
        if E0 < p['c'] < E1:
            x0, x1 = sorted((xE(p['lo']), xE(p['hi'])))
            out.append((x0, x1, y0, y1))
    return out


def _paint(ctx, body, zones, skip=(), tol=0.003) -> int:
    """Interior plaster on the masonry faces left inside the dwellings (pier,
    parapet, lintels, internal walls; the linings cover the rest). Faces of
    the portico soffits (skip: the passages' plan rectangles) stay exterior."""
    mat = ctx.mats['M_PlasterInt']
    me = body.data
    if mat.name not in [m.name for m in me.materials if m]:
        me.materials.append(mat)
    idx = [m.name if m else None for m in me.materials].index(mat.name)
    n = 0
    for poly in me.polygons:
        c = poly.center
        if poly.normal.z < -0.99 and abs(c.z - RAW) < 0.005 and any(
                x0 - tol <= c.x <= x1 + tol and y0 - tol <= c.y <= y1 + tol for x0, x1, y0, y1 in skip):
            continue
        for x0, x1, y0, y1, z0, top in zones:
            if x0 - tol <= c.x <= x1 + tol and y0 - tol <= c.y <= y1 + tol and c.z >= z0 - tol:
                zt = top(c.x, c.y) if callable(top) else top
                if c.z <= zt + tol:
                    poly.material_index = idx
                    n += 1
                    break
    return n



def _trim_seats(bm, recs) -> None:
    """The joinery pockets start where the exterior's concrete trim already
    sits in the wall (head bands 5 cm, sills 11.5 cm deep, garden ground 1.5 cm
    under the French-window thresholds): cut that brick too, so trim and body
    do not share a face (z-fighting) and the trim fills its seat."""
    for r in recs:
        kind = J.classify(r)
        if kind is None or r['kind'] != 'rect':
            continue
        sp = J.spec_for(kind)
        u0, u1, z0, z1 = J.dims(r)
        zf = J.floor_of(z0)
        garden = r['axis'] == 'x' and r['outline'][0][0] < yY(Y_BO) + 0.005      # garden-side walls
        band = None
        if r['axis'] == 'y':
            band = {round(X.HEAD, 3): X.BAND_L0, round(T1 + X.HEAD, 3): X.BAND}.get(round(z1, 3))
        elif garden and abs(z1 - X.HEAD) < 1e-3:          # garden-side bands are 1 mm slimmer
            band = (X.BAND_L0[0] + 0.001, X.BAND_L0[1] - 0.001)
        if sp['lintel'] and band is not None:
            I.face_box(bm, r, u0 - 0.12, u1 + 0.12, band[0], band[1], -0.01, X.BAND_BACK + 0.0003)
        if not sp['door'] and sp['board'] and z0 - zf > 0.5:                       # schiera._trim sills
            I.face_box(bm, r, u0 - 0.08, u1 + 0.08, z0 - 0.06, z0, -0.01, 0.1153)
        if sp['door'] and kind in ('C', 'D') and z0 - zf > 0.01 and garden:
            I.face_box(bm, r, u0 - J.MAZ, u1 + J.MAZ, zf - 0.10, zf - 0.02, -0.01, X.GARDEN_IN)

# ------------------------------------------------------------------ stair
class _Route:
    """Kit stand-in for interior.flight: sends the elements named in routes
    {element: (kit element, material)} to the kit and drops the others."""

    def __init__(self, kit, routes):
        self.kit, self.routes, self.dropped = kit, routes, []

    def __call__(self, element, mat, **props):
        if element in self.routes:
            return self.kit(*self.routes[element])
        bm = bmesh.new()
        self.dropped.append(bm)
        return bm

    def free(self):
        for bm in self.dropped:
            bm.free()


def _flight(kit, dw: Dw) -> None:
    """The flight against the party wall (2 mm joint to its plaster; the foot
    sits in the floor finishes): RC waist slab (interior.flight's profile),
    oak treads and riser boards (layers.md S1: "oak tread 30 + riser 15,
    matches the parquet"), plaster on its soffit and open side face, and
    the soffit plaster's return over the landing slab's edge at the top."""
    s = dw.s
    u0 = U_PW + 0.002
    a = dw.p(u0, Y_FOOT)
    b = (a[0], a[1] + 1.0)                             # walking north (+y)

    def t(u):                                          # across a -> b (left = +u for both s)
        return s * (u - u0)

    def strip(bm, outline, ua, ub):
        I.oprism(bm, a, b, outline, *sorted((t(ua), t(ub))))

    kw = dict(waist=WAIST, tread_t=TREAD_T, nosing=NOSING, side=s, tread_top_last=True)
    args = ((0.0, 1.0), )
    steps = (N_RISERS, RISER, GOING, 0.0)
    for start, width, routes in (
            (a, U_FL - u0, {'StairTreads': ('StairTreads', TREAD_MAT)}),                     # full width
            (a, U_FL - PL - u0, {'StairStructure': ('StairStructure', 'M_Structure')}),      # RC
            (dw.p(U_FL - PL, Y_FOOT), PL, {'StairStructure': ('StairPlaster', 'M_PlasterInt')})):  # side
        r = _Route(kit, routes)
        I.flight(r, start, *args, width, *steps, **kw)
        r.free()
    # oak riser boards under the nosings, on the tread below (the floor at the foot)
    rb = kit('StairRisers', TREAD_MAT)
    for k in range(N_RISERS):
        sk = k * GOING
        strip(rb, [(sk - RISER_T, k * RISER), (sk, k * RISER), (sk, (k + 1) * RISER - TREAD_T),
                   (sk - RISER_T, (k + 1) * RISER - TREAD_T)], u0, U_FL)
    # soffit plaster (from the floor finishes up), returned down over the landing slab's
    # cut edge at the top to the L0 ceiling plaster
    zt = -TREAD_T
    slope = RISER / GOING
    w_v = WAIST / math.cos(math.atan(slope))
    pv = PL * math.sqrt(1 + slope * slope)             # 10 mm across the slope, vertically

    def soffit(sv):
        return zt + slope * sv - w_v
    s_hit, s_top = w_v / slope, N_RISERS * GOING
    z_st = min(soffit(s_top), zt + N_RISERS * RISER - w_v)
    sp = kit('StairPlaster', 'M_PlasterInt')
    strip(sp, [(s_hit, zt), (s_top, z_st), (s_top, RAW - PL), (s_top - PL, RAW - PL),
               (s_top - PL, soffit(s_top - PL) - pv), (s_hit + pv / slope, zt)], u0, U_FL)
    # ... and on the slab's side face beside it (u 0.90, under the flight's soffit)
    s_b = (RAW - PL + pv - zt + w_v) / slope
    strip(sp, [(s_b, RAW - PL), (s_top - PL, RAW - PL), (s_top - PL, soffit(s_top - PL) - pv)], U_FL - PL, U_FL)


# ------------------------------------------------------------------ block
def _block(kit, a):
    """Elements shared by the two dwellings of a block: ground slab, party
    wall, roof and vault structure, beam B2 middle, panel lining."""
    blk = Dw(a, +1)
    xa = blk.xa
    ue_w, ue_e = bedroom_end(a, +1)[0], bedroom_end(a, -1)[0]
    # ground-floor slab F3 (laterocemento 200, soffit -0.32 over the crawl space)
    I.prism(kit('FloorSlab', 'M_Structure'), blk.rect(-U_BS, U_BS, Y_NI, Y_SI), *GF_SLAB)
    # party wall 0.20 from the ground slab to the roof slabs / vault, three zones
    z0 = GF_SLAB[1]

    def seg(Y0, Y1, tops, layers):
        a_, b_ = blk.p(0, Y0), blk.p(0, Y1)
        L = (Y1 - Y0) * M
        _wall(kit, a_, b_, _notched(L, z0, [((Yt - Y0) * M, z) for Yt, z in tops]), layers, 'PartyWall')
    # flue / vent duct at the north end of the party wall, between the two boilers (n27, n45
    # hatched at both levels): a precast flue block in the wall's 0.20, plastered
    seg(Y_NI, Y_FLUE, [(Y_NI, RAW_BAR(xa, yY(Y_NI))), (Y_FLUE, RAW_BAR(xa, yY(Y_FLUE)))], PARTY_FLUE)
    seg(Y_FLUE, Y_BI, [(Y_FLUE, RAW_BAR(xa, yY(Y_FLUE))), (Y_BI, RAW_BAR(xa, yY(Y_BI)))], PARTY_SEP)
    z_cr = _arc(ZC_IN, R_SLAB)(U_PW) - 0.002                             # 2 mm under the vault slab
    seg(Y_BI, Y_HW, [(Y_BI, Z_LINTEL), (Y_BO + dY(PL), Z_LINTEL), (Y_BO + dY(PL), z_cr), (Y_PL, z_cr),
                     (Y_PL, Z_B2M), (Y_HW, Z_B2M)], PARTY_SPINE)
    seg(Y_HW, Y_SI, [(Y_HW, RAW_LEAN(xa, yY(Y_HW))), (Y_SI, RAW_LEAN(xa, yY(Y_SI)))], PARTY_SEP)
    # roof structure R1 under the tiles (lining per dwelling), across the party wall
    I.sloped_stack(kit, blk.rect(-ue_e, ue_w, Y_NI, Y_BI), TILE_BAR, ROOF_STRUCT, 'Roof', SLOPE_BAR)
    I.sloped_stack(kit, blk.rect(-U_BS, U_BS, Y_HW, Y_SI), TILE_LEAN, ROOF_STRUCT, 'Roof', SLOPE_LEAN)
    # vault R2: structure over the core masonry clear, timber zone up to the copper sheet
    xs = _grid(xa, xa - U_CM, xa + U_CM)
    y0, y1 = yY(Y_PB), yY(Y_BO)
    r = R_TOP
    for elem, mat, t in VAULT_STRUCT:
        _band(kit('Vault' + elem, mat), lambda x, r=r: _arc(ZC_IN, r)(x - xa),
              lambda x, r=r, t=t: _arc(ZC_IN, r - t)(x - xa), xs, y0, y1)
        r -= t
    _band(kit('VaultTimber', 'M_Wood'), lambda x: _arc(ZC_CU, X.CORE_VAULT_R)(x - xa) - 0.001,
          lambda x: _arc(ZC_IN, R_TOP)(x - xa), xs, y0, y1)
    # beam B2 middle under the oculus panel and the lean-to's high coping (SE 60 B-B "trave c.a.")
    I.prism(kit('Beams', 'M_Structure'), blk.rect(-U_CM, U_CM, Y_PB, Y_HW), Z_B2M, Z_BEAM)
    # oculus panel lining (0.08: insulation + plaster) from the beam to the vault slab
    xs = _grid(xa, xa - U_CL, xa + U_CL)
    soffit = lambda x: _arc(ZC_IN, R_SLAB)(x - xa)                        # noqa: E731
    _band(kit('WallLiningInsulation', 'M_Insulation'), soffit, lambda x: Z_B2M, xs, yY(Y_PB), yY(Y_PL + dY(0.015)))
    _band(kit('WallLiningBoard', 'M_PlasterInt'), soffit, lambda x: Z_B2M, xs, yY(Y_PL + dY(0.015)), yY(Y_PL))
    # plaster on the bar's south face inside the core, above the landing lintel
    _band(kit('WallPlaster', 'M_PlasterInt'), soffit, lambda x: Z_LINTEL, xs, yY(Y_BO), yY(Y_BO + dY(PL)))


# ------------------------------------------------------------------ dwelling
def _dwelling(kit, dw: Dw):
    s = dw.s
    ue, ext = dw.u_end, dw.end_kind == 'ext'
    t_end = LIN if ext else PLASTER[0][2]
    uf = ue - t_end                                    # finished face of the bedroom's far wall
    yNf, yBf, ySf = Y_NI + dY(LIN), Y_BI - dY(LIN), Y_SI - dY(LIN)   # finished faces (Y)
    pl = kit('CeilingPlaster', 'M_PlasterInt')
    beams = kit('Beams', 'M_Structure')

    # ---------------- L0: floor, linings, ceilings, beams B1 / B2 legs
    I.floor_stack(kit, dw.rect(U_PW, U_BS - LIN, yNf, ySf), 0.0, FIN_GF)
    zb = GF_SLAB[1]
    _layers_box(kit, 'Wall', B.LINING, dw, U_PW, U_BS, Y_NI, None, zb, RAW, 'Y', +1)          # N wall
    _layers_box(kit, 'Wall', B.LINING, dw, U_PW, U_BS, Y_SI, None, zb, CEIL_LEAN, 'Y', -1)    # S wall
    # block side wall: stepped top along Y (B1, slab under the terrace and B2, lean-to)
    face_a, face_b = dw.p(U_BS, yNf), dw.p(U_BS, ySf)
    L = (ySf - yNf) * M

    def sY(Y):
        return (Y - yNf) * M
    xs_ = dw.x(U_BS)
    tops = [(0.0, RAW), (sY(Y_BI), RAW), (sY(Y_BI), Z_B1 - PL), (sY(Y_BO), Z_B1 - PL), (sY(Y_BO), RAW),
            (sY(Y_HW + dY(LIN)), RAW), (sY(Y_HW + dY(LIN)), CEIL_LEAN(xs_, yY(Y_HW + dY(LIN)))),
            (L, CEIL_LEAN(xs_, yY(ySf)))]
    side = _door_cfg(face_a, face_b, 0.0, dw.p(U_BS - 1.0, 31.0))[1]       # room side of the face
    _wall(kit, face_a, face_b, _notched(L, zb, tops), B.LINING, 'Wall', side=side)
    # L0 ceilings: plaster under the L1 slab (kitchen, under the terrace)
    I.prism(pl, dw.poly([(U_PW, yNf), (U_BS - LIN, yNf), (U_BS - LIN, Y_BI - dY(PL)),
                         (U_VD - PL, Y_BI - dY(PL)), (U_VD - PL, Y_LND), (U_PW, Y_LND)]), RAW - PL, RAW)
    I.prism(pl, dw.rect(U_CL, U_BS - LIN, Y_BO, Y_HW + dY(LIN)), RAW - PL, RAW)    # terrace + B2, core lining
    # beam B1 under the bar's south wall (u 0.95 -> 3.275, soffit 2.40), plastered; the top of
    # the flight bears on the landing slab beside it
    dw.box(beams, U_VD, U_BS, Y_BI, Y_BO, Z_B1, RAW)
    dw.box(pl, U_VD - PL, U_BS, Y_BI - dY(PL), Y_BO + dY(PL), Z_B1 - PL, Z_B1)               # soffit
    dw.box(pl, U_VD - PL, U_BS - LIN, Y_BI - dY(PL), Y_BI, Z_B1, RAW - PL)                     # north face
    dw.box(pl, U_VD - PL, U_CL, Y_BO, Y_BO + dY(PL), Z_B1, SLAB_TOP)                          # south face, void
    dw.box(pl, U_CL, U_BS - LIN, Y_BO, Y_BO + dY(PL), Z_B1, RAW - PL)                          # ... under the terrace
    dw.box(pl, U_VD - PL, U_VD, Y_BI, Y_BO, Z_B1, RAW)                                         # end face
    # beam B2 legs: RC inside the lean-to's high wall behind the terrace's face brick, on the
    # slab (soffit flush with it, SE 60 A-A / elevation); its end is lined with the core walls
    dw.box(beams, U_CM, U_BS, Y_C + dY(B2_LEAF), Y_HW, SLAB_TOP, Z_B2L_TOP)
    # lean-to: lining on the high wall, sloping ceiling lining (R1 under the roof slab)
    _layers_box(kit, 'Wall', B.LINING, dw, U_CM, U_BS, Y_HW, None, RAW, CEIL_LEAN, 'Y', +1)
    I.sloped_stack(kit, dw.rect(U_PW, U_BS, Y_HW, Y_SI), RAW_LEAN, B.LINING, 'Ceiling', SLOPE_LEAN)
    # beam B2 middle (block object): soffit plaster per dwelling, south face strip
    # (the core lining wraps the leg's end under it and the corner beyond, see the core below)
    I.prism(pl, dw.poly([(U_PW, Y_PL), (U_CL, Y_PL), (U_CL, Y_PB), (U_CM, Y_PB), (U_CM, Y_HW), (U_CL, Y_HW),
                         (U_CL, Y_HW + dY(PL)), (U_PW, Y_HW + dY(PL))]), Z_B2M - PL, Z_B2M)
    I.prism(pl, dw.rect(U_PW, U_CL, Y_HW, Y_HW + dY(PL)), Z_B2M, CEIL_LEAN)

    # ---------------- L1: slab, floors, linings, partitions, doors, ceiling
    slab = kit('FloorSlab', 'M_Structure')
    I.prism(slab, dw.poly([(U_PW, Y_NI), (ue, Y_NI), (ue, Y_BI), (U_BS, Y_BI), (U_BS, Y_BO), (U_FL, Y_BO),
                           (U_FL, Y_LND), (U_PW, Y_LND)]), RAW, SLAB_TOP)
    I.prism(slab, dw.poly([(U_CM, Y_BO), (U_PP, Y_BO), (U_PP, Y_C), (U_BS, Y_C), (U_BS, Y_HW),
                           (U_CM, Y_HW)]), RAW, SLAB_TOP)                                        # terrace + B2
    # (the render under the slab over the porticoes: build(), per passage)
    yb0, yb1 = Y_BATH - dY(0.055), Y_BATH + dY(0.055)
    I.floor_stack(kit, dw.rect(U_PW, U_PART[0], yNf, yb0), T1, FIN_INT)                      # bathroom
    y_prp = Y_BO - dY(PARAPET_T)
    I.floor_stack(kit, dw.poly([(U_PW, yb1), (U_PART[0], yb1), (U_PART[0], y_prp), (U_FL, y_prp),
                                (U_FL, Y_LND), (U_PW, Y_LND)]), T1, FIN_INT)                 # landing
    # parapet over the void in the plane of the bar's S face (0.92 high, n5 F; 0.10, n45)
    yp = Y_BO - dY(PARAPET_T / 2)
    Lq = U_CL - U_FL - PL
    _wall(kit, dw.p(U_FL + PL, yp), dw.p(U_CL, yp), _notched(Lq, SLAB_TOP, [(0.0, Z_PARAPET), (Lq, Z_PARAPET)]),
          PARTITION_10, 'Partition')
    dw.box(kit('PartitionPlaster', 'M_PlasterInt'), U_FL, U_FL + PL, Y_BO - dY(PARAPET_T), Y_BO,
           SLAB_TOP, Z_PARAPET)                                                                # plastered free end
    dw.box(pl, U_FL, U_CL, Y_BO - dY(PARAPET_T), Y_BO, Z_PARAPET, Z_PARAPET + PL)           # plaster cap
    # the slab's corner beside the top of the flight (u 0.90 -> B1's end plaster): soffit, south edge
    dw.box(pl, U_FL, U_VD - PL, Y_LND, Y_BO, RAW - PL, RAW)
    dw.box(pl, U_FL, U_VD - PL, Y_BO, Y_BO + dY(PL), RAW - PL, SLAB_TOP)
    bed = dw.rect(U_PART[1], uf, yNf, yBf)
    I.floor_stack(kit, bed, T1, FIN_INT[:2])                                                   # bedroom
    I.floor_stack(kit, dw.rect(U_PART[1], U_BS, yNf, yBf), T1 - 0.06, FIN_INT[2:])          # over the kitchen
    I.floor_stack(kit, dw.rect(U_BS, uf, yNf, yBf), T1 - 0.06, FIN_OPEN[2:])                 # over the portico
    # door thresholds: the floor runs through the partitions' openings
    I.floor_stack(kit, dw.rect(*U_BATH_DOOR, yb0, yb1), T1, FIN_INT)
    I.floor_stack(kit, dw.rect(U_PART[0], U_PART[1], *Y_BED_DOOR), T1, FIN_INT)
    # wall linings: bar N wall (bath, bedroom), bar S wall (bedroom), far wall
    _layers_box(kit, 'Wall', B.LINING, dw, U_PW, U_PART[0], Y_NI, None, SLAB_TOP, CEIL_BAR, 'Y', +1)
    _layers_box(kit, 'Wall', B.LINING, dw, U_PART[1], ue, Y_NI, None, SLAB_TOP, CEIL_BAR, 'Y', +1)
    _layers_box(kit, 'Wall', B.LINING, dw, U_PART[1], ue, Y_BI, None, SLAB_TOP, CEIL_BAR, 'Y', -1)
    _layers_box(kit, 'Wall', B.LINING if ext else PLASTER, dw, ue, None, yNf, yBf, SLAB_TOP, CEIL_BAR, 'u', -1)
    # sloping ceiling lining under the bar roof slab (R1, SE 54 det. 3)
    I.sloped_stack(kit, dw.rect(U_PW, ue, Y_NI, Y_BI), RAW_BAR, B.LINING, 'Ceiling', SLOPE_BAR)
    # partitions 0.10 to the finished ceiling, with their doors
    xp = dw.x((U_PART[0] + U_PART[1]) / 2)
    a_, b_ = (xp, yY(Y_NI)), (xp, yY(Y_BI))
    Lp = (Y_BI - Y_NI) * M
    d0, d1 = ((Y - Y_NI) * M for Y in Y_BED_DOOR)
    tops = [(0.0, CEIL_BAR(xp, yY(Y_NI))), (Lp, CEIL_BAR(xp, yY(Y_BI)))]
    _wall(kit, a_, b_, _notched(Lp, SLAB_TOP, tops, [(d0, d1, DOOR_HEAD)]), PARTITION_10, 'Partition')
    hinge, swing = _door_cfg(a_, b_, d1, dw.p(3.0, 30.0))
    # parked at 60 deg: at 90 deg the leaf lies along the bar's south wall 0.23 in front of the
    # terrace door and laps its opening by 0.15 (hinge at the south jamb per the n45 arcs)
    I.door(kit, a_, b_, (d0 + d1) / 2, d1 - d0, DOOR_HEAD, T1, DOOR_T, hinge, swing, 60.0)
    a_, b_ = dw.p(U_PW, Y_BATH), dw.p(U_PART[0], Y_BATH)
    Lb = U_PART[0] - U_PW
    zt = CEIL_BAR(dw.x(1.0), yY(yb1))
    e0, e1 = U_BATH_DOOR[0] - U_PW, U_BATH_DOOR[1] - U_PW
    _wall(kit, a_, b_, _notched(Lb, SLAB_TOP, [(0.0, zt), (Lb, zt)], [(e0, e1, DOOR_HEAD)]), PARTITION_10,
          'Partition')
    hinge, swing = _door_cfg(a_, b_, e1, dw.p(1.0, 29.6))
    I.door(kit, a_, b_, (e0 + e1) / 2, e1 - e0, DOOR_HEAD, T1, DOOR_T, hinge, swing, 90.0)

    # ---------------- terrace (R3 on the slab, finish as built)
    I.floor_stack(kit, dw.rect(U_CO, U_PP, Y_BO, Y_C), Z_TERR, TERRACE_THIN, 'Terrace')

    # ---------------- core: wall lining (W2), vault lining, stair, balustrade
    xa = dw.xa
    cl = dw.x(U_CL)
    # (it stands on the L0 ceiling plaster, which runs under it to the void edge)
    _layers_box(kit, 'Wall', B.LINING, dw, U_CM, None, Y_BO, Y_PB, RAW,
                lambda x, y: _arc(ZC_IN, R_SLAB)(x - xa), 'u', -1)
    # ... on along the end of beam B2's leg under the B2 middle soffit plaster, and a solid
    # board corner where it meets the lean-to high wall's lining: no lining edge in view
    # (without the adhesive bed there: it would touch the high wall's along an edge only)
    no_bed = [(e, None if e == 'LiningAdhesive' else m, t) for e, m, t in B.LINING]
    _layers_box(kit, 'Wall', no_bed, dw, U_CM, None, Y_PB, Y_HW, RAW, Z_B2M - PL, 'u', -1)
    I.prism(kit('WallLiningBoard', 'M_PlasterInt'), dw.rect(U_CL, U_CM, Y_HW, Y_HW + dY(LIN)), RAW, CEIL_LEAN)
    xs = _grid(xa, dw.x(U_PW), cl)
    r = R_SLAB
    for elem, mat, t in B.LINING:
        _band(kit('Ceiling' + elem, mat), lambda x, r=r: _arc(ZC_IN, r)(x - xa),
              lambda x, r=r, t=t: _arc(ZC_IN, r - t)(x - xa), xs, yY(Y_PL), yY(Y_BO + dY(PL)))
        r -= t
    _flight(kit, dw)
    # balustrade on the void side: flat bars every 0.11, rail 1.00 above the nosings, stringer bar
    ub = (U_FL + U_VD) / 2
    p0 = Vector((*dw.p(ub, Y_FOOT + dY(0.02)), RISER - 0.20))
    s1 = (Y_FOOT - Y_BO) * M - 0.01                                     # up to the parapet's face
    p1 = Vector((*dw.p(ub, Y_FOOT - dY(s1)), RISER + (s1 + 0.02) * RISER / GOING - 0.20))
    I.handrail(kit, [p0, p1], height=1.20, post_every=0.11, rail_d=0.035, post_d=0.014)
    I.handrail(kit, [p0, p1], height=0.0, rail_d=0.03, posts=False)


# ------------------------------------------------------------------ build
def build(ctx) -> None:
    if geo.THROUGH is None:
        return
    _register_types()
    panel = bpy.data.objects.get('SM_Schiera_Panel')
    panel_recs = I.openings_of(panel.name) if panel else []
    for r in panel_recs:
        r['type'] = 'OS'
    for tag, E0, E1, axes in X.segments():
        body = bpy.data.objects[f'SM_Schiera_Body_{tag}']
        recs = [r for r in I.openings_of(body.name) if r['kind'] != 'arch']
        for r in recs:
            kind = J.classify(r)
            if kind in ('P', 'F'):
                r['type'] = kind + 'S'
        x_lo, x_hi = sorted((xE(E0), xE(E1)))
        precs = [r for r in panel_recs if x_lo < r['u'] < x_hi]
        # 1. hollow the body: rooms, slabs, core, beams' seats, joinery pockets
        cut, zones = bmesh.new(), []
        for a in axes:
            _cutter(cut, zones, a)
        _add_pockets(cut, recs)
        _trim_seats(cut, recs)
        zones += _pocket_zones(recs)
        I.hollow(ctx, body, cut)
        ports = _portico_rects(E0, E1)
        _paint(ctx, body, zones, skip=ports)
        # 2. layers, partitions, doors, stairs, joinery
        kit = I.Kit(ctx, PART, tag, COL)
        for a in axes:
            _block(kit, a)
            for s in (1, -1):
                _dwelling(kit, Dw(a, s))
        # render under the L1 slab over each portico passage, wall to wall and to its ends (as built)
        for x0, x1, y0, y1 in ports:
            I.prism(kit('PorticoRender', 'M_Plaster'), I.rect(x0, x1, y0, y1), RAW - PL, RAW)
        J.build_openings(kit, recs + precs)
        for r in precs:
            _oculus_reveal(kit, r)
        for r in recs:
            for part in _extra_parts(r):
                name = 'SillBlocks' if J.classify(r) == 'FS' else 'Thresholds'      # M_Concrete both
                I.face_box(kit(name, 'M_Concrete'), r, *part)
            if J.classify(r) == 'FS':
                _f_handle(kit, r)
            _niche_reveals(kit, r)
        objs = kit.flush()
        # 3. linings cut round the windows and doors (and the oculi)
        for name, o in objs.items():
            if name.startswith(f'SM_{PART}_Wall'):
                # the outlines are in lining_cutter already: cut_openings would add them a second
                # time (coincident solids -> a non-manifold cutter)
                I.cut_openings(ctx, o, [], extra=_lining_cutter(recs + precs))
