"""Construction build-ups (docs/INTERIORS.md section 2; SE 50, 51, 53, 54, 56,
58, 59, 60, 63, 64, 65): layer stacks for the interior engine.

Each stack is a list of (element, material, thickness in m), outermost /
topmost first; material None is an air gap (not built). Element names become
part of the object names (SM_<Part>_<Prefix><Element>_<Tag>), so layers of the
same material in one stack share an object.

Key rules (verified on the detail sheets):
- exterior wall W1: 395 solid bonded face brick (the module axis lies 370
  behind the outer face) + a 55 insulated plasterboard lining ("Placo") on the
  warm side = 450; finished face = axis + 0.080;
- at each floor the RC slab end runs into the wall behind a 120 face-brick
  leaf with 10 mortar and 10 polystyrene (SE 54 det. 1, SE 60);
- intermediate floor 300 (100 build-up + 200 laterocemento), raw soffit
  z_f - 0.30 = 2.71 above the floor below, plaster 10 -> finished ceiling 2.70;
- ground floor 320, soffit -0.32; floors over open air carry insulation;
- pitched roof 350 perpendicular (34 %), raw soffit T + 2.53 + 0.34 s, lined;
- copper vault R 6.00 finished soffit, 308 radial.
"""
from __future__ import annotations

# ------------------------------------------------------------------ walls
LINING = [('LiningAdhesive', 'M_Screed', 0.015), ('LiningInsulation', 'M_Insulation', 0.030),
          ('LiningBoard', 'M_PlasterInt', 0.010)]                  # 55, on the warm face
LINING_T = sum(t for _, _, t in LINING)
WALL_EXT_MASONRY = 0.395                                           # W1 face brick (37 + 2,5)
AXIS_FROM_OUT = 0.370                                              # module axis behind the outer face
SLAB_ZONE = dict(leaf=0.120, mortar=0.010, polystyrene=0.010)      # at each slab, outside -> in
NICHE = dict(depth=0.135, z1=0.81, extra_w=0.07)                   # radiator niche, finestre tipo only

WALL_CORE = [('Render', 'M_Plaster', 0.020), ('Brick', 'M_Brick', 0.260)] + LINING          # W2 335
WALL_STAIR = [('Brick', 'M_Brick', 0.260)] + LINING                                         # W3 315
WALL_SPINE = [('SpinePlaster', 'M_PlasterInt', 0.015), ('SpineRC', 'M_Structure', 0.170),
              ('SpinePlaster', 'M_PlasterInt', 0.015)]                                      # W4 200
WALL_SEP = [('Plaster', 'M_PlasterInt', 0.015), ('Leaf', 'M_HollowBrick', 0.080),
            ('Wool', 'M_Insulation', 0.020), ('Leaf', 'M_HollowBrick', 0.080),
            ('Plaster', 'M_PlasterInt', 0.015)]                                             # W5 210
WALL_JOINT_LEAF = [('Plaster', 'M_PlasterInt', 0.015), ('JointLeaf', 'M_Brick', 0.185),
                   ('JointWool', 'M_Insulation', 0.040)]           # W6: one side of the 490 double wall
PARTITION = [('Plaster', 'M_PlasterInt', 0.015), ('Core', 'M_HollowBrick', 0.080),
             ('Plaster', 'M_PlasterInt', 0.015)]                                            # W7 110
PARTITION_WET = [('Plaster', 'M_PlasterInt', 0.015), ('Core', 'M_HollowBrick', 0.120),
                 ('Plaster', 'M_PlasterInt', 0.015)]                                        # W7 150, plumbing
CELLAR_PART = [('CellarBrick', 'M_Brick', 0.120)]                                           # W8 120

# ------------------------------------------------------------------ floors
CEILING = [('CeilingPlaster', 'M_PlasterInt', 0.010)]              # under the raw soffit
FLOOR_INT = [('Parquet', 'M_Parquet', 0.015), ('Screed', 'M_Screed', 0.045),
             ('Fill', 'M_Screed', 0.040), ('Slab', 'M_Structure', 0.200)]                  # F1 300
FLOOR_OPEN = [('Parquet', 'M_Parquet', 0.015), ('Screed', 'M_Screed', 0.045),
              ('Insulation', 'M_Insulation', 0.040), ('Slab', 'M_Structure', 0.200)]       # F2 300
FLOOR_GF = [('Parquet', 'M_Parquet', 0.015), ('Screed', 'M_Screed', 0.045),
            ('Insulation', 'M_Insulation', 0.030), ('Fill', 'M_Screed', 0.030),
            ('Slab', 'M_Structure', 0.200)]                                                 # F3 320, soffit -0.32
FLOOR_CELLAR = [('CellarFloor', 'M_Concrete', 0.120), ('Gravel', 'M_Ground', 0.200)]       # F4, top -0.32
FLOOR_HALL = [('HallFloor', 'M_Screed', 0.030), ('Screed', 'M_Screed', 0.070),
              ('Slab', 'M_Structure', 0.200)]                      # common stair hall: "pavimento in cemento"
TERRACE = [('Tiles', 'M_Stone', 0.015), ('Bed', 'M_Screed', 0.025), ('Protection', 'M_Screed', 0.040),
           ('Membrane', 'M_Membrane', 0.010), ('Insulation', 'M_Insulation', 0.040),
           ('Falls', 'M_Screed', 0.100), ('Slab', 'M_Structure', 0.200)]                   # R3 430, finish z_f + 0.13
GALLERY_DECK = [('Tiles', 'M_Stone', 0.015), ('Bed', 'M_Screed', 0.020), ('Membrane', 'M_Membrane', 0.005),
                ('Falls', 'M_Screed', 0.040), ('Slab', 'M_Structure', 0.200)]              # R4 280, finish 2.99

# ------------------------------------------------------------------ roofs
ROOF_TILE_UNDER = [('Membrane', 'M_Membrane', 0.005), ('Insulation', 'M_Insulation', 0.040),
                   ('Cappa', 'M_Structure', 0.040), ('Slab', 'M_Structure', 0.120)] + LINING
# R1: under the clay tiles (90, the exterior's tile object); 350 perpendicular in all
ROOF_PITCH = 0.34
ROOF_RAW_SOFFIT = 2.53            # T + 2.53 + 0.34 s at the low wall's masonry face (s = 0)
ROOF_VAULT_UNDER = [('Boarding', 'M_Wood', 0.022), ('Battens', 'M_Wood', 0.025),
                    ('Membrane', 'M_Membrane', 0.005), ('Insulation', 'M_Insulation', 0.040),
                    ('Cappa', 'M_Structure', 0.040), ('Slab', 'M_Structure', 0.120)] + LINING
# R2: under the copper sheet; finished soffit R 6.00 springing T + 2.15 at the lining faces
VAULT_R_SOFFIT = 6.00
VAULT_SPRING = 2.15

# ------------------------------------------------------------------ levels
CEILING_CLEAR = 2.70              # finished ceiling above the floor (raw soffit 2.71 - plaster)
RAW_SOFFIT = 2.71
FLOOR_T = 0.30
GF_SOFFIT = -0.32
TERRACE_UP = 0.13                 # terrace finish above the floor inside


def total(stack) -> float:
    return sum(t for _, _, t in stack)
