"""Site context of Gino Valle's IACP housing on the Giudecca (docs/ANALYSIS.md
section 3 levels, section 7 site). Approximate context, exact where it meets the
buildings.

Drawings: n2 / n32 (site / roof plan), n36 (site axonometric), n71
(axonometric with the square grid and the mooring poles), n81 (study model from
the east: walled north garden with ~16 trees, arched footbridge at the
south-east), n52 (urban profiles: the footbridge arch), n53 (L0 plan: garden
walls and gates), n11 / SE 8 (south-row gardens), n20 / SE 63 (levels -0.45 /
-0.10, garden wall to +1.22, precast steps 35/13 at the garden entrances).

Objects (collection COL_Site; skill: one object per element, closed solids,
quads wherever the shape allows, real metric scale):
  SM_Site_Water              thin water slab at -2.50 ("medio mare")
  SM_Site_Plate              land plate between and north of the tower
                             columns: paving top at -0.45, flush Istrian-stone
                             coping strip 0.30 m along the water edges, brick
                             quay walls down to -2.60; notched for the tower
                             water stairs, under the towers only below -0.45
  SM_Site_Banks              far banks: S. Biagio east bank, south block,
                             north land (Molino Stucky side), Sacca Fisola
  SM_Site_SquareGrid         Istrian-stone grid lines of the open square
  SM_Site_GardenLawn_South / SM_Site_GardenWalls_South /
  SM_Site_GardenSteps_South  south-row gardens, walls to +1.22, gates + steps
  SM_Site_GardenLawn_North / SM_Site_GardenWalls_North /
  SM_Site_GardenCoping_North / SM_Site_GardenSteps_North
                             walled garden north of the complex
  SM_Site_TreeTrunks / SM_Site_TreeCrowns   ~16 low-poly trees
  SM_Site_Footbridge / SM_Site_FootbridgeParapet  arched footbridge over the
                             south rio, solid parapets
  SM_Site_MooringPoles       wooden poles ("pali") at the water stairs and the square

Rectilinear solids are built by _grid_solid(): the union of axis-aligned
rectangles extruded on the grid of all their edges, so every face is a quad,
neighbouring cells share their edges exactly and the shell is closed without
any boolean (skill: "plan cuts to avoid cleanup"). No openings are cut in this
part, so no cutters are needed. Lawns fill only the space between the inner
faces of their walls, and the water stops short of the bank outlines, so no
two faces of this part lie in one plane facing the same way (no z-fighting).
"""
from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import geo
from .common import xE, yY
from .params import (BLOCKS, MODULE, SITE, TOWER, Z_COURT, Z_FOUND, Z_GARDEN_WALL,
                     Z_PAVING, Z_WATER)

M = MODULE
COL = 'Site'

# ------------------------------------------------------------ local constants
Z_BASE = Z_PAVING - 0.05          # bases of walls / lawns: 5 cm into the paving (task rule)
WATER_T = 0.05                    # thickness of the water slab (thin closed solid)
WATER_INSET = 0.02                # m, the water stops this far inside the outer bank faces at the
                                  # model boundary (E -30, Y -40, Y 80): no coplanar faces
QUAY_BAND = 0.30                  # m, Istrian-stone coping strip along the quay edges (task, n71)
NW_LAND = True                    # land north of the north-west tower: n2 / n53 show the boundary on
                                  # its north face; spec 4 has a water stair only north of the NE tower
SACCA_E1 = 125.0                  # western limit of the Sacca Fisola bank (beyond the water slab)
TUCK = 0.02                       # m, plate strips under the towers stop this far inside the
                                  # tower end walls, so no plate face is coplanar with a tower face

# open square: stone grid (n71, n36: ~1 module); lines on the carpet's half-module
# axes along E (they continue the garden cross walls 42.5 + 3k) and on whole Y
GRID_W = 0.16                     # m, width of the stone lines (approx., n71)
GRID_Z = (Z_PAVING - 0.02, Z_PAVING + 0.002)   # lines 2 mm proud of the paving

