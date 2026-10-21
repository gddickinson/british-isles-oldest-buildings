"""Pronunciations parsed from Wikipedia article openings (fixed wikitext; no network)."""
import unittest

from bidb.pron_db import audio_urls
from bidb.pron_parse import clean_lead, parse_lead, variety_of

BELVOIR = ("{{Infobox castle|name='''Belvoir'''}}\n'''Belvoir Castle''' ({{IPAc-en|ˈ|b|iː|v|ər|"
           "audio=En-belvoir_castle.ogg}} {{respell|BEE|vər}})<ref>{{cite web|url=x}}</ref> is a castle.")
KILKENNY = ("'''Kilkenny Castle''' ({{langx|ga|Caisleán Chill Chainnigh}} "
            "{{IPA|ga|ˈkaʃlʲaːnˠ ˈçiːl̠ʲ ˈxan̠ʲəɟ|pron}}) is a castle.")
EDINBURGH = ("'''Edinburgh'''{{efn|{{IPAc-en|audio=edinburgh.ogg|ˈ|ɛ|d|ɪ|n|b|ər|ə}} {{respell|ED|in|bər|ə}}; "
             "{{IPA|sco|ˈɛdɪnbʌrə|lang}}; {{langx|gd|Dùn Èideann}} {{IPA|gd|t̪un ˈeːtʲən̪ˠ|}}}} is the capital.")
BELFAST = ("'''Belfast''' ({{IPAc-en|ˈ|b|ɛ|l|f|æ|s|t}} {{Respell|BEL-fast}}, {{IPAc-en|-|f|a:|s|t}}, "
           "{{Respell|-fahst}}) is a city.")
ARAN = ("'''{{langr|ga|Dún Aonghasa}}''' is a hill fort. It lies on {{langr|ga|[[Inishmore|Inis Mór]]}}, "
        "at the edge of a cliff.")
LOCAL = "'''Shrewsbury''' ({{IPAc-en|ˈ|ʃ|r|oʊ|z|b|ər|i}}, ''locally'' {{IPAc-en|ˈ|ʃ|r|uː|z|b|ər|i}}) is a town."


def rows(text, title=""):
    return parse_lead(clean_lead(text), title)


class ParseTest(unittest.TestCase):
    def test_english_with_respelling_and_audio(self):
        [r] = rows(BELVOIR)
        self.assertEqual((r["name"], r["ipa"], r["respell"], r["audio"]),
                         ("Belvoir Castle", "ˈbiːvər", "BEE-vər", "En-belvoir_castle.ogg"))

    def test_native_name_joined_with_its_ipa(self):
        [r] = rows(KILKENNY)
        self.assertEqual((r["name"], r["variety"]), ("Caisleán Chill Chainnigh", "Irish"))
        self.assertTrue(r["ipa"].startswith("ˈkaʃ"))

    def test_footnote_pronunciations(self):
        got = {r["variety"]: r for r in rows(EDINBURGH)}
        self.assertEqual(got["English"]["respell"], "ED-in-bər-ə")
        self.assertEqual(got["Scots"]["ipa"], "ˈɛdɪnbʌrə")
        self.assertEqual(got["Scottish Gaelic"]["name"], "Dùn Èideann")

    def test_partial_alternatives_skipped(self):
        self.assertEqual([r["respell"] for r in rows(BELFAST)], ["BEL-fast"])

    def test_foreign_words_in_running_text_are_not_names(self):
        self.assertEqual([r["name"] for r in rows(ARAN)], ["Dún Aonghasa"])

    def test_second_bold_and_etymology(self):
        got = rows("'''Dun Mor Vaul''' (or simply '''Dun Mor'''; {{langx|gd|Dùn Mòr}}) is a broch.")
        self.assertEqual([r["name"] for r in got], ["Dùn Mòr"])
        got = rows("The '''Radcliffe Camera''' (from [[Latin]] {{lang|la|camera}}, meaning 'chamber') is a library.")
        self.assertEqual(got, [])

    def test_local_qualifier(self):
        self.assertEqual([r["variety"] for r in rows(LOCAL)], ["English", "Local"])

    def test_variety_codes(self):
        self.assertEqual(variety_of("en-gb"), "British English")
        self.assertEqual(variety_of("cy"), "Welsh")
        self.assertEqual(variety_of("gv"), "Manx")

    def test_audio_urls(self):
        u = audio_urls("En-belvoir castle.ogg")
        self.assertTrue(u["src"].endswith("/En-belvoir_castle.ogg"))
        self.assertTrue(u["mp3"].endswith(".ogg.mp3"))


if __name__ == "__main__":
    unittest.main()
