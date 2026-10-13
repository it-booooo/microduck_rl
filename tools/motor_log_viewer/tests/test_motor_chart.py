import tempfile
import unittest

import matplotlib

matplotlib.use("Agg")
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from tools.motor_log_viewer.charts.motor_chart import populate_motor_timeseries_figure
from tools.motor_log_viewer.charts.torque_speed_chart import populate_torque_speed_figure
from tools.motor_log_viewer.data.csv_loader import parse_motor_log_info
from tools.motor_log_viewer.data.motor_dataset import MotorLogDataset
from tools.motor_log_viewer.tests.fixtures import write_motor_log_csv


class MotorChartTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        csv_path = write_motor_log_csv(self.directory.name, rows=200)
        info = parse_motor_log_info(csv_path)
        self.dataset = MotorLogDataset.from_csv(info)

    def tearDown(self):
        self.directory.cleanup()

    def test_timeseries_figure_has_four_axes_with_voltage_model(self):
        # self.dataset's fixture carries R_ohm/vin_V by default -> voltage row.
        fig = Figure()
        FigureCanvasAgg(fig)  # attach a real canvas before populating -- see chart_helpers.

        navigation = populate_motor_timeseries_figure(
            fig, self.dataset, ["left_knee", "right_knee"]
        )

        self.assertEqual(len(fig.axes), 4)
        self.assertEqual(fig.axes[-1].get_ylabel(), "Est. voltage [V]")
        left, right = fig.axes[0].get_xlim()
        navigation.set_xlim(left + 0.1, right - 0.1)
        new_left, new_right = fig.axes[0].get_xlim()
        self.assertGreater(new_left, left)
        self.assertLess(new_right, right)

        navigation.reset_x_zoom()
        self.assertEqual(fig.axes[0].get_xlim(), (left, right))

    def test_timeseries_figure_falls_back_to_three_axes_without_voltage_model(self):
        directory = tempfile.TemporaryDirectory()
        try:
            csv_path = write_motor_log_csv(
                directory.name, rows=50, with_voltage_model=False
            )
            info = parse_motor_log_info(csv_path)
            dataset = MotorLogDataset.from_csv(info)

            fig = Figure()
            FigureCanvasAgg(fig)
            populate_motor_timeseries_figure(fig, dataset, ["left_knee"])

            self.assertEqual(len(fig.axes), 3)
        finally:
            directory.cleanup()

    def test_torque_speed_figure_shows_only_the_requested_joint(self):
        fig = Figure()
        FigureCanvasAgg(fig)

        populate_torque_speed_figure(fig, self.dataset, "left_knee")

        self.assertEqual(len(fig.axes), 1)
        self.assertEqual(fig.axes[0].get_title(), "left_knee")
        self.assertTrue(fig.axes[0].has_data())

    def test_torque_speed_figure_redraw_replaces_the_previous_joint(self):
        fig = Figure()
        FigureCanvasAgg(fig)

        populate_torque_speed_figure(fig, self.dataset, "left_knee")
        populate_torque_speed_figure(fig, self.dataset, "right_ankle")

        self.assertEqual(len(fig.axes), 1)
        self.assertEqual(fig.axes[0].get_title(), "right_ankle")


if __name__ == "__main__":
    unittest.main()
