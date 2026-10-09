"""Schiera - the row of four two-storey blocks (eight dwellings) at the south-east
of the complex (docs/ANALYSIS.md section 3 roof rule, section 6 schiera).

Drawings: n27 (SE 44 ground floor), n45 (SE 45 first floor), n26 (SE 46 roof
plan), n6 (SE 47 south face, titled "nord"), n13 (SE 48 north face, titled
"sud"), n5 (SE 49 sections A/B and end elevation DE), n40 (SE 60 precast oculus
panel, 1:10), n37 (published plans/sections/elevations), n39 (1:200 axo).

Massing (spec 6):
  * north bar Y 28.78 -> 31.22 over E 7.28 -> 39.72, two storeys, mono-pitch
    roof rising south (coping 5.91 north wall, 7.10 south wall), split at the
    expansion joint E 23.5;
  * four blocks on the party axes E 35.5 / 27.5 / 19.5 / 11.5 (axis +-2.224):
    L0 one deep volume to Y 35.22; above it the twin-stair core with a copper
    barrel vault and the south oculus panel, an L1 terrace either side and a
    single-storey lean-to Y 32.93 -> 35.22 falling south 4.10 -> 2.90;
  * five bays between blocks / end walls: porticoes through the bar (8 arches
    on both faces, partition walls on E 31.5 / 23.5 / 15.5) and walled gardens.

Objects (jasonkneen-3d-modeling skill, hard-surface workflow: closed solids at
real scale, one object per building element, Exact booleans with all cutters
of a target in ONE hidden cutter object, cleanup + normals after every boolean):
  SM_Schiera_Body_E / _W         brick: bar segment + its two blocks (one exact
                                 union), every opening cut in one exact
                                 difference (self-intersecting cutters allowed)
  SM_Schiera_Body_<E|W>_Glass    glass panes of the windows and doors
  SM_Schiera_Trim                exposed concrete: copings, verges, lintel bands,
                                 sills, arch lintel blocks, low-wall copings, the
                                 copertina under each oculus panel
  SM_Schiera_Panel (+ _Glass)    precast oculus panels (SE 60)
  SM_Schiera_Roof                clay tiles of the bar and lean-to roofs
  SM_Schiera_Copper              core vaults and eave flashings, box gutters,
                                 downpipes (hoppers, clips, shoes), flue pipes
  SM_Schiera_Masonry             brick: low walls in the north arches, garden walls
  SM_Schiera_GardenCoping        concrete copings of the garden walls
  SM_Schiera_Steps               north steps of the porticoes
  SM_Schiera_Gardens             garden ground (lawn, ~0.00)
  SM_Schiera_Doors               kitchen door leaves inside the porticoes
"""
from __future__ import annotations

import math

import bmesh
import bpy

from . import geo
from .common import (Openings, add_copings, add_pavilion, east_face, north_face,
                     pavilion_section, south_face, u_on, west_face, xE, yY)
from .params import (COPING_H, CORE_CROWN, CORE_EAVE, CORE_VAULT_R, DOOR, FLOORS, FRENCH, MODULE,
                     ROOF_HIGH, SCHIERA, SLAB, WIN_SMALL, WIN_STD, Z_GARDEN_WALL, Z_PAVING)

S = SCHIERA
M = MODULE
COL = 'Schiera'

