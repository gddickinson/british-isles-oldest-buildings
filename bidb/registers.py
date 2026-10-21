"""Official heritage registers -> place records.

England (Historic England NHLE), Scotland (HES), Wales (Cadw), Northern Ireland (DfC HED) and
Ireland (National Monuments Service SMR, NIAH). Endpoints tested 2026-10-19; see INTERFACE.md.
Each record keeps the register's own name, reference, period text (where the register has
one) and a link to the official record.
"""
import re

from .place_records import blank
from .registers_client import arcgis, wfs

HE = ("https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/"
      "National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer")
HES = "https://inspire.hes.scot/arcgis/rest/services/HES/HES_Designations/MapServer"
CADW = "https://datamap.gov.wales/geoserver/ows"
NI = ("https://services2.arcgis.com/BdBkthNLO9mzGAMO/arcgis/rest/services/"
      "Historic_Environment_Division_GIS_Data/FeatureServer")
IE = "https://services-eu1.arcgis.com/HyjXgkV6KGMSF3jt/arcgis/rest/services"

ATTRIBUTION = {
    "Historic England": "© Historic England 2026. Contains Ordnance Survey data © Crown copyright "
                        "and database right 2026. Released under the Open Government Licence.",
    "Historic Environment Scotland": "Contains Historic Environment Scotland and Ordnance Survey "
                                     "data © Historic Environment Scotland © Crown copyright and "
                                     "database right 2026 (Open Government Licence).",
    "Cadw": "Designated Historic Asset GIS Data, The Welsh Historic Environment Service (Cadw), "
            "2026, licensed under the Open Government Licence v3.0.",
    "DfC Historic Environment Division": "Contains public sector information licensed under the "
                                         "Open Government Licence v3.0 - Department for "
                                         "Communities Historic Environment Division.",
    "National Monuments Service": "Archaeological Survey of Ireland, National Monuments Service, "
                                  "Department of Housing, Local Government and Heritage (CC BY 4.0).",
    "Open Plaques": "Open Plaques (openplaques.org), public domain.",
    "NIAH": "National Inventory of Architectural Heritage, Department of Housing, Local "
            "Government and Heritage (CC BY 4.0).",
}

# Irish SMR classes kept (prefix match); ringforts, enclosures and fulachtaí fia are left out
IE_SMR_CLASSES = ["Church", "Castle", "Megalithic tomb", "Stone circle", "Stone row", "Ogham stone",
                  "Cross - High cross", "Ecclesiastical enclosure", "Ecclesiastical site",
                  "Round tower", "Religious house", "Ritual site - holy well", "Hillfort",
                  "Promontory fort", "Crannog", "Rock art", "Clochan", "Battlefield", "Cathedral",
                  "Friary", "Abbey", "Priory", "Tower house", "Bawn", "Wedge tomb"]

_PERIOD_YEARS = [  # (pattern in lower-case period text, representative year)
    (r"mesolithic", -6000), (r"neolithic", -3000), (r"bronze age", -1500), (r"iron age", -400),
    (r"prehistoric", -2000), (r"roman", 200), (r"early medieval|early christian|pictish", 800),
    (r"post[- ]medieval", 1650), (r"medieval", 1250), (r"\bc(\d{1,2})(?:th|st|nd|rd)\b", None),
    (r"18th|19th|georgian|victorian|industrial", 1800), (r"modern|20th", 1900),
]


def period_year(text):
    """Representative start year for a register period such as 'Bronze Age' or 'C12TH'."""
    for part in re.split(r"[;,/]", (text or "").lower()):     # the first listed period wins
        for pattern, year in _PERIOD_YEARS:
            m = re.search(pattern, part)
            if m:
                return (int(m.group(1)) - 1) * 100 + 50 if year is None else year
    return None


def _title(s):
    s = re.sub(r"\s+", " ", (s or "").strip())
    letters = [c for c in s if c.isalpha()]
    mostly_upper = letters and sum(c.isupper() for c in letters) > 0.7 * len(letters)
    return s.title() if mostly_upper else s


def _rec(pid, kind, name, lat, lon, source, nation, period=None, **kw):
    year = period_year(period)
    return blank(pid, kind, _title(name) or pid, lat=lat, lon=lon, source=source, nation=nation,
                 year_start=year, date_text=f"{_title(period)} (register period)" if period else "",
                 **kw)


