"""PBR materials (Principled BSDF) named per the skill's convention (M_ prefix).

This module owns every M_ material of the model: the part modules look them up
in ctx.mats and never create their own. Colours are given in sRGB 0-255 and
converted to linear. Only base colour, metallic and roughness are used, so the
materials survive glTF / FBX / OBJ export unchanged. Brick and roof tiles get a
generated base-colour image (textures.py, 1 m x 1 m on the world-scale box UVs
of geo.world_box_uv): an image texture is exported to every format, unlike a
procedural node, which glTF drops (the GLB then shows the material white).

Every shell of the model is closed and outward-facing, so the materials use
backface culling: the GLB is written single-sided (doubleSided false) and a
flipped normal shows up in any viewer instead of being hidden.
"""
from __future__ import annotations

import bpy

from . import textures

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
    'M_RoofTile': ((164, 86, 62), 0.0, 0.8),      # clay tiles ("tegole", SE 54)
    'M_Stone': ((222, 216, 202), 0.0, 0.7),       # Istrian stone copings, steps, grid lines
    'M_Foliage': ((74, 98, 50), 0.0, 0.95),
    'M_Bark': ((86, 70, 56), 0.0, 0.9),
    'M_Wood': ((112, 94, 74), 0.0, 0.85),         # weathered oak mooring poles
    # interiors and construction layers (docs/INTERIORS.md)
    'M_Parquet': ((176, 128, 82), 0.0, 0.45),     # oak herringbone parquet (interior floor finish)
    'M_PlasterInt': ((236, 232, 224), 0.0, 0.9),  # interior lime plaster, painted
    'M_Insulation': ((222, 200, 118), 0.0, 1.0),  # thermal / acoustic insulation
    'M_Screed': ((172, 168, 160), 0.0, 0.95),     # cement screed ("massetto")
    'M_Structure': ((150, 148, 142), 0.0, 0.9),   # reinforced concrete / laterocemento slabs, ring beams
    'M_HollowBrick': ((186, 110, 82), 0.0, 0.9),  # hollow clay blocks ("laterizio forato"), partitions
    'M_Membrane': ((40, 40, 42), 0.0, 0.6),       # bituminous waterproofing / vapour barrier
    'M_DoorLeaf': ((168, 132, 92), 0.0, 0.55),    # interior door leaves (wood)
    'M_DoorFrame': ((150, 116, 80), 0.0, 0.55),   # interior door casings and architraves
    'M_StairTread': ((214, 206, 190), 0.0, 0.5),  # stair treads and landings
    'M_Steel': ((58, 60, 62), 0.6, 0.4),          # handrails, balustrades
}

# material -> generator of its base-colour image (T_<Asset>_D, textures.py)
TEXTURES = {'M_Brick': textures.brick, 'M_RoofTile': textures.roof_tile, 'M_Parquet': textures.parquet}


def srgb_to_linear(c: int) -> float:
    """One sRGB channel 0-255 -> linear 0-1."""
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


_lin = srgb_to_linear          # old private name


def linear_rgba(rgb) -> tuple[float, float, float, float]:
    return tuple(srgb_to_linear(c) for c in rgb) + (1.0,)


def make_materials(textured: bool = True, texture_dir: str | None = None) -> dict[str, bpy.types.Material]:
    """Create (or update) every material of PALETTE.

    textured: drive M_Brick and M_RoofTile's Base Color with their generated
    images (packed into the .blend and embedded in the GLB); False gives the
    plain colour only. texture_dir: also write the images there as PNG, so
    that FBX / OBJ exported to that folder can reference them."""
    mats = {}
    for name, (rgb, metal, rough) in PALETTE.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes.get('Principled BSDF')
        col = linear_rgba(rgb)
        bsdf.inputs['Base Color'].default_value = col     # also the FBX / OBJ diffuse colour (Kd)
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = rough
        m.diffuse_color = col
        m.use_backface_culling = True
        if textured and name in TEXTURES:
            textures.attach(m, TEXTURES[name](texture_dir))
        mats[name] = m
    return mats