# ------------------------------------------------------------ local constants
Z0 = -0.50                       # building bases: 5 cm into the -0.45 paving (task rule)
T = FLOORS[1]                    # 3.01, top floor of the bar (roof rule: copings T+2.90 / T+4.10)
WALL = 0.37                      # spec 6: walls 0.37 thick, axes on their inner faces
#                                  (params.WALL 0.395 includes the carpet's 2.5 cm render)
WM = WALL / M
GAP = 0.04                       # m, expansion-joint gap on E 23.5 (as the carpet, spec 5.2)
E_EAST, E_WEST = S['e']          # 7.28, 39.72 outer faces
Y_N, Y_S = S['y']                # 28.78, 35.22
Y_BAR = S['bar_y'][1]            # 31.22 south face of the bar
Y_CORE = S['core_y'][1]          # 32.93 core / terraces | lean-to
HALF = S['block_half']           # 2.224 modules
JOINT_E = S['joint']             # 23.5
CORE_HW = S['panel']['w'] / 2    # 2.085 m: core outer faces = panel width 4.17 (SE 60 plan:
#                                  0.335 + 0.10 + 1.55 + 0.20 + 1.55 + 0.10 + 0.335)
# core roof (spec 3 roof rule, SE 59 eave detail, n5 section F measured at X36 / X28):
# brick core walls to the eave T+2.48 = 5.49 (= top of the bar's 5.36 -> 5.49 band) under a
# copper flashing ("scossalina in rame"); copper vault R CORE_VAULT_R = 6.00 spanning E-W
# with its crown at T+2.70 = 5.71, dropping into the internal gutter inside the wall tops
EAVE = T + CORE_EAVE             # 5.49
VAULT_CROWN = T + CORE_CROWN     # 5.71 (n5 F: outer crown 5.67-5.71; spec 6 "~5.6")
CORE_TOP = EAVE - 0.01           # brick core top, 1 cm inside the flashing
FLASH = (0.025, 0.02, 1.55)      # flashing: thickness, outer overhang, inner edge (m from the
#                                  axis, under the vault, which meets the 5.495 top at +-1.59)
TERRACE_Z = 3.00                 # L1 terrace paving (SE 60 "+0.00 pav. finito 1 piano" = 3.01)
PARAPET_T = 0.37                 # terrace side parapet = block side wall (n45: terrace clear 1.22)
BAND_H = 0.13                    # concrete lintel bands 13 cm over the window heads (n6, n13 "13")
HEAD = WIN_STD[2]                # 2.35 head above the floor (SE 53)
BAND = (T + HEAD + 0.002, T + HEAD + BAND_H)   # 5.36 -> 5.49 round the bar (n6, n13, n5 DE);
#                                  2 mm over the heads: no coplanar soffits
BAND_L0 = (HEAD + 0.002, HEAD + BAND_H)        # 2.35 -> 2.48 lean-to and garden-side walls (n6, n5)
BAND_PROUD, BAND_BACK = 0.03, 0.05
# portico arches (n13 / n6 dimension strings): 0.62 low wall + passage + 0.62 low wall
ARCH_LONG = 2.345                # 0.62 + 1.105 + 0.62, arches beside a partition wall
ARCH_SHORT = 2.15                # 0.62 + 0.91 + 0.62, end bays and the joint bay (n13 "62 91 62")
PIER = 0.74                      # pier between the paired arches on a partition (n13 "74", n6)
LOW_WALL = (0.62, 1.25)          # low walls either side of the passage: width, top (n13)
LOW_WALL_SET = 0.04              # m, low walls set back from the face (n27)
LOW_WALL_IN = 0.01               # m, low walls stop short of the wall's inner face (they run
#                                  5 mm into the jambs: no coplanar faces with the body)
LINTEL_OV = 0.40                 # m, north lintel blocks run 0.40 past the arch (n13: 2.97 over 2.15)
PART_T = 0.25                    # m, portico partitions on E 31.5 / 15.5 (n27)
JOINT_WALL = 0.22                # m, each leaf of the double partition on the joint (n27)
CEILING = FLOORS[1] - SLAB       # 2.71 portico ceiling = L1 slab underside (SE 58)
STEP = (0.25, 0.15)              # north steps: tread, riser (-0.45 -> 0.00 in 3 risers, n13 / n27)
DOOR_Y = 30.50                   # kitchen doors in the portico side walls: n27 (SE 44) openings
#                                  Y 30.20 -> 30.79 at the X38 and X26 block walls
FRENCH_Y = (31.62, 32.38)        # two French windows in each garden-side block wall (n27, n37, n5 DE)
FRENCH_W = 0.91                  # m, their width (n5 DE: two lights ~0.9 with a 0.33 pier)
TERRACE_DOOR_W = 0.78            # terrace doors (n6 0.78, n40 0.74 measured)
NORTH_PAIR = (-0.51, 0.49)       # north L1 windows at party axis -0.51 / +0.49 module (spec 6)
TERRACE_DOOR_DX = 1.68           # modules (spec 6)
LEAN_WIN_DX = 1.0                # modules (spec 6)
GW_T = 0.25                      # m, garden walls (n27: south wall ~0.26, recessed behind the lean-to)
GW_Y = S['garden_y'][1]          # 34.97 inner face of the south garden wall
PANEL_Y = (0.24, 0.10)           # m NORTH of Y 32.93: north / south face of the 0.14 panel, which
#                                  closes the core's south end in front of the lean-to's high
#                                  coping (n5 section A: Y 32.78 -> 32.89; SE 60 B-B "8 | 14 | 23":
#                                  23 cm of beam and copertina south of the panel to axis Y 33)
Z_BEAM = ROOF_HIGH - COPING_H    # 3.98: top of the beam / lean-to wall under the copertina
PIPE_R = 0.05                    # downpipes Ø 0.10 (n13 / n6 double lines)
DOWNPIPE_DX = 0.36               # m, lean-to downpipes inside the block corners (n6)
PIPE_OFF = 0.035                 # m, downpipes stand off the wall face (clips, hoppers into the wall)
SHOE_Z = -0.40                   # lean-to downpipes turn back into the wall just above the
#                                  -0.45 quay: the south face Y 35.22 is 5 cm from the rio (spec 6/7)
LINTEL_JOINT = 0.01              # m, joint between the paired north lintel blocks (n13)
FLUE = dict(r=0.09, dx=0.13, dy=0.13, z0=5.40, top=7.85)   # twin flue pipes (spec 9, n5, n39)


def m2E(m: float) -> float:
    """Metres -> modules."""
    return m / M


# --------------------------------------------------------------- materials
def _lin(c: int) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _tile_material(ctx) -> None:
    """Clay tiles ('tegole', SE 54) - not part of materials.PALETTE."""
    if 'M_RoofTile' in ctx.mats:
        return
    m = bpy.data.materials.get('M_RoofTile') or bpy.data.materials.new('M_RoofTile')
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    col = tuple(_lin(c) for c in (164, 86, 62)) + (1.0,)
    bsdf.inputs['Base Color'].default_value = col
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.8
    m.diffuse_color = col
    ctx.mats['M_RoofTile'] = m


# ------------------------------------------------------------------ layout
def _near(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) < tol


def bays():
    """Clear E-ranges of the five bays between block side walls / bar end walls."""
    edges = [E_EAST + WM]
    for a in sorted(S['axes']):
        edges += [a - HALF, a + HALF]
    edges.append(E_WEST - WM)
    return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]


def partition_half(p: float) -> float:
    """Half the E-width (modules) of the portico partition on p."""
    if _near(p, JOINT_E):
        return m2E(GAP / 2 + JOINT_WALL)
    return m2E(PART_T / 2)


