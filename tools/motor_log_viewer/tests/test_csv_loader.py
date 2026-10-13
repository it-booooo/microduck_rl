import tempfile
import unittest

from tools.motor_log_viewer.data.csv_loader import parse_motor_log_info
from tools.motor_log_viewer.tests.fixtures import JOINT_NAMES, write_motor_log_csv


class CsvLoaderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.csv_path = write_motor_log_csv(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_parses_joint_names_and_meta_from_sidecar(self):
        info = parse_motor_log_info(self.csv_path)
        self.assertEqual(info["joint_names"], JOINT_NAMES)
        self.assertAlmostEqual(info["meta"]["kt_Nm_per_A"], 0.366)
        self.assertIn("tau_left_knee", info["columns"])

    def test_falls_back_to_column_names_without_meta_json(self):
        self.csv_path.with_name("fixture.meta.json").unlink()
        info = parse_motor_log_info(self.csv_path)
        self.assertIsNone(info["meta"])
        self.assertEqual(info["joint_names"], JOINT_NAMES)


if __name__ == "__main__":
    unittest.main()
