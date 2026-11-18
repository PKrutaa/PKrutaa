import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('snake_style', Path(__file__).parents[1] / 'scripts/style_snake.py')
style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)


class SnakeStyle(unittest.TestCase):
    def test_keeps_original_movement_and_fixed_segments_with_new_face(self):
        source = '<svg><style>.s{animation:none linear 10s infinite}@keyframes s0{to{transform:translate(16px,0)}}</style><rect class="s s0" x="0"/><rect class="s s1" x="1"/></svg>'
        result = style.decorate(source, '#0d1117')
        self.assertIn('@keyframes s0{to{transform:translate(16px,0)}}', result)
        self.assertEqual(result.count('class="s s'), 2)
        self.assertEqual(result.count('width="15" height="15"'), 2)
        self.assertEqual(result.count('<circle'), 2)
        self.assertIn('snake-tongue', result)


if __name__ == '__main__':
    unittest.main()
