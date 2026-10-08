# Gino Valle — Residenze IACP alla Giudecca: analysis of the drawings

Consolidated reading of the 89 files in `plans/` (catalogue: `plans/INDEX.md`).
This document is the specification the 3D model is built from. Every value
cites the drawings it comes from (`nNN` = index in `plans/INDEX.md`, `SE nn` =
sheet number of the 1:50 / detail drawings). Values marked *(est.)* are
measured from scans rather than read from a dimension.

Status: **draft v1 — under verification** (see "Open questions").

---

## 1. The project

| | |
|---|---|
| Name on the drawings | *Alloggi Giudecca — Legge 25.02.80 — Area Trevisan* (IACP social housing) |
| Architect | Gino Valle (Studio Architetti Valle) |
| Executive drawings | Jan 1984 – Nov 1985 (`SE` sheets, "GT 80"); axonometric SE 1/200 dated May 1985 (n39) |
| Earlier schemes (not modelled) | n25 (scheme of July 1980, sheet "95 AG"), n85 (Casabella 478, March 1982 cover) |
| Site | West end of the Giudecca, Venice: south of the Molino Stucky, Canale dei Lavraneri / Sacca Fisola bridge to the west, rio di S. Biagio to the east (n25, n32, n36, n4) |
| Address (2018) | Calle dei Lavraneri, Giudecca, 30133 Venezia (n80, "Unfolding Pavilion" poster) |

Three building types make up the complex:

* **Torri** — two columns of five 4-storey towers, at the west and east ends.
* **Tappeto** ("carpet") — between the tower columns: three east–west rows of
  *H-houses* (north pavilion + stair core + south pavilion, with light courts
  beside each core), 4, 3 and 2 storeys from north to south.
* **Schiera** — a row of four 2-storey blocks (eight dwellings) at the south-east.

Plus a central open space (*campo*) inside the carpet, an open paved square in
the south-west, gardens, external stairs and the north arcade.

## 2. Coordinate system

The 1:50 sheets use numbered axes, 1 module = **1.65 m** (n1 "165", SE chains).

* **X (ES axis numbers)** run east → west. X = 0 is near the outer (east) face of
  the east towers. The axes are not uniform: X4 → X5 is only half a module
  (n16, n62), so tower axes and carpet axes are offset by 0.5 module.
* **E** (used in this document) = uniform module coordinate, east → west:
  `E = X` for tower axes (X ≤ 4), `E = X − 0.5` for carpet / schiera axes (X ≥ 5).
  E is what the fine square grid of the overall plans measures (n34, n33, n70).
* **Y** (ES axis numbers) run north → south, uniform. Y = −4 is the north end of
  the towers, Y = 0 is the axis of the carpet's north arcade, ~35 the south end.
* Heights **z** in metres, ±0.00 = finished ground floor of the dwellings.

Model (Blender, 1 unit = 1 m, Z up, +Y = north, +X = east):

```
x = (36.0 − E) · 1.65        y = (15.5 − Y) · 1.65        z = z
```

Caution: sheet titles name the **viewing direction**, not the façade
("Prospetto sud" draws the north face, n13/n16). Key-plan insets on the carpet
and tower sheets are rotated (top = east, left = north); schiera sheets are
north-up.

## 3. Levels (all parts)

| Level | z (m) | Source |
|---|---|---|
| Finished floors L0 / L1 / L2 / L3 | 0.00 / 3.01 / 6.02 / 9.02 | every section; floor-to-floor 3.01 = 2.71 + 0.30 slab (SE 58, SE 54) |
| Exterior paving, piazza, north side, tower quays | −0.45 | SE 63, SE 64, n61, n16 |
| Cellars (cantine), court floors | −0.32 | SE 63, SE 56, n76 |
| Gardens of the south row | ≈ 0.00, walls to +1.22 | SE 63 |
| Mean sea level ("Medio mare") | ≈ −2.5 | n16 |
| Foundation base | −1.95 | SE 63 |

Rule for pitched (mono-pitch) pavilion roofs, all rows and towers
(T = top-floor level of that part): outer wall + coping at **T + 4.10**, roof
plane at **34 %** over the 3.30 m between walls (SE 54: 37 + 330 + 37 = 404),
inner (low) edge ≈ **T + 2.95**. Core roofs: slab **T + 2.70**, parapet **T + 2.91**.

