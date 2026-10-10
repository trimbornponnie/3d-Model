"""Tower interiors (docs/INTERIORS.md): the ten towers' stair halls, dwellings,
construction layers and joinery.

Research: scratchpad reports towers.md (rooms, walls, doors, stairs: n8 SE 36
L0, n56 SE 37 L1, n28 SE 38 L2, n46 SE 39 L3, n62 SE 41 sections K-K / A-A,
n74 SE 58 stair 1:10, n55 published type plans), layers.md (W1, W3, W5, W7,
F1-F3, R1-R3) and windows.md (joinery.py). Exterior: towers.py (guarded
edits only).

All ten towers are identical inside (towers.md T.0). The interior of the
east tower k is built on SM_Tower_Body_E<k>; the west tower k is its mirror
image in E (x -> -x), so the hollowed body, every layer object and the
joinery are mirrored into SM_Tower_*_W<k> exactly like towers.py mirrors the
exterior (_mirror below: mirror, flip the winding, no normal recalculation -
the bodies hold room cavities).

Drawing frame of one tower: E in modules (absolute, x = xE(E)), dY in metres
from the tower axis, + to the south (y = y_axis - dY). Per tower:

  L0  type A flat: living + kitchen (N pavilion), bedroom + bathroom (S),
      corridor E 2.05 -> 2.57 with the passage into the living room and the
      bedroom door; porch (exterior) behind the slot; common stair hall:
      lobby, flight 1 (8 risers) in the lower zone, half-landing in three
      strips, flight 2 (7 risers) in the upper zone - precast RC steps 13/35
      spanning between the walls, 17 x 0.177 (SE 58);
  L1  type A flat again (loggia instead of the porch), common landing with
      the two entrance doors (D1 type A, D2 type C duplex), the duplex
      vestibule in the lower zone and the private flight L1 -> L2
      (15 x 0.2007, 14 x 0.235, SE 58);
  L2  duplex night floor: bedrooms N, middle (under the lean-to) and S,
      bathroom, hall with the stairwell and the flight L2 -> L3;
  L3  duplex day floor: living room open to the stair hall, kitchen, shower
      room, two terraces; hall under the curved copper roof.

Construction layers: exterior walls W1 0.395 face brick + 0.055 insulated
lining; stair-hall outer wall W3 0.25 + lining; spine 0.30 (+ 0.03
insulation on the duplex side); L2 walls 0.25 + plaster; partitions W7 0.11
(L0 / L1) and 0.15 (L2 / L3, under the L3 hall wall); floors F3 / F1 / F2,
the common hall in cement; roofs R1 (pavilions, lean-to) and R2 (stair
hall) under the exterior tiles and copper; terraces R3, porch and loggia
paving.
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import buildups as B
from . import geo
from . import interior as I
from . import joinery as J
from . import towers as X
from .common import pavilion_section, xE, yY
from .params import FLOORS, MODULE as M, TOWER, WIN_SMALL

PART = 'Tower'
COL_E, COL_W = X.COL_E, X.COL_W


def e(m: float) -> float:
    """Metres -> modules (along E)."""
    return m / M


# ------------------------------------------------------------------ build-ups
W1 = B.WALL_EXT_MASONRY              # 0.395 face brick
LIN = B.LINING_T                     # 0.055 insulated lining
PL = 0.015                           # plaster on internal masonry
CPL = 0.010                          # ceiling plaster under the slabs
SLAB_T = 0.20
FIN_INT = B.FLOOR_INT[:3]            # parquet, screed, fill (F1, slab separate)
FIN_OPEN = B.FLOOR_OPEN[:3]          # parquet, screed, insulation (F2)
FIN_GF = B.FLOOR_GF[:4]              # parquet, screed, insulation, fill (F3)
HALL_GF = [('Floor', 'M_Screed', 0.030), ('Screed', 'M_Screed', 0.090)]     # cement floor (SE 58)
HALL_UP = [('Floor', 'M_Screed', 0.030), ('Screed', 'M_Screed', 0.070)]
# outdoor paving of porch, loggia and terraces: frost-proof cotto / klinker tiles (layers.md R3),
# M_Brick - the fired-clay red the exterior-only build shows on these floors
PORCH = [('Tiles', 'M_Brick', 0.020), ('Bed', 'M_Screed', 0.030), ('Falls', 'M_Screed', 0.070)]
LOGGIA = [('Tiles', 'M_Brick', 0.015), ('Bed', 'M_Screed', 0.025), ('Membrane', 'M_Membrane', 0.010),
          ('Falls', 'M_Screed', 0.050)]
TERRACE = [('Tiles', 'M_Brick', 0.015), ('Bed', 'M_Screed', 0.020), ('Membrane', 'M_Membrane', 0.010),
           ('Insulation', 'M_Insulation', 0.040), ('Falls', 'M_Screed', 0.015)]   # R3 on the slab, finish 9.02 as built
PARQ_T = FIN_INT[0][2]               # 0.015 parquet (radiator niches)
TREAD_MAT = 'M_DoorLeaf'             # hardwood treads of the private flights, oak like the parquet (towers.md T.5)
FPL = 0.015                          # plaster under the L2 -> L3 flight (inside the duplex)
PLASTER = [('Plaster', 'M_PlasterInt', PL)]
SPINE_DUP = [('SpineInsulation', 'M_Insulation', 0.030), ('Plaster', 'M_PlasterInt', PL)]   # SE 58 "33 ISOLAZIONE"
HALLWALL = [('LiningInsulation', 'M_Insulation', 0.020), ('LiningBoard', 'M_PlasterInt', 0.010)]
PART_WET = B.PARTITION_WET           # 0.15 under the L3 hall wall
PART_STD = B.PARTITION               # 0.11
ROOF_STRUCT = [l for l in B.ROOF_TILE_UNDER if not l[0].startswith('Lining')]    # 0.205 under the tiles
# R2 under the copper: the drawn layers (membrane, insulation, topping, curved slab; 0.205) right
# under the exterior's 60 mm copper shell, which stands for copper + boarding + battens (layers.md
# R2 rule: keep the drawn layers, the assumed boarding / batten zone takes up the rest)
VAULT_STRUCT = [l for l in B.ROOF_VAULT_UNDER
                if not l[0].startswith('Lining') and l[0] not in ('Boarding', 'Battens')]
UNDER_FLIGHT = [('FlightInsulation', 'M_Insulation', 0.040), ('FlightPlaster', 'M_PlasterInt', 0.020)]

# ------------------------------------------------------------------ E lines (modules)
E_OUT = TOWER['e_outer']             # -0.20 outer face
E_OW = E_OUT + e(W1)                 # 0.0394 outer wall, masonry face (L0-L2)
E_SB = TOWER['e_band']               # 0.78 recessed / set-back wall, outer face
E_SBI = E_SB + e(W1)                 # 1.0194 its masonry face (L2, L3)
E_PO = E_SB + e(X.SLOT['wall'])      # 1.0042 recessed wall behind porch / loggia (as cut by towers.py)
E_BW = E_SB + e(X.POCKET['depth'])   # 1.78 back wall, porch face
E_BWI = E_BW + e(W1)                 # 2.0194
E_HO = 2.759                         # stair-hall outer wall, hall face (SE 58)
E_HOI = E_HO - e(0.25)               # 2.6075 its corridor-side masonry face (25 face brick)
E_SPU = 3.262 + e(PL)                # spine masonry, upper-zone side (SE 58 "30", plastered)
E_SPL = 3.444 - e(PL)                # spine masonry, lower-zone side
E_IW = TOWER['e_inner'] - e(W1)      # 3.9806 inner wall masonry face (pavilions and middle)
E_HW = X.E_HALL                      # 2.86 L3 hall wall outer face (as built) = L2 / L3 partition face
E_HWI = E_HW + e(0.12)               # 2.9327 L3 hall wall masonry face
E_P2 = E_HW + e(0.15)                # 2.9509 L2 / L3 partitions' east face = L3 hall finished face
E_P0 = (2.88, 2.88 + e(0.11))        # L0 / L1 kitchen and bathroom partitions (n8, n56)
# finished faces
EF_OW, EF_SB, EF_IW = E_OW + e(LIN), E_SBI + e(LIN), E_IW - e(LIN)
EF_BW, EF_HO = E_BWI + e(LIN), E_HOI - e(LIN)
EF_SPD = E_SPL + e(0.045)            # 3.4622 spine, duplex side = stairwell edge at L2 / L3
EF_SPW = EF_SPD - e(PL)              # slabs at the stairwell's spine side stop behind its edge plaster
EF_SPU, EF_SPL = E_SPU - e(PL), E_SPL + e(PL)     # 3.262 / 3.444 spine plaster in the hall
EF_IWH = E_IW - e(PL)                # inner wall plaster in the hall

# ------------------------------------------------------------------ dY lines (m, + south)
D_END = TOWER['length'] * M / 2      # 6.145 end face
D_ENDI = D_END - W1                  # 5.75 end wall masonry face
D_MID = TOWER['mid'] * M / 2         # 2.105 middle part / pavilion middle-side face
D_PW = D_MID + W1                    # 2.50 pavilion middle-side wall, room-side masonry face
D_L2W = 2.25                         # L2 walls (25) and the L1 vestibule's north wall, middle-side face
DF_END, DF_PW = D_ENDI - LIN, D_PW + LIN          # 5.695 / 2.555 finished
DF_PW2 = D_PW + PL                   # L2 pavilion wall, plastered room face (n28: 25 + plaster)
D_LOBBY = -0.855                     # lobby end / flight 1 foot (SE 58 "125")
D_HL = 1.245                         # half-landing edge (SE 58 "335")
D_L1L = -0.555                       # L1 landing end (SE 58 "155")
D_D1 = (-1.900, -0.990)              # D1 / D2 openings (SE 58 "20,5 | 91")
D_VF, D_VT = -0.905, 2.385           # private flights: first and last riser (SE 58 "132", 14 x 23,5)
D_BATH2 = (-3.56, -3.45)             # L2 bathroom partition (n28)
D_SHOW3 = (3.50, 3.61)               # L3 shower-room partition (n46)
SJ = 0.06                            # D13 / D16: jamb by the long partition (architraves clear of it)
SILL_T = 0.03                        # stone sills of the entrance doors D1 / D2

# ------------------------------------------------------------------ levels
Z0, Z1, Z2, Z3 = FLOORS
GF_SOFFIT = B.GF_SOFFIT              # -0.32
RAW = (None, Z1 - B.FLOOR_T, Z2 - B.FLOOR_T, Z3 - B.FLOOR_T)    # slab soffits 2.71 / 5.72 / 8.72
DOOR_H = 2.10                        # interior doors (n62 K-K "2,10")
Z_HLAND = 3.80                       # spine strip open over the half-landing (headroom 2.03)
Z_BEAM2 = 8.36                       # L2 downstand over the inner strip, north line (n62 K-K)
Z_BEAM3 = 11.20                      # L3 inner-strip openings (beam under the pavilion roofs)
HALL_RISER, HALL_GOING = Z1 / 17, 0.30                           # SE 58: 17 x 17,7, treads 30
STEP_T, STEP_LAP = 0.13, 0.05        # precast steps "13/35"
FL_GOING, FL_N = 0.235, 15           # private flights 15 risers, 14 x 23,5 (SE 58)
FL_WAIST, FL_TREAD, FL_NOSE = 0.12, 0.03, 0.02


def _flight_geom(z0: float, riser: float):
    """Soffit of a private flight (interior.flight's profile) as a function
    of dY, its flat foot end, the top-end soffit level and the top level."""
    zt = z0 - FL_TREAD
    slope = riser / FL_GOING
    w_v = FL_WAIST / math.cos(math.atan(slope))
    s_hit = w_v / slope
    s_top = (FL_N - 1) * FL_GOING          # = interior.flight(n_risers=14, tread_top_last=True)

    def soffit(d):
        s = d - D_VF
        return zt if s <= s_hit else zt + slope * s - w_v
    return soffit, D_VF + s_hit, zt + slope * s_top - w_v, slope


SOFF1, D_HIT1, Z_SOFTOP1, SLOPE1 = _flight_geom(Z1, (Z2 - Z1) / FL_N)
SOFF2, D_HIT2, Z_SOFTOP2, SLOPE2 = _flight_geom(Z2, (Z3 - Z2) / FL_N)


# ------------------------------------------------------------------ helpers
def _snap(vals, tol=5e-4):
    """Sorted distinct values, those closer than tol merged (no slivers)."""
    out = []
    for v in sorted(vals):
        if not out or v - out[-1] > tol:
            out.append(v)
    return out


def _faces(a0, a1, z0, z1, holes, tol=5e-4):
    """Rectangle [a0, a1] x [z0, z1] minus the union of hole rectangles as
    [(outer, [inner, ...]), ...]: the outlines (a, z) of the free grid cells,
    outer loops counter-clockwise with the hole loops inside them - one solid
    with real holes per piece of wall (fewer triangles than a rectangle
    cover)."""
    if z1 - z0 < tol or a1 - a0 < tol:
        return []
    hs = []
    for h0, h1, k0, k1 in holes:
        h0, h1 = max(min(h0, h1), a0), min(max(h0, h1), a1)
        k0, k1 = max(k0, z0), min(k1, z1)
        if h1 - h0 > tol and k1 - k0 > tol:
            hs.append((h0, h1, k0, k1))
    if not hs:
        return [([(a0, z0), (a1, z0), (a1, z1), (a0, z1)], [])]
    us = _snap([a0, a1] + [v for h in hs for v in h[:2]], tol)
    zs = _snap([z0, z1] + [v for h in hs for v in h[2:]], tol)
    us[0], us[-1], zs[0], zs[-1] = a0, a1, z0, z1
    nu, nz = len(us) - 1, len(zs) - 1
    free = [[not any(h[0] < (us[i] + us[i + 1]) / 2 < h[1] and h[2] < (zs[j] + zs[j + 1]) / 2 < h[3] for h in hs)
             for j in range(nz)] for i in range(nu)]

    def ok(i, j):
        return 0 <= i < nu and 0 <= j < nz and free[i][j]
    edges = {}
    for i in range(nu):
        for j in range(nz):
            if not free[i][j]:
                continue
            if not ok(i, j - 1):
                edges.setdefault((i, j), []).append((i + 1, j))
            if not ok(i + 1, j):
                edges.setdefault((i + 1, j), []).append((i + 1, j + 1))
            if not ok(i, j + 1):
                edges.setdefault((i + 1, j + 1), []).append((i, j + 1))
            if not ok(i - 1, j):
                edges.setdefault((i, j + 1), []).append((i, j))
    loops = []
    while edges:
        start = next(iter(edges))
        loop, cur, prev = [start], start, None
        while True:
            nxt = edges[cur]
            if len(nxt) > 1 and prev is not None:           # pinch: keep the free cells on the left
                d0 = (cur[0] - prev[0], cur[1] - prev[1])
                nxt.sort(key=lambda q: -(d0[0] * (q[1] - cur[1]) - d0[1] * (q[0] - cur[0])))
            q = nxt.pop(0)
            if not nxt:
                del edges[cur]
            prev, cur = cur, q
            if cur == start:
                break
            loop.append(cur)
        pts = [(us[i], zs[j]) for i, j in loop]
        n = len(pts)
        simp = [pts[k] for k in range(n)
                if abs((pts[k][0] - pts[k - 1][0]) * (pts[(k + 1) % n][1] - pts[k][1])
                       - (pts[k][1] - pts[k - 1][1]) * (pts[(k + 1) % n][0] - pts[k][0])) > 1e-12]
        loops.append(simp)
    outers = [lp for lp in loops if I.area(lp) > 0]
    inners = [lp for lp in loops if I.area(lp) < 0]
    groups = [(o, []) for o in outers]

    def inside(pt, poly):
        x, y = pt
        c = False
        for k in range(len(poly)):
            (xa, ya), (xb, yb) = poly[k - 1], poly[k]
            if (ya > y) != (yb > y) and x < xa + (y - ya) * (xb - xa) / (yb - ya):
                c = not c
        return c
    for h in inners:
        probe = ((h[0][0] + h[1][0]) / 2 + 1e-5, (h[0][1] + h[1][1]) / 2 + 1e-5)
        for o, ins in groups:
            if inside(h[0], o) or inside(probe, o):
                ins.append(h)
                break
    return groups


def _fill(loops) -> list[tuple[int, int, int]]:
    """Triangles (indices into the concatenated loops) filling a planar (a, z)
    outline with holes: bmesh triangle fill with beauty rotation, which,
    unlike a plain scanline fill, leaves no zero-area triangles where hole
    edges line up."""
    bm = bmesh.new()
    flat = [p for lp in loops for p in lp]
    vs = [bm.verts.new((a, z, 0.0)) for a, z in flat]
    es, o = [], 0
    for lp in loops:
        n = len(lp)
        es += [bm.edges.new((vs[o + k], vs[o + (k + 1) % n])) for k in range(n)]
        o += n
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es, normal=(0.0, 0.0, 1.0))
    bm.verts.index_update()
    tris = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return tris


def _lining_rects(r) -> list[tuple]:
    """(u0, u1, z0, z1) rectangles an opening takes out of the wall lining:
    the opening, the frame pocket behind a stop jamb (its reveal plaster runs
    to the finished face), the window board, the radiator niche and the RC
    threshold of French doors. The lining runs on over the lintel and the
    sill block (joinery.lining_cutter cuts their pockets as well, which
    would leave 55 mm deep bands of bare concrete over and under every
    window)."""
    kind = J.classify(r)
    u0, u1, z0, z1 = J.dims(r)
    out = [(u0, u1, z0, z1)]
    if kind is None:
        return out
    s = J.spec_for(kind)
    zf = J.floor_of(z0)
    maz = J.MAZ
    if s['jamb'] == 'stop' and r['kind'] == 'rect':
        out.append((u0 - maz, u1 + maz, z0, z1 + maz))
    if not s['door'] and s['board'] and r['kind'] == 'rect' and z0 - zf > 0.5:
        e = maz + 0.02 if s['jamb'] == 'stop' else 0.02
        out.append((u0 - e, u1 + e, z0 - 0.025, z0))
    if s['niche'] and r['kind'] == 'rect':
        out.append((u0 - maz, u1 + maz, zf - PARQ_T, z0 - 0.13))     # down to the niche parquet
    if s['door'] and kind in ('C', 'D') and z0 - zf > 0.01:
        out.append((u0 - maz, u1 + maz, zf - 0.02, z0))
    return out


def _door_cfg(a, b, s_hinge, s_centre, room):
    """hinge ('a' / 'b': the door's jamb on the a or b side) and swing (+1 =
    left of a -> b / -1) of a door centred s_centre metres from a, hinged on
    its jamb at s_hinge and opening into the side of the point `room`."""
    A, Bv = Vector(a), Vector(b)
    ev = (Bv - A).normalized()
    n = Vector((-ev.y, ev.x))
    return ('a' if s_hinge < s_centre else 'b'), (1 if n.dot(Vector(room) - A) > 0 else -1)


def _wall(kit, a, b, outline_sz, layers, prefix):
    """Wall on the plan centreline a -> b: each layer the (s, z) outline
    extruded across it, layers listed from the left face (seen from a)."""
    T = sum(t for _, _, t in layers)
    t0 = T / 2
    for elem, mat, t in layers:
        if mat is not None:
            I.oprism(kit(prefix + elem, mat), a, b, outline_sz, t0 - t, t0)
        t0 -= t


def _notched(L, z0, tops, doors=()):
    """(s, z) outline of a wall of length L from z0, top polyline tops
    [(s, z), ...] from s = 0 to s = L, door notches [(s0, s1, head)]."""
    out = [(0.0, z0)]
    for s0, s1, head in sorted(doors):
        out += [(s0, z0), (s0, head), (s1, head), (s1, z0)]
    out.append((L, z0))
    out += list(reversed(tops))
    return out


def _register_types() -> None:
    """Tower opening types not in joinery.TYPES: the dwelling entrance doors in
    the 0.25 stair-hall wall (D1) and the 0.30 spine (D2), frame flush with the
    dwelling face (SE 53 B, SE 65; no lintel: the 0.395 L-lintel would stand
    out of these walls), and the street door, framed flush with the inner face
    of the 0.23 inner wall left behind the as-built face E 4.12 (the exterior
    steps end on it, towers.ENTRANCE_FRAME). 'FT', 'ET' and 'E1T' are the
    casement windows of types F, E and E1 with their handles built here
    (window_handles, at mid-sash): joinery.opening puts a window's handle at
    min(z_f + 1.05, ...), which lands on the bottom rail of the E / E1
    sashes (sill z_f + 0.94) and 38 cm below the F sash (sill z_f + 1.43)."""
    J.TYPES.setdefault('FT', dict(J.TYPES['F'], handle=False))
    J.TYPES.setdefault('ET', dict(J.TYPES['E'], handle=False))
    J.TYPES.setdefault('E1T', dict(J.TYPES['E1'], handle=False))
    J.TYPES.setdefault('PTW', dict(J.TYPES['P'], lintel=False, frame_at=0.25 + LIN - 0.065))
    J.TYPES.setdefault('PTS', dict(J.TYPES['P'], lintel=False, frame_at=0.30 + 0.03 - 0.065))
    J.TYPES.setdefault('PTE', dict(J.TYPES['PT'], frame_at=X.ENTRANCE_FRAME))


def _pockets(r) -> list[tuple]:
    """joinery.pockets(r); pockets that start on the outer face start 1 cm in
    front of it (a cutter face coplanar with the façade leaves double faces),
    a stop pocket sitting on a threshold pocket reaches 0.5 mm into it
    (shared corners), and the radiator niche reaches PARQ_T below the floor
    for the parquet that runs into it (niche_finishes)."""
    kind = J.classify(r)
    zn = None
    if kind is not None and r['kind'] == 'rect' and J.spec_for(kind)['niche']:
        zn = J.floor_of(J.dims(r)[2])
    ps = [(u0, u1, z0 - PARQ_T if zn is not None and abs(z0 - zn) < 1e-9 and abs(d0 - J.STOP) < 1e-9 else z0,
           z1, -0.01 if d0 <= 0.0 else d0, d1) for u0, u1, z0, z1, d0, d1 in J.pockets(r)]
    out = []
    for p in ps:
        u0, u1, z0, z1, d0, d1 = p
        for q in ps:
            if q is not p and abs(q[3] - z0) < 1e-9 and abs(q[0] - u0) < 1e-9 and abs(q[1] - u1) < 1e-9 \
                    and q[4] <= d0 + 1e-9 and d1 <= q[5] + 1e-9:
                z0 -= 0.0005
        out.append((u0, u1, z0, z1, d0, d1))
    return out


def _hollow(ctx, body, volumes):
    """interior.hollow with the cutter's shells kept apart (merge=False): the
    rooms are separate overlapping or touching prisms, whose welded corners
    would make the cutter non-manifold."""
    if not len(volumes.faces):
        volumes.free()
        return
    cutter = geo.object_from_bmesh(volumes, f'{body.name}_CutInt', ctx.cutters, merge=False)
    mod = body.modifiers.new('Bool_Interior', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.use_self = True
    mod.object = cutter
    geo.apply_modifiers(body)
    geo.cleanup(body, dist=1e-6, recalc=False)


def _mirror_mesh(src: bpy.types.Object, name: str) -> bpy.types.Mesh:
    """Mesh of `src` mirrored x -> -x (E' = 72 - E) with the winding flipped
    back; normals are not recalculated (cavities stay cavities)."""
    me = src.data.copy()
    me.name = name
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.transform(bm, matrix=Matrix.Scale(-1.0, 4, (1.0, 0.0, 0.0)), verts=bm.verts)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return me


# ------------------------------------------------------------------ one tower
class _Tower:
    """Interior of the east tower k."""

    def __init__(self, ctx, k: int):
        self.ctx, self.k = ctx, k
        self.tw = X._Tower(ctx, k)                  # coordinates only
        self.yt = yY(self.tw.Yt)
        self.body = bpy.data.objects[self.tw.name('Body')]
        self.kit = I.Kit(ctx, PART, f'E{k}', COL_E)
        self.cut = bmesh.new()
        self.zones = []                             # (x0, x1, y0, y1, z0, top) painted M_PlasterInt
        self.edged = set()                          # kit objects with plastered edge faces (slot 1)
        # roof planes: tile undersides (towers.roofs) of the N / S pavilions and the lean-to
        self.tile = {}
        for s, (Ye, Yi) in zip((-1, 1), self.tw.pavs):
            sec = pavilion_section(Yi, Ye, X.Z_FOUND, X.T)
            (yl, zl), (yh, zh) = sec[5], sec[4]
            m = (zh - zl) / (yh - yl)
            self.tile[s] = ((lambda x, y, yl=yl, zl=zl, m=m: zl + m * (y - yl)), abs(m))
        xa, xb = xE(X.E_BAND), xE(X.E_HALL)
        self.lean_slope = (TOWER['mid_lean_high'] - TOWER['mid_lean_low']) / (xa - xb)

    # -------------------------------------------------------------- frame
    def x(self, E):
        return xE(E)

    def y(self, d):
        return self.yt - d

    def p(self, E, d):
        return (xE(E), self.yt - d)

    def R(self, E0, E1, d0, d1):
        return I.rect(xE(E0), xE(E1), self.yt - d0, self.yt - d1)

    def d_of(self, yw):
        return self.yt - yw

    def E_of(self, xw):
        return 36.0 - xw / M

    # -------------------------------------------------------------- roof planes
    def tile_under(self, s):
        return self.tile[s][0]

    def roof_raw(self, s):
        f, m = self.tile[s]
        k = math.sqrt(1 + m * m)
        return lambda x, y: f(x, y) - B.total(ROOF_STRUCT) * k

    def roof_ceil(self, s):
        f, m = self.tile[s]
        k = math.sqrt(1 + m * m)
        return lambda x, y: f(x, y) - (B.total(ROOF_STRUCT) + LIN) * k

    def lean_under(self, x, y=0.0):
        return X._lean_z(x) - 0.05

    def lean_raw(self, x, y=0.0):
        return self.lean_under(x) - B.total(ROOF_STRUCT) * math.sqrt(1 + self.lean_slope ** 2)

    def lean_ceil(self, x, y=0.0):
        return self.lean_under(x) - (B.total(ROOF_STRUCT) + LIN) * math.sqrt(1 + self.lean_slope ** 2)

    def hall_stations(self, E0, E1):
        """x stations for the stair-hall vault between E0 and E1: the copper's
        stations (towers._hall_xs) inside, plus the end points."""
        xs, xi = xE(X.E_HALL), xE(X.E_IN_MID)
        st = X._hall_xs(xi, xs)
        lo, hi = sorted((xE(E0), xE(E1)))
        return [lo] + [v for v in sorted(st) if lo + 1e-4 < v < hi - 1e-4] + [hi]

    def copper_under(self, x):
        """Underside of the copper shell: the polyline through its stations."""
        xs, xi = xE(X.E_HALL), xE(X.E_IN_MID)
        st = sorted(X._hall_xs(xi, xs))
        for a, b in zip(st[:-1], st[1:]):
            if a - 1e-9 <= x <= b + 1e-9:
                za, zb = X._hall_z(a), X._hall_z(b)
                return za + (zb - za) * (x - a) / (b - a) - 0.06
        return X._hall_z(x) - 0.06

    def vault_raw(self, x):
        return self.copper_under(x) - B.total(VAULT_STRUCT)

    def vault_ceil(self, x):
        return self.vault_raw(x) - LIN

    # -------------------------------------------------------------- cutter
    def cbox(self, E0, E1, d0, d1, z0, z1, paint=False, ptop=None):
        I.prism(self.cut, self.R(E0, E1, d0, d1), z0, z1)
        if paint:
            self.zone(E0, E1, d0, d1, z0, ptop if ptop is not None else z1)

    def zone(self, E0, E1, d0, d1, z0, top):
        xs = sorted((xE(E0), xE(E1)))
        ys = sorted((self.y(d0), self.y(d1)))
        self.zones.append((xs[0], xs[1], ys[0], ys[1], z0, top))

    def cutter(self, recs):
        t = self
        for s in (-1, 1):
            def D(a, b):
                return (s * a, s * b) if s > 0 else (s * b, s * a)
            # pavilion rooms: outer band part (L0-L2) and the rest up to the roof
            t.cbox(E_OW, E_SBI + 0.006, *D(D_PW, D_ENDI), GF_SOFFIT, RAW[3], paint=True)
            I.prism(t.cut, t.R(E_SBI, E_IW, *D(D_PW, D_ENDI)), GF_SOFFIT,
                    lambda x, y, f=t.tile_under(s): f(x, y) + 0.01)
            t.zone(E_SBI, E_IW, *D(D_PW, D_ENDI), GF_SOFFIT, t.roof_raw(s))
            # L3 terrace: slab zone over the L2 room, layers between the parapets
            t.cbox(E_OW, E_SB, *D(D_PW, D_ENDI), RAW[3] - 0.02, RAW[3] + SLAB_T + 0.005)
            pt = TOWER['terrace_parapet_t']
            t.cbox(E_OUT + e(pt), E_SB, *D(D_MID + pt, D_END - pt), RAW[3] + SLAB_T, Z3 + 0.01)
            # L2 inner strip through the pavilion wall: downstand in the N (n62 K-K), none in the S
            t.cbox(E_HW, E_IW, *D(D_MID - 0.005, D_PW + 0.01), RAW[2], Z_BEAM2 if s < 0 else RAW[3], paint=True)
            # L3 inner strip openings under the beams carrying the pavilion roofs
            t.cbox(E_P2, E_IW, *D(D_MID - 0.01, D_PW + 0.01), RAW[3] if s < 0 else RAW[3] - 0.02, Z_BEAM3,
                   paint=True)
        # middle part: porch + loggia (exterior), corridor, stair zones
        t.cbox(E_PO, E_BW, -D_MID, D_MID, GF_SOFFIT, RAW[2])
        t.cbox(E_BWI, E_HOI, -D_MID, D_MID, GF_SOFFIT, RAW[2], paint=True)
        t.cbox(E_HO, E_SPU, -D_MID, D_MID, GF_SOFFIT, RAW[2])
        t.cbox(E_SPL, E_IW, -D_MID, D_MID, GF_SOFFIT, RAW[3])
        t.cbox(E_HO + 0.004, E_IW - 0.004, -D_MID, D_LOBBY, GF_SOFFIT, RAW[1])          # lobby
        t.cbox(E_SPU - 0.004, E_SPL + 0.004, D_HL, D_MID, GF_SOFFIT, Z_HLAND)           # over the half-landing
        t.zone(E_SPU - 0.004, E_SPL + 0.004, D_HL - 0.005, D_MID, GF_SOFFIT, Z_HLAND + 0.005)
        t.zone(E_SPU - 0.004, E_SPL + 0.004, -D_MID, D_LOBBY + 0.005, GF_SOFFIT, RAW[1] + 0.005)
        t.cbox(E_SPL, E_IW, -D_L2W, -D_MID + 0.005, RAW[1], RAW[2], paint=True)          # vestibule, N
        # L1 flight top over the S wall, under the flight's soffit
        prof = [(t.y(D_MID - 0.005), SOFF1(D_MID - 0.005)), (t.y(D_VT), Z_SOFTOP1),
                (t.y(D_VT), RAW[2] + 0.01), (t.y(D_MID - 0.005), RAW[2] + 0.01)]
        geo.add_prism_x(t.cut, prof, xE(E_IW), xE(E_SPL))
        # L2: inner strip of the middle, middle bedroom under the lean-to
        t.cbox(E_HW - 0.01, E_IW, -D_MID, D_MID, RAW[2], RAW[3], paint=True)
        I.prism(t.cut, t.R(E_SBI, E_HW, -D_MID, D_MID), RAW[2], lambda x, y: t.lean_under(x) + 0.01)
        I.prism(t.cut, t.R(E_SBI, E_HW, -D_L2W, D_L2W), RAW[2], lambda x, y: t.lean_raw(x))
        t.zone(E_SBI, E_HW + 0.002, -D_L2W, D_L2W, RAW[2], lambda x, y: t.lean_raw(x) + 0.005)
        # L3 hall under the copper roof
        xs = t.hall_stations(E_HWI, E_IW)
        prof = [(xs[0], RAW[3] - 0.02), (xs[-1], RAW[3] - 0.02)] + \
               [(v, t.copper_under(v) + 0.01) for v in reversed(xs)]
        geo.add_prism_y(t.cut, prof, t.y(D_MID), t.y(-D_MID))
        t.zones.append((xs[0], xs[-1], t.y(D_MID), t.y(-D_MID), RAW[3], lambda x, y: t.vault_raw(x)))
        # passages and doors through the masonry
        for zf, z0 in ((Z0, GF_SOFFIT), (Z1, RAW[1])):
            t.cbox(EF_BW, EF_HO, -D_PW - 0.01, -D_MID + 0.005, z0, zf + DOOR_H, paint=True)    # D6 passage
            ec = (EF_BW + EF_HO) / 2
            st = zf - (0.12 if zf == Z0 else 0.10)
            t.cbox(ec - e(0.40), ec + e(0.40), D_MID - 0.005, D_PW + 0.01, st, zf + DOOR_H)  # D7 door
            t.cbox(E_HOI - 0.006, E_HO + 0.006, *D_D1, zf - SILL_T, zf + 2.07)               # D1 door + sill
        t.cbox(E_SPU - 0.006, E_SPL + 0.006, *D_D1, Z1 - SILL_T, Z1 + 2.07)                 # D2 door + sill
        # registered openings: my own French doors D4, joinery pockets, trim seats
        for r in recs:
            if r.get('own'):
                geo.Face(r['axis'], r['coord'], r['out']).solid(t.cut, r['outline'], 0.70, outside=0.15)
            for u0, u1, z0, z1, d0, d1 in _pockets(r):
                I.face_box(t.cut, r, u0, u1, z0, z1, d0, d1)
        t.trim_seats(recs)
        for r in recs:
            kind = J.classify(r)
            if kind is None or r['kind'] != 'rect':
                continue
            sp = J.spec_for(kind)
            u0, u1, z0, z1 = J.dims(r)
            zf = J.floor_of(z0)
            maz, d_in = J.MAZ, J.FINISH + 0.05
            if kind == 'K':
                # reveals of the stair windows (frame flush with the outer face): plaster
                t.fzone(r, u0 - 0.005, u1 + 0.005, z0 - 0.005, z1 + 0.005, 0.005, 0.40)
            if sp['jamb'] == 'stop':
                # frame pocket behind the stop: its jambs and head show 1 cm beside the frame
                t.fzone(r, u0 - maz, u1 + maz, z0, z1 + maz, J.STOP, d_in)
            if sp['niche']:
                # radiator niche (pocket sunk by PARQ_T, _pockets): jambs plastered (paint)
                t.fzone(r, u0 - maz, u1 + maz, zf - PARQ_T, z0 - 0.13, J.STOP, d_in)

    def fzone(self, r, u0, u1, z0, z1, d0, d1):
        """Paint zone over a box in an opening's face frame (joinery.Frame3)."""
        c0, c1 = sorted((r['coord'] - r['out'] * d0, r['coord'] - r['out'] * d1))
        a0, a1 = sorted((u0, u1))
        if r['axis'] == 'x':
            self.zones.append((c0, c1, a0, a1, z0, z1))
        else:
            self.zones.append((a0, a1, c0, c1, z0, z1))

    def trim_seats(self, recs):
        """The exterior's concrete head bands (5 cm into the brick), the L3 band
        ring and the sills (11.5 cm) sit where the joinery pockets start: cut
        that brick too, so trim and body share no face (z-fighting)."""
        for r in recs:
            kind = J.classify(r)
            if kind is None or r['kind'] != 'rect':
                continue
            sp = J.spec_for(kind)
            u0, u1, z0, z1 = J.dims(r)
            zf = J.floor_of(z0)
            if sp['lintel']:
                band = None
                if abs(z1 - (zf + X.HEAD)) < 1e-3 and zf < Z3 - 0.1:
                    band = (zf + X.HEAD + 0.002, zf + X.HEAD + X.BAND_H)
                elif zf > Z3 - 0.1 and abs(z1 - 11.37) < 1e-3:
                    band = X.L3_BAND
                if band is not None and r['axis'] == 'x' and abs(r['coord'] - xE(1.78)) > 0.01:
                    I.face_box(self.cut, r, u0 - 0.12, u1 + 0.12, band[0], band[1], -0.01, X.BAND_IN)
            if not sp['door'] and sp['board'] and z0 - zf > 0.5:
                I.face_box(self.cut, r, u0 - 0.05, u1 + 0.05, z0 - 0.05, z0, -0.01, 0.115)

    # -------------------------------------------------------------- records
    def records(self):
        recs = [r for r in I.openings_of(self.body.name)]
        own_handles = {'F': 'FT', 'E': 'ET', 'E1': 'E1T'}
        for r in recs:
            if J.classify(r) == 'PT':
                r['type'] = 'PTE'
            elif J.classify(r) in own_handles:
                r['type'] = own_handles[J.classify(r)]
        own = []
        # D4: French doors porch / loggia -> living room (N) and bedroom (S), SE 53 D 77,5 x 225
        w, ec = 0.775, 1.45
        for s in (-1, 1):
            face = geo.Face('y', self.y(s * D_MID), 1 if s > 0 else -1)
            for zf in (Z0, Z1):
                u = xE(ec)
                outline = [(u - w / 2, zf + 0.10), (u + w / 2, zf + 0.10), (u + w / 2, zf + 2.35), (u - w / 2, zf + 2.35)]
                own.append(geo.register(face, outline, 'rect', u=u, z0=zf + 0.10, width=w, height=2.25))
                own[-1]['type'] = 'D'
        # D1 (type A entrance, stair-hall outer wall) and D2 (duplex entrance, spine)
        for E_f, typ, zfs in ((E_HO, 'PTW', (Z0, Z1)), (EF_SPU, 'PTS', (Z1,))):
            face = geo.Face('x', xE(E_f), -1 if typ == 'PTW' else 1)
            for zf in zfs:
                u0, u1 = sorted((self.y(D_D1[0]), self.y(D_D1[1])))
                outline = [(u0, zf), (u1, zf), (u1, zf + 2.07), (u0, zf + 2.07)]
                own.append(geo.register(face, outline, 'rect', u=(u0 + u1) / 2, z0=zf, width=u1 - u0, height=2.07))
                own[-1]['type'] = typ
        for r in own:
            r['target'] = self.body.name
            r['own'] = r['type'] == 'D'
        return recs + own

    # -------------------------------------------------------------- holes
    def holes(self, recs, axis, coord, depth=0.65):
        """Lining holes (local a, z) of the registered openings whose wall
        face lies within `depth` of the lining face (axis 'x': world x =
        coord, a = dY; axis 'y': world y = coord, a = E): what the joinery
        puts through the lining plane (_lining_rects)."""
        out = []
        for r in recs:
            if r['axis'] != axis:
                continue
            if not (-0.05 <= (r['coord'] - coord) * r['out'] <= depth):
                continue
            for u0, u1, z0, z1 in _lining_rects(r):
                if axis == 'x':
                    a0, a1 = sorted((self.d_of(u0), self.d_of(u1)))
                else:
                    a0, a1 = sorted((self.E_of(u0), self.E_of(u1)))
                out.append((a0, a1, z0, z1))
        return out

    # -------------------------------------------------------------- layers on faces
    def face_layers(self, prefix, layers, axis, c, sgn, a0, a1, z0, top, holes=()):
        """Layers on a masonry face: axis 'E' (face at E = c, layers toward
        sgn * E, extent dY a0 -> a1) or 'D' (face at dY = c, toward sgn * dY,
        extent E a0 -> a1), from z0 up to `top`: a level or a plane z(x, y)
        (sloping ceilings: each layer ends exactly on it). Holes (a0, a1, z0,
        z1) are left open: each layer is one solid with real holes per piece
        of wall (_faces, _layer_shell); under a sloping top the solid stops on
        a level just below it and one prism per layer carries the slope."""
        lo, hi = sorted((a0, a1))
        T = sum(t for _, _, t in layers)
        hs = [(max(h0, lo), min(h1, hi), h2, h3) for h0, h1, h2, h3 in holes
              if min(h1, hi) - max(h0, lo) > 1e-6 and h3 > z0 + 1e-6]
        if not callable(top):
            segs = [(lo, hi, top, None)]
        else:
            def zmin(ua, ub):
                return min(top(x, y) for x, y in self._layer_rect(axis, c, sgn, 0.0, T, ua, ub))
            zg = zmin(lo, hi) - 0.03
            cuts = sorted({lo, hi} | {v for h in hs if h[3] > zg - 1e-6 for v in h[:2]})
            segs = []
            for ua, ub in zip(cuts[:-1], cuts[1:]):
                if ub - ua < 1e-6:
                    continue
                zc = zmin(ua, ub)
                zb = zc - 0.03
                tall = [h[3] for h in hs if h[0] < ub - 1e-6 and h[1] > ua + 1e-6 and h[3] > zb]
                if tall:
                    zb = max(tall)
                segs.append((ua, ub, zb, top if zc - zb > 1e-3 else None))
        d = 0.0
        for elem, mat, t in layers:
            if mat is not None:
                bm = self.kit(prefix + elem, mat)
                n0 = len(bm.faces)
                for ua, ub, zb, ftop in segs:
                    for outer, inner in _faces(ua, ub, z0, zb, hs):
                        if not inner and len(outer) == 4:
                            (pa, za), (pb, zz) = min(outer), max(outer)
                            I.prism(bm, self._layer_rect(axis, c, sgn, d, d + t, pa, pb), za, zz)
                        else:
                            self._layer_shell(bm, axis, c, sgn, d, d + t, outer, inner)
                    if ftop is not None:
                        I.prism(bm, self._layer_rect(axis, c, sgn, d, d + t, ua, ub), zb, ftop)
                self._mark_edges(prefix + elem, mat, bm, n0, axis)
            d += t
        return d

    def _mark_edges(self, elem, mat, bm, n0, axis):
        """Side faces (hole reveals, ends, top, bottom) of the adhesive and
        insulation layers of a lining get material slot 1 = M_PlasterInt:
        the plaster / board return that wraps the lining's edges at the
        openings and wall ends (layers.md W1), drawn without thickness. Kit
        objects carry one material, so build() adds the slot after flush."""
        if mat == 'M_PlasterInt':
            return
        bm.faces.ensure_lookup_table()
        k = 0 if axis == 'E' else 1                  # wall normal: world x ('E' faces) or y ('D' faces)
        for i in range(n0, len(bm.faces)):
            f = bm.faces[i]
            f.normal_update()
            if abs(f.normal[k]) < 0.5:
                f.material_index = 1
        self.edged.add(self.kit.name(elem))

    def _layer_rect(self, axis, c, sgn, d0, d1, a0, a1):
        if axis == 'E':
            return I.rect(xE(c + sgn * e(d0)), xE(c + sgn * e(d1)), self.y(a0), self.y(a1))
        return I.rect(xE(a0), xE(a1), self.y(c + sgn * d0), self.y(c + sgn * d1))

    def _layer_shell(self, bm, axis, c, sgn, d0, d1, outer, inners):
        """One layer slab of an (a, z) outline with holes on a face: both caps
        triangulated (_fill), the outline and the holes walled."""
        loops = [outer] + list(inners)
        flat = [p for lp in loops for p in lp]
        tris = _fill(loops)

        def w(a, z, d):
            if axis == 'E':
                return (xE(c + sgn * e(d)), self.y(a), z)
            return (xE(a), self.y(c + sgn * d), z)
        vf = [bm.verts.new(w(a, z, d0)) for a, z in flat]
        vb = [bm.verts.new(w(a, z, d1)) for a, z in flat]
        for i, j, k in tris:
            bm.faces.new((vf[i], vf[j], vf[k]))
            bm.faces.new((vb[k], vb[j], vb[i]))
        o = 0
        for lp in loops:
            n = len(lp)
            for k in range(n):
                i, j = o + k, o + (k + 1) % n
                bm.faces.new((vf[j], vf[i], vb[i], vb[j]))
            o += n

    def _layer_poly(self, bm, axis, c, sgn, d0, d1, poly_az):
        """One layer slab of an (a, z) polygon on a face."""
        pts = []
        for a, z in poly_az:
            if not pts or abs(a - pts[-1][0]) > 1e-7 or abs(z - pts[-1][1]) > 1e-7:
                pts.append((a, z))
        if len(pts) > 2 and abs(pts[0][0] - pts[-1][0]) < 1e-7 and abs(pts[0][1] - pts[-1][1]) < 1e-7:
            pts.pop()
        if len(pts) < 3 or abs(I.area(pts)) < 1e-8:
            return
        if I.area(pts) < 0:
            pts = list(reversed(pts))
        if axis == 'E':
            x0, x1 = sorted((xE(c + sgn * e(d0)), xE(c + sgn * e(d1))))
            geo.add_prism_x(bm, [(self.y(a), z) for a, z in pts], x0, x1)
        else:
            y0, y1 = sorted((self.y(c + sgn * d0), self.y(c + sgn * d1)))
            geo.add_prism_y(bm, [(xE(a), z) for a, z in pts], y0, y1)

    def face_poly(self, prefix, layers, axis, c, sgn, poly_az):
        d = 0.0
        for elem, mat, t in layers:
            if mat is not None:
                bm = self.kit(prefix + elem, mat)
                n0 = len(bm.faces)
                self._layer_poly(bm, axis, c, sgn, d, d + t, poly_az)
                self._mark_edges(prefix + elem, mat, bm, n0, axis)
            d += t

    # -------------------------------------------------------------- floors
    def floor(self, E0, E1, d0, d1, z, layers, prefix='Floor'):
        I.floor_stack(self.kit, self.R(E0, E1, d0, d1), z, layers, prefix)

    def slab(self, E0, E1, d0, d1, z0, t=SLAB_T):
        I.prism(self.kit('FloorSlab', 'M_Structure'), self.R(E0, E1, d0, d1), z0, z0 + t)

    def ceiling(self, E0, E1, d0, d1, z):
        I.prism(self.kit('CeilingPlaster', 'M_PlasterInt'), self.R(E0, E1, d0, d1), z - CPL, z)

    # ================================================================ build
    def build(self):
        recs = self.records()
        self.recs = recs
        self.cutter(recs)
        _hollow(self.ctx, self.body, self.cut)
        self.paint()
        self.floors()
        self.walls()
        self.partitions()
        self.roofs()
        self.hall_stair()
        self.private_stairs()
        self.stairwell_finishes()
        self.entrance_sills()
        # the 60 x 60 stair windows have steel frames and sashes (n3): own objects, as a Kit
        # object keeps the material of the first opening that names it (cream M_Joinery)
        J.build_openings(self.kit, [r for r in recs if J.classify(r) == 'K'], prefix='StairWindow')
        J.build_openings(self.kit, recs)
        self.street_door_stops(recs)
        self.window_handles(recs)
        self.niche_finishes(recs)
        objs = self.kit.flush()
        plaster = self.ctx.mats['M_PlasterInt']
        # private flights: plastered RC (risers, stringers, ends) under the oak treads
        o = objs.get(self.kit.name('StairStructure'))
        if o is not None:
            for p in o.data.polygons:
                if abs(p.normal.z) < 0.5:
                    p.material_index = 1
            self.edged.add(o.name)
        for name in self.edged:
            o = objs.get(name)
            if o is not None and any(p.material_index == 1 for p in o.data.polygons):
                o.data.materials.append(plaster)
        return objs

    # -------------------------------------------------------------- paint
    def paint(self, tol=0.003, probe=0.01, share=0.5):
        """M_PlasterInt on the body faces of the dwellings: a polygon is
        painted when at least `share` of its area faces into a paint zone -
        each triangle's centroid moved `probe` along the face normal (into
        the room for a cavity face, into the open air for an exterior one)
        must lie in a zone. Testing the polygon centre alone painted the
        exterior face brick of towers E0 / W0: there the hollowing merged the
        interior stub under the lean-to (dY -2.105) with the face brick above
        the lean-to into one polygon whose centre lay in the bedroom zone."""
        mat = self.ctx.mats['M_PlasterInt']
        me = self.body.data
        if mat.name not in [m.name for m in me.materials if m]:
            me.materials.append(mat)
        idx = [m.name if m else None for m in me.materials].index(mat.name)

        def inside(p):
            for x0, x1, y0, y1, z0, top in self.zones:
                if x0 - tol <= p.x <= x1 + tol and y0 - tol <= p.y <= y1 + tol and p.z >= z0 - tol:
                    zt = top(p.x, p.y) if callable(top) else top
                    if p.z <= zt + tol:
                        return True
            return False
        me.calc_loop_triangles()
        area_in, area = [0.0] * len(me.polygons), [0.0] * len(me.polygons)
        vs = me.vertices
        for tri in me.loop_triangles:
            k = tri.polygon_index
            a, b, c = (vs[i].co for i in tri.vertices)
            area[k] += tri.area
            if inside((a + b + c) / 3 + me.polygons[k].normal * probe):
                area_in[k] += tri.area
        for poly in me.polygons:
            k = poly.index
            if area[k] > 0 and area_in[k] >= share * area[k]:
                poly.material_index = idx

    # -------------------------------------------------------------- floors
    def floors(self):
        t = self
        ec = (EF_BW + EF_HO) / 2
        d7 = (ec - e(0.40), ec + e(0.40))
        for k, zf in ((0, Z0), (1, Z1)):
            fin = FIN_GF if k == 0 else FIN_INT
            z_slab = GF_SOFFIT if k == 0 else RAW[1]
            for s in (-1, 1):
                def D(a, b):
                    return (s * a, s * b) if s > 0 else (s * b, s * a)
                t.slab(E_OW, E_IW, *D(D_PW, D_ENDI), z_slab)
                t.floor(EF_OW, E_P0[0], *D(DF_PW, DF_END), zf, fin)
                t.floor(E_P0[1], EF_IW, *D(DF_PW, DF_END), zf, fin)
                dd = (-4.115 if s < 0 else 3.04)
                t.floor(E_P0[0], E_P0[1], dd - 0.375, dd + 0.375, zf, fin)            # D8 / D9 doorway
            # corridor + passage, D7 doorway
            t.slab(E_BWI, E_HOI, -D_MID, D_MID, z_slab)
            t.slab(EF_BW, EF_HO, -D_PW, -D_MID, z_slab)
            t.floor(EF_BW, EF_HO, -DF_PW, D_MID - PL, zf, fin)
            t.floor(*d7, D_MID - PL, DF_PW, zf, fin)
            t.ceiling(EF_BW, EF_HO, -D_MID, D_MID - PL, RAW[k + 1])
            # porch / loggia (exterior paving on the slab)
            t.slab(E_PO, E_BW, -D_MID, D_MID, z_slab)
            t.floor(E_PO, E_BW, -D_MID, D_MID, zf, PORCH if k == 0 else LOGGIA, 'Terrace')
        # pavilion ceilings: L0 (under the L1 slab) and L1 (under L2)
        for k in (1, 2):
            for s in (-1, 1):
                def D(a, b):
                    return (s * a, s * b) if s > 0 else (s * b, s * a)
                t.ceiling(EF_OW, E_P0[0], *D(DF_PW, DF_END), RAW[k])
                t.ceiling(E_P0[1], EF_IW, *D(DF_PW, DF_END), RAW[k])
        # ---------------- common hall
        hall = [(E_HO, E_IW, -D_MID, D_LOBBY), (E_HO, E_SPU, D_LOBBY, D_MID), (E_SPL, E_IW, D_LOBBY, D_MID),
                (E_SPU, E_SPL, D_HL, D_MID)]
        for E0, E1, d0, d1 in hall:
            t.slab(E0, E1, d0, d1, GF_SOFFIT)
            t.floor(E0, E1, d0, d1, Z0, HALL_GF, 'Hall')
        t.slab(E_HO, E_SPU, -D_MID, D_L1L, RAW[1])                                     # L1 landing
        t.floor(E_HO, E_SPU, -D_MID, D_L1L, Z1, HALL_UP, 'Hall')
        t.ceiling(E_HO, E_SPU, -D_MID, D_L1L, RAW[1])
        t.ceiling(E_HO, E_SPU, -D_MID, D_MID, RAW[2])                                  # under the L2 slab
        # vestibule (F2 over the lobby); slab on under the private flight's foot
        t.slab(E_SPL, E_IW, -D_L2W, D_HIT1, RAW[1])
        I.prism(t.kit('FloorScreed', 'M_Screed'), t.R(EF_SPD, EF_IW, D_VF, D_HIT1), RAW[1] + SLAB_T, Z1 - FL_TREAD)
        t.floor(EF_SPD, EF_IW, -D_L2W + PL, D_VF, Z1, FIN_OPEN)
        t.ceiling(E_SPL, E_IW, -D_MID, D_HIT1, RAW[1])                                 # over the wall plaster too
        t.ceiling(EF_SPD, EF_IW, -D_L2W + PL, D_VF, RAW[2])                             # vestibule ceiling
        # ---------------- L2
        for s in (-1, 1):
            def D(a, b):
                return (s * a, s * b) if s > 0 else (s * b, s * a)
            t.slab(E_OW, E_IW, *D(D_PW, D_ENDI), RAW[2])
            t.floor(EF_OW, E_HW, *D(DF_PW2, DF_END), Z2, FIN_INT)                       # bedrooms N / S
            t.ceiling(EF_OW, E_HW, *D(DF_PW2, DF_END), RAW[3])
        t.slab(E_SBI, E_IW, -D_L2W, D_VF, RAW[2])
        t.slab(E_SBI, EF_SPW, D_VF, D_L2W, RAW[2])                                    # well: spine side plastered
        t.slab(E_HW, E_IW, -D_PW, -D_L2W, RAW[2])
        t.slab(E_HW, EF_SPW, D_L2W, D_VT, RAW[2])
        t.slab(E_HW, EF_SPD, D_VT, D_PW, RAW[2])
        t.slab(EF_SPD, E_IW, D_VT, D_PW, RAW[2])
        t.floor(EF_SB, E_HW, -D_L2W + PL, D_L2W - PL, Z2, FIN_OPEN)                    # middle bedroom
        # bathroom N, hall (pavilion parts F1, middle F2), stairwell open
        t.floor(E_P2, EF_IW, -DF_END, D_BATH2[0], Z2, FIN_INT)
        t.ceiling(E_P2, EF_IW, -DF_END, D_BATH2[0], RAW[3])
        t.floor(E_P2 + e(SJ), E_P2 + e(SJ + 0.75), D_BATH2[0], D_BATH2[1], Z2, FIN_INT)        # D13 doorway
        t.floor(E_P2, EF_IW, D_BATH2[1], -D_L2W, Z2, FIN_INT)
        t.floor(E_P2, EF_IW, -D_L2W, D_VF, Z2, FIN_OPEN)
        t.floor(E_P2, EF_SPW, D_VF, D_L2W, Z2, FIN_OPEN)
        t.floor(E_P2, EF_SPW, D_L2W, D_VT, Z2, FIN_INT)
        t.floor(E_P2, EF_IW, D_VT, DF_END, Z2, FIN_INT)
        # L2 hall ceilings (under the L3 slab; the N downstand is the painted body)
        t.ceiling(E_P2, EF_IW, D_BATH2[1], -D_PW, RAW[3])
        t.ceiling(E_P2, EF_IW, -D_MID, D_VF, RAW[3])
        t.ceiling(E_P2, EF_SPW, D_VF, D_VT, RAW[3])
        t.ceiling(E_P2, EF_IW, D_VT, DF_END, RAW[3])
        # ---------------- L3
        for s in (-1, 1):
            def D(a, b):
                return (s * a, s * b) if s > 0 else (s * b, s * a)
            t.slab(E_SBI, E_IW, *D(D_PW, D_ENDI), RAW[3])
            # terrace R3: slab over the L2 room, layers between the parapets
            t.slab(E_OW, E_SB, *D(D_PW, D_ENDI), RAW[3])
            pt = TOWER['terrace_parapet_t']
            t.floor(E_OUT + e(pt), E_SB, *D(D_MID + pt, D_END - pt), Z3, TERRACE, 'Terrace')
        t.floor(EF_SB, EF_IW, -DF_END, -DF_PW, Z3, FIN_INT)                            # living
        t.floor(EF_SB, E_HW, DF_PW, DF_END, Z3, FIN_INT)                               # kitchen
        t.floor(E_P2, EF_IW, D_SHOW3[1], DF_END, Z3, FIN_INT)                          # shower room
        t.floor(E_P2 + e(SJ), E_P2 + e(SJ + 0.75), D_SHOW3[0], D_SHOW3[1], Z3, FIN_INT)        # D16 doorway
        t.floor(E_HW, E_P2, 3.055 - 0.375, 3.055 + 0.375, Z3, FIN_INT)                 # D15 doorway
        t.slab(E_HWI, E_IW, -D_MID, D_VF, RAW[3])
        t.slab(E_HWI, EF_SPW, D_VF, D_MID, RAW[3])
        t.slab(E_P2, E_IW, -D_PW, -D_MID, RAW[3])
        t.slab(E_P2, EF_SPW, D_MID, D_VT, RAW[3])
        t.slab(E_P2, EF_SPD, D_VT, D_PW, RAW[3])
        t.slab(EF_SPD, E_IW, D_VT, D_PW, RAW[3])
        t.floor(E_P2, EF_IW, -DF_PW, D_VF, Z3, FIN_INT)                                # hall
        t.floor(E_P2, EF_SPW, D_VF, D_VT, Z3, FIN_INT)
        t.floor(E_P2, EF_IW, D_VT, D_SHOW3[0], Z3, FIN_INT)

    # -------------------------------------------------------------- walls
    def walls(self):
        t, recs = self, self.recs
        xo, xi = xE(E_OW), xE(E_IW)
        for k, zf in ((0, Z0), (1, Z1)):
            st = zf - (0.12 if k == 0 else 0.10)
            top = RAW[k + 1]
            for s in (-1, 1):
                def D(a, b):
                    return (s * a, s * b) if s > 0 else (s * b, s * a)
                ha = [h for h in t.holes(recs, 'x', xo) if D(D_PW, D_ENDI)[0] - 0.01 <= h[0] <= D(D_PW, D_ENDI)[1]]
                hi = [h for h in t.holes(recs, 'x', xi) if D(D_PW, D_ENDI)[0] - 0.01 <= h[0] <= D(D_PW, D_ENDI)[1]]
                # outer and inner walls full length, end and middle-side walls between them
                t.face_layers('Wall', B.LINING, 'E', E_OW, 1, *D(D_PW, D_ENDI), st, top, ha)
                t.face_layers('Wall', B.LINING, 'E', E_IW, -1, *D(D_PW, D_ENDI), st, top, hi)
                t.face_layers('Wall', B.LINING, 'D', s * D_ENDI, -s, EF_OW, EF_IW, st, top)
                hm = t.holes(recs, 'y', t.y(s * D_MID))
                ec = (EF_BW + EF_HO) / 2
                hm.append((EF_BW, EF_HO, st, zf + DOOR_H) if s < 0 else (ec - e(0.40), ec + e(0.40), st, zf + DOOR_H))
                t.face_layers('Wall', B.LINING, 'D', s * D_PW, s, EF_OW, EF_IW, st, top, hm)
            # corridor: back wall and stair-hall wall lined, plaster at the S end
            hb = t.holes(recs, 'x', xE(E_BW))
            t.face_layers('Wall', B.LINING, 'E', E_BWI, 1, -D_MID, D_MID, st, top, hb)
            h1 = [(D_D1[0], D_D1[1], zf - SILL_T, zf + 2.07)]
            t.face_layers('Wall', B.LINING, 'E', E_HOI, -1, -D_MID, D_MID, st, top, h1)
            ec = (EF_BW + EF_HO) / 2
            t.face_layers('Wall', PLASTER, 'D', D_MID, -1, EF_BW, EF_HO, st, top,
                          [(ec - e(0.40), ec + e(0.40), st, zf + DOOR_H)])
        # ---------------- common hall (L0 / L1): plaster on the spine and the inner wall
        hp = t.holes(recs, 'x', xE(X.E_IN_MID))
        t.face_layers('Wall', PLASTER, 'E', E_SPU, -1, D_LOBBY, D_L1L, Z0, RAW[1] - CPL)
        t.face_layers('Wall', PLASTER, 'E', E_SPU, -1, D_L1L, D_HL, Z0, RAW[2] - CPL)
        t.face_layers('Wall', PLASTER, 'E', E_SPU, -1, D_HL, D_MID, Z_HLAND, RAW[2] - CPL)
        t.face_layers('Wall', PLASTER, 'E', E_SPU, -1, -D_MID, D_L1L, Z1, RAW[2] - CPL,
                      [(D_D1[0], D_D1[1], Z1, Z1 + 2.07)])
        # lower zone, under the vestibule slab and the private flight's soffit
        soff = [(d, SOFF1(d)) for d in (D_HIT1, D_HL, D_MID)]
        t.face_layers('Wall', PLASTER, 'E', E_IW, -1, -D_MID, D_HIT1, Z0, RAW[1] - CPL,
                      [h for h in hp if h[1] < D_HIT1 + 0.01])
        t.face_poly('Wall', PLASTER, 'E', E_IW, -1, [(D_HIT1, Z0), (D_MID, Z0)] + list(reversed(soff)))
        t.face_layers('Wall', PLASTER, 'E', E_SPL, 1, D_LOBBY, D_HIT1, Z0, RAW[1] - CPL)
        t.face_poly('Wall', PLASTER, 'E', E_SPL, 1, [(D_HIT1, Z0), (D_HL, Z0), (D_HL, SOFF1(D_HL)), (D_HIT1, SOFF1(D_HIT1))])
        t.face_poly('Wall', PLASTER, 'E', E_SPL, 1, [(D_HL, Z_HLAND), (D_MID, Z_HLAND), (D_MID, SOFF1(D_MID)),
                                                      (D_HL, SOFF1(D_HL))])
        # ---------------- duplex: vestibule and the L1 -> L2 flight (above its soffit)
        hk = t.holes(recs, 'x', xE(X.E_IN_MID))
        st1 = RAW[1] + SLAB_T
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, -D_L2W, D_VF, st1, RAW[2],
                      [h for h in hk if h[2] > Z1 and h[3] < Z2])
        t.face_layers('Wall', SPINE_DUP, 'E', E_SPL, 1, -D_L2W, D_VF, st1, RAW[2],
                      [(D_D1[0], D_D1[1], Z1 - SILL_T, Z1 + 2.07)])
        t.face_layers('Wall', PLASTER, 'D', -D_L2W, 1, EF_SPD, EF_IW, st1, RAW[2])
        up = [(D_VF, st1), (D_HIT1, st1)] + [(d, SOFF1(d)) for d in (D_HIT1, D_VT)] + [(D_VT, RAW[2]), (D_VF, RAW[2])]
        t.face_poly('Wall', B.LINING, 'E', E_IW, -1, up)
        t.face_poly('Wall', SPINE_DUP, 'E', E_SPL, 1, up)
        # ---------------- L2 / L3 inner wall (pavilion inner walls + middle inner wall)
        hk = t.holes(recs, 'x', xE(X.E_IN_MID)) + t.holes(recs, 'x', xi)
        st2, st3 = RAW[2] + SLAB_T, RAW[3] + SLAB_T
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, -D_ENDI, -D_PW, st2, RAW[3], hk)
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, -D_PW, -D_MID, st2, Z_BEAM2)
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, -D_MID, D_VF, st2, RAW[3], hk)
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, D_VT, D_ENDI, st2, RAW[3], hk)
        # stairwell column, from the L2 slab soffit up to the L3 ceilings
        zv = lambda x, y: t.vault_ceil(x)                                                  # noqa: E731
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, D_VF, D_MID, RAW[2], zv, hk)
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, D_MID, D_VT, RAW[2], Z_BEAM3, hk)
        # L3: pavilion parts under the sloping ceilings, middle under the vault and the beams
        for s in (-1, 1):
            def D(a, b):
                return (s * a, s * b) if s > 0 else (s * b, s * a)
            f = t.roof_ceil(s)
            a0, a1 = D(D_PW, D_ENDI)
            t.face_layers('Wall', B.LINING, 'E', E_IW, -1, a0, a1, st3, f, hk)
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, -D_PW, -D_MID, st3, Z_BEAM3)
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, -D_MID, D_VF, st3, zv, hk)
        t.face_layers('Wall', B.LINING, 'E', E_IW, -1, D_VT, D_PW, st3, Z_BEAM3)
        # ---------------- L2 rooms
        for s in (-1, 1):
            def D(a, b):
                return (s * a, s * b) if s > 0 else (s * b, s * a)
            ha = [h for h in t.holes(recs, 'x', xo) if D(D_PW, D_ENDI)[0] - 0.01 <= h[0] <= D(D_PW, D_ENDI)[1]]
            t.face_layers('Wall', B.LINING, 'E', E_OW, 1, *D(D_PW, D_ENDI), st2, RAW[3], ha)
            t.face_layers('Wall', B.LINING, 'D', s * D_ENDI, -s, EF_OW, EF_IW, st2, RAW[3])
            t.face_layers('Wall', PLASTER, 'D', s * D_PW, s, EF_OW, E_HW, st2, RAW[3])    # 25 + plaster (n28)
            # middle bedroom: plaster on the 25 walls, under the lean-to ceiling
            I.prism(t.kit('WallPlaster', 'M_PlasterInt'), t.R(EF_SB, E_HW, s * D_L2W, s * (D_L2W - PL)), st2,
                    lambda x, y: t.lean_ceil(x))
        hm = t.holes(recs, 'x', xE(E_SB))
        t.face_layers('Wall', B.LINING, 'E', E_SBI, 1, -D_L2W, D_L2W, st2, lambda x, y: t.lean_ceil(x),
                      [h for h in hm if Z2 < h[2] < Z3])
        # ---------------- L3 rooms
        hs = t.holes(recs, 'x', xE(E_SB))
        for s in (-1, 1):
            def D(a, b):
                return (s * a, s * b) if s > 0 else (s * b, s * a)
            f = t.roof_ceil(s)
            a0, a1 = D(D_PW, D_ENDI)
            t.face_layers('Wall', B.LINING, 'E', E_SBI, 1, a0, a1, st3, f, [h for h in hs if h[2] > Z3 - 0.1])
            t.face_layers('Wall', B.LINING, 'D', s * D_ENDI, -s, EF_SB, EF_IW, st3, f)
            t.face_layers('Wall', B.LINING, 'D', s * D_PW, s, EF_SB, E_P2 if s < 0 else E_HW, st3, f)
        # hall wall (0.12 + 0.03), up to the vault ceiling
        hh = t.holes(recs, 'x', xE(E_HW))
        t.face_layers('Wall', HALLWALL, 'E', E_HWI, 1, -D_MID, D_MID, st3, lambda x, y: t.vault_ceil(x), hh)

    # -------------------------------------------------------------- partitions
    def partitions(self):
        t, kit = self, self.kit
        dt_std = B.total(PART_STD) - 0.002
        dt_wet = B.total(PART_WET) - 0.002
        for k, zf in ((0, Z0), (1, Z1)):
            st = zf - (0.12 if k == 0 else 0.10)
            top = RAW[k + 1]
            ep = (E_P0[0] + E_P0[1]) / 2
            for s in (-1, 1):
                d_a, d_b = (-DF_END, -DF_PW) if s < 0 else (DF_PW, DF_END)
                a, b = t.p(ep, d_a), t.p(ep, d_b)
                L = d_b - d_a
                dc = (-4.115 if s < 0 else 3.04) - d_a
                _wall(kit, a, b, _notched(L, st, [(0, top), (L, top)], [(dc - 0.375, dc + 0.375, zf + DOOR_H)]),
                      PART_STD, 'Partition')
                # D8: hinge on the north jamb into the kitchen; D9: hinge north, into the bathroom
                room = t.p(3.4, (d_a + d_b) / 2)
                hinge, swing = _door_cfg(a, b, dc - 0.375, dc, room)
                I.door(kit, a, b, dc, 0.75, zf + DOOR_H, zf, dt_std, hinge, swing, 90.0)
            # D7: corridor -> bedroom, hinge on the inner jamb, into the bedroom
            dw = (D_MID - PL + DF_PW) / 2
            a, b = t.p(EF_BW, dw), t.p(EF_HO, dw)
            L = (EF_HO - EF_BW) * M
            hinge, swing = _door_cfg(a, b, L / 2 + 0.40, L / 2, t.p(2.3, 3.5))
            I.door(kit, a, b, L / 2, 0.80, zf + DOOR_H, zf, DF_PW - (D_MID - PL) - 0.002, hinge, swing, 90.0)
        # ---------------- L2: long partition E 2.86 -> 2.951 (bedrooms | hall), bathroom partition
        ep = (E_HW + E_P2) / 2
        st, top = RAW[2] + SLAB_T, RAW[3]
        a, b = t.p(ep, -DF_END), t.p(ep, DF_END)
        L = 2 * DF_END

        def sL(d):
            return d + DF_END
        tops = [(0, top), (sL(-D_PW), top), (sL(-D_PW), Z_BEAM2), (sL(-D_MID), Z_BEAM2), (sL(-D_MID), top), (L, top)]
        doors = [(-3.015, 'b', -4.0, 0.75), (1.26, 'b', 0.0, 0.80), (3.61, 'a', 4.5, 0.80)]   # D10-D12: centre, hinge jamb, room dY, width
        notch = [(sL(c) - w / 2, sL(c) + w / 2, Z2 + DOOR_H) for c, _, _, w in doors]
        _wall(kit, a, b, _notched(L, st, tops, notch), PART_WET, 'Partition')
        for c, jamb, droom, w in doors:
            sh = sL(c) + (w / 2 if jamb == 'b' else -w / 2)
            hinge, swing = _door_cfg(a, b, sh, sL(c), t.p(1.5, droom))
            I.door(kit, a, b, sL(c), w, Z2 + DOOR_H, Z2, dt_wet, hinge, swing, 90.0)
            t.floor(E_HW, E_P2, c - w / 2, c + w / 2, Z2, FIN_INT if abs(c) > D_L2W else FIN_OPEN)
        db = (D_BATH2[0] + D_BATH2[1]) / 2
        a, b = t.p(E_P2, db), t.p(EF_IW, db)
        L = (EF_IW - E_P2) * M
        _wall(kit, a, b, _notched(L, st, [(0, top), (L, top)], [(SJ, SJ + 0.75, Z2 + DOOR_H)]), PART_STD, 'Partition')
        hinge, swing = _door_cfg(a, b, SJ, SJ + 0.375, t.p(3.4, -4.5))
        I.door(kit, a, b, SJ + 0.375, 0.75, Z2 + DOOR_H, Z2, dt_std, hinge, swing, 90.0)
        # ---------------- L3: kitchen partition (under the sloping ceiling), shower-room partition
        f = t.roof_ceil(1)
        st = RAW[3] + SLAB_T
        a, b = t.p(ep, D_PW), t.p(ep, DF_END)
        L = DF_END - D_PW
        xm = xE(ep)
        tops = [(0, f(xm, t.y(D_PW))), (L, f(xm, t.y(DF_END)))]
        dc = 3.055 - D_PW
        _wall(kit, a, b, _notched(L, st, tops, [(dc - 0.375, dc + 0.375, Z3 + DOOR_H)]), PART_WET, 'Partition')
        hinge, swing = _door_cfg(a, b, dc - 0.375, dc, t.p(2.0, 4.0))
        I.door(kit, a, b, dc, 0.75, Z3 + DOOR_H, Z3, dt_wet, hinge, swing, 90.0)
        ds = (D_SHOW3[0] + D_SHOW3[1]) / 2
        a, b = t.p(E_P2, ds), t.p(EF_IW, ds)
        L = (EF_IW - E_P2) * M
        zt = f(xE(EF_IW), t.y(ds))
        _wall(kit, a, b, _notched(L, st, [(0, zt), (L, zt)], [(SJ, SJ + 0.75, Z3 + DOOR_H)]), PART_STD, 'Partition')
        hinge, swing = _door_cfg(a, b, SJ, SJ + 0.375, t.p(3.4, 4.5))
        I.door(kit, a, b, SJ + 0.375, 0.75, Z3 + DOOR_H, Z3, dt_std, hinge, swing, 90.0)

    # -------------------------------------------------------------- roofs
    def roofs(self):
        t, kit = self, self.kit
        for s in (-1, 1):
            d0, d1 = (-D_ENDI, -D_PW) if s < 0 else (D_PW, D_ENDI)
            poly = t.R(E_SBI, E_IW, d0, d1)
            f, m = t.tile[s]
            raw = I.sloped_stack(kit, poly, f, ROOF_STRUCT, 'Roof', m)
            I.sloped_stack(kit, poly, raw, B.LINING, 'Ceiling', m)
        # lean-to over the middle bedroom: structure between the pavilion walls, lining over the room
        I.sloped_stack(kit, t.R(E_SBI, E_HW, -D_MID, D_MID), lambda x, y: t.lean_under(x), ROOF_STRUCT, 'Roof',
                       t.lean_slope)
        I.sloped_stack(kit, t.R(E_SBI, E_HW, -D_L2W, D_L2W), lambda x, y: t.lean_raw(x), B.LINING, 'Ceiling',
                       t.lean_slope)
        # stair-hall vault R2 under the copper: structure, then the lining
        xs = t.hall_stations(E_HWI, E_IW)
        y0, y1 = t.y(D_MID), t.y(-D_MID)
        dz = 0.0
        for elem, mat, th in VAULT_STRUCT + B.LINING:
            prefix = 'Vault' if not elem.startswith('Lining') else 'Ceiling'
            top = [(v, t.copper_under(v) - dz) for v in xs]
            bot = [(v, t.copper_under(v) - dz - th) for v in reversed(xs)]
            geo.add_prism_y(kit(prefix + elem, mat), top + bot, y0, y1)
            dz += th
        # both ends of the vault lining stop on the L3 strip openings (E_P2 -> E_IW, head
        # Z_BEAM3): where the vault ceiling runs below that head (the low side of the arc)
        # the insulation / adhesive / slab ends would show from the opening - a plaster board
        # return closes them, from the lining's underside up to the head
        bd = kit('CeilingLiningBoard', 'M_PlasterInt')
        lo, hi = sorted((xE(E_IW), xE(E_P2)))
        pts = [(v, t.vault_ceil(v)) for v in [lo] + [v for v in xs if lo + 1e-6 < v < hi - 1e-6] + [hi]]
        runs, run = [], []
        for (xa, za), (xb, zb) in zip(pts, pts[1:]):
            ina, inb = za < Z_BEAM3 - 1e-4, zb < Z_BEAM3 - 1e-4
            if ina and not run:
                run = [(xa, za)]
            if ina != inb:
                xc = xa + (Z_BEAM3 - za) / (zb - za) * (xb - xa)
                run.append((xc, Z_BEAM3))
                if ina:
                    runs.append(run)
                    run = []
            elif inb:
                run.append((xb, zb))
        if run:
            runs.append(run)
        for run in runs:
            # top edge at the head, then the lining underside back (crossing points sit on the head)
            poly = [(run[0][0], Z_BEAM3), (run[-1][0], Z_BEAM3)] + \
                   [p for p in reversed(run) if p[1] < Z_BEAM3 - 1e-6]
            for s in (-1, 1):
                ya, yb = sorted((t.y(s * D_MID), t.y(s * (D_MID + 0.012))))
                geo.add_prism_y(bd, poly, ya, yb)

    # -------------------------------------------------------------- common stair
    def hall_stair(self):
        t, kit = self, self.kit
        r, g = HALL_RISER, HALL_GOING
        steps = kit('HallSteps', 'M_Concrete')
        bed = kit('HallStepBeds', 'M_Screed')

        def step(E0, E1, d_front, d_back, z_top, z_below):
            """Precast step 13/35: lap 5 cm over the step below, on a mortar bed."""
            sg = 1 if d_back > d_front else -1
            df = d_front - sg * STEP_LAP
            I.prism(steps, t.R(E0, E1, df, d_back), z_top - STEP_T, z_top)
            if z_top - STEP_T > z_below + 1e-4:
                I.prism(bed, t.R(E0, E1, df, d_front), z_below, z_top - STEP_T)
        # flight 1: lower zone, risers 1-8 rising south from the lobby
        for i in range(7):
            d0 = D_LOBBY + i * g
            step(EF_SPL, EF_IWH, d0, d0 + g, (i + 1) * r, i * r)
        # half-landing in three strips (risers 9 and 10 on the spine's faces)
        lands = [(EF_SPL, EF_IWH, 8 * r), (EF_SPU, EF_SPL, 9 * r), (E_HO, EF_SPU, 10 * r)]
        for E0, E1, z in lands:
            I.landing(kit, t.R(E0, E1, D_HL, D_MID), z, thickness=0.15, finish_t=0.03, finish_mat='M_Screed',
                      prefix='HallLanding')
        # flight 2: upper zone, risers 11-17 rising north to the L1 landing
        for j in range(6):
            d0 = D_HL - j * g
            step(E_HO, EF_SPU, d0, d0 - g, (11 + j) * r, (10 + j) * r)
        # wall handrails on the spine side, 0.92 above the nosings (SE 58 "92")
        xr1 = xE(EF_SPL + e(0.06))
        I.handrail(kit, [(xr1, t.y(D_LOBBY - STEP_LAP), r), (xr1, t.y(D_HL - g), 7 * r)], height=0.92,
                   rail_d=0.04, posts=False, prefix='HallStair')
        xr2 = xE(EF_SPU - e(0.06))
        I.handrail(kit, [(xr2, t.y(D_HL + STEP_LAP), 11 * r), (xr2, t.y(D_L1L + g), 16 * r)], height=0.92,
                   rail_d=0.04, posts=False, prefix='HallStair')

    # -------------------------------------------------------------- stairwell
    def stairwell_finishes(self):
        """Plaster on the edges of the L2 and L3 floor openings over the
        private flights (E 3.462 -> 3.957 x dY -0.905 -> +2.385) and under
        the L2 -> L3 flight, which is seen from the duplex (the L1 -> L2
        flight over the common hall has UNDER_FLIGHT): spine side flush with
        the spine plaster (the slabs stop EF_SPW), north edges in front of
        the slab, the top risers (slab edge over the last tread) and the
        flight's top end hanging under the L3 slab."""
        t = self
        bm = t.kit('StairwellPlaster', 'M_PlasterInt')
        r1, r2 = (Z2 - Z1) / FL_N, (Z3 - Z2) / FL_N
        zt2 = Z2 - FL_TREAD                                  # underside of the L2 -> L3 flight's foot
        I.prism(bm, t.R(EF_SPW, EF_SPD, D_VF, D_VT), RAW[2], Z2)
        I.prism(bm, t.R(EF_SPW, EF_SPD, D_VF, D_VT), RAW[3] - CPL, Z3)
        I.prism(bm, t.R(EF_SPD, EF_IW, D_VF, D_VF + PL), RAW[2] - CPL, zt2 - FPL)
        I.prism(bm, t.R(EF_SPD, EF_IW, D_VF, D_VF + PL), RAW[3] - CPL, Z3)
        I.prism(bm, t.R(EF_SPD, EF_IW, D_VT - PL, D_VT), Z2 - r1, Z2)
        I.prism(bm, t.R(EF_SPD, EF_IW, D_VT - PL, D_VT), Z3 - r2, Z3)
        pts = [(D_VF, zt2), (D_HIT2, zt2), (D_VT, Z_SOFTOP2)]
        prof = [(t.y(d), z) for d, z in pts] + [(t.y(d), z - FPL) for d, z in reversed(pts)]
        geo.add_prism_x(bm, prof, xE(EF_IW), xE(EF_SPD))
        I.prism(bm, t.R(EF_SPD, EF_IW, D_VT, D_VT + PL), Z_SOFTOP2 - FPL, RAW[3] - CPL)

    # -------------------------------------------------------------- window handles
    def window_handles(self, recs):
        """Handles of the casement windows 'FT', 'ET', 'E1T' (_register_types):
        the joinery's handle (SE 51 lever on a rose) at the sash's mid-height,
        on the meeting stiles of a pair of casements or on the opening stile
        of a single sash. Sash outline as joinery.opening builds it: behind a
        stop jamb the frame laps the brick, so the sashes fill the opening
        above the frame's bottom member; a plain jamb frames inside it."""
        bm = self.kit('WindowHandles', 'M_Steel')
        for r in recs:
            kind = J.classify(r)
            if kind not in ('FT', 'ET', 'E1T') or r['kind'] != 'rect':
                continue
            sp = J.spec_for(kind)
            fw, fd = sp['frame']
            sw, sd = sp['sash']
            u0, u1, z0, z1 = J.dims(r)
            if sp['jamb'] == 'stop':
                d0, iu0, iu1, iz0, iz1 = J.STOP, u0, u1, z0 + fw, z1
            else:
                d0, iu0, iu1, iz0, iz1 = J.WALL, u0 + fw, u1 - fw, z0 + fw, z1 - fw
            if sp.get('frame_at') is not None:
                d0 = sp['frame_at']
            ds = d0 + (fd - sd) / 2
            uh = (iu0 + iu1) / 2 if sp['leaves'] == 2 else iu1 - sw / 2
            zh = (iz0 + iz1) / 2
            I.face_box(bm, r, uh - 0.012, uh + 0.012, zh - 0.07, zh + 0.07, ds + sd, ds + sd + 0.012)
            I.face_box(bm, r, uh - 0.012, uh + 0.012, zh - 0.10, zh + 0.012, ds + sd + 0.012, ds + sd + 0.06)

    # -------------------------------------------------------------- street door stops
    def street_door_stops(self, recs):
        """Stops of the street door D3 ('PTE', joinery._street_door): the
        leaf closes 3 mm clear of the posts and the transom and 8 mm over the
        frame's bottom member, at their own depth with nothing behind, so a
        2-3 mm through slit ran round the closed leaf (light leak into the
        lobby). 12 x 12 stop beads on the inside of the posts and the transom
        and a threshold bar, lapping the leaf's edges by 12 mm."""
        for r in recs:
            if J.classify(r) != 'PTE' or r['kind'] != 'rect':
                continue
            sp = J.spec_for('PTE')
            fw, fd = sp['frame']
            sw, sd = sp['sash']
            u0, u1, z0, z1 = J.dims(r)
            zf = J.floor_of(z0)
            ds = sp['frame_at'] + (fd - sd) / 2
            um = (u0 + u1) / 2
            a, b = um - 0.46, um + 0.46                         # leaf 0.92 between the posts
            iz0, zt = z0 + fw, zf + 2.04
            bm = self.kit('WindowFrames', sp['frame_mat'])
            d0, d1 = ds + 0.056, ds + 0.068
            I.face_box(bm, r, a - 0.05, a + 0.012, iz0, zt + 0.05, d0, d1)
            I.face_box(bm, r, b - 0.012, b + 0.05, iz0, zt + 0.05, d0, d1)
            I.face_box(bm, r, a + 0.012, b - 0.012, zt - 0.012, zt + 0.05, d0, d1)
            I.face_box(bm, r, a + 0.012, b - 0.012, iz0, iz0 + 0.015, d0, d1)

    # -------------------------------------------------------------- radiator niches
    def niche_finishes(self, recs):
        """Radiator niches under the type E windows (SE 53 E): the joinery
        lines the back (NicheLining, standing on zf); here the parquet runs
        into the niche, under that lining (the pocket is sunk by the parquet,
        _pockets), and a plaster soffit covers the RC sill block and the
        lining's cut edge. The jambs are the painted brick (paint zones) and
        the lining's plastered edges."""
        for r in recs:
            kind = J.classify(r)
            if kind is None or r['kind'] != 'rect' or not J.spec_for(kind)['niche']:
                continue
            u0, u1, z0, z1 = J.dims(r)
            zf = J.floor_of(z0)
            a0, a1 = u0 - J.MAZ, u1 + J.MAZ
            I.face_box(self.kit('FloorParquet', 'M_Parquet'), r, a0, a1, zf - PARQ_T, zf, J.STOP, J.FINISH)
            I.face_box(self.kit('NicheLining', 'M_PlasterInt'), r, a0, a1, z0 - 0.13 - PL, z0 - 0.13,
                       J.STOP + J.LIN, J.FINISH)

    # -------------------------------------------------------------- entrance sills
    def entrance_sills(self):
        """Stone sills (soglie) under the dwelling entrance doors D1 (type A,
        L0 and L1, stair-hall outer wall) and D2 (duplex, L1, spine): from the
        hall face to the dwelling's finished face, flush with both floors."""
        bm = self.kit('EntranceSills', 'M_Stone')
        for zf in (Z0, Z1):
            I.prism(bm, self.R(E_HO, EF_HO, *D_D1), zf - SILL_T, zf)
        I.prism(bm, self.R(E_SPU, EF_SPD, *D_D1), Z1 - SILL_T, Z1)

    # -------------------------------------------------------------- private stairs
    def private_stairs(self):
        t, kit = self, self.kit
        width = (EF_IW - EF_SPD) * M
        for zf, riser in ((Z1, (Z2 - Z1) / FL_N), (Z2, (Z3 - Z2) / FL_N)):
            # 14 risers and a top tread (the 15th riser is the upper floor's edge): interior.flight's
            # profile with the last riser at its top end would fold back on itself
            I.flight(kit, t.p(EF_SPD, D_VF), (0.0, -1.0), width, FL_N - 1, riser, FL_GOING, zf, waist=FL_WAIST,
                     tread_t=FL_TREAD, nosing=FL_NOSE, side=-1, tread_top_last=True, tread_mat=TREAD_MAT)
        # under the L1 -> L2 flight (common hall below): insulation and plaster (SE 58 "ISOLAZIONE")
        pts = [D_HIT1, D_MID]
        dz = 0.0
        for elem, mat, th in UNDER_FLIGHT:
            prof = [(t.y(d), SOFF1(d) - dz) for d in pts] + [(t.y(d), SOFF1(d) - dz - th) for d in reversed(pts)]
            geo.add_prism_x(kit(elem, mat), prof, xE(EF_IWH), xE(EF_SPL))
            dz += th
        # L1 -> L2: wall rail on the spine; L2 -> L3: balustrade on the open side; level guards
        r1, r2 = (Z2 - Z1) / FL_N, (Z3 - Z2) / FL_N
        xr = xE(EF_SPD + e(0.06))
        I.handrail(kit, [(xr, t.y(D_VF), Z1 + r1), (xr, t.y(D_VT - FL_GOING), Z2 - r1)], height=0.92,
                   rail_d=0.04, posts=False)
        xb = xE(EF_SPD + e(0.03))
        p0 = (xb, t.y(D_VF + 0.02), Z2 + r2 - 0.20)
        p1 = (xb, t.y(D_VT - FL_GOING - 0.02), Z3 - r2 - 0.20)
        I.handrail(kit, [p0, p1], height=1.12, post_every=0.11, rail_d=0.04, post_d=0.014)
        xg = xE(EF_SPD - e(0.03))
        I.handrail(kit, [(xg, t.y(D_VF), Z2), (xg, t.y(D_VT), Z2)], height=1.00, post_every=0.11,
                   rail_d=0.04, post_d=0.014)
        I.handrail(kit, [(xg, t.y(D_VF - 0.03), Z3), (xg, t.y(D_VT), Z3)], height=1.00, post_every=0.11,
                   rail_d=0.04, post_d=0.014)
        yg = t.y(D_VF - 0.03)
        I.handrail(kit, [(xE(EF_SPD + e(0.02)), yg, Z3), (xE(EF_IW - e(0.02)), yg, Z3)], height=1.00,
                   post_every=0.11, rail_d=0.04, post_d=0.014)


# ------------------------------------------------------------------ build
def _mirror(objs: dict, k: int) -> None:
    """West tower k: a mirrored copy of every interior object of the east one."""
    col_w = bpy.data.collections[f'COL_{COL_W}']
    for name, o in objs.items():
        wname = name.replace(f'_E{k}', f'_W{k}')
        w = bpy.data.objects.new(wname, _mirror_mesh(o, wname))
        for key in o.keys():
            w[key] = o[key]
        col_w.objects.link(w)


def build(ctx) -> None:
    if geo.THROUGH is None:
        return
    _register_types()
    for k in range(TOWER['count']):
        t = _Tower(ctx, k)
        objs = t.build()
        # west tower: body and interior objects mirrored
        bw = bpy.data.objects[f'SM_Tower_Body_W{k}']
        old = bw.data
        bw.data = _mirror_mesh(t.body, bw.name)
        bpy.data.meshes.remove(old)
        _mirror(objs, k)
