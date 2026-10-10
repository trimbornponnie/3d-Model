"""Torri - the two columns of five 4-storey towers standing in the water
(docs/ANALYSIS.md §3 roof rule, §4 towers).

Drawings: n61 (SE 42, outer face), n7 (SE 43, inner face), n62 (SE 41,
sections A-A / K-K), n55 (published plans, sections, elevations), n63 (SE 40,
roof plan), n8 (SE 36, ground floor), n46 (SE 39, third floor), n16 (SE 24,
north end of tower 0), n64 (SE 22, chimney stacks seen beyond), n81 (model).

The east column is built tower by tower; the west column is its mirror image
in E (E' = 72 - E, i.e. x -> -x), openings and glass included. The water
stairs are built per column (west: the 4 gaps; east: the 4 gaps plus one
north of tower 0).

Per tower (skill: hard-surface workflow, one object per building element):
  SM_Tower_Body_<c><k>     brick: pavilions, outer bands, terrace parapets,
                           lean-to block, stair hall - one exact union, then
                           the openings cut by exact differences (one for all
                           windows and the slot, two more for the porch and
                           loggia behind the slot)
  SM_Tower_Glass_<c><k>    glass panes of all windows and doors
  SM_Tower_Trim_<c><k>     exposed concrete: copings, verges, head bands,
                           sills, loggia hood, the bands and parapet coping
                           inside the middle slot, chimney caps
  SM_Tower_Roof_<c><k>     clay tiles: pavilion roofs and middle lean-to
  SM_Tower_Copper_<c><k>   curved stair-hall roof, gutters
  SM_Tower_Masonry_<c><k>  brick details: patio wall and floor, chimneys
  SM_Tower_Door_<c><k>     entrance door leaf
  SM_Tower_Steps_<c><k>    entrance steps
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Matrix

from . import geo
from .common import (Openings, add_copings, add_pavilion, east_face, pavilion_section,
                     west_face, xE, yY)
from .params import (COPING_H, FLOORS, FRENCH, MODULE, ROOF_LOW, SLAB, TOWER, WIN_SMALL,
                     Z_FOUND, Z_PAVING)

# ----------------------------------------------------------------- constants
T = FLOORS[3]                                   # top floor of the towers (9.02)
PAV = TOWER['pav']                              # 4.04 m pavilions
E_OUT, E_BAND = TOWER['e_outer'], TOWER['e_band']
E_IN, E_IN_MID, E_HALL = TOWER['e_inner'], TOWER['e_inner_mid'], TOWER['e_stair_hall']
COL_E, COL_W = 'Towers_East', 'Towers_West'

BAND_H = 0.13            # concrete head bands z_f+2.35 -> 2.48 (n61, n7)
BAND_OUT = 0.02          # bands ~2 cm proud
BAND_IN = 0.05           # ... and bedded 5 cm into the brick
VERGE_IN = 0.20          # verges reach 20 cm in over the pavilion side walls (2 cm overhang outside)
GUTTER_BED = 0.01        # copper gutters bedded 1 cm into the walls they hang on
HEAD = 2.35              # window head above floor (SE 53)
L3_BAND = (11.38, 11.51)                        # band on the L3 walls (n61, n16, n62)
TERRACE_COPING = (9.84, TOWER['terrace_parapet'])   # parapet coping 9.84-9.97 (n61, n62)
TERRACE_T = TOWER['terrace_parapet_t']          # 0.30 parapet -> terrace ~1.3 x 3.4 m (n46)

# outer face of the pavilions, on the pavilion axes (n61 / SE 42)
OUT_SINGLE = (1.03, 0.95)                       # L0, L1 single window: width, sill offset
OUT_PAIR = (0.93, 0.36, 6.97, 8.37)             # L2 pair: width, pier, sill, head
FRENCH_L3 = (1.04, 9.02, 11.37)                 # L3 French door in the set-back wall E 0.78
# recessed middle wall E 0.78 (n61, n62 A-A). The L0 opening and the L1 arched
# loggia read as ONE slot 2.12 wide, jambs unbroken from the patio floor to the
# arch (n61 / SE 42 towers 0 and 2, n55 outer elevation, n81 model photo).
# Inside the slot, on a plane `set` behind the wall face, sit the L0 lintel band
# (2.35-2.48), the L1 slab edge and the loggia parapet with its coping (n61;
# n62 A-A draws the slab edge / parapet block set back ~0.15 from the face).
MID_L0 = (2.12, 2.35)                           # opening to the patio: width, head
SLOT = dict(w=2.12, set=0.15, wall=0.37)        # slot width, set-back of the inner plane, wall
SLAB_EDGE = (2.74, 2.87)                        # L1 slab edge in the slot (n61 measured)
LOGGIA = dict(w=2.12, floor=FLOORS[1], parapet=3.98, coping=0.12, spring=5.00, crown=5.44)
# open porch (L0) and loggia terrace (L1) behind the wall: back wall ~1.6 m behind
# the face (n62 A-A), terrace to ~E 1.9 (n56 L1 plan), full width between the
# pavilion side walls (n8, n56: 4.21 - 2 x 0.37); a French door in the back wall,
# whose jambs show through the slot in n61 at L0 and L1
POCKET = dict(depth=1.65, w=TOWER['mid'] * MODULE - 2 * 0.37)
HOOD = (3.02, 0.77)                             # precast hood round the arch, 5.00 -> 5.77
MID_L2 = (0.92, 0.37, 6.95, 8.37)               # two windows, pier, sill, head
HALL_WIN = (0.61, 10.46, (4.87, 6.15))          # E 2.86 wall: size, sill, centres from N end (m)
# inner face (n7 / SE 43)
STAIR_WIN = (0.61, ((4.835, 4.42), (4.835, 7.42), (7.59, 6.83), (7.59, 9.81)))
ENTRANCE = dict(w=1.25, h=2.33, recess=0.30, door=(0.92, 2.04), jamb=0.05,
                steps=3, step_w=1.55, tread=0.25)
ENTRANCE_FRAME = 0.165   # interiors: street-door frame depth behind E 4.12 (interior_towers); the steps end on it
# chimney stacks on the N / S end faces, corbelled out (n64 background, n39);
# heights, width and depth from params.TOWER['chimney'] (measured on n64, SE 22,
# Nov 1985, calibrated on the 13.12 / 11.93 lines of the same tower; spec §4):
# corbel 11.55 -> 11.90, stack 13.75 under a 0.10 cap, top 13.85. Local values:
# projection 0.25 of the 0.45 depth (n64: the facing stacks of two towers leave
# a clear gap in the 0.91 m slot), cap 0.10 (spec §4: stack top 13.75, cap
# 13.85); E position not dimensioned (assumption: E 3.80).
_CH = TOWER['chimney']
CHIMNEY = {'w': _CH['w'], 'd': _CH['d'], 'corbel_bottom': _CH['bracket'][0], 'bracket': _CH['bracket'][1],
           'top': _CH['top'], 'proj': 0.25, 'e_centre': 3.80, 'cap': 0.10}
WATER_RISER = 0.155                              # 13 risers x 0.155 (n61, n8, n63)


def _lin(c: int) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _tile_material(ctx) -> None:
    """Clay tiles ('tegole', SE 54) - not part of materials.PALETTE."""
    if 'M_RoofTile' in ctx.mats:
        return
    m = bpy.data.materials.get('M_RoofTile') or bpy.data.materials.new('M_RoofTile')
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    col = tuple(_lin(c) for c in (164, 86, 62)) + (1.0,)
    bsdf.inputs['Base Color'].default_value = col
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.8
    m.diffuse_color = col
    ctx.mats['M_RoofTile'] = m


# ------------------------------------------------------------------ helpers
def _box(bm, x0, x1, y0, y1, z0, z1):
    geo.add_box(bm, x0, x1, y0, y1, z0, z1)


def _ring(bm, outer, inner, z0, z1):
    """Closed rectangular ring (x0, x1, y0, y1 outer and inner) from z0 to z1,
    one manifold solid."""
    def rect(r, z):
        x0, x1, y0, y1 = r
        return [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    ob, ot, ib, it = rect(outer, z0), rect(outer, z1), rect(inner, z0), rect(inner, z1)
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((ob[k], ob[j], ot[j], ot[k]))       # outer side
        bm.faces.new((ib[j], ib[k], it[k], it[j]))       # inner side
        bm.faces.new((ot[k], ot[j], it[j], it[k]))       # top
        bm.faces.new((ob[j], ob[k], ib[k], ib[j]))       # bottom


def _face_box(bm, face, u0, u1, z0, z1, out, inside):
    """Box on a façade: `out` m proud of the face, `inside` m into the wall."""
    a, b = face.coord + face.out * out, face.coord - face.out * inside
    if face.axis == 'x':
        _box(bm, a, b, u0, u1, z0, z1)
    else:
        _box(bm, u0, u1, a, b, z0, z1)


def _pane(bm, face, outline, depth, t=0.02):
    """Glass sheet `t` thick whose front is `depth` m behind the face."""
    a = face.coord - face.out * depth
    b = a - face.out * t
    if face.axis == 'x':
        geo.add_prism_x(bm, outline, min(a, b), max(a, b))
    else:
        geo.add_prism_y(bm, outline, min(a, b), max(a, b))


def _rect(u, w, z0, z1):
    return [(u - w / 2, z0), (u + w / 2, z0), (u + w / 2, z1), (u - w / 2, z1)]


def _behind(face, d: float) -> geo.Face:
    """The plane parallel to `face`, `d` m behind it (same outward normal)."""
    return geo.Face(face.axis, face.coord - face.out * d, face.out)


def _lean_z(x: float) -> float:
    """Top of the middle lean-to tiles (34 %): 8.92 at E 0.78 -> 10.05 at E 2.86."""
    xa, xb = xE(E_BAND), xE(E_HALL)
    lo, hi = TOWER['mid_lean_low'], TOWER['mid_lean_high']
    return lo + (xa - x) / (xa - xb) * (hi - lo)


def _hall_z(x: float) -> float:
    """Top of the curved copper stair-hall roof: 11.40 at E 2.86 rising to the
    11.73 crown at the inner face E 4.12 (n62 A-A, eave and gutter SE 59)."""
    lo, hi = TOWER['hall_roof']
    xa, xb = xE(E_HALL), xE(E_IN_MID)
    w, h = xa - xb, hi - lo
    r = (w * w + h * h) / (2 * h)
    d = x - xb
    return hi - r + math.sqrt(max(r * r - d * d, 0.0))


def _hall_xs(xi: float, xs: float, n: int = 10) -> list[float]:
    """x stations of the curved stair-hall roof between the inner face (xi)
    and the hall wall E 2.86 (xs), shared by the brick body and the copper."""
    return [xi + (xs - xi) * j / n for j in range(n + 1)]


def _mirror_copy(obj, name: str, col) -> bpy.types.Object:
    """West-column copy: mirror x -> -x (E' = 72 - E), flip the winding."""
    me = obj.data.copy()
    me.name = name
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.transform(bm, matrix=Matrix.Scale(-1.0, 4, (1.0, 0.0, 0.0)), verts=bm.verts)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    return o


# ------------------------------------------------------------ one tower
class _Tower:
    """Tower k of the east column (Y from the north face y_first + 8k)."""

    def __init__(self, ctx, k: int):
        self.ctx, self.k = ctx, k
        self.tag = f'E{k}'
        self.YN = TOWER['y_first'] + TOWER['pitch'] * k
        self.YS = self.YN + TOWER['length']
        self.Ym0, self.Ym1 = self.YN + PAV, self.YS - PAV          # middle part
        self.Yt = (self.YN + self.YS) / 2                           # tower axis
        # (end-face Y, middle-side Y) of the north and south pavilions
        self.pavs = ((self.YN, self.YN + PAV), (self.YS, self.YS - PAV))

    def name(self, element: str) -> str:
        return f'SM_Tower_{element}_{self.tag}'

    def Y_from_north(self, m: float) -> float:
        """Plan Y of a point `m` metres south of the tower's north face."""
        return self.YN + m / MODULE

    # ---------------------------------------------------------- brick body
    def body(self) -> bpy.types.Object:
        ctx = self.ctx
        pieces = []
        for i, (Ye, Yi) in enumerate(self.pavs):
            ye, yi = yY(Ye), yY(Yi)
            s = 1.0 if ye > yi else -1.0
            # pavilion body E 0.78 -> 4.22 up to the mono-pitch roof
            pieces.append(ctx.solid(self.name(f'Tmp{i}a'), COL_E, 'M_Brick',
                                    lambda bm, Ye=Ye, Yi=Yi: add_pavilion(bm, E_BAND, E_IN, Yi, Ye, Z_FOUND, T)))
            # outer band E -0.20 -> 0.78, built to L2 (terrace floor at L3)
            xo, xb = xE(E_OUT), xE(E_BAND) - 0.03
            pieces.append(ctx.solid(self.name(f'Tmp{i}b'), COL_E, 'M_Brick',
                                    lambda bm, ye=ye, yi=yi: _box(bm, xo, xb, ye, yi, Z_FOUND, T)))
            # terrace parapet (U) round the L3 terrace, 0.30 thick, to 9.84
            t = TERRACE_T
            u = [(xo, ye), (xb, ye), (xb, ye - s * t), (xo - t, ye - s * t),
                 (xo - t, yi + s * t), (xb, yi + s * t), (xb, yi), (xo, yi)]
            pieces.append(ctx.solid(self.name(f'Tmp{i}c'), COL_E, 'M_Brick',
                                    lambda bm, u=u: geo.add_prism_z(bm, u, T - 0.04, TERRACE_COPING[0])))
        y0, y1 = yY(self.Ym1) - 0.10, yY(self.Ym0) + 0.10          # 10 cm into the pavilions
        # middle: outer rooms under the lean-to, E 0.78 -> 2.86
        xa, xh = xE(E_BAND), xE(E_HALL) - 0.05
        lean = [(xa, Z_FOUND), (xh, Z_FOUND), (xh, _lean_z(xh) - 0.05), (xa, _lean_z(xa) - 0.05)]
        pieces.append(ctx.solid(self.name('Tmp2a'), COL_E, 'M_Brick',
                                lambda bm: geo.add_prism_y(bm, lean, y0, y1)))
        # stair hall E 2.86 -> 4.12 under the curved copper roof
        xs, xi = xE(E_HALL), xE(E_IN_MID)
        arc = [(x, _hall_z(x) - 0.06) for x in _hall_xs(xi, xs)]
        hall = [(xs, Z_FOUND), (xi, Z_FOUND)] + arc
        pieces.append(ctx.solid(self.name('Tmp2b'), COL_E, 'M_Brick',
                                lambda bm: geo.add_prism_y(bm, hall, y0, y1)))
        target = pieces[0]
        geo.boolean_union(target, pieces[1:])
        target.name = target.data.name = self.name('Body')
        return target

    # ------------------------------------------------------------ openings
    def openings(self, body):
        op = Openings(self.ctx, body, glass_name=self.name('Glass'))
        sills = []                     # (face, u, w, z_sill) for the trim
        f_out, f_l3, f_in = east_face(E_OUT), east_face(E_BAND), west_face(E_IN)
        for Ye, Yi in self.pavs:
            Ya = (Ye + Yi) / 2                       # pavilion axis (2.02 m from the end)
            ua = yY(Ya)
            w, so = OUT_SINGLE
            for zf in FLOORS[:2]:                    # L0, L1 single 1.03 windows
                op.rect(f_out, Ya, 0.0, zf + so, w, HEAD - so)
                sills.append((f_out, ua, w, zf + so))
            pw, pier, s2, h2 = OUT_PAIR              # L2 pair 0.93 + 0.36 + 0.93
            for sg in (-1, 1):
                dm = sg * (pw + pier) / 2
                op.rect(f_out, Ya, dm, s2, pw, h2 - s2)
                sills.append((f_out, ua - dm, pw, s2))
            fw, f0, f1 = FRENCH_L3                   # L3 French door onto the terrace
            op.rect(f_l3, Ya, 0.0, f0 + 0.02, fw, f1 - f0 - 0.02)
            iw, isill, ihead = WIN_SMALL             # inner face 0.91 x 0.92 per floor
            for zf in FLOORS:
                op.rect(f_in, Ya, 0.0, zf + isill, iw, ihead - isill)
                sills.append((f_in, ua, iw, zf + isill))
        # recessed middle wall E 0.78, on the tower axis: one tall slot from the
        # patio floor to the arch (pass 1, `set` deep) ...
        ut = yY(self.Yt)
        L, S, P = LOGGIA, SLOT, POCKET
        rise = L['crown'] - L['spring']
        op.outline(f_l3, geo.arch_profile(ut, S['w'], L['spring'], rise, 0.0), S['set'])
        # ... pass 2: behind the set-back plane, through the rest of the wall, the
        # L0 opening (under the lintel band) and the L1 arch (above the parapet
        # coping)
        tunnels = bmesh.new()
        f_set = _behind(f_l3, S['set'] - 0.05)
        f_set.solid(tunnels, _rect(ut, S['w'], 0.0, MID_L0[1]), S['wall'] - S['set'] + 0.10, outside=0.0)
        f_set.solid(tunnels, geo.arch_profile(ut, S['w'], L['spring'], rise, L['parapet'] - L['coping']),
                    S['wall'] - S['set'] + 0.10, outside=0.0)
        # ... pass 3: the open porch (L0) and loggia (L1) rooms, under the slabs
        rooms = bmesh.new()
        for z0, z1 in ((FLOORS[0], FLOORS[1] - SLAB), (FLOORS[1], FLOORS[2] - SLAB)):
            _behind(f_l3, S['wall']).solid(rooms, _rect(ut, P['w'], z0, z1), P['depth'] - S['wall'], outside=0.0)
        # ... pass 4: the French doors in the back wall of porch and loggia
        doors = bmesh.new()
        fw, fs, fh = FRENCH
        for zf in FLOORS[:2]:
            rec = geo.opening(_behind(f_l3, P['depth']), doors, op.panes, ut, zf + fs, fw, fh - fs)
            if geo.THROUGH is not None:          # interiors: the joinery and hollowing find it by its body
                rec['target'] = body.name
        mw, mp, ms, mh = MID_L2
        for sg in (-1, 1):
            dm = sg * (mw + mp) / 2
            op.rect(f_l3, self.Yt, dm, ms, mw, mh - ms)
            sills.append((f_l3, ut - dm, mw, ms))
        # stair-hall wall E 2.86, above the lean-to
        hw, hs, hcs = HALL_WIN
        for m in hcs:
            op.rect(east_face(E_HALL), self.Y_from_north(m), 0.0, hs, hw, hw)
        # inner face of the middle part E 4.12: stair windows and entrance
        f_mid = west_face(E_IN_MID)
        sw, wins = STAIR_WIN
        for m, z in wins:
            op.rect(f_mid, self.Y_from_north(m), 0.0, z, sw, sw)
        en = ENTRANCE
        Ye_c = self.Ym0 + (en['jamb'] + en['w'] / 2) / MODULE
        op.rect(f_mid, Ye_c, 0.0, 0.0, en['w'], en['h'], recess=en['recess'], pane=False)
        ue = yY(Ye_c)
        if geo.THROUGH is None:                  # interiors: the joinery glazes the street door
            _pane(op.panes, f_mid, _rect(ue, en['w'] - 0.006, 0.003, en['h'] - 0.003), en['recess'] - 0.03)
        op.apply()
        # the slot's tunnels, rooms and doors overlap one another, so they go in
        # separate exact differences (the cutter shells of one boolean never
        # overlap), in an order where each cut reaches open air - a cavity cut
        # inside the solid would get its normals flipped by geo.cleanup()
        self._cut(body, tunnels, 2)
        self._cut(body, rooms, 3)
        self._cut(body, doors, 4)
        return sills, ue

    def _cut(self, body, bm, i: int) -> None:
        """Extra exact difference on the body; cutters stay in the hidden
        Cutters collection as <body>_Cut1, _Cut2, ..."""
        first = bpy.data.objects.get(f'{body.name}_Cut')
        if first is not None:
            first.name = f'{body.name}_Cut1'
        geo.boolean_difference(body, bm, self.ctx.cutters)
        new = bpy.data.objects.get(f'{body.name}_Cut')
        if new is not None:
            new.name = f'{body.name}_Cut{i}'

    # --------------------------------------------------------------- trim
    def trim(self, sills):
        bm = bmesh.new()
        ctx = self.ctx
        f_out, f_l3, f_in = east_face(E_OUT), east_face(E_BAND), west_face(E_IN)
        xo, xb, xi = xE(E_OUT), xE(E_BAND), xE(E_IN)
        for Ye, Yi in self.pavs:
            ye, yi = yY(Ye), yY(Yi)
            s = 1.0 if ye > yi else -1.0
            ylo, yhi = min(ye, yi) - BAND_OUT, max(ye, yi) + BAND_OUT
            # copings on the high (end) and low (middle-side) walls, SE 54. The
            # low one tops out at 11.93 (spec §3/§4; n62, n7, n61 level marks):
            # the shared rule T + 2.90 gives 11.92, so it is 13 cm high, not 12
            # (SE 54: 0.10-0.13), on the same wall top
            add_copings(bm, E_BAND, E_IN, Yi, Ye, T, low=False)
            geo.add_box(bm, xi - 0.02, xb + 0.02, yi - 0.02 * s, yi + s * 0.37,
                        T + ROOF_LOW - COPING_H, TOWER['low'])
            # verges along the sloping roof edges at E 0.78 and E 4.22
            sec = pavilion_section(Yi, Ye, Z_FOUND, T)
            (yl, zl), (yh, zh) = sec[5], sec[4]
            m = (zh - zl) / (yh - yl)
            ya, yb = yl - s * 0.05, yh + s * 0.05
            za, zb = zl + m * (ya - yl), zl + m * (yb - yl)
            verge = [(ya, za - 0.01), (yb, zb - 0.01), (yb, zb + 0.11), (ya, za + 0.11)]
            # (the tile slab stops at their inner faces - see roofs())
            geo.add_prism_x(bm, verge, xb - VERGE_IN, xb + 0.02)
            geo.add_prism_x(bm, verge, xi - 0.02, xi + VERGE_IN)
            # terrace parapet coping (U), 2 cm overhang
            t, o = TERRACE_T, 0.02
            xc = xb - 0.02
            u = [(xo + o, ye + s * o), (xc, ye + s * o), (xc, ye - s * (t + o)), (xo - t - o, ye - s * (t + o)),
                 (xo - t - o, yi + s * (t + o)), (xc, yi + s * (t + o)), (xc, yi - s * o), (xo + o, yi - s * o)]
            geo.add_prism_z(bm, u, *TERRACE_COPING)
            # head bands z_f+2.35 -> 2.48 on the outer (L0-L2) and inner (L0-L2) faces
            for zf in FLOORS[:3]:
                z0 = zf + HEAD + 0.002
                _face_box(bm, f_out, ylo, yhi, z0, z0 + BAND_H - 0.002, BAND_OUT, BAND_IN)
                _face_box(bm, f_in, ylo, yhi, z0, z0 + BAND_H - 0.002, BAND_OUT, BAND_IN)
            # L3 band 11.38 -> 11.51 round the L3 walls of the pavilion: one closed
            # ring (2 cm proud, 5 cm bedded), so the corners have no overlapping faces
            z0, z1 = L3_BAND
            _ring(bm, (xi - BAND_OUT, xb + BAND_OUT, ylo, yhi),
                  (xi + BAND_IN, xb - BAND_IN, ylo + BAND_OUT + BAND_IN, yhi - BAND_OUT - BAND_IN), z0, z1)
            # chimney cap
            ch = CHIMNEY
            xc0 = xE(ch['e_centre'])
            emb = ch['d'] - ch['proj']
            _box(bm, xc0 - ch['w'] / 2 - 0.05, xc0 + ch['w'] / 2 + 0.05,
                 ye - s * (emb + 0.05), ye + s * (ch['proj'] + 0.05), ch['top'] - ch['cap'], ch['top'])
        # window sills (2 cm above the reveal floor, 4 cm proud)
        for face, u, w, z in sills:
            _face_box(bm, face, u - w / 2 - 0.05, u + w / 2 + 0.05, z - 0.05, z + 0.01, 0.04, 0.115)
        # precast hood 3.02 x 0.77 round the loggia arch, on the wall E 0.78
        ut = yY(self.Yt)
        L, S = LOGGIA, SLOT
        hw, hh = HOOD
        arch = geo.arch_profile(ut, L['w'], L['spring'], L['crown'] - L['spring'], L['floor'])
        arc = arch[3:-1]            # arc points between the springs
        top = L['spring'] + hh
        outline = ([(ut + hw / 2, L['spring']), (ut + L['w'] / 2, L['spring'])] + arc +
                   [(ut - L['w'] / 2, L['spring']), (ut - hw / 2, L['spring']), (ut - hw / 2, top), (ut + hw / 2, top)])
        # back face shared exactly with the wall face (bedding it into the wall
        # would run its intrados into the slot's arch soffit, coplanar)
        geo.add_prism_x(bm, outline, xb, xb + 0.04)
        # inside the slot, on the set-back plane (1 cm into the jambs): L0 lintel
        # band 2.35 -> 2.48, L1 slab edge, parapet coping to 3.98 (n61, n62 A-A)
        f_set = _behind(f_l3, S['set'])
        u0, u1 = ut - S['w'] / 2 - 0.01, ut + S['w'] / 2 + 0.01
        z0 = MID_L0[1] + 0.002
        _face_box(bm, f_set, u0, u1, z0, z0 + BAND_H - 0.002, BAND_OUT, BAND_IN)
        _face_box(bm, f_set, u0, u1, *SLAB_EDGE, BAND_OUT, BAND_IN)
        _face_box(bm, f_set, u0, u1, L['parapet'] - L['coping'], L['parapet'], 0.02, S['wall'] - S['set'] + 0.02)
        # L2 head band 8.37 -> 8.50 across the middle wall, between the outer
        # bands of the two pavilions (n61 towers 0 and 2, n55 outer elevation)
        z0 = FLOORS[2] + HEAD + 0.002
        _face_box(bm, f_l3, yY(self.Ym1) - 0.05, yY(self.Ym0) + 0.05, z0, z0 + BAND_H - 0.002, BAND_OUT, BAND_IN)
        # patio wall coping (top 1.26)
        e0, e1, ztop = TOWER['patio_wall']
        # (ends shared exactly with the pavilions' outer bands, like the wall under it)
        _box(bm, xE(e1) - 0.02, xE(e0) + 0.02, yY(self.Ym1), yY(self.Ym0), ztop - 0.12, ztop)
        return geo.object_from_bmesh(bm, self.name('Trim'), ctx.col(COL_E), ctx.mats['M_Concrete'])

    # ------------------------------------------------------- tiled roofs
    def roofs(self):
        bm = bmesh.new()
        xb, xi = xE(E_BAND), xE(E_IN)
        for Ye, Yi in self.pavs:
            sec = pavilion_section(Yi, Ye, Z_FOUND, T)
            (yl, zl), (yh, zh) = sec[5], sec[4]
            # between the verges (trim): the slab ends on their inner faces
            # instead of running on under them with its soffit ~1 cm over theirs
            geo.add_prism_x(bm, [(yl, zl), (yh, zh), (yh, zh + 0.05), (yl, zl + 0.05)],
                            xi + VERGE_IN, xb - VERGE_IN)
        # lean-to over the outer rooms of the middle part
        x1, x2 = xE(E_BAND) + 0.06, xE(E_HALL)
        prof = [(x1, _lean_z(x1) - 0.05), (x2, _lean_z(x2) - 0.05), (x2, _lean_z(x2)), (x1, _lean_z(x1))]
        geo.add_prism_y(bm, prof, yY(self.Ym1), yY(self.Ym0))
        return geo.object_from_bmesh(bm, self.name('Roof'), self.ctx.col(COL_E), self.ctx.mats['M_RoofTile'])

    # ---------------------------------------------------- copper, gutters
    def copper(self):
        bm = bmesh.new()
        y0, y1 = yY(self.Ym1), yY(self.Ym0)
        xs, xi = xE(E_HALL), xE(E_IN_MID)
        xa, xz = xs + 0.10, xi - 0.03
        # same stations as the body's hall top between the walls, so the
        # shell's soffit lies exactly on it (different chords left slits <1 mm)
        xs_ = [xz] + _hall_xs(xi, xs) + [xa]
        shell = [(x, _hall_z(x)) for x in xs_] + [(x, _hall_z(x) - 0.06) for x in reversed(xs_)]
        geo.add_prism_y(bm, shell, y0 - 0.02, y1 + 0.02)
        # eave gutter of the stair hall (SE 59) and of the lean-to, bedded 1 cm
        # into the wall they hang on and into the pavilion walls at their ends
        b = GUTTER_BED
        _box(bm, xs - b, xs + 0.17, y0 - b, y1 + b, 11.14, _hall_z(xa) - 0.09)
        xl = xE(E_BAND)
        _box(bm, xl - b, xl + 0.17, y0 - b, y1 + b, 8.70, _lean_z(xl + 0.06) - 0.07)
        # copper box gutters at the low end of the pavilion roofs, bedded 2 cm
        # into the low wall (the tile slab ends on its inner face: 1 cm would
        # leave the two end faces ~1 cm apart, near-coplanar)
        for Ye, Yi in self.pavs:
            sec = pavilion_section(Yi, Ye, Z_FOUND, T)
            yl, zl = sec[5]
            s = 1.0 if yY(Ye) > yY(Yi) else -1.0
            # (ends 2 cm inside the side faces, under the verges)
            _box(bm, xE(E_IN) + 2 * b, xE(E_BAND) - 2 * b, yl - s * 2 * b, yl + s * 0.24, zl - 0.02, zl + 0.07)
        return geo.object_from_bmesh(bm, self.name('Copper'), self.ctx.col(COL_E), self.ctx.mats['M_Copper'])

    # ------------------------------------------------ brick details
    def masonry(self):
        bm = bmesh.new()
        # patio: low front wall E -0.12 -> 0.04 (top 1.26, coping 0.12) on a
        # floor at 0.00 that closes the void, both standing in the water
        # (the floor stops at the wall face: in the slot the body's own floor
        # continues it at 0.00 without overlapping faces). The loggia parapet is
        # part of the body, left standing behind the slot's set-back plane.
        e0, e1, ztop = TOWER['patio_wall']
        xa, xw, xb = xE(e0), xE(e1), xE(E_BAND)
        prof = [(xa, Z_FOUND), (xb, Z_FOUND), (xb, 0.0), (xw, 0.0), (xw, ztop - 0.12), (xa, ztop - 0.12)]
        geo.add_prism_y(bm, prof, yY(self.Ym1), yY(self.Ym0))
        # corbelled chimney stacks on the end faces
        ch = CHIMNEY
        xc = xE(ch['e_centre'])
        emb = ch['d'] - ch['proj']
        for Ye, Yi in self.pavs:
            ye = yY(Ye)
            s = 1.0 if ye > yY(Yi) else -1.0
            prof = [(ye - s * emb, ch['corbel_bottom']), (ye, ch['corbel_bottom']),
                    (ye + s * ch['proj'], ch['bracket']), (ye + s * ch['proj'], ch['top'] - ch['cap']),
                    (ye - s * emb, ch['top'] - ch['cap'])]
            geo.add_prism_x(bm, prof, xc - ch['w'] / 2, xc + ch['w'] / 2)
        return geo.object_from_bmesh(bm, self.name('Masonry'), self.ctx.col(COL_E), self.ctx.mats['M_Brick'])

    # ------------------------------------------------------ entrance
    def entrance(self, ue):
        en = ENTRANCE
        f = west_face(E_IN_MID)
        dw, dh = en['door']
        door = None
        if geo.THROUGH is None:                  # interiors: the joinery builds the street door
            bm = bmesh.new()
            a, b = f.coord - f.out * (en['recess'] - 0.07), f.coord - f.out * (en['recess'] - 0.035)
            _box(bm, a, b, ue - dw / 2, ue + dw / 2, 0.012, dh)
            door = geo.object_from_bmesh(bm, self.name('Door'), self.ctx.col(COL_E), self.ctx.mats['M_Frame'])
        # three steps from the calle (-0.45) to the threshold, 1.55 wide
        bm = bmesh.new()
        xf, tr = f.coord, en['tread']
        r = (0.0 - Z_PAVING) / en['steps']
        x_in = xf + (en['recess'] - 0.07 if geo.THROUGH is None else ENTRANCE_FRAME)
        prof = [(x_in, Z_PAVING - 0.05)]
        prof.append((xf - en['steps'] * tr, Z_PAVING - 0.05))
        for i in range(en['steps']):
            x = xf - (en['steps'] - i) * tr
            z = Z_PAVING + (i + 1) * r + (0.01 if i == en['steps'] - 1 else 0.0)
            prof += [(x, z), (x + tr, z)] if i < en['steps'] - 1 else [(x, z)]
        prof.append((x_in, Z_PAVING + en['steps'] * r + 0.01))
        y_n = yY(self.Ym0)              # against the side of the north pavilion, shared face
        geo.add_prism_y(bm, prof, y_n - en['step_w'], y_n)
        steps = geo.object_from_bmesh(bm, self.name('Steps'), self.ctx.col(COL_E), self.ctx.mats['M_Paving'])
        return door, steps

    def build(self):
        body = self.body()
        sills, ue = self.openings(body)
        objs = [body, bpy.data.objects.get(self.name('Glass')), self.trim(sills), self.roofs(),
                self.copper(), self.masonry()]
        objs += list(self.entrance(ue))
        return [o for o in objs if o is not None]   # (interiors: no glass panes, no door leaf)


# ------------------------------------------------------------ water stairs
def _water_stairs(ctx, side: str):
    """Flights in the 0.91 m gaps: flat at -0.45 from E 4.22 to 2.45, then 13
    risers x 0.155 down to -2.45 at E 0.25 (n61, n8, n63). East column also
    north of tower 0. Built in east coordinates, mirrored for the west."""
    ws = TOWER['water_stair']
    n = ws['risers']
    run = (ws['e_top'] - ws['e_bottom']) / (n - 1)          # 0.3025 m treads
    sx = 1.0 if side == 'E' else -1.0
    pts = [(E_IN, Z_PAVING), (ws['e_top'], Z_PAVING)]
    z = Z_PAVING
    for i in range(n):
        e = ws['e_top'] - i * run
        z -= WATER_RISER
        pts.append((e, z))
        e_next = e - run if i < n - 1 else ws['e_bottom'] - 0.30 / MODULE
        pts.append((e_next, z))
    pts.append((pts[-1][0], Z_FOUND))
    pts.append((E_IN, Z_FOUND))
    prof = [(sx * xE(e), zz) for e, zz in pts]
    gaps = []
    for k in range(TOWER['count'] - 1):
        y_s = TOWER['y_first'] + TOWER['pitch'] * k + TOWER['length']
        gaps.append((y_s, TOWER['y_first'] + TOWER['pitch'] * (k + 1)))
    if side == 'E':
        gaps.insert(0, (TOWER['y_first'] - TOWER['gap'], TOWER['y_first']))
    bm = bmesh.new()
    for Y0, Y1 in gaps:
        # full gap width: the end faces are shared exactly with the tower end
        # walls (north of tower 0: with the land plate's quay face at Y -4.7765).
        # Not bedded in: the flat top at -0.45 and the E 4.22 end would then lie
        # in the planes of the plate's top / the towers' inner faces.
        geo.add_prism_y(bm, prof, yY(Y1), yY(Y0))
    col = COL_E if side == 'E' else COL_W
    return geo.object_from_bmesh(bm, f'SM_Tower_WaterStairs_{side}', ctx.col(col), ctx.mats['M_Paving'])


# --------------------------------------------------------------------- build
def build(ctx):
    _tile_material(ctx)
    col_w = ctx.col(COL_W)
    for k in range(TOWER['count']):
        for obj in _Tower(ctx, k).build():
            _mirror_copy(obj, obj.name.replace(f'_E{k}', f'_W{k}'), col_w)
    _water_stairs(ctx, 'E')
    _water_stairs(ctx, 'W')
