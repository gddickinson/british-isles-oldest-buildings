"""Stories from article wikitext, and tour stop choice / ordering.
.venv/bin/python -m unittest discover tests"""
import unittest

from bidb import tour_plan
from bidb.stories_parse import find, sections

ARTICLE = """{{Infobox castle|name=Example Castle}}
'''Example Castle''' is a castle in [[Somewhere]].<ref>A source</ref>

==History==
The castle was built in 1200 by [[William de Example|William]]. It was besieged in 1645.

==Legends==
According to legend, a [[giant]] named Bran threw the stones from the hill.&nbsp;He lived in the woods.

==Ghosts==
The castle is said to be haunted by a Grey Lady who walks the battlements.
The ghost appeared in the TV series ''Most Haunted'' in 2004.

==In popular culture==
The castle is the setting for a murder mystery novel.

==References==
{{reflist}}
[[Category:Reportedly haunted locations in England]]
"""


class Stories(unittest.TestCase):
    def setUp(self):
        self.found = find(sections(ARTICLE))

    def test_themed_sections_and_kinds(self):
        kinds = [s["kind"] for s in self.found]
        self.assertEqual(kinds.count("legend"), 1)
        self.assertEqual(kinds.count("supernatural"), 1)
        legend = next(s for s in self.found if s["kind"] == "legend")
        self.assertIn("giant named Bran", legend["text"])
        self.assertNotIn("&nbsp;", legend["text"])

    def test_popular_culture_and_tv_left_out(self):
        text = " ".join(s["text"] for s in self.found)
        self.assertNotIn("Most Haunted", text)
        self.assertNotIn("murder mystery", text)
        self.assertNotIn("besieged", text)

    def test_category_only_counts_when_no_text(self):
        self.assertFalse(any(s["text"].startswith("Wikipedia lists") for s in self.found))
        only_cat = find(sections("'''X''' is a house.\n[[Category:Reportedly haunted locations in Wales]]"))
        self.assertEqual([s["kind"] for s in only_cat], ["supernatural"])


class Tours(unittest.TestCase):
    def test_order_is_shortest_line(self):
        pts = [{"lat": 0, "lon": x} for x in (0, 3, 1, 2)]
        self.assertEqual([p["lon"] for p in tour_plan.order(pts)], [0, 1, 2, 3])

    def test_pick_spreads_stops(self):
        c = (54.0, -1.0)
        cands = [{"lat": 54.0, "lon": -1.0 + i * 0.0005, "score": 10 - i} for i in range(10)]
        cands += [{"lat": 54.004 + i * 0.002, "lon": -1.0, "score": 1} for i in range(6)]
        stops = tour_plan.pick_stops(cands, c, "walk")
        for a in stops:
            for b in stops:
                if a is not b:
                    self.assertGreaterEqual(tour_plan.km((a["lat"], a["lon"]), (b["lat"], b["lon"])), 0.12)

    def test_interest_prefers_landmarks_with_stories(self):
        plain = {"year_start": 1700}
        rich = {"year_start": 1100, "landmark": "Grade I", "stories": 2, "image_thumb": "x"}
        self.assertGreater(tour_plan.interest(rich), tour_plan.interest(plain))


if __name__ == "__main__":
    unittest.main()
