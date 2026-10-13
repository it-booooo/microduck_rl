import tempfile
import unittest
from pathlib import Path

from tools.motor_log_viewer.data.csv_loader import parse_motor_log_info
from tools.motor_log_viewer.data_validation.input_checks import check
from tools.motor_log_viewer.tests.fixtures import write_motor_log_csv


class InputChecksTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.directory.cleanup()

    def test_clean_fixture_passes(self):
        csv_path = write_motor_log_csv(self.directory.name)
        info = parse_motor_log_info(csv_path)
        report = check(info, output_path=False)
        self.assertTrue(report["ok"])
        self.assertEqual(report["non_finite_count"], 0)
        self.assertEqual(report["missing_columns"], [])
        self.assertIsNone(report["fell_at_s"])

    def test_missing_column_is_reported(self):
        csv_path = write_motor_log_csv(self.directory.name)
        lines = csv_path.read_text().splitlines()
        header = lines[0].split(",")
        drop_index = header.index("tau_left_knee")
        rewritten = []
        for line in lines:
            cells = line.split(",")
            del cells[drop_index]
            rewritten.append(",".join(cells))
        csv_path.write_text("\n".join(rewritten) + "\n")

        info = parse_motor_log_info(csv_path)
        report = check(info, output_path=False)
        self.assertFalse(report["ok"])
        self.assertIn("tau_left_knee", report["missing_columns"])

    def test_fall_is_flagged_but_not_fatal(self):
        csv_path = write_motor_log_csv(self.directory.name, fell_at_s=3.2)
        info = parse_motor_log_info(csv_path)
        report = check(info, output_path=False)
        self.assertEqual(report["fell_at_s"], 3.2)
        self.assertTrue(report["ok"])

    def test_writes_report_csv_by_default(self):
        csv_path = write_motor_log_csv(self.directory.name)
        info = parse_motor_log_info(csv_path)
        report = check(info)
        self.assertTrue(Path(report["output_path"]).is_file())


if __name__ == "__main__":
    unittest.main()
