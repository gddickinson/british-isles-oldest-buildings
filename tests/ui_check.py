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
    "innovations": ("/oldest", r"(?s)Innovations and firsts made in the isles.*Coke-fired blast furnace.*Dolly the sheep"),
    "law_events": ("/change", r"(?s)Statute of Labourers.*Bubble Act.*Slavery abolished; slave owners compensated.*Big Bang"),
    "types": ("/types", r"(?s)Building types.*Family tree.*Domestic.*Wealden house"),
    "type_page": ("/types?t=wealden-house", r"(?s)Wealden house.*A medieval house with central open hall.*A form of.*Hall house.*Earliest surviving example"),
    "types_time": ("/types?tab=time&year=1300", r"(?s)Types in use.*types in use in 1300.*Motte and bailey.*Materials and techniques by century.*Rubble masonry"),
    "type_chains": ("/types?t=motte-and-bailey", r"(?s)What came before and what came next.*Ringfort.*Concentric castle.*Spread across the isles.*counties"),
    "material_page": ("/types?m=brick", r"(?s)Brick.*Main types of its records.*Revival of.*Roman brick and tile"),
    "material_stone": ("/types?m=limestone", r"(?s)Limestone.*Sedimentary rock consisting mainly of calcium carbonate.*Bath stone.*West Kennet Long Barrow"),
    "type_bridge": ("/types?t=transporter-bridge", r"(?s)Transporter bridge.*A form of.*Bridge.*Earliest surviving example.*Newport Transporter Bridge"),
    "material_bedrock": ("/types?m=bath-stone", r"(?s)Bath stone.*Limestone and dolostone \(Jurassic\).*mapped examples \(\d+%\) stand on it"),
    "material_ireland": ("/types?m=granite", r"(?s)Granite.*Granite and other felsic intrusions.*mapped examples \(\d+%\) stand on it.*1:500,000 \(Ireland\)"),
    "material_abroad": ("/types?m=caen-stone", r"(?s)Caen stone.*Quarried outside the isles"),
    "types_here": ("/building/Q17530628", r"(?s)Building type and materials.*Wealden house.*see its family"),
    "trades": ("/trades?t=sugar", r"(?s)Trades and industries.*Sugar and slavery.*Timeline.*Slave Trade Act.*What historians say.*Capitalism and Slavery"),
    "things": ("/things", r"(?s)Oldest things.*Food and drink.*Oldest recipe or cookery book.*sources?"),
    "things_search": ("/things?q=harp&sort=year", r"(?s)Oldest things.*[Hh]arp"),
    "glossary": ("/glossary?q=wealden", r"(?s)Glossary.*Wealden house.*FISH Thesaurus"),
    "glossary_see": ("/glossary#term-grade-ii", r"(?s)Grade II\*.*Listed building"),
    "trades_change": ("/change", r"(?s)Trade stories:.*Sugar and slavery.*Tea story"),
    "trade_here": ("/building/Q2566525", r"(?s)Trade and industry here.*Cromford Mill, the first water-powered.*story of.*cotton"),
    "trade_map": ("/map?trade=coal", r"(?s)Trade.*places and buildings of the trade, ringed.*The story of coal"),
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
    "change_trade_goods": ("/change", r"(?s)Textile exports, 1846-1938.*Coal, iron and machinery exports, 1846-1938.*Main exports, share of all UK exports"),
    "change_trade_imports": ("/change", r"(?s)Food imports, 1854-1938.*Raw material imports, 1854-1938.*Main imports, share of all imports"),
    "change_trade_atlas": ("/change", r"(?s)Main exports by SITC division, share of all UK exports, 1962-2024.*Bustos-Yildirim.*Main imports by SITC division, share of all UK imports, 1962-2024"),
    "change_work": ("/change", r"(?s)Working in farming, fishing and mining.*1926-2022.*Keibek.*Charles Booth.*1881-1911 from the 1911 census tables.*Working in making and building.*Working in services"),
    "change_work_nations": ("/change", r"(?s)Work by sector: Scotland, 1841-1911.*Booth.*From 1891 the censuses.*Work by sector: Ireland, 1841-2022.*four province volumes.*From 1926 the state"),
    "change_trade_joined": ("/change", r"(?s)Main exports, share of all UK exports, 1846-2024.*Breaks in definition.*1975: From 1975 the Growth Lab.*Main imports, share of all UK imports, 1854-2024"),
    "change_trade_sitc": ("/change", r"(?s)Textile exports by division, 1953-1974.*Standard International Trade Classification.*Coal, iron and machinery exports by division, 1953-1974.*Main imports by division, share of all imports, 1953-1974.*Overseas trade at the prices of the time, 1953-1974"),
    "change_trade_groups": ("/change", r"(?s)Textile exports by group, 1938-1952.*Annual Abstract of Statistics.*Coal, iron and machinery exports by group, 1938-1952.*Main imports by group, share of all imports, 1938-1952.*Overseas trade at the prices of the time, 1938-1952"),
    "change_trade_hmrc": ("/change", r"(?s)Textile exports, 2000-20\d\d.*Overseas Trade Statistics.*Coal, iron and machinery exports, 2000-20.*Main imports, share of all imports, 2000-20.*Raw cotton and wool imported by weight, 2000-20"),
    "change_trade_quantities": ("/change", r"(?s)Food imports by weight, 1854-1938.*Raw cotton and wool imported by weight, 1854-1938.*Timber imported, 1857-1934.*Sawn softwood and pit props.*Food import prices, 1854-1938.*Raw material import prices, 1854-1938"),
    "change_tea": ("/change", r"(?s)Tea retained for home consumption.*432 million in 1938.*Tea drunk per person.*Ministry of Food.*Family Food.*Price of imported tea.*16.1d. in 1919.*Wholesale price of tea.*19.44d. in 1938.*Duty on tea.*Imperial Preference.*Commutation Act cuts the tea duty.*Tea rationed"),
    "places_institutions": ("/places?kind_group=Public+institutions", r"data-place="),
    "quiz_menu": ("/quiz", r"Say the name"),
    "quiz_story": ("/quiz?q=story", r"▇▇▇"),
    "quiz_order": ("/quiz?q=order", r"quiz-rank"),
    "quiz_first": ("/quiz?q=first", r"(?s)Which came first\?.*Innovation|Law or institution"),
    "quiz_typefirst": ("/quiz?q=typefirst", r"(?s)Which kind of building was built first"),
    "quiz_things": ("/quiz?q=things", r"(?s)Oldest things.*Which is .*quiz-choices"),
    "quiz_material": ("/quiz?q=material", r"(?s)quiz-photo.*built of or with\?"),
    "quiz_nametype": ("/quiz?q=nametype", r"(?s)quiz-photo.*What kind of building is this\?"),
    "help_types": ("/help", r"id=\"types\""),
    "places_nature": ("/places?kind_group=Nature+%26+deep+time", r"data-place="),
    "settings_share": ("/settings", r"Only this computer can open the app"),
    "building_domesday": ("/building/Q17529018", r"recorded in Domesday Book with 2 churches and a priest"),
    "people": ("/people", r'data-person=|class="person'),
    "pronunciation": ("/pronunciation?q=ll", r'class="ipa"|class="respell"'),
    "stories": ("/stories", r'class="story story-'),
    "tours": ("/tours", r'class="tour-card'),
    "tour_detail": ("/tours?mode=walk", r'class="tour-stops"'),
    "tour_trade": ("/tours?theme=trade", r"(?s)tour-card.*Markets &(amp;)? trade of"),
    "tour_warning": ("/tours", r"(?s)Computer-made suggestions, not tested routes.*Before you go"),
    "help_accuracy": ("/help#accuracy", r"(?s)Accuracy and safety.*generated automatically and may be wrong.*Use the tours with care"),
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