def porticoes():
    """The eight porticoes: dict(c=arch centre E, w=span m, lo, hi=clear E-range,
    bay=(lo, hi) of the whole bay, part=partition E or None).

    Spec 6 centres the arches on E 8.5 ... 38.5. The n13 / n6 dimension strings
    refine this: the end-bay and joint-bay arches are 2.15 (0.62 + 0.91 + 0.62)
    centred on those axes; the arches beside the partitions on E 31.5 / 15.5
    are 2.345 (0.62 + 1.105 + 0.62) either side of a 0.74 pier on the partition,
    i.e. centred 0.065 module inside the nominal axes."""
    out = []
    for blo, bhi in bays():
        parts = [p for p in S['garden_walls_e'] if blo < p < bhi]
        subs = [(blo, bhi)]
        if parts:
            p = parts[0]
            t = partition_half(p)
            subs = [(blo, p - t), (p + t, bhi)]
        for lo, hi in subs:
            c = [a for a in S['arches'] if lo < a < hi][0]
            part = parts[0] if parts else None
            if part is None or _near(part, JOINT_E):
                w = ARCH_SHORT
            else:
                w = ARCH_LONG
                s = 1.0 if c > part else -1.0
                c = part + s * m2E(PIER / 2 + ARCH_LONG / 2)
            out.append(dict(c=c, w=w, lo=lo, hi=hi, bay=(blo, bhi), part=part))
    return out


def block_face_of(lo: float, hi: float):
    """The block side face bounding a portico / garden E-range, or None."""
    for a in S['axes']:
        if _near(lo, a + HALF, 1e-4):
            return west_face(lo)
        if _near(hi, a - HALF, 1e-4):
            return east_face(hi)
    return None


def segments():
    """Bar segments split at the expansion joint: (tag, E0, E1, block axes)."""
    g = m2E(GAP / 2)
    out = []
    for tag, e0, e1 in (('E', E_EAST, JOINT_E - g), ('W', JOINT_E + g, E_WEST)):
        out.append((tag, e0, e1, tuple(sorted(a for a in S['axes'] if e0 < a < e1))))
    return out


# ------------------------------------------------------------- geometry kit
def _box(bm, x0, x1, y0, y1, z0, z1):
    geo.add_box(bm, x0, x1, y0, y1, z0, z1)


def _on_face(bm, face, u0, u1, z0, z1, proud, back):
    """Box on a facade: `proud` m in front of the face, `back` m into the wall."""
    a, b = face.coord + face.out * proud, face.coord - face.out * back
    if face.axis == 'x':
        _box(bm, a, b, u0, u1, z0, z1)
    else:
        _box(bm, u0, u1, a, b, z0, z1)


def _octagon(cx, cy, r, n=8):
    return [(cx + r * math.cos(2 * math.pi * (k + 0.5) / n), cy + r * math.sin(2 * math.pi * (k + 0.5) / n))
            for k in range(n)]


def _pipe(bm, cx, cy, r, z0, z1):
    geo.add_prism_z(bm, _octagon(cx, cy, r), z0, z1)


def _arc_pts(u, w, spring, crown, n=12):
    """Intrados points of a segmental arch from u - w/2 to u + w/2 (springs excluded)."""
    pts = geo.arch_profile(u, w, spring, crown - spring, spring - 1.0, n)[3:-1]
    return list(reversed(pts))


def _lintel_outline(u0, u1, arches, z0, z1):
    """(u, z) outline of a lintel block u0..u1 (world u, ascending) with the
    segmental arches [(u, w)] notched out of its underside (spring = z0)."""
    pts = [(u0, z1), (u0, z0)]
    for u, w in sorted(arches):
        pts.append((u - w / 2, z0))
        pts += _arc_pts(u, w, z0, S['arch_crown'])
        pts.append((u + w / 2, z0))
    pts += [(u1, z0), (u1, z1)]
    return pts


def _vault_z(x: float) -> float:
    """Height of the core vault's copper surface (R CORE_VAULT_R, crown
    VAULT_CROWN) at distance x from the house axis."""
    zc = VAULT_CROWN - CORE_VAULT_R
    return zc + math.sqrt(max(CORE_VAULT_R ** 2 - x * x, 0.0))


def _panel_y() -> tuple[float, float]:
    """World y of the oculus panel's north (back) and south (front) faces."""
    return yY(Y_CORE) + PANEL_Y[0], yY(Y_CORE) + PANEL_Y[1]


def _verge(bm, E_face, inward, Y_low, Y_high, Tz):
    """Sloping concrete coping on an exposed pavilion end wall along the roof
    line, running 5 cm into the wall copings (as the towers' verges)."""
    sec = pavilion_section(Y_low, Y_high, Z0, Tz, WALL)
    (yl, zl), (yh, zh) = sec[5], sec[4]
    s = 1.0 if yY(Y_high) > yY(Y_low) else -1.0
    m = (zh - zl) / (yh - yl)
    ya, yb = yl - s * 0.05, yh + s * 0.05
    za, zb = zl + m * (ya - yl), zl + m * (yb - yl)
    prof = [(ya, za - 0.01), (yb, zb - 0.01), (yb, zb + 0.11), (ya, za + 0.11)]
    xf = xE(E_face)
    xa, xb = xf - inward * 0.019, xf + inward * 0.40      # 1 mm inside the coping ends
    geo.add_prism_x(bm, prof, min(xa, xb), max(xa, xb))


