# Gino Valle — Residenze IACP alla Giudecca: analysis of the drawings

Consolidated reading of the 89 files in `plans/` (catalogue: `plans/INDEX.md`).
This is the specification the 3D model is built from; the machine-readable
version of the same numbers is `model/giudecca/params.py`.

`nNN` = index in `plans/INDEX.md`, `SE nn` = sheet number of the executive
drawings. Values were read from dimension strings and level marks where legible,
otherwise measured on the scans against the axis bubbles (±0.05–0.15 module).

**Status: v2 — verified.** Draft v1 was checked claim by claim by seven
independent adversarial readers plus a completeness critic (230 checks; 72
corrected, 1 refuted). Section 9 lists what remains uncertain and how the model
handles it.

---

## 1. The project

| | |
|---|---|
| Name on the drawings | *Alloggi Giudecca — Legge 25.02.80 — Area Trevisan* (IACP social housing) |
| Architect | Gino Valle (Studio Architetti Valle) |
| Executive drawings | Jan 1984 – Nov 1985 (`SE` sheets, "GT 80"); 1:200 axonometric May 1985 (n39) |
| Earlier schemes, not modelled | n25 (July 1980, sheet "95 AG"), n85 (Casabella 478, March 1982) |
| Site | West end of the Giudecca, Venice, south of the Molino Stucky; Canale dei Lavraneri (Sacca Fisola) to the west, rio di S. Biagio to the east, a rio along the south (n25, n2, n36, n52) |
| Address (2018) | Calle dei Lavraneri, 30133 Venezia (n80) |

Parts:

* **Torri** — two columns of five 4-storey towers standing in the water at the
  west and east ends.
* **Tappeto** ("carpet") — three east–west rows of *H-houses* (north pavilion,
  stair core, south pavilion, light courts between the cores), 4 / 3 / 2 storeys
  from north to south, in two blocks (6 + 4 houses) separated by a 0.91 m slot.
* **Campo** — an open court cut into the carpet where the two houses flank the slot.
* **Schiera** — four 2-storey blocks (eight dwellings) at the south-east.
* Open square in the south-west, walled gardens, the north arcade with its
  external stairs, the garden north of the complex.

## 2. Coordinate system

1 module = **1.65 m**. Axis numbers of the 1:50 sheets:

* **X** runs east → west. Tower axes are integers 0…4 (east column); the carpet
  and schiera axes continue at X 5, 6, … but X4 → X5 is only half a module.
* **E** (used throughout) is the uniform module coordinate east → west:
  `E = X` on the towers, `E = X − 0.5` on the carpet and schiera. Carpet house
  axes therefore fall on half-integers (E 8.5, 14.5, …). The fine grid of the
  overall plans n34 / n33 / n70 follows the same half-module jump.
* **Y** runs north → south, uniform. Y = −4.225 is the north face of the towers,
  Y = 0 the north arcade axis of the carpet, Y = 35.225 the south face of the towers.
* **z** in metres; ±0.00 = finished ground floor of the dwellings.

The complex is mirror-symmetric in E about **E = 36.0** for the towers and the
carpet blocks' outer faces (not in its internal layout).

Model (Blender, 1 unit = 1 m, Z up, +X east, +Y north):

```
x = (36.0 − E) · 1.65        y = (15.5 − Y) · 1.65
```

Sheet titles name the **viewing direction**, not the façade ("Prospetto sud"
draws the north face). Key-plan insets on carpet and tower sheets are rotated
(top = east, left = north); schiera sheets are north-up.

## 3. Levels and the roof rule

| Level | z (m) | Source |
|---|---|---|
| Floors L0 / L1 / L2 / L3 | 0.00 / 3.01 / 6.02 / 9.02 | all sections; 3.01 = 2.71 + 0.30 slab (SE 58, SE 54) |
| Paving: north apron, calli, campo, square, portico | −0.45 | SE 63, SE 64, SE 28 |
| Cellars (cantine) | −0.32 | SE 63, SE 56 |
| Light courts, gardens | ≈ −0.10 | SE 63 |
| Garden walls, top | +1.22 | SE 63 |
| High water ("alta marea") / mean sea ("medio mare") | ≈ −1.15 / −2.50 | n61, n16 |

**Pavilion roof rule** (all mono-pitch roofs; T = top-floor level of the part):

| Element | z |
|---|---|
| High (outer) wall coping | T + 4.10 |
| Concrete band under it, outer face | T + 2.71 → T + 3.01 |
| Roof plane (clay tiles, "tegole", SE 54) | 34 %, ≈ 0.1 m below the coping line |
| Low (inner) wall coping, with copper box gutter | T + 2.90 |
| Core walls (eaves, copper gutter, SE 59) | T + 2.48 |
| Core roof: curved slab R 6.00 spanning E–W, crown | T + 2.70 |

