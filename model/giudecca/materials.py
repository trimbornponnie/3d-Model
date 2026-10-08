"""PBR materials (Principled BSDF) named per the skill's convention (M_ prefix).

Colours are given in sRGB 0-255 and converted to linear. Only base colour,
metallic and roughness are used so the materials survive glTF/FBX export
unchanged; a procedural brick bond is layered on top for Blender renders only.
"""
from __future__ import annotations

import bpy

PALETTE = {
    # name: (sRGB, metallic, roughness)
    'M_Brick': ((156, 84, 62), 0.0, 0.85),        # Venetian face brick ("mattoni a faccia vista")
    'M_Concrete': ((196, 191, 180), 0.0, 0.75),   # exposed concrete copings, bands, lintels, sills
    'M_Copper': ((112, 78, 58), 0.55, 0.45),      # copper sheet roofs ("manto in lamina di rame")
    'M_Glass': ((38, 48, 54), 0.0, 0.08),
    'M_Frame': ((52, 62, 58), 0.2, 0.5),          # painted window frames / railings
    'M_Paving': ((166, 160, 148), 0.0, 0.9),      # trachyte / stone paving
    'M_Ground': ((134, 128, 116), 0.0, 0.95),
    'M_Grass': ((92, 116, 64), 0.0, 1.0),
    'M_Water': ((44, 76, 84), 0.0, 0.06),
    'M_Plaster': ((214, 204, 186), 0.0, 0.9),     # rendered walls ("intonaco")
}


def _lin(c: int) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def make_materials(brick_procedural: bool = True) -> dict[str, bpy.types.Material]:
    mats = {}
    for name, (rgb, metal, rough) in PALETTE.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes.get('Principled BSDF')
        col = tuple(_lin(c) for c in rgb) + (1.0,)
        bsdf.inputs['Base Color'].default_value = col
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = rough
        m.diffuse_color = col
        if name == 'M_Brick' and brick_procedural:
            _brick_nodes(nt, bsdf, col)
        mats[name] = m
    return mats


def _brick_nodes(nt, bsdf, col) -> None:
    """Brick bond at real scale (course 7.0 cm incl. joint, SE 59; brick ~26 cm),
    driven by the world-scale box-projected UVs from geo.world_box_uv
    (1 UV unit = 1 m, uniform texel density). Render-only."""
    tex = nt.nodes.new('ShaderNodeTexBrick')
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    tex.inputs['Scale'].default_value = 1.0
    tex.inputs['Brick Width'].default_value = 0.26
    tex.inputs['Row Height'].default_value = 0.07
    tex.inputs['Mortar Size'].default_value = 0.008
    tex.offset = 0.5
    c1 = col
    c2 = tuple(min(1.0, v * 1.18) for v in col[:3]) + (1.0,)
    tex.inputs['Color1'].default_value = c1
    tex.inputs['Color2'].default_value = c2
    tex.inputs['Mortar'].default_value = (0.55, 0.52, 0.47, 1.0)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