def _tiles(bm, E0, E1, Y_low, Y_high, Tz):
    """Clay-tile layer 5 cm thick on the roof plane between the long walls."""
    sec = pavilion_section(Y_low, Y_high, Z0, Tz, WALL)
    (yl, zl), (yh, zh) = sec[5], sec[4]
    geo.add_prism_x(bm, [(yl, zl), (yh, zh), (yh, zh + 0.05), (yl, zl + 0.05)],
                    min(xE(E0), xE(E1)), max(xE(E0), xE(E1)))


def _box_gutter(bm, E0, E1, Y_low, Y_high, Tz):
    """Copper box gutter at the low wall (roof rule: low coping with copper box gutter)."""
    sec = pavilion_section(Y_low, Y_high, Z0, Tz, WALL)
    yl, zl = sec[5]
    s = 1.0 if yY(Y_high) > yY(Y_low) else -1.0
    x0, x1 = sorted((xE(E0), xE(E1)))
    _box(bm, x0 + 0.01, x1 - 0.01, yl + s * 0.002, yl + s * 0.24, zl - 0.02, zl + 0.07)


# ---------------------------------------------------------------- the body
def _upper_profile(a: float):
    """(x, z) section across a block between the bar and the lean-to: L0
    volume up to the terrace floor and the side parapets (the core is
    _core_profile)."""
    xw, xe = xE(a + HALF), xE(a - HALF)
    top = S['terrace_parapet'] - COPING_H
    return [(xw, Z0), (xe, Z0), (xe, top), (xe - PARAPET_T, top), (xe - PARAPET_T, TERRACE_Z),
            (xw + PARAPET_T, TERRACE_Z), (xw + PARAPET_T, top), (xw, top)]


def _core_profile(y_bar: float, y_end: float):
    """(y, z) long section of a core above the terrace floor: up to the eave
    (under the flashing and vault) from the bar to the oculus panel's back face,
    then only up to the beam / copertina under the panel (SE 60 A-A, B-B) as far
    as the lean-to wall."""
    y_pn = _panel_y()[0]
    zb = TERRACE_Z - 0.01
    return [(y_end, zb), (y_bar, zb), (y_bar, CORE_TOP), (y_pn, CORE_TOP), (y_pn, Z_BEAM), (y_end, Z_BEAM)]


def _body(ctx, tag, E0, E1, axes):
    name = f'SM_Schiera_Body_{tag}'
    target = ctx.solid(name, COL, 'M_Brick',
                       lambda bm: add_pavilion(bm, E0, E1, S['bar_y'][0], Y_BAR, Z0, T, WALL))
    pieces = []
    y_up = (yY(Y_BAR) + 0.03, yY(Y_CORE) - 0.075)     # 3 cm into the bar, 7.5 cm into the lean-to wall
    for i, a in enumerate(axes):
        pieces.append(ctx.solid(f'SM_Schiera_Tmp_{tag}{i}a', COL, 'M_Brick',
                                lambda bm, a=a: geo.add_prism_y(bm, _upper_profile(a), y_up[1], y_up[0])))
        pieces.append(ctx.solid(f'SM_Schiera_Tmp_{tag}{i}c', COL, 'M_Brick',
                                lambda bm, a=a: geo.add_prism_x(bm, _core_profile(*y_up),
                                                                xE(a) - CORE_HW, xE(a) + CORE_HW)))
        pieces.append(ctx.solid(f'SM_Schiera_Tmp_{tag}{i}b', COL, 'M_Brick',
                                lambda bm, a=a: add_pavilion(bm, a - HALF, a + HALF, Y_S, Y_CORE, Z0, 0.0, WALL)))
    geo.boolean_union(target, pieces)
    target.name = target.data.name = name
    return target


class Cuts(Openings):
    """common.Openings, but the exact solver runs in self-intersection mode so
    that the collected cutters of one target may overlap (portico passages,
    arches, doors and lintel pockets); still ONE boolean per target with the
    cutter object kept in the hidden Cutters collection."""

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


def _lintels(E0, E1):
    """Precast lintel blocks 2.0 -> 2.80 over the portico arches of a segment:
    [(face, u0, u1, [(u, w)], u_joint or None)] in world u. North face (n13):
    one block per arch running 0.40 past it; over the paired arches of a
    partition bay two blocks butt on the partition axis with a 1 cm joint
    (n13: joint line over the 0.74 pier; each block has its own wall pocket,
    so the brick behind the joint closes it); cut at the expansion joint.
    South face (n6): a band across each bay between the walls (1 cm into
    them), cut at the expansion joint."""
    out = []
    fn, fs = north_face(Y_N), south_face(Y_BAR)
    groups = {}
    for p in porticoes():
        if E0 < p['c'] < E1:
            groups.setdefault(p['bay'], []).append(p)
    for (blo, bhi), ps in groups.items():
        arches = [(xE(p['c']), p['w']) for p in ps]
        if blo < JOINT_E < bhi:
            # joint bay: one portico of it per segment; blocks and band end at the joint
            (u, w), = arches
            uj = xE(E1) if ps[0]['c'] < JOINT_E else xE(E0)
            far = u + w / 2 + LINTEL_OV if uj < u else u - w / 2 - LINTEL_OV
            out.append((fn, min(uj, far), max(uj, far), arches, uj))
            wall = xE(blo) + 0.01 if uj < u else xE(bhi) - 0.01          # 1 cm into the block wall
            out.append((fs, min(uj, wall), max(uj, wall), arches, uj))
            continue
        if len(ps) == 2:
            # paired arches either side of a partition: two blocks with a joint on its axis
            uj = xE(ps[0]['part'])
            for u, w in arches:
                if u < uj:
                    out.append((fn, u - w / 2 - LINTEL_OV, uj - LINTEL_JOINT / 2, [(u, w)], None))
                else:
                    out.append((fn, uj + LINTEL_JOINT / 2, u + w / 2 + LINTEL_OV, [(u, w)], None))
        else:
            (u, w), = arches
            out.append((fn, u - w / 2 - LINTEL_OV, u + w / 2 + LINTEL_OV, arches, None))
        out.append((fs, xE(bhi) - 0.01, xE(blo) + 0.01, arches, None))
    return out