| Part | T | High coping | Low coping | Core crown | Sources |
|---|---|---|---|---|---|
| North row | 9.02 | 13.12 | 11.93 | 11.72 | n64, n18, n29, n62 |
| Middle row | 6.02 | 10.12 | 8.92 | 8.72 | n49, n29 |
| South row | 3.01 | 7.10 | 5.91 | 5.71 | n29, n9, n47 |
| Towers | 9.02 | 13.12 | 11.93 | stair hall 11.40 → 11.73 | n62, n7, n61 |
| Schiera north bar | 3.01 | 7.10 (south wall) | 5.91 (north wall) | panel 5.91, vault ≈ 5.6 | n5, n13, n40 |

Copings: concrete ("copertina c.a."), ≈ 0.20 wide, 0.10–0.13 high (SE 54).

## 4. Towers (torri)

10 identical towers (n7, n61, n62, n8, n56, n28, n46, n63, n55, n74).
East column described; the west column is its mirror image in E (E' = 72 − E).

* **Along Y**: tower k (k = 0…4) spans `Y ∈ [−4.225 + 8k, 3.225 + 8k]`
  (12.29 m), split 4.04 | 4.21 | 4.04 m into north pavilion, middle, south
  pavilion. Gaps 0.91 m. Pavilion axes 2.02 m and 10.27 m from the north end;
  tower axis 6.145 m.
* **Along E**: outer face E −0.20, on the water (no quay). Pavilion inner face
  E 4.22, middle-part inner face E 4.12 (toward the calle).
* **Outer band** E −0.20 → 0.78:
  * pavilions: built to L2; at L3 a terrace (≈ 1.3 × 3.4 m) behind a 0.30
    parapet to **9.97** (coping 9.84–9.97). L3 and the roofs stand on the body
    E 0.78 → 4.22 (5.68 m);
  * middle part: an **open void** from ground to sky, closed at ground by a low
    front wall (E −0.12 → 0.04, top 1.26) round a small patio.
* **Roofs**: pavilion mono-pitch roofs over E 0.78 → 4.22 rising **outward**
  (to the N / S ends): coping 11.93 at the inner edge, 13.12 at the end walls.
  Middle part: a 34 % lean-to over the outer rooms from 8.92 (E 0.78) up to
  ≈ 10.05 (E 2.86); stair-hall block E 2.86 → 4.12 with a curved copper roof
  from 11.40 to 11.73.
* **Stair**: middle part, inner side; L0 → L1 dog-leg, then straight flights.
  Entrance at the north end of the middle part on the inner face (opening
  1.25 × 2.33, door 0.92 × 2.04, three steps 1.55 wide).
* **Openings** (z_f = floor level; widths are clear openings):
  * outer face of the pavilions, on the pavilion axes: L0 and L1 single
    1.03 m windows (sill z_f + 0.95, head z_f + 2.35); L2 a pair 0.93 + 0.36 +
    0.93 (sill 6.97, head 8.37); L3 a French door 1.04 × (9.02 → 11.37) in the
    set-back wall at E 0.78;
  * recessed middle wall (E 0.78, tower axis): L0 opening 2.12 × 2.35 to the
    patio; L1 arched loggia opening 2.12 wide, parapet to 3.98, spring 5.00,
    crown 5.44, precast hood 3.02 × 0.77; L2 two 0.92 windows with a 0.37 pier
    (6.95 → 8.37); two 0.61 windows (10.46 → 11.07) in the stair-hall wall at
    E 2.86, at 4.87 and 6.15 m from the north end;
  * inner face: per pavilion one 0.91 × 0.92 window per floor (z_f + 1.43 →
    z_f + 2.35) on the pavilion axes; middle part: entrance door and four
    0.61 stair windows (4.53–5.14 m from the N end at z 4.42 and 7.42;
    7.28–7.90 m at z 6.83 and 9.81);
  * N and S end faces: blank face brick, one corbelled chimney stack each
    (bracket ≈ 12.3, top ≈ 14.2; n64, n39).
* **Bands**: continuous 13 cm concrete head bands at z_f + 2.35 → 2.48 on the
  pavilion faces; 11.38 → 11.51 on the L3 walls.
* **Water stairs**: in every gap (and north of the north-east tower), a flight
  of 13 risers × 0.155 / 0.30 treads, full gap width, descending outward from
  −0.45 at E 2.45 to −2.45 at E 0.25; flat at −0.45 from E 2.45 to 4.22.

## 5. Carpet (tappeto)

### 5.1 Rows (dimension chains SE 9 / 12 / 15; sections n64, n29)

Core zones are centred on **Y = 3.5 + 8k**. Pavilion 4.04 m (2.4485 module),
core zone 4.21 m (2.5515), joint 0.91 m (0.5515).

| Row | North pavilion | Core zone | South pavilion | Joint |
|---|---|---|---|---|
| North (L0–L3) | −0.224 → 2.224 | 2.224 → 4.776 | 4.776 → 7.224 | 7.224 → 7.776 |
| Middle (L0–L2) | 7.776 → 10.224 | 10.224 → 12.776 | 12.776 → 15.224 | 15.224 → 15.776 |
| South (L0–L1) | 15.776 → 18.224 | 18.224 → 20.776 | 20.776 → 23.224 | — |

The **joint strips** are built up to the taller row's top floor and are open
**roof terraces** above it: north/middle deck ≈ 9.15 (L3 terraces of the north
row), middle/south deck ≈ 6.15 (L2 terraces of the middle row). Their parapet is
the lower row's high wall (10.12 / 7.10) (n64, n18, n33, n70, n35).

### 5.2 Houses (n34, n47, n30, n16, n14)

* **East block** E 5.28 → 41.72 (6 houses), **west block** E 42.28 → 66.72
  (4 houses); the 0.91 m **slot** E 41.72 → 42.28 runs through all rows.
* House (core) axes: E **8.5, 14.5, 20.5, 26.5, 32.5, 38.5** | **45.5, 51.5,
  57.5, 63.5**. Party walls on E 11.5, 17.5, 23.5, 29.5, 35.5 | 48.5, 54.5, 60.5.
  Expansion joints (double walls, 9 cm) on **E 17.5, 29.5, 54.5**: 2-house
  segments of 20.185 m (19.71 m for the middle segment of the east block).
* Block faces are 5.32 m (3.22 modules) from the nearest house axis.
* **Cores**: 4.10 m wide, centred on the house axis, two parallel flights
  (each H-house is two mirrored dwellings). North-row cores start at L1, on four
  corner piers (axis ± 1.15 module).
* **Light courts** between cores (≈ 3.5 modules), open to the sky from the
  ground; half-courts at the block ends closed by a 1.25 m wall in the middle and
  south rows.
* **Notches**: the north row's south pavilion and the middle row's north
  pavilion are interrupted on **every core axis** by a 2.97 m bay (axis ±
  1.485 m). In the north row the bay cuts the top floor and roof: it holds the L3
  stair landing under the core's copper vault and is closed to the south by the
  **oculus panel** (§5.5). In the middle row the bay is cut down to an L2 terrace.
  All other pavilions run continuously along each segment (n57, n66, n59, n35).

### 5.3 What is built on each floor (n53, n34, n33, n70, SE 8–17)

| | North row | Middle row | South row |
|---|---|---|---|
| L0 | **Open portico** Y −0.22 → 4.95: north arcade, pier rows Y ≈ 2.11 and 4.95; cores float above on corner piers; courts open. South pavilion band Y 4.95 → 7.22: **cantine** at E 9.75–19.6, 21.6–31.45, 52.55–62.25, **open pilotis** elsewhere (incl. an arch in the block-end walls). | Covered E–W corridor in the joint (Y 7.24 → 7.98); cantine Y 8.0 → 10.22; 8 cores (no core in the campo houses); **covered passage** under the south pavilion, Y 13.0 → 15.0, pier row on its north side, open at the block ends and into the campo. | Dwellings (kitchens N, living rooms S with French doors to the gardens); cellars in the joint. |
| L1 | **Gallery** ("ballatoio") in the north pavilion: deck Y 0.45 → 2.22, parapet to 3.87, behind the arcade; 10 cores; south pavilion rooms. | rooms; 8 cores | rooms (top floor) |
| L2 | complete | complete (top floor); L2 terraces in the north-pavilion notches and on the M/S joint | — |
| L3 | complete (top floor); L3 terraces on the N/M joint | — | — |

### 5.4 The campo (n11, n31, n33, n34, n35, n53)

* Spans the two houses flanking the slot, between party walls **E 35.5 and 48.5**.
* The middle row is absent there; open to the sky Y 8.24 → 15.0.
* The north row's south pavilion over the campo starts at L2 (and reaches
  Y ≈ 8.0–8.24 at L2), carried on tall brick piers in two rows at **Y 7.1 and
  8.1** (type-2 piers 0.74 × 0.395 at house axis ± 1.12 module, a small drain
  pier on the axis, L-shaped corner piers at the slot, T piers on E 35.5 / 48.5),
  height −0.45 → 5.06 plus a concrete band to 5.80 (n11, n72).
