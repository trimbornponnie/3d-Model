"""Interior engine (docs/INTERIORS.md): hollows the masonry bodies built by the
exterior modules, then builds the construction layers, partitions, doors and
stairs inside them. The part modules (interior_towers, interior_carpet,
interior_schiera) hold the data - rooms, walls, doors, stairs per dwelling -
and call these primitives.

All geometry is in world metres (x east, y north, z up); the part modules
convert their drawing coordinates with common.xE / yY. Plan polygons are lists
of (x, y), counter-clockwise seen from above. Layer stacks are lists of
(element, material, thickness), outermost / topmost first.

Object names follow the skill's convention, SM_<Part>_<Element>_<Tag>: one
object per element and material per tower, carpet segment or schiera block
(e.g. SM_Tower_FloorParquet_E0, SM_Carpet_Partitions_E1).
"""
from __future__ import annotations

import math
from typing import Callable, Sequence

import bmesh
import bpy
from mathutils import Vector

from . import geo

Poly = Sequence[tuple[float, float]]


# ------------------------------------------------------------------- bags
class Kit:
    """One bmesh per (element, material) of a part tag, flushed into objects."""

    def __init__(self, ctx, part: str, tag: str, col: str):
        self.ctx, self.part, self.tag, self.col = ctx, part, tag, col
        self.items: dict[str, tuple[bmesh.types.BMesh, str, dict]] = {}

    def name(self, element: str) -> str:
        return f'SM_{self.part}_{element}_{self.tag}'

    def __call__(self, element: str, mat: str, **props) -> bmesh.types.BMesh:
        name = self.name(element)
        if name not in self.items:
            self.items[name] = (bmesh.new(), mat, props)
        return self.items[name][0]

    def flush(self) -> dict[str, bpy.types.Object]:
        out = {}
        for name, (bm, mat, props) in self.items.items():
            if len(bm.faces):
                o = geo.object_from_bmesh(bm, name, self.ctx.col(self.col), self.ctx.mats[mat])
                for k, v in props.items():
                    o[k] = v
                out[name] = o
            else:
                bm.free()
        self.items = {}
        return out


# --------------------------------------------------------------- polygons
def rect(x0: float, x1: float, y0: float, y1: float) -> list[tuple[float, float]]:
    """Axis-aligned rectangle, counter-clockwise."""
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def area(poly: Poly) -> float:
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                     for i in range(len(poly)))


def ccw(poly: Poly) -> list[tuple[float, float]]:
    p = [tuple(map(float, v)) for v in poly]
    return p if area(p) > 0 else list(reversed(p))


def offset(poly: Poly, d: float) -> list[tuple[float, float]]:
    """Polygon offset by d (positive = inward for a ccw polygon), mitred
    corners. Meant for the rectilinear rooms of this project."""
    p = ccw(poly)
    n = len(p)
    out = []
    for i in range(n):
        a, b, c = Vector(p[i - 1]), Vector(p[i]), Vector(p[(i + 1) % n])
        e1, e2 = (b - a).normalized(), (c - b).normalized()
        n1, n2 = Vector((-e1.y, e1.x)), Vector((-e2.y, e2.x))      # inward normals (left of a ccw edge)
        m = n1 + n2
        if m.length < 1e-9:
            out.append(tuple(b + n1 * d))
            continue
        m.normalize()
        k = d / max(m.dot(n1), 1e-6)
        out.append(tuple(b + m * k))
    return out


# --------------------------------------------------------------- solids
def prism(bm, poly: Poly, z0: float, top: float | Callable[[float, float], float]) -> None:
    """Prism over a plan polygon from z0 to `top`: a level or a function
    z(x, y) for a sloping or curved top (one vertex per polygon corner, so a
    planar top only)."""
    p = ccw(poly)
    bot = [bm.verts.new((x, y, z0)) for x, y in p]
    top_v = [bm.verts.new((x, y, top(x, y) if callable(top) else top)) for x, y in p]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top_v)
    n = len(p)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top_v[j], top_v[i]))


def ring(bm, outer: Poly, inner: Poly, z0: float, z1: float) -> None:
    """Closed ring solid between two polygons with the same corner count
    (e.g. a polygon and its offset), from z0 to z1: one manifold shell."""
    o, i_ = ccw(outer), ccw(inner)
    assert len(o) == len(i_)
    ob = [bm.verts.new((x, y, z0)) for x, y in o]
    ot = [bm.verts.new((x, y, z1)) for x, y in o]
    ib = [bm.verts.new((x, y, z0)) for x, y in i_]
    it = [bm.verts.new((x, y, z1)) for x, y in i_]
    n = len(o)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((ob[k], ob[j], ot[j], ot[k]))        # outer side
        bm.faces.new((ib[j], ib[k], it[k], it[j]))        # inner side
        bm.faces.new((ot[k], ot[j], it[j], it[k]))        # top
        bm.faces.new((ob[j], ob[k], ib[k], ib[j]))        # bottom