def _openings(ctx, body, tag, E0, E1, axes, bags):
    """All openings of one body in one exact difference."""
    op = Cuts(ctx, body)
    fn, fs, fl = north_face(Y_N), south_face(Y_BAR), south_face(Y_S)
    sills = bags['sills']
    y_in_n = yY(Y_N) - WALL                   # inner face of the north wall
    y_in_s = yY(Y_BAR) + WALL                 # inner face of the south wall
    ports = [p for p in porticoes() if E0 < p['c'] < E1]
    for p in ports:
        # the portico passage through the bar (floor 0.00, ceiling = L1 slab underside)
        x0, x1 = sorted((xE(p['lo']), xE(p['hi'])))
        _box(op.cut, x0, x1, y_in_s, y_in_n, 0.0, CEILING)
        # arches on both faces, cut right through the walls
        for f in (fn, fs):
            op.arch(f, p['c'], 0.0, 0.0, p['w'], S['arch_spring'], S['arch_crown'], through=WALL)
        # kitchen door from the portico in the block side wall (n27)
        bf = block_face_of(p['lo'], p['hi'])
        if bf is not None:
            dw, _, dh = DOOR
            op.rect(bf, DOOR_Y, 0.0, 0.0, dw, dh, pane=False, recess=0.20)
            ud = u_on(bf, DOOR_Y)
            a = bf.coord - bf.out * 0.155
            b = bf.coord - bf.out * 0.195
            bm = bags['doors']
            if bf.axis == 'x':
                _box(bm, a, b, ud - dw / 2 + 0.005, ud + dw / 2 - 0.005, 0.005, dh - 0.005)
        # L1 window above each arch on the south face, 1.04 x 1.41 (3.95 -> 5.36)
        w, so, hd = WIN_STD
        op.rect(fs, p['c'], 0.0, T + so, w, hd - so)
        sills.append((fs, xE(p['c']), w, T + so))
    # lintel pockets: the precast blocks take the full wall depth
    for f, u0, u1, arches, uj in _lintels(E0, E1):
        a0, a1 = u0, u1
        if uj is not None:                   # run out through the joint end of the segment
            a0, a1 = (u0 - 0.05, u1) if _near(u0, uj) else (u0, u1 + 0.05)
        op.outline(f, [(a0, S['arch_spring']), (a1, S['arch_spring']), (a1, S['arch_block_top']),
                       (a0, S['arch_block_top'])], WALL)
    for a in axes:
        # north face L1: pairs of 0.91 x 0.92 (4.44 -> 5.36) beside the party axis
        w, so, hd = WIN_SMALL
        for d in NORTH_PAIR:
            op.rect(fn, a + d, 0.0, T + so, w, hd - so)
            sills.append((fn, xE(a + d), w, T + so))
        # terrace doors in the bar's south wall at axis +-1.68 module
        for s in (-1, 1):
            op.rect(fs, a + s * TERRACE_DOOR_DX, 0.0, T, TERRACE_DOOR_W, HEAD)
        # lean-to south face: two 1.04 x 1.41 windows (0.94 -> 2.35) at axis +-1 module
        w, so, hd = WIN_STD
        for s in (-1, 1):
            op.rect(fl, a + s * LEAN_WIN_DX, 0.0, so, w, hd - so)
            sills.append((fl, xE(a + s * LEAN_WIN_DX), w, so))
        # garden-side walls: two French windows each (n27, n37, n5 end elevation)
        for f in (east_face(a - HALF), west_face(a + HALF)):
            for Yf in FRENCH_Y:
                op.rect(f, Yf, 0.0, FRENCH[1], FRENCH_W, FRENCH[2] - FRENCH[1])
        # dark recess behind the oculi in the core's south face (= the panel's back face)
        fc = geo.Face('y', _panel_y()[0], -1)
        P = S['panel']
        for s in (-1, 1):
            op.outline(fc, geo.circle_profile(xE(a) - s * P['dx'], P['oculus_z'], P['oculus_d'] / 2), 0.35)
    op.apply()
    # paving on the portico floors / thresholds and the terraces, plaster soffits
    geo.assign_material_by_normal(body, [
        (ctx.mats['M_Paving'], lambda c, n: n.z > 0.99 and (abs(c.z) < 0.005 or TERRACE_Z - 0.005 < c.z < T + 0.005)),
        (ctx.mats['M_Plaster'], lambda c, n: n.z < -0.99 and abs(c.z - CEILING) < 0.005),
    ])


