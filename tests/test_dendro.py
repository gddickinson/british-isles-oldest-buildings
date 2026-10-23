import unittest

from bidb.dendro import match, tokens
from bidb.osgrid import to_latlon


def grid(*recs):
    from collections import defaultdict
    g = defaultdict(list)
    for rid, name, lat, lon in recs:
        g[round(lat * 20), round(lon * 20)].append((rid, name, lat, lon, tokens(name)))
    return g


class OsGrid(unittest.TestCase):
    def test_british_and_irish(self):
        lat, lon = to_latlon("SP 536 027")                 # Littlemore, Oxford
        self.assertAlmostEqual(lat, 51.72, delta=0.01)
        self.assertAlmostEqual(lon, -1.22, delta=0.01)
        lat, lon = to_latlon("C 799 348", irish=True)      # Pottagh, Co. Londonderry
        self.assertAlmostEqual(lat, 55.15, delta=0.01)
        self.assertAlmostEqual(lon, -6.74, delta=0.015)

    def test_typos_and_bad_refs(self):
        self.assertIsNotNone(to_latlon("S0 281 554"))      # zero for the letter O
        self.assertIsNone(to_latlon("SP 12345"))
        self.assertIsNone(to_latlon(""))


class Match(unittest.TestCase):
    def entry(self, location, lat=52.0, lon=-1.0):
        return {"location": location, "lat": lat, "lon": lon}

    def test_name_match(self):
        g = grid(("Q1", "Horton Court", 52.001, -1.0))
        self.assertEqual(match(self.entry("Horton, Horton Court; North Range"), g)[0], "Q1")

    def test_town_only_is_not_enough(self):
        g = grid(("Q2", "Tamworth Castle", 52.001, -1.0))
        self.assertIsNone(match(self.entry("Tamworth, 6 Market Street"), g))
        self.assertIsNone(match(self.entry("Tamworth, 16 Castle Street"), g))   # a street name is not the castle

    def test_town_and_kind(self):
        g = grid(("Q3", "Lincoln Cathedral", 52.002, -1.0))
        self.assertEqual(match(self.entry("Lincoln, Cathedral, NE Transept roof"), g)[0], "Q3")

    def test_other_dedication(self):
        g = grid(("Q4", "St Paul's Church, Bristol", 52.002, -1.0))
        self.assertIsNone(match(self.entry("Bristol, Whitson Street, Church of St James, chancel roof"), g))


if __name__ == "__main__":
    unittest.main()


class DendroAdd(unittest.TestCase):
    """bidb.dendro_add: which Wikidata items may take a VAG entry's date (cases from the first review)."""

    def test_plausible(self):
        from bidb.dendro_add import plausible
        cases = [("23 And 25, Kirkgate", "Newark-on-Trent, 37 Kirkgate", False),
                 ("9, Market End", "Coggeshall, 9 Market End", True),
                 ("East Hele Farmhouse", "King's Nympton, West Hele", False),
                 ("3rd White Cloth Hall", "Leeds, 100 Kirkgate, First White Cloth Hall", False),
                 ("The Red Cross Public House", "Henley-on-Thames, Hart Street, The Red Lion Hotel, West wing", False),
                 ("Old Barn At Home Farm", "Newdigate, Home Farm House", False),
                 ("Church of St Bartholomew", "Munsley, Church of St Bartholomew, Dug-out church chest", False),
                 ("Pennellick Farmhouse", "Pelynt, Pennellick", True),
                 ("1 and 2, Ufton Fields", "Ufton, 1-2 Ufton Fields, Cruck House", True),
                 ("The King's Head Public House", "Shrewsbury, Mardol, The King's Head", True),
                 ("Kilve Chantry", "Kilve, Sea Lane, Kilve Chantry, North wing", True)]
        for label, location, want in cases:
            self.assertEqual(plausible(label, {"location": location}), want, label)

    def test_year_of_range(self):
        from bidb.dendro_add import year_of
        self.assertEqual(year_of({"felled_from": 1300, "felled_to": 1335}), 1317)   # "1315-15+20"
        self.assertEqual(year_of({"felled_from": 1430, "felled_to": 1432}), 1430)