def england(log=print):
    out = []
    layers = [(6, "scheduled", "Scheduled monument"), (7, "park_garden", "Registered park and garden"),
              (8, "battle", "Registered battlefield"), (9, "shipwreck", "Protected wreck")]
    for layer, kind, desig in layers:
        fields = "ListEntry,Name,hyperlink" + (",Grade" if kind == "park_garden" else "")
        rows = arcgis(f"{HE}/{layer}", fields, polygons=True,
                      fid_field="OBJECTID")
        for a, lat, lon in rows:
            grade = f" (Grade {a['Grade']})" if a.get("Grade") else ""
            out.append(_rec(f"nhle-{a['ListEntry']}", kind, a.get("Name"), lat, lon, "Historic England",
                            "England", designation=desig + grade, url=a.get("hyperlink"),
                            type=desig, extra_ref=f"NHLE {a['ListEntry']}"))
        log(f"  Historic England layer {layer}: {len(rows)}")
    return out


def scotland(log=print):
    out = []
    layers = [(5, "scheduled", "Scheduled monument"), (4, "park_garden", "Inventory garden and designed landscape"),
              (3, "battle", "Inventory battlefield")]
    for layer, kind, desig in layers:
        fields = "DES_REF,DES_TITLE,LOCAL_AUTH,LINK" + (",CATEGORY,PARISH" if layer == 5 else "")
        rows = arcgis(f"{HES}/{layer}", fields,
                      paging="fid", page=2000, polygons=True)
        for a, lat, lon in rows:
            cat = a.get("CATEGORY") if layer == 5 else None
            period = cat.split(":")[0] if cat else None
            out.append(_rec(f"hes-{a['DES_REF']}", kind, a.get("DES_TITLE"), lat, lon,
                            "Historic Environment Scotland", "Scotland",
                            period if period and period_year(period) else None,
                            designation=desig, url=a.get("LINK"), type=(cat.split(":", 1)[-1].strip() if cat else desig),
                            locality=", ".join(x for x in (a.get("PARISH"), a.get("LOCAL_AUTH")) if x),
                            extra_ref=a["DES_REF"]))
        log(f"  HES layer {layer}: {len(rows)}")
    return out


def wales(log=print):
    out = []
    for props, lat, lon in wfs(CADW, "inspire-wg:Cadw_SAM"):
        ref = (props.get("SAMNumber") or "").strip()
        out.append(_rec(f"cadw-{ref}", "scheduled", props.get("Name"), lat, lon, "Cadw", "Wales",
                        (props.get("Period") or "").strip() or None, designation="Scheduled monument",
                        type=(props.get("SiteType") or "").strip() or "Scheduled monument",
                        url=props.get("Report"), extra_ref=ref,
                        locality=", ".join(x.strip() for x in (props.get("Community"), props.get("UnitaryAuthority")) if x)))
    n = len(out)
    for props, lat, lon in wfs(CADW, "geonode:cadw_rhpg_registeredareas"):
        ref = props.get("reference_number")
        phase = props.get("main_phase_en")
        out.append(_rec(f"cadw-{ref}", "park_garden", props.get("site_name_en"), lat, lon, "Cadw",
                        "Wales", designation=f"Registered historic park and garden (Grade {props.get('grade_gradd')})",
                        type=props.get("site_type_en"), url=props.get("report_en"), extra_ref=ref,
                        description=f"Main phases: {phase}" if phase else None,
                        locality=props.get("la_en")))
    for props, lat, lon in wfs(CADW, "inspire-wg:Cadw_DesignatedWrecks"):
        name = props.get("Name") or props.get("name") or props.get("SiteName")
        ref = props.get("WreckNumber") or props.get("RecordNumber") or name
        out.append(_rec(f"cadw-wreck-{ref}", "shipwreck", name, lat, lon, "Cadw", "Wales",
                        designation="Designated wreck", extra_ref=str(ref)))
    log(f"  Cadw: {n} scheduled monuments, {len(out) - n} parks and wrecks")
    return out


