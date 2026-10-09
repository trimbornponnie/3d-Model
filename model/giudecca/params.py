"""Every dimension of the model, taken from docs/ANALYSIS.md (v2, verified).

Plan coordinates are in modules (1 module = 1.65 m):
  E  east -> west, uniform (E = X on tower axes, E = X - 0.5 on carpet/schiera axes)
  Y  north -> south
Heights z are metres, 0.00 = finished ground floor of the dwellings.
"""

MODULE = 1.65

# ------------------------------------------------------------------- levels
FLOORS = (0.00, 3.01, 6.02, 9.02)      # L0..L3
SLAB = 0.30                            # floor slab thickness (2.71 clear + 0.30)
Z_PAVING = -0.45                       # piazza, calli, north apron, campo, porticoes
Z_COURT = -0.10                        # light courts and gardens
Z_GARDEN_WALL = 1.22
Z_WATER = -2.50                        # "medio mare"
Z_FOUND = -2.60                        # bottom of everything that stands in the water

WALL = 0.395                           # exterior wall 37 + 2.5 cm (SE 50/53)
WALL_M = WALL / MODULE

# roof rule (T = top-floor level of the part)
ROOF_HIGH = 4.10                       # high (outer) coping
ROOF_LOW = 2.90                        # low (inner) coping, with copper box gutter
HEAD_BAND = (2.35, 2.48)               # 13 cm concrete head bands, z_f + 2.35 -> 2.48 on every part (spec 4, n47 chain
                                       # "13 | 1,48 | 13 | 2,88", n61, n7); the one source for the part modules' bands
CORE_EAVE = 2.48                       # core E/W walls, copper gutter
CORE_CROWN = 2.70                      # core vault crown (R 6.00 spanning E-W)
CORE_VAULT_R = 6.00
COPING_H = 0.12                        # coping height; width = wall + 2 cm overhang (common.add_copings)

# ------------------------------------------------------------------- towers
TOWER = dict(
    count=5, pitch=8.0,
    y_first=-4.225,            # north face of tower k = y_first + 8k
    pav=2.4485,                # 4.04 m  (north pavilion, south pavilion)
    mid=2.5515,                # 4.21 m  middle part
    gap=0.5515,                # 0.91 m
    e_outer=-0.20, e_band=0.78, e_inner=4.22, e_inner_mid=4.12,
    e_stair_hall=2.86,         # stair-hall block E 2.86 -> 4.12
    top=13.12, low=11.93,
    terrace_parapet=9.97, terrace_parapet_t=0.30,
    mid_lean_low=8.92, mid_lean_high=10.05,
    hall_roof=(11.40, 11.73),
    patio_wall=(-0.12, 0.04, 1.26),          # (E0, E1, top) low front wall of the middle void
    mirror_axis=36.0,                        # west column: E' = 72 - E
    chimney=dict(bracket=(11.55, 11.90), top=13.85, w=0.80, d=0.45),   # measured on n64
    water_stair=dict(e_top=2.45, e_bottom=0.25, risers=13),
)
# tower length 2 pav + mid = 7.4485 (12.29 m = 4.04 | 4.21 | 4.04); south face of tower k at
# Y 3.2235 + 8k (spec 4 rounds it to 3.225 + 8k); gap = pitch - length = 0.5515
TOWER['length'] = 2 * TOWER['pav'] + TOWER['mid']

# ------------------------------------------------------------------- carpet
PAV = 2.4485                   # pavilion depth (4.04 m)
CORE_ZONE = 2.5515             # 4.21 m
ROWS = {
    #        T     floors  core-zone centre
    'N': dict(T=9.02, levels=4, yc=3.5),
    'M': dict(T=6.02, levels=3, yc=11.5),
    'S': dict(T=3.01, levels=2, yc=19.5),
}
for _r in ROWS.values():
    _r['npav'] = (_r['yc'] - CORE_ZONE / 2 - PAV, _r['yc'] - CORE_ZONE / 2)
    _r['core'] = (_r['yc'] - CORE_ZONE / 2, _r['yc'] + CORE_ZONE / 2)
    _r['spav'] = (_r['yc'] + CORE_ZONE / 2, _r['yc'] + CORE_ZONE / 2 + PAV)
# expansion joints between the rows (0.91 m): (Y0, Y1, deck z), Y from the rows' pavilion faces
JOINTS = {'NM': (ROWS['N']['spav'][1], ROWS['M']['npav'][0], 9.15),       # 7.22425 -> 7.77575
          'MS': (ROWS['M']['spav'][1], ROWS['S']['npav'][0], 6.15)}       # 15.22425 -> 15.77575

