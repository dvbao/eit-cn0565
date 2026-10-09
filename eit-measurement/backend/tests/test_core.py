"""Unit tests for app.eit: protocol, relative change, baseline policies, design. No real data needed."""

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

from app.eit import features as ft
from app.services import protocol_runner as design  # noqa: E402
from app.eit.io import Session  # noqa: E402
from app.eit.protocol import make_sequence, mirror_pairs, side_masks, std_sequence  # noqa: E402

SITES = [f"L{i}" for i in range(1, 9)] + [f"R{i}" for i in range(8, 0, -1)]


def write_session(folder: Path, frames, n_el=16, seed=0, base=None, trial_windows=None, sites=None, distances=(1, 1)):
    """Synthetic live session. frames = [(trial_id, task, state, gain)]: V_frame = base * gain.
    trial_windows = {trial_id: valid} writes a trial_windows.csv; sites = site name per ring index."""
    sites = sites or SITES[:n_el]
    rng = np.random.default_rng(seed)
    seq = make_sequence(n_el, *distances)
    if base is None:
        base = (rng.uniform(60, 400, len(seq)) * np.exp(1j * rng.uniform(-np.pi, np.pi, len(seq))))
    meta = {
        "source": "live", "status": "complete", "settings": {"mode": "live", "frequency_hz": 50000, "amplitude_mvpp": 600},
        "protocol": {"logical_to_physical": list(range(n_el))},
        "mapping": {"channels": [{"index": i, "site": sites[i], "skin_landmark": ""} for i in range(n_el)]},
        "sequence": [[int(a), int(m), int(n), int(b)] for a, b, m, n in seq],
        "origin_perf_counter_ns": 0, "started_utc": "2026-01-01T00:00:00+00:00",
    }
    folder.mkdir(parents=True)
    (folder / "meta.json").write_text(json.dumps(meta))
    pats, frs, evs, t = [], [], [], 1.0
    for fid, (trial, task, state, gain) in enumerate(frames):
        evs.append({"event": "STATE_CUE", "time_s": t})
        t += 2.0
        frs.append({"frame_id": fid, "trial_id": trial, "task": task, "state": state, "start_perf_counter_ns": int(t * 1e9),
                    "end_perf_counter_ns": int((t + len(seq) * 0.1) * 1e9), "duration_s": len(seq) * 0.1,
                    "pattern_count": len(seq), "complete": True})
        v = base * gain
        for k, (a, b, m, n) in enumerate(seq):
            pats.append({"frame_id": fid, "pattern_id": k, "f_plus": a, "s_plus": m, "s_minus": n, "f_minus": b,
                         "real_raw": v[k].real, "imag_raw": v[k].imag, "start_s": t + 0.1 * k,
                         "end_s": t + 0.1 * k + 0.09, "error": np.nan})
        t += len(seq) * 0.1 + 0.5
    evs.append({"event": "SESSION_END", "time_s": t})
    pd.DataFrame(pats).to_csv(folder / "patterns.csv", index=False)
    pd.DataFrame(frs).to_csv(folder / "frames.csv", index=False)
    pd.DataFrame(evs).to_csv(folder / "events.csv", index=False)
    if trial_windows is not None:
        pd.DataFrame([{"trial_id": t, "valid": v} for t, v in trial_windows.items()]).to_csv(
            folder / "trial_windows.csv", index=False)
    return base


class ProtocolTests(unittest.TestCase):
    def test_std_sequence_matches_pyeit(self):
        try:
            import pyeit.eit.protocol as protocol
        except ImportError:
            self.skipTest("pyEIT not installed")
        p = protocol.create(16, 1, 1, "std")
        rows = np.array([(a, b, m, n) for (a, b), ms in zip(p.ex_mat, p.meas_mat) for n, m in ms])
        np.testing.assert_array_equal(std_sequence(16), rows)

    def test_side_masks_and_mirror_pairs(self):
        seq = std_sequence(16)
        left, right = side_masks(seq, SITES)
        self.assertEqual((left.sum(), right.sum()), (30, 30))
        pairs = mirror_pairs(seq, SITES)
        self.assertEqual(len(pairs), 30)
        self.assertTrue(all(left[i] and right[j] for i, j in pairs))