| Part | T | High edge | Low edge | Core roof / parapet | Sources |
|---|---|---|---|---|---|
| North row (4 st.) | 9.02 | 13.12 | ≈ 11.9 | 11.72 / 11.93 | n64, n18, n17, n29, n68, n12 |
| Middle row (3 st.) | 6.02 | 10.12 (10.13–10.38) | ≈ 9.0 | 8.73 / 8.93–9.02 | n29, n64, n68 |
| South row (2 st.) | 3.01 | 7.10 | ≈ 6.0 | 5.71 / 5.92 | n29, n47, n64 |
| Towers (4 st.) | 9.02 | 13.12 | 11.75 | 11.73 / 11.93 | n62, n7, n61 |
| Schiera north bar (2 st.) | 3.01 | 7.10 (south side) | 5.91 (north wall) | core crown ≈ 5.9–6.0 | n5, n6, n13, n37 |

## 4. Towers (torri)

10 towers, 5 per column, identical (n7, n61, n8, n55).

* **Along Y** (dimension chain SE 37 / SE 41: 4.04 | 4.21 | 4.04 | 0.91 m):
  tower k (k = 0…4) is 12.29 m long, centred on Y = −0.5 + 8k, i.e.
  `Y ∈ [−4.225 + 8k, 3.225 + 8k]`; gaps 0.91 m (0.552 module), pitch 13.20 m.
  Three parts: north pavilion 4.04 m, middle 4.21 m, south pavilion 4.04 m.
* **Along E**: east column E ∈ [−0.15, 4.35] (≈ 7.4 m deep); west column mirrored
  about E = 36.0 → E ∈ [67.65, 72.15]. *(est., n8, n53, n55, n62)*
* **Outer band** (1 module, the face toward the canal): full height only to L2;
  at L3 it is a **terrace** with parapet ≈ +9.9; L3 and the roofs stand on the
  remaining ≈ 3.4-module body (n55 E–W section, n70, n46, n61, n16).
* **Roofs**: pavilions mono-pitch 34 % rising **outward** (to the N and S ends)
  from 11.75 to 13.12; middle flat roof 11.73, parapet 11.93 (n62 B–B, n7).
* **Middle part**: stair hall (dog-leg flights, n74 SE 58) on the **inner**
  side (toward the carpet); on the **outer** side a 1-module recessed band:
  L0 recessed entrance ≈ 2.1 × 2.4, L1 arched loggia (crown ≈ 5.5, R ≈ 1.15–1.5)
  behind a rail, L2 a pair of windows, L3 two 0.6 m square windows above the
  terrace parapet (n61, n55, ES 42).
* **Windows**:
  * Outer face, per pavilion, one per floor ≈ 1.04 m wide: L0 sill 0.94 / head
    2.39; L1 3.85 / 5.38; L2 a pair (1.03 each) 6.84 / 8.46; L3 9.92 / 11.46 (n61).
  * Inner face, per pavilion, one per floor 0.91 × 0.92 (sill +1.43, head +2.35
    above each floor, SE 53); middle: entrance door 0.91 × 2.04 (SE 53), small
    0.6 × 0.6 stair windows staggered (n3, n7).
  * N and S end faces: blank face brick (n16).
* **Gaps**: narrow steps (≈ 10 risers) descend from the quay toward the water
  (≈ −2.2) in each 0.91 m gap (n61, n62, n8).
* Material: face brick ("mattoni a faccia vista"), concrete copings, bands and
  lintels (13 cm bands at lintels and sills, SE 53).

## 5. Carpet (tappeto)

### 5.1 Rows along Y (dimension chains SE 9, SE 12, SE 15; sections n64, n29)

| Row | North pavilion | Core zone (cores + courts) | South pavilion | Joint strip |
|---|---|---|---|---|
| North (4 st.) | −0.29 → 2.16 | 2.16 → 4.71 | 4.71 → 7.16 | 7.16 → 7.71 |
| Middle (3 st.) | 7.71 → 10.16 | 10.16 → 12.71 | 12.71 → 15.16 | 15.16 → 15.71 |
| South (2 st.) | 15.71 → 18.16 | 18.16 → 20.71 | 20.71 → 23.16 | — |

