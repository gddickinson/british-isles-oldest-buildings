"""British Isles oldest-buildings database builder.

Modules:
    config               paths, cutoff year, endpoints, user agent
    http                 polite cached HTTP client (retries, rate limit, disk cache)
    dates                Wikidata time values -> year / display text
    wikidata             candidate discovery (SPARQL) and entity details (wbgetentities)
    wikipedia_list       parser for Wikipedia's curated oldest-buildings lists (UK, Scotland)
    enrich               Wikipedia summaries and postcodes.io addresses
    classify             category, period, nation and heritage-grade classification
    db                   SQLite schema, writes and read queries used by the GUI
    build                command-line pipeline that ties the stages together
"""
