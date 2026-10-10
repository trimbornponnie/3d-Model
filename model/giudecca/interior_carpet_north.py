"""Carpet north row interiors: the ordinary H-houses (Tipo C) and the two
campo houses (Tipo B2, house axes E 38.5 / 45.5), L0-L3 (research report
carpet_north.md, build-ups layers.md, joinery windows.md; docs/INTERIORS.md).

Each H-house holds two mirror-image triplex maisonettes (dE > 0 west, the
east one mirrored by code). Per dwelling:
  L0  cellars in the cantine band (cells 1.3-2.9 x 3.16, 120 brick partitions,
      F4 floor at -0.32, cellar doors onto the joint corridor);
  L1  entrance from the gallery through the 0.34 core wall (portoncino 0.91 x
      2.07), landing, corridor, the L1 -> L2 flight; in the south pavilion the
      hall, bagno 2 and camera 1 (none in the campo houses: there the core is
      closed by a wall at Y 4.776 -> 4.99);
  L2  camera 2 in the north pavilion, landing, corridor, hall, bagno 1 and
      camera 3, which runs on across the joint;
  L3  soggiorno in the north pavilion, open to the core strip, the notch
      landing under the copper vault, cucina, the notch terrace and the joint
      terrace at 9.15.
One straight flight per storey (15 risers, 14 treads 0.235), L1 -> L2 and
L2 -> L3 superimposed against the axis wall (dE 0.105 -> 0.88), rising south.

Walls: the exterior masonry stays in the bodies (W1 0.395, core W2 0.28,
end walls 0.37 as the exterior's hollows, joint leaves 0.185) and gets the
insulated lining (55) on its warm faces; the axis and party walls (W5 0.21),
the core spine (0.21, RC) and the partitions (W7 0.11 / 0.15; the camera |
hall + bath wall 0.16, dE 1.77 -> 1.93, so that the cameras are the written
2.92 and the baths the verified 1.66 wide) are separate layered objects;
floors F1 / F2 per room on one structural slab per storey; roofs R1 under
the exterior's tile plane, the core vault R2 under its copper skin, terraces
R3 (9.15), the gallery deck R4 (2.99).

L3 sloped ceilings (deviation): the R1 stack (350 perpendicular, layers.md)
hangs under the exterior's tile plane, which is 0.153 lower at the low wall
(tile top 11.709 vs T + 2.842 = 11.862) and steeper (0.364 vs 0.34) than
layers.md's R1 geometry. The exterior must not move, so the finished ceilings
are 11.34 at the low-wall lining -> 12.52 at the high one, 0.15 - 0.08 under
the drawn T + 2.472 + 0.34 s (11.49 -> 12.60; report: 11.54 -> 12.64).

Joinery: joinery.build_openings, except the trifore, the two-light pairs and
the finestre tipo, whose local builders (trifora_joinery, two_light_joinery,
window_e) avoid the engine's coplanar / overlapping parts there; the plain
reveals of the core windows and terrace doors and the radiator-niche jambs
get plaster returns (reveal_finishes).

Boundary with interior_carpet_ms (the middle row) - read before changing:
* L1 (z 2.71 -> 5.72): this module hollows SouthPavN right to its south face
  (Y 7.224) and builds the structural slab 2.71 -> 2.91 under all of it. Its
  rooms end at Y 6.906 (L1_SOUTH), the north face of the L1 dividing wall.
  The dividing wall (Y 6.906 -> 7.027, W5) and everything of the middle-row
  rooms above that slab south of Y 6.906 (floor layers, walls, ceiling
  plaster) are interior_carpet_ms's.
* L2 (z 5.72 -> 8.72): this module hollows JointNM above z 5.72 and builds
  the north dwellings' camera 3 / bagno 1 across the joint, the slab
  5.72 -> 5.92 and the deck above; the rooms end at NorthPavM's north face
  (Y 7.776, L2_SOUTH; bagno 1 at 7.72 with a chase), whose masonry is the L2
  dividing wall (plastered here on the north side): interior_carpet_ms keeps
  NorthPavM's north wall (Y 7.776 -> 8.015) solid at L2 behind them. The
  drawn wall is 0.20 at Y 7.906 -> 8.027 (n78), i.e. the rooms are 0.13
  module shorter here (reported deviation).
* JointNM below z 5.72 is interior_carpet_ms's.

Everything here runs only with geo.THROUGH set (build.py --interiors).
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

from . import buildups as BU
from . import carpet as C
from . import geo
from . import interior as I
from . import joinery as J
from .common import xE, yY
from .params import (BLOCKS, CAMPO, CAMPO_HOUSES, COPING_H, CORE_CROWN, CORE_EAVE, CORE_VAULT_R, CORE_W, EXT_STAIRS,
                     FLOORS, GALLERY, JOINTS, MODULE, NOTCH_HALF, ROOF_HIGH, ROOF_LOW, ROWS, SLAB, WALL)

M = MODULE
WM = WALL / M                       # W1 masonry 0.395 in modules
LIN = BU.LINING_T                   # 0.055 insulated lining
PL = 0.015                          # plaster on interior masonry faces
EW = C.END_WALL                     # 0.37: block-end, slot and campo end walls (as the exterior's hollows)
LEAF = C.GAP / 2 + 0.185            # 0.23: joint line -> masonry face of the joint leaf (W6)
T = ROWS['N']['T']                  # 9.02
Z1, Z2, Z3 = FLOORS[1], FLOORS[2], FLOORS[3]
EPS = 0.02                          # cutter overshoot (modules or metres, as used)

# ----------------------------------------------------------- plan positions
YN0, YN1 = ROWS['N']['npav']        # -0.224, 2.224 (outer faces)
YS0, YS1 = ROWS['N']['spav']        # 4.776, 7.224
YNI0, YNI1 = YN0 + WM, YN1 - WM     # masonry faces 0.015, 1.985
YSI0, YSI1 = YS0 + WM, YS1 - WM     # 5.015, 6.985
YJ1 = JOINTS['NM'][1]               # 7.776, NorthPavM north face
Y_ENT = YN1 - 0.34 / M              # 2.018: gallery face of the L1 entrance wall ("34 | 91,5", n31)
Y_FOOT = 2.779                      # foot of the flights
YX0, YX1 = C.LANDING_N              # L3 cross wall 5.868 -> 6.05 (core body)
L1_SOUTH = 6.906                    # L1 rooms end (dividing wall, interior_carpet_ms)
L2_SOUTH = YJ1                      # L2 rooms end (NorthPavM masonry)
Y_BATH2 = 7.72                      # L2 bagno 1 south face; chase to the dividing wall (n78, n10)
Y_BATH2_CAMPO = 7.79                # the same in the campo houses (n78)
Y_CAMPO_IN = CAMPO['l2_south'] - WM                      # 8.0006, campo L2 wall masonry face
Y_CAMPO_PAR = CAMPO['l2_south'] - C.CAMPO_PARAPET_T / M  # 8.088, L3 terrace parapet inner face
Y_C2 = YNI1 + 0.055 / M             # camera-2 partition centre: north face on the pavilion wall face (n78)
Y_C2S = YNI1 + 0.11 / M             # its south face
Y_HB = {1: 5.89, 2: 5.975}          # hall | bath partitions (n67 5.86/5.92; n78, n10 5.94-6.01, verified)
T_HB = {1: 0.11, 2: 0.15}           # their thickness (W7; the L2 one carries the bath plumbing)
Y_CLOSE = YS0 + 0.353 / M           # campo houses: L1 core closing wall to Y 4.99 (n31)
Y_C0 = ROWS['N']['core'][1] - 0.05 - 0.002 / M   # its inner face: 2 mm before the exterior's corner
                                    # piers (Y 4.726 -> 5.07, dE 1.70 -> 2.10, the '2' piers of n31)

D_AX = 0.105                        # axis wall half thickness (W5 0.21, spine 0.21)
D_CORE = CORE_W / 2 - 0.28          # 1.77: core wall masonry face (0.02 render + 0.26 brick)
D_CORE_T = CORE_W / 2 - D_CORE      # 0.28 core wall masonry
D_P0, D_P1 = D_CORE, 1.93          # camera | hall + bath wall: hall / bath face on the core wall's masonry
                                    # line (bath 1.66 wide, verified 1.75-1.79 on four sheets), camera face
                                    # 1.93 (camera '2,92' from the party wall face, n31, n67, n78)
D_KIT = NOTCH_HALF + WALL           # 1.88: kitchen side, masonry face of the notch side wall
D_BAND = 0.88                       # flight band | corridor (n31: flight 0.78 against the spine)
D_ENT = C.UNDER_CORE                # 1.6975: the N-pav south wall opening under the core
D_PARTY = 3 * M                     # 4.95
D_FACE = 3.22 * M                   # 5.313: block end / slot face
Z_BEAM3 = T + 2.14                  # L3 beam between the soggiorno and the core strip (n65, vault springing)

# doors: (centre, opening width) - opening = leaf + 2 x 0.023 casing (windows.md 7: leaves 0.80 / bath 0.70)
DOOR_ROOM, DOOR_BATH, DOOR_HEAD = 0.85, 0.75, 2.10
D_C2DOOR = 1.65 - DOOR_ROOM / 2          # camera-2 door, jamb at dE 1.65 (n78)
ENT = dict(d=(0.28, 1.19), h=2.07, lintel=(0.16, 1.31, 0.41), sill=0.03)  # portoncino (SE 65, n31)
TER = dict(d=(0.51, 1.285), h=2.05)                                        # L3 terrace doors (n65 "77,5")
CELLAR = dict(w=0.775, z0=-0.32, z1=1.73, sill=0.11)                      # porte cantine (SE 65)

# flights (n31 "14 x 23,5 = 3,29", n18 15 risers per storey)
N_RISERS = 15
FL_WAIST, FL_TREAD, FL_NOSE, FL_RISER = 0.16, 0.03, 0.02, 0.015   # waist, oak tread / nosing / riser (S1)
TREAD_MAT = 'M_DoorLeaf'             # oak treads and risers, matching the parquet (layers.md S1; as towers / schiera)
GOING = (YS0 - Y_FOOT) * M / (N_RISERS - 1)

# stacks
SPINE = [('Plaster', 'M_PlasterInt', 0.015), ('RC', 'M_Structure', 0.18), ('Plaster', 'M_PlasterInt', 0.015)]
FL_INT = BU.FLOOR_INT[:-1]          # parquet / screed / fill on the slab
FL_OPEN = BU.FLOOR_OPEN[:-1]        # parquet / screed / insulation (over open air, cellars)
PLASTER = [('Plaster', 'M_PlasterInt', PL)]
PARQ = BU.FLOOR_INT[0][2]           # 0.015 parquet
ENT_WALL = [('EntranceBrick', 'M_Brick', 0.34 - LIN)] + BU.LINING   # outside -> in (SE 65: 26 + 5 + lining)
PART_CAM = [('Plaster', 'M_PlasterInt', 0.015), ('Core', 'M_HollowBrick', D_P1 - D_P0 - 0.030),
            ('Plaster', 'M_PlasterInt', 0.015)]    # W7 with a 130 core: carries the bath plumbing and vent
T_CAM = D_P1 - D_P0                 # 0.16


# ------------------------------------------------------------ joinery types
def _register_types() -> None:
    """Local opening types (added to joinery.TYPES, the engine file is not
    edited): the portoncino in the 0.34 core wall with its own lintel (PN),
    the terrace door in the 0.30 L3 cross wall (DN)."""
    # PN: frame inner face on the lining board's back (0.34 - 0.010 - frame depth) so the
    # lining's insulation / adhesive ends at the jambs and head sit behind the frame and only
    # the 10 mm board shows as the reveal (frame_at STOP left 5 mm of insulation bare)
    J.TYPES.setdefault('PN', dict(J.TYPES['P'], lintel=False,
                                  frame_at=0.34 - BU.LINING[-1][2] - J.TYPES['P'].get('frame', J.BASE['frame'])[1]))
    J.TYPES.setdefault('N_E1P', dict(J.TYPES['E1'], lintel=False, board=False))   # a light of a two-light pair
    J.TYPES.setdefault('N_E', dict(J.TYPES['E'], board=False))                   # finestra tipo, own sill / board
    J.TYPES.setdefault('DN', dict(jamb='plain', door=True, leaves=1, bottom_rail=0.150, board=False,
                                  lintel=False, niche=False, frame_at=0.115))


# ------------------------------------------------------------ small helpers
def ER(E0, E1, Y0, Y1):
    return I.rect(xE(E0), xE(E1), yY(Y0), yY(Y1))


def roof_plane(Y_low, Y_high):
    """Tile top plane z(y) of a pavilion of the north row as the exterior
    builds it (common.pavilion_section, wall 0.37, 0.10 under the copings)
    and its slope."""
    yl, yh = yY(Y_low), yY(Y_high)
    s = 1.0 if yh > yl else -1.0
    H, L = T + ROOF_HIGH - COPING_H - 0.10, T + ROOF_LOW - COPING_H - 0.10
    y1, y2 = yl + s * C.PW, yh - s * C.PW
    k = (H - L) / (y2 - y1)
    return (lambda y: L + (y - y1) * k), abs(k)


ROOF_N, SLOPE_N = roof_plane(YN1, YN0)
ROOF_S, SLOPE_S = roof_plane(YS0, YS1)
KN, KS = math.sqrt(1 + SLOPE_N ** 2), math.sqrt(1 + SLOPE_S ** 2)
TILE = 0.090
UNDER = BU.total(BU.ROOF_TILE_UNDER)        # 0.260


def roof_under(pav):
    """Underside of the tiles (top of the R1 layers) z(x, y)."""
    f, k = (ROOF_N, KN) if pav == 'N' else (ROOF_S, KS)
    return lambda x, y: f(y) - TILE * k


def roof_ceiling(pav):
    """Finished sloped ceiling (bottom of the R1 lining) z(x, y)."""
    f, k = (ROOF_N, KN) if pav == 'N' else (ROOF_S, KS)
    return lambda x, y: f(y) - (TILE + UNDER) * k


VAULT_ZC = T + CORE_CROWN - CORE_VAULT_R                   # 5.72, centre of the R 6.00 arc
VAULT_R0 = CORE_VAULT_R - 0.002                           # copper skin 2 mm
VAULT_RIN = VAULT_R0 - BU.total(BU.ROOF_VAULT_UNDER)      # finished soffit radius


class _Vault:
    """Finished vault soffit z(x, y) (curved across x: strips along x are cut
    into short pieces under it)."""
    curved = True

    def __init__(self, xc):
        self.xc = xc

    def __call__(self, x, y):
        return VAULT_ZC + math.sqrt(max(VAULT_RIN ** 2 - (x - self.xc) ** 2, 0.0))


def vault_soffit(xc):
    return _Vault(xc)


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


def outer(kind, l1_spav=False):
    """(dE of the outer room boundary, side type) of a dwelling: the face of
    the party wall object (W), the plastered joint leaf (P) or the lined end
    wall (L); the campo party wall is an exterior end wall at L1 (S-pav)."""
    if kind == 'end':
        return D_FACE - EW, 'L'
    if kind == 'joint':
        return D_PARTY - LEAF, 'P'
    if kind == 'campo' and l1_spav:
        return D_PARTY - EW, 'L'
    return D_PARTY - D_AX, 'W'


def end_E(k, E, inward, mode='room'):
    """E of a part end. k: 'face' (block end / slot), 'campo_wall' (the
    normal S-pav's exterior end on the campo line at L1), 'joint', 'abut'
    (continuous into the neighbouring part). Modes: 'room' cutter of the
    rooms (masonry face; beyond the end at abutments), 'poly' room-zone
    objects (masonry face; the end exactly at abutments), 'slab' slab objects
    (the end-wall face, the body's end under a joint leaf or at an
    abutment), 'cut' cutter of the slab zones (beyond the body's end at
    joints and abutments)."""
    if k in ('face', 'campo_wall'):
        return E + inward * EW / M
    if k == 'joint':
        if mode in ('room', 'poly'):
            return E + inward * LEAF / M
        b = E + inward * C.GAP / 2 / M
        return b if mode == 'slab' else b - inward * EPS
    if mode in ('poly', 'slab'):
        return E
    return E - inward * EPS


SOFF = {Z1: Z2 - SLAB, Z2: Z3 - SLAB}       # raw soffits over L1 / L2 (5.72, 8.72)


# ======================================================================= run
class Run:
    def __init__(self, ctx):
        self.ctx = ctx
        self.cut: dict[str, bmesh.types.BMesh] = {}
        self.body_recs: dict[str, list] = {}
        self.kits: list = []

    def obj(self, name):
        o = bpy.data.objects.get(name)
        return o if o is not None and o.type == 'MESH' else None

    def cutter(self, name):
        if name not in self.cut:
            self.cut[name] = bmesh.new()
        return self.cut[name]

    def cbox(self, name, x0, x1, y0, y1, z0, z1):
        if self.obj(name) is not None:
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
        """Exterior stand-ins the interiors replace (under geo.THROUGH only):
        the trifora mullions (the joinery builds the trifore), the floating
        cores' slab edges (rebuilt as the L1 core slab), the gallery deck box
        (rebuilt as R4); the gallery parapet and the external stairs' top
        tread meet the 2.99 deck."""
        for o in list(bpy.data.objects):
            if o.type != 'MESH':
                continue
            n = o.name
            if n.startswith(('SM_Carpet_Frames_', 'SM_Carpet_CoreSlabs_')) or \
                    (n.startswith('SM_Carpet_Gallery_') and not n.startswith('SM_Carpet_GalleryParapet')):
                bpy.data.objects.remove(o, do_unlink=True)
            elif n.startswith('SM_Carpet_GalleryParapet_'):
                _move_z(o, Z1, Z1 - 0.10)
            elif n.startswith('SM_Carpet_ExtStairSteps_'):
                _move_z(o, Z1, Z1 - 0.02)
        # opening types the classifier cannot know
        for r in geo.OPENINGS:
            t = r.get('target') or ''
            if t.startswith('SM_Carpet_CantineN_') and r['kind'] == 'rect' and r.get('through') is None:
                r['type'] = 'CD'                         # cellar door under the core (SE 65)

    # ------------------------------------------------------------ segments
    def segment(self, seg):
        ctx = self.ctx
        kit = I.Kit(ctx, 'Carpet', f'N{seg.tag}', seg.col)
        part = seg.part()
        normal, campo = seg.split_campo()
        S = Seg(self, kit, seg, part, normal, campo)
        S.build()
        self.kits.append(S)

    # --------------------------------------------------------------- vaults
    def vault_skin(self, block):
        """Cut the copper lens of the core vaults down to a 2 mm skin; the
        R2 layers are built under it per house."""
        name = f'SM_Carpet_VaultsN_{block.capitalize()}'
        if self.obj(name) is None:
            return
        bm = self.cutter(name)
        z_lo = T + CORE_EAVE - 0.15
        for a in C.block_axes(block, 'N'):
            xc = xE(a)
            arc = I._arc_band(xc, VAULT_ZC, VAULT_R0, VAULT_R0 - 0.1, D_CORE, 24)[:25]   # the R2 stack's outer arc
            w = D_CORE + 0.005                        # 5 mm past the bodies' faces (no coplanar end faces)
            ze = VAULT_ZC + math.sqrt(VAULT_R0 ** 2 - w * w)
            prof = [(xc - w, z_lo), (xc + w, z_lo), (xc + w, ze)] + list(reversed(arc)) + [(xc - w, ze)]
            geo.add_prism_y(bm, prof, yY(YX0 + 0.06), yY(YN1 - 0.05))

    # -------------------------------------------------------------- finish
    def hollow_all(self):
        for name, bm in self.cut.items():
            o = self.obj(name)
            if o is None:
                bm.free()
                continue
            J.add_pockets(bm, self.recs(name))
            for r in self.recs(name):                  # radiator niches sunk for the parquet run into them
                if _has_niche(r):
                    u0, u1, z0, z1 = J.dims(r)
                    zf = J.floor_of(z0)
                    I.face_box(bm, r, u0 - J.MAZ, u1 + J.MAZ, zf - PARQ, zf + 0.01, J.STOP, J.FINISH + 0.05)
            _hollow(self.ctx, o, bm)
        self.cut = {}

    def finish(self):
        for S in self.kits:
            S.finish()


def _hollow(ctx, body, volumes):
    """interior.hollow with the cutter's shells kept apart: hollow() welds
    coincident vertices of touching boxes (object_from_bmesh merge=True),
    which makes the cutter non-manifold and the exact difference fail."""
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


def _lining_cutter(recs, depth=0.60):
    """joinery.lining_cutter, 0.60 deep instead of 1.2 (the linings lie at
    d 0.28 - 0.45 behind the outer faces): the openings and what the joinery
    passes through the lining (joinery.lining_boxes; the boards of the
    finestre tipo and two-light pairs, built here by sill_and_board, too)."""
    bm = bmesh.new()
    for r in recs:
        kind = J.classify(r)
        geo.Face(r['axis'], r['coord'], r['out']).solid(bm, r['outline'], depth, outside=0.3)
        for u0, u1, z0, z1 in J.lining_boxes(r, kind, board=True if kind in ('N_E', 'N_E1P') else None):
            I.face_box(bm, r, u0, u1, z0, z1, J.WALL - 0.02, depth)
        if _has_niche(r):                       # the parquet runs into the radiator niche
            u0, u1, z0, z1 = J.dims(r)
            zf = J.floor_of(z0)
            I.face_box(bm, r, u0 - J.MAZ, u1 + J.MAZ, zf - PARQ, zf + 0.01, J.WALL - 0.02, depth)
    return bm


def _has_niche(r):
    k = J.classify(r)
    return k is not None and r['kind'] == 'rect' and J.spec_for(k)['niche']


LAYER_DZ = 16.0       # z shift between the lining layers while they are cut together


def _cut_linings(ctx, objs, recs):
    """Cut the openings out of the wall-lining layer objects in one exact
    difference. The layers touch face to face, and the self-intersecting
    difference fuses touching shells, so they are cut apart: layer i is
    shifted up by i * LAYER_DZ (the linings lie at z 2.9 - 13), with its own
    copy of the cutter, joined into one temporary mesh, cut, split back by
    height and shifted down again (float error ~2e-6 m)."""
    objs = [o for o in objs if o is not None]
    if not objs or not recs:
        return
    bm = bmesh.new()
    for i, o in enumerate(objs):
        n0 = len(bm.verts)
        bm.from_mesh(o.data)
        bm.verts.ensure_lookup_table()
        bmesh.ops.translate(bm, vec=(0.0, 0.0, LAYER_DZ * i), verts=bm.verts[n0:])
    me = bpy.data.meshes.new('CUT_LiningJoin')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(objs[0].data.materials[0])
    tmp = bpy.data.objects.new('CUT_LiningJoin', me)
    ctx.root.objects.link(tmp)                 # evaluated only in a visible collection
    cut = bmesh.new()
    for i in range(len(objs)):
        c = _lining_cutter(recs)
        bmesh.ops.translate(c, vec=(0.0, 0.0, LAYER_DZ * i), verts=c.verts)
        mc = bpy.data.meshes.new('CUT_LiningCutterPart')
        c.to_mesh(mc)
        c.free()
        cut.from_mesh(mc)
        bpy.data.meshes.remove(mc)
    _cut_openings(ctx, tmp, recs, cut)
    bm = bmesh.new()
    bm.from_mesh(tmp.data)
    for i, o in enumerate(objs):
        b = bm.copy()
        bad = [f for f in b.faces if round((f.calc_center_median().z - 8.0) / LAYER_DZ) != i]
        bmesh.ops.delete(b, geom=bad, context='FACES')
        loose = [v for v in b.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(b, geom=loose, context='VERTS')
        bmesh.ops.translate(b, vec=(0.0, 0.0, -LAYER_DZ * i), verts=b.verts)
        for f in b.faces:
            f.material_index = 0
        b.to_mesh(o.data)
        b.free()
        o.data.update()
    bm.free()
    bpy.data.objects.remove(tmp, do_unlink=True)


def _cut_openings(ctx, obj, recs, bm):
    """interior.cut_openings for a layer object made of separate touching
    shells (the wall linings): the cutter's shells and the object's shells
    are not welded (no merge by distance)."""
    if not len(bm.faces):
        bm.free()
        return
    cutter = geo.object_from_bmesh(bm, f'{obj.name}_CutOpenings', ctx.cutters, merge=False)
    mod = obj.modifiers.new('Bool_Openings', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.use_self = True
    mod.object = cutter
    geo.apply_modifiers(obj)
    bm2 = bmesh.new()
    bm2.from_mesh(obj.data)
    bmesh.ops.dissolve_degenerate(bm2, dist=1e-6, edges=bm2.edges)
    loose = [v for v in bm2.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm2, geom=loose, context='VERTS')
    bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
    bm2.to_mesh(obj.data)
    bm2.free()
    obj.data.update()


def trifora_joinery(kit, rec, prefix='Window'):
    """joinery._trifora with the two posts on the light boundaries: there the
    frame ring steps down from the side sills to the centre sill (its inner
    face at +-0.46 from the centre below the side sills), and the engine's
    casements, from +-0.52, ran into that step (coplanar faces, overlapping
    solids). Here each post spans +-0.462 -> +-0.58 (0.118, centred on the
    0.52 boundary, 2 mm off the step's inner face) and the two casements fill
    +-0.458 (SE 51: fixed side lights, two casements in the centre)."""
    s = J.spec_for('T')
    fr = J.Frame3(rec)
    d0 = J._frame_depth(rec, s)
    fw, fd = s['frame']
    sw, sd = s['sash']
    fbm = kit(f'{prefix}Frames', s['frame_mat'])
    lbm = kit(f'{prefix}Leaves', s['leaf_mat'])
    gbm = kit(f'{prefix}Glass', s['glass_mat'])
    inner = J._ring(fbm, fr, rec['outline'], fw, d0, d0 + fd)
    u0, u1, z0, z1 = J.dims(rec)
    uc = (u0 + u1) / 2
    zs_side = min(z for u, z in rec['outline'] if abs(u - u0) < 1e-6)
    pa, pb = 0.462, 0.58                       # post faces from the centre
    for sg in (-1, 1):
        ua, ub = sorted((uc + sg * pa, uc + sg * pb))
        ztop = min(J._z_on(inner, ua), J._z_on(inner, ub)) + 0.02
        J._box(fbm, fr, ua, ub, zs_side + fw - 0.02, ztop, d0 + 0.002, d0 + fd - 0.002)
    for sg in (-1, 1):
        lo = [(u, z) for u, z in inner if sg * (u - uc) >= pb - 1e-6]
        cut = uc + sg * pb
        if len(lo) >= 2:
            poly = J._side_light(inner, uc, sg, cut, zs_side + fw)
            if poly:
                J._glass(gbm, fr, poly, d0 + fd / 2, s['glass'])
    a, b = uc - 0.458, uc + 0.458
    zc0 = min(p[1] for p in inner if abs(p[0] - uc) < 0.47)
    ds = d0 + (fd - sd) / 2
    for la, lb_ in ((a, uc), (uc, b)):
        top = [(u, z) for u, z in inner if la - 1e-6 <= u <= lb_ + 1e-6 and z > zc0 + 0.5]
        za, zb = J._z_on(inner, la), J._z_on(inner, lb_)
        out = [(la, zc0), (lb_, zc0), (lb_, zb)] + sorted([q for q in top if la < q[0] < lb_],
                                                          key=lambda q: -q[0]) + [(la, za)]
        gl = I.offset(out, sw)
        J._ring(lbm, fr, out, sw, ds, ds + sd)
        J._glass(gbm, fr, gl, ds + sd / 2, s['glass'])
    hb = kit(f'{prefix}Handles', 'M_Steel')
    zh = J.floor_of(z0) + 1.05
    J._box(hb, fr, uc - 0.012, uc + 0.012, zh - 0.07, zh + 0.07, ds + sd, ds + sd + 0.012)


def two_light_pairs(recs):
    """The two lights of each two-light window (carpet.two_light: two E1
    records on one face, 0.14 brick mullion between them)."""
    groups = {}
    for r in recs:
        if r.get('done') or J.classify(r) != 'E1':
            continue
        u0, u1, z0, z1 = J.dims(r)
        groups.setdefault((r['axis'], round(r['coord'], 4), r['out'], round(z0, 3), round(z1, 3)), []).append(r)
    pairs = []
    for g in groups.values():
        g.sort(key=lambda r: J.dims(r)[0])
        i = 0
        while i + 1 < len(g):
            if abs(J.dims(g[i + 1])[0] - J.dims(g[i])[1] - C.MULLION) < 0.01:
                pairs.append((g[i], g[i + 1]))
                i += 2
            else:
                i += 1
    return pairs


def two_light_joinery(kit, ra, rb, prefix='Window'):
    """Joinery of a two-light window: frames, casements and reveals per light
    (engine), but one RC lintel, one inner sill block and one window board
    over the pair. The engine builds them per light, and over the 0.14
    mullion the lintel / sill ends of one light ran into the other light's
    pocket (coplanar faces with its frame, reveal head and board)."""
    for r in (ra, rb):
        r['done'] = True
        J.opening(kit, r, 'N_E1P', prefix)
    s = J.spec_for('E1')
    fr = J.Frame3(ra)
    U0, z0, z1 = J.dims(ra)[0], J.dims(ra)[2], J.dims(ra)[3]
    U1 = J.dims(rb)[1]
    d0 = J._frame_depth(ra, s)
    fd = s['frame'][1]
    ST, MZ, W = J.STOP, J.MAZ, J.WALL
    lb = kit('Lintels', 'M_Structure')
    J._box(lb, fr, U0 - 0.12, U1 + 0.12, z1, z1 + 0.13, 0.05, ST)
    J._box(lb, fr, U0 - 0.12, U1 + 0.12, z1 + MZ, z1 + 0.13, ST, W)
    J._box(lb, fr, U0 - 0.12, U0 - MZ, z1, z1 + MZ, ST, W)
    J._box(lb, fr, U1 + MZ, U1 + 0.12, z1, z1 + MZ, ST, W)
    sill_and_board(kit, fr, U0, U1, z0, d0, fd, prefix)


def sill_and_board(kit, fr, U0, U1, z0, d0, fd, prefix='Window'):
    """Inner part of the RC sill and the timber window board over U0 -> U1
    (stop-jamb windows, as joinery.opening), the sill block under the board
    stopping at its underside: no coplanar tops."""
    MZ, W = J.MAZ, J.WALL
    sb = kit('SillBlocks', 'M_Concrete')
    J._box(sb, fr, U0 - 0.12, U1 + 0.12, z0 - 0.13, z0, 0.115, d0)
    J._box(sb, fr, U0 - 0.12, U0 - MZ - 0.02, z0 - 0.13, z0, d0, W)
    J._box(sb, fr, U1 + MZ + 0.02, U1 + 0.12, z0 - 0.13, z0, d0, W)
    J._box(sb, fr, U0 - MZ - 0.02, U1 + MZ + 0.02, z0 - 0.13, z0 - 0.025, d0, W)
    wb = kit(f'{prefix}Boards', 'M_Joinery')
    J._box(wb, fr, U0 - MZ - 0.02, U1 + MZ + 0.02, z0 - 0.025, z0, d0 + fd, J.FINISH + 0.02)


def window_e(kit, r, prefix='Window'):
    """A finestra tipo (E): engine joinery without its sill / board, then
    sill_and_board."""
    r['done'] = True
    J.opening(kit, r, 'N_E', prefix)
    s = J.spec_for('E')
    u0, u1, z0, z1 = J.dims(r)
    sill_and_board(kit, J.Frame3(r), u0, u1, z0, J._frame_depth(r, s), s['frame'][1], prefix)


def reveal_finishes(kit, recs):
    """Finishes the joinery engine leaves raw on this row's openings:
    * plaster returns (15) on the inner reveals of the plain-jamb openings
      whose frame sits forward in the wall - the core windows K (steel frame
      at the outer face, layers.md W2: reveals lined, the 45 deg splay is not
      modelled) and the L3 terrace doors DN - from the back of the frame to
      the finished wall face (core wall 0.28 + lining, cross wall 0.30 +
      lining);
    * the radiator niches under the finestre tipo (E): the parquet runs into
      the niche (under the joinery's back lining; the pocket is sunk by it,
      Run.hollow_all, _lining_cutter), plaster on the side jambs and on the
      niche top (the RC sill block's underside and the lining's cut edge),
      from the back lining to the finished face (as interior_towers)."""
    bm = kit('WindowReveals', 'M_PlasterInt')
    t = 0.015
    for r in recs:
        k = J.classify(r)
        if k not in ('K', 'DN', 'E'):
            continue
        sp = J.spec_for(k)
        u0, u1, z0, z1 = J.dims(r)
        if k == 'E':
            if not _has_niche(r):
                continue
            zf = J.floor_of(z0)
            da, db = J.STOP + LIN, J.FINISH
            a0, a1 = u0 - J.MAZ, u1 + J.MAZ
            for ua, ub in ((a0, a0 + t), (a1 - t, a1)):
                I.face_box(bm, r, ua, ub, zf, z0 - 0.13, da, db)
            I.face_box(bm, r, a0 + t, a1 - t, z0 - 0.13 - t, z0 - 0.13, da, db)          # niche top
            I.face_box(kit('FloorParquet', 'M_Parquet', uv_rotate=45.0), r, a0, a1, zf - PARQ, zf, J.STOP, J.FINISH)
            continue
        da = J._frame_depth(r, sp) + sp['frame'][1] + 0.002
        db = (D_CORE_T if k == 'K' else (YX1 - YX0) * M) + LIN
        I.face_box(bm, r, u0, u0 + t, z0, z1, da, db)                 # jambs
        I.face_box(bm, r, u1 - t, u1, z0, z1, da, db)
        I.face_box(bm, r, u0 + t, u1 - t, z1 - t, z1, da, db)         # head
        if k == 'K':
            I.face_box(bm, r, u0 + t, u1 - t, z0, z0 + t, da, db)     # sill


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
    for p in out:
        if not clean or abs(p[0] - clean[-1][0]) > 1e-7 or abs(p[1] - clean[-1][1]) > 1e-7:
            clean.append(p)
    if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 1e-7 and abs(clean[0][1] - clean[-1][1]) < 1e-7:
        clean.pop()
    return clean


def _move_z(o, z_from, z_to):
    """Move the vertices of an object lying at z_from to z_to."""
    for v in o.data.vertices:
        if abs(v.co.z - z_from) < 1e-4:
            v.co.z = z_to
    o.data.update()


# =================================================================== segment
class Seg:
    """The interiors of one carpet segment of the north row (bodies NorthPavN,
    SouthPavN (+ campo part), CantineN, JointNM above 5.72, the houses' cores)."""

    def __init__(self, R, kit, seg, part, normal, campo):
        self.R, self.kit, self.seg, self.part, self.normal, self.campo = R, kit, seg, part, normal, campo
        t = seg.tag
        self.np = f'SM_Carpet_NorthPavN_{t}'
        self.sp = f'SM_Carpet_SouthPavN_{t}'
        self.spc = f'SM_Carpet_SouthPavN_Campo{t}'
        self.cant = f'SM_Carpet_CantineN_{t}'
        self.jnm = f'SM_Carpet_JointNM_{t}'
        self.core = f'SM_Carpet_CoresN_{seg.block.capitalize()}'
        self.new_recs: list = []
        self.houses = [House(self, a) for a in seg.axes]

    # E ranges of the parts ---------------------------------------------
    def rng(self, p, mode='room', campo_wall=False):
        """Interior E range of a part: k 'campo' is an exterior end wall
        (campo_wall=True, the normal S-pav at L1) or continuous."""
        def k(v):
            if v == 'campo':
                return 'campo_wall' if campo_wall else 'abut'
            return v
        return end_E(k(p.k0), p.E0, 1, mode), end_E(k(p.k1), p.E1, -1, mode)

    def build(self):
        kit, R = self.kit, self.R
        self.gallery()
        self.npav()
        if self.normal is not None:
            self.spav_normal()
            self.joint()
            self.cantine()
        if self.campo is not None:
            self.spav_campo()
        self.spav_roof()
        for h in self.houses:
            h.build()

    # ------------------------------------------------------------ gallery
    def gallery(self):
        """R4 deck of the gallery, finish 2.99 (SE 64): tiles / bed / membrane
        / falls on the fair-faced RC slab 2.71 -> 2.91, between the parapet and
        the pavilion's south wall, and into each entrance recess."""
        kit, seg, part = self.kit, self.seg, self.part
        ga = seg.E0 + C.END_BAY / M if part.k0 == 'face' else part.e0
        gb = seg.E1 - C.END_BAY / M if part.k1 == 'face' else part.e1
        y0, y1 = GALLERY['deck_y'][0], YN1 - WM + 0.003
        yp = y0 + GALLERY['parapet_t'] / M
        top = Z1 - 0.02                                    # 2.99
        z_slab = Z1 - 0.10
        slab = kit('GallerySlab', 'M_Concrete')
        I.prism(slab, ER(ga, gb, y0, y1), C.Z_L1_SOFFIT, z_slab)
        polys = [ER(ga, gb, yp, YNI1)]
        for Es in EXT_STAIRS['e']:
            if ga < Es < gb:
                polys.append(ER(Es - 0.85 / M, Es + 0.85 / M, y0, yp))
        for a in seg.axes:
            I.prism(slab, ER(a - D_ENT / M, a + D_ENT / M, y1, YN1), C.Z_L1_SOFFIT, z_slab)
            polys.append(ER(a - D_ENT / M, a + D_ENT / M, YNI1, Y_ENT))
        for p in polys:
            I.floor_stack(kit, p, top, BU.GALLERY_DECK[:-1], prefix='Gallery')

    # ---------------------------------------------------- north pavilion
    def npav(self):
        """L2 + L3 cavity of the north pavilion over the gallery (z 5.72 ->
        tile underside), the L2 (F2, over the gallery) and L3 slabs, the R1
        roof layers; party walls; per house: see House."""
        R, kit, part = self.R, self.kit, self.part
        e0, e1 = self.rng(part, 'room')
        q0, q1 = self.rng(part, 'poly')
        t0, t1 = self.rng(part, 'cut')
        b0, b1 = self.rng(part, 'slab')
        # slab zones run under the joint leaves (through the body ends at joints)
        R.cEY(self.np, t0, t1, YNI0, YNI1, C.Z_L2_SOFFIT, Z2 - 0.10)
        R.cEY(self.np, t0, t1, YNI0, YNI1, Z3 - SLAB, Z3 - 0.10)
        R.cprism(self.np, ER(e0, e1, YNI0, YNI1), C.Z_L2_SOFFIT - 0.01, roof_under('N'))
        I.prism(self.kit('FloorSlabExposed', 'M_Concrete'), ER(b0, b1, YNI0, YNI1), Z2 - SLAB, Z2 - 0.10)
        I.prism(self.kit('FloorSlab', 'M_Structure'), ER(b0, b1, YNI0, YNI1), Z3 - SLAB, Z3 - 0.10)
        I.sloped_stack(kit, ER(q0, q1, YNI0, YNI1), roof_under('N'), BU.ROOF_TILE_UNDER, prefix='Roof',
                       slope=SLOPE_N)
        # party walls (W5) at L2 and L3
        for E in self.party_lines(part):
            for zf in (Z2, Z3):
                top = SOFF[Z2] if zf == Z2 else roof_ceiling('N')
                wall(kit, BU.WALL_SEP, (xE(E), yY(YNI0)), (xE(E), yY(YNI1)), zf - 0.10, top, prefix='Sep')

    def party_lines(self, p, campo_too=True):
        out = []
        for E in C.PARTY:
            if p.E0 + 1e-6 < E < p.E1 - 1e-6 and not any(abs(E - j) < 1e-6 for j in C.JOINT_E):
                out.append(E)
        return out

    # ---------------------------------------------------- south pavilion
    def spav_normal(self):
        R, kit, p = self.R, self.kit, self.normal
        sp = self.sp
        e0, e1 = self.rng(p, 'room')                   # L2 / L3 (continuous into the campo part)
        f0, f1 = self.rng(p, 'room', campo_wall=True)  # L1: the campo end is an exterior wall
        t0, t1 = self.rng(p, 'cut')
        tf0, tf1 = self.rng(p, 'cut', campo_wall=True)
        b0, b1 = self.rng(p, 'slab')
        bf0, bf1 = self.rng(p, 'slab', campo_wall=True)
        # L1: slab zone under everything (through at joints), the storey to the
        # south face (Y 7.224, the dividing-wall zone of interior_carpet_ms)
        R.cEY(sp, tf0, tf1, YSI0, YS1 + EPS, C.Z_L1_SOFFIT - 0.10, Z1 - 0.10)
        R.cEY(sp, f0, f1, YSI0, YS1 + EPS, C.Z_L1_SOFFIT - 0.10, C.Z_L2_SOFFIT)
        I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(bf0, bf1, YSI0, YS1), C.Z_L1_SOFFIT, Z1 - 0.10)
        # L2: slab zone and storey to the south face (rooms run on across the joint)
        R.cEY(sp, t0, t1, YSI0, YS1 + EPS, C.Z_L2_SOFFIT, Z2 - 0.10)
        R.cEY(sp, e0, e1, YSI0, YS1 + EPS, C.Z_L2_SOFFIT, Z3 - SLAB)
        I.prism(kit('FloorSlab', 'M_Structure'), ER(b0, b1, YSI0, YS1), Z2 - SLAB, Z2 - 0.10)
        # L3: kitchens between the notches, their slab, the roof
        self.spav_l3(sp, p)
        # party walls L1 / L2 / L3 (not on the campo line at L1)
        for E in self.party_lines(p):
            self.spav_party(E, L2_SOUTH)
        for E in CAMPO['e']:
            if abs(E - p.E0) < 1e-6 or abs(E - p.E1) < 1e-6:
                self.spav_party(E, L2_SOUTH, l1=False)

    def spav_l3(self, body, p):
        kit, R = self.kit, self.R
        e0, e1 = self.rng(p, 'room')
        q0, q1 = self.rng(p, 'poly')
        for g0, g1 in C.notch_gaps(e0, e1, p.axes, half=D_KIT):
            R.cprism(body, ER(g0, g1, YSI0, YSI1), Z3 - SLAB - 0.01, roof_under('S'))
        for g0, g1 in C.notch_gaps(q0, q1, p.axes, half=D_KIT):
            I.prism(kit('FloorSlab', 'M_Structure'), ER(g0, g1, YSI0, YSI1), Z3 - SLAB, Z3 - 0.10)

    def spav_roof(self):
        """R1 under the south pavilion's tiles, kitchens between the notches;
        one run over the normal and the campo part (no layer ends on the
        abutment E 35.5 / 48.5, where the exterior's gutters end)."""
        parts = [p for p in (self.normal, self.campo) if p is not None]
        rs = [self.rng(p, 'poly') for p in parts]
        q0, q1 = min(r[0] for r in rs), max(r[1] for r in rs)
        axes = sorted(a for p in parts for a in p.axes)
        for g0, g1 in C.notch_gaps(q0, q1, axes, half=D_KIT):
            I.sloped_stack(self.kit, ER(g0, g1, YSI0, YSI1), roof_under('S'), BU.ROOF_TILE_UNDER, prefix='Roof',
                           slope=SLOPE_S)

    def spav_party(self, E, y_end, l1=True, campo_side=None):
        kit = self.kit
        x = xE(E)
        if l1:
            wall(kit, BU.WALL_SEP, (x, yY(YSI0)), (x, yY(L1_SOUTH)), Z1 - 0.10, SOFF[Z1], prefix='Sep')
        wall(kit, BU.WALL_SEP, (x, yY(YSI0)), (x, yY(y_end)), Z2 - 0.10, SOFF[Z2], prefix='Sep')
        wall(kit, BU.WALL_SEP, (x, yY(YSI0)), (x, yY(YSI1)), Z3 - 0.10, roof_ceiling('S'), prefix='Sep')

    def spav_campo(self):
        """The campo part of the south pavilion from L2 (on the pier bands):
        L2 rooms to the campo face (F2 over the campo), L3 as ordinary, the
        terrace over the L2 extension to the parapet / oculus panel."""
        R, kit, p = self.R, self.kit, self.campo
        sp = self.spc
        e0, e1 = self.rng(p, 'room')
        q0, q1 = self.rng(p, 'poly')
        t0, t1 = self.rng(p, 'cut')
        b0, b1 = self.rng(p, 'slab')
        a = p.axes[0]
        R.cEY(sp, t0, t1, YSI0, Y_CAMPO_IN, C.CAMPO_SP_Z0 - 0.10, Z2 - 0.10)
        # L2 storey; behind the baths the body stays as the chase (Y 7.79 -> 8.0)
        R.cEY(sp, e0, e1, YSI0, Y_BATH2_CAMPO, Z2 - 0.10, Z3 - SLAB)
        for g0, g1 in C.minus_ranges(e0, e1, [(a - D_CORE / M, a + D_CORE / M)]):
            R.cEY(sp, g0, g1, Y_BATH2_CAMPO - EPS, Y_CAMPO_IN, Z2 - 0.10, Z3 - SLAB)
        # 2 mm short of the abutment with the normal part: the exterior's campo
        # band on the pier row ends on that line (no coplanar end faces)
        c0 = b0 + (0.002 / M if p.k0 == 'campo' else 0.0)
        c1 = b1 - (0.002 / M if p.k1 == 'campo' else 0.0)
        I.prism(kit('FloorSlabExposed', 'M_Concrete'), ER(c0, c1, YSI0, Y_CAMPO_IN), Z2 - SLAB, Z2 - 0.10)
        self.spav_l3(sp, p)
        # terrace over the L2 extension (R3), outside the notch (the notch: House)
        notch = [(a - NOTCH_HALF / M, a + NOTCH_HALF / M)]
        for g0, g1 in C.minus_ranges(e0, e1, notch):
            R.cEY(sp, g0, g1, YS1 - EPS, Y_CAMPO_PAR, Z3 - SLAB, Z3 + 0.20)
        for g0, g1 in C.minus_ranges(q0, q1, notch):
            self.deck(ER(g0, g1, YS1, Y_CAMPO_PAR), ER(g0, g1, YS1, Y_CAMPO_PAR))
        # L2 party half wall on the campo line beyond NorthPavM's end wall
        for E in CAMPO['e']:
            if abs(E - p.E0) < 1e-6 or abs(E - p.E1) < 1e-6:
                inward = 1 if abs(E - p.E0) < 1e-6 else -1     # toward the campo house (+E = -x)
                half = [('Leaf', 'M_HollowBrick', 0.09), ('Plaster', 'M_PlasterInt', 0.015)]
                # from 2 mm inside the party wall's end (NorthPavM's end band is flush with Y 7.776)
                A, B = (xE(E), yY(L2_SOUTH - 0.002 / M)), (xE(E), yY(Y_CAMPO_IN))
                # A -> B runs south: its left is east (-E); the campo house lies right for inward > 0
                lay = half if inward > 0 else list(reversed(half))
                wall(kit, lay, A, B, Z2 - 0.10, SOFF[Z2], prefix='Sep', offset=-inward * BU.total(half) / 2)

    def deck(self, slab_poly, layer_poly):
        if slab_poly is not None:
            I.prism(self.kit('FloorSlab', 'M_Structure'), slab_poly, Z3 - SLAB, Z3 - 0.10)
        if layer_poly is not None:
            I.floor_stack(self.kit, layer_poly, Z3 + BU.TERRACE_UP, BU.TERRACE[:-1], prefix='Terrace')

    # -------------------------------------------------------------- joint
    def joint(self):
        """JointNM above 5.72: the L2 rooms run across it (camera 3 to
        NorthPavM's face, bagno 1 to 7.72 with the chase), the slab 5.72 ->
        5.92 and the terrace deck R3 (9.15) over them."""
        R, kit, p = self.R, self.kit, self.normal
        jn = self.jnm
        if R.obj(jn) is None:
            return
        j0, j1 = C.JOINTS['NM'][0], C.JOINTS['NM'][1]
        xs = [v.co.x for v in R.obj(jn).data.vertices]
        n0, n1 = 36.0 - max(xs) / M, 36.0 - min(xs) / M     # its E extent
        rk = lambda k, E, inward: (E + inward * (LEAF / M) if k == 'joint' else E - inward * EPS)
        r0, r1 = rk(p.k0, p.E0, 1), rk(p.k1, p.E1, -1)
        R.cEY(jn, n0 - EPS, n1 + EPS, j0 - EPS, j1 + EPS, C.Z_L2_SOFFIT, Z2 - 0.10)
        R.cEY(jn, n0 - EPS, n1 + EPS, j0 - EPS, j1 + EPS, Z3 - SLAB, Z3 + 0.20)
        R.cEY(jn, max(r0, n0 - EPS), min(r1, n1 + EPS), j0 - EPS, Y_BATH2, Z2 - 0.10, Z3 - SLAB)
        baths = [(a - D_CORE / M, a + D_CORE / M) for a in p.axes]
        for g0, g1 in C.minus_ranges(max(r0, n0 - EPS), min(r1, n1 + EPS), baths):
            R.cEY(jn, g0, g1, Y_BATH2 - EPS, j1 + EPS, Z2 - 0.10, Z3 - SLAB)
        I.prism(kit('FloorSlab', 'M_Structure'), ER(n0, n1, j0, j1), Z2 - SLAB, Z2 - 0.10)
        # deck: slab over the whole strip, layers split by the notch dividers
        self.deck(ER(n0, n1, j0, j1), None)
        dv = [(a - 0.10 / M, a + 0.10 / M) for a in p.axes]
        for g0, g1 in C.minus_ranges(n0, n1, dv):
            self.deck(None, ER(g0, g1, j0, j1))

    # ------------------------------------------------------------ cantine
    def cantine(self):
        """L0 cellars in the cantine ranges of the north row's S-pav band
        (n11, SE 56, SE 65): cells between 120 brick partitions, F4 floor at
        -0.32, ceiling plaster under the L1 slab, a cellar door each onto the
        joint corridor."""
        R, kit, p = self.R, self.kit, self.normal
        name = self.cant
        if R.obj(name) is None:
            return
        y0, y1 = C.BAND_Y0 + WM, YSI1
        a_in, b_in = p.e0, p.e1
        for c0, c1 in C_RANGES(a_in, b_in):
            lo = c0 + (0.12 / M if c0 > a_in + 1e-6 else (LEAF - C.GAP / 2) / M)
            hi = c1 - (0.12 / M if c1 < b_in - 1e-6 else (LEAF - C.GAP / 2) / M)
            walls = cellar_walls(lo, hi, p.axes)
            edges = [lo] + [v for w in walls for v in (w - 0.06 / M, w + 0.06 / M)] + [hi]
            for w in walls:
                I.prism(kit('CellarBrick', 'M_Brick'), ER(w - 0.06 / M, w + 0.06 / M, y0, y1),
                        CELLAR['z0'] - 0.32, C.Z_L1_SOFFIT)
            R.cEY(name, lo, hi, y0, y1, -0.75, C.Z_L1_SOFFIT + 0.05)
            for i in range(0, len(edges), 2):
                E0, E1 = edges[i], edges[i + 1]
                poly = ER(E0, E1, y0, y1)
                I.floor_stack(kit, poly, CELLAR['z0'], BU.FLOOR_CELLAR, prefix='')
                I.prism(kit('CeilingPlaster', 'M_PlasterInt'), poly, C.Z_L1_SOFFIT - 0.01, C.Z_L1_SOFFIT)
                if (E1 - E0) * M >= 1.0:
                    self.cellar_door((E0 + E1) / 2)

    def cellar_door(self, Ec):
        R, kit = self.R, self.kit
        f = geo.Face('y', yY(YS1), -1)
        u0, u1 = sorted((xE(Ec) - CELLAR['w'] / 2, xE(Ec) + CELLAR['w'] / 2))
        out = [(u0, CELLAR['z0']), (u1, CELLAR['z0']), (u1, CELLAR['z1']), (u0, CELLAR['z1'])]
        rec = geo.register(f, out, 'rect', u=(u0 + u1) / 2, z0=CELLAR['z0'], width=CELLAR['w'],
                           height=CELLAR['z1'] - CELLAR['z0'], through=None, recess=0.0)
        rec['target'], rec['type'] = self.cant, 'CD'
        self.new_recs.append(rec)
        zs = CELLAR['z0'] - CELLAR['sill']
        f.solid(R.cutter(self.cant), [(u0, zs), (u1, zs), (u1, CELLAR['z1']), (u0, CELLAR['z1'])], WALL + 0.05,
                outside=0.05)
        I.prism(kit('Thresholds', 'M_Concrete'), I.rect(u0, u1, yY(YS1), yY(YSI1)), zs, CELLAR['z0'])

    # -------------------------------------------------------------- finish
    def finish(self):
        """Joinery, flush, cut the wall linings round the windows."""
        R, kit = self.R, self.kit
        names = [self.np, self.sp, self.spc, self.cant]
        recs = [r for n in names for r in R.recs(n)]
        xs = [xE(a) for a in self.seg.axes]
        recs += [r for r in R.recs(self.core) if r.get('type') != 'DN'
                 and any(abs((r['coord'] if r['axis'] == 'x' else sum(J.dims(r)[:2]) / 2) - x) < 3.5 for x in xs)]
        recs += self.new_recs
        import time
        t0 = time.time()
        for r in recs:
            if not r.get('done') and J.classify(r) == 'T':
                r['done'] = True
                trifora_joinery(kit, r)
        for ra, rb in two_light_pairs(recs):
            two_light_joinery(kit, ra, rb)
        for r in recs:
            if not r.get('done') and r['kind'] == 'rect' and J.classify(r) == 'E':
                window_e(kit, r)
        J.build_openings(kit, recs)
        reveal_finishes(kit, recs)
        objs = kit.flush()
        t1 = time.time()
        lin = [r for r in recs if r.get('type') not in ('PN', 'DN', 'CD') and J.classify(r) is not None
               and not r['target'].startswith('SM_Carpet_CantineN')]
        _cut_linings(self.R.ctx, [objs.get(kit.name(n)) for n in
                                  ('WallLiningAdhesive', 'WallLiningInsulation', 'WallLiningBoard')], lin)
        print(f'[carpet north] {self.seg.tag}: joinery + flush {t1 - t0:.1f} s, linings {time.time() - t1:.1f} s')


def C_RANGES(a_in, b_in):
    """Cantine ranges clipped to a part."""
    out = []
    for c0, c1 in C.CANTINE_N:
        lo, hi = max(c0, a_in), min(c1, b_in)
        if hi - lo > 1.0 / M:
            out.append((lo, hi))
    return out


def cellar_walls(lo, hi, axes):
    """E of the 120 cellar partitions in [lo, hi]: either side of the cell
    under the core (with the door from the portico) and of the arch cells,
    and on the party walls; none leaving a cell under 0.9 m."""
    cand = sorted([a + d / M for a in axes for d in (-2.16, -0.76, 0.76, 2.16)] +
                  [E for E in C.PARTY if not any(abs(E - j) < 1e-6 for j in C.JOINT_E)])
    walls = [w for w in cand if lo + 0.5 / M < w < hi - 0.5 / M]
    changed = True
    while changed:
        changed = False
        edges = [lo] + walls + [hi]
        for i in range(1, len(edges) - 1):
            if (edges[i] - edges[i - 1]) * M - 0.06 < 0.9 or (edges[i + 1] - edges[i]) * M - 0.06 < 0.9:
                walls.pop(i - 1)
                changed = True
                break
    return walls


# ===================================================================== house
class House:
    """One H-house of the north row: two mirrored dwellings (s = +1 west,
    -1 east; d = metres from the house axis toward side s)."""

    def __init__(self, S, a):
        self.S, self.R, self.kit, self.a = S, S.R, S.kit, a
        self.campo = a in CAMPO_HOUSES
        self.xa = xE(a)
        self.kind = {s: side_kind(a, s) for s in (-1, 1)}
        self.sp = S.spc if self.campo else S.sp

    def X(self, s, d):
        return self.xa - s * d

    def rect(self, s, d0, d1, Y0, Y1):
        return I.rect(self.X(s, d0), self.X(s, d1), yY(Y0), yY(Y1))

    def cut(self, name, s, d0, d1, Y0, Y1, z0, z1):
        self.R.cbox(name, self.X(s, d0), self.X(s, d1), yY(Y0), yY(Y1), z0, z1)

    def P(self, s, d, Y):
        return (self.X(s, d), yY(Y))

    # ---------------------------------------------------------------- all
    def build(self):
        self.core_volumes()
        self.slabs()
        for s in (-1, 1):
            self.cells(s)
            self.walls(s)
            self.doors(s)
            self.stairs(s)
        self.axis_walls()
        self.entrance()
        self.vault()
        self.terrace()
        if self.campo:
            self.closing_wall()

    # ------------------------------------------------------------ hollows
    def core_volumes(self):
        S, h = self.S, self
        core, np_, sp = S.core, S.np, self.sp
        D = D_CORE
        # the core: one void through L1 -> vault, both dwellings; its bottom
        # 0.30 everywhere (the L1 core slab and its edge band replace it)
        h.cut(core, 1, -D, D, YN1 - EPS, YS0 + EPS, C.Z_L1_SOFFIT - 0.10, T + 3.5)
        h.cut(core, 1, -CORE_W / 2 - 0.05, CORE_W / 2 + 0.05, YN1 - EPS, YS0 + EPS, C.Z_L1_SOFFIT - 0.10, Z1)
        # the core's landing part lies inside the S-pav beyond the notch: keep it in the notch only
        for s in (-1, 1):
            h.cut(core, s, NOTCH_HALF, CORE_W / 2 + 0.05, YS0, YX1 + EPS, Z3 - SLAB, T + 3.5)
        h.cut(core, 1, -CORE_W / 2 - 0.05, CORE_W / 2 + 0.05, YS0, YX1 + EPS, Z3 - SLAB, JOINTS['NM'][2])
        # L3 notch landing: core body to the top, S-pav up to the vault's outer surface
        h.cut(core, 1, -D, D, YS0 - EPS, YX0, Z3 - SLAB, T + 3.5)
        if self.R.obj(sp) is not None:
            arc = I._arc_band(self.xa, VAULT_ZC, VAULT_R0, VAULT_R0 - 0.1, D_CORE, 24)[:25]
            prof = [(self.xa - D, Z3 - SLAB), (self.xa + D, Z3 - SLAB)] + list(reversed(arc))
            geo.add_prism_y(self.R.cutter(sp), prof, yY(YX0), yY(YS0 - EPS))
        for name in (core, sp):
            for s in (-1, 1):
                # kitchen door through the landing | kitchen wall
                yc = 5.36
                h.cut(name, s, D_CORE - 0.01, D_KIT + 0.01, yc - DOOR_ROOM / 2 / M, yc + DOOR_ROOM / 2 / M,
                      Z3 - 0.10, Z3 + DOOR_HEAD)
                # terrace door through the cross wall
                h.cut(name, s, TER['d'][0], TER['d'][1], YX0 - EPS, YX1 + EPS, Z3 - 0.10, Z3 + BU.TERRACE_UP + TER['h'])
        # N-pav south wall over the core width at L2 / L3 (beam at L3)
        h.cut(np_, 1, -D, D, YNI1 - EPS, YN1 + EPS, C.Z_L2_SOFFIT, Z_BEAM3)
        # S-pav north wall over the hall width at L1 / L2 (no wall, n67)
        if not self.campo:
            h.cut(sp, 1, -D, D, YS0 - EPS, YSI0 + EPS, C.Z_L1_SOFFIT - 0.10, C.Z_L2_SOFFIT)
        h.cut(sp, 1, -D, D, YS0 - EPS, YSI0 + EPS, C.Z_L2_SOFFIT - (0.10 if self.campo else 0.0), Z3 - SLAB)
        # notch terrace deck zone (S-pav from 8.72; R3 to 9.15)
        y_end = Y_CAMPO_PAR if self.campo else YS1 + EPS
        h.cut(sp, 1, -NOTCH_HALF - 0.01, NOTCH_HALF + 0.01, YX1, y_end, Z3 - SLAB, Z3 + 0.20)
        if self.campo:
            # campo L2 bath chase: keep the body Y 7.79 -> 8.0 behind the bath (cut back below)
            pass

    # -------------------------------------------------------------- slabs
    def slabs(self):
        kit, h = self.kit, self
        D = D_CORE
        sl = kit('FloorSlab', 'M_Structure')
        # L1 core slab, fair-faced and 2 cm proud of the core faces, its edge
        # band to 3.01 round the sides as the exterior's (n9)
        cs = kit('CoreSlab', 'M_Concrete')
        hw = CORE_W / 2 + 0.02
        y_end = Y_CLOSE + 0.02 / M if self.campo else YS0
        I.prism(cs, h.rect(1, -hw, hw, YN1, y_end), Z1 - SLAB - 0.03, Z1 - 0.10)
        for s in (-1, 1):
            I.prism(cs, h.rect(s, D, hw, YN1, y_end), Z1 - 0.10, Z1)
        # L1 halls in the S-pav north wall zone
        if not self.campo:
            I.prism(kit('FloorSlabExposed', 'M_Concrete'), h.rect(1, -D, D, YS0, YSI0), Z1 - SLAB, Z1 - 0.10)
        # L2: N-pav strip in front of the entrance, core landing, corridors, halls
        I.prism(kit('FloorSlabExposed', 'M_Concrete'), h.rect(1, -D, D, YNI1, Y_ENT), Z2 - SLAB, Z2 - 0.10)
        I.prism(sl, h.rect(1, -D, D, Y_ENT, Y_FOOT), Z2 - SLAB, Z2 - 0.10)
        for s in (-1, 1):                  # corridors: PL short of the well edge (its plaster, well_edges)
            I.prism(sl, h.rect(s, D_BAND + PL, D, Y_FOOT, YS0), Z2 - SLAB, Z2 - 0.10)
            I.prism(sl, h.rect(s, D_BAND + PL, D, Y_FOOT, YS0), Z3 - SLAB, Z3 - 0.10)
        I.prism(kit('FloorSlabExposed' if self.campo else 'FloorSlab', 'M_Concrete' if self.campo else 'M_Structure'),
                h.rect(1, -D, D, YS0, YSI0), Z2 - SLAB, Z2 - 0.10)
        # L3: core strip (beam zone + landing), notch landing
        I.prism(sl, h.rect(1, -D, D, YNI1, Y_FOOT), Z3 - SLAB, Z3 - 0.10)
        I.prism(sl, h.rect(1, -D, D, YS0, YX0), Z3 - SLAB, Z3 - 0.10)

    # -------------------------------------------------------------- cells
    def cells(self, s):
        h, kit = self, self.kit
        kN = self.kind[s]
        dN, tN = outer(kN)                     # N-pav / S-pav L2-L3
        d1, t1 = outer(kN, l1_spav=True)       # S-pav L1
        D = D_CORE
        flat = 'flat'
        cell = self.cell
        # ---- L1
        cell(s, D_AX, D, YN1, Y_FOOT, Z1, dict(N='W', S='O', A='W', O='L'), FL_OPEN, flat)          # landing
        y_core_end = Y_C0 if self.campo else YS0
        cell(s, D_AX + 0.002, D_BAND - 0.002, Y_FOOT + 0.003 / M, y_core_end, Z1,
             dict(N='O', S='W' if self.campo else 'O', A='W', O='O'), FL_OPEN, None)      # flight band (under it)
        cell(s, D_BAND, D, Y_FOOT, y_core_end, Z1, dict(N='O', S='W' if self.campo else 'O', A='O', O='L'),
             FL_OPEN, flat)                                                                          # corridor
        if not self.campo:
            yh = Y_HB[1] - T_HB[1] / 2 / M
            yb = Y_HB[1] + T_HB[1] / 2 / M
            cell(s, D_AX, D, YS0, YSI0, Z1, dict(N='O', S='O', A='W', O='L'), FL_OPEN, flat)          # pass
            cell(s, D_AX, D_P0, YSI0, yh, Z1, dict(N='O', S='W', A='W', O='W'), FL_OPEN, flat)       # hall
            cell(s, D_AX, D_P0, yb, L1_SOUTH, Z1, dict(N='W', S='W', A='W', O='W'), FL_OPEN, flat)   # bagno 2
            cell(s, D_P1, d1, YSI0, L1_SOUTH, Z1, dict(N='L', S='W', A='W', O=t1), FL_OPEN, flat)    # camera 1
        # ---- L2
        fl_n = FL_OPEN                                                                   # over the gallery
        cell(s, D_AX, D, YNI0, YNI1, Z2, dict(N='L', S='W', A='W', O='O'), fl_n, flat)   # camera 2 (core side)
        cell(s, D, dN, YNI0, YNI1, Z2, dict(N='L', S='L', A='O', O=tN), fl_n, flat)      # camera 2
        cell(s, D_AX, D, Y_C2S, Y_FOOT, Z2, dict(N='W', S='O', A='W', O='L'), FL_INT, flat)   # landing
        cell(s, D_BAND, D, Y_FOOT, YS0, Z2, dict(N='O', S='O', A='O', O='L'), None, flat)      # corridor
        self.corridor_floor(s, Z2)
        fl_s = FL_OPEN if self.campo else FL_INT
        y2 = Y_CAMPO_IN if self.campo else L2_SOUTH
        yb2 = Y_BATH2_CAMPO if self.campo else Y_BATH2
        yh = Y_HB[2] - T_HB[2] / 2 / M
        yb = Y_HB[2] + T_HB[2] / 2 / M
        cell(s, D_AX, D, YS0, YSI0, Z2, dict(N='O', S='O', A='W', O='L'), fl_s, flat)              # pass
        cell(s, D_AX, D_P0, YSI0, yh, Z2, dict(N='O', S='W', A='W', O='W'), fl_s, flat)            # hall
        cell(s, D_AX, D_P0, yb, yb2, Z2, dict(N='W', S='P', A='W', O='W'), fl_s, flat)             # bagno 1
        cell(s, D_P1, dN, YSI0, y2, Z2, dict(N='L', S='L' if self.campo else 'P', A='W', O=tN), fl_s, flat)  # camera 3
        # ---- L3
        cell(s, D_AX, D, YNI0, YNI1, Z3, dict(N='L', S=('L', Z_BEAM3), A='W', O='O'), FL_INT, 'roofN')   # soggiorno
        cell(s, D, dN, YNI0, YNI1, Z3, dict(N='L', S='L', A='O', O=tN), FL_INT, 'roofN')
        cell(s, D_AX, D, YNI1, YN1, Z3, dict(N='O', S='O', A='W', O='L'), FL_INT, ('beam', Z_BEAM3),
             trim=dict(O=(0.002 / M, 0.0)))                                                              # pass
        cell(s, D_AX, D, YN1, Y_FOOT, Z3, dict(N='O', S='O', A='W', O='L'), FL_INT, 'vault')             # landing
        cell(s, D_BAND, D, Y_FOOT, YS0, Z3, dict(N='O', S='O', A='O', O='L'), None, 'vault')             # corridor
        self.corridor_floor(s, Z3)
        kd = (5.36 - DOOR_ROOM / 2 / M, 5.36 + DOOR_ROOM / 2 / M, Z3 + DOOR_HEAD)
        td = (TER['d'][0], TER['d'][1], Z3 + BU.TERRACE_UP + TER['h'])
        cell(s, D_AX, D, YS0, YX0, Z3, dict(N='O', S='L', A='W', O='L'), FL_INT, 'vault',
             gaps=dict(O=[kd], S=[td]))                                                                  # notch landing
        cell(s, D_KIT, dN, YSI0, YSI1, Z3, dict(N='L', S='L', A='L', O=tN), FL_INT, 'roofS',
             gaps=dict(A=[kd]))                                                                          # cucina
        # beam skin on the core side of the L3 beam, up to the vault
        sk = kit('WallPlaster', 'M_PlasterInt')
        zs = Z_BEAM3
        x1 = math.sqrt(max(VAULT_RIN ** 2 - (zs - VAULT_ZC) ** 2, 0.0))
        x1 = min(x1, D_CORE - LIN)
        n = 8
        xs = [D_AX + (x1 - D_AX) * i / n for i in range(n + 1)]
        zt = [VAULT_ZC + math.sqrt(VAULT_RIN ** 2 - x * x) for x in xs]
        prof = [(self.X(s, x), z) for x, z in zip(xs, zt)] + [(self.X(s, D_AX), zs)]
        geo.add_prism_y(sk, I.ccw(prof), yY(YN1) - PL, yY(YN1))
        self.lining_returns(s)

    def lining_returns(self, s):
        """Board returns (WallLiningBoard) where a lined face ends at an
        external corner of the masonry or in front of a flush finish, so
        that the lining's adhesive / insulation edges are not left bare:
        - L1 / L2 pass through the S-pav wall: the core-face lining (O) ends
          at YSI0, 55 mm proud of the hall partition's plaster;
        - L2 camera 2: the S lining of the outer cell ends at D_CORE, 55 mm
          proud of the camera-2 partition's plaster (core cell);
        - L3 pass through the N-pav wall into the soggiorno: the pass lining
          (O) is carried round the jamb (adhesive + insulation) and closed by
          a board flush with the soggiorno's S lining; the S lining over the
          beam (core cell, from Z_BEAM3) gets a board soffit."""
        kit = self.kit
        bd = kit('WallLiningBoard', 'M_PlasterInt')
        BT = BU.LINING[-1][2]                                  # board 0.010
        # L1 (not in the campo houses: closed core) / L2 passes, hall side
        for zf in ((Z2,) if self.campo else (Z1, Z2)):
            I.prism(bd, self.rect(s, D_CORE - LIN, D_CORE, YSI0, YSI0 + BT / M), zf, SOFF[zf] - 0.01)
        # L2 camera 2, core cell side
        I.prism(bd, self.rect(s, D_CORE - BT, D_CORE, YNI1 - LIN / M, YNI1), Z2, SOFF[Z2] - 0.01)
        # L3 pass jamb: lining carried from the pass (ends at YNI1 + 2 mm)
        # to the soggiorno's board plane, over the core cell's floor
        ya, yb = YNI1 + 0.002 / M, YNI1 - (LIN - BT) / M
        d = D_CORE
        for elem, mat, t in BU.LINING[:-1]:
            I.prism(kit(f'Wall{elem}', mat), self.rect(s, d - t, d, ya, yb), Z3, Z_BEAM3)
            d -= t
        I.prism(bd, self.rect(s, D_CORE - LIN, D_CORE, yb, YNI1 - LIN / M), Z3, Z_BEAM3)
        I.prism(bd, self.rect(s, D_CORE - LIN, d, ya, yb), Z3, Z_BEAM3)
        # soffit of the S lining over the beam (core cell)
        I.prism(bd, self.rect(s, D_AX, D_CORE - LIN, YNI1 - LIN / M, YNI1), Z_BEAM3 - 0.01, Z_BEAM3)

    def cell(self, s, d0, d1, Y0, Y1, zf, sides, floor, ceil, gaps=None, trim=None):
        """A room (or part of one): floor layers inside the finished faces,
        linings / plaster on its masonry sides, ceiling plaster."""
        kit = self.kit
        gaps = gaps or {}

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
            I.prism(kit('CeilingPlaster', 'M_PlasterInt'), poly, SOFF[zf] - 0.01, SOFF[zf])
        elif isinstance(ceil, tuple) and ceil[0] == 'beam':
            I.prism(kit('CeilingPlaster', 'M_PlasterInt'), poly, ceil[1] - 0.01, ceil[1])
        # wall finishes
        if ceil == 'flat':
            top = SOFF[zf]
        elif ceil in ('roofN', 'roofS'):
            top = roof_ceiling(ceil[-1])
        elif ceil == 'vault':
            top = vault_soffit(self.xa)
        elif isinstance(ceil, tuple):
            top = ceil[1]
        else:
            top = SOFF[zf]
        z0 = zf - 0.10
        th = {k: (LIN if typ(k)[0] == 'L' else PL) for k in 'NSAO'}
        lay = lambda k: BU.LINING if typ(k)[0] == 'L' else PLASTER
        has = lambda k: typ(k)[0] in ('L', 'P')
        # N / S run full length, A / O between them
        for k in 'NS':
            if not has(k):
                continue
            t, zfrom = typ(k)
            yA = Y0 if k == 'N' else Y1
            inward = 1 if k == 'N' else -1
            self.strip(s, 'd', yA, inward, d0, d1, zfrom if zfrom is not None else z0, top, lay(k), gaps.get(k, ()))
        for k in 'AO':
            if not has(k):
                continue
            t, zfrom = typ(k)
            dA = d0 if k == 'A' else d1
            inward = 1 if k == 'A' else -1
            ya = Y0 + (th['N'] / M if has('N') and typ('N')[1] is None else 0.0)
            yb = Y1 - (th['S'] / M if has('S') and typ('S')[1] is None else 0.0)
            if trim and k in trim:
                ya, yb = ya + trim[k][0], yb - trim[k][1]
            self.strip(s, 'Y', dA, inward, ya, yb, zfrom if zfrom is not None else z0, top, lay(k), gaps.get(k, ()))

    def strip(self, s, along, c, inward, l0, l1, z0, top, layers, gaps=()):
        """Wall finish on a masonry face: along 'd' (face at Y = c, layers
        toward +Y if inward > 0) or along 'Y' (face at d = c, toward +d);
        from l0 to l1 (d metres or Y modules); gaps [(g0, g1, head)] leave
        door openings. Tops follow `top` (a level or z(x, y)); strips under
        the vault are split into short pieces."""
        kit = self.kit
        off = 0.0
        vault = getattr(top, 'curved', False) and along == 'd'
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
            pieces = []
            cur = l0
            for g0, g1, head in sorted(gaps):
                if g0 > cur:
                    pieces.append((cur, g0, z0))
                pieces.append((g0, g1, head))
                cur = g1
            if cur < l1:
                pieces.append((cur, l1, z0))
            for p0, p1, zb in pieces:
                n = max(1, int(math.ceil(abs(p1 - p0) / 0.25))) if vault else 1
                for i in range(n):
                    q0, q1 = p0 + (p1 - p0) * i / n, p0 + (p1 - p0) * (i + 1) / n
                    poly = self.rect(s, q0, q1, a0, a1) if along == 'd' else self.rect(s, a0, a1, q0, q1)
                    zt = top
                    if callable(top):
                        ztop = min(top(x, y) for x, y in poly)
                        if zb >= ztop - 1e-4:
                            continue
                    elif zb >= top - 1e-4:
                        continue
                    I.prism(bm, poly, zb, zt)
            off += t

    # -------------------------------------------------------------- walls
    def walls(self, s):
        kit, h = self.kit, self
        D = D_CORE
        dc = (D_P0 + D_P1) / 2
        # camera | hall partition, L1 and L2
        if not self.campo:
            wall(kit, PART_CAM, h.P(s, dc, YSI0), h.P(s, dc, L1_SOUTH), Z1 - 0.10, SOFF[Z1],
                 doors=[((5.36 - YSI0) * M, DOOR_ROOM, Z1 + DOOR_HEAD)], prefix='Partition')
        y2 = Y_CAMPO_IN if self.campo else L2_SOUTH
        wall(kit, PART_CAM, h.P(s, dc, YSI0), h.P(s, dc, y2), Z2 - 0.10, SOFF[Z2],
             doors=[((5.40 - YSI0) * M, DOOR_ROOM, Z2 + DOOR_HEAD)], prefix='Partition')
        # hall | bath partitions (along d)
        for lvl, zf, dd in ((1, Z1, 1.23), (2, Z2, 1.305)):
            if lvl == 1 and self.campo:
                continue
            st = BU.PARTITION if lvl == 1 else BU.PARTITION_WET
            wall(kit, st, h.P(s, D_AX, Y_HB[lvl]), h.P(s, D_P0, Y_HB[lvl]), zf - 0.10, SOFF[zf],
                 doors=[(dd - D_AX, DOOR_BATH, zf + DOOR_HEAD)], prefix='Partition')
        # camera 2 | landing partition (L2, along d)
        wall(kit, BU.PARTITION, h.P(s, D_AX, Y_C2), h.P(s, D, Y_C2), Z2 - 0.10, SOFF[Z2],
             doors=[(D_C2DOOR - D_AX, DOOR_ROOM, Z2 + DOOR_HEAD)], prefix='Partition')

    def axis_walls(self):
        """Axis wall between the two dwellings (W5 in the pavilions, RC spine
        in the core, 0.21), per storey."""
        kit, h = self.kit, self
        P = lambda Y: (self.xa, yY(Y))
        # L1
        wall(kit, SPINE, P(YN1), P(Y_C0 if self.campo else YS0), Z1 - 0.10, SOFF[Z1], prefix='Spine')
        if not self.campo:
            wall(kit, BU.WALL_SEP, P(YS0), P(L1_SOUTH), Z1 - 0.10, SOFF[Z1], prefix='Sep')
        # L2
        wall(kit, BU.WALL_SEP, P(YNI0), P(YNI1), Z2 - 0.10, SOFF[Z2], prefix='Sep')
        wall(kit, SPINE, P(YNI1), P(YS0), Z2 - 0.10, SOFF[Z2], prefix='Spine')
        # over the well the spine runs on through the slab zones (no slab there between the flights)
        for zf in (Z2, Z3):
            wall(kit, SPINE, P(Y_FOOT), P(YS0), zf - SLAB, zf - 0.10, prefix='Spine')
        wall(kit, BU.WALL_SEP, P(YS0), P(Y_BATH2_CAMPO if self.campo else Y_BATH2), Z2 - 0.10, SOFF[Z2],
             prefix='Sep')
        # L3: N-pav to the roof, beam zone, core strip and notch landing to the vault
        wall(kit, BU.WALL_SEP, P(YNI0), P(YNI1), Z3 - 0.10, roof_ceiling('N'), prefix='Sep')
        wall(kit, SPINE, P(YNI1), P(YN1), Z3 - 0.10, Z_BEAM3, prefix='Spine')
        zc = VAULT_ZC + VAULT_RIN + 0.002            # 2 mm into the vault lining board at the crown
        wall(kit, SPINE, P(YN1), P(YX0), Z3 - 0.10, zc, prefix='Spine')

    def doors(self, s):
        kit, h = self.kit, self
        dc = (D_P0 + D_P1) / 2
        sw_cam = -s                    # walls along +Y (south): +d (the camera) lies right for s = +1
        if not self.campo:
            I.door(kit, h.P(s, dc, YSI0), h.P(s, dc, L1_SOUTH), (5.36 - YSI0) * M, DOOR_ROOM, Z1 + DOOR_HEAD, Z1,
                   T_CAM - 0.002, hinge='a', swing=sw_cam)
        y2 = Y_CAMPO_IN if self.campo else L2_SOUTH
        I.door(kit, h.P(s, dc, YSI0), h.P(s, dc, y2), (5.40 - YSI0) * M, DOOR_ROOM, Z2 + DOOR_HEAD, Z2,
               T_CAM - 0.002, hinge='a', swing=sw_cam)
        for lvl, zf, dd, t in ((1, Z1, 1.23, 0.11), (2, Z2, 1.305, 0.15)):
            if lvl == 1 and self.campo:
                continue
            # walls along +d: the bath (south) lies left for s = +1
            I.door(kit, h.P(s, D_AX, Y_HB[lvl]), h.P(s, D_P0, Y_HB[lvl]), dd - D_AX, DOOR_BATH, zf + DOOR_HEAD, zf,
                   t - 0.002, hinge='b', swing=s)
            self.door_floor(s, 'd', Y_HB[lvl], dd, DOOR_BATH, t, zf, FL_OPEN if lvl == 1 else
                            (FL_OPEN if self.campo else FL_INT))
        I.door(kit, h.P(s, D_AX, Y_C2), h.P(s, D_CORE, Y_C2), D_C2DOOR - D_AX, DOOR_ROOM, Z2 + DOOR_HEAD, Z2,
               0.11 - 0.002, hinge='b', swing=-s)
        self.door_floor(s, 'd', Y_C2, D_C2DOOR, DOOR_ROOM, 0.11, Z2, FL_INT)
        if not self.campo:
            self.door_floor(s, 'Y', dc, 5.36, DOOR_ROOM, T_CAM, Z1, FL_OPEN)
        self.door_floor(s, 'Y', dc, 5.40, DOOR_ROOM, T_CAM, Z2, FL_OPEN if self.campo else FL_INT)
        # kitchen door through the L3 landing | kitchen wall (core masonry + both linings)
        dk = (D_CORE - LIN + D_KIT + LIN) / 2
        I.door(kit, h.P(s, dk, YS0), h.P(s, dk, YSI1), (5.36 - YS0) * M, DOOR_ROOM, Z3 + DOOR_HEAD, Z3,
               D_KIT - D_CORE + 2 * LIN - 0.002, hinge='a', swing=sw_cam)
        self.door_floor(s, 'Y', dk, 5.36, DOOR_ROOM, D_KIT - D_CORE + 2 * LIN, Z3, FL_INT)

    def door_floor(self, s, along, c, pos, w, t, zf, layers):
        """Floor layers in a door opening (between the two rooms' floors)."""
        if along == 'Y':
            poly = self.rect(s, c - t / 2, c + t / 2, pos - w / 2 / M, pos + w / 2 / M)
        else:
            poly = self.rect(s, pos - w / 2, pos + w / 2, c - t / 2 / M, c + t / 2 / M)
        I.floor_stack(self.kit, poly, zf, layers)

    # ------------------------------------------------------------- stairs
    def stairs(self, s):
        """Two superimposed straight flights against the axis wall, rising
        south: L1 -> L2 (15 x 0.2007) and L2 -> L3 (15 x 0.200), treads 0.235;
        light steel balustrades on the open edge and round the L3 well, a
        handrail on the spine (layers.md S1, report §6). The flights stand
        PL inside the band: their open side is a plastered string
        (flight_finishes)."""
        kit, h = self.kit, self
        start = h.P(s, D_AX, Y_FOOT)
        width = D_BAND - D_AX - PL
        rails = kit('BalustradeRails', 'M_Steel')
        for zf, rise in ((Z1, (Z2 - Z1) / N_RISERS), (Z2, (Z3 - Z2) / N_RISERS)):
            # 14 steps + the upper floor's edge as the 15th riser (flight() without
            # tread_top_last leaves a zero-width fin on the top riser)
            I.flight(kit, start, (0, -1), width, N_RISERS - 1, rise, GOING, zf, waist=FL_WAIST, side=-s,
                     tread_top_last=True, tread_t=FL_TREAD, nosing=FL_NOSE, tread_mat=TREAD_MAT)
            self.flight_finishes(s, zf, rise)
            # raked balustrade on the open edge, handrail on the spine
            for d, posts in ((D_BAND - 0.025, True), (D_AX + 0.055, False)):
                def pt(sv, dz):
                    z = zf + rise * (1 + (sv + 0.02) / GOING) + dz
                    return (h.X(s, d), yY(Y_FOOT) - sv, z)
                s_end = (N_RISERS - 1) * GOING
                _bar(rails, pt(-0.02, 0.90), pt(s_end, 0.90), 0.04)
                if posts:
                    _bar(rails, pt(-0.02, 0.45), pt(s_end, 0.45), 0.02)
                    for k in (0, 4, 8, 12):
                        sv = k * GOING + GOING / 2
                        zt = zf + (k + 1) * rise
                        _bar(rails, (h.X(s, d), yY(Y_FOOT) - sv, zt), pt(sv, 0.90), 0.025)
                else:
                    for sv in (0.3, s_end - 0.3):        # wall brackets
                        p = pt(sv, 0.90)
                        _bar(rails, p, (h.X(s, D_AX + 0.003), p[1], p[2]), 0.015)
        # horizontal balustrades: L2 and L3 corridor edges, L3 well's north edge
        for zf in (Z2, Z3):
            self.balustrade([h.P(s, D_BAND + 0.03, Y_FOOT + 0.02 / M), h.P(s, D_BAND + 0.03, YS0 - 0.02 / M)], zf)
        self.balustrade([h.P(s, D_AX + 0.03, Y_FOOT - 0.03 / M), h.P(s, D_BAND + 0.03, Y_FOOT - 0.03 / M)], Z3)
        self.well_edges(s)

    def flight_finishes(self, s, zf, rise):
        """Finishes of one flight (interior.flight's profile, foot at Y_FOOT,
        finished level zf): oak risers (layers.md S1: tread 30 + riser 15;
        the top one closes the upper floor's edge), plaster (PL) under the
        soffit and the flat foot, a plastered string on the open side (the
        PL the flight stands inside the band) and on the top end where it
        hangs below the upper slab into the S-pav pass. The L1 flight stands
        on the floor (finishes clipped at zf); in the campo houses its top
        runs into the L1 closing wall (clipped there below 5.72)."""
        kit, h = self.kit, self
        n, g = N_RISERS - 1, GOING
        zt = zf - FL_TREAD
        slope = rise / g
        cos_a = math.cos(math.atan(slope))
        w_v = FL_WAIST / cos_a
        s_hit, s_top = w_v / slope, n * g
        pv = PL / cos_a                                  # the soffit plaster, vertically
        z_up = zf + N_RISERS * rise                      # upper finished floor
        on_floor = zf == Z1
        y = lambda sv: yY(Y_FOOT) - sv
        da, db, dc = D_AX, D_BAND - PL, D_BAND
        # region kept: list of alternative half-plane sets (a, b, c): a*s + b*z <= c
        under = [(0.0, -1.0, -(zt - pv)), (slope, -1.0, slope * s_hit - zt + pv)]   # above the plaster's underside
        if on_floor:
            under.append((0.0, -1.0, -zf))
        if on_floor and self.campo:
            s_clip = (Y_C0 - Y_FOOT) * M
            keep = [[(1.0, 0.0, s_clip)], [(-1.0, 0.0, -s_clip), (0.0, -1.0, -C.Z_L2_SOFFIT)]]
        else:
            keep = [[]]

        def put(bm, poly, d0, d1, extra=()):
            for alt in keep:
                q = poly
                for a, b, c in list(under) + list(extra) + alt:
                    q = _clip(q, a, b, c)
                    if len(q) < 3:
                        break
                if len(q) >= 3 and abs(I.area(q)) > 1e-7:
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
        # top end below the upper slab, into the pass (not in the campo houses at L1: closing wall)
        if not (on_floor and self.campo):
            z_ceil = z_up - SLAB - 0.01                  # the pass's ceiling plaster underside
            I.prism(pl, h.rect(s, da, dc, YS0, YS0 + PL / M), zt + slope * s_top - w_v - pv, z_ceil)
        # oak risers: 15 under each tread, the top one on the last tread up to the upper floor
        rb = kit('StairRisers', TREAD_MAT)
        for k in range(n):
            I.prism(rb, I.rect(h.X(s, da), h.X(s, db), y(k * g - FL_RISER), y(k * g)),
                    zf + k * rise, zf + (k + 1) * rise - FL_TREAD)
        I.prism(rb, I.rect(h.X(s, da), h.X(s, dc), y(s_top - FL_RISER), y(s_top)), zf + n * rise, z_up)

    def well_edges(self, s):
        """Edges of the stair well: the L2 landing's edge under the L2 -> L3
        flight's foot, the L3 landing's edge and the L2 / L3 corridor edges
        (d = D_BAND) are plastered (PL, from the ceiling plaster below); the
        parquet of the open edges runs over the plaster (the corridor slabs
        and screeds stop PL short: House.slabs, corridor_floor)."""
        kit, h = self.kit, self
        pl = kit('StairPlaster', 'M_PlasterInt')
        rise2 = (Z3 - Z2) / N_RISERS
        pv2 = PL / math.cos(math.atan(rise2 / GOING))
        yb = Y_FOOT + PL / M
        I.prism(pl, h.rect(s, D_AX, D_BAND, Y_FOOT, yb), SOFF[Z1] - 0.01, Z2 - FL_TREAD - pv2)
        I.prism(pl, h.rect(s, D_AX, D_BAND, Y_FOOT, yb), SOFF[Z2] - 0.01, Z3 - PARQ)
        I.prism(kit('FloorParquet', 'M_Parquet', uv_rotate=45.0), h.rect(s, D_AX, D_BAND, Y_FOOT, yb), Z3 - PARQ, Z3)
        for zf in (Z2, Z3):
            I.prism(pl, h.rect(s, D_BAND, D_BAND + PL, Y_FOOT, YS0), zf - SLAB, zf - PARQ)

    def corridor_floor(self, s, zf):
        """F1 of an L2 / L3 corridor beside the well: the parquet to the edge,
        screed and fill PL short of it (well_edges plasters the edge)."""
        poly = self.rect(s, D_BAND, D_CORE - LIN, Y_FOOT, YS0)
        I.floor_stack(self.kit, poly, zf, FL_INT[:1])
        I.floor_stack(self.kit, self.rect(s, D_BAND + PL, D_CORE - LIN, Y_FOOT, YS0), zf - PARQ, FL_INT[1:])

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

    # ----------------------------------------------------------- entrance
    def entrance(self):
        """L1 core wall to the gallery, Y 2.018 -> 2.224 (0.34: face brick +
        insulated lining, SE 65) between the N-pav wall piers, with the two
        portoncini 0.91 x 2.07 (n31), their RC lintels and thresholds."""
        kit, S, h = self.kit, self.S, self
        z0, z1 = Z1 - 0.10, C.Z_L2_SOFFIT
        x0, x1 = self.X(1, -D_ENT), self.X(1, D_ENT)           # east -> west
        A, B = (x0, yY(Y_ENT)), (x1, yY(Y_ENT))
        L = x0 - x1
        hd = Z1 + ENT['h']
        lt0, lt1, lh = ENT['lintel']
        # positions along A -> B (t = d + D_ENT)
        doors = [(D_ENT + sg * (ENT['d'][0] + ENT['d'][1]) / 2, ENT['d'][1] - ENT['d'][0]) for sg in (-1, 1)]
        lint = [(D_ENT + sg * (lt0 + lt1) / 2, lt1 - lt0) for sg in (-1, 1)]
        # brick: door notches to the lintel underside, lintel notches above
        out = [(0.0, z0)]
        for (dc, w), (lc, lw) in zip(sorted(doors), sorted(lint)):
            out += [(dc - w / 2, z0), (dc - w / 2, hd), (lc - lw / 2, hd), (lc - lw / 2, hd + lh),
                    (lc + lw / 2, hd + lh), (lc + lw / 2, hd), (dc + w / 2, hd), (dc + w / 2, z0)]
        out += [(L, z0), (L, z1), (0.0, z1)]
        # A -> B runs west (-x): its left is south (-y), into the core
        tb = ENT_WALL[0][2] / M
        I.oprism(kit('EntranceBrick', 'M_Brick'), A, B, out, 0.0, tb * M)
        # lining on the landing side
        t = tb * M
        for elem, mat, th in BU.LINING:
            wall_layer = [(0.0, z0)]
            for dc, w in sorted(doors):
                wall_layer += [(dc - w / 2, z0), (dc - w / 2, hd), (dc + w / 2, hd), (dc + w / 2, z0)]
            wall_layer += [(L, z0), (L, z1), (0.0, z1)]
            I.oprism(kit(f'Wall{elem}', mat), A, B, wall_layer, t, t + th)
            t += th
        # the N-pav corner piers (inner faces D_ENT) stand 17.5 mm proud of the core-wall
        # linings (faces D_CORE - LIN): a board returns across each pier's end, from the core
        # lining's face to the pier face, between the parquet and the ceiling plaster (its own
        # element: it meets the board layers along edges, which the linings' cut would fuse)
        BT = BU.LINING[-1][2]
        for sg in (-1, 1):
            I.prism(kit('WallLiningReturn', 'M_PlasterInt'), self.rect(sg, D_CORE - LIN, D_ENT, YN1, YN1 + BT / M),
                    Z1, SOFF[Z1] - 0.01)
        for (lc, lw) in lint:
            I.oprism(kit('EntranceLintel', 'M_Concrete'), A, B,
                     [(lc - lw / 2, hd), (lc + lw / 2, hd), (lc + lw / 2, hd + lh), (lc - lw / 2, hd + lh)], 0.0, tb * M)
        # portoncini (joinery 'PN'), thresholds
        f = geo.Face('y', yY(Y_ENT), 1)
        for sg in (-1, 1):
            u0, u1 = sorted((self.X(sg, ENT['d'][0]), self.X(sg, ENT['d'][1])))
            zs = Z1 + ENT['sill']
            rec = geo.register(f, [(u0, zs), (u1, zs), (u1, hd), (u0, hd)], 'rect', u=(u0 + u1) / 2, z0=zs,
                               width=u1 - u0, height=hd - zs, through=None, recess=0.0)
            rec['target'], rec['type'] = S.np, 'PN'
            S.new_recs.append(rec)
            I.prism(kit('Thresholds', 'M_Concrete'), I.rect(u0, u1, yY(Y_ENT), yY(YN1)), z0, zs)
        # floor of the gallery side is the R4 deck (Seg.gallery)

    # --------------------------------------------------------------- vault
    def vault(self):
        """R2 layers under the copper skin over the core strip and the notch
        landing, R 6.00 (finished soffit R 5.69 in the model)."""
        I.vault_stack(self.kit, self.xa, VAULT_ZC, VAULT_R0, D_CORE, yY(YX0), yY(YN1), BU.ROOF_VAULT_UNDER,
                      prefix='Vault', segments=24)

    # ------------------------------------------------------------ terrace
    def terrace(self):
        """L3 notch terrace (R3, 9.15): slab, layers either side of the low
        axis divider, the terrace doors' thresholds and joinery."""
        kit, S, h = self.kit, self.S, self
        y_end = Y_CAMPO_PAR if self.campo else YS1
        S.deck(h.rect(1, -NOTCH_HALF, NOTCH_HALF, YX1, y_end), None)
        for s in (-1, 1):
            S.deck(None, h.rect(s, 0.10, NOTCH_HALF, YX1, y_end))
        # low divider on the axis to the oculus panel (n58, n65; height assumed)
        y_div = Y_CAMPO_PAR if self.campo else YJ1
        I.prism(kit('TerraceWall', 'M_Brick'), h.rect(1, -0.10, 0.10, YX1, y_div), Z3 - 0.10, 9.98)
        I.prism(kit('TerraceCoping', 'M_Concrete'), h.rect(1, -0.12, 0.12, YX1, y_div - 0.0 / M), 9.98, 10.10)
        # terrace doors in the cross wall: thresholds (landing 9.02 -> deck 9.15) and joinery
        f = geo.Face('y', yY(YX1), -1)
        hd = Z3 + BU.TERRACE_UP + TER['h']
        for s in (-1, 1):
            u0, u1 = sorted((self.X(s, TER['d'][0]), self.X(s, TER['d'][1])))
            zs = Z3 + BU.TERRACE_UP
            rec = geo.register(f, [(u0, zs), (u1, zs), (u1, hd), (u0, hd)], 'rect', u=(u0 + u1) / 2, z0=zs,
                               width=u1 - u0, height=hd - zs, through=None, recess=0.0)
            rec['target'], rec['type'] = S.core, 'DN'
            S.new_recs.append(rec)
            I.prism(kit('Thresholds', 'M_Concrete'), I.rect(u0, u1, yY(YX1), yY(YX0 - LIN / M)), Z3 - 0.10, zs)

    # ------------------------------------------------- campo: closing wall
    def closing_wall(self):
        """Campo houses, L1: the core closed at the south by a wall to Y 4.99
        between the corner piers (n31), lined inside; its inner face is on
        the exterior's corner piers (Y 4.726, drawn 4.776)."""
        kit = self.kit
        z0, z1 = Z1 - 0.10, C.Z_L2_SOFFIT
        y = Y_C0
        for elem, mat, th in reversed(BU.LINING):
            # board on the room face (Y_C0), adhesive on the brick;
            # across the corridors' lining planes, in front of the corner piers
            I.prism(kit(f'Wall{elem}', mat), self.rect(1, -D_CORE, D_CORE, y, y + th / M), z0, z1)
            y += th / M
        # brick between the corner piers (their inner faces at dE -+1.6975)
        I.prism(kit('CoreWallBrick', 'M_Brick'), self.rect(1, -D_ENT, D_ENT, y, Y_CLOSE), z0, z1)


# --------------------------------------------------------------------- walls
def wall(kit, layers, A, B, z0, top, doors=(), prefix='Wall', offset=0.0):
    """Straight layered wall on the plan line A -> B (centre line, shifted
    `offset` metres to the left), from z0 to `top` (a level, or z(x, y)
    evaluated at both ends: a sloping top along the wall); doors [(s, w,
    head)] leave openings centred s metres from A. Layers are listed from the
    left face (seen from A to B) to the right."""
    A, B = Vector(A), Vector(B)
    L = (B - A).length
    if callable(top):
        ta, tb = top(A.x, A.y), top(B.x, B.y)
    else:
        ta = tb = top
    out = [(0.0, z0)]
    for s_c, w, head in sorted(doors):
        out += [(s_c - w / 2, z0), (s_c - w / 2, head), (s_c + w / 2, head), (s_c + w / 2, z0)]
    out += [(L, z0), (L, tb), (0.0, ta)]
    Ttot = sum(t for _, _, t in layers)
    t_left = Ttot / 2 + offset
    for elem, mat, t in layers:
        if mat is not None:
            I.oprism(kit(f'{prefix}{elem}', mat), A, B, out, t_left - t, t_left)
        t_left -= t


# ===================================================================== build
def build(ctx) -> None:
    if geo.THROUGH is None:
        return
    import time
    t0 = time.time()
    _register_types()
    R = Run(ctx)
    R.prepare()
    for seg in C.segments():
        R.segment(seg)
    for block in BLOCKS:
        R.vault_skin(block)
    t1 = time.time()
    R.hollow_all()
    t2 = time.time()
    R.finish()
    print(f'[carpet north] layout {t1 - t0:.1f} s, hollow {t2 - t1:.1f} s, joinery + linings {time.time() - t2:.1f} s')
