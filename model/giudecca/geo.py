"""Mesh helpers for the Giudecca model (Blender 4.x / 5.x, bpy).

Conventions (see docs/ANALYSIS.md §2): 1 Blender unit = 1 m, +X east, +Y north,
+Z up. Every solid is built as a closed, consistently-oriented mesh so that the
exact boolean solver and the manifold checks in validate.py stay reliable.

Following the jasonkneen-3d-modeling skill (hard-surface workflow):
- openings are cut with booleans, cutters live in a hidden "Cutters" collection
  (renamed CUT_* by rename_cutters() so they never pass for SM_ meshes), the
  Exact solver is used, and every boolean is followed by a merge-by-distance
  and a normal recalculation;
- n-gons left by booleans are triangulated before export (validate.py).
"""
from __future__ import annotations

import math
import re
from typing import Iterable, Sequence

import bmesh
import bpy
from mathutils import Vector

EPS = 1e-4


# ---------------------------------------------------------------- collections
def collection(name: str, parent: bpy.types.Collection | None = None,
               hide: bool = False) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    col.hide_render = hide
    col.hide_viewport = hide
    return col


def _link(obj: bpy.types.Object, col: bpy.types.Collection) -> bpy.types.Object:
    col.objects.link(obj)
    return obj


def object_from_bmesh(bm: bmesh.types.BMesh, name: str, col: bpy.types.Collection,
                      material: bpy.types.Material | None = None) -> bpy.types.Object:
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=EPS)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    if material is not None:
        me.materials.append(material)
    return _link(obj, col)


# ------------------------------------------------------------------ primitives
def add_box(bm: bmesh.types.BMesh, x0: float, x1: float, y0: float, y1: float,
            z0: float, z1: float) -> None:
    """Axis-aligned box (6 quads) appended to bm."""
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    v = [bm.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])


def add_prism_x(bm: bmesh.types.BMesh, profile_yz: Sequence[tuple[float, float]],
                x0: float, x1: float) -> None:
    """Extrude a closed (y, z) profile (counter-clockwise seen from +X) from x0 to x1."""
    _add_prism(bm, [(x0, y, z) for y, z in profile_yz], Vector((x1 - x0, 0, 0)))


def add_prism_y(bm: bmesh.types.BMesh, profile_xz: Sequence[tuple[float, float]],
                y0: float, y1: float) -> None:
    """Extrude a closed (x, z) profile from y0 to y1."""
    _add_prism(bm, [(x, y0, z) for x, z in profile_xz], Vector((0, y1 - y0, 0)))


def add_prism_z(bm: bmesh.types.BMesh, poly_xy: Sequence[tuple[float, float]],
                z0: float, z1: float) -> None:
    """Extrude a closed (x, y) footprint polygon from z0 to z1."""
    _add_prism(bm, [(x, y, z0) for x, y in poly_xy], Vector((0, 0, z1 - z0)))


def _add_prism(bm: bmesh.types.BMesh, base: Sequence[tuple[float, float, float]],
               d: Vector) -> None:
    n = len(base)
    bot = [bm.verts.new(p) for p in base]
    top = [bm.verts.new(Vector(p) + d) for p in base]
    bm.faces.new(bot)
    bm.faces.new(list(reversed(top)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))


def box(name: str, col, x0, x1, y0, y1, z0, z1, material=None) -> bpy.types.Object:
    bm = bmesh.new()
    add_box(bm, x0, x1, y0, y1, z0, z1)
    return object_from_bmesh(bm, name, col, material)


def arch_profile(cx: float, width: float, z_spring: float, rise: float,
                 z_bottom: float, segments: int = 12) -> list[tuple[float, float]]:
    """Closed (u, z) outline of an opening with a segmental (or semicircular,
    rise = width / 2) arched head, counter-clockwise."""
    half = width / 2.0
    pts = [(cx - half, z_bottom), (cx + half, z_bottom), (cx + half, z_spring)]
    if rise > EPS:
        r = (half ** 2 + rise ** 2) / (2 * rise)
        zc = z_spring + rise - r
        a0 = math.atan2(z_spring - zc, half)
        for k in range(1, segments):
            a = a0 + (math.pi - 2 * a0) * k / segments
            pts.append((cx + r * math.cos(a), zc + r * math.sin(a)))
    pts.append((cx - half, z_spring))
    return pts


def circle_profile(cu: float, cz: float, radius: float, segments: int = 16):
    return [(cu + radius * math.cos(2 * math.pi * k / segments),
             cz + radius * math.sin(2 * math.pi * k / segments)) for k in range(segments)]