class RelativeChangeTests(unittest.TestCase):
    def test_fixed_gain_and_polarity_cancel(self):
        rest = np.array([2 + 3j, -4 + 1j])
        task = rest * np.array([1.02 + 0.03j, 0.99 - 0.01j])
        gain = np.array([-1j, -2 + 3j])
        np.testing.assert_allclose(ft.relative_change(task, rest), ft.relative_change(task * gain, rest * gain))

    def test_zero_or_nonfinite_reference_rejected(self):
        for bad in (0.0, np.nan, np.inf):
            with self.assertRaises(ValueError):
                ft.relative_change(np.array([1.0]), np.array([bad]))


class BaselinePolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        frames = [("T1", "REST", "task", 1.00), ("T2", "A", "task", 1.10), ("T3", "REST", "task", 1.01),
                  ("T4", "B", "task", 1.20), ("T5", "REST", "task", 1.02)]
        write_session(Path(self.tmp.name) / "s", frames)
        self.s = Session(Path(self.tmp.name) / "s")

    def tearDown(self):
        self.tmp.cleanup()

    def dz(self, policy):
        return {c.task: c.dz for c in ft.changes(self.s, policy)}

    def test_initial_rest(self):
        d = self.dz("initial_rest")
        np.testing.assert_allclose(d["A"], 0.10)
        np.testing.assert_allclose(d["B"], 0.20)

    def test_preceding_rest(self):
        d = self.dz("preceding_rest")
        np.testing.assert_allclose(d["A"], 0.10)
        np.testing.assert_allclose(d["B"], 1.20 / 1.01 - 1)

    def test_bracketing_rest(self):
        d = self.dz("bracketing_rest")
        np.testing.assert_allclose(d["A"], 1.10 / 1.005 - 1)
        np.testing.assert_allclose(d["B"], 1.20 / 1.015 - 1)

    def test_rest_rest_noise_from_consecutive_rest_frames(self):
        from app.eit.qc import qc_summary, rest_rest_noise
        noise = rest_rest_noise(self.s)
        self.assertEqual(noise.kind.tolist(), ["across_task", "across_task"])  # a task separates every rest pair
        np.testing.assert_allclose(noise.median_abs_dz_pct_ge100, [1.0, 100 * (1.02 / 1.01 - 1)])
        summary = qc_summary(self.s, 50.0)
        self.assertEqual((summary["rest_rest_pairs"], summary["rest_across_task_pairs"]), (0, 2))

    def test_adjacent_rest_frames_give_noise_floor(self):
        tmp = tempfile.TemporaryDirectory()
        write_session(Path(tmp.name) / "s2", [("T1", "REST", "task", 1.00), ("T1", "REST", "task", 1.003),
                                               ("T2", "A", "task", 1.10)])
        from app.eit.qc import rest_rest_noise
        noise = rest_rest_noise(Session(Path(tmp.name) / "s2"))
        self.assertEqual(noise.kind.tolist(), ["adjacent"])
        np.testing.assert_allclose(noise.median_abs_dz_pct_ge100, [0.3])
        # a pure gain change lies along the rest phasor: in-phase RMS = complex RMS
        np.testing.assert_allclose(noise.rms_dv_inphase_counts, noise.rms_dv_counts)
        tmp.cleanup()

    def test_rest_noise_table_has_columns_when_empty(self):
        from app.eit.qc import REST_NOISE_COLUMNS, rest_rest_noise
        tmp = tempfile.TemporaryDirectory()
        write_session(Path(tmp.name) / "s3", [("T1", "REST", "task", 1.0), ("T2", "A", "task", 1.1)])
        noise = rest_rest_noise(Session(Path(tmp.name) / "s3"))
        self.assertEqual((len(noise), noise.columns.tolist()), (0, REST_NOISE_COLUMNS))
        tmp.cleanup()

    def test_rest_pairs_around_a_control_block(self):
        from app.eit.qc import rest_rest_noise
        tmp = tempfile.TemporaryDirectory()
        write_session(Path(tmp.name) / "s4", [("T1", "REST", "task", 1.0), ("T2", "REST_CONTROL", "task", 1.0),
                                               ("T3", "REST", "task", 1.0), ("T4", "A", "task", 1.1),
                                               ("T5", "REST", "task", 1.0)])
        self.assertEqual(rest_rest_noise(Session(Path(tmp.name) / "s4")).kind.tolist(),
                         ["across_control", "across_task"])
        tmp.cleanup()

    def test_bracketing_time_uses_the_same_weights_as_the_reference(self):
        tmp = tempfile.TemporaryDirectory()
        write_session(Path(tmp.name) / "s5", [("T1", "REST", "task", 1.0), ("T2", "REST", "task", 1.0),
                                               ("T3", "A", "task", 1.1), ("T4", "REST", "task", 1.0)])
        s = Session(Path(tmp.name) / "s5")
        (c,) = ft.changes(s, "bracketing_rest")
        mid = s.frames.set_index("frame_id").mid_s
        expected = mid[2] - ((mid[0] + mid[1]) / 2 + mid[3]) / 2  # mean of the two block means
        self.assertAlmostEqual(c.t_since_ref_s, expected)
        (k1,) = ft.changes(s, "preceding_rest", rest_k=1)
        self.assertEqual(k1.ref_frames, [1])  # only the rest frame closest to the task
        tmp.cleanup()

    def test_trials_marked_invalid_are_excluded(self):
        tmp = tempfile.TemporaryDirectory()
        write_session(Path(tmp.name) / "s6", [("T1", "REST", "task", 1.0), ("T2", "A", "task", 1.1),
                                               ("T3", "REST", "task", 1.0), ("T4", "B", "task", 1.2)],
                      trial_windows={"T1": True, "T2": False, "T3": True, "T4": True})
        s = Session(Path(tmp.name) / "s6")
        self.assertEqual([c.task for c in ft.changes(s, "preceding_rest")], ["B"])
        self.assertEqual(s.task_frames, [3])
        tmp.cleanup()

    def test_invalid_rest_frame_between_rest_frames_keeps_them_adjacent(self):
        from app.eit.qc import rest_rest_noise
        tmp = tempfile.TemporaryDirectory()
        write_session(Path(tmp.name) / "s7", [("T1", "REST", "task", 1.0), ("T2", "REST", "task", 1.0),
                                               ("T3", "REST", "task", 1.0), ("T4", "A", "task", 1.1)],
                      trial_windows={"T1": True, "T2": False, "T3": True, "T4": True})
        self.assertEqual(rest_rest_noise(Session(Path(tmp.name) / "s7")).kind.tolist(), ["adjacent"])
        tmp.cleanup()


