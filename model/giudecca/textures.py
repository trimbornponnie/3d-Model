"""Tileable base-colour textures generated in Blender (no external assets).

Each image covers exactly 1 m x 1 m, matching the world-scale box UVs from
geo.world_box_uv (1 UV unit = 1 m), so texel density is identical on every
object (skill: uv-unwrapping-strategy). Sizes are powers of two and names
follow the skill's convention: T_<Asset>_D (diffuse / base colour).

- T_Brick_D: Venetian face brick in running bond, 4 bricks per metre (25 cm
  incl. joint, SE 50 uses 26) and 14 courses per metre (7.1 cm, SE 59 measures
  7.0), lime mortar joints ~8 mm.
- T_RoofTile_D: clay tiles ("tegole", SE 54), 5 per metre across the slope and
  3 courses per metre down it, shaded at each course's lower edge.
"""
from __future__ import annotations

import os

import bpy
import numpy as np

SIZE = 1024


def _srgb(c):
    return np.asarray(c, dtype=np.float32) / 255.0


def _save(name: str, rgb: np.ndarray, out_dir: str | None) -> bpy.types.Image:
    img = bpy.data.images.get(name) or bpy.data.images.new(name, SIZE, SIZE, alpha=False)
    img.colorspace_settings.name = 'sRGB'   # set first: changing it later regenerates the buffer
    rgba = np.ones((SIZE, SIZE, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(rgb, 0, 1)
    img.pixels.foreach_set(rgba.ravel())
    img.update()                   # without this, save() writes the empty generated buffer
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        img.filepath_raw = os.path.join(out_dir, f'{name}.png')
        img.file_format = 'PNG'
        img.save()
    img.pack()                     # embed in the .blend and in the GLB
    return img


def brick(out_dir: str | None = None, seed: int = 7) -> bpy.types.Image:
    rng = np.random.default_rng(seed)
    n_courses, n_bricks = 14, 4
    ch, bw = SIZE / n_courses, SIZE / n_bricks
    joint = 8.0 / 1000.0 * SIZE                      # ~8 mm at 1 m = 1024 px
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    course = np.floor(y / ch).astype(int)
    xs = (x + (course % 2) * bw / 2.0) % SIZE        # running bond: half-brick offset
    col = np.floor(xs / bw).astype(int)
    in_joint = ((y % ch) < joint) | ((xs % bw) < joint)
    base = _srgb((156, 84, 62))
    # firing variation: mostly brightness, plus a small correlated warm/cool shift
    warm = rng.normal(0.0, 0.03, size=(n_courses, n_bricks, 1)).astype(np.float32)
    tint = warm * np.array([1.0, 0.55, 0.35], dtype=np.float32)
    tone = rng.normal(1.0, 0.09, size=(n_courses, n_bricks, 1)).astype(np.float32)
    rgb = (base[None, None, :] + tint[course, col]) * tone[course, col]
    rgb *= (1.0 + rng.normal(0.0, 0.035, size=(SIZE, SIZE, 1)).astype(np.float32))  # fired-clay grain
    mortar = _srgb((178, 170, 156)) * (1.0 + rng.normal(0.0, 0.03, size=(SIZE, SIZE, 1)).astype(np.float32))
    rgb = np.where(in_joint[..., None], mortar, rgb)
    return _save('T_Brick_D', rgb, out_dir)


def roof_tile(out_dir: str | None = None, seed: int = 11) -> bpy.types.Image:
    rng = np.random.default_rng(seed)
    n_rows, n_cols = 3, 5
    rh, cw = SIZE / n_rows, SIZE / n_cols
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    row = np.floor(y / rh).astype(int)
    xs = (x + (row % 2) * cw / 2.0) % SIZE
    col = np.floor(xs / cw).astype(int)
    fy = (y % rh) / rh                                # 0 at course edge -> 1 at next
    fx = (xs % cw) / cw
    base = _srgb((164, 86, 62))
    tone = rng.normal(1.0, 0.07, size=(n_rows, n_cols, 1)).astype(np.float32)
    rgb = base[None, None, :] * tone[row, col]
    rgb *= (0.78 + 0.22 * np.sqrt(np.clip(fy, 0, 1)))[..., None]       # shadow under the overlapping course
    rgb *= (0.90 + 0.10 * np.sin(np.pi * fx))[..., None]               # tile camber
    rgb *= (1.0 + rng.normal(0.0, 0.03, size=(SIZE, SIZE, 1)).astype(np.float32))
    return _save('T_RoofTile_D', rgb, out_dir)


def attach(mat: bpy.types.Material, image: bpy.types.Image) -> None:
    """Drive the material's Base Color with `image` through the UV map, replacing
    any procedural node so the colour survives glTF / FBX / OBJ export."""
    nt = mat.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    for link in list(bsdf.inputs['Base Color'].links):
        nt.links.remove(link)
    for node in [n for n in nt.nodes if n.type in ('TEX_BRICK', 'MAPPING', 'TEX_COORD', 'TEX_IMAGE')]:
        nt.nodes.remove(node)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.interpolation = 'Linear'
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