Pavilion depth 4.04 m, core zone 4.21 m, joint 0.91 m (same chain as the towers).
The joint strips are built and roofed flat at the **lower** neighbour's high
edge (≈ 10.1 between north and middle rows, ≈ 7.1–7.3 between middle and south),
and carry chimney stacks (n64, n29, n18).

### 5.2 Houses along E

* Two blocks separated by a **0.91 m slot** (E 41.72 → 42.28) running through
  all rows (n47 chain, n30, n53, n70):
  * **East block**: 6 houses, party-wall axes at E = 5.6 + 6k (k = 0…6), outer
    faces E 5.48 and 41.72.
  * **West block**: 4 houses, party-wall axes at E = 42.4 + 6k (k = 0…4), faces
    E 42.28 and 66.52.
  * 2-house segments (≈ 20.17 m) with expansion joints between (n47, n59).
* Each house is 6 modules (9.9 m) wide; **stair core** centred on the house axis
  (E 8.6, 14.6, 20.6, 26.6, 32.6, 38.6 | 45.4, 51.4, 57.4, 63.4), ≈ 2.4 modules
  (3.96 m) wide outside, two parallel flights split by a central wall: each
  H-house is two mirrored dwellings (n69, n22, n30).
* **Light courts** between cores, ≈ 3.6 modules wide, open to the sky; at the
  block ends half-courts (≈ 1.9 modules) closed by a ≈ 1.3 m wall (n9).
* Pavilions run continuously along each 2-house segment.

### 5.3 What exists on each floor

| | North row | Middle row | South row |
|---|---|---|---|
| L0 | Open **portico** Y −0.29 → ≈ 5.0 (pier rows at Y ≈ 0, 2.2, 5.0); no cores; **cantine** Y 5.0 → 7.16 | cantine Y 7.71 → 10.16 (E–W corridor along the joint); 8 cores + courts; covered **E–W passage** under the south pavilion (pier row Y ≈ 13.0) | dwellings (kitchens N, living rooms S with French doors to gardens) |
| L1 | **Gallery** ("ballatoio") in the north pavilion behind the arcade; 10 cores; south pavilion rooms | rooms; 8 cores | rooms (top floor) |
| L2 | full | full (top floor), doors to terraces on the joint strip | — |
| L3 | full (top floor), doors to terraces on the joint strip | — | — |

### 5.4 The campo

* Occupies the two houses flanking the slot: E 35.6 → 48.4 (n33, n34, n53).
* Middle row absent there on all floors; open to the sky Y ≈ 8.2 → 15.2.
* North row's south pavilion absent at L0–L1 over Y ≈ 4.7 → 8.2, replaced by
  tall piers (rows at Y ≈ 7.1 and 8.1); present at L2–L3 (n34, n33, n35, n36).
* Two straight stairs in the courts beside the campo cores (E ≈ 36.4 and 47.3,
  Y ≈ 1.6 → 5.7) lead to the gallery (n34, SE 8/11/14/17/20).
* The red 7 × 5 grid on n1 is the 2018 pavilion installation — **not** modelled.

### 5.5 Façades

* **North façade** (Y = −0.29, both blocks, n16, n59 d4, n52 profile 4):
  * L0–L1 **double-height arcade**, repeating per house: [arch | two flat openings
    on the core axis | arch], arch pairs straddle every party wall. Arches
    segmental, spring ≈ 5.10, crown ≈ 5.55; flat openings ≈ 1.8 m wide, head 5.10;
    exposed concrete lintel band 5.10 → 5.86 (SE 66 panels, 76 cm). Gallery slab
    (3.01) and parapet (≈ 3.9) visible behind.
  * L2 blank brick. L3 **trifore** (arched triple windows, 1.87 m, SE 51/53)
    every 3 modules (house axis ± 1.5), crown ≈ +2.35 above L3. Flat top at 13.12.
* **External stairs** to the gallery at E ≈ 10.5 and 55.5: straight flights from
  Y ≈ −4.2 to −0.29, −0.45 → 2.99, 20 risers × 17.2, treads 30, landing 1.00,
  clear width 1.19, side walls 0.255 with sloping coping (SE 64).