def obox(bm, a: tuple[float, float], b: tuple[float, float], s0: float, s1: float,
         t0: float, t1: float, z0: float, z1: float) -> None:
    """Box in the frame of the plan segment a -> b: from s0 to s1 metres along
    it, t0 to t1 metres across it (to the left of a -> b), z0 to z1."""
    a, b = Vector(a), Vector(b)
    e = (b - a).normalized()
    n = Vector((-e.y, e.x))
    pts = [a + e * s + n * t for s, t in ((s0, t0), (s1, t0), (s1, t1), (s0, t1))]
    prism(bm, [(p.x, p.y) for p in pts], z0, z1)


def oprism(bm, a, b, outline_sz: Poly, t0: float, t1: float) -> None:
    """Prism of an (s, z) outline drawn in the vertical plane of the plan
    segment a -> b (s metres from a), extruded from t0 to t1 metres across it
    (positive = left of a -> b). One manifold shell, concave outlines allowed."""
    A, B = Vector(a), Vector(b)
    e = (B - A).normalized()
    n = Vector((-e.y, e.x))
    pts = list(outline_sz)
    # orient the outline counter-clockwise in (s, z)
    if area(pts) < 0:
        pts = list(reversed(pts))
    va = [bm.verts.new((*(A + e * s_ + n * t0)[:], z)) for s_, z in pts]
    vb = [bm.verts.new((*(A + e * s_ + n * t1)[:], z)) for s_, z in pts]
    bm.faces.new(va)
    bm.faces.new(list(reversed(vb)))
    k = len(pts)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((va[j], va[i], vb[i], vb[j]))


