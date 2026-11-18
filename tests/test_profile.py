import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('profile_generator', Path(__file__).parents[1] / 'scripts/generate_profile.py')
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class ActivityStats(unittest.TestCase):
    def test_streak_resets_on_inactive_days(self):
        self.assertEqual(profile.activity([0, 1, 2, 0, 4, 2, 1, 0]), (5, 3))
        self.assertEqual(profile.activity([]), (0, 0))


if __name__ == '__main__':
    unittest.main()
