import csv
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure

from tools.motor_log_viewer.data.csv_loader import parse_motor_log_info
from tools.motor_log_viewer.data.motor_dataset import MotorLogDataset
from tools.motor_log_viewer.data_export.file_writers import (
    write_figure_png,
    write_summary_csv,
)
from tools.motor_log_viewer.tests.fixtures import write_motor_log_csv


class FileWritersTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.directory.cleanup()

    def test_write_summary_csv_round_trips_joint_names(self):
        csv_path = write_motor_log_csv(self.directory.name)
        info = parse_motor_log_info(csv_path)
        dataset = MotorLogDataset.from_csv(info)
        out_path = Path(self.directory.name) / "summary.csv"

        write_summary_csv(dataset.summary(), out_path)

        with out_path.open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual({row["joint"] for row in rows}, set(dataset.joint_names))

    def test_write_figure_png_creates_a_file(self):
        fig = Figure()
        fig.add_subplot().plot([0, 1], [0, 1])
        out_path = Path(self.directory.name) / "chart.png"

        write_figure_png(fig, out_path)

        self.assertTrue(out_path.is_file())
        self.assertGreater(out_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
