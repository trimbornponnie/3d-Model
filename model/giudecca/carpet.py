"""Carpet ("tappeto") of Gino Valle's IACP housing on the Giudecca, with its campo.

Specification: docs/ANALYSIS.md sections 3 (levels, roof rule) and 5 (carpet);
numbers from params.py. Local constants that params.py does not define carry
a comment citing the drawing they were read from.

Structure (spec 5.1-5.2): three east-west rows of H-houses (north row L0-L3,
middle row L0-L2, south row L0-L1), in two blocks separated by the 0.91 m slot,
each block split into 2-house segments at the expansion joints. Per row and
segment: a north pavilion (mono-pitch roof rising north), a south pavilion
(rising south), the stair cores on the house axes with curved copper roofs, the
light courts between them; joint strips between the rows carry roof terraces.
The campo (spec 5.4) replaces the middle row of the two houses flanking the slot.

Modelling (jasonkneen-3d-modeling skill, hard-surface workflow): every element
is a closed solid at real scale; openings are exact boolean differences with
all cutters of one target collected into one hidden cutter object; overlapping
cutters are allowed (self-intersection mode of the exact solver); cleanup and
normal recalculation after every boolean; names SM_<Asset>_<Variant>_<Index>.
"""
from __future__ import annotations

import math

import bmesh
import bpy

from . import geo
from .common import (Openings, add_copings, add_pavilion, box_EY, east_face, north_face,
                     pavilion_section, poly_EY, south_face, u_on, west_face, xE, yY)
from .params import (ARCADE, BLOCKS, CAMPO, CAMPO_HOUSES, CANTINE_N, COPING_H, CORE_CROWN, CORE_EAVE,
                     CORE_PIER_OFFSET, CORRIDOR_NM, CORE_VAULT_R, CORE_W, CORE_WIN, EXT_STAIRS, FLOORS,
                     FRENCH, GALLERY, JOINTS, MODULE, NOTCH_HALF, OCULUS_PANEL, PASSAGE_M,
                     PORTICO_PIER_ROWS, ROOF_HIGH, ROOF_LOW, ROWS, SLAB, TRIFORA,
                     WALL, WALL_M, WIN_STD, Z_COURT, Z_PAVING)

M = MODULE

# ------------------------------------------------------------ local constants
Z0 = -0.50                    # building bases: 5 cm into the -0.45 paving (task rule)
GAP = 0.09                    # m, expansion joints: double walls 9 cm apart (spec 5.2; n16 chain "53 | 9 | 53")
PW = 0.37                     # m, pavilion wall used by the roof profile (common.pavilion_section)
END_WALL = 0.37               # m, block-end wall thickness (SE 50: 37 cm brick)
T_N, T_M, T_S = ROWS['N']['T'], ROWS['M']['T'], ROWS['S']['T']
Z_L1_SOFFIT = FLOORS[1] - SLAB          # 2.71 underside of the L1 slab (SE 58)
Z_L2_SOFFIT = FLOORS[2] - SLAB          # 5.72 underside of the L2 slab
CORE_HALF = CORE_W / 2                  # 2.05 m
CPIER_X = CORE_PIER_OFFSET * M          # 1.8975 m, core corner piers (spec 5.2)
CPIER_W = 0.40                          # m, corner pier width along E (n11 type-1 piers, measured)
UNDER_CORE = CPIER_X - CPIER_W / 2      # 1.6975 m, half-width of the opening under a floating core
COURT_DX = 3.30                         # m, court openings at axis +-3.30 (spec 5.5)
TWO_LIGHT = 2.13                        # m, court two-light windows (spec 5.5)
MULLION = 0.14                          # m, pier between the lights of a two-light (spec 5.5)
NN_COURT_ARCH = dict(w=2.30, spring=5.05, crown=5.52)     # north-row N-pav court arches (spec 5.5; width n59/n77)
L0_ARCH = dict(w=2.15, spring=1.95, crown=2.36, panel=2.71)  # L0 arches, "2,15" R 1.62 (n9, spec 5.5)
NM_ARCH = dict(w=2.15, spring=2.10, crown=2.51)           # middle-row N-pav court arches (n50 "2,10", R 1.62)
END_ARCH_N = dict(y=0.98, w=2.15, spring=4.85, crown=5.26, panel=5.62)   # block-end arch into the portico (n9)
END_ARCH_SPN_Y = 6.0                    # Y of the L0 end arch of the north row's S-pav band (n9)
END_ARCH_PASSAGE_Y = 14.0               # Y of the end arch of the middle-row passage (n9)
BAND_Y0 = PORTICO_PIER_ROWS[1] - WALL_M / 2   # 4.83: north face of the L0 band of the north row S-pav
NOTCH_TERRACE = FLOORS[2] + 0.13        # 6.15, middle-row notch terrace (spec 5.2)
CAMPO_SP_Z0 = Z_L2_SOFFIT               # 5.72, campo S-pav from L2 up on the pier bands (spec 5.4)
CAMPO_PARAPET = 9.97                    # top of the campo L3 terrace parapet (n47 SE 33; = tower L3 terraces)
CAMPO_PARAPET_T = 0.25                  # m, parapet thickness (n50, measured)
# Façade bands. The elevations draw 13 cm concrete bands at the heads of the
# openings, not at T+2.71 -> T+3.01 (spec 3 roof rule): n47 (SE 33) chain
# "13 | 1,48 | 13 | 2,88 | 13" under the 7.10 coping = bands 5.36-5.49 and
# 2.35-2.48; the same lines at 8.37 / 11.37 on the faces above the joints; n9 /
# n29 one band across each exposed pavilion end wall at the top-floor head; n48 /
# n59 the same bands on the court faces. As on the towers (spec 4): z_f+2.36 -> 2.49.
BAND = (2.36, 2.49)
BAND_N3 = (TRIFORA['lintel'][2] - 0.135, TRIFORA['lintel'][2] - 0.005)   # north row north pavilion L3: at the trifora lintel tops (n16, n59)
TERRACE_END_TOP = {'NM': CAMPO_PARAPET, 'MS': 6.90}   # end parapets of the joint terraces at the block ends (n9 "12" copings ~9.9 / ~6.9; n29)
SLOT_PIER = dict(leg=0.945, t=0.40, row=0.74)   # type-1 L piers at the campo slot face (n11 chain "94,5 | 2,15 | 94,5")
SLOT_ARCH = dict(w=2.15, rise=0.46)     # arch under the slot-face band of the campo pavilion (n29 SE 35: spring ~4.9, crown ~5.3)
END_BAY = ARCADE['end_pier'] + ARCADE['arch_w_short'] + ARCADE['pier'] / 2   # 3.465 m: block-end arcade bay without gallery (n16, n59)
CHIMNEY_1 = dict(w=0.40, slot_in=0.79)  # single-flue stacks at the slot / campo ends (n47: 0.79 m in from the slot faces)
SN_COURT_DOOR = 1.14                    # m, south-row N-pav court face: one French door per side at L0 (n48 SE 31)
CAMPO_SOUTH_Y = (PASSAGE_M[1], JOINTS['MS'][1])     # 15.0 -> 15.776, one-storey arcade (n49)
CAMPO_SOUTH_TOP = FLOORS[1]             # 3.01 (n49)
CHIMNEY = dict(w=0.90, d=0.45, n_top=14.0, n_corbel=10.75, m_top=10.9, m_corbel=7.75)   # spec 5.5 / 9
STAIR_SIDE_H = 0.95                     # m, height of the external-stair side walls above the pitch line (SE 64)
LOW_WALL = 1.25                         # half-court walls (spec 5.2)
LOW_WALL_T = 0.30
CORE_WIN_DY = 1.08                      # m, landing windows at the core-zone mid-line +-1.08 (spec 5.5)


def m2E(m: float) -> float:
    """Metres -> modules."""
    return m / M


# --------------------------------------------------------------- materials
def _lin(c: int) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def ensure_roof_material(ctx) -> None:
    """Clay-tile roof material ("tegole", SE 54), with a render-only tile course
    pattern driven by the world-scale UVs (1 UV unit = 1 m)."""
    if 'M_RoofTile' in ctx.mats:
        return
    m = bpy.data.materials.get('M_RoofTile') or bpy.data.materials.new('M_RoofTile')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    col = (_lin(164), _lin(86), _lin(62), 1.0)
    bsdf.inputs['Base Color'].default_value = col
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.8
    m.diffuse_color = col
    tex = nt.nodes.new('ShaderNodeTexBrick')
    coord = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(coord.outputs['UV'], tex.inputs['Vector'])
    tex.inputs['Scale'].default_value = 1.0
    tex.inputs['Brick Width'].default_value = 0.22
    tex.inputs['Row Height'].default_value = 0.30
    tex.inputs['Mortar Size'].default_value = 0.012
    tex.offset = 0.5
    tex.inputs['Color1'].default_value = col
    tex.inputs['Color2'].default_value = tuple(v * 0.88 for v in col[:3]) + (1.0,)
    tex.inputs['Mortar'].default_value = tuple(v * 0.55 for v in col[:3]) + (1.0,)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    ctx.mats['M_RoofTile'] = m