# south-row gardens (SE 63, n11, n53)
GW_T = 0.30                       # m, garden wall thickness (spec 7)
GATE_W = 1.10                     # m, gate clear width (n53: pairs of gates either side of the
                                  # house-axis cross walls of the east block; measured ~1.1)
STEP_TREAD = 0.35                 # SE 63 "gradini in c.a. prefabbr. 35/13"
STEP_N = 3                        # risers from the paving (-0.45) to the garden (-0.10)

# north garden (spec 7, n2, n81); lawn at Z_COURT (spec 3: gardens -0.10)
NG_WALL_T = 0.30                  # m, wall thickness (assumption, as the garden walls)
NG_GATE = (42.0, 2.40)            # gate in the south wall on the slot axis E 42.0, width m (assumption),
                                  # with a threshold and steps down to the apron like the south gates
NG_COPING = (0.03, 0.09)          # stone coping: overhang, height (m)
TREES = dict(count=16, seed=1985, min_dist=8.0, margin=3.0,
             trunk=(3.2, 4.4), crown_r=(3.3, 4.6), r_base=0.26, r_top=0.14)

# footbridge over the south rio (n2, n71, n81, n52). n52 profiles 1 and 2, scaled on the tower
# level lines of the same sheet (coping 13.12, head bands 2.35 / 5.36 / 8.37 / 11.38): the arch
# springs from vertical abutments at about quay level and spans the whole rio, intrados crown
# +1.5..+2.0, top line (parapet) +2.6..+3.15, flat middle; n71 / n81: solid parapets ending in
# blocks at the feet. 17 risers x 0.15 from the paving to the crown landing at +2.10.
FB = dict(risers=17, tread=0.30, landing=2.80, deck=2.10, crown=1.75, spring=-0.40,
          abut_proud=0.03, parapet_t=0.24, parapet_h=0.90, end_block=0.45)

# mooring poles ("pali", n71): offset from the quay / tower faces, radius, top range
POLES = dict(off=1.8, r=0.12, top=(1.0, 1.7), bottom=Z_FOUND - 0.10, seed=7,
             bricola_r=0.34)              # m, base radius of a triple; the tops meet
# the three bricole off the square's quay, measured along the quay line between the tower
# columns (parallel projection keeps ratios): n36 ~ E 55.0-55.8 / 48.3-48.8 / 41.6-41.7;
# n71 shows two of them, at ~ E 55 and ~ 45. None west of ~ E 56.
BRICOLE_E = (55.5, 48.5, 41.7)


# ------------------------------------------------------------------ helpers
def _lin(c: int) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _material(ctx, name: str, rgb, rough: float, metal: float = 0.0):
    """Local material (not in materials.PALETTE), created once."""
    if name in ctx.mats:
        return ctx.mats[name]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    col = tuple(_lin(c) for c in rgb) + (1.0,)
    bsdf.inputs['Base Color'].default_value = col
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    m.diffuse_color = col
    ctx.mats[name] = m
    return m


def _local_materials(ctx) -> None:
    _material(ctx, 'M_Stone', (222, 216, 202), 0.7)      # Istrian stone copings, steps, grid lines
    _material(ctx, 'M_Foliage', (74, 98, 50), 0.95)
    _material(ctx, 'M_Bark', (86, 70, 56), 0.9)
    _material(ctx, 'M_Wood', (112, 94, 74), 0.85)        # weathered oak mooring poles


def _wr(E0: float, E1: float, Y0: float, Y1: float):
    """Drawing rectangle (modules) -> world rectangle (x0, x1, y0, y1), sorted."""
    xa, xb = sorted((xE(E0), xE(E1)))
    ya, yb = sorted((yY(Y0), yY(Y1)))
    return (xa, xb, ya, yb)


def _inside(r, x: float, y: float) -> bool:
    return r[0] < x < r[1] and r[2] < y < r[3]


