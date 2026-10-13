import unittest

from tools.motor_log_viewer.charts.chart_helpers import clamp_xlim, resolve_plot_step


class ChartHelpersTests(unittest.TestCase):
    def test_resolve_plot_step_defaults_to_5000_point_budget(self):
        self.assertEqual(resolve_plot_step(50_000, None), 10)
        self.assertEqual(resolve_plot_step(100, None), 1)
        self.assertEqual(resolve_plot_step(50_000, 3), 3)

    def test_clamp_xlim_keeps_window_width_inside_bounds(self):
        self.assertEqual(clamp_xlim(-1, 4, (0, 10)), (0, 5))
        self.assertEqual(clamp_xlim(6, 15, (0, 10)), (1, 10))
        self.assertEqual(clamp_xlim(2, 4, (0, 10)), (2, 4))

    def test_clamp_xlim_returns_full_range_when_wider_than_bounds(self):
        self.assertEqual(clamp_xlim(-5, 20, (0, 10)), (0, 10))


if __name__ == "__main__":
    unittest.main()
