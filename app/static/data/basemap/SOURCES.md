# Offline map data

Built by `python -m app.basemap_build` from:

- **Natural Earth** 10m (public domain): counties and council areas (admin-1), neighbouring
  countries, major roads, railways, lakes, mountain regions, airports.
- **GeoNames** (CC BY 4.0, geonames.org): cities, towns and villages; hills, ranges, forests, moors,
  glens, islands, lakes, bays and headlands.
- **OpenStreetMap** (© OpenStreetMap contributors, ODbL 1.0): named rivers and canals; national
  parks, AONBs / National Landscapes and National Scenic Areas; national walking routes; railway and bus
  stations (`stations.json`); minor (secondary and tertiary) roads and named streams (`minor/`, `streams/`, built by
  `python -m app.basemap_tiled`). `rivers.json`, `parks.json`, `trails.json`, `minor/` and `streams/` are derived from OpenStreetMap and are available
  under the Open Database Licence.

- **Historic County Borders Project** (county-borders.co.uk; free for any use with
  acknowledgement): this project made use of data provided by the Historic County Borders Project
  (`historic_counties.json`, pre-1974 counties, definition A).

Geometries are simplified for display; they are not survey-accurate.