# ------------------------------------------------------------ concrete trim
def _trim(ctx, bags):
    bm = bmesh.new()
    fn, fs, fl = north_face(Y_N), south_face(Y_BAR), south_face(Y_S)
    xw, xe = xE(E_WEST), xE(E_EAST)
    for tag, E0, E1, axes in segments():
        # bar copings 7.10 / 5.91, flush with the wall ends at the joint
        e0 = E0 + (m2E(0.02) if _near(E0, JOINT_E + m2E(GAP / 2)) else 0.0)
        e1 = E1 - (m2E(0.02) if _near(E1, JOINT_E - m2E(GAP / 2)) else 0.0)
        add_copings(bm, e0, e1, S['bar_y'][0], Y_BAR, T, WALL)
        # precast lintel blocks over the portico arches (n13, n6), full wall depth
        for f, u0, u1, arches, uj in _lintels(E0, E1):
            outline = _lintel_outline(u0, u1, arches, S['arch_spring'], S['arch_block_top'])
            f.solid(bm, outline, WALL, outside=0.03)
    # sloping verges on the exposed bar ends
    _verge(bm, E_EAST, -1, S['bar_y'][0], Y_BAR, T)
    _verge(bm, E_WEST, +1, S['bar_y'][0], Y_BAR, T)
    # lintel band 5.36 -> 5.49 round the bar (north, south, both ends); on the south face
    # it stops 1 cm inside each core's side walls, which rise to the same eave (5.49)
    _on_face(bm, fn, xw - BAND_PROUD, xe + BAND_PROUD, *BAND, BAND_PROUD, BAND_BACK)
    stops = [xw - BAND_PROUD]
    for a in sorted(S['axes'], reverse=True):            # west -> east = ascending x
        stops += [xE(a) - CORE_HW + 0.01, xE(a) + CORE_HW - 0.01]
    stops.append(xe + BAND_PROUD)
    for i in range(0, len(stops), 2):
        _on_face(bm, fs, stops[i], stops[i + 1], *BAND, BAND_PROUD, BAND_BACK)
    yn, ys = yY(Y_N) + 0.028, yY(Y_BAR) - 0.028
    _on_face(bm, east_face(E_EAST), ys, yn, *BAND, BAND_PROUD - 0.002, BAND_BACK)
    _on_face(bm, west_face(E_WEST), ys, yn, *BAND, BAND_PROUD - 0.002, BAND_BACK)
    for a in S['axes']:
        xa0, xa1 = xE(a + HALF), xE(a - HALF)
        # lean-to copings 4.10 / 2.90 and verges on both block sides
        add_copings(bm, a - HALF, a + HALF, Y_S, Y_CORE, 0.0, WALL)
        _verge(bm, a - HALF, -1, Y_S, Y_CORE, 0.0)
        _verge(bm, a + HALF, +1, Y_S, Y_CORE, 0.0)
        # copertina under and in front of the oculus panel (SE 60 B-B), 3.98 -> 4.09 (the
        # panel's base), from the core's south face to the lean-to's high coping, 2 cm
        # past the core's side walls
        xc = xE(a)
        _box(bm, xc - CORE_HW - 0.02, xc + CORE_HW + 0.02, _panel_y()[0], yY(Y_CORE) + 0.02,
             Z_BEAM, S['panel']['base'])
        # terrace side parapet copings to 4.09
        top = S['terrace_parapet']
        for xo, inward in ((xa1, -1), (xa0, +1)):
            xa, xb = xo - inward * 0.017, xo + inward * (PARAPET_T + 0.02)
            _box(bm, min(xa, xb), max(xa, xb), yY(Y_CORE) - 0.05, yY(Y_BAR) + 0.005, top - COPING_H, top)
        # L0 band 2.35 -> 2.48 on the lean-to south face and the garden-side walls
        _on_face(bm, fl, xa0 - BAND_PROUD, xa1 + BAND_PROUD, *BAND_L0, BAND_PROUD, BAND_BACK)
        for f in (east_face(a - HALF), west_face(a + HALF)):
            _on_face(bm, f, yY(Y_S) + 0.028, yY(Y_BAR) + 0.005, *BAND_L0, BAND_PROUD - 0.002, BAND_BACK)
    # window sills: 4 cm proud, 8 cm past the reveals
    for f, u, w, z in bags['sills']:
        _on_face(bm, f, u - w / 2 - 0.08, u + w / 2 + 0.08, z - 0.06, z + 0.01, 0.04, 0.115)
    # copings of the low walls in the north arches, 1.17 -> 1.25; like the walls they
    # stop 1 cm short of the inner wall face (no coplanar overlap at the jambs)
    lw, lt = LOW_WALL
    for p in porticoes():
        u, w = xE(p['c']), p['w']
        y0 = yY(Y_N) + 0.02 - LOW_WALL_SET
        for ua, ub in ((u - w / 2 - 0.005, u - w / 2 + lw + 0.02), (u + w / 2 - lw - 0.02, u + w / 2 + 0.005)):
            _box(bm, ua, ub, yY(Y_N) - WALL + LOW_WALL_IN, y0, lt - 0.08, lt)
    return geo.object_from_bmesh(bm, 'SM_Schiera_Trim', ctx.col(COL), ctx.mats['M_Concrete'])


# ---------------------------------------------------------- oculus panels
def _panels(ctx):
    """Precast concrete panels closing the cores to the south (SE 60): 4.17 wide,
    on the 4.09 copertina, sides 5.57, arc R 6.50 with crown 5.91, oculi Ø 0.60
    at z 4.66, axis +-0.825 m; 0.14 thick, Y 32.785 -> 32.87, against the core's
    south end, with the copertina and the lean-to roof starting in front of it."""
    P = S['panel']
    hw = P['w'] / 2
    R = 6.50                                  # SE 60 "r = 6.50"
    zc = P['crown'] - R
    z_side = zc + math.sqrt(R * R - hw * hw)  # 5.567 ~ P['side'] 5.57
    a0 = math.atan2(z_side - zc, hw)
    y_back, y_front = _panel_y()

    def fill(bm):
        for a in S['axes']:
            xa = xE(a)
            pts = [(xa - hw, P['base']), (xa + hw, P['base']), (xa + hw, z_side)]
            n = 16
            for k in range(1, n):
                ang = a0 + (math.pi - 2 * a0) * k / n
                pts.append((xa + R * math.cos(ang), zc + R * math.sin(ang)))
            pts.append((xa - hw, z_side))
            geo.add_prism_y(bm, pts, y_front, y_back)
    obj = ctx.solid('SM_Schiera_Panel', COL, 'M_Concrete', fill)
    op = Cuts(ctx, obj)
    f = geo.Face('y', y_front, -1)
    for a in S['axes']:
        for s in (-1, 1):
            op.round(f, a, s * P['dx'], P['oculus_z'], P['oculus_d'])
    op.apply()
    return obj


