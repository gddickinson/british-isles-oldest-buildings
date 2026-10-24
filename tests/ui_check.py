"""Browser checks of every page in headless Chrome (slow, so not part of unittest discover):

    .venv/bin/python -m tests.ui_check            all pages, temporary server
    .venv/bin/python -m tests.ui_check --base http://127.0.0.1:5050 --only tours stories

Each page must load without JavaScript errors and show what it is for (a pattern in the final
DOM). Exits 1 if any check fails.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from app.screenshot import find_chrome, temporary_server

# name: (path, pattern that must be in the rendered page)
PAGES = {
    "catalogue": ("/", r'class="card'),
    "catalogue_story_filter": ("/?story=supernatural", r'<b id="total">\d'),
    "building": ("/building/Q1529151", r'class="story story-'),
    "building_timeline": ("/building/Q816295", r'class="tl-year"'),
    "map": ("/map", r'leaflet-container'),
    "places": ("/places", r'data-place='),
    "places_underground": ("/places?kind_group=Underground", r'data-place='),
    "places_military": ("/places?kind_group=Military+heritage", r'data-place='),
    "museum_place": ("/places#Q2086562", r'Kept here'),
    "museum_building": ("/building/Q6373", r'Notable objects here'),
    "places_bridges": ("/places?kind_group=Bridges", r'data-place='),
    "building_then": ("/building/Q1025398", r'Then: paintings'),
    "places_excavations": ("/places?kind_group=Excavations", r'data-place='),
    "building_evidence": ("/building/Q441079", r'Catalogue value confirmed'),
    "data_evidence": ("/data", r'Catalogue corrected'),
    "building_dendro": ("/building/Q17741395", r"Tree-ring dated:</b> 1418/19"),
    "oldest_nature": ("/oldest", r"(?s)Oldest in nature.*Fortingall Yew"),
    "places_graves": ("/places?kind_group=Graves+%26+burial+grounds", r"data-place="),
    "places_sport": ("/places?kind_group=Sport+%26+leisure", r"data-place="),
    "oldest_sport": ("/oldest", r"(?s)Oldest sporting grounds and clubs.*Sheffield"),
    "oldest_civic": ("/oldest", r"(?s)Oldest schools, hospitals and public services.*St Peter"),
    "oldest_tea": ("/oldest", r"(?s)The tea trade: merchants, firms.*Horniman.*Garraway"),
    "oldest_guilds": ("/oldest", r"(?s)Guilds, companies, exchanges and banks.*Worshipful Company of Weavers.*Merchants of the Staple.*Jamaica Wine House"),
    "places_tea": ("/places?kind_label=Tea+merchant+or+firm", r"(?s)data-place=.*Horniman"),
    "places_livery": ("/places?kind_label=Livery+company+or+guild", r"(?s)data-place=.*Worshipful Company"),
    "places_livery_people": ("/places?kind_label=Livery+company+or+guild#Q8037025", r"(?s)Master, governor or officer.*Member"),
    "people_officers": ("/people?role=Master%2C+governor+or+officer", r"(?s)Master, governor or officer: Bank of England"),
    "places_guildhalls": ("/places?kind_label=Guildhall%2C+livery+or+merchants%27+hall", r"(?s)data-place=.*Hall"),
    "change_firms": ("/change", r"(?s)Firms founded per decade.*Of these, closed.*Making things.*Banks, finance and insurance.*Publishing, print and media.*Wikidata \(firms\)"),
    "change_registers": ("/change", r"(?s)Companies incorporated per year.*still on the register.*Companies on the register.*Effective register.*Companies registered per year: Ireland.*Contains Irish Public Sector Data.*Companies alive today by decade founded: making.*Companies alive today by decade founded: publishing"),
    "change_patents": ("/change", r"(?s)Patents granted per year.*Woodcroft.*European patents for the UK.*Patent applications published per year.*Patents Act 1977"),
    "change_trade": ("/change", r"(?s)Overseas trade, 1800-1938.*Federico and Tena-Junguito.*Overseas trade since 1948.*Goods exported, share of the economy.*Overseas trade: Ireland"),
    "change_trade_values": ("/change", r"(?s)Overseas trade at the prices of the time, 1854-1938.*Statistical Abstracts.*Re-exports, share of all exports"),
    "change_trade_goods": ("/change", r"(?s)Textile exports, 1854-1938.*Coal, iron and machinery exports, 1854-1938.*Main exports, share of all UK exports"),
    "change_trade_imports": ("/change", r"(?s)Food imports, 1854-1938.*Raw material imports, 1854-1938.*Main imports, share of all imports"),
    "change_tea": ("/change", r"(?s)Tea retained for home consumption.*432 million in 1938.*Tea drunk per person.*Ministry of Food.*Family Food.*Price of imported tea.*16.1d. in 1919.*Duty on tea.*Imperial Preference.*Commutation Act cuts the tea duty.*Tea rationed"),
    "places_institutions": ("/places?kind_group=Public+institutions", r"data-place="),
    "quiz_menu": ("/quiz", r"Say the name"),
    "quiz_story": ("/quiz?q=story", r"▇▇▇"),
    "quiz_order": ("/quiz?q=order", r"quiz-rank"),
    "places_nature": ("/places?kind_group=Nature+%26+deep+time", r"data-place="),
    "settings_share": ("/settings", r"Only this computer can open the app"),
    "building_domesday": ("/building/Q17529018", r"recorded in Domesday Book with 2 churches and a priest"),
    "people": ("/people", r'data-person=|class="person'),
    "pronunciation": ("/pronunciation?q=ll", r'class="ipa"|class="respell"'),
    "stories": ("/stories", r'class="story story-'),
    "tours": ("/tours", r'class="tour-card'),
    "tour_detail": ("/tours?mode=walk", r'class="tour-stops"'),
    "tour_builder": ("/tours?tab=build", r'id="tb_list"'),
    "history": ("/history", r'class="otd-year"'),
    "quiz": ("/quiz?q=period", r'class="quiz-choices'),
    "oldest": ("/oldest", r'class="ex"'),
    "stats": ("/stats", r'<svg'),
    "compare": ("/compare", r'compare'),
    "data": ("/data", r'Data quality'),
    "settings": ("/settings", r'Data location'),
    "help": ("/help", r'id="tours"'),
}
JS_ERROR = re.compile(r"Uncaught|CONSOLE\(\d+\)\] \"(?:Error|TypeError|ReferenceError|SyntaxError)", re.I)


def check(base, name, path, pattern, chrome):
    with tempfile.TemporaryDirectory() as profile:
        proc = subprocess.run([chrome, "--headless=new", "--disable-gpu", f"--user-data-dir={profile}",
                               "--virtual-time-budget=20000", "--enable-logging=stderr", "--v=0", "--dump-dom",
                               base + path], capture_output=True, text=True, timeout=120)
    errors = [l for l in proc.stderr.splitlines() if JS_ERROR.search(l)]
    found = re.search(pattern, proc.stdout) is not None
    return found and not errors, errors[:3], found


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", help="use a running server")
    ap.add_argument("--only", nargs="*", help="page names to check")
    a = ap.parse_args()
    chrome = find_chrome()
    if not chrome:
        sys.exit("No Chrome/Chromium found (Settings → Screenshots sets the path)")
    names = a.only or list(PAGES)

    def run(base):
        bad = 0
        for name in names:
            path, pattern = PAGES[name]
            ok, errors, found = check(base, name, path, pattern, chrome)
            bad += not ok
            print(f"{'ok  ' if ok else 'FAIL'} {name:24} {path}" + ("" if found else "  (expected content missing)"))
            for e in errors:
                print("       ", e[-200:])
        print(f"{len(names) - bad}/{len(names)} pages passed")
        return bad

    if a.base:
        bad = run(a.base)
    else:
        with temporary_server() as base:
            bad = run(base)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