# ---------------------------------------------------------------- façade frame
class Face:
    """An axis-aligned façade plane.

    axis: 'x' (plane x = const, façade facing ±X) or 'y' (plane y = const).
    coord: the plane coordinate (outer face of the wall).
    out: +1 / -1, direction of the outward normal along that axis.
    u runs along the façade (world y for 'x' faces, world x for 'y' faces).
    """

    def __init__(self, axis: str, coord: float, out: int):
        assert axis in ('x', 'y') and out in (1, -1)
        self.axis, self.coord, self.out = axis, coord, out

    def solid(self, bm, outline_uz, depth: float, outside: float = 0.15):
        """Prism of the (u, z) outline from `outside` m in front of the face to
        `depth` m into the wall."""
        a = self.coord + self.out * outside
        b = self.coord - self.out * depth
        if self.axis == 'x':
            add_prism_x(bm, list(outline_uz), min(a, b), max(a, b))
        else:
            # profile is (x, z) for a y-extrusion
            add_prism_y(bm, list(outline_uz), min(a, b), max(a, b))

    def plane_point(self, u: float, z: float, offset: float = 0.0) -> Vector:
        c = self.coord - self.out * offset
        return Vector((c, u, z)) if self.axis == 'x' else Vector((u, c, z))


# ------------------------------------------------------------ openings registry
# Every window, door and oculus cut by opening() / round_window() (and by the
# modules' own recess cutters through register()) is recorded here, so the
# joinery (frames, sashes, glass, sills) and the interiors can be built from
# one list after the parts. With THROUGH set (interiors on), these openings are
# cut THROUGH deep from the outer face - right through the wall - and get no
# plain glass pane: the joinery puts the glazing in.
OPENINGS: list[dict] = []
THROUGH: float | None = None


def register(face: Face, outline, kind: str, **info) -> dict:
    """Record one opening on `face` (outline in the face's (u, z) plane)."""
    rec = dict(axis=face.axis, coord=face.coord, out=face.out,
               outline=[(float(u), float(z)) for u, z in outline], kind=kind, target=None, **info)
    OPENINGS.append(rec)
    return rec


def opening(face: Face, cutters_bm, panes_bm, u: float, z0: float, width: float,
            height: float, arch_rise: float = 0.0, recess: float = 0.0,
            through: float | None = None, pane: bool = True,
            glass_inset: float = 0.12, keep_recess: bool = False) -> dict:
    """Add one opening on `face`; returns its OPENINGS record.

    - through=None: a recess `recess` deep (or 0.25 m default) with a glass pane
      at its back - used for windows/doors of closed volumes (with THROUGH set:
      cut THROUGH deep and no pane, unless keep_recess, for blind niches);
    - through=<wall thickness>: cut right through (arcades, passages).
    The outline is a rectangle, or rectangle + segmental arch when arch_rise > 0.
    """
    z_spring = z0 + height - arch_rise
    outline = arch_profile(u, width, z_spring, arch_rise, z0) if arch_rise > EPS else [
        (u - width / 2, z0), (u + width / 2, z0), (u + width / 2, z0 + height), (u - width / 2, z0 + height)]
    rec = register(face, outline, 'arch' if arch_rise > EPS else 'rect', u=u, z0=z0, width=width,
                   height=height, arch_rise=arch_rise, recess=recess, through=through, pane=pane,
                   glass_inset=glass_inset, keep_recess=keep_recess)
    depth = through + 0.2 if through is not None else max(recess, glass_inset + 0.04)
    if through is None and THROUGH is not None and not keep_recess:
        depth, pane = THROUGH, False
    face.solid(cutters_bm, outline, depth)
    if pane and through is None:
        # glass sheet 2 cm thick at the back of the recess, slightly inside the cut
        shrink = 0.002
        o = [(p[0] + (shrink if p[0] < u else -shrink), p[1] + (shrink if p[1] < z0 + height / 2 else -shrink))
             for p in outline]
        a = face.coord - face.out * glass_inset
        b = a - face.out * 0.02
        if face.axis == 'x':
            add_prism_x(panes_bm, o, min(a, b), max(a, b))
        else:
            add_prism_y(panes_bm, o, min(a, b), max(a, b))
    return rec


def round_window(face: Face, cutters_bm, panes_bm, u: float, zc: float, diameter: float,
                 recess: float = 0.18) -> dict:
    prof = circle_profile(u, zc, diameter / 2)
    rec = register(face, prof, 'round', u=u, zc=zc, diameter=diameter, recess=recess)
    if THROUGH is not None:
        face.solid(cutters_bm, prof, THROUGH)
        return rec
    face.solid(cutters_bm, prof, recess)
    prof_in = circle_profile(u, zc, diameter / 2 - 0.003)
    a = face.coord - face.out * (recess - 0.04)
    b = a - face.out * 0.02
    if face.axis == 'x':
        add_prism_x(panes_bm, prof_in, min(a, b), max(a, b))
    else:
        add_prism_y(panes_bm, prof_in, min(a, b), max(a, b))
    return rec


