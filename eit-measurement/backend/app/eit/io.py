"""Read one CN0565 pilot session folder (output of the acquisition software) without modifying it."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .protocol import ring_distances

REQUIRED_FILES = ("meta.json", "patterns.csv", "frames.csv", "events.csv")
REST_STATES = {"rest", "pre_rest", "post_rest", "baseline"}


class Session:
    """One recording session: metadata, per-frame complex vectors and frame/event tables.

    Attributes
    ----------
    name, path, label : folder name, folder path, short label used in tables/figures
    meta : parsed meta.json
    freq, amp : configured excitation frequency (Hz) and amplitude command (firmware units)
    n_el, n_pat : electrode and measurement counts
    seq : (n_pat, 4) logical (A=F+, B=F-, M=S+, N=S-) electrode indices on the ring
    ring_distances : (force_distance, sense_distance) if seq is a regular ring protocol, else None
    sites : site name of each logical ring index, e.g. ['L1', ..., 'L8', 'R8', ..., 'R1']
    frames : one row per frame: frame_id, trial_id, task, state, is_rest, valid, start_s, end_s, mid_s
    invalid_trials : trial_ids marked valid=False in trial_windows.csv (excluded from the analysis)
    V : frame_id -> complex vector (n_pat,) of raw DFT counts (real_raw + j imag_raw)
    T : frame_id -> mid time (s) of every measurement
    """

    def __init__(self, path, label=None, rest_label: str = "REST"):
        self.path = Path(path)
        self.name = self.path.name
        missing = [f for f in REQUIRED_FILES if not (self.path / f).exists()]
        if missing:
            raise FileNotFoundError(f"{self.path}: missing {missing}")
        self.meta = json.loads((self.path / "meta.json").read_text())
        source = self.meta.get("source")
        mode = self.meta.get("settings", {}).get("mode")
        if source == "mock" or mode == "mock" or source != "live":
            raise ValueError(f"{self.name}: source={source!r}, mode={mode!r}; only live recordings are analysed")
        self.rest_label = rest_label
        settings = self.meta["settings"]
        self.freq = int(settings["frequency_hz"])
        self.amp = float(settings.get("amplitude_mvpp", np.nan))
        self.label = label or f"{self.freq // 1000} kHz"

        self.patterns = pd.read_csv(self.path / "patterns.csv")
        self.events = pd.read_csv(self.path / "events.csv")
        checks = self.path / "configuration_checks.csv"
        self.checks = pd.read_csv(checks) if checks.exists() else None
        windows = self.path / "trial_windows.csv"
        self.trial_windows = pd.read_csv(windows) if windows.exists() else None

        l2p = self.meta["protocol"]["logical_to_physical"]
        self.n_el = len(l2p)
        p2l = {phys: i for i, phys in enumerate(l2p)}
        phys_site = {c["index"]: c["site"] for c in self.meta["mapping"]["channels"]}
        self.sites = [phys_site[l2p[i]] for i in range(self.n_el)]
        self.landmarks = {c["site"]: c.get("skin_landmark", "") for c in self.meta["mapping"]["channels"]}
        # meta "sequence" rows are (F+, S+, S-, F-) physical X lines -> logical (A, B, M, N)
        self.seq = np.array([(p2l[fp], p2l[fm], p2l[sp], p2l[sm]) for fp, sp, sm, fm in self.meta["sequence"]])
        self.n_pat = len(self.seq)
        self.ring_distances = ring_distances(self.seq, self.n_el)

        origin = self.meta["origin_perf_counter_ns"]
        frames = pd.read_csv(self.path / "frames.csv").sort_values("frame_id").reset_index(drop=True)
        frames["start_s"] = (frames["start_perf_counter_ns"] - origin) / 1e9
        frames["end_s"] = (frames["end_perf_counter_ns"] - origin) / 1e9
        frames["mid_s"] = (frames["start_s"] + frames["end_s"]) / 2
        state = frames["state"].astype(str).str.lower()
        frames["is_rest"] = (frames["task"].astype(str) == rest_label) | state.isin(REST_STATES)
        self.invalid_trials = set()
        if self.trial_windows is not None and "valid" in self.trial_windows:
            ok = self.trial_windows["valid"].astype(str).str.strip().str.lower().isin(("true", "1", "yes"))
            self.invalid_trials = set(self.trial_windows.loc[~ok, "trial_id"].astype(str))
        frames["valid"] = ~frames["trial_id"].astype(str).isin(self.invalid_trials)
        self.frames = frames

        self.V, self.T = {}, {}
        for fid, g in self.patterns.groupby("frame_id"):
            g = g.sort_values("pattern_id")
            self.V[int(fid)] = (g["real_raw"] + 1j * g["imag_raw"]).to_numpy()
            self.T[int(fid)] = ((g["start_s"] + g["end_s"]) / 2).to_numpy()

    # -- convenience ---------------------------------------------------------------
    @property
    def rest_frames(self) -> list:
        return [int(f) for f in self.frames.loc[self.frames.is_rest & self.frames.valid, "frame_id"]]

    @property
    def task_frames(self) -> list:
        return [int(f) for f in self.frames.loc[~self.frames.is_rest & self.frames.valid, "frame_id"]]

    def rest_mean(self) -> np.ndarray:
        """Complex mean of all rest frames: defines which channels are strong in this session."""
        if not self.rest_frames:
            raise ValueError(f"{self.name}: no rest frame")
        return np.mean([self.V[f] for f in self.rest_frames], axis=0)

    def frame(self, frame_id: int) -> pd.Series:
        return self.frames.set_index("frame_id").loc[frame_id]

    def protocol_is_std(self) -> bool:
        """Adjacent drive and adjacent sense (force_distance = sense_distance = 1)."""
        return self.ring_distances == (1, 1)


def sha256_tree(path) -> dict:
    """SHA-256 of every file in a raw session folder (provenance for the manifest)."""
    path = Path(path)
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(path.iterdir()) if p.is_file()}
