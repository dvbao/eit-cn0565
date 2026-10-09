"""Regression: the pipeline reproduces the 2026-10-05 three-frequency results exactly.

Expected values were saved from the original analysis scripts before the reorganisation
(tests/fixtures/three_frequency_20261005_expected.json). Skipped if the raw sessions are absent.
"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.eit.config import load_config  # noqa: E402
from app.eit.report import run_study  # noqa: E402

CONFIG = ROOT / "data/studies/three-frequency-20261005.json"
EXPECTED = json.loads((BACKEND / "tests/fixtures/three_frequency_20261005_expected.json").read_text())
RAW = ROOT / "data/sessions/session-1-20261005-10000Hz-600mV"


@unittest.skipUnless(RAW.exists(), "raw sessions not available")
class ThreeFrequencyRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cfg = copy.deepcopy(load_config(CONFIG))
        cfg["out_root"] = cls.tmp.name
        cfg["outputs"] = {"report_figures": False, "slide_figures": False, "clean_images": False}
        cls.out = run_study(cfg)
        cls.t = {name: pd.read_csv(cls.out / "tables" / f"{name}.csv") for name in
                 ("qc_summary", "task_features", "lateralization", "correlation_across_sessions", "additivity",
                  "electrode_involvement", "recon_metrics")}
        cls.rec = json.loads((cls.out / "tables/recognition.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def close(self, a, b, msg):
        self.assertAlmostEqual(float(a), float(b), places=9, msg=msg)

    def test_qc(self):
        q = self.t["qc_summary"].set_index("label")
        for lab, e in EXPECTED["qc"].items():
            self.assertEqual(int(q.loc[lab, "rest_n_ge_50"]), e["rest_n_ge_50"])
            self.assertEqual(q.loc[lab, "frames_inside_hold"], e["frames_inside_hold"])
            for k in ("rest_abs_median_counts", "recip_err_strong_median_pct", "recip_err_after_drive_gain_fit_pct"):
                self.close(q.loc[lab, k], e[k], f"{lab} {k}")

    def test_task_features(self):
        tf = self.t["task_features"].set_index(["label", "task"])
        for key, e in EXPECTED["task_features"].items():
            lab, task = key.split("|")
            for k, v in e.items():
                self.close(tf.loc[(lab, task), k], v, f"{key} {k}")

    def test_lateralization(self):
        lat = self.t["lateralization"].set_index(["label", "task"])
        for key, e in EXPECTED["lateralization"].items():
            lab, task = key.split("|")
            for k, v in e.items():
                self.close(lat.loc[(lab, task), k], v, f"{key} {k}")

    def test_correlations_additivity_involvement(self):
        xc = self.t["correlation_across_sessions"].set_index(["session_a", "session_b", "task"])
        for key, v in EXPECTED["cross_session_r"].items():
            a, b, task = key.split("|")
            self.close(xc.loc[(a, b, task), "r_same_task_common_strong"], v, key)
        add = self.t["additivity"].set_index(["label", "task"])
        for key, v in EXPECTED["additivity_r2"].items():
            lab, task = key.split("|")
            self.close(add.loc[(lab, task), "r2"], v, key)
        inv = self.t["electrode_involvement"].set_index(["label", "task"])
        for key, e in EXPECTED["involvement"].items():
            lab, task = key.split("|")
            for site, v in e.items():
                self.close(inv.loc[(lab, task), site], v, f"{key} {site}")

    def test_recognition(self):
        self.close(self.rec["accuracy"], EXPECTED["recognition"]["accuracy"], "accuracy")
        self.close(self.rec["perm_p"], EXPECTED["recognition"]["perm_p"], "perm_p")

    def test_reconstruction(self):
        m = self.t["recon_metrics"].set_index(["algorithm", "label", "task"])
        for key, e in EXPECTED["recon"].items():
            algo, lab, task = key.split("|")
            for k, v in e.items():
                self.close(m.loc[(algo, lab, task), k], v, f"{key} {k}")


if __name__ == "__main__":
    unittest.main()
