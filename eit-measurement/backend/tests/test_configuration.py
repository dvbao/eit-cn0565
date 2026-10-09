"""Configurable hardware and study design: everything derived from the electrode count and the design."""

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

from app.services import protocol_runner as ds  # noqa: E402
from app.schemas.models import MeasurementConfig, load_measurement, load_wiring, wired_sites  # noqa: E402
from app.eit.protocol import make_sequence, ring_distances, std_sequence  # noqa: E402

WIRING = ROOT / "data/hardware/C16-R-user-interleaved-TMJ5-v2-208.json"
MEASUREMENT = ROOT / "data/hardware/measurement-16el-50kHz.json"
DESIGN = ROOT / "data/protocols/facial-rest-task-rest-v1.json"


def adi_switch_sequence(n, force, sense):
    """Copy of adi.cn0565.switch_sequence (pyadi-iio), returned as (F+, F-, S+, S-)."""
    rows = []
    for i in range(n):
        f_plus, f_minus = i, (i + force) % n
        for j in range(n):
            s_plus = j % n
            if s_plus in (f_plus, f_minus):
                continue
            s_minus = (s_plus + sense) % n
            if s_minus in (f_plus, f_minus):
                continue
            rows.append((f_plus, f_minus, s_plus, s_minus))
    return np.array(rows)