class DriveGainTests(unittest.TestCase):
    def test_gain_fit_is_supported_only_for_real_per_drive_gains(self):
        from app.eit.qc import qc_summary
        seq = std_sequence(16)
        rng = np.random.default_rng(3)
        base = rng.uniform(60, 400, len(seq)) * np.exp(1j * rng.uniform(-np.pi, np.pi, len(seq)))
        index = {tuple(r): i for i, r in enumerate(seq)}
        for i, (a, b, m, n) in enumerate(seq):  # make the data reciprocal
            k = index.get((m, n, a, b))
            if k is not None and k > i:
                base[k] = base[i]
        gain = np.exp(rng.normal(0, 0.15, 16))[seq[:, 0]]  # one current per drive pair
        tmp = tempfile.TemporaryDirectory()
        noisy = base * np.exp(rng.normal(0, 0.15, len(seq)) + 1j * rng.normal(0, 0.15, len(seq)))
        write_session(Path(tmp.name) / "g", [("T1", "REST", "task", gain)], base=base)
        write_session(Path(tmp.name) / "n", [("T1", "REST", "task", 1.0)], base=noisy)
        with_gain = qc_summary(Session(Path(tmp.name) / "g"), 50.0)
        no_gain = qc_summary(Session(Path(tmp.name) / "n"), 50.0)
        self.assertLess(with_gain["recip_err_after_drive_gain_fit_pct"], 1e-6)
        self.assertTrue(with_gain["drive_gain_fit_supported"])
        self.assertFalse(no_gain["drive_gain_fit_supported"])
        self.assertGreater(no_gain["recip_fit_ratio"], no_gain["recip_fit_null_ratio_p05"])
        tmp.cleanup()


class DesignTests(unittest.TestCase):
    def test_seeded_design_is_reproducible_and_complete(self):
        tasks = ["SMILE_LEFT", "SMILE_RIGHT", "PUFF_BOTH"]
        a = design.make_design(tasks, rounds=2, seed=7)
        b = design.make_design(tasks, rounds=2, seed=7)
        c = design.make_design(tasks, rounds=2, seed=8)
        pd.testing.assert_frame_equal(a, b)
        self.assertFalse(a.task.tolist() == c.task.tolist())
        for t in tasks + [design.CONTROL]:
            self.assertEqual((a.task == t).sum(), 2)
        not_rest = a[a.task != "REST"].index
        self.assertTrue(all(a.loc[i - 1, "task"] == "REST" and a.loc[i + 1, "task"] == "REST" for i in not_rest))
        self.assertTrue((a.seed == 7).all())  # the operator sheet (.csv) carries its seed


if __name__ == "__main__":
    unittest.main()
