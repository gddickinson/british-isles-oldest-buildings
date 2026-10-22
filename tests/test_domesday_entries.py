import unittest

from bidb.domesday_entries import parse

PAGE = """<html><title>Bosham | Domesday Book</title><p>It had a recorded population of 150.5 households in 1086.</p>
<dl><dt>Households</dt><dd>39 villagers. 51 smallholders. 17 slaves.</dd>
<dt>Other resources</dt><dd>Woodland 6 swine render. 8 mills. 2 fisheries. 1 church.</dd></dl>
<p>Phillimore reference : Sussex 1,1 View on page: Sussex folio 16</p>
<dd>2 villagers. 1 priest.</dd><dd>0.5 church. 0.15 church lands.</dd><p>Notes on the data : Churches: 1/4 church; half a church at Leverton</p><p>Phillimore reference : Sussex 6,1 View on page</p>
<p>Other households are sometimes noted, including priests, widows, burgesses.</p></html>"""


class Parse(unittest.TestCase):
    def test_counts_every_entry(self):
        got = parse(PAGE)
        self.assertEqual((got["churches"], got["priests"], got["households"]), (1.5, 1, 150.5))
        self.assertEqual(got["phillimore"], "Sussex 1,1; Sussex 6,1")

    def test_not_a_place_page(self):
        self.assertIsNone(parse("<html>Not found</html>"))


if __name__ == "__main__":
    unittest.main()
