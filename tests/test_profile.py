import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('profile_generator', Path(__file__).parents[1] / 'scripts/generate_profile.py')
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class SnakeRules(unittest.TestCase):
    def test_moves_without_collisions_and_grows_only_when_eating(self):
        for width in (2, 7, 53):
            for food in (set(), {(1, 1)}, {(x, y) for x in range(width) for y in range(7)}):
                with self.subTest(width=width, food_count=len(food)):
                    frames = profile.simulate(width, food)
                    remaining = set(food)
                    for previous, current in zip(frames, frames[1:]):
                        head = current[0]
                        self.assertEqual(abs(head[0]-previous[0][0])+abs(head[1]-previous[0][1]), 1)
                        self.assertTrue(0 <= head[0] < width and 0 <= head[1] < 8)
                        self.assertEqual(len(current), len(set(current)))
                        ate = head in remaining
                        self.assertEqual(len(current), len(previous) + ate)
                        self.assertEqual(current[1:], previous if ate else previous[:-1])
                        remaining.discard(head)
                    self.assertFalse(remaining)

    def test_streak_resets_on_inactive_days(self):
        self.assertEqual(profile.activity([0, 1, 2, 0, 4, 2, 1, 0]), (5, 3))
        self.assertEqual(profile.activity([]), (0, 0))


if __name__ == '__main__':
    unittest.main()
