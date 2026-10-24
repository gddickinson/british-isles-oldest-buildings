"""Livery companies (roadmap C3a): the two Wikipedia tables, hall names, the London check (no network)."""
import unittest

from bidb import institutions, livery, trade_works

PRECEDENCE = """===List of companies in order of precedence===
{| class="wikitable sortable"
! Order !! Company !! Year Charter Granted<ref name=vine>Vine</ref>
|-
| 1 || [[Worshipful Company of Mercers]] (general merchants) || 1394<ref>{{Cite web |title=700 years |url=https://www.mercers.co.uk/x |website=m}}</ref>
|-
| 6 || [[Worshipful Company of Skinners]]{{efn|name=alternate|The Skinners' and Merchant Taylors' alternate.}} (fur traders) || 1327
|-
| 46 || [[Worshipful Company of Plaisterers]] (plasterers) ||
|}
"""
HALLS = """{| class="wikitable sortable"
!Livery company
!#
!Company name
!Motto
!Language
!Translation
!Livery Hall
!Ref
|-
|[[Worshipful Company of Bakers]]
|19
|Bakers
|Praise God For All
|English
|
|Bakers' Hall, Harp Lane
|
|-
|[[Worshipful Company of Carpenters]]
|26
|Carpenters
|Honour God
|English
|
|[[Carpenters' Hall, London|Carpenters' Hall]], Throgmorton Avenue, [[London Wall]]
|
|-
|[[Worshipful Company of Weavers]]
|42
|Weavers
|Weave Truth With Trust
|English
|
|
|
|}
"""


class LiveryTables(unittest.TestCase):
    def test_precedence(self):
        c = livery.companies(PRECEDENCE)
        self.assertEqual(c["Worshipful Company of Mercers"], {
            "order": 1, "name": "Worshipful Company of Mercers", "trade": "general merchants", "charter": 1394,
            "charter_url": "https://www.mercers.co.uk/x"})
        self.assertEqual(c["Worshipful Company of Skinners"]["trade"], "fur traders")   # footnote dropped
        self.assertIsNone(c["Worshipful Company of Plaisterers"]["charter"])

    def test_halls(self):
        h = livery.halls(HALLS)
        self.assertEqual(h["Worshipful Company of Bakers"]["hall"], "Bakers' Hall, Harp Lane")
        self.assertIsNone(h["Worshipful Company of Bakers"]["hall_title"])
        # the hall's own link, not the street's
        self.assertEqual(h["Worshipful Company of Carpenters"]["hall_title"], "Carpenters' Hall, London")
        self.assertIsNone(h["Worshipful Company of Weavers"]["hall"])

    def test_hall_titles(self):
        h = livery.halls(HALLS)
        self.assertEqual(livery.hall_titles(h["Worshipful Company of Bakers"]), ["Bakers' Hall, London", "Bakers' Hall"])
        self.assertEqual(livery.hall_titles(h["Worshipful Company of Weavers"]), [])
        self.assertIsNone(livery.hall_name({"hall": "HMS Wellington, Temple Pier"}))
        self.assertEqual(livery.hall_name({"hall": "Insurers' Hall (closed)"}), "Insurers' Hall")

    def test_london(self):
        self.assertTrue(livery.in_london(51.5155, -0.101))         # Cutlers' Hall, Warwick Lane
        self.assertFalse(livery.in_london(53.3823, -1.46964))      # Cutlers' Hall, Sheffield


class TradeKinds(unittest.TestCase):
    def test_new_kinds(self):
        for k in ("tr_guild", "tr_bourse", "tr_merchant", "tr_livery"):
            self.assertEqual(trade_works.GROUPS[k], "Markets & trade")
        self.assertEqual(trade_works.LABELS["tr_guild"], livery.GUILD_LABEL)
        self.assertTrue(set(trade_works.KINDS).isdisjoint(institutions.KINDS))


if __name__ == "__main__":
    unittest.main()
