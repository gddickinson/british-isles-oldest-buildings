# BT6a: building-gen checked against the sources (2026-10-28)

building-gen (`~/Documents/GitHub/building-gen`, commit b58feca, MIT) was checked before any of its output is shown
here. Its outputs in `output/` (seed 42, every type, plus the detailed `build_complete.py` townhouse) were read against
the sourced `plan` and `structure` of the catalogue's own building types (`data/curated/building_types/lineage*.json`)
and against the catalogue's floor plans.

**Verdict: none of the four implemented types is shown, as a 3D model or an image.** Each has errors a visitor would
take as fact. What BT6 shows instead: plans of real examples (BT6b, done) and, later, labelled diagrams drawn from
sources (BT6c). Fixes belong in building-gen itself; once a type passes the checks below it can be shown, labelled as
an illustration.

## Every type
- The CLI applies one style to every type (`--style georgian` is the only one): the sheets are titled "Georgian
  Victorian Terrace", "Georgian Cottage", "Georgian Tavern", and all are drawn in brick.
- Furniture and fittings of today in every period: sofa, wardrobes, washing machine ("WM") and fridge ("FR") in a
  cottage scullery and a "medieval" tavern kitchen, fitted bathrooms with baths.
- The 3D views (`*_3d_views.png`) are boxes with a flat lid; the roof is a separate dark prism beside the gable;
  the `*_3d_perspective.png` images are blank.

## Georgian townhouse (`townhouse`, `townhouse_reference`, `grosvenor_townhouse`, `build_complete.py`)
Sourced plan (terraced-house, townhouse): a row of tall narrow houses, several storeys, two or three rooms deep,
sometimes with a basement and attic.
- `grosvenor_townhouse`: 12.1 × 11.7 m, nearly square, with a 50 m² "dressing room" on the ground floor and a stair
  hall filling the middle third of every floor: not the narrow front-and-back-room plan with a side stair.
- `build_complete.py` front elevation ("Grosvenor Street Townhouse (1763)"): the chimney stacks are drawn in front
  of the façade, across the windows of the two outer bays; part of the staircase shows through the top-floor front
  wall; a steep 45° gable faces the street, where a London house of the 1760s has a parapet hiding a low roof; the
  ground floor sits at pavement level with no area or basement light, though the program has a basement.
- `townhouse_reference` (8.7 × 9.7 m) is closest: three bays, front and back rooms with the stair between, a fireplace
  per room. Still: rooms on the first floor left blank, bathroom and WC indoors as fitted rooms.

## Victorian terrace (`victorian_terrace`)
Sourced plan (bylaw terrace): front living room and back dining room with the stair between, two bedrooms above,
often a rear scullery, a long narrow yard with the privy.
- Right in outline: hall and stair to one side, front and back rooms, kitchen and scullery behind.
- The rear outshot is the full width of the house, so there is no yard beside it; real back extensions are narrower.
- A fitted bathroom over the kitchen: the sourced plan has a privy in the yard (bathrooms came later).
- Fireplaces on the cross wall between front and back rooms rather than on the party walls.
- The attic floor is a single storage room over half the plan, the front half left as void.

## Cottage (`cottage`)
Sourced (cottage): the cheapest local materials (thatch, slate, rubble stone or cob), typically "two up, two down".
- Right: two up, two down, thick (0.5 m) walls, front door straight into the hall, no passage.
- No windows on the ground floor at all; upstairs windows only in the gables.
- The stair runs full depth between the rooms as a walled corridor; the fireplaces are on the rear partition, not
  in a central or gable stack (the template's own notes say central or end chimney with inglenook).
- Brick, not the local materials the type is defined by; the 3D roof is flat.

## Medieval tavern (`tavern`)
Sourced (inn): two-storey timber frame with steep shingle roofs (14th century); rooms round an inner court, kitchen
and parlour at the front, stables at the back.
- A compact brick double pile of 10.4 × 8.1 m: no courtyard, no stables, no timber frame.
- Corridor-plan guest rooms with wardrobes, a central landing and stair: a Georgian house plan.

## The catalogue's floor plans
Of the 517 records with a Commons plan, two are of these types (townhouse: Plas Mawr, 1576; Argyll's Lodging, 1632:
neither Georgian); none are cottages, inns or terraces. So the catalogue cannot test these four types; the sources
above do. building-gen's own `example_floorplans/georgian/` has eight plans with no source or licence recorded.

## What a type must pass before it is shown (BT6d)
1. Footprint, number of rooms deep and stair position as the sourced plan of the type.
2. Walls, roof and windows in the materials and forms of the type's period and region (no one style for all).
3. Fittings of the period only, or none.
4. Chimneys, roofs and stairs inside the building envelope; roof drawn on the walls.
5. A note of the sources it follows, shown with it, and the label "an illustration, not a record".
