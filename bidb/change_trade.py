"""Overseas trade for "Change over time" (roadmap C5b1), from open data only.

- Federico-Tena World Trade Historical Database (CC BY 4.0): imports and exports of the United Kingdom 1800-1938 and
  of the Irish Free State 1922-1938, in million dollars at 1913 prices (current boundaries: the UK's figures include
  all of Ireland to 1922).
- ONS UK Economic Accounts (OGL): exports and imports of goods and services 1948-2025 in chained volume measures
  (IKBK, IKBL), goods exports at current prices (BOKG) and GDP at current prices (YBHA) for the share of the economy.
- CSO TSA01 (CC BY 4.0): Ireland's merchandise imports and exports 1930-2025 in euro (current prices).
- CEPII TRADHIST via Our World in Data (Etalab 2.0 / CC BY): merchandise exports as a share of GDP, UK 1827-2014,
  Ireland 1926-2014.

The two UK eras are not joined: the dollar figures at 1913 prices and the ONS's pounds at the prices of its
reference year are different measures, and 1939-47 has neither.

    python -m bidb.change_trade   → data/curated/change/data/trade_*.csv + series.json entries
                                    (then python -m bidb.change_series)
"""
import csv
import json
import re
import sys
import time

from .change_firms import DATA
from .change_registers import _csv, _download, _row, xlsx_rows

FT_URLS = {"uk": "https://edatos.consorciomadrono.es/api/access/datafile/1778",
           "ireland": "https://edatos.consorciomadrono.es/api/access/datafile/1730"}
ONS_PATHS = {"ikbk": "economy/grossdomesticproductgdp", "ikbl": "economy/grossdomesticproductgdp",
             "ikbh": "economy/nationalaccounts/balanceofpayments", "bokg": "economy/nationalaccounts/balanceofpayments",
             "ybha": "economy/grossdomesticproductgdp"}
ONS_URL = "https://www.ons.gov.uk/generator?format=csv&uri=/{path}/timeseries/{cdid}/ukea"
CSO_URL = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/TSA01/CSV/1.0/en"
OWID_URL = "https://ourworldindata.org/grapher/merchandise-exports-gdp-cepii.csv"
IRISH_POUND = 0.787564                     # Irish pounds to the euro (CSO converts the years before 1999 at this rate)


def ft(path, sheet="Constant prices"):
    """{year: (imports, exports)} in million dollars from a Federico-Tena workbook, current boundaries (columns B, C)."""
    out = {}
    for r in xlsx_rows(path, sheet, "ABC"):
        if re.fullmatch(r"1[89]\d\d", r[0].strip()) and r[1].strip() and r[2].strip():
            out[int(r[0])] = (float(r[1]), float(r[2]))
    return out


def ons(path):
    """{year: value} from the yearly rows of an ONS time-series CSV ("1948","2246")."""
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.reader(f):
            if len(r) == 2 and re.fullmatch(r"\d{4}", r[0]) and r[1].strip():
                out[int(r[0])] = float(r[1])
    return out


def reference_year(cvm, cp):
    """The year a chained volume series is priced in: where it comes closest to the current-price series."""
    return min((y for y in cvm if y in cp), key=lambda y: abs(cvm[y] / cp[y] - 1))


def cso(path):
    """{year: (imports, exports)} in euro thousand from TSA01."""
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            kind = {"Total Imports": 0, "Total Exports": 1}.get(r["Statistic Label"])
            if kind is not None and r["VALUE"].strip():
                out.setdefault(int(r["Year"]), [None, None])[kind] = float(r["VALUE"])
    return {y: tuple(v) for y, v in out.items() if None not in v}