def _grid_solid(bm, rects, zs, splits=(), top_mat=None, side_mat: int = 0, bot_mat: int = 0) -> None:
    """Union of world rectangles (x0, x1, y0, y1) extruded through the ascending z
    levels `zs`. Built on the grid of all rectangle edges (plus `splits`, world
    rectangles whose edges only subdivide the top, e.g. for a material band), so
    the result is one closed, consistently oriented all-quad shell per connected
    region. top_mat(x, y) -> material index of the top cell at (x, y)."""
    q = lambda v: round(v, 6)
    xs = sorted({q(v) for r in rects for v in r[:2]})
    ys = sorted({q(v) for r in rects for v in r[2:]})
    lo_x, hi_x, lo_y, hi_y = xs[0], xs[-1], ys[0], ys[-1]
    xs = sorted(set(xs) | {q(v) for r in splits for v in r[:2] if lo_x < q(v) < hi_x})
    ys = sorted(set(ys) | {q(v) for r in splits for v in r[2:] if lo_y < q(v) < hi_y})
    nx, ny = len(xs) - 1, len(ys) - 1
    cov = [[any(_inside(r, (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2) for r in rects)
            for j in range(ny)] for i in range(nx)]
    for i in range(nx - 1):
        for j in range(ny - 1):
            a, b, c, d = cov[i][j], cov[i + 1][j], cov[i][j + 1], cov[i + 1][j + 1]
            if (a and d and not b and not c) or (b and c and not a and not d):
                raise ValueError(f'_grid_solid: cells touch only at a corner near ({xs[i + 1]}, {ys[j + 1]})')
    verts = {}

    def V(i, j, k):
        key = (i, j, k)
        if key not in verts:
            verts[key] = bm.verts.new((xs[i], ys[j], zs[k]))
        return verts[key]

    def C(i, j):
        return 0 <= i < nx and 0 <= j < ny and cov[i][j]

    kt = len(zs) - 1
    for i in range(nx):
        for j in range(ny):
            if not cov[i][j]:
                continue
            f = bm.faces.new((V(i, j, kt), V(i + 1, j, kt), V(i + 1, j + 1, kt), V(i, j + 1, kt)))
            f.material_index = top_mat((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2) if top_mat else 0
            f = bm.faces.new((V(i, j, 0), V(i, j + 1, 0), V(i + 1, j + 1, 0), V(i + 1, j, 0)))
            f.material_index = bot_mat
            for di, dj, e0, e1 in ((-1, 0, (i, j + 1), (i, j)), (1, 0, (i + 1, j), (i + 1, j + 1)),
                                   (0, -1, (i, j), (i + 1, j)), (0, 1, (i + 1, j + 1), (i, j + 1))):
                if C(i + di, j + dj):
                    continue
                for k in range(kt):
                    f = bm.faces.new((V(*e0, k), V(*e1, k), V(*e1, k + 1), V(*e0, k + 1)))
                    f.material_index = side_mat


def _object(ctx, name: str, bm, mats) -> bpy.types.Object:
    """bmesh -> object in COL_Site with the material slots `mats` (in index order)."""
    obj = geo.object_from_bmesh(bm, name, ctx.col(COL), ctx.mats[mats[0]])
    for m in mats[1:]:
        obj.data.materials.append(ctx.mats[m])
    return obj


def _band_fn(bands, inside_idx: int, outside_idx: int = 0):
    return lambda x, y: inside_idx if any(_inside(b, x, y) for b in bands) else outside_idx


def _intervals_minus(a: float, b: float, cuts):
    """[a, b] minus the (sorted, disjoint) intervals `cuts`."""
    out, cur = [], a
    for c0, c1 in sorted(cuts):
        if c0 > cur:
            out.append((cur, c0))
        cur = max(cur, c1)
    if cur < b:
        out.append((cur, b))
    return out


def _W(E: float) -> float:
    """West column mirror of an east-column E (spec 4: E' = 72 - E)."""
    return 2.0 * TOWER['mirror_axis'] - E


def _tower_spans():
    t = TOWER
    return [(t['y_first'] + t['pitch'] * k, t['y_first'] + t['pitch'] * k + t['length'])
            for k in range(t['count'])]


# --------------------------------------------------------------- water, land
def _water(ctx) -> None:
    """Water slab E -30 -> 110, Y -40 -> 80 (task). Its outer faces at E -30,
    Y -40 and Y 80 would lie in the planes of the bank slabs' outer faces, so it
    stops WATER_INSET short of them; its west end E 110 lies inside the Sacca
    Fisola bank (E 108 -> 125)."""
    (e0, e1), (y0, y1) = SITE['water_e'], SITE['water_y']
    d = WATER_INSET / M
    bm = bmesh.new()
    geo.add_box(bm, *_wr(e0 + d, e1, y0 + d, y1 - d), Z_WATER - WATER_T, Z_WATER)
    _object(ctx, 'SM_Site_Water', bm, ['M_Water'])


def _plate(ctx) -> None:
    """Land plate (spec 7, task): north of the towers E -0.20 -> 72.20 for
    Y -27.0 -> -4.7765 (north end of the NE water stair); between the tower
    columns from the stair tops E 2.45 / 69.55 to Y 35.25 - but notched back to
    the tower inner faces E 4.22 / 67.78 in the 0.91 m gaps, where the water
    stairs (towers part) start flush at -0.45; in E 2.45 -> 4.22 it stays
    2 cm inside the tower spans so it never shows on (or z-fights with) the
    tower end faces above the water."""
    t = TOWER
    e0, e1 = SITE['land_e']
    y0, y1 = SITE['land_y']
    e_st, e_in = t['water_stair']['e_top'], t['e_inner']
    y_n = t['y_first'] - t['gap']                       # -4.7765
    rects = [(e0, e1, y0, y_n), (e_in, _W(e_in), y_n, y1)]
    ins = TUCK / M
    for k, (ya, yb) in enumerate(_tower_spans()):
        # strips under the towers end TUCK inside the tower end walls (no coplanar faces)
        ya_w = ya if (k == 0 and NW_LAND) else ya + ins
        rects += [(e_st, e_in, ya + ins, yb - ins), (_W(e_in), _W(e_st), ya_w, yb - ins)]
    if NW_LAND:
        rects.append((_W(e_in), e1, y_n, t['y_first']))
    b = QUAY_BAND / M
    bands = [(e0, e0 + b, y0, y_n),                       # rio di S. Biagio quay
             (e0, e_st, y_n - b, y_n),                    # north side of the NE water stair
             (e1 - b, e1, y0, t['y_first'] if NW_LAND else y_n),   # Canale dei Lavraneri quay
             (e_in, _W(e_in), y1 - b, y1)]                # south rio quay
    wr = [_wr(*r) for r in rects]
    wb = [_wr(*r) for r in bands]
    bm = bmesh.new()
    _grid_solid(bm, wr, (Z_FOUND, Z_PAVING), splits=wb, top_mat=_band_fn(wb, 1), side_mat=2)
    _object(ctx, 'SM_Site_Plate', bm, ['M_Paving', 'M_Stone', 'M_Brick'])


def _banks(ctx) -> None:
    """Far banks as simple land slabs (spec 7, n2 / n32): S. Biagio east bank
    (E < -7), south block across the rio (Y > 40.5), the land north of the
    plate (n2: continues to the Molino Stucky) and the Sacca Fisola shore (E > 108)."""
    (we0, we1), (wy0, wy1) = SITE['water_e'], SITE['water_y']
    e0, e1 = SITE['land_e']
    y0 = SITE['land_y'][0]
    ef, ys, ec = SITE['rio_east_far'], SITE['rio_south_far'], SITE['canal_west_far']
    b = QUAY_BAND / M
    parts = [
        ((we0, ef, wy0, wy1), [(ef - b, ef, wy0, wy1)]),
        ((e0, e1, ys, wy1), [(e0, e1, ys, ys + b), (e0, e0 + b, ys, wy1), (e1 - b, e1, ys, wy1)]),
        ((e0, e1, wy0, y0), [(e0, e0 + b, wy0, y0), (e1 - b, e1, wy0, y0)]),
        ((ec, SACCA_E1, wy0, wy1), [(ec, ec + b, wy0, wy1)]),
    ]
    bm = bmesh.new()
    for rect, bands in parts:
        wb = [_wr(*r) for r in bands]
        _grid_solid(bm, [_wr(*rect)], (Z_FOUND, Z_PAVING), splits=wb, top_mat=_band_fn(wb, 1), side_mat=2)
    _object(ctx, 'SM_Site_Banks', bm, ['M_Ground', 'M_Stone', 'M_Brick'])


def _square_grid(ctx) -> None:
    """Stone grid of the open square E 39.72 -> 67.78, Y 25.0 -> 35.25 (spec 7,
    n71). The square's north-east corner E < 41.72, Y < 27.0 belongs to the
    east-block gardens; lines stop at the quay coping strip."""
    (s_e0, s_e1), (s_y0, s_y1) = SITE['square_e'], SITE['square_y']
    (_, g_e1), (_, g_y1) = SITE['gardens_s']['east']
    w = GRID_W / M / 2
    y_end = s_y1 - QUAY_BAND / M
    rects = []
    E = math.ceil(s_e0 + w - 0.5) + 0.5               # first half-module axis inside the square
    while E < s_e1 - w:
        rects.append((E - w, E + w, g_y1 if E < g_e1 else s_y0, y_end))
        E += 1.0
    for Y in range(math.ceil(s_y0 + w), math.floor(y_end - w) + 1):
        rects.append((s_e0 if Y - w > g_y1 else g_e1, s_e1, Y - w, Y + w))
    bm = bmesh.new()
    _grid_solid(bm, [_wr(*r) for r in rects], GRID_Z)
    _object(ctx, 'SM_Site_SquareGrid', bm, ['M_Stone'])


# ------------------------------------------------------------------ gardens
def _gardens_south(ctx) -> None:
    """South-row gardens (spec 7, SE 63, n11, n53): lawn at -0.10, front, end and
    cross walls 0.30 thick to +1.22, cross walls on the house axes and party
    walls (E 5.5 + 3k / 42.5 + 3k). East block: pairs of gates either side of
    each house-axis cross wall (n53), with precast steps down to the passage.
    The lawn is one slab per compartment, between the inner faces of the walls,
    so the walls' outer faces are plain brick down to the paving."""
    t = GW_T / M
    gw = GATE_W / M
    lawn, walls, steps = bmesh.new(), bmesh.new(), bmesh.new()
    rise = (Z_COURT - Z_PAVING) / STEP_N
    for name, ((e0, e1), (y0, y1)) in SITE['gardens_s'].items():
        blk = BLOCKS[name]
        cross = sorted(blk['axes'] + blk['party'])
        rects = [(e0, e0 + t, y0, y1), (e1 - t, e1, y0, y1)]
        rects += [(E - t / 2, E + t / 2, y0, y1) for E in cross]
        gates = []
        if name == 'east':
            for E in blk['axes']:
                gates += [(E - t / 2 - gw, E - t / 2), (E + t / 2, E + t / 2 + gw)]
        rects += [(a, b, y1 - t, y1) for a, b in _intervals_minus(e0, e1, gates)]
        _grid_solid(walls, [_wr(*r) for r in rects], (Z_BASE, Z_GARDEN_WALL))
        inner = [e0 + t] + [v for E in cross for v in (E - t / 2, E + t / 2)] + [e1 - t]
        comps = [(inner[k], inner[k + 1], y0, y1 - t) for k in range(0, len(inner), 2)]
        _grid_solid(lawn, [_wr(*r) for r in comps], (Z_BASE, Z_COURT))
        # threshold in the wall gap + steps outside (profile in world y, z; + y = north)
        prof = _step_profile(yY(y1 - t), yY(y1), rise)
        for a, b in gates:
            xa, xb = sorted((xE(a), xE(b)))
            geo.add_prism_x(steps, prof, xa, xb)
    _object(ctx, 'SM_Site_GardenLawn_South', lawn, ['M_Grass'])
    _object(ctx, 'SM_Site_GardenWalls_South', walls, ['M_Brick'])
    _object(ctx, 'SM_Site_GardenSteps_South', steps, ['M_Concrete'])


def _step_profile(y_in: float, y_out: float, rise: float):
    """(y, z) outline of a gate threshold (in the wall, flush with the lawn) and
    STEP_N - 1 steps outside it, descending southward (-y) to the paving."""
    pts = [(y_in, Z_BASE), (y_in, Z_COURT), (y_out, Z_COURT)]
    y = y_out
    for k in range(1, STEP_N):
        z = Z_COURT - k * rise
        pts.append((y, z))
        y -= STEP_TREAD
        pts.append((y, z))
    pts.append((y, Z_BASE))
    return pts


def _garden_north(ctx) -> None:
    """Walled garden north of the complex E 11 -> 55, Y -26.5 -> -4.7 (spec 7,
    n2, n81): lawn at Z_COURT (spec 3: gardens -0.10) between the inner faces
    of the walls, 2.0 m brick walls with a stone coping, a gate to the north
    apron on the slot axis with a threshold and steps down to the paving."""
    (e0, e1), (y0, y1) = SITE['garden_e'], SITE['garden_y']
    t = NG_WALL_T / M
    ge, gw = NG_GATE[0], NG_GATE[1] / M
    gate = (ge - gw / 2, ge + gw / 2)
    rects = [(e0, e1, y0, y0 + t), (e0, e0 + t, y0, y1), (e1 - t, e1, y0, y1)]
    rects += [(a, b, y1 - t, y1) for a, b in _intervals_minus(e0, e1, [gate])]
    z_top = Z_PAVING + SITE['garden_wall']
    bm = bmesh.new()
    _grid_solid(bm, [_wr(*r) for r in rects], (Z_BASE, z_top))
    _object(ctx, 'SM_Site_GardenWalls_North', bm, ['M_Brick'])
    c = NG_COPING[0] / M
    bm = bmesh.new()
    _grid_solid(bm, [_wr(a - c, b + c, ya - c, yb + c) for a, b, ya, yb in rects],
                (z_top - 0.02, z_top - 0.02 + NG_COPING[1]))
    _object(ctx, 'SM_Site_GardenCoping_North', bm, ['M_Stone'])
    bm = bmesh.new()
    _grid_solid(bm, [_wr(e0 + t, e1 - t, y0 + t, y1 - t)], (Z_BASE, Z_COURT))
    _object(ctx, 'SM_Site_GardenLawn_North', bm, ['M_Grass'])
    bm = bmesh.new()
    xa, xb = sorted((xE(gate[0]), xE(gate[1])))
    geo.add_prism_x(bm, _step_profile(yY(y1 - t), yY(y1), (Z_COURT - Z_PAVING) / STEP_N), xa, xb)
    _object(ctx, 'SM_Site_GardenSteps_North', bm, ['M_Stone'])
    _trees(ctx, (e0, e1, y0, y1))


def _trees(ctx, area) -> None:
    """~16 low-poly trees (n81, n36, n71): tapered 7-sided trunks and crowns of
    three jittered icospheres, scattered with a minimum spacing; the path from
    the gate is kept free."""
    T = TREES
    rng = random.Random(T['seed'])
    e0, e1, y0, y1 = area
    m = T['margin'] / M
    pts = []
    for _ in range(5000):
        if len(pts) >= T['count']:
            break
        E, Y = rng.uniform(e0 + m, e1 - m), rng.uniform(y0 + m, y1 - m)
        if abs(E - NG_GATE[0]) < 2.0 and Y > y1 - 8.0:
            continue
        if all(math.hypot(E - a, Y - b) * M >= T['min_dist'] for a, b in pts):
            pts.append((E, Y))
    trunks, crowns = bmesh.new(), bmesh.new()
    for E, Y in pts:
        x, y = xE(E), yY(Y)
        h = rng.uniform(*T['trunk'])
        R = rng.uniform(*T['crown_r'])
        zc = h + 0.8 * R
        z0 = Z_COURT - 0.10
        z1 = zc - 0.2 * R
        bmesh.ops.create_cone(trunks, cap_ends=True, cap_tris=True, segments=7,
                              radius1=T['r_base'], radius2=T['r_top'], depth=z1 - z0,
                              matrix=Matrix.Translation((x, y, (z0 + z1) / 2)))
        a = rng.uniform(0, 2 * math.pi)
        lobes = [(0.0, 0.0, 0.0, R)]
        for k in range(2):
            ang = a + k * math.pi * rng.uniform(0.8, 1.2)
            d = 0.55 * R
            lobes.append((d * math.cos(ang), d * math.sin(ang), rng.uniform(-0.35, 0.15) * R,
                          R * rng.uniform(0.6, 0.75)))
        for dx, dy, dz, r in lobes:
            c = Vector((x + dx, y + dy, zc + dz))
            res = bmesh.ops.create_icosphere(crowns, subdivisions=2, radius=r,
                                             matrix=Matrix.Translation(c) @ Matrix.Diagonal((1.0, 1.0, 0.85, 1.0)))
            for v in res['verts']:
                v.co = c + (v.co - c) * rng.uniform(0.9, 1.1)
    _object(ctx, 'SM_Site_TreeTrunks', trunks, ['M_Bark'])
    _object(ctx, 'SM_Site_TreeCrowns', crowns, ['M_Foliage'])


# --------------------------------------------------------------- footbridge
def _footbridge(ctx) -> None:
    """Arched footbridge over the south rio at E 4.4 -> 5.5 (spec 7, n2, n71,
    n81, n52): a brick segmental arch springing at about quay level from
    abutments 3 cm proud of the quays and spanning the whole rio, a stepped deck
    of Istrian-stone treads (17 risers each way to a landing at the crown)
    running onto both banks, and solid brick parapets with a stone coping that
    end in blocks at the feet (n71, n81, n52 show closed parapets).

    Built as x-prisms of one (s, z) section (s: metres south of the crown,
    y = yc - s): the deck body between the parapets, and the two parapets over
    the full section from the arch to the coping line, so the bridge's outer
    sides are single brick faces and no two faces overlap in one plane."""
    f = FB
    fe0, fe1 = SITE['footbridge_e']
    yq_n, yq_s = SITE['land_y'][1], SITE['rio_south_far']        # quay lines Y 35.25 / 40.5
    xa, xb = sorted((xE(fe0), xE(fe1)))
    pt = f['parapet_t']
    yc = yY((yq_n + yq_s) / 2)                                   # world y of the crown
    half = (yq_s - yq_n) * M / 2                                 # 4.33 m, half the rio width
    n, t = f['risers'], f['tread']
    h = (f['deck'] - Z_PAVING) / n
    L2 = f['landing'] / 2
    S = L2 + (n - 1) * t                                         # half length of the deck
    zb = Z_BASE - 0.10                                            # bottom of the ends, inside the banks
    sa = half - f['abut_proud']                                  # abutment faces
    zs = Z_WATER - 0.06
    # stepped deck: first riser at s = -S, last one at the landing edge s = -L2
    top = [(-S, Z_PAVING + h)]
    for i in range(1, n):
        s = -S + i * t
        top += [(s, Z_PAVING + i * h), (s, Z_PAVING + (i + 1) * h)]
    top += [(-p[0], p[1]) for p in reversed(top)]
    # intrados: segmental arch from the spring at the abutment faces to the crown
    rise = f['crown'] - f['spring']
    R = (sa ** 2 + rise ** 2) / (2 * rise)
    zc = f['crown'] - R
    a0 = math.atan2(f['spring'] - zc, sa)
    segs = 24
    arch = [(R * math.cos(a0 + (math.pi - 2 * a0) * k / segs),          # s = +sa (south) -> -sa
             zc + R * math.sin(a0 + (math.pi - 2 * a0) * k / segs)) for k in range(segs + 1)]
    bottom = [(S, zb), (half + 0.08, zb), (half + 0.08, zs), (sa, zs)] + arch + \
             [(-sa, zs), (-half - 0.08, zs), (-half - 0.08, zb), (-S, zb)]
    # parapet coping line: parallel to the pitch line through the nosings, flat
    # over the landing, with a level end block at each foot
    H, eb = f['parapet_h'], f['end_block']
    z_blk = Z_PAVING + h + eb * h / t + H
    z_top = Z_PAVING + n * h + H
    coping = [(-S, z_blk), (-S + eb, z_blk), (-L2, z_top), (L2, z_top), (S - eb, z_blk), (S, z_blk)]

    def yz(pts):
        return [(yc - s, z) for s, z in pts]

    bm = bmesh.new()
    geo.add_prism_x(bm, yz(top + bottom), xa + pt, xb - pt)
    body = _object(ctx, 'SM_Site_Footbridge', bm, ['M_Brick'])
    # stone treads, landing and risers (risers face away from the crown; the
    # intrados and the abutment faces face towards it and stay brick)
    geo.assign_material_by_normal(body, [
        (ctx.mats['M_Stone'], lambda c, nn: nn.z > 0.7 or (
            abs(nn.y) > 0.7 and nn.y * (c.y - yc) > 0 and c.z > Z_PAVING - 0.2)),
    ])
    bm = bmesh.new()
    for x0 in (xa, xb - pt):
        geo.add_prism_x(bm, yz(coping + bottom), x0, x0 + pt)
    par = _object(ctx, 'SM_Site_FootbridgeParapet', bm, ['M_Brick'])
    geo.assign_material_by_normal(par, [(ctx.mats['M_Stone'], lambda c, nn: nn.z > 0.3)])


# ------------------------------------------------------------ mooring poles
def _poles(ctx) -> None:
    """Mooring poles (n71): pairs flanking every tower water stair, three
    'bricole' (leaning triples) off the south quay of the square at BRICOLE_E
    (n36, n71: on its eastern half, the last one next to the schiera)."""
    P = POLES
    rng = random.Random(P['seed'])
    t = TOWER
    off = P['off'] / M
    gaps = [(yb + ya2) / 2 for (ya, yb), (ya2, _) in zip(_tower_spans(), _tower_spans()[1:])]
    y_ne = t['y_first'] - t['gap'] / 2
    spots = []                                    # (E, Y, centre the pole leans to, or None)
    for Y in gaps + [y_ne]:
        for dY in (-0.6, 0.6):
            spots.append((t['e_outer'] - off, Y + dY, None))
    for Y in gaps:
        for dY in (-0.6, 0.6):
            spots.append((_W(t['e_outer']) + off, Y + dY, None))
    yq = SITE['land_y'][1] + off
    for Ec in BRICOLE_E:
        for j in range(3):
            a = 2 * math.pi * j / 3 + 0.3
            rb = P['bricola_r'] / M
            spots.append((Ec + rb * math.cos(a), yq + rb * math.sin(a), (Ec, yq)))
    bm = bmesh.new()
    for E, Y, centre in spots:
        x, y = xE(E), yY(Y)
        z0, z1 = P['bottom'], rng.uniform(*P['top'])
        L = z1 - z0
        if centre is None:
            ax, ang = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized(), math.radians(rng.uniform(0, 3))
        else:                                     # bricola: lean in so the tops meet
            d = Vector((xE(centre[0]) - x, yY(centre[1]) - y, 0))
            ax, ang = Vector((-d.y, d.x, 0)).normalized(), math.atan2(d.length - P['r'], L)
        rot = Matrix.Rotation(ang, 4, ax)         # + about (d rotated 90 deg) tilts the top towards d
        base = Vector((x, y, z0))
        mat = Matrix.Translation(base) @ rot @ Matrix.Translation((0, 0, L / 2))
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=8, radius1=P['r'],
                              radius2=P['r'] * 0.85, depth=L, matrix=mat)
    _object(ctx, 'SM_Site_MooringPoles', bm, ['M_Wood'])


# --------------------------------------------------------------------- build
def build(ctx) -> None:
    _local_materials(ctx)
    _water(ctx)
    _plate(ctx)
    _banks(ctx)
    _square_grid(ctx)
    _gardens_south(ctx)
    _garden_north(ctx)
    _footbridge(ctx)
    _poles(ctx)
