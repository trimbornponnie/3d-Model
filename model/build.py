"""Build the 3D model of Gino Valle's IACP housing on the Giudecca (1984-85).

Usage (Blender as a Python module, Python 3.11, `pip install bpy==5.0.1`):

    python model/build.py                       # everything, export to model/output
    python model/build.py --only towers carpet  # selected parts
    python model/build.py --render              # also write preview renders
    python model/build.py --no-export --render --out /tmp/x

or inside Blender:  blender -b -P model/build.py -- --render

Specification: docs/ANALYSIS.md; numbers: model/giudecca/params.py.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

from giudecca import geo, materials, render, validate  # noqa: E402
from giudecca.common import Ctx  # noqa: E402

PARTS = ('site', 'towers', 'carpet', 'schiera')
THROUGH = 0.70          # depth of the window / door cutters with interiors: through any wall (max 0.395 + reveals)


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*', default=list(PARTS), choices=PARTS)
    ap.add_argument('--out', default=os.path.join(HERE, 'output'))
    ap.add_argument('--no-export', action='store_true')
    ap.add_argument('--render', action='store_true')
    ap.add_argument('--interiors', action='store_true',
                    help='interiors, construction layers and joinery (work in progress)')
    ap.add_argument('--views', nargs='*', default=None)
    ap.add_argument('--samples', type=int, default=48)
    ap.add_argument('--res', type=int, nargs=2, default=(1600, 1000))
    return ap.parse_args(argv)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'      # skill: model at real scale, 1 unit = 1 m
    s.unit_settings.scale_length = 1.0


def mesh_objects(ctx):
    """The exportable meshes: everything but the boolean cutters."""
    return [o for o in bpy.data.objects
            if o.type == 'MESH' and not o.name.startswith('CUT_')
            and ctx.cutters.name not in [c.name for c in o.users_collection]]


def export(ctx, out_dir: str, name: str = 'SM_Giudecca_IACP_Valle'):
    os.makedirs(out_dir, exist_ok=True)
    objs = mesh_objects(ctx)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    paths = {}
    p = os.path.join(out_dir, f'{name}.glb')
    # the T_*_D images are packed (embedded in the GLB and FBX) and also written
    # to out_dir by make_materials(texture_dir=out_dir), where the OBJ's MTL finds them
    bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', use_selection=True,
                              export_apply=True, export_yup=True)
    paths['glb'] = p
    p = os.path.join(out_dir, f'{name}.fbx')
    bpy.ops.export_scene.fbx(filepath=p, use_selection=True, apply_scale_options='FBX_SCALE_ALL',
                             apply_unit_scale=True, use_mesh_modifiers=True, axis_forward='-Z', axis_up='Y',
                             path_mode='COPY', embed_textures=True)
    paths['fbx'] = p
    p = os.path.join(out_dir, f'{name}.obj')
    bpy.ops.wm.obj_export(filepath=p, export_selected_objects=True, export_materials=True,
                          path_mode='STRIP')
    paths['obj'] = p
    return paths


def main():
    args = parse_args()
    t0 = time.time()
    reset_scene()
    mats = materials.make_materials(texture_dir=None if args.no_export else args.out)
    root = geo.collection('COL_Giudecca')
    ctx = Ctx(mats=mats, root=root, cutters=geo.collection('Cutters', hide=True))
    timings = {}
    interiors = args.interiors
    geo.OPENINGS.clear()
    # with interiors, windows and doors are cut right through the walls and the
    # joinery glazes them (geo.THROUGH); the bodies are hollowed afterwards
    geo.THROUGH = THROUGH if interiors else None
    for part in PARTS:
        if part not in args.only:
            continue
        t = time.time()
        mod = importlib.import_module(f'giudecca.{part}')
        mod.build(ctx)
        if interiors and importlib.util.find_spec(f'giudecca.interior_{part}') is not None:
            importlib.import_module(f'giudecca.interior_{part}').build(ctx)
        timings[part] = round(time.time() - t, 1)
        print(f'[build] {part}: {timings[part]} s')
    if interiors and importlib.util.find_spec('giudecca.joinery') is not None:
        t = time.time()
        importlib.import_module('giudecca.joinery').build(ctx)
        timings['joinery'] = round(time.time() - t, 1)
        print(f"[build] joinery: {timings['joinery']} s ({len(geo.OPENINGS)} openings)")
    n_cut = geo.rename_cutters(ctx.cutters)          # SM_..._Cut -> CUT_..., kept hidden, never exported
    objs = mesh_objects(ctx)
    for o in objs:
        geo.world_box_uv(o)
    prep = validate.prepare_for_export(objs)          # the only step that edits the meshes
    prep['cutters_renamed'] = n_cut
    print('[prepare]', json.dumps(prep))
    report = validate.check_scene(objs, for_export=True, cross=True)     # read-only
    report['prepared'] = prep
    report['timings_s'] = timings
    report['parts'] = args.only
    print('[validate]', json.dumps({k: v for k, v in report.items() if k not in ('problems', 'warnings')}))
    for p in report['problems'][:40]:
        print('[problem]', p)
    print(f"[warnings] {len(report['warnings'])} between objects (zfight / contact), listed in build_report.json")
    for w in report['warnings'][:12]:
        print('[warning]', w)
    os.makedirs(args.out, exist_ok=True)
    if not args.no_export:
        report['files'] = export(ctx, args.out)
    if args.render:
        report['renders'] = render.render_views(args.out, args.views, tuple(args.res), args.samples)
    if not args.no_export:
        p = os.path.join(args.out, 'SM_Giudecca_IACP_Valle.blend')
        bpy.ops.wm.save_as_mainfile(filepath=p, compress=True)
        report['files']['blend'] = p
    report['total_s'] = round(time.time() - t0, 1)
    with open(os.path.join(args.out, 'build_report.json'), 'w') as f:
        json.dump(report, f, indent=1)
    print('[done]', report['total_s'], 's')


if __name__ == '__main__':
    main()