# ------------------------------------------------------------- tiles, copper
def _roofs(ctx):
    bm = bmesh.new()
    for tag, E0, E1, axes in segments():
        _tiles(bm, E0, E1, S['bar_y'][0], Y_BAR, T)
    for a in S['axes']:
        _tiles(bm, a - HALF, a + HALF, Y_S, Y_CORE, 0.0)
    return geo.object_from_bmesh(bm, 'SM_Schiera_Roof', ctx.col(COL), ctx.mats['M_RoofTile'])


def _copper(ctx):
    bm = bmesh.new()
    # vault and flashings from the panel's back face (1 mm off) to the bar's south face
    y0, y1 = _panel_y()[0] + 0.001, yY(Y_BAR) - 0.003
    zb = CORE_TOP - 0.02                       # vault base, 2 cm inside the brick core
    h = math.sqrt(CORE_VAULT_R ** 2 - (zb - VAULT_CROWN + CORE_VAULT_R) ** 2)
    n = 16
    ft, fo, fi = FLASH
    for a in S['axes']:
        xa = xE(a)
        # copper vault R 6.00 spanning E-W, crown T+2.70 = 5.71 (spec 3 roof rule, SE 59, n5)
        arc = [(xa - h + 2 * h * k / n, _vault_z(-h + 2 * h * k / n)) for k in range(1, n)]
        geo.add_prism_y(bm, [(xa - h, zb), (xa + h, zb)] + list(reversed(arc)), y0, y1)
        # copper flashings on the core walls: the eave line at 5.49 (SE 59 "scossalina in rame")
        for s in (-1, 1):
            xa_, xb_ = xa + s * fi, xa + s * (CORE_HW + fo)
            _box(bm, min(xa_, xb_), max(xa_, xb_), y0, y1, EAVE - ft + 0.005, EAVE + 0.005)
        # twin flue pipes on the party axis against the bar's south wall (spec 9, n5, n39)
        yc = yY(Y_BAR) - FLUE['dy']
        for s in (-1, 1):
            _pipe(bm, xa + s * FLUE['dx'], yc, FLUE['r'], FLUE['z0'], FLUE['top'] - 0.07)
            _pipe(bm, xa + s * FLUE['dx'], yc, FLUE['r'] + 0.03, FLUE['top'] - 0.07, FLUE['top'])
        # downpipe on the north face between the window pair, from the box gutter, standing
        # on the -0.45 paving; hopper and clips run 1 cm into the wall
        yw = yY(Y_N)
        yp = yw + PIPE_OFF + PIPE_R
        _pipe(bm, xa, yp, PIPE_R, Z_PAVING, 5.52)
        _box(bm, xa - 0.11, xa + 0.11, yw - 0.01, yw + 0.20, 5.50, 5.74)
        for zc in (1.50, 3.40):
            _box(bm, xa - 0.015, xa + 0.015, yw - 0.01, yp, zc, zc + 0.04)
        # lean-to downpipes inside the block corners (n6, n26): hopper, clips and a shoe
        # turning back into the wall just above the quay (the face is 5 cm from the rio)
        yw = yY(Y_S)
        yp = yw - PIPE_OFF - PIPE_R
        for s in (-1, 1):
            xp = xa + s * (HALF * M - DOWNPIPE_DX)
            _pipe(bm, xp, yp, PIPE_R, SHOE_Z + 0.05, 2.52)
            _box(bm, xp - 0.11, xp + 0.11, yw - 0.20, yw + 0.01, 2.50, 2.74)
            _box(bm, xp - 0.04, xp + 0.04, yp - 0.04, yw + 0.03, SHOE_Z, SHOE_Z + 0.10)
            for zc in (0.80, 1.80):
                _box(bm, xp - 0.015, xp + 0.015, yp, yw + 0.01, zc, zc + 0.04)
        _box_gutter(bm, a - HALF, a + HALF, Y_S, Y_CORE, 0.0)
    for tag, E0, E1, axes in segments():
        _box_gutter(bm, E0, E1, S['bar_y'][0], Y_BAR, T)
    return geo.object_from_bmesh(bm, 'SM_Schiera_Copper', ctx.col(COL), ctx.mats['M_Copper'])


# ------------------------------------------------- masonry, gardens, steps
def _garden_ranges():
    """Clear E-ranges of the gardens (between block walls, dividing walls and the
    garden end walls)."""
    out = []
    for lo, hi in bays():
        if _near(lo, E_EAST + WM):
            lo = E_EAST + m2E(GW_T)
        if _near(hi, E_WEST - WM):
            hi = E_WEST - m2E(GW_T)
        parts = [p for p in S['garden_walls_e'] if lo < p < hi]
        if parts:
            t = m2E(GW_T / 2)
            out += [(lo, parts[0] - t), (parts[0] + t, hi)]
        else:
            out.append((lo, hi))
    return out