def owid(path, entity):
    """{year: value} for one entity of an Our World in Data grapher CSV."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {int(r["Year"]): float(r[list(r)[-1]]) for r in csv.DictReader(f) if r["Entity"] == entity}


def share(part, whole):
    """{year: part as a percentage of whole}."""
    return {y: round(part[y] / whole[y] * 100, 2) for y in sorted(part) if y in whole}


def _pts(d, i=None, scale=1, nd=1):
    return [(y, round((v if i is None else v[i]) * scale, nd)) for y, v in sorted(d.items())]


FT_NOTE = ("Imports and exports of goods in million US dollars at 1913 prices, so the line shows how much was traded, "
           "not what it was worth at the time, from Federico and Tena-Junguito's World Trade Historical Database "
           "(official trade statistics converted and deflated by the authors). The United Kingdom includes all of "
           "Ireland to 1922; from 1923 trade with the Irish Free State is foreign trade. At 1913 prices the UK imported {i1800:,.0f} million dollars of "
           "goods in 1800, {i1913:,.0f} million in 1913 and {i1938:,.0f} million in 1938; exports were {e1913:,.0f} "
           "million in 1913 and {e1938:,.0f} million in 1938, {fall}% below {peak}.")
FT_IE_NOTE = ("Imports and exports of goods of the Irish Free State (from 1937 Éire) in million US dollars at 1913 "
              "prices, from Federico and Tena-Junguito's World Trade Historical Database, on the same scale as the "
              "UK's 1800-1938 graph. Imports were {i0:,.0f} million in {y0} and {i1:,.0f} million in {y1}; exports "
              "{e0:,.0f} million and {e1:,.0f} million. The first two years are far below the third (imports {i2:,.0f} million "
              "in {y2}): the Free State was founded on 6 December 1922 and set up its customs frontier on 1 April "
              "1923, and the database's notes do not say how these years were filled. The CSO's own figures (graph \"Overseas trade: Ireland\") "
              "begin in 1930.")
ONS_NOTE = ("Exports and imports of goods and services by the United Kingdom, from the ONS national accounts, as chained "
            "volume measures in pounds at {ref} prices (series IKBK and IKBL): what was traded each year, priced as "
            "in {ref}. Exports were £{e0:,.0f} billion in {y0} and £{e1:,.0f} billion in {y1} at these prices. Not "
            "joined to the 1800-1938 graph: that is in dollars at 1913 prices, and no figures are drawn for 1939-47.")
SHARE_NOTE = ("Goods exported as a share of the economy (GDP at current prices). United Kingdom 1827-2014 and Ireland "
              "1926-2014 from CEPII's TRADHIST database (Fouquin and Hugot 2016) as published by Our World in Data; "
              "the second UK line is the ONS's exports of goods (BOKG) as a share of GDP (YBHA), 1948-{last}, "
              "{diff} percentage points from CEPII's on average where both run. Services, {services}% of the UK's "
              "exports in {last} (ONS IKBH less BOKG), are not counted.")
IE_NOTE = ("Ireland's (the state's) merchandise imports and exports, from the CSO's table TSA01, in million euro at the "
           "prices of each year (before 1999, Irish pounds converted at {rate} to the euro). Not joined to the "
           "Federico-Tena figures for 1922-38 (their own graph): over 1930-38, the years both cover, their "
           "dollar exports divided by the CSO's give between {usd[0]:.2f} and {usd[1]:.2f} dollars to the Irish pound, "
           "so the two differ in more than the exchange rate. Exports have been above imports every year since "
           "{cross}.")
SOURCES_FT = ["federico_tena_uk", "federico_tena_ireland"]


def write(ft_uk, ft_ie, cvm_x, cvm_m, ref, share_cepii_uk, share_ons, share_cepii_ie, cso_ie, usd, services,
          log=print):
    py = max(ft_uk, key=lambda y: ft_uk[y][1])
    peak = ft_uk[py][1]
    ie = {y: (m / 1000, x / 1000) for y, (m, x) in cso_ie.items()}
    cross = next(y for y in sorted(ie) if all(ie[z][1] > ie[z][0] for z in ie if z >= y))
    both = [y for y in share_ons if y in share_cepii_uk]
    diff = round(sum(abs(share_ons[y] - share_cepii_uk[y]) for y in both) / len(both), 1)
    files = {"trade_ft_imports_uk": _pts(ft_uk, 0), "trade_ft_exports_uk": _pts(ft_uk, 1),
             "trade_ft_imports_ie": _pts(ft_ie, 0), "trade_ft_exports_ie": _pts(ft_ie, 1),
             "trade_exports_uk": _pts(cvm_x, None, 1 / 1000), "trade_imports_uk": _pts(cvm_m, None, 1 / 1000),
             "trade_share_uk": _pts(share_cepii_uk, nd=2), "trade_share_ons_uk": _pts(share_ons, nd=2),
             "trade_share_ie": _pts(share_cepii_ie, nd=2),
             "trade_imports_ie": _pts(ie, 0), "trade_exports_ie": _pts(ie, 1)}
    for sid, pts in files.items():
        _csv(sid, pts)
    usd13 = "million $ at 1913 prices"
    f = {y: ft_uk[y] for y in (1800, 1913, 1938)}
    rows = [
        _row("trade_ft_imports_uk", "Overseas trade, 1800-1938 (at 1913 prices)", "Imports", usd13, SOURCES_FT[:1],
             "United Kingdom (all Ireland to 1922)",
             FT_NOTE.format(i1800=f[1800][0], i1913=f[1913][0], i1938=f[1938][0], e1913=f[1913][1], e1938=f[1938][1],
                            fall=round((1 - f[1938][1] / peak) * 100),
                            peak="their peak" if py == 1913 else f"their peak of {peak:,.0f} million in {py}"),
             ["trade_ft_exports_uk"], unit="$m"),
        _row("trade_ft_exports_uk", "UK exports", "Exports", usd13, SOURCES_FT[:1], "United Kingdom", unit="$m"),
        _row("trade_ft_imports_ie", "Overseas trade, 1922-1938 (at 1913 prices)", "Imports", usd13, SOURCES_FT[1:],
             "Irish Free State", FT_IE_NOTE.format(y0=min(ft_ie), y1=max(ft_ie), i0=ft_ie[min(ft_ie)][0],
                                                   i1=ft_ie[max(ft_ie)][0], e0=ft_ie[min(ft_ie)][1],
                                                   e1=ft_ie[max(ft_ie)][1], y2=min(ft_ie) + 2,
                                                   i2=ft_ie[min(ft_ie) + 2][0]), ["trade_ft_exports_ie"], unit="$m"),
        _row("trade_ft_exports_ie", "Irish Free State exports", "Exports", usd13, SOURCES_FT[1:],
             "Irish Free State", unit="$m"),
        _row("trade_exports_uk", "Overseas trade since 1948", "Exports (goods and services)", f"£ billion at {ref} prices",
             ["ons_trade_volumes"], "United Kingdom",
             ONS_NOTE.format(ref=ref, y0=min(cvm_x), e0=cvm_x[min(cvm_x)] / 1000, y1=max(cvm_x),
                             e1=cvm_x[max(cvm_x)] / 1000), ["trade_imports_uk"], unit="£bn"),
        _row("trade_imports_uk", "UK imports", "Imports (goods and services)", f"£ billion at {ref} prices",
             ["ons_trade_volumes"], "United Kingdom", unit="£bn"),
        _row("trade_share_uk", "Goods exported, share of the economy", "UK (CEPII)", "% of GDP",
             ["cepii_exports_gdp"], "United Kingdom; Ireland",
             SHARE_NOTE.format(last=max(share_ons), diff=diff, services=services), ["trade_share_ons_uk", "trade_share_ie"], unit="%"),
        _row("trade_share_ons_uk", "UK goods exports, share of GDP (ONS)", "UK (ONS)", "% of GDP",
             ["ons_trade_volumes"], "United Kingdom", unit="%"),
        _row("trade_share_ie", "Ireland goods exports, share of GDP", "Ireland (CEPII)", "% of GDP",
             ["cepii_exports_gdp"], "Ireland", unit="%"),
        _row("trade_exports_ie", "Overseas trade: Ireland", "Exports", "€ million (current prices)", ["cso_tsa01"],
             "Ireland (the state)", IE_NOTE.format(rate=IRISH_POUND, usd=usd, cross=cross), ["trade_imports_ie"],
             unit="€m"),
        _row("trade_imports_ie", "Ireland imports", "Imports", "€ million (current prices)", ["cso_tsa01"],
             "Ireland (the state)", unit="€m"),
    ]
    for r in rows:
        r["zero"] = True
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith("trade_")]
    path.write_text(json.dumps(keep + rows, ensure_ascii=False, indent=1))
    log(f"graphs: 5 ({len(rows)} series); CEPII and ONS shares differ by {diff} points on average; "
        f"Ireland's exports above imports from {cross}")


def _ons(cdid, log):
    name = f"trade_ons_{cdid}.csv"
    for attempt in range(4):                 # the ONS answers 429 to quick requests
        try:
            return ons(_download(ONS_URL.format(path=ONS_PATHS[cdid], cdid=cdid), name, log))
        except Exception as e:
            if "429" not in str(e) or attempt == 3:
                raise
            time.sleep(20)


def run(log=print):
    ft_uk = ft(_download(FT_URLS["uk"], "trade_ft_uk.xlsx", log))
    ft_ie = ft(_download(FT_URLS["ireland"], "trade_ft_ireland.xlsx", log))
    ft_ie_now = ft(_download(FT_URLS["ireland"], "trade_ft_ireland.xlsx", log), "Current prices")
    o = {c: _ons(c, log) for c in ONS_PATHS}
    ref = reference_year(o["ikbk"], o["ikbh"])
    cso_ie = cso(_download(CSO_URL, "trade_cso_tsa01.csv", log))
    cepii = _download(OWID_URL, "trade_owid_exports_gdp_cepii.csv", log)
    uk, ie = owid(cepii, "United Kingdom"), owid(cepii, "Ireland")
    whole = lambda d: {y: v for y, v in d.items() if y <= 2025}
    log(f"Federico-Tena UK {min(ft_uk)}-{max(ft_uk)}, Ireland {min(ft_ie)}-{max(ft_ie)}; ONS {min(o['ikbk'])}-"
        f"{max(o['ikbk'])} at {ref} prices; CSO {min(cso_ie)}-{max(cso_ie)}; CEPII UK {min(uk)}-{max(uk)}, "
        f"Ireland {min(ie)}-{max(ie)}")
    last = max(y for y in o["bokg"] if y <= 2025)
    rates = [ft_ie_now[y][1] / (cso_ie[y][1] / 1000 * IRISH_POUND) for y in range(1930, 1939)]
    for y, r in zip(range(1930, 1939), rates):
        log(f"  check {y}: Federico-Tena exports / CSO exports = {r:.2f} dollars to the Irish pound")
    write(ft_uk, ft_ie, whole(o["ikbk"]), whole(o["ikbl"]), ref, uk, share(whole(o["bokg"]), o["ybha"]), ie,
          cso_ie, (min(rates), max(rates)), round((1 - o["bokg"][last] / o["ikbh"][last]) * 100), log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