class SequenceTests(unittest.TestCase):
    def test_counts_follow_the_electrode_count(self):
        self.assertEqual([len(std_sequence(n)) for n in (8, 16, 32)], [40, 208, 928])

    def test_same_rows_and_order_as_driver_and_pyeit(self):
        try:
            import pyeit.eit.protocol as protocol
        except ImportError:
            self.skipTest("pyEIT not installed")
        for n in (8, 16, 32):
            for f, s in ((1, 1), (2, 1), (1, 2), (n // 2, 1)):
                seq = make_sequence(n, f, s)
                np.testing.assert_array_equal(seq, adi_switch_sequence(n, f, s))
                p = protocol.create(n, f, s, "std")
                rows = np.array([(a, b, m, k) for (a, b), ms in zip(p.ex_mat, p.meas_mat) for k, m in ms])
                np.testing.assert_array_equal(seq, rows)
                self.assertEqual(ring_distances(seq, n), (f, s))

    def test_invalid_rings_are_rejected(self):
        for args in ((3, 1, 1), (8, 0, 1), (8, 1, 8)):
            with self.assertRaises(ValueError):
                make_sequence(*args)
        self.assertIsNone(ring_distances(std_sequence(16)[::-1], 16))


class MeasurementConfigTests(unittest.TestCase):
    def test_derived_values(self):
        self.assertEqual(MeasurementConfig(n_electrodes=16).summary(), {"n_measurements": 208, "frame_s": 20.59})
        self.assertEqual(MeasurementConfig(n_electrodes=8).summary(), {"n_measurements": 40, "frame_s": 3.96})

    def test_validation(self):
        wiring = load_wiring(WIRING)
        self.assertEqual(load_measurement(MEASUREMENT).validate(wiring), [])
        problems = MeasurementConfig(n_electrodes=12, force_distance=12, measurement_mode="x").validate(wiring)
        self.assertEqual(len(problems), 3)  # distance, mode, wiring mismatch (12 electrodes fit the board)
        self.assertTrue(any("board X lines" in p for p in MeasurementConfig(n_electrodes=32).validate()))

    def test_wiring_file_matches_the_pilot_sessions(self):
        wiring = load_wiring(WIRING)
        self.assertEqual(wired_sites(wiring), [f"L{i}" for i in range(1, 9)] + [f"R{i}" for i in range(8, 0, -1)])
        meta = ROOT / "data/sessions/session-1-20261005-10000Hz-600mV/meta.json"
        if meta.exists():
            m = json.loads(meta.read_text())
            self.assertEqual(wiring["logical_to_physical"], m["protocol"]["logical_to_physical"])
            self.assertEqual(wiring["channels"], m["mapping"]["channels"])


class StudyDesignTests(unittest.TestCase):
    def setUp(self):
        self.design = ds.load_design(DESIGN)

    def test_hold_follows_the_hardware(self):
        for n, hold in ((16, 2.0 + 208 * 0.099 + 0.5), (8, 2.0 + 40 * 0.099 + 0.5)):
            df = ds.expand(self.design, MeasurementConfig(n_electrodes=n).frame_s)
            self.assertTrue(np.allclose(df[df.frames == 1].hold_s, round(hold, 2)))

    def test_rest_run_is_split_to_fit_the_hold_cap(self):
        df16 = ds.expand(self.design, MeasurementConfig(n_electrodes=16).frame_s)
        self.assertEqual(df16.head(3)[["task", "frames"]].values.tolist(), [["REST", 1]] * 3)
        self.assertEqual(df16.ready_s.iloc[1], 0.0)  # no GET READY between consecutive REST blocks
        df8 = ds.expand(self.design, MeasurementConfig(n_electrodes=8).frame_s)
        self.assertEqual(df8.iloc[0][["task", "frames"]].tolist(), ["REST", 3])

    def test_design_is_complete_reproducible_and_valid(self):
        frame_s = load_measurement(MEASUREMENT).frame_s
        self.assertEqual(ds.validate(self.design, frame_s), [])
        a, b = ds.expand(self.design, frame_s), ds.expand(self.design, frame_s)
        pd.testing.assert_frame_equal(a, b)
        for t in self.design.tasks:
            self.assertEqual((a.task == t.name).sum(), self.design.rounds)
        self.assertEqual((a.task == "REST_CONTROL").sum(), self.design.rounds)
        inner = a[a.kind != "rest"].index
        self.assertTrue(all(a.kind[i - 1] == "rest" and a.kind[i + 1] == "rest" for i in inner))

    def test_invalid_designs_are_explained(self):
        frame_s = MeasurementConfig(n_electrodes=16).frame_s
        too_long = copy.deepcopy(self.design)
        too_long.frames_per_task = 2
        self.assertTrue(any("exceeds the cap" in p for p in ds.validate(too_long, frame_s)))
        too_short = copy.deepcopy(self.design)
        too_short.tasks[0].hold_s = 10.0
        self.assertTrue(any("shorter than" in p for p in ds.validate(too_short, frame_s)))
        self.assertTrue(any("does not fit" in p for p in ds.validate(self.design, MeasurementConfig(n_electrodes=32).frame_s)))

    def test_json_round_trip(self):
        again = ds.StudyDesign(**json.loads(self.design.to_json()))
        self.assertEqual(again.to_json(), self.design.to_json())


class EightElectrodeSessionTests(unittest.TestCase):
    """A synthetic 8-electrode session goes through the whole analysis, reconstruction included."""

    def test_pipeline_runs_with_eight_electrodes(self):
        from app.eit.config import DEFAULTS
        from app.eit.report import run_study
        from test_core import write_session

        tmp = tempfile.TemporaryDirectory()
        raw = Path(tmp.name) / "raw"
        rng = np.random.default_rng(1)
        pattern = 1 + 0.03 * rng.normal(size=40)
        frames = [("T1", "REST", "task", np.ones(40)), ("T2", "SMILE_LEFT", "task", pattern),
                  ("T3", "REST", "task", np.ones(40))]
        write_session(raw / "s8", frames, n_el=8, sites=["L1", "L2", "L3", "L4", "R4", "R3", "R2", "R1"])
        cfg = copy.deepcopy(DEFAULTS)
        cfg.update({"study_id": "eight", "raw_root": str(raw), "out_root": str(Path(tmp.name) / "out"),
                    "sessions": [{"dir": "s8", "label": "8 el"}], "baseline": "bracketing_rest",
                    "config_path": str(raw / "cfg.json"),
                    "outputs": {"report_figures": False, "slide_figures": False, "clean_images": False}})
        out = run_study(cfg, quick=True)
        q = pd.read_csv(out / "tables/qc_summary.csv").iloc[0]
        self.assertEqual((int(q.n_electrodes), int(q.n_measurements)), (8, 40))
        m = pd.read_csv(out / "tables/recon_metrics.csv")
        self.assertEqual(set(m.algorithm), {"BP", "JAC", "GREIT"})
        lat = pd.read_csv(out / "tables/lateralization.csv")
        self.assertEqual(len(lat), 1)
        tmp.cleanup()

    def _run(self, frames, **session):
        from app.eit.config import DEFAULTS
        from app.eit.report import run_study
        from test_core import write_session

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        raw = Path(tmp.name) / "raw"
        write_session(raw / "s", frames, **session)
        cfg = copy.deepcopy(DEFAULTS)
        cfg.update({"study_id": "x", "raw_root": str(raw), "out_root": str(Path(tmp.name) / "out"),
                    "sessions": [{"dir": "s", "label": "x"}], "config_path": str(raw / "cfg.json")})
        return run_study(cfg, quick=True)

    def test_force_distance_different_from_sense_distance(self):
        n = len(make_sequence(16, 2, 1))
        out = self._run([("T1", "REST", "task", np.ones(n)), ("T2", "A", "task", 1.02 * np.ones(n))],
                        distances=(2, 1))
        q = pd.read_csv(out / "tables/qc_summary.csv").iloc[0]
        self.assertEqual((int(q.force_distance), int(q.sense_distance), int(q.recip_pairs)), (2, 1, 0))
        self.assertTrue((out / "tables/recon_metrics.csv").exists())

    def test_site_names_without_left_right(self):
        out = self._run([("T1", "REST", "task", 1.0), ("T2", "A", "task", 1.02)], n_el=8,
                        sites=[f"E{i}" for i in range(8)])
        self.assertFalse((out / "figures/lateralization.png").exists())
        self.assertIn("lateralisation is not available", (out / "README.md").read_text())

    def test_sites_without_a_mirror_do_not_break_lateralisation(self):
        from app.eit.protocol import mirror_pairs
        self.assertEqual(mirror_pairs(std_sequence(8), [f"L{i}" for i in range(1, 9)]), [])


if __name__ == "__main__":
    unittest.main()