def northern_ireland(log=print):
    out = []
    rows = arcgis(f"{NI}/0", "SMRNo,Townland_s_,Edited_Type,General_Type,General_Period,Protection,Council",
                  where="Protection IS NOT NULL AND Protection <> ''", fid_field="OBJECTID")
    for a, lat, lon in rows:
        name = (a.get("Edited_Type") or "").split(":", 1)
        title = name[1].strip() if len(name) > 1 else f"{_title(name[0])}, {_title(a.get('Townland_s_'))}"
        out.append(_rec(f"nismr-{a['SMRNo']}", "scheduled", title, lat, lon,
                        "DfC Historic Environment Division", "Northern Ireland",
                        a.get("General_Period") if period_year(a.get("General_Period")) else None,
                        designation=a.get("Protection"), type=_title(a.get("General_Type")),
                        locality=", ".join(_title(x) for x in (a.get("Townland_s_"), a.get("Council")) if x),
                        extra_ref=a["SMRNo"]))
    for a, lat, lon in arcgis(f"{NI}/8", "BATTLE,DDMMYY,CENTURY,TYPE,OUTCOME,MAIN_REF", polygons=True,
                              fid_field="OBJECTID"):
        out.append(_rec(f"nibat-{a.get('MAIN_REF') or a.get('BATTLE')}", "battle", a.get("BATTLE"), lat, lon,
                        "DfC Historic Environment Division", "Northern Ireland",
                        f"C{a['CENTURY']}TH" if str(a.get("CENTURY") or "").isdigit() else None,
                        designation="Battlesite record", type=_title(a.get("TYPE")) or "Battle",
                        description=_title(a.get("OUTCOME")) or None, extra_ref=a.get("MAIN_REF")))
    for a, lat, lon in arcgis(f"{NI}/9", "REF_NO,SITE,STATUS,COUNCIL,Grade", polygons=True,
                              fid_field="OBJECTID"):
        out.append(_rec(f"nipg-{a['REF_NO']}", "park_garden", a.get("SITE"), lat, lon,
                        "DfC Historic Environment Division", "Northern Ireland",
                        designation=f"Historic park, garden and demesne ({_title(a.get('STATUS'))})",
                        locality=_title(a.get("COUNCIL")), extra_ref=a.get("REF_NO")))
    log(f"  Northern Ireland: {len(rows)} protected monuments, {len(out) - len(rows)} battles and parks")
    return out


def ireland(log=print):
    where = " OR ".join(f"MONUMENT_CLASS LIKE '{c}%'" for c in IE_SMR_CLASSES)
    rows = arcgis(f"{IE}/SMROpenData/FeatureServer/0",
                  "SMRS,COUNTY,TOWNLAND,MONUMENT_CLASS,WEBSITE_LINK,WEB_NOTES,LATITUDE,LONGITUDE",
                  where=where, fid_field="OBJECTID")
    out = []
    for a, lat, lon in rows:
        cls = a.get("MONUMENT_CLASS") or "Monument"
        kind = "battle" if cls.startswith("Battlefield") else "scheduled"
        notes = re.sub(r"\s+", " ", a.get("WEB_NOTES") or "").strip()
        out.append(_rec(f"iesmr-{a['SMRS']}", kind, f"{cls}, {_title(a.get('TOWNLAND'))}",
                        a.get("LATITUDE") or lat, a.get("LONGITUDE") or lon,
                        "National Monuments Service", "Republic of Ireland",
                        designation="Record of Monuments and Places", type=cls,
                        locality=f"{_title(a.get('TOWNLAND'))}, County {_title(a.get('COUNTY'))}",
                        county=f"County {_title(a.get('COUNTY'))}",
                        description=(notes[:600] + " …") if len(notes) > 600 else notes or None,
                        url=a.get("WEBSITE_LINK"), extra_ref=a["SMRS"]))
    log(f"  Ireland SMR (selected classes): {len(out)}")
    return out


def niah_early(before=1500):
    """NIAH buildings dated before `before`: raw attribute dicts for the building catalogue."""
    rows = arcgis(f"{IE}/NIAHBuildingsOpenData/FeatureServer/0",
                  "REG_NO,NAME,ORIGINAL_TYPE,TOWN,TOWNLAND,COUNTY,DESCRIPTION,APPRAISAL,DATEFROM,"
                  "DATETO,RATING,WEBSITE_LINK,LATITUDE,LONGITUDE",
                  where=f"DATEFROM < {before}", fid_field="OBJECTID_1")
    return [a for a, _, _ in rows]


ALL = [england, scotland, wales, northern_ireland, ireland]
