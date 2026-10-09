# Interiors

The interior stage of the model: rooms, dwelling-separating walls, partitions, internal doors,
stairs, construction layers and real windows and doors for every part of Gino Valle's IACP housing
on the Giudecca. It is a companion of [`ANALYSIS.md`](ANALYSIS.md), which specifies the exterior and
is not repeated here.

**Coordinates.** As in `ANALYSIS.md` §2: E and Y in modules (1 module = 1.65 m), z in metres with
0.00 = finished ground floor of the dwellings, floors at 0.00 / 3.01 / 6.02 / 9.02, `x = (36.0 −
E)·1.65`, `y = (15.5 − Y)·1.65`. Per house the reports use dE / dY in metres from the house axis
(+dE = west, +dY = south); the schiera uses u = metres from the party axis into the dwelling.
Thicknesses in the tables are in mm, levels in m.

**Status marks.** D = written or drawn on a sheet, M = measured on the scan, A = assumed (Italian
public-housing practice of 1984, Legge 373/1976). Sheet numbers (SE 50, n3 …) follow `plans/INDEX.md`.

**Sources.** The verified research reports of the interior stage (layers, joinery, towers, carpet
north, carpet middle and south, schiera), the builders' reports per part, the independent review of
the towers, and the code in `model/giudecca/`. Where sources disagree the text says which one the
model follows.

## 1. Scope and how to build

### 1.1 What the interior stage adds

* Rooms, dwelling-separating walls, partitions, internal doors (open 90° so the rooms read), stairs,
  landings and balustrades, per the 1:50 plans and the 1:10 / 1:1 details.
* Joinery for every window and door: frames, sashes, glass, handles, window boards, reveals, sills,
  thresholds, lintels, radiator niches.
