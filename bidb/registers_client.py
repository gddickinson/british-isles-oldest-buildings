"""Paged readers for official heritage-register services (ArcGIS REST and OGC WFS).

All results are cached on disk by bidb.http; geometries are reduced to one WGS84 point
(the centre of the feature's bounding box, or the server's centroid where offered).
"""
from .http import request_json


def _centre(geom):
    """One (lat, lon) from an Esri JSON or GeoJSON geometry."""
    if not geom:
        return None, None
    if "x" in geom and "y" in geom:
        return geom["y"], geom["x"]
    coords = geom.get("points") or geom.get("rings") or geom.get("paths") or geom.get("coordinates")
    xs, ys = [], []

    def walk(c):
        if c and isinstance(c[0], (int, float)):
            xs.append(c[0])
            ys.append(c[1])
        else:
            for sub in c or []:
                walk(sub)
    walk(coords)
    if not xs:
        return None, None
    return (min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2


def arcgis(layer_url, fields, where="1=1", paging="offset", page=2000, polygons=False,
           fid_field="FID", max_records=None):
    """[(attributes, lat, lon)] for every feature matching `where`.

    paging="offset" uses resultOffset (ArcGIS Online); paging="fid" walks FID ranges (servers
    that do not support pagination, e.g. HES).
    """
    out, start = [], 0
    while True:
        params = {"where": where, "outFields": fields, "outSR": 4326, "f": "json"}
        if paging == "offset":
            params.update(resultOffset=start, resultRecordCount=page, orderByFields=fid_field)
        else:
            params["where"] = f"({where}) AND {fid_field} >= {start} AND {fid_field} < {start + page}"
        if polygons and paging == "offset":
            params.update(returnGeometry="false", returnCentroid="true")
        elif polygons:
            params.update(maxAllowableOffset=0.002, geometryPrecision=5)
        res = request_json(f"{layer_url}/query", params=params, min_interval=1.1)
        if "error" in res:
            raise RuntimeError(f"{layer_url}: {res['error']}")
        feats = res.get("features", [])
        for f in feats:
            lat, lon = _centre(f.get("centroid") or f.get("geometry"))
            out.append((f.get("attributes", {}), lat, lon))
        if max_records and len(out) >= max_records:
            return out[:max_records]
        if paging == "offset":
            if not feats or not res.get("exceededTransferLimit") and len(feats) < page:
                return out
            start += len(feats)
        else:
            if not feats and start > _max_fid(layer_url, where, fid_field):
                return out
            start += page


_MAX_FID = {}


def _max_fid(layer_url, where, fid_field):
    key = (layer_url, where)
    if key not in _MAX_FID:
        res = request_json(f"{layer_url}/query", params={
            "where": where, "returnIdsOnly": "true", "f": "json"}, min_interval=1.1)
        ids = res.get("objectIds") or [0]
        _MAX_FID[key] = max(ids)
    return _MAX_FID[key]


def wfs(base_url, type_name, page=1000):
    """[(properties, lat, lon)] for a WFS 2.0 feature type, as GeoJSON in EPSG:4326."""
    out, start = [], 0
    while True:
        res = request_json(base_url, params={
            "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": type_name,
            "outputFormat": "application/json", "srsName": "EPSG:4326", "count": page,
            "startIndex": start, "sortBy": None}, min_interval=1.1)
        feats = res.get("features", [])
        for f in feats:
            lat, lon = _centre(f.get("geometry"))
            out.append((f.get("properties", {}), lat, lon))
        if len(feats) < page:
            return out
        start += page
