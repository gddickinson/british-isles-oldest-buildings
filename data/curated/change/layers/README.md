# Inputs of the "Change over time" map layers

Small, simplified copies of published data, made once by the research step and kept here so the layers can be
rebuilt without downloading gigabytes again. Built into `app/static/data/change/` by `bidb.change_geology`,
`bidb.change_layers` (HYDE, read from its archive directly) and `bidb.change_rasters`. Sources, licences and
credits: `DATA_LICENSE.md` (Change over time).

| File | What | Made from |
|---|---|---|
| `bgs625k_bedrock_period.geojson` | GB bedrock dissolved by period, simplified 400 m | BGS Geology 625k V5 (OGL) |
| `gsi500k_bedrock_age.geojson` | All-Ireland bedrock by age bracket, simplified 300 m | GSI/GSNI 1:500k (CC BY 4.0 / OGL) |
| `coal_authority_coalfield_areas.geojson` | Coalfield consultation areas, simplified 200 m | Coal Authority (OGL) |
| `ghsl_built_{1975,2020}.json.gz` | % of each 1/60° cell under buildings | GHS-BUILT-S R2023A 30″ grids, cropped remotely, summed to 1/60° |
| `corine_{2000,2006,2012,2018}.json.gz` | Land cover in 9 groups of the 44 CORINE classes (0 = sea / none) | EEA CORINE map service images (lon −11..2, lat 49..61, Web Mercator), colour → class → group |
| `ancient_woodland.json.gz` | % of each 1/60° cell that is ancient woodland | AWI England (all), Wales 2021 (all but deleted), Scotland (classes 1a and 2a, "Ancient (of semi-natural origin)"), burned at 1/1200° and averaged |
| `alc_grades.json.gz` | Majority provisional ALC grade per 1/60° cell (1–5, 6 non-agricultural, 7 urban) | Natural England provisional ALC (OGL) |
| `superficial.json.gz` | Majority superficial deposit class per 1/60° cell (see `bidb.change_rasters.SUPERFICIAL`) | BGS Geology 625k superficial polygons |
| `pollen_tree_cells.geojson` | Tree cover % per 1° cell and pollen time window | LandClimII REVEALS (CC BY 4.0) |
| `buringh_cities.csv` | Population (thousands) of 192 places, 700–2000, with estimate type | Buringh 2020 (CC0); rows with 0 left out |

Grids are `{per_deg, lon0, lat1, rows}`, rows north → south from 61°N, columns east from 11°W.
`prepare_rasters.py` records how the gzipped grids were made (GDAL command-line tools, numpy and Pillow; set
`CHANGE_RESEARCH` to the folder with the downloads and `GDAL_BIN` to the GDAL tools).
