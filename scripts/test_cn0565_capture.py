import csv
import json
import math
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import cn0565_capture as capture  # noqa: E402
import cn0565_prepare_difference as prepare  # noqa: E402
import cn0565_plot_difference as plot  # noqa: E402


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.mapping_document, self.channels = capture.load_mapping(capture.DEFAULT_MAPPING)

    def test_mapping_and_adjacent_sequence(self):
        sequence = capture.make_sequence()
        self.assertEqual(len(sequence), 208)
        self.assertEqual(sequence[0], (0, 2, 3, 1))
        self.assertEqual(self.channels[0]["site"], "L1")
        self.assertEqual(self.channels[15]["site"], "R1")
        self.assertEqual(self.channels[12]["p1_pin"], 17)

    def test_mock_capture_files_and_boundaries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prefix = Path(temp_dir) / "run"
            summary = capture.capture(
                capture.MockBoard(), self.mapping_document, self.channels,
                [{"label": "rest", "frames": 2}, {"label": "task", "frames": 2}],
                prefix, {"source": "mock"},
            )
            self.assertEqual(summary["status"], "complete")
            self.assertEqual(summary["completed_frames"], 4)
            with Path(f"{prefix}.voltages.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 4 * 208)
            self.assertEqual(rows[0]["f_plus_site"], "L1")
            self.assertEqual(rows[0]["f_plus_p1_pin"], "3")
            self.assertEqual(rows[0]["s_plus_site"], "L3")
            self.assertEqual(rows[0]["s_minus_site"], "L4")
            self.assertEqual(rows[0]["f_minus_site"], "L2")
            self.assertEqual(rows[208]["frame_id"], "1")
            with Path(f"{prefix}.events.csv").open(newline="") as stream:
                events = list(csv.DictReader(stream))
            self.assertEqual([event["first_frame_id"] for event in events], ["0", "2"])
            meta = json.loads(Path(f"{prefix}.meta.json").read_text())
            self.assertEqual(len(meta["switch_sequence"]), 208)
            self.assertGreater(meta["frame_start_interval_p95_s"], 0)

    def test_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prefix = Path(temp_dir) / "run"
            Path(f"{prefix}.frames.csv").touch()
            with self.assertRaises(FileExistsError):
                capture.capture(
                    capture.MockBoard(), self.mapping_document, self.channels,
                    [{"label": "rest", "frames": 1}], prefix, {"source": "mock"},
                )

    def test_schedule_parser_uses_complete_frame_counts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            schedule = Path(temp_dir) / "schedule.json"
            schedule.write_text(json.dumps({"blocks": [
                {"label": "rest", "frames": 3},
                {"label": "task", "frames": 5},
            ]}))
            self.assertEqual(
                capture.load_blocks(Namespace(frames=None, schedule=schedule)),
                [{"label": "rest", "frames": 3}, {"label": "task", "frames": 5}],
            )

    def test_incomplete_frame_is_not_logged_as_complete(self):
        class BadBoard(capture.MockBoard):
            @property
            def all_voltages(self):
                return super().all_voltages[:-1]

        with tempfile.TemporaryDirectory() as temp_dir:
            prefix = Path(temp_dir) / "run"
            with self.assertRaisesRegex(ValueError, "Incomplete frame"):
                capture.capture(
                    BadBoard(), self.mapping_document, self.channels,
                    [{"label": "rest", "frames": 1}], prefix, {"source": "mock"},
                )
            meta = json.loads(Path(f"{prefix}.meta.json").read_text())
            self.assertEqual(meta["status"], "incomplete")
            self.assertEqual(meta["completed_frames"], 0)

    def test_rest_task_vector_preparation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prefix = Path(temp_dir) / "run"
            capture.capture(
                capture.MockBoard(), self.mapping_document, self.channels,
                [{"label": "rest", "frames": 2}, {"label": "task", "frames": 2}],
                prefix, {"source": "mock"},
            )
            result = prepare.prepare(prefix, [0, 1], [2, 3])
            self.assertEqual(len(result["v0_real_imag_raw"]), 208)
            self.assertEqual(len(result["v1_real_imag_raw"]), 208)
            self.assertEqual(result["delta_real_imag_raw"][0], [2.0, 0.0])
            with self.assertRaisesRegex(ValueError, "overlap"):
                prepare.prepare(prefix, [1], [1])

    def test_task_step_recovers_to_rest_and_plot(self):
        class StepBoard(capture.MockBoard):
            @property
            def all_voltages(self):
                self.frame_number += 1
                values = [[10.0, 2.0] for _ in self.switch_sequence]
                if 4 <= self.frame_number <= 6:
                    values[0][0] += 4.0
                    values[1][1] -= 3.0
                return values

        with tempfile.TemporaryDirectory() as temp_dir:
            prefix = Path(temp_dir) / "step"
            capture.capture(
                StepBoard(), self.mapping_document, self.channels,
                [{"label": "rest", "frames": 3}, {"label": "task", "frames": 3},
                 {"label": "post_rest", "frames": 3}], prefix, {"source": "test"},
            )
            result = prepare.prepare(prefix, [0, 1, 2], [3, 4, 5], [6, 7, 8])
            self.assertEqual(result["delta_real_imag_raw"][0], [4.0, 0.0])
            self.assertEqual(result["delta_real_imag_raw"][1], [0.0, -3.0])
            self.assertEqual(result["delta_real_imag_raw"][2:], [[0.0, 0.0]] * 206)
            self.assertAlmostEqual(result["descriptive_metrics"]["task_minus_rest_rms_raw"],
                                   math.sqrt(25 / 208))
            self.assertEqual(result["descriptive_metrics"]["post_rest_minus_rest_rms_raw"], 0)
            control = prepare.prepare(prefix, [0, 1, 2], [6, 7, 8])
            self.assertEqual(control["descriptive_metrics"]["task_minus_rest_rms_raw"], 0)
            with self.assertRaisesRegex(ValueError, "overlap"):
                prepare.prepare(prefix, [0], [3], [0])
            comparison_path = Path(temp_dir) / "trial.json"
            comparison_path.write_text(json.dumps(result))
            try:
                import matplotlib  # noqa: F401
            except ImportError:
                return  # Numerical tests work with stdlib; plot requires matplotlib.
            image_path = Path(temp_dir) / "trial.png"
            plot.plot_comparison(comparison_path, image_path)
            self.assertGreater(image_path.stat().st_size, 1000)
            with self.assertRaises(FileExistsError):
                plot.plot_comparison(comparison_path, image_path)

    def test_drift_is_visible_in_post_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prefix = Path(temp_dir) / "drift"
            capture.capture(
                capture.MockBoard(), self.mapping_document, self.channels,
                [{"label": "rest", "frames": 3}, {"label": "task", "frames": 3},
                 {"label": "post_rest", "frames": 3}], prefix, {"source": "mock"},
            )
            result = prepare.prepare(prefix, [0, 1, 2], [3, 4, 5], [6, 7, 8])
            self.assertEqual(result["descriptive_metrics"]["task_minus_rest_rms_raw"], 3)
            self.assertEqual(result["descriptive_metrics"]["post_rest_minus_rest_rms_raw"], 6)


if __name__ == "__main__":
    unittest.main()