* Two narrow straight stairs (0.9 m) rise from the campo to the gallery,
  centred at E ≈ 36.0 and 48.0, Y 5.6 → 1.7.
* The red 7 × 5 grid on n1 is the 2018 pavilion installation — **not** modelled.

### 5.5 Façades (n16, n14, n15, n59, n47, n48, n49, n77, n9, SE 50/51/53/66)

Offsets are in metres from the house axis.

* **North façade** (Y −0.224):
  * L0–L1 **arcade**, per house: central pier 0.53; flat openings 1.22 at
    ±0.265 → ±1.485 (head 5.10, concrete panel 5.10 → 5.57); piers 0.74;
    segmental arches 2.355 at ±2.225 → ±4.58 (spring 5.10, crown 5.585, precast
    panel to 5.86); half of a 0.74 party pier. Next to an expansion joint, the
    campo party walls and the block ends the arch is 2.15 wide (crown 5.545);
    block-end piers 0.945. Behind: the gallery deck (3.01) and parapet (3.87).
  * L2 blank brick.
  * L3 **trifore** at ±2.475: 1.87 wide (lights 0.415 + 1.04 + 0.415), side
    sills 9.96, central sill 9.68, spring 11.02, crown 11.37 (R 1.42),
    precast lintel 2.52 × (11.02 → 11.55).
  * Coping band 12.99 → 13.12.
