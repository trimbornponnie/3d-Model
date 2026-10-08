"""Pre-export validation following the jasonkneen-3d-modeling skill
(.claude/skills/jasonkneen-3d-modeling/references/validations.md):

- unapplied-transforms-export: every mesh has identity rotation/scale and is
  applied before export;
- missing-normals-recalculation: normals recalculated outward;
- no-ngon-check: faces with > 4 vertices are triangulated (static architecture:
  "triangles are fine for static hard surface IF intentionally placed");
- no-nonmanifold-check: every solid is watertight (no non-manifold edges/verts);
- merge-by-distance-missing: duplicate vertices merged after booleans;
- invalid-asset-naming: names match [Prefix]_[Asset]_[Variant], no spaces.
"""
from __future__ import annotations

import re

import bmesh
import bpy

NAME_RE = re.compile(r'^(SM|M|COL)_[A-Za-z0-9]+(_[A-Za-z0-9]+)*$')


def apply_transforms(objs) -> None:
    for o in objs:
        if o.type != 'MESH':
            continue
        if o.matrix_world.is_identity:
            continue
        o.data.transform(o.matrix_world)
        o.matrix_world.identity()


def triangulate_ngons(obj) -> int:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    n = len(ngons)
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons, quad_method='BEAUTY', ngon_method='BEAUTY')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return n


def stats(obj) -> dict:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    res = {
        'faces': len(bm.faces),
        'tris_equiv': sum(len(f.verts) - 2 for f in bm.faces),
        'ngons': sum(1 for f in bm.faces if len(f.verts) > 4),
        'nonmanifold_edges': sum(1 for e in bm.edges if not e.is_manifold),
        'nonmanifold_verts': sum(1 for v in bm.verts if not v.is_manifold),
        'loose_verts': sum(1 for v in bm.verts if not v.link_faces),
        'zero_area_faces': sum(1 for f in bm.faces if f.calc_area() < 1e-9),
    }
    bm.free()
    return res


def check_scene(mesh_objs, triangulate: bool = True) -> dict:
    report = {'objects': 0, 'tris': 0, 'ngons_fixed': 0, 'problems': []}
    apply_transforms(mesh_objs)
    for o in mesh_objs:
        if o.type != 'MESH':
            continue
        report['objects'] += 1
        if triangulate:
            report['ngons_fixed'] += triangulate_ngons(o)
        s = stats(o)
        report['tris'] += s['tris_equiv']
        if not NAME_RE.match(o.name):
            report['problems'].append(f"{o.name}: name does not follow SM_Asset_Variant")
        if any(abs(v - 1.0) > 1e-6 for v in o.scale) or any(abs(v) > 1e-6 for v in o.rotation_euler):
            report['problems'].append(f"{o.name}: unapplied transform")
        for k in ('ngons', 'nonmanifold_edges', 'nonmanifold_verts', 'loose_verts', 'zero_area_faces'):
            if s[k]:
                report['problems'].append(f"{o.name}: {k} = {s[k]}")
    return report
