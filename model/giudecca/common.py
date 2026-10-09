"""Shared helpers in drawing coordinates (E, Y modules; z metres).

World: x = (36 - E) * 1.65 (east = +x), y = (15.5 - Y) * 1.65 (north = +y).
Metric offsets "dm" along E or Y are in metres and follow the drawing
direction: +dm along E is westward (-x), +dm along Y is southward (-y).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import bmesh
import bpy

from . import geo
from .params import MODULE, COPING_H, ROOF_HIGH, ROOF_LOW

E0_WORLD, Y0_WORLD = 36.0, 15.5


def xE(E: float, dm: float = 0.0) -> float:
    return (E0_WORLD - E) * MODULE - dm


def yY(Y: float, dm: float = 0.0) -> float:
    return (Y0_WORLD - Y) * MODULE - dm


def mE(E: float) -> float:
    """Module length -> metres."""
    return E * MODULE


# ------------------------------------------------------------------ façades
def north_face(Y: float) -> geo.Face:
    """Face whose outward normal points north, plane at row coordinate Y."""
    return geo.Face('y', yY(Y), +1)


def south_face(Y: float) -> geo.Face:
    return geo.Face('y', yY(Y), -1)


def east_face(E: float) -> geo.Face:
    return geo.Face('x', xE(E), +1)


def west_face(E: float) -> geo.Face:
    return geo.Face('x', xE(E), -1)


def u_on(face: geo.Face, along: float, dm: float = 0.0) -> float:
    """Along-face world coordinate for a drawing coordinate: for north/south
    faces `along` is an E value, for east/west faces a Y value."""
    return xE(along, dm) if face.axis == 'y' else yY(along, dm)


# ------------------------------------------------------------------- solids
def box_EY(bm, E0: float, E1: float, Y0: float, Y1: float, z0: float, z1: float) -> None:
    geo.add_box(bm, xE(E0), xE(E1), yY(Y0), yY(Y1), z0, z1)


def poly_EY(bm, pts_EY, z0: float, z1: float) -> None:
    geo.add_prism_z(bm, [(xE(e), yY(y)) for e, y in pts_EY], z0, z1)


def pavilion_section(Y_low: float, Y_high: float, z0: float, T: float,
                     wall: float = 0.37) -> list[tuple[float, float]]:
    """(y_world, z) section of a mono-pitch pavilion between its low (inner)
    side Y_low and high (outer) side Y_high, following the roof rule.

    The walls stop COPING_H under the coping tops (T+4.10 high, T+2.90 low);
    add_copings() puts the concrete copings on them. The tiled roof plane runs
    between the walls 0.10 m under the wall tops (~36 %, drawn as 34 %).
    Works whichever of Y_low / Y_high is north."""
    yl, yh = yY(Y_low), yY(Y_high)
    s = 1.0 if yh > yl else -1.0          # world-y direction from low to high side
    H, L = T + ROOF_HIGH - COPING_H, T + ROOF_LOW - COPING_H
    return [
        (yl, z0), (yh, z0), (yh, H),
        (yh - s * wall, H), (yh - s * wall, H - 0.10),
        (yl + s * wall, L - 0.10), (yl + s * wall, L), (yl, L),
    ]


def add_pavilion(bm, E0: float, E1: float, Y_low: float, Y_high: float,
                 z0: float, T: float, wall: float = 0.37) -> None:
    geo.add_prism_x(bm, pavilion_section(Y_low, Y_high, z0, T, wall), xE(E1), xE(E0))


def add_copings(bm, E0: float, E1: float, Y_low: float, Y_high: float, T: float,
                wall: float = 0.37, high: bool = True, low: bool = True) -> None:
    """Concrete copings (SE 54) on a pavilion's high and low walls: the wall
    width plus 2 cm overhang outside, COPING_H high, tops at T+4.10 / T+2.90."""
    yl, yh = yY(Y_low), yY(Y_high)
    s = 1.0 if yh > yl else -1.0
    x0, x1 = xE(E1) - 0.02, xE(E0) + 0.02
    if high:
        geo.add_box(bm, x0, x1, yh + 0.02 * s, yh - s * wall, T + ROOF_HIGH - COPING_H, T + ROOF_HIGH)
    if low:
        geo.add_box(bm, x0, x1, yl - 0.02 * s, yl + s * wall, T + ROOF_LOW - COPING_H, T + ROOF_LOW)


# ------------------------------------------------------------- build context
@dataclass
class Ctx:
    mats: dict
    root: bpy.types.Collection
    cutters: bpy.types.Collection
    cols: dict = field(default_factory=dict)

    def col(self, name: str) -> bpy.types.Collection:
        if name not in self.cols:
            self.cols[name] = geo.collection(f'COL_{name}', self.root)
        return self.cols[name]

    def solid(self, name: str, col: str, mat: str, fill) -> bpy.types.Object:
        """Create one closed object from a bmesh filled by `fill(bm)`."""
        bm = bmesh.new()
        fill(bm)
        return geo.object_from_bmesh(bm, name, self.col(col), self.mats[mat])


class Openings:
    """Collects cutters and glass panes for one target object, then applies
    them in a single exact boolean (skill: cutters in a hidden collection)."""

    def __init__(self, ctx: Ctx, target: bpy.types.Object, glass_name: str | None = None,
                 col: str | None = None):
        self.ctx, self.target = ctx, target
        self.cut = bmesh.new()
        self.panes = bmesh.new()
        self.glass_name = glass_name or f'{target.name}_Glass'
        self.col = col

    def rect(self, face, along, dm, z0, w, h, through=None, pane=True, recess=0.0):
        geo.opening(face, self.cut, self.panes, u_on(face, along, dm), z0, w, h,
                    through=through, pane=pane, recess=recess)

    def arch(self, face, along, dm, z0, w, spring, crown, through=None, pane=True):
        geo.opening(face, self.cut, self.panes, u_on(face, along, dm), z0, w,
                    crown - z0, arch_rise=crown - spring, through=through, pane=pane)

    def outline(self, face, outline_uz, depth):
        """Arbitrary (u, z) cutter outline (world u)."""
        face.solid(self.cut, outline_uz, depth)

    def round(self, face, along, dm, zc, d):
        geo.round_window(face, self.cut, self.panes, u_on(face, along, dm), zc, d)

    def apply(self):
        geo.boolean_difference(self.target, self.cut, self.ctx.cutters)
        if len(self.panes.faces):
            col = self.ctx.col(self.col) if self.col else self.target.users_collection[0]
            geo.object_from_bmesh(self.panes, self.glass_name, col, self.ctx.mats['M_Glass'])
        else:
            self.panes.free()