* **External stairs** to the gallery at E **10.56** and **55.50**, inside an
  arcade arch: from Y −3.70 (−0.45), 5 risers, landing (Y −2.94 → −2.33), 15
  risers to the gallery (3.01) at Y ≈ +0.25; risers 0.172, treads 0.30, clear
  width 1.19, side walls 0.255 with sloping coping (SE 64).
* **Court faces** (pavilions toward the courts): one opening per floor on each
  side of a court, at ±3.30 (party wall ∓ 1.65); the top floor of every row is
  blank. North-row north pavilion: L0–L1 double-height arches (spring ≈ 5.05),
  L2 two-light 2.13. North-row south pavilion: L0 arches (spring 1.95, panel to
  2.71), L1 single 1.04, L2 two-light 2.13. Middle-row south pavilion: L0 arches
  into the passage, L1 two-light. South row: L0 French-door pairs, L1 singles.
* **Core faces** toward the courts: two 0.60 × 0.60 landing windows per floor
  (z_f + 1.20 → 1.80) at the core-zone mid-line ± 1.08 m; vault eaves with copper
  gutter at T + 2.48.
* **Oculus panel** (north row, closing each L3 notch at Y ≈ 7.16–7.22, facing
  south over the joint terrace; n60, n47, n50): precast concrete, lower part
  2.95 m wide from 9.02 to 10.10, upper part 3.76 m wide from 10.10 to an arc of
  R 6.50 with crown **11.92**; two oculi Ø 0.90 at z 10.67, axis ± 0.825.
* **North-row south face above the joint** (L3): French doors 1.04 at ±3.30
  (head 11.37) on each pavilion block, opening onto the joint terrace.
* **Middle-row south face above the joint** (L2): four doors 1.04 at ±1.00 and
  ±2.49 (head ≈ 8.37).
* **South façade** of the south row (Y 23.224): L1 two two-light windows per
  house (2 × 0.91 + 0.14 = 1.96) at ±1.74, sill 3.95, head 5.36; L0 four French
  doors 1.04 at ±1.00 and ±2.49, head 2.25; coping 7.10.
* **Block ends** (E 5.28, 41.72, 42.28, 66.72; n9): tall arch into the
  portico/gallery in the north pavilion (spring ≈ 4.85); open portico under the
  north-row core zone; L0 arch in the north row's south pavilion and at the
  passage of the middle row; low walls (1.25) closing the middle- and south-row
  half-courts; core side faces with their square windows; otherwise blank.
* **Chimneys**: corbelled stacks on the south faces of the pavilion blocks on
  the party walls and joints — north row up to ≈ 14.0 (2 + 2 or 4 flues),
  middle row up to ≈ 10.9 (n47, n64, n39).

## 6. Schiera (SE 44–49, n5, n6, n13, n37, n40)

* Outer faces **E 7.28 → 39.72**, **Y 28.78 → 35.22**; walls 0.37 thick with
  the axes on their inner faces.
