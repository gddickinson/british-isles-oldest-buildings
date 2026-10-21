"""Town pronunciations from Wiktionary entries (fixed text; no network)."""
import unittest

from bidb.pron_wiktionary import _pron_lines, parse

NEWCASTLE = """==English==
===Pronunciation===
* {{IPA|en|/ˈnjuːˌkɑːsl̩/|a=RP,Southern England}}
** {{audio|en|LL-Q1860 (eng)-Vealhurl-Newcastle.wav|a=Southern England}}
* {{IPA|en|/ˈnjuːˌkæsl̩/|a=Northern England,Midlands}}
* {{IPA|en|/ˈn(j)uˌkæsl̩/|a=US}}
* {{enPR|nōō-kăs-əl|a=cot-caught}} {{IPA|en|/ˈnuˌkæsəl/}}
===Proper noun===
# A city in [[Tyne and Wear]], [[England]].
==Welsh==
* {{IPA|cy|/ˈnɛu̯ˌkasl/|a=cy-N}}
"""
SPRINGFIELD = """==English==
* {{IPA|en|/ˈspɹɪŋfiːld/}}
===Proper noun===
# A city in [[Illinois]].
"""


class WiktionaryTest(unittest.TestCase):
    def test_regional_forms_kept_and_us_dropped(self):
        rows = parse("Newcastle", _pron_lines(NEWCASTLE))
        got = [(r["lang"], r["variety"], r["ipa"]) for r in rows if r["ipa"]]
        self.assertEqual(got, [("en", "Received Pronunciation", "ˈnjuːˌkɑːsl̩"),
                               ("en", "Northern English", "ˈnjuːˌkæsl̩"),
                               ("cy", "Welsh (north)", "ˈnɛu̯ˌkasl")])
        self.assertEqual(rows[0]["audio"], "LL-Q1860 (eng)-Vealhurl-Newcastle.wav")

    def test_places_outside_the_isles_ignored(self):
        self.assertEqual(parse("Springfield", _pron_lines(SPRINGFIELD)), [])


if __name__ == "__main__":
    unittest.main()