BLOCKS = {
    # faces (east, west), house axes, party walls, expansion joints
    'east': dict(faces=(5.28, 41.72), axes=(8.5, 14.5, 20.5, 26.5, 32.5, 38.5),
                 party=(11.5, 17.5, 23.5, 29.5, 35.5), joints=(17.5, 29.5)),
    'west': dict(faces=(42.28, 66.72), axes=(45.5, 51.5, 57.5, 63.5),
                 party=(48.5, 54.5, 60.5), joints=(54.5,)),
}
CORE_W = 4.10                  # metres, centred on the house axis
CORE_PIER_OFFSET = 1.15        # modules, corner piers of the floating north-row cores
NOTCH_HALF = 1.485             # metres, notch on every core axis (north S-pav, middle N-pav)
CAMPO = dict(e=(35.5, 48.5), pier_rows=(7.1, 8.1),
             pier_offset=1.12, pier_top=5.06, band_top=5.80,
             l2_south=8.24, stairs_y=(1.7, 5.6))   # stairs on the court-arch axes (n11)
CAMPO_HOUSES = (38.5, 45.5)    # house axes inside the campo

# ground floor of the carpet
PORTICO_PIER_ROWS = (2.11, 4.95)
CANTINE_N = ((9.75, 19.6), (21.6, 31.45), (52.55, 62.25))   # enclosed L0 E-ranges, north row S-pav band
CORRIDOR_NM = (7.24, 7.98)
PASSAGE_M = (13.0, 15.0)
GALLERY = dict(deck_y=(0.45, ROWS['N']['npav'][1]), parapet_top=3.87, parapet_t=0.15)   # deck to Y 2.22425

# north arcade (offsets in metres from the house axis; + = west)
ARCADE = dict(
    central_pier=0.53, flat_w=1.22, flat_head=5.10, flat_panel_top=5.57,
    pier=0.74, arch_w=2.355, arch_w_short=2.15, spring=5.10,
    crown=5.585, crown_short=5.545, panel_top=5.86, end_pier=0.945,
)
TRIFORA = dict(offset=2.475, width=1.87, side=0.415, centre=1.04,
               sill_side=9.96, sill_centre=9.68, spring=11.02, crown=11.37,
               lintel=(2.52, 11.02, 11.55))
EXT_STAIRS = dict(e=(10.56, 55.50), y_north=-3.70, landing=(-2.94, -2.33),
                  y_top=0.25, risers=(5, 15), riser=0.172, tread=0.30,
                  clear=1.19, side=0.255)
OCULUS_PANEL = dict(lower_w=2.95, lower_top=10.10, upper_w=3.76, radius=6.50,
                    crown=11.92, oculus_d=0.90, oculus_z=10.67, oculus_dx=0.825)
# (its position, on the joint's south edge, is derived in carpet.OCULUS_Y)

# standard openings (SE 53): width, sill offset, head offset above floor
WIN_STD = (1.04, 0.94, 2.35)
WIN_SMALL = (0.91, 1.43, 2.35)          # towers / schiera "finestre"
FRENCH = (1.04, 0.10, 2.35)
DOOR = (0.91, 0.00, 2.04)
CORE_WIN = (0.60, 1.20, 1.80)

# ------------------------------------------------------------------- schiera
SCHIERA = dict(
    e=(7.28, 39.72), y=(28.78, 35.22),
    bar_y=(28.78, 31.22), core_y=(31.22, 32.93), lean_y=(32.93, 35.22),
    axes=(35.5, 27.5, 19.5, 11.5), block_half=2.224, core_half=1.14,
    joint=23.5, bar_low=5.91, bar_high=7.10,
    lean_high=4.10, lean_low=2.90, terrace_parapet=4.09,
    panel=dict(w=4.17, side=5.57, crown=5.91, base=4.09, oculus_d=0.60, oculus_z=4.66, dx=0.825),
    vault_crown=5.71,                       # T + CORE_CROWN (n5 section F, SE 59)
    arches=(8.5, 14.5, 16.5, 22.5, 24.5, 30.5, 32.5, 38.5),
    arch_spring=2.0, arch_crown=2.5, arch_block_top=2.80,
    garden_y=(31.22, 34.97), garden_walls_e=(31.5, 23.5, 15.5),
    ground=-0.40,
)

# ------------------------------------------------------------------- site
SITE = dict(
    land_e=(-0.20, 72.20), land_y=(-27.0, 35.25),
    garden_e=(11.0, 55.0), garden_y=(-26.5, -4.7), garden_wall=2.0,
    square_e=(39.72, 67.78), square_y=(25.0, 35.25),
    # from the south face of the south row, Y 23.22425 (ROWS['S']['spav'][1])
    gardens_s=dict(east=((5.28, 41.72), (ROWS['S']['spav'][1], 27.0)),
                   west=((42.28, 66.72), (ROWS['S']['spav'][1], 25.0))),
    water_e=(-30.0, 110.0), water_y=(-40.0, 80.0),
    rio_east_far=-7.0, rio_south_far=40.5, canal_west_far=108.0,
    footbridge_e=(4.4, 5.5),
)