* **Court faces** of pavilions: L0 French doors / arches (R ≈ 1.45), upper floors
  windows (single on L1, two-light on L2) (n77, n48, n49).
* **Core faces** toward the courts: two 0.60 m square landing windows per floor
  (n3, n9, n29); crowned by a **curved precast panel with two oculi**: top arc
  R 6.50, crown T + 2.90, oculi Ø 0.90 at T + 1.65, 1.65 m apart (n60, n50, n47);
  the core roof is a shallow copper vault, R 6.0, spanning E–W (SE 59, n30, n77).
* **South façade** of the south row (Y = 23.16, n47, n48): L1 two-light windows
  ≈ 2.0 m flanking each core axis (sill ≈ 4.0, head ≈ 5.45); L0 French doors
  (1.04 × 2.25, SE 53) to the gardens.
* **Block ends** (E 5.48, 41.72, 42.28, 66.52; n9): north pavilion with a tall
  arch to the portico/gallery; middle-row south pavilion with the passage arch;
  core end faces with paired square windows; elsewhere blank brick.
* Chimneys: twin-flue stacks with caps, ≈ 14.0 on the north/middle joint, near
  core axes (n64, n47); lower ones on the middle/south joint.

## 6. Schiera

* E 7.5 → 39.5 (ES X 8–40), Y 28.95 → 35.15 (SE 44–49, n5, n6, n13, n37, n68).
* **Four blocks** (two mirrored dwellings each, party walls on ES X 36, 28, 20, 12):
  ES X 38–34, 30–26, 22–18, 14–10. Bays between blocks (ES X 40–38, 34–30,
  26–22, 18–14, 10–8): **portico** at Y 29 → 31 and **gardens** at Y 31 → 35.
* **North bar**, Y 28.95 → ≈ 31.0, continuous over the full length: 2 storeys
  (bedrooms over the porticoes at L1); mono-pitch roof rising **southward**
  (inward) from 5.91 (north wall) to 7.10.
* **Core** of each block on the party wall, Y ≈ 31.2 → 32.7: twin stairs, vaulted
  top, south-facing curved panel 4.17 m wide, crown T + 2.90 (≈ 5.91–6.0), two
  oculi Ø 0.60, 1.65 m apart (SE 60, n6).
* **South rooms**, Y ≈ 32.7 → 35.15, single storey, ≈ 7.3 m wide per block,
  lean-to falling **south** from 4.10 to 2.90; two windows ≈ 1.15 × 1.5 on the
  south face (n6). L1 terraces either side of the core (Y ≈ 31 → 33).
* North face (n13): flat 2-storey wall, high window pairs under the eave
  (≈ 1.1 × 1.0), arched portico openings (two per 4-module bay, one per 2-module
  end bay; span ≈ 2.2, crown ≈ 2.8).
* Garden walls ≈ 1.5 m between blocks (n6).

## 7. Site (approximate context only)

* Open square E ≈ 41.5 → 66.5, Y ≈ 25 → 35.3, paved in a square grid, low walls
  / planters on its north edge (n53, n71, n36).
* South-row gardens Y 23.16 → ≈ 27.2 (east block) / ≈ 25 (west block), walls 1.22.
* Garden with trees north of the complex (n2, n32, n71, n81).
* Water: Canale dei Lavraneri west, rio di S. Biagio east (steps down from the
  tower quays), a rio along the south with a footbridge at the south-east
  (n25, n52, n71, n81). Exact quay widths unknown.

## 8. Open questions (to verify)

1. Tower E-extent and the outer-band / terrace setback (n55, n61, n62 A–A).
2. Whether pavilion roofs are continuous over each 2-house segment or notched at
   cores (n59 d2 vs. model photos).
3. Joint-strip roof heights and what they contain (n64, n18, n29).
4. Exact arcade rhythm on the north façade (n16 chain partly illegible).
5. Exact E-position of the carpet's east face (E 5.4 vs 5.48 vs ES 5.9).
6. Campo piers: positions and section.
7. Schiera block extents in Y for the south rooms and the core.