def roof_tiles(ctx, obj) -> None:
    """Clay tiles on the sloping roof planes (faces tilted 6-45 deg from horizontal)."""
    geo.assign_material_by_normal(obj, [(ctx.mats['M_RoofTile'], lambda c, n: 0.70 < n.z < 0.995)])


# ------------------------------------------------------------------ cutting
class Cuts(Openings):
    """common.Openings with the exact solver's self-intersection mode, so that
    the collected cutters (and the target's shells) may overlap; still one
    boolean per target, cutters in the hidden Cutters collection."""

    def box(self, E0, E1, Y0, Y1, z0, z1):
        box_EY(self.cut, E0, E1, Y0, Y1, z0, z1)

    def poly(self, face, outline, depth=0.16, pane=True, inset=0.12):
        """Recess of any (u, z) outline with a 2 cm glass pane at `inset`."""
        face.solid(self.cut, outline, depth)
        if pane:
            cu = sum(p[0] for p in outline) / len(outline)
            cz = sum(p[1] for p in outline) / len(outline)
            o = [(cu + (u - cu) * 0.995, cz + (z - cz) * 0.995) for u, z in outline]
            a = face.coord - face.out * inset
            b = a - face.out * 0.02
            if face.axis == 'x':
                geo.add_prism_x(self.panes, o, min(a, b), max(a, b))
            else:
                geo.add_prism_y(self.panes, o, min(a, b), max(a, b))

    def apply(self):
        t = self.target
        if len(self.cut.faces):
            cutter = geo.object_from_bmesh(self.cut, f'{t.name}_Cut', self.ctx.cutters)
            mod = t.modifiers.new('Bool_Openings', 'BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.solver = 'EXACT'
            mod.use_self = True
            mod.object = cutter
            geo.apply_modifiers(t)
            geo.cleanup(t)
        else:
            self.cut.free()
        if len(self.panes.faces):
            col = self.ctx.col(self.col) if self.col else t.users_collection[0]
            geo.object_from_bmesh(self.panes, self.glass_name, col, self.ctx.mats['M_Glass'])
        else:
            self.panes.free()


class Bags:
    """One bmesh per (object name) for the many small solids of one kind."""

    def __init__(self, ctx):
        self.ctx, self.items = ctx, {}

    def __call__(self, name, col, mat):
        if name not in self.items:
            self.items[name] = (bmesh.new(), col, mat)
        return self.items[name][0]

    def flush(self):
        out = {}
        for name, (bm, col, mat) in self.items.items():
            if len(bm.faces):
                out[name] = geo.object_from_bmesh(bm, name, self.ctx.col(col), self.ctx.mats[mat])
            else:
                bm.free()
        self.items = {}
        return out


# -------------------------------------------------------------- geometry kit
def arch_pts(u, w, spring, crown, segments=12):
    """Interior points of a segmental arch head, left (u - w/2) to right."""
    pts = geo.arch_profile(u, w, spring, crown - spring, spring - 1.0, segments)[3:-1]
    return list(reversed(pts))


def arch_panel(face, bm, u, w, spring, crown, W, top, proud=0.03, back=0.05, segments=12):
    """Precast panel W x (spring -> top) with the arch of the opening cut out."""
    out = [(u - W / 2, spring), (u - w / 2, spring)] + arch_pts(u, w, spring, crown, segments) + \
          [(u + w / 2, spring), (u + W / 2, spring), (u + W / 2, top), (u - W / 2, top)]
    face.solid(bm, out, back, outside=proud)


def span_panel(face, bm, ua, ub, z0, top, arch=None, proud=0.03, back=0.05, segments=12):
    """Precast panel / band between face coordinates ua and ub, z0 -> top,
    optionally with an arch (u, w, crown) cut out of its lower edge (z0 = spring)."""
    ua, ub = sorted((ua, ub))
    pts = [(ua, z0)]
    if arch is not None:
        u, w, crown = arch
        pts += [(u - w / 2, z0)] + arch_pts(u, w, z0, crown, segments) + [(u + w / 2, z0)]
    pts += [(ub, z0), (ub, top), (ua, top)]
    face.solid(bm, pts, back, outside=proud)


def two_light(op, face, a, dm, z0, z1, w=TWO_LIGHT):
    """Two lights separated by a 0.14 brick mullion, total width w."""
    lw = (w - MULLION) / 2
    for s in (-1, 1):
        op.rect(face, a, dm + s * (MULLION + lw) / 2, z0, lw, z1 - z0)


def win(op, face, a, dm, zf, spec=WIN_STD):
    w, sill, head = spec
    op.rect(face, a, dm, zf + sill, w, head - sill)


def band_face(bm, Y, out, E0, E1, z0, z1, proud=0.03, back=0.05):
    """Concrete band on a north (out=-1) or south (out=+1) face at row coordinate Y."""
    box_EY(bm, E0, E1, Y - out * m2E(back), Y + out * m2E(proud), z0, z1)


def head_bands(bm, Y, out, ranges, zs, proud=0.03):
    """13 cm head bands (BAND) on a long face at row coordinate Y over the E
    ranges, one per (z0, z1) in zs."""
    for z0, z1 in zs:
        for p0, p1 in ranges:
            if p1 - p0 > 1e-3:
                band_face(bm, Y, out, p0, p1, z0, z1, proud=proud)


def heads(*floors):
    """(z0, z1) of the head bands of the given floor levels."""
    return [(zf + BAND[0], zf + BAND[1]) for zf in floors]


def face_ranges(part, e0, e1, axes=(), half=CORE_HALF):
    """E ranges of a long-face band: the part, 2 cm round its exposed ends (to
    meet the end-wall band), minus `half` m round each of `axes` (the cores
    abutting a court face, or the notches)."""
    a = e0 - (m2E(0.02) if part.k0 in ('face', 'campo') else 0.0)
    b = e1 + (m2E(0.02) if part.k1 in ('face', 'campo') else 0.0)
    return minus_ranges(a, b, [(x - m2E(half), x + m2E(half)) for x in axes])


def end_band(bm, E_face, inward, Y0, Y1, z):
    """Concrete band across the full width of an exposed pavilion end wall at
    the top-floor head (n9, n29), wrapping 3.5 cm round both corners."""
    Ya, Yb = sorted((Y0, Y1))
    E_a, E_b = E_face - inward * m2E(0.03), E_face + inward * m2E(0.05)
    box_EY(bm, min(E_a, E_b), max(E_a, E_b), Ya - m2E(0.035), Yb + m2E(0.035), z[0] - 0.003, z[1] + 0.003)


def terrace_end(bm_wall, bm_cop, E_face, inward, Y0, Y1, z0, top):
    """End parapet of a roof terrace at an exposed end: brick wall END_WALL
    thick from z0 to the coping, concrete coping on top (n9, n29)."""
    Ea, Eb = E_face - inward * m2E(0.005), E_face + inward * m2E(END_WALL)
    box_EY(bm_wall, min(Ea, Eb), max(Ea, Eb), Y0 + 0.002, Y1 - 0.002, z0, top - COPING_H)
    Ea, Eb = E_face - inward * m2E(0.02), E_face + inward * m2E(END_WALL + 0.02)
    box_EY(bm_cop, min(Ea, Eb), max(Ea, Eb), Y0 + 0.004, Y1 - 0.004, top - COPING_H, top)


def end_coping(bm, E_face, inward, Y_low, Y_high, T):
    """Sloping concrete coping on an exposed pavilion end wall, along the roof
    line between the high and low wall copings (n9)."""
    yl, yh = yY(Y_low), yY(Y_high)
    s = 1.0 if yh > yl else -1.0
    L, H = T + ROOF_LOW - COPING_H - 0.10, T + ROOF_HIGH - COPING_H - 0.10   # roof line at the wall faces
    p0, p1 = (yl + s * PW, L), (yh - s * PW, H)
    prof = [(p0[0], p0[1] - 0.03), (p1[0], p1[1] - 0.03), (p1[0], p1[1] + COPING_H), (p0[0], p0[1] + COPING_H)]
    xa, xb = xE(E_face) + inward * 0.02, xE(E_face) - inward * 0.40
    geo.add_prism_x(bm, prof, min(xa, xb), max(xa, xb))


def low_gutter(bm, E0, E1, Y_low, Y_high, T):
    """Copper box gutter behind the low (inner) wall coping, at the foot of the
    tiled roof (spec 3: low coping T+2.90 with copper box gutter; SE 54)."""
    s = 1 if Y_high > Y_low else -1
    Ya, Yb = Y_low + s * m2E(PW - 0.02), Y_low + s * m2E(PW + 0.28)
    z_roof = T + ROOF_LOW - COPING_H - 0.10
    box_EY(bm, E0 + 0.005, E1 - 0.005, min(Ya, Yb), max(Ya, Yb), z_roof - 0.04, z_roof + 0.06)


# ------------------------------------------------------------------ layout
class Part:
    """A run of one row between E0 and E1; end kinds:
    'face'  exposed block end, 'campo' exposed toward the campo,
    'joint' expansion joint (gap), 'abut' touching another part of the row."""

    def __init__(self, E0, E1, k0, k1, axes):
        self.E0, self.E1, self.k0, self.k1, self.axes = E0, E1, k0, k1, axes

    @property
    def e0(self):
        return self.E0 + (m2E(GAP / 2) if self.k0 == 'joint' else 0.0)

    @property
    def e1(self):
        return self.E1 - (m2E(GAP / 2) if self.k1 == 'joint' else 0.0)

    def exposed(self):
        """(E, inward sign) of the exposed ends."""
        out = []
        if self.k0 in ('face', 'campo'):
            out.append((self.E0, +1))
        if self.k1 in ('face', 'campo'):
            out.append((self.E1, -1))
        return out

    def inner(self, wall=END_WALL):
        """E range inside the end walls (beyond the segment at joints/abutments)."""
        a = self.E0 + m2E(wall) if self.k0 in ('face', 'campo') else self.E0 - 0.05
        b = self.E1 - m2E(wall) if self.k1 in ('face', 'campo') else self.E1 + 0.05
        return a, b


class Seg:
    def __init__(self, tag, block, E0, E1, axes, k0, k1):
        self.tag, self.block, self.E0, self.E1, self.axes, self.k0, self.k1 = tag, block, E0, E1, axes, k0, k1
        self.col = 'Carpet_East' if block == 'east' else 'Carpet_West'

    def part(self):
        return Part(self.E0, self.E1, self.k0, self.k1, self.axes)

    def split_campo(self):
        """(normal part or None, campo part or None) of this segment."""
        c0, c1 = CAMPO['e']
        if self.E1 <= c0 or self.E0 >= c1:
            return self.part(), None
        if self.E0 < c0:          # east block: normal E0 -> 35.5, campo 35.5 -> E1
            return (Part(self.E0, c0, self.k0, 'campo', [a for a in self.axes if a < c0]),
                    Part(c0, self.E1, 'campo', self.k1, [a for a in self.axes if a > c0]))
        return (Part(c1, self.E1, 'campo', self.k1, [a for a in self.axes if a > c1]),
                Part(self.E0, c1, self.k0, 'campo', [a for a in self.axes if a < c1]))


def segments():
    out = []
    for block, b in BLOCKS.items():
        bounds = [b['faces'][0], *b['joints'], b['faces'][1]]
        for i in range(len(bounds) - 1):
            E0, E1 = bounds[i], bounds[i + 1]
            axes = tuple(a for a in b['axes'] if E0 < a < E1)
            k0 = 'face' if i == 0 else 'joint'
            k1 = 'face' if i == len(bounds) - 2 else 'joint'
            out.append(Seg(f'{block[0].upper()}{i + 1}', block, E0, E1, axes, k0, k1))
    return out


PARTY = BLOCKS['east']['party'] + BLOCKS['west']['party']
JOINT_E = BLOCKS['east']['joints'] + BLOCKS['west']['joints']


def _near(v, seq, tol=1e-6):
    return any(abs(v - s) < tol for s in seq)


def arcade_arch(a, s):
    """(centre offset, width, crown) of the arcade arch on side s of house a:
    2.15 next to joints, campo party walls and block ends, else 2.355 (spec 5.5)."""
    b = a + 3 * s
    short = (not _near(b, PARTY)) or _near(b, JOINT_E) or _near(b, CAMPO['e'])
    if short:
        return s * COURT_DX, ARCADE['arch_w_short'], ARCADE['crown_short']
    pier_half = ARCADE['pier'] / 2
    inner = ARCADE['central_pier'] / 2 + ARCADE['flat_w'] + ARCADE['pier']     # 2.225
    return s * (inner + (4.95 - pier_half)) / 2, ARCADE['arch_w'], ARCADE['crown']


def arcade_outer(seg, a, s):
    """Metres from the house axis to the outer end of the arch panel on side s
    of house a: the panels meet at the pier centres on the party walls, stop at
    the joint gap, and run to the block face over the end pier (n16)."""
    b = a + 3 * s
    if _near(b, JOINT_E):
        return 3 * M - GAP / 2
    if _near(b, PARTY):
        return 3 * M - 0.005            # 1 cm joint between the precast panels
    return abs((seg.E1 if s > 0 else seg.E0) - a) * M + 0.02    # 2 cm round the corner


def in_ranges(E, ranges):
    return any(r0 <= E <= r1 for r0, r1 in ranges)


def minus_ranges(E0, E1, ranges):
    """[E0, E1] minus the given ranges."""
    out, cur = [], E0
    for r0, r1 in sorted(ranges):
        if r1 <= cur or r0 >= E1:
            continue
        if r0 > cur:
            out.append((cur, r0))
        cur = max(cur, r1)
    if cur < E1:
        out.append((cur, E1))
    return out


def notch_gaps(E0, E1, axes, half=NOTCH_HALF):
    return minus_ranges(E0, E1, [(a - m2E(half), a + m2E(half)) for a in axes])


# ================================================================ north row
def trifora(op, face, bm_conc, bm_frame, a, dm):
    """L3 trifora (SE 51 / SE 53): stepped sill, segmental head, precast lintel,
    two thin frame mullions between the 0.415 / 1.04 / 0.415 lights."""
    t = TRIFORA
    u = u_on(face, a, dm)
    hw, hc = t['width'] / 2, t['centre'] / 2
    head = arch_pts(u, t['width'], t['spring'], t['crown'], 14)
    out = [(u - hw, t['sill_side']), (u - hc, t['sill_side']), (u - hc, t['sill_centre']),
           (u + hc, t['sill_centre']), (u + hc, t['sill_side']), (u + hw, t['sill_side']),
           (u + hw, t['spring'])] + list(reversed(head)) + [(u - hw, t['spring'])]
    op.poly(face, out, depth=0.16)
    lw, z0, z1 = t['lintel']
    arch_panel(face, bm_conc, u, t['width'], t['spring'], t['crown'], lw, z1, segments=14)
    # stepped precast sill under the opening
    e = 0.04
    sill = [(u - hw - e, t['sill_side'] - 0.08), (u - hc - e, t['sill_side'] - 0.08),
            (u - hc - e, t['sill_centre'] - 0.08), (u + hc + e, t['sill_centre'] - 0.08),
            (u + hc + e, t['sill_side'] - 0.08), (u + hw + e, t['sill_side'] - 0.08),
            (u + hw + e, t['sill_side'] + 0.005), (u + hc, t['sill_side'] + 0.005),
            (u + hc, t['sill_centre'] + 0.005), (u - hc, t['sill_centre'] + 0.005),
            (u - hc, t['sill_side'] + 0.005), (u - hw - e, t['sill_side'] + 0.005)]
    face.solid(bm_conc, sill, 0.05, outside=0.03)
    # mullions (thin frames) at the light boundaries, from the sill to the head
    r = (hw ** 2 + (t['crown'] - t['spring']) ** 2) / (2 * (t['crown'] - t['spring']))
    zc = t['crown'] - r
    for s in (-1, 1):
        um = u + s * hc
        ztop = zc + math.sqrt(r * r - hc * hc)
        a0 = face.coord - face.out * 0.06
        b0 = face.coord - face.out * 0.11
        prof = [(um - 0.03, t['sill_centre']), (um + 0.03, t['sill_centre']), (um + 0.03, ztop), (um - 0.03, ztop)]
        geo.add_prism_y(bm_frame, prof, min(a0, b0), max(a0, b0))


def build_north(ctx, seg, bags):
    col = seg.col
    tag = seg.tag
    conc = bags(f'SM_Carpet_Concrete_{tag}', col, 'M_Concrete')
    frame = bags(f'SM_Carpet_Frames_{tag}', col, 'M_Frame')
    cop = bags(f'SM_Carpet_Copings_{tag}', col, 'M_Concrete')
    part = seg.part()
    e0, e1 = part.e0, part.e1
    yn0, yn1 = ROWS['N']['npav']            # -0.224, 2.224
    ys0, ys1 = ROWS['N']['spav']            # 4.776, 7.224

    # ---------------------------------------------------- north pavilion
    # one solid per segment from the ground to the roof; the L0-L1 portico +
    # gallery is hollowed out behind the arcade wall (spec 5.3)
    np_ = ctx.solid(f'SM_Carpet_NorthPavN_{tag}', col, 'M_Brick',
                    lambda bm: add_pavilion(bm, e0, e1, yn1, yn0, Z0, T_N))
    op = Cuts(ctx, np_)
    v0, v1 = part.inner()
    op.box(v0, v1, yn0 + WALL_M, yn1 - WALL_M, Z0 - 0.1, Z_L2_SOFFIT)
    fN, fS = north_face(yn0), south_face(yn1)
    for a in seg.axes:
        # south wall at L0-L1: open under the floating core between its corner
        # piers, double-height arches into the courts (spec 5.3 / 5.5)
        op.rect(fS, a, 0.0, Z0 - 0.1, 2 * UNDER_CORE, Z_L2_SOFFIT - Z0 + 0.1, through=WALL)
        for s in (-1, 1):
            c = NN_COURT_ARCH
            op.arch(fS, a, s * COURT_DX, Z0 - 0.1, c['w'], c['spring'], c['crown'], through=WALL)
            two_light(op, fS, a, s * COURT_DX, FLOORS[2] + WIN_STD[1], FLOORS[2] + WIN_STD[2])
        # north arcade (spec 5.5): flat pair round the central pier, arches
        # outside; the precast panels meet at the pier centres (n16)
        d_in = ARCADE['central_pier'] / 2 + ARCADE['flat_w'] + ARCADE['pier'] / 2     # 1.855 m
        for s in (-1, 1):
            dmf = s * (ARCADE['central_pier'] / 2 + ARCADE['flat_w'] / 2)
            op.rect(fN, a, dmf, Z0 - 0.1, ARCADE['flat_w'], ARCADE['flat_head'] - Z0 + 0.1, through=WALL)
            dma, w, crown = arcade_arch(a, s)
            op.arch(fN, a, dma, Z0 - 0.1, w, ARCADE['spring'], crown, through=WALL)
            span_panel(fN, conc, u_on(fN, a, s * (d_in + 0.005)), u_on(fN, a, s * arcade_outer(seg, a, s)),
                       ARCADE['spring'], ARCADE['panel_top'], arch=(u_on(fN, a, dma), w, crown))
            trifora(op, fN, conc, frame, a, s * TRIFORA['offset'])
        span_panel(fN, conc, u_on(fN, a, -(d_in - 0.005)), u_on(fN, a, d_in - 0.005),
                   ARCADE['flat_head'], ARCADE['flat_panel_top'])
    # block ends: tall arch into the portico/gallery with a precast band (n9)
    for E, inward in part.exposed():
        f = east_face(E) if inward > 0 else west_face(E)
        c = END_ARCH_N
        op.arch(f, c['y'], 0.0, Z0 - 0.1, c['w'], c['spring'], c['crown'], through=END_WALL + 0.05)
        arch_panel(f, conc, u_on(f, c['y']), c['w'], c['spring'], c['crown'],
                   (yn1 - yn0) * M + 0.04, c['panel'])
        end_coping(cop, E, inward, yn1, yn0, T_N)
        end_band(conc, E, inward, yn0, yn1, BAND_N3)
    op.apply()
    roof_tiles(ctx, np_)
    add_copings(cop, e0, e1, yn1, yn0, T_N)
    low_gutter(bags(f'SM_Carpet_Gutters_{tag}', col, 'M_Copper'), e0, e1, yn1, yn0, T_N)
    # head bands: north face at L3 (n16), court face at L2 and L3 (n59)
    head_bands(conc, yn0, -1, face_ranges(part, e0, e1), [BAND_N3], proud=0.02)
    head_bands(conc, yn1, +1, face_ranges(part, e0, e1, seg.axes, CORE_HALF + 0.08), heads(FLOORS[2]) + [BAND_N3])

    # gallery ("ballatoio"): deck at L1 behind the arcade, brick parapet with a
    # concrete coping to 3.87 (spec 5.3; brick hatch in n16); the block-end bay
    # stays a clear double-height opening (n16, n59)
    g = GALLERY
    deck = bags(f'SM_Carpet_Gallery_{tag}', col, 'M_Concrete')
    par = bags(f'SM_Carpet_GalleryParapet_{tag}', col, 'M_Brick')
    ga = seg.E0 + m2E(END_BAY) if part.k0 == 'face' else e0
    gb = seg.E1 - m2E(END_BAY) if part.k1 == 'face' else e1
    box_EY(deck, ga, gb, g['deck_y'][0], yn1 - WALL_M + 0.003, Z_L1_SOFFIT, FLOORS[1])
    stair_gaps = [(Es - m2E(0.85), Es + m2E(0.85)) for Es in EXT_STAIRS['e'] if seg.E0 < Es < seg.E1]
    py0, py1 = g['deck_y'][0], g['deck_y'][0] + m2E(g['parapet_t'])
    for p0, p1 in minus_ranges(ga, gb, stair_gaps):
        box_EY(par, p0, p1, py0, py1, FLOORS[1], g['parapet_top'] - COPING_H)
        box_EY(cop, p0, p1, py0 - m2E(0.02), py1 + m2E(0.02), g['parapet_top'] - COPING_H, g['parapet_top'])

    # ---------------------------------------------------- south pavilion
    normal, campo = seg.split_campo()
    if normal is not None:
        build_north_spav(ctx, seg, abut(normal), bags, col)
        build_north_band(ctx, seg, normal, bags, col)
    if campo is not None:
        build_campo_spav(ctx, seg, abut(campo), bags)


def abut(p):
    """The north row's south pavilion runs on over the campo from L2 up: the
    boundary between its normal and campo parts is not exposed."""
    k = lambda v: 'abut' if v == 'campo' else v
    return Part(p.E0, p.E1, k(p.k0), k(p.k1), p.axes)


def build_north_spav(ctx, seg, part, bags, col):
    """North-row south pavilion from L1 up (z 2.71), notched on every core axis
    through L3 and the roof (spec 5.2)."""
    tag = seg.tag
    ys0, ys1 = ROWS['N']['spav']
    e0, e1 = part.e0, part.e1
    conc = bags(f'SM_Carpet_Concrete_{tag}', col, 'M_Concrete')
    cop = bags(f'SM_Carpet_Copings_{tag}', col, 'M_Concrete')
    sp = ctx.solid(f'SM_Carpet_SouthPavN_{tag}', col, 'M_Brick',
                   lambda bm: add_pavilion(bm, e0, e1, ys0, ys1, Z_L1_SOFFIT, T_N))
    op = Cuts(ctx, sp)
    fN, fS = north_face(ys0), south_face(ys1)
    for a in part.axes:
        op.box(a - m2E(NOTCH_HALF), a + m2E(NOTCH_HALF), ys0 - 0.08, ys1 + 0.08, FLOORS[3], 15.0)
        for s in (-1, 1):
            win(op, fN, a, s * COURT_DX, FLOORS[1])
            two_light(op, fN, a, s * COURT_DX, FLOORS[2] + WIN_STD[1], FLOORS[2] + WIN_STD[2])
            # L3 French doors onto the joint terrace (spec 5.5)
            op.rect(fS, a, s * COURT_DX, JOINTS['NM'][2], FRENCH[0], 11.37 - JOINTS['NM'][2])
    for E, inward in part.exposed():
        end_coping(cop, E, inward, ys0, ys1, T_N)
        end_band(conc, E, inward, ys0, ys1, heads(T_N)[0])
    op.apply()
    roof_tiles(ctx, sp)
    notch_copings(cop, part.axes, ys0, ys1, T_N)
    for g0, g1 in notch_gaps(e0, e1, part.axes):
        add_copings(cop, g0, g1, ys0, ys1, T_N)
        low_gutter(bags(f'SM_Carpet_Gutters_{tag}', col, 'M_Copper'), g0, g1, ys0, ys1, T_N)
    # head bands: court face L1-L3, south face above the joint terrace L3 (n47, n59)
    head_bands(conc, ys0, -1, face_ranges(part, e0, e1, part.axes, CORE_HALF + 0.08),
               heads(FLOORS[1], FLOORS[2], FLOORS[3]))
    head_bands(conc, ys1, +1, face_ranges(part, e0, e1, part.axes, NOTCH_HALF), heads(FLOORS[3]))
    build_oculus(ctx, tag, part.axes, col, FLOORS[3])


def notch_copings(cop, axes, Y_low, Y_high, T):
    """Sloping copings on the pavilion end walls either side of each notch, as
    at the block ends (n35)."""
    for a in axes:
        end_coping(cop, a - m2E(NOTCH_HALF), -1, Y_low, Y_high, T)
        end_coping(cop, a + m2E(NOTCH_HALF), +1, Y_low, Y_high, T)


def build_oculus(ctx, tag, axes, col, z_base):
    """Precast oculus panels closing the L3 notches toward the south (n60, spec 5.5)."""
    if not axes:
        return
    P = OCULUS_PANEL
    f = south_face(P['y'][1])
    depth = (P['y'][1] - P['y'][0]) * M
    lw, uw, R = P['lower_w'] / 2, P['upper_w'] / 2, P['radius']
    zc = P['crown'] - R
    z_side = zc + math.sqrt(R * R - uw * uw)
    a0 = math.atan2(z_side - zc, uw)

    def fill(bm):
        for a in axes:
            u = u_on(f, a)
            pts = [(u - lw, z_base), (u + lw, z_base), (u + lw, P['lower_top']), (u + uw, P['lower_top']),
                   (u + uw, z_side)]
            n = 16
            for k in range(1, n):
                ang = a0 + (math.pi - 2 * a0) * k / n
                pts.append((u + R * math.cos(ang), zc + R * math.sin(ang)))
            pts += [(u - uw, z_side), (u - uw, P['lower_top']), (u - lw, P['lower_top'])]
            f.solid(bm, pts, depth, outside=0.0)
    obj = ctx.solid(f'SM_Carpet_Oculus_{tag}', col, 'M_Concrete', fill)
    op = Cuts(ctx, obj)
    for a in axes:
        for s in (-1, 1):
            op.round(f, a, s * P['oculus_dx'], P['oculus_z'], P['oculus_d'])
    op.apply()


def build_north_band(ctx, seg, part, bags, col):
    """L0 band of the north row's south pavilion (spec 5.3): enclosed cantine at
    the CANTINE_N ranges, open pilotis elsewhere; pier row at Y 4.95 with the
    floating cores' corner piers and the L0 court arches."""
    tag = seg.tag
    conc = bags(f'SM_Carpet_Concrete_{tag}', col, 'M_Concrete')
    e0, e1 = part.e0, part.e1
    ys1 = ROWS['N']['spav'][1]
    band = ctx.solid(f'SM_Carpet_CantineN_{tag}', col, 'M_Brick',
                     lambda bm: box_EY(bm, e0, e1, BAND_Y0, ys1, Z0, Z_L1_SOFFIT))
    op = Cuts(ctx, band)
    a_in, b_in = part.inner()
    ph = m2E(ARCADE['pier'] / 2)
    for p0, p1 in minus_ranges(a_in, b_in, CANTINE_N):
        op.box(p0, p1, BAND_Y0 + WALL_M, ys1 - WALL_M, Z0 - 0.1, Z_L1_SOFFIT + 0.1)
        # pilotis: the corridor side is an open pier row (n53, n11): piers at
        # the core-pier positions, on the party walls and at the zone ends
        piers = [(p0 - 1.0, p0 + ph), (p1 - ph, p1 + 1.0)]
        piers += [(x - ph, x + ph) for a in part.axes for x in (a - CORE_PIER_OFFSET, a + CORE_PIER_OFFSET)]
        piers += [(E - ph, E + ph) for E in PARTY]
        for o0, o1 in minus_ranges(p0, p1, piers):
            op.box(o0, o1, ys1 - WALL_M - 0.02, ys1 + 0.08, Z0 - 0.1, Z_L1_SOFFIT + 0.1)
    f = north_face(BAND_Y0)
    for a in part.axes:
        if in_ranges(a, CANTINE_N):
            op.rect(f, a, 0.0, 0.0, 1.20, 2.20)                      # cellar door under the core
        else:
            op.rect(f, a, 0.0, Z0 - 0.1, 2 * UNDER_CORE, Z_L1_SOFFIT - Z0 + 0.2, through=WALL)
        for s in (-1, 1):
            c = L0_ARCH
            Ec = a + s * m2E(COURT_DX)
            if in_ranges(Ec, CANTINE_N):
                op.arch(f, a, s * COURT_DX, 0.0, c['w'], c['spring'], c['crown'])
            else:
                op.arch(f, a, s * COURT_DX, Z0 - 0.1, c['w'], c['spring'], c['crown'], through=WALL)
            arch_panel(f, conc, u_on(f, a, s * COURT_DX), c['w'], c['spring'], c['crown'], c['w'] + 0.40, c['panel'])
    for E, inward in part.exposed():
        fe = east_face(E) if inward > 0 else west_face(E)
        c = L0_ARCH
        op.arch(fe, END_ARCH_SPN_Y, 0.0, Z0 - 0.1, c['w'], c['spring'], c['crown'], through=END_WALL + 0.05)
        arch_panel(fe, conc, u_on(fe, END_ARCH_SPN_Y), c['w'], c['spring'], c['crown'], c['w'] + 0.80, c['panel'])
    op.apply()


# =============================================================== middle row
def middle_part(seg):
    """The middle row is absent in the campo houses (spec 5.4)."""
    normal, campo = seg.split_campo()
    return normal


def build_middle(ctx, seg, bags):
    part = middle_part(seg)
    if part is None:
        return
    col, tag = seg.col, seg.tag
    conc = bags(f'SM_Carpet_Concrete_{tag}', col, 'M_Concrete')
    cop = bags(f'SM_Carpet_Copings_{tag}', col, 'M_Concrete')
    ends = bags(f'SM_Carpet_JointEnds_{tag}', col, 'M_Brick')
    e0, e1 = part.e0, part.e1
    yn0, yn1 = ROWS['M']['npav']           # 7.776, 10.224
    ys0, ys1 = ROWS['M']['spav']           # 12.776, 15.224

    # joint strips: open roof terraces (spec 5.1); the north/middle one spans
    # the covered E-W corridor that serves the cantine of both rows (spec 5.3, n53)
    jn = JOINTS['NM']
    ctx.solid(f'SM_Carpet_JointNM_{tag}', col, 'M_Brick',
              lambda bm: box_EY(bm, e0, e1, jn[0], jn[1], Z_L1_SOFFIT, jn[2]))
    jm = JOINTS['MS']
    ctx.solid(f'SM_Carpet_JointMS_{tag}', col, 'M_Brick', lambda bm: box_EY(bm, e0, e1, jm[0], jm[1], Z0, jm[2]))
    # at the block ends the end wall closes the corridor and rises above both
    # terraces as a coped end parapet (n53, n9); toward the campo the corridor
    # stays open and the N/M terrace runs on over the campo pavilion, the M/S
    # terrace ends in a parapet (n29)
    for E, inward in part.exposed():
        face_end = (part.k0 if inward > 0 else part.k1) == 'face'
        if face_end:
            terrace_end(ends, cop, E, inward, jn[0], jn[1], Z0, TERRACE_END_TOP['NM'])
        terrace_end(ends, cop, E, inward, jm[0], jm[1], jm[2] - 0.05, TERRACE_END_TOP['MS'])

    # north pavilion: cantine at L0, notched down to an L2 terrace on every core axis
    np_ = ctx.solid(f'SM_Carpet_NorthPavM_{tag}', col, 'M_Brick',
                    lambda bm: add_pavilion(bm, e0, e1, yn1, yn0, Z0, T_M))
    op = Cuts(ctx, np_)
    ca = part.E0 + m2E(END_WALL) if part.k0 == 'face' else part.E0 - 0.05
    cb = part.E1 - m2E(END_WALL) if part.k1 == 'face' else part.E1 + 0.05
    op.box(ca, cb, yn0 - 0.08, CORRIDOR_NM[1], Z0 - 0.1, Z_L1_SOFFIT)
    f = south_face(yn1)
    for a in part.axes:
        op.box(a - m2E(NOTCH_HALF), a + m2E(NOTCH_HALF), yn0 - 0.08, yn1 + 0.08, NOTCH_TERRACE, 12.0)
        # terrace doors in the notch side walls (L2)
        for fs in (west_face(a - m2E(NOTCH_HALF)), east_face(a + m2E(NOTCH_HALF))):
            op.rect(fs, (yn0 + yn1) / 2, 0.0, NOTCH_TERRACE, FRENCH[0], 8.37 - NOTCH_TERRACE)
        for s in (-1, 1):
            c = NM_ARCH
            op.arch(f, a, s * COURT_DX, 0.0, c['w'], c['spring'], c['crown'])
            two_light(op, f, a, s * COURT_DX, FLOORS[1] + WIN_STD[1], FLOORS[1] + WIN_STD[2])
            win(op, f, a, s * COURT_DX, FLOORS[2])
    for E, inward in part.exposed():
        end_coping(cop, E, inward, yn1, yn0, T_M)
        end_band(conc, E, inward, yn0, yn1, heads(T_M)[0])
    op.apply()
    roof_tiles(ctx, np_)
    notch_copings(cop, part.axes, yn1, yn0, T_M)
    for g0, g1 in notch_gaps(e0, e1, part.axes):
        add_copings(cop, g0, g1, yn1, yn0, T_M)
        low_gutter(bags(f'SM_Carpet_Gutters_{tag}', col, 'M_Copper'), g0, g1, yn1, yn0, T_M)
    head_bands(conc, yn1, +1, face_ranges(part, e0, e1, part.axes, CORE_HALF + 0.08), heads(FLOORS[1], FLOORS[2]))

    # south pavilion: covered E-W passage at L0 behind a pier row (spec 5.3),
    # entered through an L0 arch in the end walls at the block ends and toward
    # the campo (n9, n29)
    sp = ctx.solid(f'SM_Carpet_SouthPavM_{tag}', col, 'M_Brick',
                   lambda bm: add_pavilion(bm, e0, e1, ys0, ys1, Z0, T_M))
    op = Cuts(ctx, sp)
    pa, pb = part.inner()
    op.box(pa, pb, PASSAGE_M[0], PASSAGE_M[1], Z0 - 0.1, Z_L1_SOFFIT)
    fN, fS = north_face(ys0), south_face(ys1)
    thick = (PASSAGE_M[0] - ys0) * M
    for a in part.axes:
        op.rect(south_face(PASSAGE_M[0]), a, 0.0, 0.0, 1.10, 2.20)          # stair-core door off the passage
        for s in (-1, 1):
            c = L0_ARCH
            op.arch(fN, a, s * COURT_DX, Z0 - 0.1, c['w'], c['spring'], c['crown'], through=thick)
            arch_panel(fN, conc, u_on(fN, a, s * COURT_DX), c['w'], c['spring'], c['crown'], c['w'] + 0.40, c['panel'])
            two_light(op, fN, a, s * COURT_DX, FLOORS[1] + WIN_STD[1], FLOORS[1] + WIN_STD[2])
        # L2 doors onto the middle/south joint terrace (spec 5.5)
        for d in (-2.49, -1.00, 1.00, 2.49):
            op.rect(fS, a, d, JOINTS['MS'][2], FRENCH[0], 8.37 - JOINTS['MS'][2])
    for E, inward in part.exposed():
        fe = east_face(E) if inward > 0 else west_face(E)
        c = L0_ARCH
        op.arch(fe, END_ARCH_PASSAGE_Y, 0.0, Z0 - 0.1, c['w'], c['spring'], c['crown'], through=END_WALL + 0.05)
        arch_panel(fe, conc, u_on(fe, END_ARCH_PASSAGE_Y), c['w'], c['spring'], c['crown'], c['w'] + 0.80, c['panel'])
        end_coping(cop, E, inward, ys0, ys1, T_M)
        end_band(conc, E, inward, ys0, ys1, heads(T_M)[0])
    op.apply()
    roof_tiles(ctx, sp)
    add_copings(cop, e0, e1, ys0, ys1, T_M)
    low_gutter(bags(f'SM_Carpet_Gutters_{tag}', col, 'M_Copper'), e0, e1, ys0, ys1, T_M)
    # head bands: court face L1-L2, south face above the joint terrace L2 (n47, n59)
    head_bands(conc, ys0, -1, face_ranges(part, e0, e1, part.axes, CORE_HALF + 0.08), heads(FLOORS[1], FLOORS[2]))
    head_bands(conc, ys1, +1, face_ranges(part, e0, e1), heads(FLOORS[2]))


# ================================================================ south row
def build_south(ctx, seg, bags):
    part = seg.part()
    col, tag = seg.col, seg.tag
    conc = bags(f'SM_Carpet_Concrete_{tag}', col, 'M_Concrete')
    cop = bags(f'SM_Carpet_Copings_{tag}', col, 'M_Concrete')
    e0, e1 = part.e0, part.e1
    yn0, yn1 = ROWS['S']['npav']           # 15.776, 18.224
    ys0, ys1 = ROWS['S']['spav']           # 20.776, 23.224

    np_ = ctx.solid(f'SM_Carpet_NorthPavS_{tag}', col, 'M_Brick',
                    lambda bm: add_pavilion(bm, e0, e1, yn1, yn0, Z0, T_S))
    op = Cuts(ctx, np_)
    f = south_face(yn1)
    for a in part.axes:
        for s in (-1, 1):
            # court face (n48 SE 31): one French door per side at L0; at L1 a
            # two-light window, a single window in the campo houses
            op.rect(f, a, s * COURT_DX, FRENCH[1], SN_COURT_DOOR, FRENCH[2] - FRENCH[1])
            if a in CAMPO_HOUSES:
                win(op, f, a, s * COURT_DX, FLOORS[1])
                win(op, north_face(yn0), a, s * COURT_DX, FLOORS[1])     # north face exposed to the campo (n49)
            else:
                two_light(op, f, a, s * COURT_DX, FLOORS[1] + WIN_STD[1], FLOORS[1] + WIN_STD[2])
    for E, inward in part.exposed():
        end_coping(cop, E, inward, yn1, yn0, T_S)
        end_band(conc, E, inward, yn0, yn1, heads(T_S)[0])
    op.apply()
    roof_tiles(ctx, np_)
    add_copings(cop, e0, e1, yn1, yn0, T_S)
    low_gutter(bags(f'SM_Carpet_Gutters_{tag}', col, 'M_Copper'), e0, e1, yn1, yn0, T_S)
    head_bands(conc, yn1, +1, face_ranges(part, e0, e1, part.axes, CORE_HALF + 0.08), heads(FLOORS[0], FLOORS[1]))
    for a in part.axes:              # L1 head band on the north face where the campo exposes it
        if a in CAMPO_HOUSES:
            lo, hi = ((CAMPO['e'][0], BLOCKS['east']['faces'][1] + m2E(0.02)) if a < BLOCKS['west']['faces'][0]
                      else (BLOCKS['west']['faces'][0] - m2E(0.02), CAMPO['e'][1]))
            head_bands(conc, yn0, -1, [(lo, hi)], heads(FLOORS[1]))

    sp = ctx.solid(f'SM_Carpet_SouthPavS_{tag}', col, 'M_Brick',
                   lambda bm: add_pavilion(bm, e0, e1, ys0, ys1, Z0, T_S))
    op = Cuts(ctx, sp)
    f = south_face(ys1)
    for a in part.axes:
        # south facade (spec 5.5, SE 33): L1 two two-light windows, L0 four French doors
        for s in (-1, 1):
            two_light(op, f, a, s * 1.74, 3.95, 5.36, w=2 * 0.91 + MULLION)
        for d in (-2.49, -1.00, 1.00, 2.49):
            op.rect(f, a, d, 0.0, FRENCH[0], 2.25)
    for E, inward in part.exposed():
        end_coping(cop, E, inward, ys0, ys1, T_S)
        end_band(conc, E, inward, ys0, ys1, heads(T_S)[0])
    op.apply()
    roof_tiles(ctx, sp)
    add_copings(cop, e0, e1, ys0, ys1, T_S)
    low_gutter(bags(f'SM_Carpet_Gutters_{tag}', col, 'M_Copper'), e0, e1, ys0, ys1, T_S)
    # head bands: south facade L0 and L1 (n47 chain), blank court face L1 (n30)
    head_bands(conc, ys1, +1, face_ranges(part, e0, e1), heads(FLOORS[0], FLOORS[1]))
    head_bands(conc, ys0, -1, face_ranges(part, e0, e1, part.axes, CORE_HALF + 0.08), heads(FLOORS[1]))


# ============================================================ block elements
def block_axes(block, row):
    axes = BLOCKS[block]['axes']
    if row == 'M':
        axes = tuple(a for a in axes if a not in CAMPO_HOUSES)
    return axes


def build_cores(ctx, block, row, bags):
    """Stair cores 4.10 m wide on the house axes (spec 5.2); the north row's
    float from L1 on corner piers. Landing windows 0.60 x 0.60 on the E/W faces."""
    col = 'Carpet_East' if block == 'east' else 'Carpet_West'
    r = ROWS[row]
    T = r['T']
    y0, y1 = r['core']
    hw = m2E(CORE_HALF)
    axes = block_axes(block, row)
    zb = Z_L1_SOFFIT if row == 'N' else Z0
    top = T + CORE_EAVE
    B = block.capitalize()
    obj = ctx.solid(f'SM_Carpet_Cores{row}_{B}', col, 'M_Brick',
                    lambda bm: [box_EY(bm, a - hw, a + hw, y0, y1, zb, top) for a in axes])
    op = Cuts(ctx, obj)
    floors = [z for z in FLOORS if z < T + 0.01 and z >= (FLOORS[1] if row == 'N' else 0.0)]
    for a in axes:
        for f in (east_face(a - hw), west_face(a + hw)):
            for zf in floors:
                for d in (-CORE_WIN_DY, CORE_WIN_DY):
                    op.rect(f, r['yc'], d, zf + CORE_WIN[1], CORE_WIN[0], CORE_WIN[2] - CORE_WIN[1])
    op.apply()
    if row == 'N':                   # L1 slab edge under the floating cores (n9)
        sb = bags(f'SM_Carpet_CoreSlabs_{B}', col, 'M_Concrete')
        for a in axes:
            box_EY(sb, a - hw - m2E(0.02), a + hw + m2E(0.02), y0 + 0.003, y1 - 0.003, Z_L1_SOFFIT - 0.01, FLOORS[1])

    # curved copper roof R 6.00 spanning E-W, crown T+2.70, eaves/gutter T+2.48 (spec 3, SE 59)
    cu = bags(f'SM_Carpet_Vaults{row}_{B}', col, 'M_Copper')
    R = CORE_VAULT_R
    zc = T + CORE_CROWN - R
    zb_v = T + CORE_EAVE - 0.05
    h = math.sqrt(R * R - (zb_v - zc) ** 2)
    a0 = math.atan2(zb_v - zc, h)
    arc = [(R * math.cos(a0 + (math.pi - 2 * a0) * k / 16), zc + R * math.sin(a0 + (math.pi - 2 * a0) * k / 16))
           for k in range(1, 16)]
    prof = [(-h, zb_v), (h, zb_v)] + arc
    yv1 = OCULUS_PANEL['y'][0] if row == 'N' else y1        # north row: over the L3 notch (spec 5.2)
    for a in axes:
        xc = xE(a)
        geo.add_prism_y(cu, [(xc + x, z) for x, z in prof], yY(yv1), yY(y0))
        for s in (-1, 1):
            xa, xb = xc + s * (h + 0.01), xc + s * (CORE_HALF + 0.07)
            geo.add_box(cu, xa, xb, yY(y0) - 0.01, yY(y1) + 0.01, T + CORE_EAVE - 0.08, T + CORE_EAVE + 0.08)


def build_courts(ctx, block, row, bags):
    """Light-court floors at -0.10 and the 1.25 m walls of the half-courts at
    the block ends (middle and south rows, spec 5.2)."""
    col = 'Carpet_East' if block == 'east' else 'Carpet_West'
    B = block.capitalize()
    r = ROWS[row]
    y0, y1 = r['core']
    axes = block_axes(block, row)
    E0, E1 = BLOCKS[block]['faces']
    if row == 'M':
        if block == 'east':
            E1 = CAMPO['e'][0]
        else:
            E0 = CAMPO['e'][1]
    hw = m2E(CORE_HALF)
    lw = m2E(LOW_WALL_T)
    pv = bags(f'SM_Carpet_Courts{row}_{B}', col, 'M_Paving')
    walls = bags(f'SM_Carpet_CourtWalls{row}_{B}', col, 'M_Brick')
    stops = [E0 + lw] + [v for a in axes for v in (a - hw, a + hw)] + [E1 - lw]
    for i in range(0, len(stops), 2):
        box_EY(pv, stops[i] + 0.002, stops[i + 1] - 0.002, y0 + 0.002, y1 - 0.002, Z0, Z_COURT)
    for E, s in ((E0, 1), (E1, -1)):
        box_EY(walls, min(E, E + s * lw), max(E, E + s * lw), y0 + 0.002, y1 - 0.002, Z0, LOW_WALL)


def build_chimneys(ctx, block, bags):
    """Corbelled stacks on the south faces of the pavilion blocks at party walls
    and joints (spec 5.5): north row to 14.0, middle row to 10.9."""
    col = 'Carpet_East' if block == 'east' else 'Carpet_West'
    B = block.capitalize()
    br = bags(f'SM_Carpet_Chimneys_{B}', col, 'M_Brick')
    cap = bags(f'SM_Carpet_ChimneyCaps_{B}', col, 'M_Concrete')
    c = CHIMNEY
    d = m2E(c['d'])

    def stack(E, w, Yf, zc, top):
        hw = m2E(w / 2)
        box_EY(br, E - hw, E + hw, Yf - 0.03, Yf + d, zc + 0.20, top)
        box_EY(br, E - hw - m2E(0.08), E + hw + m2E(0.08), Yf - 0.03, Yf + d + m2E(0.08), zc, zc + 0.25)
        box_EY(cap, E - hw - m2E(0.06), E + hw + m2E(0.06), Yf - 0.02, Yf + d + m2E(0.06), top - 0.01, top + 0.10)

    rows = [('N', ROWS['N']['spav'][1], c['n_corbel'], c['n_top'])]
    rows.append(('M', ROWS['M']['spav'][1], c['m_corbel'], c['m_top']))
    for row, Yf, zc, top in rows:
        for E in BLOCKS[block]['party']:
            if row == 'M' and _near(E, CAMPO['e']):
                continue                 # the middle row ends there: single stack inside its end (below)
            stack(E, c['w'], Yf, zc, top)
    # single-flue stacks (n47 SE 33): north row 0.79 m in from the slot faces,
    # middle row flush with its end toward the campo
    inward = -1 if block == 'east' else 1
    slot = BLOCKS[block]['faces'][1] if block == 'east' else BLOCKS[block]['faces'][0]
    stack(slot + inward * m2E(CHIMNEY_1['slot_in']), CHIMNEY_1['w'], *rows[0][1:])
    E_campo = CAMPO['e'][0] if block == 'east' else CAMPO['e'][1]
    stack(E_campo + inward * m2E(CHIMNEY_1['w'] / 2), CHIMNEY_1['w'], *rows[1][1:])


def build_ext_stair(ctx, block, E, bags):
    """External stair to the gallery inside an arcade arch (SE 64, spec 5.5)."""
    col = 'Carpet_East' if block == 'east' else 'Carpet_West'
    B = block.capitalize()
    st = EXT_STAIRS
    steps = bags(f'SM_Carpet_ExtStairSteps_{B}', col, 'M_Concrete')
    walls = bags(f'SM_Carpet_ExtStairWalls_{B}', col, 'M_Brick')
    cop = bags(f'SM_Carpet_ExtStairCoping_{B}', col, 'M_Concrete')
    t = m2E(st['tread'])
    n1, n2 = st['risers']
    z_land = Z_PAVING + n1 * st['riser']
    y_land0 = st['y_north'] + (n1 - 1) * t
    y_land1 = st['landing'][1]
    rise2 = (FLOORS[1] - z_land) / n2
    top, z = [], Z_PAVING
    for k in range(n1):                     # flight 1: 5 risers, then the landing
        y = st['y_north'] + k * t
        top += [(y, z), (y, z + st['riser'])]
        z += st['riser']
    for k in range(n2):                     # flight 2: 15 risers up through the arch
        y = y_land1 + k * t
        top += [(y, z), (y, z + rise2)]
        z += rise2
    top.append((GALLERY['deck_y'][0], FLOORS[1]))   # last tread runs on to the gallery deck
    y_soffit = GALLERY['deck_y'][0] - (FLOORS[1] - 0.30 - Z0) / (rise2 / t)
    prof = [(st['y_north'], Z0)] + top + [(GALLERY['deck_y'][0], FLOORS[1] - 0.30), (y_soffit, Z0)]
    prof = [(yY(Y), z) for Y, z in prof]
    hc = m2E(st['clear'] / 2)
    geo.add_prism_x(steps, prof, xE(E + hc), xE(E - hc))
    # side walls 0.255 with a sloping coping, up to the arcade face
    yf = ROWS['N']['npav'][0]
    line = [(st['y_north'], Z_PAVING + STAIR_SIDE_H), (y_land0, z_land + STAIR_SIDE_H),
            (y_land1, z_land + STAIR_SIDE_H)]
    zf = z_land + STAIR_SIDE_H + (yf - y_land1) / t * rise2
    line.append((yf, zf))
    wall = [(st['y_north'], Z0), (yf, Z0)] + list(reversed(line))
    copl = [(Y, z - 0.02) for Y, z in line] + [(Y, z + 0.08) for Y, z in reversed(line)]
    for s in (-1, 1):
        Ea, Eb = E + s * hc, E + s * (hc + m2E(st['side']))
        geo.add_prism_x(walls, [(yY(Y), z) for Y, z in wall], xE(max(Ea, Eb)), xE(min(Ea, Eb)))
        Ea2, Eb2 = E + s * (hc - m2E(0.02)), E + s * (hc + m2E(st['side'] + 0.02))
        geo.add_prism_x(cop, [(yY(Y), z) for Y, z in copl], xE(max(Ea2, Eb2)), xE(min(Ea2, Eb2)))


def build_portico_floor(ctx, block, bags):
    """Paving of the north-row portico, courts and pilotis (spec 3: -0.45),
    1 cm proud of the site paving to avoid coincident faces."""
    col = 'Carpet_East' if block == 'east' else 'Carpet_West'
    B = block.capitalize()
    pv = bags(f'SM_Carpet_PorticoFloor_{B}', col, 'M_Paving')
    E0, E1 = BLOCKS[block]['faces']
    box_EY(pv, E0, E1, ROWS['N']['npav'][0], CORRIDOR_NM[1], Z0, Z_PAVING + 0.01)


# ==================================================================== campo
def campo_spav_profile():
    """(y, z) section of the north row's south pavilion over the campo: from L2
    (on the pier bands, 5.80) with the L2 storey reaching Y 8.24 under an L3
    terrace (9.15) and its parapet; L3 and the roof as the roof rule (spec 5.4)."""
    ys0, ys1 = ROWS['N']['spav']
    sec = pavilion_section(ys0, ys1, CAMPO_SP_Z0, T_N, PW)
    yl, _ = sec[0]
    yb = yY(CAMPO['l2_south'])
    yh = sec[1][0]
    deck = JOINTS['NM'][2]
    par = CAMPO_PARAPET - 0.12
    return [(yl, CAMPO_SP_Z0), (yb, CAMPO_SP_Z0), (yb, par), (yb + CAMPO_PARAPET_T, par),
            (yb + CAMPO_PARAPET_T, deck), (yh, deck)] + sec[2:]


def build_campo_spav(ctx, seg, part, bags):
    col = 'Carpet_Campo'
    tag = f'Campo{seg.tag}'
    conc = bags(f'SM_Carpet_Concrete_{tag}', col, 'M_Concrete')
    cop = bags(f'SM_Carpet_Copings_{tag}', col, 'M_Concrete')
    ends = bags(f'SM_Carpet_TerraceEnds_{tag}', col, 'M_Brick')
    ys0, ys1 = ROWS['N']['spav']
    yx = CAMPO['l2_south']
    e0, e1 = part.e0, part.e1
    prof = campo_spav_profile()
    sp = ctx.solid(f'SM_Carpet_SouthPavN_{tag}', col, 'M_Brick',
                   lambda bm: geo.add_prism_x(bm, prof, xE(e1), xE(e0)))
    op = Cuts(ctx, sp)
    fN, fS, fX = north_face(ys0), south_face(ys1), south_face(yx)
    for a in part.axes:
        # notch through L3 and the roof; the terrace parapet is interrupted in
        # front of the oculus panel, whose lower part shows to its base (n47, n35)
        op.box(a - m2E(NOTCH_HALF), a + m2E(NOTCH_HALF), ys0 - 0.08, yx + 0.08, JOINTS['NM'][2], 15.0)
        for s in (-1, 1):
            two_light(op, fN, a, s * COURT_DX, FLOORS[2] + WIN_STD[1], FLOORS[2] + WIN_STD[2])
            win(op, fX, a, s * COURT_DX, FLOORS[2])                       # L2 face over the campo (n50)
            op.rect(fS, a, s * COURT_DX, JOINTS['NM'][2], FRENCH[0], 11.37 - JOINTS['NM'][2])
    for E, inward in part.exposed():
        end_coping(cop, E, inward, ys0, ys1, T_N)
        end_band(conc, E, inward, ys0, ys1, heads(T_N)[0])
        # end parapet of the L3 terrace at the slot (n29)
        terrace_end(ends, cop, E, inward, ys1, yx, JOINTS['NM'][2] - 0.05, CAMPO_PARAPET)
    op.apply()
    roof_tiles(ctx, sp)
    notch_copings(cop, part.axes, ys0, ys1, T_N)
    for g0, g1 in notch_gaps(e0, e1, part.axes):
        add_copings(cop, g0, g1, ys0, ys1, T_N)
        low_gutter(bags(f'SM_Carpet_Gutters_{tag}', col, 'M_Copper'), g0, g1, ys0, ys1, T_N)
        # parapet coping of the L3 terrace over the campo
        box_EY(cop, g0, g1, yx - m2E(CAMPO_PARAPET_T + 0.02), yx + m2E(0.02), CAMPO_PARAPET - COPING_H, CAMPO_PARAPET)
    # head bands: court face L2-L3, south face above the terrace L3, face over the campo L2 (n47, n59)
    head_bands(conc, ys0, -1, face_ranges(part, e0, e1, part.axes, CORE_HALF + 0.08), heads(FLOORS[2], FLOORS[3]))
    head_bands(conc, ys1, +1, face_ranges(part, e0, e1, part.axes, NOTCH_HALF), heads(FLOORS[3]))
    head_bands(conc, yx, +1, face_ranges(part, e0, e1), heads(FLOORS[2]))
    # concrete band at the L2 floor on the face over the campo
    band_face(conc, yx, +1, e0, e1, CAMPO_SP_Z0, FLOORS[2] + 0.13)
    build_oculus(ctx, tag, part.axes, col, FLOORS[3])


def build_campo(ctx, bags):
    """Campo between party walls E 35.5 and 48.5 (spec 5.4): tall brick piers
    and concrete bands carrying the north row's south pavilion, the floating
    cores' south corner piers, the slot-face piers and arch, the two stairs to
    the gallery, the one-storey arcade on the south side (n49) and the paving."""
    col = 'Carpet_Campo'
    piers = bags('SM_Carpet_CampoPiers', col, 'M_Brick')
    bands = bags('SM_Carpet_CampoBands', col, 'M_Concrete')
    stairs = bags('SM_Carpet_CampoStairs', col, 'M_Concrete')
    pave = bags('SM_Carpet_CampoPaving', col, 'M_Paving')
    c0, c1 = CAMPO['e']
    east_face_slot, west_face_slot = BLOCKS['east']['faces'][1], BLOCKS['west']['faces'][0]
    pw, pd = m2E(0.74), m2E(WALL) / 2               # type-2 piers 0.74 x 0.395 (n11, n72)
    ys0, ys1 = ROWS['N']['spav']
    ptop = CAMPO['pier_top'] + 0.02
    runs = ((c0, east_face_slot, CAMPO_HOUSES[0]), (west_face_slot, c1, CAMPO_HOUSES[1]))
    for E0, E1, a in runs:
        slot, party = (E1, E0) if E1 == east_face_slot else (E0, E1)
        d = 1 if slot < party else -1               # from the slot face into the house
        for Yr in CAMPO['pier_rows']:
            xs = [party - d * pw / 2, a - CAMPO['pier_offset'], a + CAMPO['pier_offset']]
            if Yr > CAMPO['pier_rows'][0]:
                xs.append(slot + d * pw / 2)        # row 8.1: plain pier at the slot (n11 type 4)
            for Ep in xs:
                box_EY(piers, Ep - pw / 2, Ep + pw / 2, Yr - pd, Yr + pd, Z0, ptop)
            dr = m2E(0.15)                                  # small drain pier on the axis
            box_EY(piers, a - dr, a + dr, Yr - dr, Yr + dr, Z0, ptop)
            box_EY(bands, E0, E1, Yr - pd - 0.002, Yr + pd + 0.002, CAMPO['pier_top'], CAMPO['band_top'])
        # type-1 L piers at the slot face (n11): legs 0.945 along the face from
        # the pavilion's north and south faces, 2.15 apart, and along the rows
        L, t, r = m2E(SLOT_PIER['leg']), m2E(SLOT_PIER['t']), m2E(SLOT_PIER['row'])
        Yr0, Yr1 = PORTICO_PIER_ROWS[1] + pd, CAMPO['pier_rows'][0] - pd
        poly_EY(piers, [(slot, ys0), (slot, ys0 + L), (slot + d * t, ys0 + L), (slot + d * t, Yr0),
                        (slot + d * r, Yr0), (slot + d * r, ys0)], Z0, ptop)
        poly_EY(piers, [(slot, ys1), (slot, ys1 - L), (slot + d * t, ys1 - L), (slot + d * t, Yr1),
                        (slot + d * r, Yr1), (slot + d * r, ys1)], Z0, ptop)
        # concrete band across the slot face with the arch between the L piers (n29 SE 35)
        f = east_face(slot) if d > 0 else west_face(slot)
        span_panel(f, bands, yY(ys0), yY(CAMPO['l2_south']), CAMPO['pier_top'] - 0.005, CAMPO['band_top'] + 0.005,
                   arch=(yY(END_ARCH_SPN_Y), SLOT_ARCH['w'], CAMPO['pier_top'] - 0.005 + SLOT_ARCH['rise']),
                   proud=0.01, back=SLOT_PIER['t'])
        # floating core's south corner piers (row 4.95), up to the pavilion
        for s in (-1, 1):
            Ep = a + s * CORE_PIER_OFFSET
            box_EY(piers, Ep - m2E(CPIER_W / 2), Ep + m2E(CPIER_W / 2), ROWS['N']['core'][1] - 0.05,
                   PORTICO_PIER_ROWS[1] + pd, Z0, CAMPO_SP_Z0 + 0.02)
        # paving of the campo floor (1 cm proud of the site paving)
        box_EY(pave, E0, E1, CORRIDOR_NM[1] + 0.002, CAMPO_SOUTH_Y[0] - 0.002, Z0, Z_PAVING + 0.01)

    # stairs from the campo (Y 5.6, -0.45) up to the gallery (Y 1.7, deck at 3.01),
    # 0.9 m wide, through the court arch of the campo house next to the party
    # wall: n11 draws the treads at E ~36.1-36.8, between the party pier and the
    # core pier, i.e. on the court arch at axis -+ 3.30 (spec 5.4 "E ~36.0 / 48.0")
    yb, yt = CAMPO['stairs_y'][1], CAMPO['stairs_y'][0]
    n = 20
    run, rise = (yt - yb) / n, (FLOORS[1] - Z_PAVING) / n
    for Es in (CAMPO_HOUSES[0] - m2E(COURT_DX), CAMPO_HOUSES[1] + m2E(COURT_DX)):
        top, z = [], Z_PAVING
        for k in range(n):
            y = yb + k * run
            top += [(y, z), (y, z + rise)]
            z += rise
        top.append((yt, FLOORS[1]))
        slope = rise / abs(run)
        y_soffit = yt + (FLOORS[1] - 0.25 - Z0) / slope
        prof = [(yb, Z0)] + top + [(yt, FLOORS[1] - 0.25), (min(y_soffit, yb), Z0)]
        prof = [(yY(Y), zz) for Y, zz in prof]
        hw = m2E(0.45)
        geo.add_prism_x(stairs, prof, xE(Es + hw), xE(Es - hw))

    # one-storey arcade closing the campo to the south (n49 chain 2.15|0.74|1.22|0.52|1.22|0.74|2.45)
    cs = ctx.solid('SM_Carpet_CampoSouth', col, 'M_Brick',
                   lambda bm: [box_EY(bm, E0, E1, CAMPO_SOUTH_Y[0], CAMPO_SOUTH_Y[1], Z0, CAMPO_SOUTH_TOP)
                               for E0, E1, a in runs])
    op = Cuts(ctx, cs)
    f = north_face(CAMPO_SOUTH_Y[0])
    for E0, E1, a in runs:
        slot_side = 1 if E1 == east_face_slot else -1          # +dm = west
        for s in (-1, 1):
            op.rect(f, a, s * 0.87, 0.0, 1.22, 2.25)
            w = 2.45 if s == slot_side else 2.15
            op.rect(f, a, s * (2.22 + w / 2), 0.0, w, 2.25)
        band_face(bands, CAMPO_SOUTH_Y[0], -1, E0, E1, FLOORS[1] - 0.30, FLOORS[1] + 0.02)
    op.apply()


# ==================================================================== build
def build(ctx):
    ensure_roof_material(ctx)
    bags = Bags(ctx)
    for seg in segments():
        build_north(ctx, seg, bags)
        build_middle(ctx, seg, bags)
        build_south(ctx, seg, bags)
    for block in BLOCKS:
        for row in 'NMS':
            build_cores(ctx, block, row, bags)
        for row in 'MS':
            build_courts(ctx, block, row, bags)
        build_chimneys(ctx, block, bags)
        build_portico_floor(ctx, block, bags)
        for E in EXT_STAIRS['e']:
            if BLOCKS[block]['faces'][0] < E < BLOCKS[block]['faces'][1]:
                build_ext_stair(ctx, block, E, bags)
    build_campo(ctx, bags)
    bags.flush()
