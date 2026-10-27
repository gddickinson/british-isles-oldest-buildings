"""Wikidata inventions (C6b): only items made at a real place in the isles are kept, finds and duplicates left out."""
import unittest

from bidb import innovations_wd as iw


def b(qid, name, place, coord, classes="", found=None, by="", article=None):
    row = {"i": {"value": f"http://www.wikidata.org/entity/{qid}"},
           "place": {"value": f"http://www.wikidata.org/entity/{place}"}, "name": {"value": name},
           "pname": {"value": f"place {place}"}, "coord": {"value": coord}, "classes": {"value": classes},
           "by": {"value": by}}
    if found:
        row["found"] = {"value": found}
    if article:
        row["article"] = {"value": article}
    return row


class Items(unittest.TestCase):
    def test_kept(self):
        got = iw.items([b("Q173853", "quaternion", "Q2057981", "Point(-6.3 53.373)", "hypercomplex number",
                          "1843-10-16T00:00:00Z", "William Rowan Hamilton", "https://en.wikipedia.org/wiki/Quaternion")])
        self.assertEqual(len(got), 1)
        it = got[0]
        self.assertEqual((it["name"], it["year"], it["place"], it["by"]), ("Quaternion", 1843, "Q2057981",
                                                                          ["William Rowan Hamilton"]))
        self.assertEqual(it["wikipedia_title"], "Quaternion")
        self.assertTrue(iw._discovery(it))

    def test_left_out(self):
        rows = [b("Q1", "hydrogen", "Q145", "Point(-2 54.6)"),                       # placed only at the UK
                b("Q2", "pasteurization", "Q3", "Point(5.77 46.9)"),                  # outside the isles
                b("Q4", "Sussex maniraptors", "Q23346", "Point(-0.14 50.95)", "fossil"),
                b("Q5", "discovery of electrons", "Q6", "Point(0.11 52.2)"),          # the event, not the thing
                b("Q6591619", "mechanical computer", "Q123634", "Point(-0.147 51.5)"),  # reviewed: SKIP
                b("Q7", "penicillin", "Q8", "Point(-0.17 51.5)"),                     # researched by name
                b("Q9", "Q9", "Q8", "Point(-0.17 51.5)")]                              # no English label
        self.assertEqual(iw.items(rows, names={"penicillin"}), [])

    def test_one_per_item(self):
        rows = [b("Q10", "Daniell cell", "Q245247", "Point(-0.116 51.512)"),
                b("Q10", "Daniell cell", "Q84", "Point(-0.1275 51.507)")]
        got = iw.items(rows)
        self.assertEqual([it["place"] for it in got], ["Q245247"])


if __name__ == "__main__":
    unittest.main()