# --------------------------------------------------------------------- boolean
def boolean_difference(target: bpy.types.Object, cutter_bm: bmesh.types.BMesh,
                       cutters_col: bpy.types.Collection, keep_cutter: bool = True) -> None:
    """Exact boolean difference of `target` minus the solids in `cutter_bm`."""
    if len(cutter_bm.faces) == 0:
        cutter_bm.free()
        return
    cutter = object_from_bmesh(cutter_bm, f"{target.name}_Cut", cutters_col)
    mod = target.modifiers.new("Bool_Openings", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    apply_modifiers(target)
    cleanup(target)
    if not keep_cutter:
        bpy.data.objects.remove(cutter, do_unlink=True)


def rename_cutters(cutters_col: bpy.types.Collection, prefix: str = 'CUT_') -> int:
    """Give the cutter objects (and meshes) in `cutters_col` their own prefix:
    SM_Tower_Body_E0_Cut1 -> CUT_Tower_Body_E0_1, SM_Carpet_CampoSouth_Cut ->
    CUT_Carpet_CampoSouth. The SM_ prefix is kept for exportable static meshes
    (skill: invalid-asset-naming). Returns the number of objects renamed."""
    n = 0
    for o in list(cutters_col.objects):
        if o.name.startswith(prefix):
            continue
        base = o.name[3:] if o.name.startswith('SM_') else o.name
        m = re.match(r'^(.*)_Cut(\d*)$', base)
        if m:
            base = m.group(1) + (f'_{m.group(2)}' if m.group(2) else '')
        o.name = prefix + base
        if o.data is not None and o.data.users == 1:
            o.data.name = o.name
        n += 1
    return n


def boolean_union(target: bpy.types.Object, others: Iterable[bpy.types.Object]) -> None:
    for o in others:
        mod = target.modifiers.new("Bool_Union", 'BOOLEAN')
        mod.operation = 'UNION'
        mod.solver = 'EXACT'
        mod.object = o
        apply_modifiers(target)
        bpy.data.objects.remove(o, do_unlink=True)
    cleanup(target)


def apply_modifiers(obj: bpy.types.Object) -> None:
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = obj.data
    mats = list(old.materials)
    obj.modifiers.clear()
    obj.data = me
    for m in mats:
        if m.name not in [x.name for x in me.materials if x]:
            me.materials.append(m)
    bpy.data.meshes.remove(old)
    me.name = obj.name             # keep mesh names free of .001 suffixes in exports


def cleanup(obj: bpy.types.Object, dist: float = EPS, recalc: bool = True) -> None:
    """Merge by distance, delete loose geometry, dissolve degenerate faces and
    recalculate normals outward (skill validations: merge-by-distance-missing,
    missing-normals-recalculation). recalc=False keeps the normals as they are
    - for bodies with enclosed cavities (rooms), whose inward-facing shells a
    recalculation would turn outward."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    loose_e = [e for e in bm.edges if not e.link_faces]
    if loose_e:
        bmesh.ops.delete(bm, geom=loose_e, context='EDGES')
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def assign_material_by_normal(obj: bpy.types.Object, rules) -> None:
    """rules: list of (material, predicate(face_center, normal) -> bool), first
    match wins; unmatched faces keep slot 0."""
    me = obj.data
    slots = {}
    for mat, _ in rules:
        if mat.name not in [m.name for m in me.materials if m]:
            me.materials.append(mat)
        slots[mat.name] = [m.name for m in me.materials].index(mat.name)
    for poly in me.polygons:
        c, n = poly.center, poly.normal
        for mat, pred in rules:
            if pred(c, n):
                poly.material_index = slots[mat.name]
                break


def world_box_uv(obj: bpy.types.Object, scale: float = 1.0) -> None:
    """World-scale box projection: faces facing ±X get (y, z), ±Y get (x, z),
    ±Z get (x, y). 1 UV unit = 1/scale m, so texel density is identical on every
    object (skill: uv-unwrapping-strategy / texel-density-inconsistency).
    Faces facing up or down that are pitched along x (a lean-to rising E-W) get
    (y, x), so v always runs down the slope and the courses of the roof-tile
    image stay parallel to the eaves; level faces keep (x, y)."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = obj.matrix_world
    rot = math.radians(obj.get('uv_rotate', 0.0))     # e.g. 45 deg: herringbone parquet at 45 deg to the walls
    cr, sr = math.cos(rot), math.sin(rot)
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                u, v = co.y * (1 if n.x > 0 else -1), co.z
            elif ax == 1:
                u, v = co.x * (-1 if n.y > 0 else 1), co.z
            elif abs(n.x) > abs(n.y) + 1e-6:
                u, v = co.y, co.x       # pitched along x: v runs down the slope, as on N-S pitches
            else:
                u, v = co.x, co.y
                if rot:
                    u, v = u * cr - v * sr, u * sr + v * cr
            uv[li].uv = (u * scale, v * scale)
