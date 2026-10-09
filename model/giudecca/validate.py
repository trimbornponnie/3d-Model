"""Export preparation and validation following the jasonkneen-3d-modeling skill
(.claude/skills/jasonkneen-3d-modeling/references/validations.md).

prepare_for_export() is the only function here that changes the scene: it
applies transforms and triangulates n-gons (static architecture: "triangles
are fine for static hard surface IF intentionally placed") and returns what it
changed. check_scene() only reports. Per object, as problems:

- invalid-asset-naming: meshes SM_<Asset>_<Variant>, materials M_<Name>, no spaces;
- unapplied-transforms-export: identity rotation / scale;
- no-ngon-check: n-gons left (for_export=True, i.e. after prepare_for_export);
- no-nonmanifold-check: watertight solids, no non-manifold edges / vertices;
- merge-by-distance-missing: loose vertices, zero-area faces;
- missing-normals-recalculation: neighbouring faces with opposite winding
  (flipped_edges) and closed shells whose normals point inward (inverted_shells);
- uv-unwrapping-strategy: a UV map on every mesh, a material on every face.

Between objects, as warnings (they are visible defects or sub-millimetre
mismatches, but some are buried and harmless, so they do not fail the build):

- zfight: coplanar faces of two objects facing the same way and overlapping;
- contact: faces of two objects facing each other that should touch but sit
  1e-5 .. CONTACT_TOL m apart (a slit, or an interpenetration of a fraction of
  a millimetre), the sign of a rounded copy of a derived dimension.
"""
from __future__ import annotations

import re
from collections import defaultdict

import bmesh
import numpy as np

MESH_RE = re.compile(r'^SM_[A-Za-z0-9]+(_[A-Za-z0-9]+)*$')
MAT_RE = re.compile(r'^M_[A-Za-z0-9]+(_[A-Za-z0-9]+)*$')
NAME_RE = MESH_RE                       # old name

SLIVER_H = 1e-4                         # m, triangle altitude under which a face is a sliver
COPLANAR_TOL = 5e-4                     # m, same-facing faces closer than this z-fight
CONTACT_TOL = 1e-3                      # m, facing faces closer than this (but not touching) are a mismatch
MIN_AREA = 1e-3                         # m², overlaps smaller than this are ignored


# --------------------------------------------------------------- preparation
def apply_transforms(objs) -> int:
    n = 0
    for o in objs:
        if o.type != 'MESH' or o.matrix_world.is_identity:
            continue
        o.data.transform(o.matrix_world)
        o.matrix_world.identity()
        n += 1
    return n


