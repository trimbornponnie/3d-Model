"""Preview renders (Cycles, CPU) from viewpoints matching the source material,
so the model can be compared side by side with the drawings and model photos."""
from __future__ import annotations

import math

import bpy
from mathutils import Vector

# name: (camera location, look-at target, lens mm, ortho_scale or None[, hidden name prefixes])
VIEWS = {
    # like the 1:200 axonometric n39 / n71: from the south-west, high
    'axo_sw': ((-95.0, -95.0, 85.0), (2.0, 4.0, 2.0), None, 136.0),
    # like the white study-model photo n81: from the east, high oblique
    'model_east': ((115.0, -18.0, 62.0), (0.0, 2.0, 0.0), 32.0, None),
    # north façade (n16 / n59 d4), frontal, orthographic
    # site ground, water and garden are hidden so the ortho view reads like the 1:50 elevation
    # (camera north of the NE tower's water stair, which reaches y 33.46)
    'north_elev': ((0.0, 40.0, 6.5), (0.0, 0.0, 6.5), None, 126.0,
                   ('SM_Site_Plate', 'SM_Site_Water', 'SM_Site_Banks', 'SM_Site_Tree', 'SM_Site_Garden',
                    'SM_Site_Mooring', 'SM_Site_Bridge')),
    # bird's-eye straight down (compare with plans n33/n34/n70)
    'top': ((0.0, 0.0, 150.0), (0.0, 0.0, 0.0), None, 132.0),
    # eye level in the campo looking north to the gallery
    'campo': ((-1.5, 6.0, 1.7), (-1.5, 30.0, 6.0), 18.0, None),
}

# Interior and cutaway views of the --interiors build (docs/INTERIORS.md). Options: a point
# lamp (W) at the camera for rooms lit only through their windows; 'cut': the orthographic
# camera sits in the cutting plane itself (geometry in front of it is behind the camera) and
# nothing casts shadows, so the storey or section reads like a plan / section drawing.
INTERIOR_VIEWS = {
    # tower E0, L3 living room of the duplex looking to the hall and the stair
    'int_tower_living': ((57.09, 31.20, 10.2), (53.955, 28.70, 10.4), 16.0, None, (), {'lamp': 150}),
    # tower E0, L2 hall of the duplex with the private flight
    'int_tower_stair': ((54.12, 29.60, 7.6), (53.46, 24.90, 7.2), 16.0, None, (), {'lamp': 150}),
    # north row house 20.5, L3 living room under the tiled roof
    'int_north_living': ((21.6, 25.2, 10.6), (25.0, 21.4, 10.9), 16.0, None, (), {'lamp': 150}),
    # north row house 20.5, the stair from the L1 landing
    'int_north_stair': ((25.2, 21.75, 4.4), (25.2, 17.8, 5.9), 14.0, None, (), {'lamp': 150}),
    # middle row house 20.5, L2 hall under the copper vault with the terrace door
    'int_middle_hall': ((24.275, 5.115, 8.0), (24.375, 10.395, 7.0), 14.0, None, (), {'lamp': 150}),
    # south row house 20.5, L0 lobby and stair
    'int_south_lobby': ((24.275, -5.775, 1.6), (24.575, -1.65, 1.0), 14.0, None, (), {'lamp': 150}),
    # schiera block 35.5, L0 living room with the flight
    'int_schiera_living': ((2.6, -23.3, 1.5), (0.6, -26.6, 1.9), 16.0, None, (), {'lamp': 150}),
    # cutaway plans of the three carpet rows at house 20.5 (cut 1.5 m above the floor)
    'cut_carpet_L1': ((25.575, 3.0, 4.51), (25.575, 3.0, 0.0), None, 56.0, ('SM_Site_Tree',), {'cut': True}),
    'cut_carpet_L3': ((25.575, 3.0, 10.52), (25.575, 3.0, 0.0), None, 56.0, ('SM_Site_Tree',), {'cut': True}),
    # cutaway plan of tower E0 at L2
    'cut_tower_L2': ((56.5, 26.4, 7.52), (56.5, 26.4, 0.0), None, 16.0, (), {'cut': True}),
    # north-south section through the rooms of the west dwellings of house 20.5 (1.5 m west of
    # the house axis), seen from the east
    'cut_section_house': ((24.075, 2.0, 5.0), (0.0, 2.0, 5.0), None, 34.0, ('SM_Site_Tree',), {'cut': True}),
}
VIEWS.update(INTERIOR_VIEWS)


def _look_at(cam: bpy.types.Object, target: Vector) -> None:
    d = target - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def setup_world(strength: float = 1.0) -> None:
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new('World')
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (0.78, 0.84, 0.92, 1.0)
    bg.inputs['Strength'].default_value = 0.6 * strength
    if 'SUN_Key' not in bpy.data.objects:
        sun = bpy.data.lights.new('SUN_Key', 'SUN')
        sun.energy = 3.2
        sun.angle = math.radians(1.5)
        o = bpy.data.objects.new('SUN_Key', sun)
        scene.collection.objects.link(o)
        # Venice, early afternoon: sun from the south-south-west (azimuth 200°), 45° high;
        # a sun lamp shines along its -Z, so Z rotation = 180° - azimuth
        o.rotation_euler = (math.radians(45), 0.0, math.radians(180 - 200))


def render_views(out_dir: str, views=None, res=(1600, 1000), samples: int = 48) -> list[str]:
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX' if 'AgX' in [
        i.identifier for i in scene.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
    setup_world()
    paths = []
    for name in (views or VIEWS):
        loc, tgt, lens, ortho = VIEWS[name][:4]
        hide = VIEWS[name][4] if len(VIEWS[name]) > 4 else ()
        opts = VIEWS[name][5] if len(VIEWS[name]) > 5 else {}
        hidden = [o for o in bpy.data.objects if any(o.name.startswith(h) for h in hide)]
        for o in hidden:
            o.hide_render = True
        cd = bpy.data.cameras.get(f'CAM_{name}') or bpy.data.cameras.new(f'CAM_{name}')
        cam = bpy.data.objects.get(f'CAM_{name}') or bpy.data.objects.new(f'CAM_{name}', cd)
        if cam.name not in scene.collection.objects:
            scene.collection.objects.link(cam)
        cam.location = Vector(loc)
        _look_at(cam, Vector(tgt))
        if ortho:
            cd.type = 'ORTHO'
            cd.ortho_scale = ortho
        else:
            cd.type = 'PERSP'
            cd.lens = lens
        cd.clip_end = 2000
        cd.clip_start = 0.001 if opts.get('cut') else 0.1
        scene.camera = cam
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        if opts.get('cut'):
            for o in meshes:
                o.visible_shadow = False
        lamp = bpy.data.objects.get('LAMP_Interior')
        if lamp is None:
            lamp = bpy.data.objects.new('LAMP_Interior', bpy.data.lights.new('LAMP_Interior', 'POINT'))
            lamp.data.shadow_soft_size = 0.3
            scene.collection.objects.link(lamp)
        lamp.data.energy = float(opts.get('lamp', 0.0))
        lamp.location = Vector(loc) + Vector((0.0, 0.0, 0.3))
        lamp.hide_render = not opts.get('lamp')
        path = f'{out_dir}/{name}.png'
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        for o in hidden:
            o.hide_render = False
        for o in meshes:
            o.visible_shadow = True
        paths.append(path)
    return paths
