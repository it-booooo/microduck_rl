import math
import tempfile
import unittest

import numpy as np

from tools.motor_log_viewer.data.csv_loader import parse_motor_log_info
from tools.motor_log_viewer.data.motor_dataset import MotorLogDataset
from tools.motor_log_viewer.tests.fixtures import write_motor_log_csv


class MotorDatasetTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.csv_path = write_motor_log_csv(self.directory.name, rows=40)
        self.info = parse_motor_log_info(self.csv_path)
        self.dataset = MotorLogDataset.from_csv(self.info)

    def tearDown(self):
        self.directory.cleanup()

    def test_arrays_match_csv_row_count(self):
        self.assertEqual(len(self.dataset.time), 40)
        self.assertEqual(len(self.dataset.torque("left_knee")), 40)

    def test_summary_is_sorted_by_rms_torque_descending(self):
        rows = self.dataset.summary()
        rms_values = [row.tau_rms_Nm for row in rows]
        self.assertEqual(rms_values, sorted(rms_values, reverse=True))
        self.assertEqual({row.joint for row in rows}, set(self.dataset.joint_names))

    def test_current_matches_torque_over_kt(self):
        tau = self.dataset.torque("right_ankle")
        cur = self.dataset.current("right_ankle")
        np.testing.assert_allclose(cur, tau / self.dataset.kt, rtol=1e-6)

    def test_time_at_limit_pct_is_zero_under_limit(self):
        # left_knee's fixture amplitude (0.4 N·m) stays under torque_limit_Nm.
        stats = self.dataset.stats("left_knee")
        self.assertEqual(stats.time_at_limit_pct, 0.0)

    def test_time_at_limit_pct_is_positive_over_limit(self):
        # right_ankle's fixture amplitude (1.4 N·m) exceeds torque_limit_Nm.
        stats = self.dataset.stats("right_ankle")
        self.assertGreater(stats.time_at_limit_pct, 0.0)

    def test_voltage_matches_dc_motor_equation(self):
        cur = self.dataset.current("right_hip_pitch")
        vel = self.dataset.speed("right_hip_pitch")
        expected = cur * self.dataset.R_ohm + self.dataset.kt * vel
        np.testing.assert_allclose(
            self.dataset.voltage("right_hip_pitch"), expected, rtol=1e-6
        )

    def test_duty_cycle_is_voltage_over_vin(self):
        voltage = self.dataset.voltage("right_hip_pitch")
        np.testing.assert_allclose(
            self.dataset.duty_cycle("right_hip_pitch"), voltage / self.dataset.vin_V
        )

    def test_voltage_saturation_detected_for_heavy_joint(self):
        # right_ankle's current swing (1.4 N·m / kt ~= 3.8 A) through R_ohm
        # alone exceeds vin -- the real firmware could never hold that duty.
        stats = self.dataset.stats("right_ankle")
        self.assertGreater(stats.time_voltage_saturated_pct, 0.0)
        self.assertGreater(stats.voltage_peak_V, self.dataset.vin_V * self.dataset.max_pwm)


class MotorDatasetWithoutVoltageModelTests(unittest.TestCase):
    """Logs written before R_ohm/vin_V were added must degrade, not crash."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        csv_path = write_motor_log_csv(
            self.directory.name, rows=20, with_voltage_model=False
        )
        info = parse_motor_log_info(csv_path)
        self.dataset = MotorLogDataset.from_csv(info)

    def tearDown(self):
        self.directory.cleanup()

    def test_has_voltage_model_is_false(self):
        self.assertFalse(self.dataset.has_voltage_model)
        self.assertIsNone(self.dataset.R_ohm)

    def test_voltage_raises_a_clear_error(self):
        with self.assertRaises(ValueError):
            self.dataset.voltage("left_knee")

    def test_stats_voltage_fields_are_nan_not_a_crash(self):
        stats = self.dataset.stats("left_knee")
        self.assertTrue(math.isnan(stats.voltage_rms_V))
        self.assertTrue(math.isnan(stats.time_voltage_saturated_pct))


if __name__ == "__main__":
    unittest.main()