* The construction layers of every element: linings, floors, roofs, vaults, terraces, gallery deck.
* Oak parquet as the floor finish of every dwelling room (client's wish).
* Not modelled: furniture, kitchen units, sanitary fittings, flue boxes and vent ducts.

### 1.2 Build commands

```
python model/build.py --interiors                          # whole complex with interiors, export to model/output
python model/build.py --interiors --only site towers       # one part ("site" supplies the ground)
python model/build.py --interiors --no-export --out DIR    # build and validate only
python model/build.py --interiors --web DIR                # also the per-part Draco glTF (.json + .jpg) for the browser viewer
```

`--only` takes any of `site towers carpet schiera`; `--render`, `--views`, `--samples` and `--res`
work as before. `--web DIR` writes one Draco-compressed glTF per part as a `.json` with an embedded
buffer plus shared JPEG textures, for hosts that serve `.json` / `.jpg` but not `.glb`
(`webexport.py`); the full-quality `.glb`, `.fbx`, `.obj` and `.blend` come from the normal export.

**Without `--interiors` the build is unchanged**: exterior-only, solid bodies, recessed glass panes,
310 objects and 119,436 triangles. Every exterior-module change is guarded by `if geo.THROUGH is not
None`, and the exterior-only output was hashed against the pre-interior commit per part (towers: 102
objects identical; carpet: 866 openings, identical hash; schiera: 37 objects, 34,286 triangles).

### 1.3 What `--interiors` changes

1. `geo.THROUGH = 0.70` (`build.THROUGH`). Every window, door and oculus that the exterior modules
   cut through `geo.opening`, `geo.round_window`, `Openings.rect | arch | round` or the carpet's
   `Cuts.poly` is **recorded in `geo.OPENINGS`** (one dict per opening: `axis`, `coord`, `out`,
   `outline` as (u, z) points, `kind` rect / arch / round / poly, `target` = the body object, `w`,
   `h`, `recess`, `through`, `keep_recess`) and cut **0.70 m deep from the outer face**, through any
   wall, **without the exterior's plain glass pane**. `keep_recess=True` keeps a blind recess with
   its pane (glazed arches onto the middle-row cellar band, campo-strip cellar bays).
2. Right after each exterior part, `giudecca/interior_<part>.py: build(ctx)` runs. For the carpet,
   `interior_carpet.py` dispatches to `interior_carpet_north.py` (north row) and
   `interior_carpet_ms.py` (middle and south rows, campo strip, middle-row L0).
3. At the end `joinery.build(ctx)` gives joinery to every record not yet marked `done` by a part
   module.
4. The boolean cutters are renamed `CUT_*`, kept hidden and never exported;
   `validate.prepare_for_export` and `validate.check_scene` run as before.

Guarded edits in the exterior modules (all skipped in the exterior-only build):

| Module | Edit under `geo.THROUGH` |
|---|---|
| `towers.py` | Street-door pane and leaf not built (the joinery builds the door, type PTE at `ENTRANCE_FRAME`); the openings register their body. |
| `carpet.py` | Openings cut through without a pane. Passage core door replaced by two portoncini 0.91 × 2.07 per house (n11, n49, SE 65). Middle-row L0 core faces: the north 0.60 window becomes the garden door 0.83 × 2.35 at Y 10.62 → 11.12, the south window does not exist (n11, n64). Middle-row L2 notch side walls solid (no French doors; n10, n79). Campo porch-to-vestibule openings. NorthPavM L0 court arches and the campo-strip outer cellar bays kept as blind recesses. The north module's `prepare()` removes exterior stand-ins: trifora mullion frames, core slabs, the gallery-deck box. |
| `schiera.py` | Kitchen window in every block side wall (`KITCHEN_WIN`: centre Y 29.46, 0.95 × 1.43 → 2.35; n5 C, n27, n37), missing from the exterior-only model. Stand-in door leaves skipped. Copper vault as a 1 mm hollow sheet; flue pipes start inside the vault's timber zone (5.67). `CORE_IN` 1.805 = inner masonry face of the core walls. |

### 1.4 The engine

`interior.py` holds the primitives, `buildups.py` the layer stacks (§2), `joinery.py` the opening
types (§3). The part modules hold the data (rooms, walls, doors, stairs per dwelling) and call the
engine.

* `Kit(ctx, part, tag, col)`: one bmesh per element and material, flushed into one object
  `SM_<Part>_<Element>_<Tag>`; touching solids stay separate closed shells; an element in a second
  material gets its own object named after the material (steel stair windows, grey cellar doors).
* `hollow(ctx, body, volumes)`: one exact boolean difference in self-intersection mode; normals are
  not recalculated, so a room enclosed by masonry stays a valid inward-facing cavity.
* `cut_openings`, `openings_of`, `floor_stack` (parquet gets 45° UVs), `lining`, `partition` (with
  door openings), `door` (frame, architraves, leaf open 90°), `sloped_stack`, `vault_stack`,
  `face_box`, `flight` (RC waist, treads, risers), `landing`, `handrail`.
* `joinery.classify(rec)` picks the type (a part module may set `rec['type']`; `None` = no joinery),
  `add_pockets` adds the frame rebates, lintels, sill blocks and niches to the hollowing cutter,
  `lining_boxes` / `lining_cutter` open the linings where the joinery passes through them,
  `build_openings(kit, recs)` builds the joinery.

Per masonry body: one cutter of every room and storey zone inside the masonry (lowest slab soffit
to the raw soffit, following the roof slope or the vault on the top floor), the door passages and
the joinery pockets; `hollow`; the layers, walls, doors and stairs with a `Kit`; the joinery;
`flush`. A through-cut window must open into a hollowed room, or it leaves a dark 0.70 m pocket (§6).

## 2. Construction build-ups

Verified on the detail sheets (SE 50, 51, 53, 54, 56, 58, 59, 60, 63, 64, 65, n3) in a second,
adversarial pass; the stacks are transcribed in `model/giudecca/buildups.py`. Layers are listed
outside → inside or top → bottom, with the element and material names of the stacks.

### 2.1 Key rules

1. The "37 + 2,5" exterior wall is **solid bonded face brick 395** (header ≈ 260 + joint ≈ 15 +
   stretcher ≈ 120, no cavity); the module axis lies **370 from the outer face**.
2. An **insulated plasterboard lining ("Placo") of 55** (15 adhesive + 30 insulation + 10 board)
   covers every cold side of a heated room, including the vault and the sloped roof soffits.
3. Finished exterior wall **450**, finished face at axis + 80; a 4.04 pavilion is 3.25 clear between
   masonry and **3.14 between linings**.
4. Intermediate floors **300** (100 build-up + 200 slab), raw soffit "+2,71", finished ceiling
   z_f + 2.70. Ground floor **320**, suspended slab with its soffit at −0.32 over a crawl space.
5. At every slab the concrete hides behind a 120 face-brick leaf with 10 mortar and 10 polystyrene.
6. Core walls toward the courts: render 20 + brick 260 + lining 55 = **335**, outer faces at house
   axis ± 2.085 (core 4.17; the exterior carpet model has `CORE_W` 4.10, the schiera 4.17).
7. Top-floor ceilings follow the roof slope and are lined: **T + 2.472 + 0.34 s** (s from the low
   wall's masonry face), T + 2.49 at the low-wall lining, T + 3.56 at the high-wall lining.
8. The radiator niche (wall reduced to 260 under the sill) exists **only under the 1.04 × 1.41
   "finestre tipo"**; trifore and 0.91 × 0.92 windows have the full 395 below the sill.
9. Party walls and house-axis walls in the pavilions measure ≈ 0.21 at 1:50, not 0.25.

### 2.2 Materials (`materials.PALETTE`)

| Code | Material | Use |
|---|---|---|
| M_Brick | face brick, hand-made ≈ 260 × 120 × 55 | all fair-faced masonry; also the cotto-red paving of the tower porch, loggia and terraces |
| M_HollowBrick | hollow clay ("laterizio forato") | partitions, double-leaf separating walls |
| M_Structure | reinforced concrete / laterocemento | slabs, slab ends, ring beams, spine walls, stair waists |
| M_Concrete | exposed concrete | bands, lintels, sills, thresholds, copings, beams, steps |
| M_Plaster | external render ("intonaco") 20 | court faces of the cores, cellar fronts, passage walls |
| M_PlasterInt | interior plaster / painted board face | ceilings, plastered masonry, lining faces, reveals |
| M_Insulation | EPS / mineral wool | linings, roofs, floors over open air, joints |
| M_Screed | sand-cement screed, fill, adhesive beds | floors, lining adhesive, cement hall floors |
| M_Parquet | oak parquet, herringbone, 15 incl. adhesive | all dwelling floors (textured, 45° UVs) |
| M_RoofTile / M_Copper | clay "coppi" / copper sheet | the exterior's tile and vault objects, kept |
| M_Wood | timber boarding and battens | vault substrate |
| M_Stone | stone | terrace tiles (carpet), vestibule floor, entrance sills |
| M_Joinery | painted wood, cream ≈ RAL 9001 (233, 225, 211) | window and door frames and leaves |
| M_CellarJoinery | painted grey | cellar doors and windows |
| M_Steel | dark steel | stair windows, oculus rings, balustrades, handles |
| M_DoorLeaf / M_DoorFrame / M_StairTread | wood / pale stone | interior doors and architraves; stair treads (oak M_DoorLeaf in the towers, M_StairTread elsewhere) |

### 2.3 Walls

| Code | Wall | Layers (mm) | Total | Where | Source / status |
|---|---|---|---|---|---|
| **W1** | Exterior face-brick wall | FaceBrick M_Brick 395 · LiningAdhesive M_Screed 15 · LiningInsulation M_Insulation 30 · LiningBoard M_PlasterInt 10 | 450 | all façades, court faces, block ends, slot and campo faces, walls to portico, passage, gallery and joint corridor above L0; towers; schiera | SE 50, SE 51 det. 5, SE 54, SE 63 "8 \| 37", SE 60 "45 = 37 \| 8"; split M |
| W1 slab zone | at each floor, z_f − 0.30 → z_f | BrickLeaf M_Brick 120 · Mortar M_Screed 10 · Polystyrene M_Insulation 10 · SlabEnd M_Structure 255 | 395 | behind the exterior leaf; the lining continues above z_f − 0.10 | SE 54 det. 1 (117 / 16 / 13 / 246), SE 60 "12 \| 2 \| 25" |
| W1 lintel | z_f + 2.35 → 2.48 | LintelOuter M_Concrete 260 deep × 130 high (the façade band) · LintelInner M_Concrete 135 × 60 (2.42 → 2.48); 70 rebate below the inner leg for the sub-frame | — | over every stop-jamb opening; the band continues between openings | SE 54 det. 3 "26 / 13 / 13,5 / 6", SE 53 |
| W1 niche | z_f → z_f + 0.81 | FaceBrick M_Brick 260 + lining; recess 135 from the finished face, 1.18 wide | — | finestre tipo only | SE 53 "finestre tipo"; bottom A |
| **W2** | Core wall toward the light courts | Render M_Plaster 20 · Brick M_Brick 260 · lining 55 | 335 | carpet and schiera cores (E/W faces); render face at axis ± 2.085, lining face ± 1.75 | SE 59 "asse \| 10 \| 5,5 \| 26 \| 2", SE 60, n60 |
| **W3** | Common stair hall ↔ dwelling | (render M_Plaster 20 on the hall side where plastered) · Brick M_Brick 260 · lining 55 | 315 fair brick / 335 rendered | towers; walls carrying dwelling entrance doors | SE 58, SE 65 det. 1 "5,5", threshold "31,5 / 33,5" |
| **W4** | Core spine between the twin flights | SpinePlaster M_PlasterInt 15 · SpineRC M_Structure 170 · SpinePlaster 15 | 200 | carpet and schiera cores, centred on the axis | SE 60 / n60 "155 \| 20 \| 155"; material A |
| **W5** | Dwelling-separating wall | Plaster M_PlasterInt 15 · Leaf M_HollowBrick 80 · Wool M_Insulation 20 · Leaf M_HollowBrick 80 · Plaster 15 | 210 | house-axis walls in the pavilions; party walls E 11.5, 23.5, 60.5 (+ 35.5 / 48.5 in the north and south rows); schiera block axes; tower flats | total M (SE 12 n79, SE 13 n10); composition A |
| **W6** | Expansion-joint double wall | per side: Plaster 15 · JointLeaf M_Brick 185 · JointWool M_Insulation 40; then Air 50 (not built) | 490 | carpet E 17.5, 29.5, 54.5; schiera E 23.5 | joint "53 \| 9 \| 53" SE 50 D; leaves A |
| **W7** | Partitions in dwellings | Plaster 15 · Core M_HollowBrick 80 · Plaster 15 (wet walls: core 120 → 150) | 110 / 150 | all dwellings | A (standard tramezza); thin double lines at 1:50 |
| **W8** | Cellar partitions | CellarBrick M_Brick 120, fair-faced | 120 | carpet cantine | SE 56 "divisori cantine 12 cm" D |
| **W9** | Cellar fronts and L0 walls to the joint corridor and passage | render 20 on 260 brick infill between 395 face-brick piers; corridor walls on Y 8 / Y 15: face brick 370 + rendered leaf ≈ 130 on a 700 foundation | — | middle-row cantine front, L0 corridor and passage | SE 56 "intonaco", SE 63; infill A. The cantine front's render and plinth are not modelled. |

Wall heads under the pitched roofs (SE 54, 1:1; exterior elements): RC coping 200 wide, flush,
low wall T + 2.77 → 2.90, high wall T + 3.97 → 4.10; the roof slab rests on the lintel top (T + 2.48)
and meets the masonry at T + 2.53; copper box gutter in the slab end at the low wall.

### 2.4 Floors

| Code | Floor | Layers top → bottom (mm) | Total | Where | Source / status |
|---|---|---|---|---|---|
| **F1** | Intermediate floor in dwellings | Parquet M_Parquet 15 · Screed M_Screed 45 · Fill M_Screed 40 · Slab M_Structure 200; below the raw soffit CeilingPlaster M_PlasterInt 10 → finished ceiling z_f + 2.70 | 300 | all L1–L3 floors over heated rooms, landings included | 300 and 2.71 D (SE 58, 53, 56); split A |
| **F2** | Floor over open air or an unheated space | Parquet 15 · Screed 45 · Insulation M_Insulation 40 · Slab 200; soffit fair-faced outside, 10 plaster over cellars | 300 | L1 over the north portico, pilotis, cantine, joint corridor and passage; L2 over the gallery and over the campo; schiera L1 over the porticoes; tower loggia / middle bedroom | Legge 373 A; downstand RC beams 360 deep along the portico pier lines D (SE 56) |
| **F3** | Ground floor of dwellings and stair halls | Parquet 15 · Screed 45 · Insulation 30 · Fill 30 · Slab 200 (soffit −0.32, crawl space below, A) | 320 | south-row L0, middle-row cores, towers L0, schiera L0 | SE 63 "12 \| 20", "−0,32 imposta solaio" D; layers A |
| **F4** | Cellar floor on grade | CellarFloor M_Concrete 120 · Gravel M_Ground 200, top −0.32 | 320 | carpet cantine and cellars | SE 63 Y 16 "12 \| 20", "−0,32 pav. cantine" D |
| FLOOR_HALL | Tower common stair hall ("pavimento in cemento") | HallFloor M_Screed 30 · Screed 70 · Slab 200 | 300 | tower lobby and landings | SE 58 D |
| (F5) | Exterior paving at −0.45 | 200 bed to −0.65 | — | context, exterior | SE 63 |

Interior heights that follow: floors under another floor, terrace or deck **z_f + 2.70**; top floors
of pavilions sloped, **T + 2.472 + 0.34 s**; cores under the vault **T + 2.15** at the lining faces
(± 1.75) → **T + 2.411** at the crown (R 6.00); window heads: inner lintel leg at z_f + 2.42.

### 2.5 Roofs

| Code | Roof | Layers top → bottom (mm, perpendicular) | Total | Where | Source / status |
|---|---|---|---|---|---|
| **R1** | Pitched clay-tile roof, 34 % | Coppi M_RoofTile 90 (the exterior's tile object) · then `ROOF_TILE_UNDER`: Membrane M_Membrane 5 · Insulation M_Insulation 40 · Cappa M_Structure 40 · Slab M_Structure 120 · lining 55 | 350 | all mono-pitch pavilion roofs of the carpet, towers and schiera bar; tower middle lean-to; schiera lean-to | SE 54 det. 1–3 ("isolazione 4 cm", "cappa 4 cm", "solaio 12 cm", "imposta solaio a +2,53"); lining D, split M; no ventilation layer |
| R1 geometry | raw soffit T + 2.530 + 0.34 s; finished ceiling T + 2.472 + 0.34 s; top of tiles T + 2.842 + 0.34 s | | | | SE 54 |
| **R2** | Copper barrel vault, R 6.00 spanning E–W | Copper M_Copper 1 (the exterior's copper object) · then `ROOF_VAULT_UNDER`: Boarding M_Wood 22 · Battens M_Wood 25 · Membrane 5 · Insulation 40 · Cappa 40 · Slab 120 (curved) · lining 55 | 308 radial | carpet and schiera cores; tower stair hall (A) | SE 59 ("manto lamina in rame", "Eternit" crossed out; "isolazione 4 cm", "solaio 12 cm (curvo)", "5,5"), n60; boarding / battens A |
| R2 levels | gutter edge T + 2.48; finished soffit R 6.00, springing T + 2.15 at the lining faces ± 1.75, crown soffit T + 2.411; the drawn package puts the copper crown at T + 2.72 against 2.70 in the exterior. **Rule:** keep the drawn soffit and layers (260); the assumed boarding / batten zone absorbs the difference (29 at the crown, 53 nominal). | | | | SE 59 |
| **R3** | Roof terraces and joint decks, finish z_f + 0.13 | `TERRACE`: Tiles M_Stone 15 · Bed M_Screed 25 · Protection M_Screed 40 · Membrane 10 · Insulation 40 · Falls M_Screed 100 · Slab 200; ceiling plaster 10 below | 430 over the raw soffit | 9.15: N/M joint deck, north-row notch terraces; 6.15: M/S joint deck, middle-row notch terraces, campo south strip; tower L3 terraces (A), schiera L1 terraces (A) | SE 54 (deck slab T + 2.71 → 3.01) D; layers A; SE 55 / SE 57 not in the set |
| **R4** | L1 gallery deck (ballatoio), finish 2.99 | `GALLERY_DECK`: Tiles M_Stone 15 · Bed 20 · Membrane 5 · Falls 40 · Slab 200; fair-faced soffit over the arcade | 280 | north-row gallery | SE 64 "+2,99" D; split A |

### 2.6 Stairs

| Code | Stair | Geometry | Construction | Source / status |
|---|---|---|---|---|
| S1 | Internal dwelling stairs | carpet: one straight flight per storey, 0.78 wide against the axis wall (dE 0.105 → 0.88), 15 risers (0.2007 / 0.200), 14 goings × 0.235 = 3.29; schiera: 0.80 wide against the party wall, 15 × 0.2007, 14 × 0.235 | RC waist flight (0.16 carpet north, ≈ 0.12 schiera and towers), oak or stone treads, steel balustrades 1.00 on the open side, wall handrail | n18, n31, n67, n78, n27, n45, n5 B; layers.md S1 ("twin flights 1.55 clear") describes the schiera core half (flight 0.80 + 0.05 + void 0.80) and does not apply to the carpet's 0.78 flights |
| S2 | Tower common stair | L0 → L1: 17 risers × 0.177, goings 0.30, precast RC steps "13/35 in luce"; L1 → L2 → L3: "scala prefabbricata, 15 alzate da 20,07, 14 pedate da 23,5" | cement floors, fair-faced brick walls, wall handrail at 0.92 | SE 58 D |
| S3 | External gallery stair | precast steps 35/13 between face-brick side walls 255 | exterior element | SE 64 |

## 3. Joinery catalogue

From SE 53 ("Porte e finestre nella muratura a vista", 1:10), SE 51 (trifore, 1:1), SE 54 det. 3,
SE 65 (entrance and cellar doors), SE 56, n3 (stair window, 1:1), SE 60 / n60 (oculus panels) and
the 2018 photo n24. The 1:50 sheets draw only masonry openings; every frame, sash and glass
dimension comes from the details or is marked assumed. `joinery.py` implements the catalogue.

**The wall at the openings.** Brick 0.395 and the 0.055 lining give a finished face at d = 0.45
from the outer face. **Stop jambs** (mazzetta; E, E1, C, D): brick reveal d 0 → 0.26 at the opening
width W, pocket d 0.26 → 0.395 widened 0.07 per side (W + 0.14), head pocket 0.07 → inner soffit at
z_f + 2.42 (outer soffit 2.35). **Plain jambs** (F, P, T, K, cellar): straight through. Wooden
sub-frame ("controcassa") ≈ 0.05 × 0.025 at d 0.27 → 0.32. **No shutters** (no scuri, persiane or
roller boxes on any sheet; the 7 cm head pocket cannot hold a box; n24 shows none) and **no glazing
bars** on any type.

Engine defaults (`joinery.BASE`): outer frame 0.060 × 0.065, lapping 0.06 behind the jamb (frame =
W + 0.12: written 116, 103, 89.5); sash stiles and top rail 0.055 × 0.056; bottom rail 0.070 (doors
0.150); two side-hung casements; double glazing 0.018 ("termopane"); RC L-lintel; interior window
board; handle on the meeting stile at mid-sash; cream M_Joinery.

| Type | Name on the drawing | Opening W × H (z above z_f) | Jamb / frame position | Leaves and parts | Status |
|---|---|---|---|---|---|
| **E** | Finestre tipo | 1.04 × 1.41 (sill 0.94 → head 2.35) | stop 7; frame 1.16 × 1.47 at d ≈ 0.27 → 0.335 | two inward casements, window board, lintel, **radiator niche** 1.18 wide, 135 deep | opening H; leaves A |
| **E1** | lights of the two-light windows ("91 \| 7/7 \| 91", E2 in the research), tower pairs 0.93 / 0.92 | per light 0.91–0.995 × 1.41, brick pier 0.14 | as E | one inward casement per light | M; leaves A |
| **F** | Finestre schiera e torri | 0.91 × 0.92 (1.43 → 2.35) | plain; full-depth lintel and sill 1.15 × 0.395 × 0.13; frame 1.03 in the lining plane (d 0.395 → 0.46) | one inward casement, no board, no niche | opening H; frame A |
| **C** | Porte-finestre tappeto | 1.04 × 2.25 (threshold +0.10 → 2.35) | stop 7; frame 1.16 × 2.31 | two inward full-height leaves, bottom rail 0.15, RC threshold 0.45 deep | H (two leaves: n69) |
| **D** | Porte-finestre torri e schiera | 0.775 × 2.25 (+0.10 → 2.35); jambs 0.30 \| 0.775 \| 0.575 | stop 7; frame 0.895; lintel 1.015 | one inward leaf, threshold | H; leaf A |
| **T** | Trifore tappeto | one opening 1.87: side lights 0.415 (sill 0.94), centre 1.04 (sill 0.66); arch spring 2.00, crown 2.35, R 1.42; 12 cm concrete jamb blocks flank the centre below 0.94 | plain, full-depth reveal following the arch; one arched frame in the lining plane (d 0.395 → 0.455); precast arched lintel 2.52 | side lights **fixed**, centre **two inward casements** hinged on the posts, rebated meeting stiles; no window board, no niche | H (SE 51) |
| **K** | Serramento scala 60 / 60 | 0.60 × 0.60 (z_f + 1.20 → 1.80) | plain; inner reveals splayed 15° (jambs) / 45° (sill), square head; **metal** frame 0.040 × 0.050 flush with the outer face on a galvanised Z 40/15 sub-frame | one sash 0.035 × 0.040, sealed double unit ≈ 4/6/4 (glass 0.014), M_Steel, no handle | M; opening direction not drawn |
| **P** | Portoncino d'ingresso | 0.91 × 2.07; clear 0.80 × 1.985 | plain; hardwood frame behind the jamb on the dwelling side (d 0.26 → 0.32) | leaf 0.84 × ≈ 2.01 × 0.05, **4 raised panels** in 2 columns (lower pair ≈ 0.16 → 0.90, upper ≈ 0.99 → 1.92), insulated core ("doppio specchietto da 18"), central knob at ≈ 0.94, inside lever; opens inward; lintel 260 × 410 (2.07 → 2.48) | H (SE 65) |
| **PT** | Tower street door (n7) | 1.25 × 2.33 | plain; frame at d 0.30 | door 0.92 × 2.04 with a fixed transom light to 2.33 and fixed side margins | L–M |
| **CD** | Porte cantine | 0.775 × 2.05 (−0.32 → 1.73); clear 0.725 × 1.98 | plain, plastered infill; frame 0.06 at d 0.26 | flush leaf 0.79, grey M_CellarJoinery, precast threshold | H (SE 65, SE 56) |
| **CW** | Finestre cantine | 0.775 × 0.55 (1.18 → 1.73) | plain; frame 0.06 at d 0.26 | one sash 0.79, wired glass 0.006, bottom-hung tilting inward (vasistas), grey | size H; hinge M–L |
| **AS** | Arched glazed screens into unheated spaces (cellar band, passage) | per opening | plain; fixed frame at d 0.12 | fixed glass, no leaf | model convention |
| **O** | Oculus Ø 0.60 (schiera panel, 0.14 thick) | in the precast panel, centre z 4.66 | fixed glass in a steel ring at the inner face | no handle | L (glass not drawn); the carpet's Ø 0.90 oculi (O90) are **open, unglazed** – they close an open L3 terrace – and get no record |

Part-local types (derived from the engine types inside the part modules):

| Part | Type | Base | Difference |
|---|---|---|---|
| Towers | FT, ET, E1T | F, E, E1 | engine handle off; the handles are built by the module on the sash (the engine's old handle height fell below the 1.43 sill) |
| Towers | PTW, PTS | P | entrance doors D1 / D2 in the stair-hall wall and the spine: no lintel, frame flush with the dwelling face (0.25 + lining / 0.30 + 0.03 insulation) |
| Towers | PTE | PT | street door frame at `towers.ENTRANCE_FRAME` |
| Carpet north | PN | P | portoncini in the 0.34 core north wall, no engine lintel (the module builds EntranceLintel) |
| Carpet north | DN | D | plain-jamb terrace doors 0.775 × 2.05 in the L3 cross wall, frame at d 0.115, no lintel / niche |
| Carpet north | N_E, N_E1P | E, E1 | finestre tipo and two-light pairs with the module's own sill block, board and one lintel per pair (`window_e`, `two_light_joinery`); the trifore are built by `trifora_joinery` |
| Carpet m + s | PM | P | portoncini off the passage / vestibule, no engine lintel |
| Carpet m + s | DM | D | glazed hall → notch-terrace door 0.75 × 2.10 (A), sill 6.15, frame at d 0.10 |
| Carpet m + s | EM, E1M | E, E1 | engine joinery without board and lintel; `window_extras` adds the sill block, a board 2 mm proud and one lintel per group of lights |
| Schiera | PS | P | entrance door frame at d 0.395 → 0.46 in the lining plane (SE 53 A), on the concrete threshold (W + 0.12) × 0.46 × 0.11 (outside −0.11) |
| Schiera | FS | F | handle built by the module at mid-sash |
| Schiera | OS | O | oculus ring at d 0.16 (panel 0.14 + lining) |

Sills, thresholds and lintels (SE 53, SE 51 det. 5, SE 54 det. 3): precast window sill (W + 0.24) ×
0.395 × 0.13 at the back / 0.11 at the face, top 0.94, flush with the façade; F sill 1.15 × 0.395 ×
0.13 at 1.43; French-door threshold (W + 0.14) × 0.45 × ≈ 0.11, top +0.10; entrance threshold P
0.91 × 0.335 (0.315 on face brick) × 0.06, top +0.03; L-lintel W + 0.24 long; lintel P schiera inner
0.26 × 0.41 (2.07 → 2.48), towers 0.27 (2.07 → 2.34); trifora arch 2.52 × 0.395, 2.00 → 2.53.
Interior window boards 0.03 on E / C / D (A); none on T (n24).

Interior doors (no detail sheet; A): flush leaf 0.044, height 2.10, bathroom 0.70, other rooms 0.80
(0.73–0.75 where measured so), wooden frame plus 0.07 × 0.01 architraves on both faces, lever at
≈ 1.00, hinged and swung as drawn, modelled open 90°; entrance and street doors closed. Colours:
windows and French doors cream / ivory ≈ RAL 9001 (n24), handles dark, cellar joinery grey, K
frames and oculus rings dark steel, sills, thresholds and lintels exposed concrete.

## 4. The parts

### 4.1 Towers (torri)

Sources: n55 (published plans), 1:50 plans n8 / n56 (read flopped) / n28 (rev. Apr 1985) / n46,
sections n62 (K-K along Y, A-A along E), stair detail n74 (SE 58, 1:10), SE 53 / SE 65. **All ten
towers are identical inside**; the west column is the E-mirror (E' = 72 − E). Per tower three
dwellings: **Tipo A** (one bedroom) at L0 and at L1, and the **Tipo C duplex** (entrance and private
stair at L1, night floor L2, day floor L3).

| Floor | Room (label) | E (finished faces) | dY (m, + south) | Ceiling |
|---|---|---|---|---|
| L0, L1 | living-dining (PRANZO SOGGIORNO) | 0.04 → 2.88 | −5.75 → −2.50 | flat z_f + 2.70 |
| L0, L1 | kitchen (CUCINA) | 2.95 → 3.981 | −5.75 → −2.50 | flat |
| L0, L1 | corridor / entrance (open to the living room at D6, door D7 to the bedroom) | 2.04 → 2.577 | −2.105 → +2.105 | flat |
| L0, L1 | bedroom (CAMERA) / bathroom (BAGNO) | 0.04 → 2.88 / 2.95 → 3.981 | +2.50 → +5.75 | flat |
| L0 | common lobby (cement floor) | 2.759 → 3.965 | −2.105 → −0.855 | 2.71 |
| L0 / L1 | porch (PORTICO) / loggia (TERRAZZA), exterior | 1.02 → 1.78 | −2.105 → +2.105 | soffit 2.71 / 5.72 |
| L1 | duplex vestibule at the foot of the private flight | 3.462 → 3.947 | −2.225 → −0.905 | 5.72 |
| L2 | bedrooms N and S / middle bedroom under the lean-to | 0.04 → 2.88 / 1.02 → 2.88 | ∓(2.50 → 5.75) / −2.22 → +2.22 | flat 8.72 / sloping ≈ 8.55 → 9.60 |
| L2 | bathroom / hall with the stairwell | 2.95 → 3.981 | −5.75 → −3.56 / −3.46 → +5.75 | flat 8.72; downstand at dY −2.53 → −2.11 |
| L3 | living-dining open to the stair hall / kitchen / shower room (DOCCIA) | 1.02 → 3.981 / 1.02 → 2.88 / 2.97 → 3.981 | −5.75 → −2.50 / +2.50 → +5.75 / +3.60 → +5.75 | sloping 34 % |
| L3 | stair hall under the copper roof; two terraces (exterior) | 2.95 → 3.981; −0.02 → 0.78 | −2.50 → +3.50; ∓(2.47 → 5.90) | curved; — |

**Doors** D1–D16 as in the research: entrance doors D1 (stair-hall wall) and D2 (duplex, spine)
0.91 × 2.07 at dY −1.90 → −0.99 with stone sills; street door D3 1.25 × 2.33 (n7); French doors D4
0.775 × 2.25 (D) from porch / loggia into the rooms, D5 1.04 × 2.25 (C) corridor ↔ porch / loggia,
D14 1.04 (C) to the L3 terraces; interior doors 0.70–0.80 × 2.10 at the drawn positions and hinges.

**Stairs.** Common stair SE 58: lobby 1.25 deep; flight 1 of 8 risers rising south in the lower zone
(E 3.444 → 3.965), half-landing of 0.86 in three strips at 1.416 / 1.593 / 1.770, flight 2 of risers
11–17 rising north in the upper zone (E 2.759 → 3.262) to the L1 landing 1.55 × 0.83; **17 × 0.177
= 3.01, goings 0.30**, precast RC steps 13/35, cement floors, wall handrails at 0.92, fair-faced
brick walls, plastered spine and inner wall. Private duplex flights L1 → L2 and L2 → L3 stacked in
the lower zone (0.80 wide), **15 × 0.2007, 14 × 0.235 = 3.29**, first riser dY −0.905, top +2.385,
precast waist 0.12, 3 cm oak treads, sloped balustrade on E 3.45, level guards 1.00 along E 3.45 at
L2 and L3 and across the north end at L3 only (at L2 the next flight starts there).

**What is modelled.** One hollowed body per tower; body faces inside the dwellings painted
M_PlasterInt, the common hall left face brick (SE 58). Linings on all warm faces (W1; stair-hall
outer wall 25 brick + lining; spine 30 + 3 insulation on the duplex side; L2 pavilion walls 25 brick
plastered both sides); partitions W7 0.11 (L0 / L1) and 0.15 (L2 / L3); floors F3 / F1 / F2 and the
hall's cement floor; ceiling plaster; R1 under the pavilion tiles and the lean-to; R2 under the
stair-hall copper; terraces with a 100 mm build-up; porch and loggia paving in cotto red (M_Brick);
plaster on the stairwell slab edges and under the L2 → L3 flight. Joinery for all 36 openings per
tower (7 added by the module: D4 × 4, D1 × 2, D2).

**Naming.** `SM_Tower_<Element>_E<k>` for the east tower k = 0…4, mirrored into
`SM_Tower_<Element>_W<k>` (x → −x, winding flipped, normals kept so the rooms stay cavities); 64
objects and ≈ 24.7k triangles per tower (body 4.0k, linings 5.3k, joinery ≈ 6k). Elements: Body,
WallLining*, WallPlaster, CeilingPlaster, Floor*, HallSteps, EntranceSills, NicheLining,
StairwellPlaster, Partition*, Door*, Stair*, Balustrade*, Roof*, Vault*, Terrace*, Window*, StairWindow*.

**Deviations from the drawings (builder's report, kept after review):**

* Common entrance D3 1.25 wide (n7, exterior), not the 1.55 the n74 plan leaves open at floor level.
  Second column of stair windows per ANALYSIS (dY 1.14 → 1.75), not n74's 1.235 → 1.835. D11 per
  SE 38 rev. Apr 85 (n55 / n62 put it at dY −2.25 → −1.48).
* Stair-hall outer wall 25 brick + 5.5 lining (n74 "25"), not the 26 of SE 65 / W3. The inner wall
  of the middle part follows the exterior's face at E 4.12 (n74 writes 4.147, measured 4.12–4.16).
  The L3 stair-hall block wall follows the exterior's E 2.86 face (drawn ≈ 2.78 → 2.95) as 0.12
  brick + 0.03 lining.
* L2 / L3 partition at E 2.86 → 2.951 and 0.15 thick (wet partition) instead of E 2.88 → 2.95 and ≈
  0.11 (n28): it carries the stair-hall wall above.
* The L2 walls between pavilions and middle part have their masonry at dY ± 2.25 → 2.50 (the
  exterior wall faces) instead of 2.225 → 2.475 (n28); room faces 2.515 / 2.235 against 2.50 / 2.22.
* L3 terraces finish at 9.02 (set by the exterior: D14 sill 9.04) with a 100 mm build-up; R3 (430,
  finish 9.15) would put the terrace above the door sill.
* The south pavilion wall under the L1 → L2 flight runs up to the flight soffit (n62, n56), not the
  9 cm skin of n74 1P. The L1 spine runs through to dY +2.105 (n74 unclear). L2 → L3 has 15 risers
  (count assumed). Back wall 0.45 (n62 "45", partly legible).
* L3 stair-hall ceiling: the vault hangs from the exterior's copper (its 60 mm shell stands for
  copper + boarding + battens, R2 rule); the review probed 11.10 (E 3.0) → 11.35 (E 3.9) against
  ≈ 11.30 → 11.58 in the research (n62 A-A ≈ 11.20 → 11.44); the hall windows (head 11.07) end
  close under it.
* The L0 slab sits on solid brick (the foundation void of n62 is not modelled). The exterior copper
  box gutters at the low ends of the pavilion roofs sit inside the R1 layers, hidden between tiles
  and lining. D5's leaf configuration is not drawn (two C leaves modelled).

**Review findings and their state.** The independent review found: (1) the paint pass turning
≈ 11.5 m² of exterior face brick white on towers E0 / W0 (fixed: `paint()` tests each polygon's
triangles and paints only when at least half its area faces into a room); (2) bare brick in all 40
radiator niches (fixed: `niche_finishes`); (3) cut lining layers visible at the K stair windows and
some lining ends (K reveals now plastered; lining ends not re-verified); (4) the L3 hall ceiling
lower than drawn (boarding / batten layers dropped; the rest is listed above); (5) engine joinery
issues (fixed in the engine, §6); (6) pale terrace paving and stair treads, bare slab edges (fixed).

### 4.2 Carpet, north row (Tipo C and the campo houses Tipo B2)

Sources: n69 (types), 1:50 plans n19 / n67 / n31 (L1), n79 / n10 / n78 (L2), n51 / n65 / n58 (L3),
sections n18, n64, n17, n77, SE 65. 1:50 plans exist only for houses 8.5, 20.5, 32.5 and 38.5; the
others are repeated and mirrored. Each H-house holds **two mirror-image triplex maisonettes
L1–L3**, entered from the L1 gallery (deck 2.99, finish 3.01 inside) through the core's north wall;
no internal stair from L0. The ordinary house is Tipo C; the campo houses E 38.5 and 45.5 are Tipo
B2 (L1 core only, L2 south pavilion over the campo).

| Floor | Room (west dwelling, dE + = west) | dE (m) | Y (modules) | Size |
|---|---|---|---|---|
| L0 | cantine in the band Y 4.95 → 7.22 (E 9.75–19.6, 21.6–31.45, 52.55–62.25 only), F4 at −0.32, doors 0.775 × 2.05 onto the joint corridor | | | cells ≈ 1.3–2.9 × 3.16 |
| L1 | entrance landing / flight band / corridor | 0.10 → 1.75 / 0.10 → 0.88 / 0.88 → 1.75 | 2.224 → 2.779 / 2.779 → 4.776 | 1.65 × 0.915 ("91,5") |
| L1 | hall (disimpegno), open to the core | 0.10 → 1.85 | 4.776 → 5.86 | ≈ 1.75 × 1.79 |
| L1 | bagno 2 / camera 1 | 0.10 → 1.76 / 1.93 → 4.85 | 5.92 → 6.906 / 5.0485 → 6.906 | 1.66 × 1.68 / **2.92 × 3.12** |
| L2 | camera 2 (north pavilion, F2 over the gallery) | 0.10 → 4.85 | 0.0485 → 1.9515 | 4.75 × 3.14 |
| L2 | landing / hall / bagno 1 (tub) / camera 3 (runs on across the joint) | 0.10 → 1.75 / 0.10 → 1.85 / 0.10 → 1.76 / 1.93 → 4.85 | 2.012 → 2.779 / 4.776 → 5.94 / 6.01 → 7.72 / 5.0485 → 7.776 | 1.65 × 1.27 / 1.75 × 1.92 / 1.66 × 2.82 / 2.92 × ≈ 4.5 |
| L3 | soggiorno-pranzo (trifora, open to the core strip) / notch landing under the vault / cucina (French door to the joint terrace) | 0.10 → 4.85 / 0.10 → 1.85 / 1.93 → 4.85 | 0.0485 → 1.9515 / 4.776 → 5.86 / 5.0485 → 6.9515 | 4.75 × 3.14 / 1.75 × 1.79 / 2.92 × 3.14 |
| L3 | notch terrace and joint terrace at 9.15 (R3), low axis divider | | 6.04 → ≈ 7.79 / 7.224 → ≈ 7.79 | |

Doors: entrance 0.91 × 2.07 at dE 0.27 → 1.21 (PN); camera doors 0.70 × 2.10 at Y 5.36 / 5.40, bath
doors 0.70 at dE 0.92 → 1.62, camera-2 door at dE 0.88 → 1.65; terrace doors 0.775 × 2.05 (DN) in
the 0.30 cross wall at dE 0.48 → 1.31; kitchen French door C at dE 3.30.

**Stairs.** Two superimposed straight flights per dwelling against the axis wall, dE 0.105 → 0.88
(0.78 clear), rising south from Y 2.779 to 4.776, **15 risers (0.2007 L1 → L2, 0.200 L2 → L3), 14
treads × 0.235 = 3.29** ("14x23,5=329"), RC waist 0.16 with oak treads, raked balustrade and wall
handrail, 1.00 balustrades along dE 0.88 at L2 / L3 and round the L3 well.

**What is modelled.** Hollowed bodies NorthPavN (L2 / L3; L3 open to the core strip under a beam at
T + 2.14), SouthPavN with the campo parts (L1–L3), CoresN, JointNM above z 5.72, CantineN, VaultsN
(copper cut to a 2 mm skin). Built: gallery deck R4 at 2.99 with the parapet and the external
stairs' top tread on it; the 0.34 core entrance wall (EntranceBrick + lining + EntranceLintel) with
two portoncini; axis and party walls W5, the RC spine, partitions W7 0.11 / 0.15, the 0.16 camera |
hall + bath wall; floors F1 / F2 / F4 on one slab per storey; R1 as one run over the south pavilion;
R2 under the vault; R3 terraces at 9.15 with copings; the campo closing wall on the exterior's corner
piers, the campo L2 pavilion over the campo (F2, a 1.04 window per bedroom) and the L2 half party
wall; block ends, joint leaves (W6) and the L1 end walls on E 35.5 / 48.5 per side. Joinery: engine
`build_openings` plus the local trifora, two-light and finestre-tipo builders, with plaster returns
on the core-window and terrace-door reveals and the niche jambs.

**Naming.** `SM_Carpet_<Element>_N<seg>` for the exterior's segments E1, E2, E3, W1, W2 (350
objects, 71 elements), e.g. `SM_Carpet_FloorParquet_NE2`, `SM_Carpet_GallerySlab_NW1`.

**Deviations (builder's report):**

* L2 rooms end at NorthPavM's north face Y 7.776; the drawn L2 dividing wall is at Y 7.906 → 8.027
  (n78), ≈ 0.21 m further south. That masonry is the middle-row body, kept solid by both modules.
* Camera | hall + bath wall: one 0.16 W7 wall (15 + 130 + 15) at dE 1.77 → 1.93. Cameras are the
  written 2.92 and baths the verified 1.66; the hall is 1.665 instead of the drawn 1.75 (the drawing
  jogs: 0.08–0.10 beside the hall, ≈ 0.17 beside the bath). The WC vent duct is inside this wall.
* Campo closing wall: inner face at Y 4.726 (drawn 4.776), on the exterior's corner piers, which
  reach 8 cm into the core.
* Camera 1 of house 32.5 W and 51.5 E is ≈ 2.62 wide, not 2.92: the exterior's end wall on E 35.5 /
  48.5 lies inside the party line (n31 draws it at dE 4.88 → 5.26, outside). Faces not moved.
* Core wall: masonry 0.28 with the inner face at dE 1.77 (finished 1.715), from the exterior's
  `CORE_W` 4.10; layers.md W2 gives 335 to ± 2.085 and the report 1.75.
* L2 landing partition at Y 1.985 → 2.052 (landing 1.27; label "1,24" or "1,34", plan 1.37); camera
  and kitchen doors ≈ 5 cm south of the plans so the architraves clear the north-wall lining;
  terrace-door height 2.05 (label "2,0x"); low terrace divider to 9.98 + coping (height assumed);
  no rainwater outlets on the terraces; the cellar range follows `CANTINE_N`.
* The first research pass gave the pavilion walls as 370 brick + 25 plaster = 395 with no insulation
  (clear depth 3.25); the model follows the verified layers (W1 450, clear 3.14).

### 4.3 Carpet, middle row (Tipo B1)

Sources: n11 (SE 8, L0), n19 / n67 / n31 (L1), n79 / n10 / n78 (L2), sections n18, n64, n17, n49,
n76, n48, n30, n68, SE 56, SE 65, SE 63. Eight middle-row houses (none in the campo houses), **two
mirrored duplexes L1 + L2 per house, each entered at L0** from the covered passage.

| Floor | Room (west dwelling) | dE (m) | Y (modules) | Clear size |
|---|---|---|---|---|
| L0 | N/M corridor (public, −0.45) / cantine front 0.28 / six cantina cells per house (F4 at −0.32): 4 outer cells with doors CD on the corridor, 2 middle cells private with a window CW on the corridor and a door from the core | whole house | 7.24 → 7.92 / 7.98 → 8.15 (model) / → 9.985 | cells 1.50–1.53 |
| L0 | private entrance hall / corridor under flight A (F3 at 0.00) | 0.105 → 1.755 / 0.87 → 1.755 | 12.145 → 12.78 / 10.08 → 12.145 | |
| L0 | entrance door in the core south wall (PM) / landing in the passage / 3 steps to −0.45 / garden door in the core side wall (DM-like, 0.83 × 2.35) / covered passage (−0.45) | 0.305 → 1.215 | 12.78 → 13.00 / 13.00 → 13.40 / 13.40 → 13.76 / 10.62 → 11.12 / 13.76 → 15.00 | |
| L1 | bath / north bedroom (across the N/M joint to the W5 at Y 6.906 → 7.033) | 0.105 → 1.84 / 1.98 → 4.845 | 7.05 → 8.79 / 7.05 → 9.95 | 1.74 × 2.87 / 2.87 × 4.79 |
| L1 | hall (top of flight A) / core corridor / south landing / south bedroom | 0.105 → 1.84 / 0.87 → 1.755 / 0.105 → 1.755 / 0.105 → 4.845 | 8.85 → 10.145 / 10.145 → 12.145 / 12.145 → 13.00 / 13.06 → 14.94 | / / 1.65 × 1.40 / 4.74 × 3.10 |
| L2 | kitchen (court window, no terrace door) / notch terrace (R3 6.15) / hall under the vault with the glazed door DM to the terrace / corridor / landing open to the living room / living-dining with 4 French doors to the M/S deck | 1.98 → 4.845 / 0.105 → ≈ 1.50 / 0.105 → 1.84 / 0.87 → 1.755 / 0.105 → 1.755 / 0.105 → 4.845 | 8.03 → 9.95 / 8.00 → 8.94 / 9.12 → 10.145 / 10.145 → 12.145 / 12.145 → 13.05 / 13.05 → 14.94 | 2.87 × 3.17 / ≈ 1.40 × 1.55 / 1.74 × 1.69 / / / 4.74 × 3.12 |

Doors: bath 0.70 × 2.10 (dE 0.91 → 1.70), bedrooms 0.80 × 2.10 (north bedroom in the bay wall at Y ≈
9.42 → 9.90, south bedroom in the landing partition), kitchen 0.80 in the bay wall at Y ≈ 9.40 →
9.87; middle-cell door 0.70 × 2.10 in the thin wall at Y 9.985 → 10.08 with two concrete steps.

**Stairs.** Flight A (L0 → L1) and flight B (L1 → L2) stacked in dE 0.105 → 0.87, rising **north**
from Y 12.145 to 10.145, **15 × 0.2007, 14 goings × 0.2357**, RC waist, raked steel balustrade on
the open edge, handrail on the spine, horizontal balustrades along the wells.

### 4.4 Carpet, south row (Tipo B)

Ten houses including the campo houses 38.5 / 45.5; **two mirrored duplexes L0 + L1 per house** with
a shared porch and vestibule on the axis.

| Floor | Room (west dwelling) | dE (m) | Y (modules) | Clear size |
|---|---|---|---|---|
| L0 | shared porch (−0.45; open north to the passage, or to the campo) with the cellar doors in its side walls / axis pier ± 0.26 / openings 1.22 each with 3 steps / shared vestibule (stone on screed, unheated) | ± 1.50 | 15.00 → 15.82 / 15.82 → 16.07 / 16.18 → 17.00 | |
| L0 | entrance door PM in the door wall (W3 masonry Y 17.0 → 17.158 + lining, stone threshold) / lobby / kitchen (French door C to the court) / flight rising south / corridor / living-dining open to the core, 2 French doors C at dE 1.00 / 2.49 | 0.305 → 1.215 / 0.105 → 1.88 / 1.97 → 4.845 / 0.105 → 0.87 / 0.87 → 1.755 / 0.105 → 4.845 | 17.00 / 17.15 → 18.20 / 16.10 → 17.96 / 18.20 → 20.19 / 18.20 → 20.78 / 21.04 → 22.95 | / 1.78 × 1.73 / 2.87 × 3.06 / / / 4.74 × 3.15 |
| L0 | cellar in the M/S joint (F4), door CD in the porch side wall | 1.97 → 4.845 | 15.26 → 15.90 | ≈ 2.9 × 1.06 |
| L1 | bath (tub north) / north bedroom (across the joint to the W5 at Y 14.936 → 15.064) / hall / corridor / landing / south bedroom (two-light 1.96 at dE 1.74) | 0.105 → 1.84 / 1.98 → 4.845 / 0.105 → 1.84 / 0.87 → 1.755 / 0.105 → 1.755 / 0.105 → 4.845 | 15.06 → 16.80 / 15.06 → 17.96 / 16.86 → 18.20 / 18.20 → 20.19 / 20.19 → 20.97 / 21.04 → 22.95 | 1.74 × 2.87 / 2.87 × 4.79 / / / 1.65 × 1.29 / 4.74 × 3.15 |

Ceilings at L1: flat 5.72 under the joint deck and the NorthPavS high-wall beam, then sloped under
R1; core under the vault. The south flight rises **south** from Y 18.20 to 20.19, 15 × 0.2007, 14 ×
0.235.

**What is modelled (middle and south rows).** All bodies of the two rows hollowed; the cantine with
W8 partitions, F4 floors, plaster ceilings, cellar doors and windows (new records on the corridor
face); the middle-row L0 core on F3 with lined core and passage walls, garden door and portoncini;
the passage landing, three precast steps (PassageSteps) and the fair-faced south downstand beam
z 2.35 → 2.71 (PassageBeam); the fair-faced L1 slab over corridor and passage (FloorSlabExposed); W5
dividing walls to the north row (Y 6.906 → 7.033, built in the north body's void) and to the south
row (Y 14.936 → 15.064); W7 bay walls (wet), bath, landing and lobby partitions; spine W4; axis and
party walls W5; floors F1 / F2 / F3; kitchens under R1; halls under R2 with the DM door; the M/S
joint deck R3 at 6.15 with low dividers and copings on each axis; the campo south strip
(SM_Carpet_CampoSouth) with the L1 rooms to the lined north wall at Y 15.239, the L0 cellars and the
strip deck; the vaults cut to a 2 mm copper skin with the R2 stack per house; R1 under all four
pavilion roofs. Joinery for 680 openings in the 10 kits.

**Naming.** One Kit per row and segment: `SM_Carpet_<Element>_M<seg>` / `_S<seg>` (614 objects),
e.g. `SM_Carpet_StairTreads_SE2`, `SM_Carpet_PassageBeam_ME1`.

**Deviations (builder's report):**

* Ceilings follow the exterior's roof planes (tile top T + 2.68 at the low wall): the R1 ceilings
  are ≈ 0.2 m lower than the drawn T + 2.47 + 0.34 s. The R2 soffit follows the exterior's copper
  crown (radius 5.69): springing T + 2.13 (drawn 2.15), beams over the core openings at T + 2.12.
* South-row L1 landing → bedroom door head 2.05 instead of 2.10, to clear the beam (n30 shows ≈
  5.14, 3 cm above this head).
* South-bedroom doors in both rows centred at dE 1.22 instead of 1.305 (opening 0.795 → 1.645
  against the drawn 0.91 → 1.70) so the architrave clears the core wall's lining.
* Middle-row houses 32.5 W and 51.5 E toward the campo: the exterior's end wall stays at E 35.5 /
  48.5 (0.37 + lining), so those rooms are 0.32 m narrower than drawn (the drawing runs the room to
  E 35.45).
* Campo strip: the L1 north wall stays at Y 15.0 (masonry face 15.239), so the campo houses' bath
  and north bedroom are ≈ 0.24 m shorter than drawn; strip cellars Y 15.18 → 15.90 (drawn ≈ 15.08
  → 15.88).
* Cantine front wall Y 7.98 → 8.15 (0.28, from the exterior's corridor face) against the drawn 7.92
  → 8.09; cells to the masonry face 9.985 (drawn 9.97); render (W9) and plinth not modelled.
* Bay walls W7 wet (0.15) along their whole length; the drawing shows RC (0.18 → 0.22) in the joints.
* L2 hall | kitchen wall: core / N-pav masonry 1.77 → 1.88 plus plaster and lining (0.18) against
  the drawn W7 at 1.84 → 1.98; kitchen notch-side face 1.935 (drawn 1.98). South-row kitchen face
  at dE 1.97 along its whole length; lobby | kitchen partition W7 0.11 centred at 1.915 (drawn 1.88
  → 1.97).
* South-row cellar doors centred at Y 15.58 (15.345 → 15.815), cut through JointMS and NorthPavS
  (drawn ≈ 15.30 → 15.85).
* Flights sit 3 mm off the spine face and the open edge (no coplanar faces with the floors).
* Passage: only the south downstand beam (Y 14.75 → 15.0, 0.36 deep); the north one would lie half
  inside the wall; the party-wall arches do not exist in the exterior's continuous tunnel.
* Not modelled: the bath vent duct ("VENT. WC") in the bay-wall line, the court-garden walls, the
  passage-side render of the cantine front.
* The middle-row L0 hall has parquet (client's wish; the report allows stone).

### 4.5 Schiera (Tipo A1)

Sources: n27 (SE 44, L0), n45 (SE 45, L1), n26 (roof), n5 (SE 49, sections), n40 (SE 60, core
1:10), n41 (SE 59), SE 54, SE 53, n37 (published "Alloggi Tipo A1"). Four identical blocks on the
party axes E 35.5 / 27.5 / 19.5 / 11.5, **eight mirrored two-storey, one-bedroom maisonettes** D1–D8
(D1 = block 35.5 W … D8 = block 11.5 E).

| Level | Room | u (m from the party axis) | Y (modules) | Ceiling |
|---|---|---|---|---|
| L0 | kitchen (CUCINA), entered from the portico through the block side wall; open, with no wall or door, to the dining-living room | 0.10 → 3.22 | 29.05 → 30.95 | 2.70 flat; beam B1 (soffit ≈ 2.40) on the kitchen / living line Y 30.95 → 31.19 |
| L0 | dining-living (PRANZO-SOGGIORNO), running south into the lean-to | 0.10 → 3.22 | 31.19 → 34.95 | 2.70 under the terrace (u 1.65 → 3.22, Y 31.19 → 33.05, B2's legs flush); open to the vault over the void u 0.95 → 1.65 × Y 31.22 → 32.74; B2 middle soffit 3.56 at Y 32.80 → 33.05; lean-to sloping ≈ 3.60 → 2.53 from Y 33.05 |
| L1 | landing at the top of the flight, open to the core through the bar's south wall (lintel 5.01, parapet 3.93 over the void) | 0.10 → 1.75 | 30.41 → 31.20 | roof soffit |
| L1 | bath (BAGNO) | 0.10 → 1.75 (1.65, written) | 29.05 → 30.35 | 5.54 → ≈ 6.25 |
| L1 | bedroom (CAMERA) to the end wall (D1, D8: 4.66), the 0.20 wall over the portico partition on E 31.5 / 15.5 (D2, D3, D6, D7: 4.65) or its own joint leaf at E 23.5 (D4, D5: 4.505) | 1.85 → end | 29.05 → 30.95 | 5.54 → ≈ 6.65 |
| L1 | terrace (R3, 1.22 × 2.61, finish 3.00 as built) | 2.085 → 3.305 | 31.22 → 32.80 | open |

Openings per dwelling: entrance door P 0.91 × 2.07 at Y 30.226 → 30.796 (hinge north, into the
kitchen), kitchen window F at Y 29.168 → 29.744, two French windows D to the garden (exterior
positions Y 31.62 / 32.38, 0.91 wide), lean-to window E (centre 1 module, radiator niche), bath
window F (4.44 → 5.36) and bedroom window E over the arch (3.95 → 5.36) at L1, terrace door D
(centre u 2.77), one oculus Ø 0.60 (u 0.825, z 4.66). Internal doors: bath 0.70 (hinge u ≈ 1.62),
bedroom 0.73 (hinge at the south jamb); none at L0.

**Stair.** One straight flight per dwelling against the party wall (twin flights mirrored about it),
0.80 clear (u 0.10 → 0.90) with a 5 cm balustrade zone to the void, rising south → north, **15 ×
0.2007, 14 × 0.235 = 3.29** ("a. 20 / p. 23,5"), foot riser Y 33.194, top riser Y 31.20, precast
steps on an inclined slab, steel balustrade joining the 0.92 parapet across the void.

**What is modelled.** Per block: the hollowed body with its inside faces painted; R1 under the bar
and lean-to tiles; R2 under the copper with the timber zone; the 0.20 party wall (hollow-clay
leaves with wool, the RC spine W4 in the core) with the precast flue block at its north end
(Y 29.05 → 29.40, full height); F3 ground slab, F1 / F2 at L1; portico render; wall and ceiling
linings (the core lining wraps the end of beam B2's leg); beams B1 and B2; the 0.92 parapet over
the void; 0.10 partitions with their doors; R3 terraces with a flush 3 cm threshold under the
terrace door; flights with balustrades; panel lining and oculus glass; the full-depth RC sill of
the F windows; the entrance threshold; plaster returns and a 1 cm upstand in the radiator niches;
joinery for all 88 openings.

**Naming.** `SM_Schiera_<Element>_E` / `_W` for the two segment bodies (blocks 35.5 + 27.5 east of
the joint, 19.5 + 11.5 west), e.g. `SM_Schiera_PartyWallFlue_E`, `SM_Schiera_VaultTimber_W`; ≈ 145
objects including the site.

**Deviations (builder's report):**

* Core lining face at u 1.75 (masonry 1.805 + 0.055 lining), per layers.md W2 and the n45 chain "80
  \| 5 \| 80"; the verified schiera report reads the SE 59 "10" as extra insulation (face at 1.65),
  but on n41 the "isolazione 4 cm" label belongs to the vault.
* Terrace south edge and lean-to high wall follow the fixed exterior (Y 32.93 + 0.37 + lining,
  finished face Y 33.12; drawn terrace edge 32.80, B2 inner face 33.05). Terrace finish 3.00 as
  built (drawn 3.01); terrace-door sill 3.01 (drawn 3.11).
* French windows keep the exterior's positions and 0.91 width; the verified report gives Y 31.368 →
  31.850 and 32.071 → 32.553, 0.795 masonry.
* Top flight step: the landing nosing is a 15th tread in stair material between Y 31.20 and 31.058;
  the parquet starts at 31.058.
* Entrance door closed; its inner lintel follows the engine (2.04 → 2.17), not SE 53 A (2.07 → 2.48).
* Roof build-ups follow the exterior tile planes (bar 36 %, lean-to 39.5 %), so the ceilings sit up
  to 6 cm (bar) and 11 cm (lean-to) off the drawn 34 % line T + 2.47 + 0.34 s.
* Flue block 0.20 thick, flush with the party wall (plans ≈ 0.22). Exterior wall 450 (37 + 8; n5,
  SE 60, n45) kept although SE 53 / SE 54 show 39.5 at openings and eaves.

## 5. Finishes

* **Oak parquet everywhere in the dwellings** – living rooms, bedrooms, halls, corridors, landings,
  kitchens, bathrooms and the middle-row L0 entrance halls – at the client's explicit wish. Material
  `M_Parquet`, 15 mm including adhesive on the screed; the texture `T_Parquet_D` is a herringbone
  ("spina di pesce") of 5 × 25 cm staves, and every parquet object carries `uv_rotate = 45°` so
  `geo.world_box_uv` sets the staves at 45° to the walls with the spine parallel to them.
* **Real-world alternative, not modelled:** 1984 practice (and the 2018 photo n24) would put 15 mm
  ceramic tiles at the same thickness – no level change – in the bathrooms and shower rooms,
  optionally in the kitchens, with wall tiles to about 2.00 m. A client decision; only the top layer
  of the stacks would change.
* Stair treads: oak (M_DoorLeaf) in the towers, M_StairTread in the carpet and schiera. Walls and
  ceilings M_PlasterInt. Tower common halls: cement floors, fair-faced brick. Terrace paving: cotto
  red (M_Brick) in the towers, M_Stone in the carpet and schiera. South-row vestibule: stone.
* No furniture, kitchen units, sanitary fittings, radiators, skirtings, flue boxes or vent ducts.

## 6. Validation and performance

**Full build** (`python model/build.py --interiors`, `build_report.json`): **1,982 objects, 976,034
triangles, 0 n-gons, 0 `[problem]` lines, 103 warnings, 81 slivers, 212.5 s** (site 0.3 s, towers
10.0 s, carpet 90.9 s, schiera 22.9 s; the rest is export preparation, validation and export).

| Part | Triangles (part, incl. joinery) | Budget | Objects | Module time | With the site |
|---|---|---|---|---|---|
| Towers | 247,972 (≈ 24.7k per tower) | 250,000 | 642 | 10–13 s | 685 objects, 273,740 |
| Carpet north | 217,278 (kit objects 190,798 + bodies 26,480) | 500,000 | 350 kit objects | ≈ 50 s idle, 66 s loaded | carpet (both modules) + site: 1,198 objects, 655,296 |
| Carpet middle + south | ≈ 392,000 (354k in 614 kit objects, 38k in the bodies) | 450,000 | 614 | 27–40 s | |
| Schiera | 70,302 (17,540 exterior) | 150,000 | — | 8–17 s | 145 objects, 96,454 |

The towers' margin is ≈ 2k triangles; the balusters (≈ 1.3k per tower) are the first candidate for
simplification.

**Warnings.** All 103 warnings of the full interior build also occur in the exterior-only build (109
there; six Gallery / NorthPavN z-fights vanish because the gallery-deck stand-in is replaced by R4).
They are z-fights between exterior objects whose faces were deliberately left where they are: the
tower bodies against the site plate at z −2.6 (10), the carpet end bands against the pavilion bodies
(44), the middle-row arch panels 2.5 cm over the core width (5), the campo bands, piers, grid, steps,
gutters and concrete, the court walls, and the schiera bodies against the site at z −0.5 (4). No
warning involves an interior object. The engine commit "Joinery engine: fixes shared by all parts"
removed the joinery warnings the builders had reported: window board and sill-block side pieces no
longer share a top face, the entrance-door knob sits on the leaf, window handles sit at mid-sash,
reveal plaster is flush with the frame, the linings are cut only where the joinery passes through
them, and an element in a second material (steel stair windows, grey cellar doors) gets its own
object.

**Slivers** (altitude under 0.1 mm; counted, not flagged): 56 in the tower bodies where the vault
cutter meets the pavilion wall face at dY ± 2.105, z ≈ 11.6 (hidden under the copper); 25 in the
schiera bodies at the 2.48 band seats; none in the carpet.

**Checks used by the builders and reviewers** (evidence under the scratchpad `impl/<part>/`
folders):

* `[problem]` count 0 from `validate.check_scene`: naming, applied transforms, no n-gons, watertight
  manifold shells, no loose vertices or zero-area faces, consistent normals (cavities allowed), a UV
  map and a material on every face; between objects the zfight / contact warnings.
* **Plan cuts** per floor (camera at floor + 1.5 m, geometry above hidden) overlaid on, or beside,
  the calibrated 1:50 plans: towers n8 / n56 / n28 / n46; carpet north n67 / n10 / n65 (house 20.5),
  campo house 38.5, block ends 8.5 and 63.5; carpet middle and south n11 / n67 / n10; schiera n27 /
  n45 (block 35.5) and whole-row L1 cuts of all 8 dwellings.
* **Sections** against the drawn ones: towers K-K and A-A (n62, n74); carpet N–S through flights and
  rooms, E–W through the cores (n18, n30); schiera capped sections B (n5) and F.
* **Ray probes:** inward rays through every opening (no cut ending in solid brick; the carpet m + s
  module runs a BVH parity test at d 0.46 / 0.66 behind every record: 0 openings end in brick);
  4,000 rays from each of 23 room points per tower for light leaks (none); scans for exposed
  insulation, adhesive or bare masonry seen from the rooms; an all-orientation z-fight check that
  also compares shells inside one object.
* **Exterior unchanged:** per-object geometry hashes against the pre-interior commit, exterior
  renders before / after from the same cameras, per-face material checks of exterior faces (which
  caught the tower E0 / W0 paint defect).
* Layer thickness probes (F1, F2, F3, the hall floor, R1, R2, terraces) and interior perspectives of
  every room type.

## 7. Known limitations and open questions

Consolidated from the research and the builders' reports.

**Sources**

1. Sheets SE 55 (notch / terraces), SE 57 (gallery / carpet core stair), SE 61 (schiera ground) and
   SE 62 (tower ground) are referenced but not in the set, so R3, R4, S1 and the tower and schiera
   F3 are assumed.
2. 1:50 plans exist only for carpet houses 8.5, 20.5, 32.5 and 38.5 (north row) and for the middle /
   south rows of the east block; the other houses and the west block are repeated and mirrored.
   Tower L1 (n56) was read flopped.
3. Not drawn or illegible: the composition of party and house-axis walls (≈ 0.21 measured), the
   expansion-joint leaves, the floor finish layers, the radiator-niche bottom, the leaf divisions of
   E, E1, F and D, the hinge sides of the schiera French windows and terrace door, interior-door
   labels ("7?/2?0"), the north-row L2 landing label ("1,24" or "1,34" against a measured 1.37; model
   1.27, **open**), the terrace-door height ("2,0x"; 2.05 used), the n62 L2 middle-bedroom ceiling.

**Walls and dimensions – open**

4. Carpet core width: layers.md W2 4.17 (± 2.085) against the exterior's `CORE_W` 4.10; the inner
   face ± 1.75 holds either way. The model keeps the exterior (north: masonry 0.28 to dE 1.77,
   finished 1.715).
5. n60 campo-house core at E 38.5: the west closure "10 \| 18,5" to a "telaio inclinato" is
   unexplained (modelled as W2). SE 63 axis Y 16: an unhatched ≈ 130 zone on the cellar side.
6. Should the north row's L2 rooms reach the drawn dividing wall at Y 7.906? `interior_carpet_ms`
   would have to hollow NorthPavM's north wall to 7.906 and the north module extend its rooms.
7. Should the exterior move the L1 end wall of houses 32.5 / 51.5 on the campo line outward (n31: dE
   4.88 → 5.26)? It would restore the 2.92 camera 1 and the middle-row rooms to E 35.45.
8. Is the north-row L2 bath zone Y 7.72 → 7.776 a pipe chase or solid? Modelled solid.
9. Schiera: should the French windows move to the verified 0.795 at Y 31.609 / 32.312, and the
   terrace door get its 0.10 step (sill 3.11)? Exterior changes. Wall 39.5 or 45: 45 kept.
10. Towers: the L3 stair-hall block wall (drawn E ≈ 2.78 → 2.95, exterior 2.86), the inner face of
    the middle part (n74 4.147 rendered, exterior 4.12 face brick) and the entrance width (1.25 or
    1.55) follow the exterior. Should the L3 terraces follow R3 (9.15)? That would raise D14's sill.
11. The tower L3 hall ceiling is lower than the n62 reading (§4.1).

**Allocation and use**

12. Which dwellings own the north-row cantine and the four outer cantina cells per middle-row house
    is not drawn (probably north-row dwellings); they are modelled as public cells off the corridor.
13. No dividing wall is drawn across the middle-row courts (dashed line only on E 29.5).

**Not modelled**

14. Bath vent ducts ("VENT. WC", ≈ 0.20 × 0.25 in the bay-wall line), flue boxes and kitchen
    counters, the cantine fronts' render and plinth (W9), the passage's north downstand beam and
    party-wall arches, rainwater outlets on the north-row terraces, the tower foundation void,
    skirtings. The schiera's exterior flue pipes stand next to the bar's south wall while the drawn
    duct is at the north end of the party wall; the outlet is not shown (low confidence).
15. Carpet core-window reveals are lined but square, not splayed 45° (n3). Towers: lining ends not
    re-verified after the review.

**Finishes – client decision**

16. Parquet in bathrooms, shower rooms and kitchens (modelled) against the 1984 norm of ceramic
    tiles (§5). Terrace divider heights (1.00 assumed) and the division of the joint terraces at the
    party lines are not drawn.

**Exterior-only points noticed on the way** (outside the interior scope): the carpet end bands and
campo bands z-fight with the pavilion bodies; the middle-row L0 arch panels overlap the core width
by 2.5 cm; the tile texture should show coppi; the copings are drawn 200 wide, 130 high and flush
against the model's wall + 20 overhang, 120 high; the vault crown is drawn at T + 2.72 against 2.70.