def _masonry(ctx):
    """Brick: low walls inside the north arches; garden walls to +1.22 (coping
    1.10 -> 1.22 separate): south walls Y 34.97 (+0.25), dividing walls on
    E 31.5 / 23.5 / 15.5, end walls flush with the bar's end faces."""
    bm = bmesh.new()
    lw, lt = LOW_WALL
    for p in porticoes():
        u, w = xE(p['c']), p['w']
        y0 = yY(Y_N) - LOW_WALL_SET
        for ua, ub in ((u - w / 2 - 0.005, u - w / 2 + lw), (u + w / 2 - lw, u + w / 2 + 0.005)):
            _box(bm, ua, ub, yY(Y_N) - WALL + LOW_WALL_IN, y0, -0.05, lt - 0.08)
    top = Z_GARDEN_WALL - COPING_H
    ys_in, ys_out = yY(GW_Y), yY(GW_Y + m2E(GW_T))
    d = m2E(0.03)
    for lo, hi in bays():
        lo_ = E_EAST + m2E(GW_T) if _near(lo, E_EAST + WM) else lo
        hi_ = E_WEST - m2E(GW_T) if _near(hi, E_WEST - WM) else hi
        _box(bm, xE(lo_ - d), xE(hi_ + d), ys_out, ys_in, Z0, top)
    for p in S['garden_walls_e']:
        t = m2E(GW_T / 2)
        _box(bm, xE(p - t), xE(p + t), ys_in - 0.03, yY(Y_BAR) + 0.03, Z0, top)
    for e0, e1 in ((E_EAST, E_EAST + m2E(GW_T)), (E_WEST - m2E(GW_T), E_WEST)):
        # flush with the bar's end face: stop at the bar (no coplanar overlap), and
        # 1 mm proud of the south wall's outer face that runs into it
        _box(bm, xE(e0), xE(e1), ys_out - 0.001, yY(Y_BAR), Z0, top)
    return geo.object_from_bmesh(bm, 'SM_Schiera_Masonry', ctx.col(COL), ctx.mats['M_Brick'])


def _garden_copings(ctx):
    bm = bmesh.new()
    zc0, zc1 = Z_GARDEN_WALL - COPING_H, Z_GARDEN_WALL
    ys_in, ys_out = yY(GW_Y), yY(GW_Y + m2E(GW_T))
    for lo, hi in bays():
        lo_ = E_EAST + m2E(GW_T) if _near(lo, E_EAST + WM) else lo
        hi_ = E_WEST - m2E(GW_T) if _near(hi, E_WEST - WM) else hi
        _box(bm, xE(hi_) - 0.01, xE(lo_) + 0.01, ys_out - 0.02, ys_in + 0.02, zc0, zc1)
    for p in S['garden_walls_e']:
        xp = xE(p)
        # 1 mm lower than the south copings they run into: no coplanar overlapping tops
        _box(bm, xp - GW_T / 2 - 0.02, xp + GW_T / 2 + 0.02, ys_in + 0.015, yY(Y_BAR) + 0.005, zc0, zc1 - 0.001)
    for e0, e1 in ((E_EAST, E_EAST + m2E(GW_T)), (E_WEST - m2E(GW_T), E_WEST)):
        x0, x1 = sorted((xE(e0), xE(e1)))
        _box(bm, x0 - 0.02, x1 + 0.02, ys_out - 0.021, yY(Y_BAR) + 0.005, zc0, zc1 - 0.001)
    return geo.object_from_bmesh(bm, 'SM_Schiera_GardenCoping', ctx.col(COL), ctx.mats['M_Concrete'])


def _gardens(ctx):
    """Garden ground (lawn) just under 0.00 (spec 6: gardens ~0.00)."""
    bm = bmesh.new()
    for lo, hi in _garden_ranges():
        _box(bm, xE(hi) + 0.002, xE(lo) - 0.002, yY(GW_Y) + 0.002, yY(Y_BAR) - 0.002, Z0, -0.02)
    return geo.object_from_bmesh(bm, 'SM_Schiera_Gardens', ctx.col(COL), ctx.mats['M_Grass'])


def _steps(ctx):
    """Two steps (risers 0.15, treads 0.25) up to the 0.00 threshold in front of
    each north arch, between the low walls (n13, n27)."""
    bm = bmesh.new()
    tr, rs = STEP
    yf = yY(Y_N)
    lw = LOW_WALL[0]
    for p in porticoes():
        u, w = xE(p['c']), p['w']
        u0, u1 = u - w / 2 + lw + 0.002, u + w / 2 - lw - 0.002
        _box(bm, u0, u1, yf + 2 * tr, yf + tr, Z0, -2 * rs)
        _box(bm, u0, u1, yf + tr - 0.001, yf - 0.005, Z0, -rs)
    return geo.object_from_bmesh(bm, 'SM_Schiera_Steps', ctx.col(COL), ctx.mats['M_Paving'])


# --------------------------------------------------------------------- build
def build(ctx):
    _tile_material(ctx)
    bags = {'sills': [], 'doors': bmesh.new()}
    for tag, E0, E1, axes in segments():
        body = _body(ctx, tag, E0, E1, axes)
        _openings(ctx, body, tag, E0, E1, axes, bags)
    _trim(ctx, bags)
    geo.object_from_bmesh(bags['doors'], 'SM_Schiera_Doors', ctx.col(COL), ctx.mats['M_Frame'])
    _panels(ctx)
    _roofs(ctx)
    _copper(ctx)
    _masonry(ctx)
    _garden_copings(ctx)
    _gardens(ctx)
    _steps(ctx)
