import unittest
from shapely.geometry import shape, Polygon
from engine import load, run

class TestEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = load('example_site.json')
        cls.schemes = run(cls.site, 12)

    def test_scheme_count(self):
        self.assertEqual(len(self.schemes), 12)

    def test_constraints(self):
        site = self.site
        usable = Polygon(site['boundary']).buffer(-site['setback_m'], join_style=2)
        for scheme in self.schemes:
            self.assertLessEqual(scheme['metrics']['achieved_far'], site['far_limit'] + 0.001)
            for i, b in enumerate(scheme['buildings']):
                geom = shape(b['geometry'])
                self.assertTrue(usable.covers(geom))
                self.assertLessEqual(b['height_m'], site['height_limit_m'] + 1e-8)
                for other in scheme['buildings'][i+1:]:
                    self.assertGreaterEqual(geom.distance(shape(other['geometry'])) + 1e-8, site['screening_spacing_m'])

    def test_reproducible(self):
        self.assertEqual(run(self.site, 5), run(self.site, 5))

    def test_unverified_codes_flagged(self):
        for s in self.schemes:
            self.assertEqual(s['checks']['daylight'], 'NOT_EVALUATED')