# --------------------------------------------------------------- hollowing
def hollow(ctx, body: bpy.types.Object, volumes: bmesh.types.BMesh, tag: str = 'Int') -> None:
    """Cut the interior volumes (rooms, stair wells, door passages through the
    masonry) out of a body: one exact difference in self-intersection mode, so
    the volumes may overlap. Normals are kept as the solver returns them (not
    recalculated), so that a room enclosed by the masonry stays an inward-
    facing cavity."""
    if not len(volumes.faces):
        volumes.free()
        return
    cutter = geo.object_from_bmesh(volumes, f'{body.name}_Cut{tag}', ctx.cutters)
    mod = body.modifiers.new('Bool_Interior', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.use_self = True
    mod.object = cutter
    geo.apply_modifiers(body)
    geo.cleanup(body, recalc=False)


def cut_openings(ctx, obj: bpy.types.Object, recs: Sequence[dict], depth: float = 1.5,
                 extra: bmesh.types.BMesh | None = None) -> None:
    """Cut registered openings (geo.OPENINGS records) through a layer object -
    e.g. the wall linings - from 0.3 m outside the outer face to `depth` in."""
    bm = extra if extra is not None else bmesh.new()
    for r in recs:
        f = geo.Face(r['axis'], r['coord'], r['out'])
        f.solid(bm, r['outline'], depth, outside=0.3)
    if not len(bm.faces):
        bm.free()
        return
    cutter = geo.object_from_bmesh(bm, f'{obj.name}_CutOpenings', ctx.cutters)
    mod = obj.modifiers.new('Bool_Openings', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.use_self = True
    mod.object = cutter
    geo.apply_modifiers(obj)
    geo.cleanup(obj)


def openings_of(target: str, recs: Sequence[dict] | None = None) -> list[dict]:
    """Registered openings cut into the object named `target`."""
    return [r for r in (geo.OPENINGS if recs is None else recs) if r.get('target') == target]


# --------------------------------------------------------------- layers
def floor_stack(kit: Kit, poly: Poly, z_top: float, layers, prefix: str = 'Floor') -> float:
    """Horizontal build-up over a plan polygon, from the finished level z_top
    down: layers [(element, material, thickness), ...] top first. Returns the
    bottom level."""
    z = z_top
    for elem, mat, t in layers:
        if t > 0:
            props = {'uv_rotate': 45.0} if mat == 'M_Parquet' else {}
            prism(kit(f'{prefix}{elem}', mat, **props), poly, z - t, z)
        z -= t
    return z


def lining(kit: Kit, poly: Poly, z0: float, z1: float, layers, prefix: str = 'Wall') -> list[tuple[float, float]]:
    """Layers on the inner face of the walls round a room: poly is the
    masonry's inner face (ccw), layers [(element, material, thickness), ...]
    from the masonry inward. Returns the finished room outline."""
    d = 0.0
    outer = ccw(poly)
    for elem, mat, t in layers:
        if t <= 0:
            continue
        inner = offset(poly, d + t)
        ring(kit(f'{prefix}{elem}', mat), outer, inner, z0, z1)
        outer, d = inner, d + t
    return outer


def partition(kit: Kit, a, b, z0: float, z1: float, layers, doors=(), prefix: str = 'Partition',
              extend: float = 0.0) -> None:
    """Straight wall on the plan centreline a -> b, from z0 to z1, built of
    `layers` [(element, material, thickness), ...] listed from the left face
    (seen from a towards b) to the right; doors [(s_centre, width, head), ...]
    leave openings at s_centre metres from a. `extend` lengthens both ends
    (e.g. into the wall linings). Each layer is one solid: the wall's (s, z)
    outline with the door notches, extruded across the layer."""
    L = (Vector(b) - Vector(a)).length
    T = sum(t for _, _, t in layers)
    out = [(-extend, z0)]
    for s_c, w, head in sorted(doors):
        g0, g1 = s_c - w / 2, s_c + w / 2
        if head >= z1 - 1e-6:                      # full-height gap: split the wall
            raise ValueError('door as high as the wall: build two partitions')
        out += [(g0, z0), (g0, head), (g1, head), (g1, z0)]
    out += [(L + extend, z0), (L + extend, z1), (-extend, z1)]
    t_left = T / 2
    for elem, mat, t in layers:
        oprism(kit(f'{prefix}{elem}', mat), a, b, out, t_left - t, t_left)
        t_left -= t


def door(kit: Kit, a, b, s: float, width: float, head: float, z0: float, wall_t: float,
         hinge: str = 'a', swing: int = 1, open_deg: float = 90.0,
         leaf_mat: str = 'M_DoorLeaf', frame_mat: str = 'M_DoorFrame',
         leaf_t: float = 0.04, casing: float = 0.02, archi: tuple[float, float] = (0.07, 0.015),
         prefix: str = 'Door') -> None:
    """Interior door in a wall on the plan line a -> b (the wall's centreline,
    thickness wall_t) at s metres from a: a casing lining the opening's jambs
    and head, architraves on both faces, and the leaf, hinged at the jamb on
    the `a` or `b` side and opened `open_deg` towards side `swing` (+1 =
    left of a -> b)."""
    fr = kit(f'{prefix}Frames', frame_mat)
    s0, s1 = s - width / 2, s + width / 2
    h = wall_t / 2 + 0.002

    def u_frame(o0, o1, top, c):
        return [(o0, z0), (o0 + c, z0), (o0 + c, top - c), (o1 - c, top - c), (o1 - c, z0), (o1, z0),
                (o1, top), (o0, top)]
    # casing (jambs + head) lining the opening through the wall
    oprism(fr, a, b, u_frame(s0, s1, head, casing), -h, h)
    # architraves on both faces, round the casing
    aw, at = archi
    for side in (-1, 1):
        t0, t1 = sorted((side * (h - 0.001), side * (h + at)))     # 1 mm into the casing: no shared edges
        oprism(fr, a, b, u_frame(s0 + casing - aw, s1 - casing + aw, head - casing + aw, aw), t0, t1)
    # leaf, rotated about the hinge
    A, B = Vector(a), Vector(b)
    e = (B - A).normalized()
    n = Vector((-e.y, e.x))
    lw = width - 2 * casing - 0.006
    hinge_s = s0 + casing + 0.003 if hinge == 'a' else s1 - casing - 0.003
    dir_s = 1.0 if hinge == 'a' else -1.0
    piv = A + e * hinge_s + n * (swing * (h - 0.0))
    ang = math.radians(open_deg) * swing * dir_s
    ca, sa = math.cos(ang), math.sin(ang)

    def rot(v: Vector) -> Vector:
        return Vector((v.x * ca - v.y * sa, v.x * sa + v.y * ca))

    along, across = e * dir_s, -n * swing
    pts = [Vector((0, 0)), along * lw, along * lw + across * leaf_t, across * leaf_t]
    poly = [tuple(piv + rot(p)) for p in pts]
    prism(kit(f'{prefix}Leaves', leaf_mat), poly, z0 + 0.008, head - casing - 0.003)


# --------------------------------------------------------------- stairs
def flight(kit: Kit, start, direction, width: float, n_risers: int, riser: float, going: float,
           z0: float, waist: float = 0.15, tread_t: float = 0.03, nosing: float = 0.02,
           tread_mat: str = 'M_StairTread', struct_mat: str = 'M_Structure',
           side: int = 1, prefix: str = 'Stair', tread_top_last: bool = False) -> tuple[Vector, float]:
    """Straight flight: a stepped reinforced-concrete waist slab and finish
    treads. `start` is the plan point at the foot of the first riser on the
    flight's edge, `direction` the walking direction, the flight lies `width`
    to the left (side=1) or right (side=-1) of that edge. z0 is the finished
    level at the foot; each step rises `riser` (finished) with `going` treads.
    The last riser lands on the upper floor (n_risers - 1 treads), unless
    tread_top_last. Returns (plan point at the top riser, finished top level)."""
    P0, d = Vector(start), Vector(direction).normalized()
    nrm = Vector((-d.y, d.x)) * side
    n_treads = n_risers if tread_top_last else n_risers - 1
    zt = z0 - tread_t                         # top of the structure at the foot
    slope = riser / going
    w_v = waist / math.cos(math.atan(slope))  # waist measured vertically
    s_top = n_treads * going
    z_top = zt + n_risers * riser
    # closed (s, z) profile: floor at the foot, the steps, the top end, the soffit
    prof = [(0.0, zt)]
    for k in range(n_risers):
        prof.append((k * going, zt + (k + 1) * riser))
        if k + 1 < n_risers or tread_top_last:
            prof.append(((k + 1) * going, zt + (k + 1) * riser))
    s_hit = w_v / slope                       # soffit (inner-corner line - w_v) meets the floor
    z_soffit_top = zt + slope * s_top - w_v
    if tread_top_last:
        z_soffit_top = min(z_soffit_top, z_top - w_v)
    prof += [(s_top, z_top - 1e-9), (s_top, z_soffit_top), (min(s_hit, s_top * 0.999), zt)]
    # drop consecutive duplicates
    clean = []
    for pt in prof:
        if not clean or abs(pt[0] - clean[-1][0]) > 1e-7 or abs(pt[1] - clean[-1][1]) > 1e-7:
            clean.append(pt)
    bm = kit(f'{prefix}Structure', struct_mat)
    va = [bm.verts.new((*(P0 + d * s_)[:], z)) for s_, z in clean]
    vb = [bm.verts.new((*(P0 + d * s_ + nrm * width)[:], z)) for s_, z in clean]
    nv = len(clean)
    bm.faces.new(va)
    bm.faces.new(list(reversed(vb)))
    for i in range(nv):
        j = (i + 1) % nv
        bm.faces.new((va[j], va[i], vb[i], vb[j]))
    # treads, with a small nosing
    tb = kit(f'{prefix}Treads', tread_mat)
    for k in range(n_treads):
        s0, s1 = k * going - nosing, (k + 1) * going
        z = z0 + (k + 1) * riser
        c0, c1 = P0 + d * s0, P0 + d * s1
        quad = [c0, c1, c1 + nrm * width, c0 + nrm * width]
        prism(tb, [(p.x, p.y) for p in quad], z - tread_t, z)
    return P0 + d * s_top, z0 + n_risers * riser


def landing(kit: Kit, poly: Poly, z_top: float, thickness: float = 0.18, finish_t: float = 0.03,
            finish_mat: str = 'M_StairTread', struct_mat: str = 'M_Structure', prefix: str = 'Stair') -> None:
    prism(kit(f'{prefix}Treads', finish_mat), poly, z_top - finish_t, z_top)
    prism(kit(f'{prefix}Structure', struct_mat), poly, z_top - finish_t - thickness, z_top - finish_t)


def handrail(kit: Kit, pts3d, height: float = 0.90, post_every: float = 1.0, rail_d: float = 0.04,
             post_d: float = 0.025, mat: str = 'M_Steel', prefix: str = 'Stair', posts: bool = True) -> None:
    """Handrail along a 3D polyline of nosing points (x, y, z), `height`
    above it, with square posts every `post_every` metres."""
    bm = kit(f'{prefix}Rails', mat)
    P = [Vector(p) for p in pts3d]
    for p, q in zip(P[:-1], P[1:]):
        _bar(bm, p + Vector((0, 0, height)), q + Vector((0, 0, height)), rail_d)
        if posts:
            L = (q - p).length
            k = max(1, int(L / post_every))
            for i in range(k + 1):
                c = p + (q - p) * (i / k)
                _bar(bm, c, c + Vector((0, 0, height)), post_d)


def _bar(bm, p: Vector, q: Vector, d: float) -> None:
    """Square bar of side d from p to q."""
    ax = (q - p)
    if ax.length < 1e-6:
        return
    ax_n = ax.normalized()
    ref = Vector((0, 0, 1)) if abs(ax_n.z) < 0.9 else Vector((1, 0, 0))
    u = ax_n.cross(ref).normalized() * (d / 2)
    v = ax_n.cross(u).normalized() * (d / 2)
    corners = [-u - v, u - v, u + v, -u + v]
    a = [bm.verts.new(p + c) for c in corners]
    b = [bm.verts.new(q + c) for c in corners]
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))
