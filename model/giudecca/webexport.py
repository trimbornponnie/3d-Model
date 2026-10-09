"""Web export for the browser viewer: one Draco-compressed glTF per part
(site, towers, carpet, schiera), each written as a .json glTF with its
geometry in an embedded data-URI buffer and its textures as separate JPEG
files shared by all parts (hosts that serve .json / .jpg but not .glb, and
keep every file small). The full-quality GLB / FBX / OBJ come from build.py.
"""
from __future__ import annotations

import base64
import json
import os
import struct

import bpy

PARTS = {'site': 'SM_Site_', 'towers': 'SM_Tower_', 'carpet': 'SM_Carpet_', 'schiera': 'SM_Schiera_',
         'misc': 'SM_Joinery_'}


def _glb_to_json(glb_path: str, json_path: str, img_dir: str) -> dict:
    b = open(glb_path, 'rb').read()
    jlen = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + jlen])
    o = 20 + jlen
    blen = struct.unpack('<I', b[o:o + 4])[0]
    bin_ = b[o + 8:o + 8 + blen]
    img_views = {}
    for im in j.get('images', []):
        bv = j['bufferViews'][im['bufferView']]
        data = bin_[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]
        ext = '.jpg' if im.get('mimeType') == 'image/jpeg' else '.png'
        name = im.get('name', 'image') + ext
        p = os.path.join(img_dir, name)
        if not os.path.exists(p):
            open(p, 'wb').write(data)
        img_views[im['bufferView']] = name
        del im['bufferView']
        im.pop('mimeType', None)
        im['uri'] = name
    views, remap, buf = [], {}, bytearray()
    for i, bv in enumerate(j['bufferViews']):
        if i in img_views:
            continue
        data = bin_[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]
        while len(buf) % 4:
            buf.append(0)
        nbv = dict(bv, byteOffset=len(buf))
        buf += data
        remap[i] = len(views)
        views.append(nbv)
    j['bufferViews'] = views
    for acc in j.get('accessors', []):
        if 'bufferView' in acc:
            acc['bufferView'] = remap[acc['bufferView']]
    for ext in ('KHR_draco_mesh_compression',):
        for mesh in j.get('meshes', []):
            for prim in mesh.get('primitives', []):
                d = prim.get('extensions', {}).get(ext)
                if d and 'bufferView' in d:
                    d['bufferView'] = remap[d['bufferView']]
    j['buffers'] = [{'byteLength': len(buf),
                     'uri': 'data:application/octet-stream;base64,' + base64.b64encode(bytes(buf)).decode()}]
    json.dump(j, open(json_path, 'w'), separators=(',', ':'))
    return {'json': json_path, 'bytes': os.path.getsize(json_path), 'images': [im['uri'] for im in j.get('images', [])]}


def export(objs, out_dir: str) -> dict:
    """Write <out_dir>/gq-<part>.json (+ shared T_*.jpg) for the given mesh objects."""
    os.makedirs(out_dir, exist_ok=True)
    res = {}
    for part, prefix in PARTS.items():
        sel = [o for o in objs if o.name.startswith(prefix)]
        if not sel:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in sel:
            o.select_set(True)
        bpy.context.view_layer.objects.active = sel[0]
        glb = os.path.join(out_dir, f'_gq-{part}.glb')
        bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True, export_apply=True,
                                  export_yup=True, export_image_format='JPEG', export_image_quality=82,
                                  export_draco_mesh_compression_enable=True,
                                  export_draco_mesh_compression_level=6,
                                  export_draco_position_quantization=14,
                                  export_draco_normal_quantization=10,
                                  export_draco_texcoord_quantization=12)
        res[part] = _glb_to_json(glb, os.path.join(out_dir, f'gq-{part}.json'), out_dir)
        os.remove(glb)
    return res
