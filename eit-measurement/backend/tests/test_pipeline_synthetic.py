"""End-to-end run of `python -m app study` on a synthetic session with the next-session design:
3 initial REST frames, REST -> TASK -> REST blocks, 2 rounds, 2 frames per task, REST_CONTROL blocks."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "tests"))

from app.eit.config import DEFAULTS  # noqa: E402
from app.eit.report import run_study  # noqa: E402
from test_core import write_session  # noqa: E402


def design_frames(seed=0):
    rng = np.random.default_rng(seed)
    patterns = {t: 1 + 0.03 * rng.normal(size=208) for t in ("SMILE_LEFT", "PUFF_BOTH")}
    frames, trial = [], 0

    def add(task, n, gain):
        nonlocal trial
        trial += 1
        for _ in range(n):
            frames.append((f"T{trial:03d}", task, "task", gain * (1 + 0.001 * rng.normal(size=208))))

    add("REST", 3, np.ones(208))
    for _ in range(2):
        for task in ("SMILE_LEFT", "REST_CONTROL", "PUFF_BOTH"):
            add("REST", 1, np.ones(208))
            add(task, 2, patterns.get(task, np.ones(208)))
    add("REST", 1, np.ones(208))
    return frames


class SyntheticNextSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        raw = Path(cls.tmp.name) / "raw"
        write_session(raw / "synthetic-rest-task-rest", design_frames())
        cfg = copy.deepcopy(DEFAULTS)
        cfg.update({"study_id": "synthetic", "raw_root": str(raw), "out_root": str(Path(cls.tmp.name) / "out"),
                    "sessions": [{"dir": "synthetic-rest-task-rest", "label": "50 kHz"}],
                    "baseline": "bracketing_rest", "drop_first_task_frames": 1, "config_path": str(raw / "cfg.json")})
        cls.out = run_study(cfg, quick=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_outputs_exist(self):
        for rel in ("README.md", "manifest.json", "tables/task_features.csv", "tables/qc_summary.csv",
                    "tables/recognition.json", "tables/recon_metrics.csv", "figures/recon_bp_jac_greit_by_session.png",
                    "slides/S4_bp_jac_greit_50kHz.png", "clean/README.txt"):
            self.assertTrue((self.out / rel).exists(), rel)

    def test_repetitions_controls_and_noise_floor(self):
        tf = pd.read_csv(self.out / "tables/task_features.csv").set_index("task")
        self.assertEqual(set(tf.index), {"SMILE_LEFT", "REST_CONTROL", "PUFF_BOTH"})
        self.assertTrue((tf.n_repetitions == 2).all())
        self.assertLess(tf.loc["REST_CONTROL", "median_abs_dz_pct_strong"], 0.5)   # ~0.1 % noise only
        self.assertGreater(tf.loc["SMILE_LEFT", "median_abs_dz_pct_strong"], 1.0)  # 3 % pattern
        q = pd.read_csv(self.out / "tables/qc_summary.csv").iloc[0]
        self.assertEqual(int(q.rest_rest_pairs), 3)            # 3 initial REST + the first REST of round 1 are adjacent
        self.assertEqual(int(q.rest_across_control_pairs), 2)  # one REST_CONTROL block per round
        self.assertEqual(int(q.rest_across_task_pairs), 4)     # SMILE_LEFT and PUFF_BOTH, 2 rounds

    def test_leave_one_repetition_out_recognition(self):
        rec = json.loads((self.out / "tables/recognition.json").read_text())
        self.assertEqual(rec["groups"], ["rep1", "rep2"])
        self.assertEqual(rec["accuracy"], 1.0)
        self.assertEqual(rec["tasks"], ["SMILE_LEFT", "PUFF_BOTH"])  # REST_CONTROL is not a class
        # both rounds use the same order: recognition is confounded with position, and says so
        self.assertIn("confounded", rec["caveat"])
        self.assertIn("confounded with position", (self.out / "README.md").read_text())

    def test_readme_separates_control_and_warns_about_settings(self):
        text = (self.out / "README.md").read_text()
        self.assertIn("REST_CONTROL (no-task null", text)
        self.assertNotIn("single rest", text)


if __name__ == "__main__":
    unittest.main()