* **North bar** Y 28.78 → 31.22 (a 4.04 m pavilion), continuous over the full
  length, two storeys; mono-pitch roof rising **south**: coping 5.91 on the
  north wall, 7.10 on the south wall. Expansion joint on E 23.5.
* **Four blocks** on party axes E **35.5, 27.5, 19.5, 11.5**, each 7.34 m wide
  (axis ± 2.224 module), two mirrored dwellings. At L0 one deep volume Y 28.78 →
  35.22 (kitchen north, living room south). Above L0:
  * **core** (twin stairs) axis ± 1.14 module, Y 31.22 → 32.93, barrel vault
    (crown ≈ 5.6), with a **south-facing oculus panel** 4.17 m wide on the 4.09
    coping: sides 5.57, crown 5.91 (R 6.50), oculi Ø 0.60 at z 4.66, axis ±
    0.825 m (SE 60);
  * **L1 terraces** either side of the core, Y 31.22 → 32.93, parapet to 4.09;
  * **single-storey lean-to** Y 32.93 → 35.22 over the full block width,
    falling south from 4.10 to 2.90.
* **Bays** between the blocks (E 39.5–37.5, 33.5–29.5, 25.5–21.5, 17.5–13.5,
  9.5–7.5): **porticoes** under the north bar and **gardens** south of it
  (Y 31.22 → 34.97, walls to +1.22, dividing walls on E 31.5 / 23.5 / 15.5).
* **Portico arches** (both faces of the bar), centred on E 8.5, 14.5, 16.5,
  22.5, 24.5, 30.5, 32.5, 38.5: span 2.15 (end bays) / 2.34, spring 2.0, crown
  2.5, precast block 2.0 → 2.80; 0.62 × 1.25 low walls either side of a 1.10
  passage; steps on the north side.
* **Windows**: north face L1 four pairs of 0.91 × 0.92 (4.44 → 5.36) at party
  axis −0.51 / +0.49 module; bar south face L1 1.04 × 1.41 windows above each
  arch (3.95 → 5.36) and terrace doors at party axis ± 1.68 module; lean-to south
  face two 1.04 × 1.41 windows per block (0.94 → 2.35) at axis ± 1 module; end
  faces blank.
* Ground outside ≈ −0.40; gardens and porticoes ≈ 0.00.

## 7. Site (context, approximate)

* Paving at −0.45 between the tower columns: north apron Y −4.7 → −0.22,
  calli between towers and carpet (E 4.22 → 5.28 and 66.72 → 67.78), the passage
  Y 27.0 → 28.78, the campo, and the **open square** E ≈ 39.7 → 67.78,
  Y 25.0 → 35.25 (square grid ≈ 1 module).
* South-row **gardens**: east block Y 23.22 → 27.0, west block Y 23.22 → 25.0,
  walls 0.30 × top +1.22, cross walls every 3 modules.
* **Water** at −2.50 (high water −1.15): Canale dei Lavraneri to the west
  (≈ 60 m), rio di S. Biagio to the east (≈ 11 m, far bank E ≈ −7), a rio to
  the south (≈ 8 m, Y 35.25 → 40.5) with a small arched footbridge at
  E ≈ 4.4–5.5. The towers rise straight from the water.
* **Garden** north of the complex E ≈ 11 → 55, Y ≈ −26.5 → −4.7, walled, with
  trees.

## 8. Materials

| Material | Where |
|---|---|
| Face brick ("mattoni a faccia vista") | all walls and piers |
| Exposed concrete | copings, bands, lintel and sill pieces, arcade panels, oculus panels, loggia hoods |
| Clay tiles | pavilion mono-pitch roofs (SE 54) |
| Copper | core vaults, stair-hall roofs, gutters and flashings (SE 59) |
| Glass, painted frames | windows and doors |
| Stone paving / lawn / water | site |

## 9. Remaining uncertainty and how the model treats it

| Item | Evidence | Model |
|---|---|---|
| Middle-row north-pavilion notch depth (L2 terrace) | medium (n66, n57) | notch cut down to the L2 floor |
| Chimney flue counts and exact sections | medium | simple corbelled stacks with caps at the stated tops |
| Window frames, glazing bars, reveals | not in the 1:50 sheets | glass set 0.12 m back; mullions only where drawn (trifore, two-lights) |
| Schiera flue pipes | low (n5, n39) | small twin pipes, top 7.85 |
| West-column water stairs | mirrored from the east column | mirrored |
| Site beyond the complex | approximate (site plans) | simple ground, water and garden only |
