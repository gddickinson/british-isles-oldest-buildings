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
    "type_diagram": ("/types?t=wealden-house", r"(?s)Diagrams.*Wealden house: ground plan.*cross passage.*Drawn from.*four bays"),
    "type_place_plans": ("/types?t=polygonal-fort", r"(?s)Plans of real examples.*among the places.*Fort Gomer"),
    "type_diagram_prison": ("/types?t=separate-system-prison", r"(?s)Diagrams.*Separate system prison: plan.*radiating wings of prison blocks.*Drawn from"),
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
    "models": ("/models", r"(?s)3D models.*Stonehenge.*Bryn Celli Ddu"),
    "model_bryn_celli_ddu": ("/model/bryn_celli_ddu", r"(?s)Bryn Celli Ddu in 3D.*(The 3D model needs WebGL|sh-ready).*What it is built from"),
    "model_newgrange": ("/model/newgrange", r"(?s)Newgrange in 3D.*(The 3D model needs WebGL|sh-ready).*What it is built from"),
    "model_calanais": ("/model/calanais", r"(?s)Calanais in 3D.*(The 3D model needs WebGL|sh-ready).*What it is built from"),
    "stonehenge": ("/stonehenge", r"(?s)Stonehenge in 3D.*(The 3D model needs WebGL|sh-ready).*Was the circle ever complete"),
    "sky": ("/sky", r"(?s)Sky calendar.*Midwinter \(winter solstice\).*Newgrange.*The moon's standstills"),
    "sky_churches": ("/sky#churches", r"(?s)Churches and their saints' days.*sky-hist.*midwinter sunrise.*Over each church's skyline.*either saint"),
    "building_orientation": ("/building/Q390150", r"(?s)Orientation.*The east end of the outline's axis points.*where the skyline stands.*over a flat horizon"),
    "building_skyline": ("/building/Q339503", r"(?s)over the skyline 133\.9° SE.*sky-panorama.*bare ground with no trees"),
    "building_gridref": ("/building/Q339503", r"(?s)Coordinates.*Irish grid O 0074 7272</span> <button class=\"copy-btn\""),
    "building_gridref_os": ("/building/Q390150", r"(?s)Coordinates.*OS grid SU 1428 2950"),
    "map_gridref": ("/map?lat=51.1789&lon=-1.8262&z=15&mark=Stonehenge", r"gm-readout[^>]*>OS grid SU 12\d\d 42\d\d<"),
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
    "change_wages": ("/change", r"(?s)(?=.*Real wage rates, 1879-1938.*1914-1934 \(July 1914 = 100\).*Bowley.*76 in July 1917.*115 at the end of 1934.*Real wage rates, 1935-1975.*167 and 168.*152 in 1975.*Average weekly earnings at 2025 prices, 1963-2025.*modelled estimates.*1976-77 and 1995)(?=.*Wages in towns, 1790-1860.*not yet established)"),
    "change_banks": ("/change", r"(?s)Country banks in England and Wales, 1809-1832.*Gilbart.*940 in 1814.*Post-office Directory for 1834.*Country bank failures, 1809-1830.*311 in 1809-1830"),
    "change_banknotes": ("/change", r"(?s)Bank notes in circulation, 1846-1922.*£20.8 million of Bank of England.*June 1900.*Country bank notes in England and Wales, 1846-1921.*£2,000 remained in March 1921"),
    "change_savings": ("/change", r"(?s)Savings banks: amount due to depositors, 1846-1975.*passed them in 1885.*passed the Post Office's ordinary accounts in 1965.*1939: From 1939 at 31 March.*Savings banks by nation, 1846-1898.*Ireland's deposits fell.*Savings bank accounts open, 1897-1938.*coupon accounts"),
    "change_patents_ie": ("/change", r"(?s)Patents in Ireland, 2000-2025.*25% of the pre - 1992 level.*Patents with effect in Ireland, 2001-2025.*same legal status in Ireland.*Irish patent applications by term, 2001-2025.*Part II of the 1992 Act"),
    "change_clearing": ("/change", r"(?s)London Bankers' Clearing House: amounts cleared, 1868-1974.*District Bank.*1939: From 28 August 1939 the general clearing.*London Bankers' Clearing House at 1974 prices, 1868-1974.*less than in 1913.*Provincial bankers' clearing houses, 1897-1967.*Manchester was the largest.*afternoon clearing at Liverpool.*London credit clearing, 1961-1974.*Bankers' Automated Clearing Service"),
    "change_charters": ("/change", r"(?s)Borough charters per decade, 1040-1309.*861 charters to 261 towns.*as nearly exhaustive.*Ballard and Tait, British Borough Charters 1216-1307"),
    "change_steam": ("/change", r"(?s)Power in British industry, 1760-1907.*Kanefsky.*165,000 each.*2,279"),
    "change_shipping": ("/change", r"(?s)Merchant fleet registered in the UK, 1848-1970.*Nos. 10, 13, 26, 32.*overtook sail in 1883.*3.4 million tons in 1848.*Merchant ships built in the UK, 1846-1938.*steam first outweighed sail in 1870.*Breaks in definition.*1871: From 1871 ships built whether registered or not.*1897: From 1897 all merchant ships.*Merchant ships completed in the UK, 1940-1974.*611 in 1967.*UK-registered trading fleet, 1950-2025.*31.5 million in 1975.*1986: From 1986 Lloyd's Register"),
    "change_tea": ("/change", r"(?s)Tea retained for home consumption.*432 million in 1938.*Tea drunk per person.*Ministry of Food.*Family Food.*Price of imported tea.*16.1d. in 1919.*Price of imported tea by origin, 1854-1864.*Japan.*Wholesale price of tea.*19.44d. in 1938.*Duty on tea.*2s. 2¼d.*Imperial Preference.*1 January 1964.*Commutation Act cuts the tea duty.*Tea rationed"),
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
