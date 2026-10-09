"""Formula and full-frame audit regressions; no raw recording is modified."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/analysis"))
import english_pilot_review as review


class VoltageRatioTests(unittest.TestCase):
    def test_fixed_complex_gain_and_polarity_cancel(self):
        rest = np.array([2 + 3j, -4 + 1j])
        task = rest * np.array([1.02 + .03j, .99 - .01j])
        gain = np.array([-1j, -2 + 3j])
        np.testing.assert_allclose(review.relative_voltage(task, rest),
                                   review.relative_voltage(task * gain, rest * gain))

    def test_task_dependent_gain_does_not_cancel(self):
        rest = np.array([2 + 3j])
        task = rest.copy()
        np.testing.assert_allclose(review.relative_voltage(1.02 * task, rest), [.02])

    def test_zero_and_nonfinite_rest_rejected(self):
        for invalid in (0., np.nan, np.inf):
            with self.assertRaises(ValueError):
                review.relative_voltage(np.array([1.]), np.array([invalid]))

    def test_small_denominator_amplifies_same_count_difference(self):
        rest = np.array([1., 100.])
        result = review.relative_voltage(rest + 1., rest)
        np.testing.assert_allclose(result, [1., .01])

    def test_exact_magnitude_phase_reconstruct_complex_ratio(self):
        rest = np.array([2 + 3j, -4 + 1j])
        task = np.array([2.2 + 3.1j, -3.8 + .9j])
        ratio = task / rest
        reconstructed = np.abs(ratio) * np.exp(1j * np.angle(ratio)) - 1
        np.testing.assert_allclose(review.relative_voltage(task, rest), reconstructed)


class MultiFrequencyReconstructionTests(unittest.TestCase):
    def setUp(self):
        class LinearTestSolver:
            def __init__(self, gain):
                self.gain = gain

            def solve(self, v1, v0, normalize):
                return self.gain * (v1 - v0) / v0

        self.solvers = {n: LinearTestSolver(gain) for n, gain in (("BP", 1), ("JAC", 2), ("GREIT", 3))}
        self.common = np.array([True, False, True])
        self.vm = np.array([10., 12.])
        self.sessions = []
        for freq in (10000, 50000, 80000):
            rest = (freq / 10000) * np.array([1 + 1j, 2 - 1j, 3 + 2j])
            states = {"REST": rest}
            for index, task in enumerate(review.TASKS, start=1):
                states[task] = rest * (1 + .01 * index * freq / 10000 + .002j * index)
            self.sessions.append({"freq": freq, "v": states})
        self.images = review.reconstruct_states(self.sessions, self.common, None, self.vm, self.solvers)

    def test_covers_three_frequencies_seven_states_three_algorithms(self):
        self.assertEqual(set(self.images), {10000, 50000, 80000})
        for states in self.images.values():
            self.assertEqual(set(states), set(review.STATES))
            for ims in states.values():
                self.assertEqual(set(ims), {"BP", "JAC", "GREIT"})
        self.assertEqual(sum(len(ims) for states in self.images.values() for ims in states.values()), 63)

    def test_rest_is_zero_at_each_frequency(self):
        for states in self.images.values():
            for vals in states["REST"].values():
                np.testing.assert_array_equal(vals, [0., 0.])

    def test_each_frequency_uses_its_own_rest(self):
        for freq, states in self.images.items():
            np.testing.assert_allclose(states["SMILE_LEFT"]["BP"], .01 * freq / 10000)

    def test_excluded_measurements_are_not_projected(self):
        self.sessions[0]["v"]["SMILE_LEFT"][1] *= 100
        changed = review.reconstruct_states(self.sessions, self.common, None, self.vm, self.solvers)
        for n in self.solvers:
            np.testing.assert_allclose(changed[10000]["SMILE_LEFT"][n], self.images[10000]["SMILE_LEFT"][n])
            self.assertEqual(len(changed[10000]["SMILE_LEFT"][n]), 2)

    def test_colour_scale_is_shared_over_frequencies_and_states(self):
        scales = review.shared_image_scales(self.images)
        for n, gain in (("BP", 1), ("JAC", 2), ("GREIT", 3)):
            self.assertAlmostEqual(scales[n], gain * .48)

    def test_all_zero_images_have_valid_positive_scale(self):
        for states in self.images.values():
            for ims in states.values():
                for vals in ims.values():
                    vals[:] = 0
        scales = review.shared_image_scales(self.images)
        self.assertTrue(all(value > 0 for value in scales.values()))


class RecordedDataAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / review.source.SESSION_NAMES[0]
        if not path.exists():
            raise unittest.SkipTest("Live pilot raw folders are not included in this checkout.")
        cls.recording = review.source.load_session(path)

    def test_every_frame_passes(self):
        self.assertTrue(all(review.audit_session(self.recording).values()))

    def test_nonrest_sequence_corruption_detected(self):
        changed = dict(self.recording)
        changed["patterns"] = self.recording["patterns"].copy(deep=True)
        # First REST remains correct: a first-frame-only audit would miss this.
        changed["patterns"].loc[208, "f_plus"] = 15
        with self.assertRaises(ValueError):
            review.audit_session(changed)

    def test_nonrest_site_name_corruption_detected(self):
        changed = dict(self.recording)
        changed["patterns"] = self.recording["patterns"].copy(deep=True)
        changed["patterns"].loc[208, "f_plus_site"] = "R8"
        with self.assertRaises(ValueError):
            review.audit_session(changed)

    def test_out_of_frame_measurement_detected(self):
        changed = dict(self.recording)
        changed["patterns"] = self.recording["patterns"].copy(deep=True)
        changed["patterns"].loc[208, "start_s"] = 0
        with self.assertRaises(ValueError):
            review.audit_session(changed)


if __name__ == "__main__":
    unittest.main()