def triangulate_ngons(obj) -> int:
    """Triangulate the faces with more than 4 vertices; winding is kept."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons, quad_method='BEAUTY', ngon_method='BEAUTY')
        bm.to_mesh(obj.data)
        obj.data.update()
    bm.free()
    return len(ngons)


def prepare_for_export(mesh_objs) -> dict:
    """Apply transforms and triangulate n-gons. The only step that edits meshes."""
    objs = [o for o in mesh_objs if o.type == 'MESH']
    return {'transforms_applied': apply_transforms(objs),
            'ngons_triangulated': sum(triangulate_ngons(o) for o in objs)}


# ---------------------------------------------------------------- per object
def _shell_volumes(bm) -> list[tuple[float, tuple, tuple]]:
    """Signed volume of every closed connected shell (negative = inward normals)."""
    seen, vols = set(), []
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        stack, comp, closed = [f0], [], True
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            comp.append(f)
            for e in f.edges:
                if len(e.link_faces) != 2:
                    closed = False
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        if not closed:
            continue
        vol = 0.0
        pts = []
        for f in comp:
            co = [v.co for v in f.verts]
            pts += co
            a = co[0]
            for k in range(1, len(co) - 1):
                vol += a.dot(co[k].cross(co[k + 1]))
        lo = tuple(min(p[i] for p in pts) for i in range(3))
        hi = tuple(max(p[i] for p in pts) for i in range(3))
        vols.append((vol / 6.0, lo, hi))
    return vols


def _inverted(shells) -> tuple[int, int]:
    """(inverted shells, cavities): a closed shell with negative volume is a
    cavity - a room enclosed by masonry, faces pointing into it - when it lies
    inside a positive shell of the same object (bounding boxes, 1 mm
    tolerance); otherwise it is an inverted shell."""
    inv = cav = 0
    pos = [(lo, hi) for v, lo, hi in shells if v > 1e-9]
    for v, lo, hi in shells:
        if v >= -1e-9:
            continue
        inside = any(all(plo[i] - 1e-3 <= lo[i] and hi[i] <= phi[i] + 1e-3 for i in range(3)) for plo, phi in pos)
        if inside:
            cav += 1
        else:
            inv += 1
    return inv, cav


def stats(obj) -> dict:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.index_update()
    slivers = zero = 0
    for f in bm.faces:
        a = f.calc_area()
        if a < 1e-9:
            zero += 1
        elif 2 * a / max(e.calc_length() for e in f.edges) < SLIVER_H:
            slivers += 1
    vols = _shell_volumes(bm)
    inv, cav = _inverted(vols)
    me = obj.data
    res = {
        'faces': len(bm.faces),
        'tris_equiv': sum(len(f.verts) - 2 for f in bm.faces),
        'ngons': sum(1 for f in bm.faces if len(f.verts) > 4),
        'nonmanifold_edges': sum(1 for e in bm.edges if not e.is_manifold),
        'nonmanifold_verts': sum(1 for v in bm.verts if not v.is_manifold),
        'loose_verts': sum(1 for v in bm.verts if not v.link_faces),
        'zero_area_faces': zero,
        'slivers': slivers,
        'flipped_edges': sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous),
        'inverted_shells': inv,
        'cavities': cav,
        'shells': len(vols),
        'uv_maps': len(me.uv_layers),
        'faces_without_material': sum(1 for p in me.polygons
                                      if p.material_index >= len(me.materials) or me.materials[p.material_index] is None),
    }
    bm.free()
    return res


# ------------------------------------------------------------- between objects
def _axis_faces(mesh_objs) -> dict:
    """Axis-aligned faces of all objects as flat arrays: axis k, sign of the
    normal, plane coordinate c, 2D extents lo / hi in the other two axes,
    object index oi and polygon index pi (world = mesh coordinates here, the
    transforms being applied)."""
    cols = defaultdict(list)
    for oi, o in enumerate(mesh_objs):
        me = o.data
        n = len(me.polygons)
        if not n:
            continue
        nor = np.empty(n * 3)
        me.polygons.foreach_get('normal', nor)
        nor = nor.reshape(n, 3)
        ls = np.empty(n, dtype=np.int64)
        me.polygons.foreach_get('loop_start', ls)
        vi = np.empty(len(me.loops), dtype=np.int64)
        me.loops.foreach_get('vertex_index', vi)
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get('co', co)
        lco = co.reshape(-1, 3)[vi]                       # one row per loop
        lo, hi = np.minimum.reduceat(lco, ls), np.maximum.reduceat(lco, ls)
        ax = np.abs(nor).argmax(1)
        sel = np.nonzero(np.abs(nor[np.arange(n), ax]) > 0.9999)[0]
        for k in range(3):
            f = sel[ax[sel] == k]
            other = [i for i in range(3) if i != k]
            cols['k'].append(np.full(len(f), k))
            cols['sign'].append(np.where(nor[f, k] > 0, 1, -1))
            cols['c'].append((lo[f, k] + hi[f, k]) / 2)
            cols['lo'].append(lo[f][:, other])
            cols['hi'].append(hi[f][:, other])
            cols['oi'].append(np.full(len(f), oi))
            cols['pi'].append(f)
    return {key: np.concatenate(v) for key, v in cols.items()}


def _poly2d(obj, pi: int, k: int):
    me = obj.data
    pts = np.array([me.vertices[v].co[:] for v in me.polygons[pi].vertices])
    return pts[:, [i for i in range(3) if i != k]]


def _area(poly) -> float:
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _clip_area(a, b) -> float:
    """Overlap area of two convex polygons (Sutherland-Hodgman)."""
    a = a if _area(a) > 0 else a[::-1]
    b = b if _area(b) > 0 else b[::-1]
    out = [tuple(p) for p in a]
    for i in range(len(b)):
        p0, p1 = b[i], b[(i + 1) % len(b)]
        inp, out = out, []
        if not inp:
            return 0.0

        def side(q):
            return (p1[0] - p0[0]) * (q[1] - p0[1]) - (p1[1] - p0[1]) * (q[0] - p0[0])
        for j in range(len(inp)):
            q, r = inp[j], inp[(j + 1) % len(inp)]
            sq, sr = side(q), side(r)
            if sq >= 0:
                out.append(q)
            if (sq >= 0) != (sr >= 0):
                t = sq / (sq - sr)
                out.append((q[0] + t * (r[0] - q[0]), q[1] + t * (r[1] - q[1])))
    return abs(_area(np.array(out))) if len(out) >= 3 else 0.0


def cross_object(mesh_objs, coplanar_tol: float = COPLANAR_TOL, contact_tol: float = CONTACT_TOL,
                 min_area: float = MIN_AREA) -> list[str]:
    """Coplanar same-facing overlaps (zfight) and facing faces that miss contact
    by less than contact_tol (contact) between different objects."""
    objs = [o for o in mesh_objs if o.type == 'MESH']
    F = _axis_faces(objs)
    if not len(F.get('c', ())):
        return []
    acc = defaultdict(float)
    polys = {}

    def poly(i):
        if i not in polys:
            polys[i] = _poly2d(objs[F['oi'][i]], int(F['pi'][i]), int(F['k'][i]))
        return polys[i]

    for k in range(3):
        idx = {sg: np.nonzero((F['k'] == k) & (F['sign'] == sg))[0] for sg in (1, -1)}
        # same-facing pairs within coplanar_tol; +k faces against -k faces within contact_tol
        for kind, A, B, tol, dmin in (('zfight', idx[1], idx[1], coplanar_tol, 0.0),
                                      ('zfight', idx[-1], idx[-1], coplanar_tol, 0.0),
                                      ('contact', idx[1], idx[-1], contact_tol, 1e-5)):
            if not len(A) or not len(B):
                continue
            A = A[np.argsort(F['c'][A])]
            B = B[np.argsort(F['c'][B])]
            cb = F['c'][B]
            # one group of A per plane (coordinates equal to 1 micron)
            cuts = np.nonzero(np.diff(np.round(F['c'][A], 6)))[0] + 1
            for g in np.split(A, cuts):
                c = F['c'][g[0]]
                j0 = np.searchsorted(cb, c - tol - 1e-6)
                j1 = np.searchsorted(cb, c + tol + 1e-6, 'right')
                if j0 == j1:
                    continue
                Bj = B[j0:j1]
                for s in range(0, len(g), 256):
                    ga = g[s:s + 256]
                    ov = (np.minimum(F['hi'][ga][:, None], F['hi'][Bj][None])
                          - np.maximum(F['lo'][ga][:, None], F['lo'][Bj][None]) > 1e-6).all(-1)
                    oa, ob = F['oi'][ga][:, None], F['oi'][Bj][None]
                    ov &= (ob > oa) if kind == 'zfight' else (ob != oa)
                    d = F['c'][Bj][None] - F['c'][ga][:, None]
                    ov &= (np.abs(d) >= dmin) & (np.abs(d) <= tol)
                    for ia, jb in zip(*np.nonzero(ov)):
                        fa, fb = ga[ia], Bj[jb]
                        area = _clip_area(poly(fa), poly(fb))
                        if area <= 1e-8:
                            continue
                        a, b = sorted((objs[F['oi'][fa]].name, objs[F['oi'][fb]].name))
                        acc[(kind, a, b, 'xyz'[k], round(float(c), 3), round(float(d[ia, jb]) * 1000, 2))] += area
    out = []
    for (kind, a, b, ax, c, dmm), area in sorted(acc.items(), key=lambda kv: -kv[1]):
        if area < min_area:
            continue
        if kind == 'zfight':
            out.append(f"zfight {a} / {b}: {area:.3f} m2 coplanar, same facing, at {ax} = {c}")
        else:
            what = 'gap' if dmm > 0 else 'overlap'
            out.append(f"contact {a} / {b}: {what} {abs(dmm):.2f} mm over {area:.3f} m2 at {ax} = {c}")
    return out


# --------------------------------------------------------------------- report
def check_scene(mesh_objs, triangulate: bool = False, for_export: bool = False,
                cross: bool = False) -> dict:
    """Report on the scene without changing it.

    triangulate=True first runs prepare_for_export() (the old behaviour of this
    function) and records what it changed; for_export=True also counts n-gons
    left over as problems. cross=True adds the between-object warnings
    (cross_object, a few seconds on the whole model; build.py turns it on)."""
    objs = [o for o in mesh_objs if o.type == 'MESH']
    report = {'objects': 0, 'tris': 0, 'ngons': 0, 'ngons_fixed': 0, 'slivers': 0,
              'problems': [], 'warnings': []}
    if triangulate:
        prep = prepare_for_export(objs)
        report['ngons_fixed'] = prep['ngons_triangulated']
        report['transforms_applied'] = prep['transforms_applied']
    for o in objs:
        report['objects'] += 1
        s = stats(o)
        report['tris'] += s['tris_equiv']
        report['ngons'] += s['ngons']
        report['slivers'] += s['slivers']
        P = report['problems']
        if not MESH_RE.match(o.name):
            P.append(f"{o.name}: mesh name does not follow SM_Asset_Variant")
        for m in o.data.materials:
            if m is not None and not MAT_RE.match(m.name):
                P.append(f"{o.name}: material {m.name} does not follow M_Name")
        if not o.matrix_world.is_identity:
            P.append(f"{o.name}: unapplied transform")
        keys = ['nonmanifold_edges', 'nonmanifold_verts', 'loose_verts', 'zero_area_faces',
                'flipped_edges', 'inverted_shells', 'faces_without_material']
        if for_export:
            keys.append('ngons')
        for k in keys:
            if s[k]:
                P.append(f"{o.name}: {k} = {s[k]}")
        if not s['uv_maps']:
            P.append(f"{o.name}: no UV map")
    if cross:
        report['warnings'] = cross_object(objs)
    return report
