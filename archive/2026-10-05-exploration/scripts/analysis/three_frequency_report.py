r"""Cross-frequency report for the 10 / 50 / 80 kHz facial pilot sessions (2026-10-05).

Reads three live `state_sequence` recordings (REST + six tasks, one 208-pattern
frame each) and writes tables/figures to ``data/processed/pilot/``. Raw folders
are only read, never modified.

Implements the handoff `chatbot-handoff-2026-10-05-three-frequency-analysis.md`
without ``scripts/cn0565_pilot.py`` (that module lives on the Windows
acquisition PC and is not in this repository). Every feature is therefore
re-implemented here and named explicitly.

Key definitions (all phase/gain/polarity invariant within a session):

* ``dz = (v_task - v_REST) / v_REST`` per pattern (complex relative change);
  ``|dz|`` in %; ``Re(dz)`` ~ relative magnitude change, ``Im(dz)`` ~ phase
  change in rad.
* *strong* pattern: ``|v_REST| >= 50`` counts in that session (the threshold
  that reproduces the handoff numbers). Noise model: 2 counts per pattern for a
  frame-to-frame difference (REST->REST RMS 1.2-2.9 counts, separate session
  ``session-20261005T040628-a0a874``, 10 kHz, amplitude 800).
* Task labels are ``cue_assumed``: no video/EMG; session 1 additionally has an
  operator-reported ``trial_windows.csv``, sessions 2 and 3 do not.

The reconstruction section is an EXPLORATORY 2-D disk projection (pyEIT FEM,
16 point electrodes equally spaced in ring order L1..L8, R8..R1). It is not a
facial or anatomical image.

macOS/Linux:  .venv-sim/bin/python scripts/analysis/three_frequency_report.py
Windows:      .\cn0565-env\Scripts\python.exe scripts\analysis\three_frequency_report.py
"""

from __future__ import annotations

import argparse
import itertools
import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, LogNorm, TwoSlopeNorm  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SESSION_NAMES = (
    "session-1-20261005-10000Hz-600mV",
    "session-2-20261005-50000Hz-600mV",
    "session-3-20261005-80000Hz-600mV",
)
TASKS = ("SMILE_LEFT", "SMILE_RIGHT", "SMILE_BOTH", "PUFF_LEFT", "PUFF_RIGHT", "PUFF_BOTH")
STATES = ("REST",) + TASKS
N_EL = 16
N_PAT = 208
STRONG_COUNTS = 50.0
NOISE_COUNTS = 2.0
NOISE_COUNTS_MAX = 2.9
REL_THRESHOLDS_PCT = (1.0, 2.0)

# Reconstruction hyper-parameters (exploratory; see report).
RECON_H0 = 0.07
RECON_P = 0.5
RECON_LAMBDA_FRAC = 0.1
RECON_REL_FLOOR = 0.005
RECON_NOISE_DRAWS = 200

# Colours: validated categorical slots 1-3 (all-pairs) for frequency, a
# separate validated pair for L/R, blue sequential ramp, blue<->red diverging.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
MASK = "#d9d8d3"
FREQ_COLORS = {10000: "#2a78d6", 50000: "#eb6834", 80000: "#1baf7a"}
SIDE_COLORS = {"L": "#4a3aa7", "R": "#008300"}
SEQ = LinearSegmentedColormap.from_list(
    "seq_blue",
    ["#f4f8fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
)
SEQ.set_bad(MASK)
DIV = LinearSegmentedColormap.from_list(
    "div_blue_red",
    ["#0d366b", "#2a78d6", "#9ec5f4", "#f0efec", "#f3b0ab", "#e34948", "#8f2322"],
)
DIV.set_bad(MASK)

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "text.color": INK,
        "axes.labelcolor": INK2,
        "axes.edgecolor": GRID,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


# --------------------------------------------------------------------------
# Loading and protocol geometry
# --------------------------------------------------------------------------


def resolve_session(name: str) -> Path:
    for candidate in (REPO / "data/raw/pilot" / name, REPO / name, Path(name)):
        if (candidate / "meta.json").exists():
            return candidate
    raise FileNotFoundError(f"session folder not found: {name}")


def pyeit_std_sequence() -> np.ndarray:
    """(A, B, M, N) logical rows of pyEIT protocol.create(16, 1, 1, 'std').

    Written out explicitly so loading does not depend on pyEIT. pyEIT stores
    pairs as [N, M] and computes V[N] - V[M]; only relative changes are used
    here, so that sign convention cancels.
    """
    rows = []
    for a in range(N_EL):
        b = (a + 1) % N_EL
        for m in range(N_EL):
            n = (m + 1) % N_EL
            if len({a, b} & {m, n}) == 0:
                rows.append((a, b, m, n))
    return np.array(rows)


def load_session(path: Path) -> dict:
    meta = json.loads((path / "meta.json").read_text())
    if meta.get("source") == "mock" or meta.get("settings", {}).get("mode") != "live":
        raise ValueError(f"{path.name}: not a live recording")
    pats = pd.read_csv(path / "patterns.csv")
    frames = pd.read_csv(path / "frames.csv")
    events = pd.read_csv(path / "events.csv")
    checks = pd.read_csv(path / "configuration_checks.csv")
    tw_path = path / "trial_windows.csv"
    trial_windows = pd.read_csv(tw_path) if tw_path.exists() else None

    l2p = meta["protocol"]["logical_to_physical"]
    p2l = {phys: i for i, phys in enumerate(l2p)}
    phys_site = {c["index"]: c["site"] for c in meta["mapping"]["channels"]}
    sites = [phys_site[l2p[i]] for i in range(N_EL)]
    landmarks = {c["site"]: c["skin_landmark"] for c in meta["mapping"]["channels"]}
    # meta sequence is (F+, S+, S-, F-) in physical X lines -> logical (A=F+, B=F-, M=S+, N=S-)
    seq = np.array([(p2l[fp], p2l[fm], p2l[sp], p2l[sm]) for fp, sp, sm, fm in meta["sequence"]])

    v, t_mid = {}, {}
    for state, g in pats.groupby("task"):
        g = g.sort_values("pattern_id")
        v[state] = (g["real_raw"] + 1j * g["imag_raw"]).to_numpy()
        t_mid[state] = ((g["start_s"] + g["end_s"]) / 2).to_numpy()
    return {
        "name": path.name,
        "path": path,
        "meta": meta,
        "freq": int(meta["settings"]["frequency_hz"]),
        "amp": float(meta["settings"]["amplitude_mvpp"]),
        "patterns": pats,
        "frames": frames,
        "events": events,
        "checks": checks,
        "trial_windows": trial_windows,
        "seq": seq,
        "sites": sites,
        "landmarks": landmarks,
        "v": v,
        "t_mid": t_mid,
    }


def pair_label(sites, i):
    return f"{sites[i]}-{sites[(i + 1) % N_EL]}"


def dz_of(s: dict, task: str) -> np.ndarray:
    v0 = s["v"]["REST"]
    return (s["v"][task] - v0) / v0


def strong_mask(s: dict) -> np.ndarray:
    return np.abs(s["v"]["REST"]) >= STRONG_COUNTS


def to_matrix(values: np.ndarray, seq: np.ndarray) -> np.ndarray:
    """208 values -> 16 drive pairs x 16 sense-pair positions (3 NaN per row)."""
    mat = np.full((N_EL, N_EL), np.nan)
    for k, (a, _, m, _) in enumerate(seq):
        mat[a, m] = values[k]
    return mat


# --------------------------------------------------------------------------
# QC, timing, reciprocity
# --------------------------------------------------------------------------


def reciprocity(s: dict, state: str, fit_drive_gain: bool) -> tuple[float, float, np.ndarray]:
    """Median |v_AB,MN / v_MN,AB - 1| over reciprocal pairs where both are strong.

    With ``fit_drive_gain`` a per-drive complex gain c_g is removed first
    (ln v_i - ln v_k = c_g(i) - c_g(k)); this models unknown drive current in
    voltage mode. Returns (median before, median after, ln|gain| per drive).
    """
    seq = s["seq"]
    index = {tuple(r): i for i, r in enumerate(seq)}
    v, v0 = s["v"][state], s["v"]["REST"]
    rows, y = [], []
    for i, (a, b, m, n) in enumerate(seq):
        k = index.get((m, n, a, b))
        if k is None or k <= i or min(abs(v0[i]), abs(v0[k])) < STRONG_COUNTS:
            continue
        row = np.zeros(N_EL)
        row[a] += 1
        row[m] -= 1
        rows.append(row)
        y.append(np.log(v[i] / v[k]))
    a_mat, y = np.array(rows), np.array(y)
    before = float(np.median(np.abs(np.exp(y) - 1)))
    if not fit_drive_gain:
        return before, np.nan, np.full(N_EL, np.nan)
    a_aug = np.vstack([a_mat, np.ones(N_EL)])
    c_re = np.linalg.lstsq(a_aug, np.r_[y.real, 0], rcond=None)[0]
    c_im = np.linalg.lstsq(a_aug, np.r_[y.imag, 0], rcond=None)[0]
    resid = y - (a_mat @ c_re + 1j * (a_mat @ c_im))
    return before, float(np.median(np.abs(np.exp(resid) - 1))), c_re


def audit(s: dict) -> dict:
    p, meta = s["patterns"], s["meta"]
    per_frame = p.groupby("frame_id")["pattern_id"].agg(lambda x: sorted(x) == list(range(N_PAT)))
    csv_seq = (
        p[p.frame_id == 0].sort_values("pattern_id")[["f_plus", "s_plus", "s_minus", "f_minus"]].to_numpy()
    )
    chk = s["checks"]
    within = []
    for _, fr in s["frames"].iterrows():
        rows = p[p.frame_id == fr.frame_id]
        within.append(bool(np.all(np.diff(rows.sort_values("pattern_id")["start_s"]) > 0)))
    return {
        "status_complete": meta.get("status") == "complete",
        "source_live": meta.get("source") == "live",
        "frames_7x208": len(s["frames"]) == 7 and bool(per_frame.all()) and len(p) == 7 * N_PAT,
        "no_pattern_errors": int(p["error"].notna().sum()) == 0,
        "csv_matches_meta_sequence": bool(np.array_equal(csv_seq, np.array(meta["sequence"]))),
        "sequence_equals_pyeit_std": bool(np.array_equal(s["seq"], pyeit_std_sequence())),
        "pattern_times_monotonic": all(within),
        "hz_constant": bool((chk["frequency_hz"] == s["freq"]).all()),
        "amp_constant": bool((chk["amplitude_mvpp"] == s["amp"]).all()),
        "voltage_mode": bool((~chk["magnitude_mode"].astype(bool)).all() and (~chk["impedance_mode"].astype(bool)).all()),
    }


def timing(s: dict) -> pd.DataFrame:
    ev, fr, meta = s["events"], s["frames"], s["meta"]
    origin = meta["origin_perf_counter_ns"]
    cues = ev[ev.event == "STATE_CUE"].set_index("trial_id")["time_s"]
    end_t = ev[ev.event == "SESSION_END"]["time_s"].iloc[0]
    phase_start = ev[ev.event == "PHASE_START"].set_index("trial_id")["time_s"]
    trial_ids = list(cues.index)
    rest_mid = None
    out = []
    for k, tid in enumerate(trial_ids):
        row = fr[fr.trial_id == tid].iloc[0]
        f0 = (row.start_perf_counter_ns - origin) / 1e9
        f1 = (row.end_perf_counter_ns - origin) / 1e9
        nxt = cues.iloc[k + 1] if k + 1 < len(trial_ids) else end_t
        mid = (f0 + f1) / 2
        if row.task == "REST":
            rest_mid = mid
        out.append(
            {
                "session": s["name"],
                "freq_hz": s["freq"],
                "trial_id": tid,
                "task": row.task,
                "cue_s": cues[tid],
                "settle_s": phase_start[tid] - cues[tid],
                "frame_start_s": f0,
                "frame_end_s": f1,
                "frame_duration_s": row.duration_s,
                "next_cue_s": nxt,
                "hold_s": nxt - cues[tid],
                "frame_inside_hold": bool(f0 >= cues[tid] and f1 <= nxt),
                "slack_after_frame_s": nxt - f1,
                "t_since_rest_mid_s": mid - rest_mid,
            }
        )
    return pd.DataFrame(out)


def table_t1(sessions, timings) -> pd.DataFrame:
    rows = []
    for s in sessions:
        a = audit(s)
        tm = timings[s["name"]]
        v0 = s["v"]["REST"]
        rec_before, rec_after, _ = reciprocity(s, "REST", True)
        tw = s["trial_windows"]
        rows.append(
            {
                "session": s["name"],
                "freq_hz": s["freq"],
                "amplitude_cmd": s["amp"],
                "started_utc": s["meta"]["started_utc"],
                "audit_pass": all(a.values()),
                **a,
                "frames_inside_hold": f"{int(tm.frame_inside_hold.sum())}/{len(tm)}",
                "settle_s_median": tm.settle_s.median(),
                "frame_s_median": tm.frame_duration_s.median(),
                "hold_task_s_median": tm[tm.task != "REST"].hold_s.median(),
                "last_task_after_rest_s": tm.t_since_rest_mid_s.max(),
                "rest_abs_median_counts": float(np.median(np.abs(v0))),
                "rest_n_ge_50": int((np.abs(v0) >= 50).sum()),
                "rest_n_ge_100": int((np.abs(v0) >= 100).sum()),
                "rest_phase_median_deg": float(np.degrees(np.median(np.angle(v0)))),
                "recip_err_strong_median_pct": 100 * rec_before,
                "recip_err_after_drive_gain_fit_pct": 100 * rec_after,
                "trial_windows": "operator_reported" if tw is not None else "MISSING (cue_assumed)",
                "label_mode": "cue_assumed",
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------


def side_masks(seq: np.ndarray):
    left = np.all(seq <= 7, axis=1)
    right = np.all(seq >= 8, axis=1)
    return left, right


def mirror_pairs(seq: np.ndarray):
    """(i_left, i_right) with the right pattern the L<->R mirror (i -> 15-i)."""
    index = {(frozenset(r[:2]), frozenset(r[2:])): k for k, r in enumerate(seq)}
    left, _ = side_masks(seq)
    pairs = []
    for i in np.flatnonzero(left):
        a, b, m, n = (N_EL - 1 - x for x in seq[i])
        pairs.append((i, index[(frozenset((a, b)), frozenset((m, n)))]))
    return pairs


def session_pattern_table(s: dict, timings: pd.DataFrame) -> pd.DataFrame:
    seq, sites, v0 = s["seq"], s["sites"], s["v"]["REST"]
    strong = strong_mask(s)
    rows = []
    for task in TASKS:
        dz = dz_of(s, task)
        f0 = timings.set_index("task").loc[task, "frame_start_s"]
        for k in range(N_PAT):
            a, b, m, n = seq[k]
            rows.append(
                {
                    "task": task,
                    "pattern_id": k,
                    "drive_pair": f"{sites[a]}->{sites[b]}",
                    "sense_pair": f"{sites[m]}->{sites[n]}",
                    "rest_abs_counts": abs(v0[k]),
                    "strong": bool(strong[k]),
                    "dz_abs_pct": 100 * abs(dz[k]),
                    "dz_re_pct": 100 * dz[k].real,
                    "dz_im_pct": 100 * dz[k].imag,
                    "dv_abs_counts": abs(s["v"][task][k] - v0[k]),
                    "t_after_frame_start_s": s["t_mid"][task][k] - f0,
                }
            )
    return pd.DataFrame(rows)


def table_t2(sessions, timings) -> pd.DataFrame:
    rows = []
    for s in sessions:
        v0, strong = s["v"]["REST"], strong_mask(s)
        tm = timings[s["name"]].set_index("task")
        for task in TASKS:
            dz = dz_of(s, task)
            dv = np.abs(s["v"][task] - v0)
            a = 100 * np.abs(dz[strong])
            rows.append(
                {
                    "session": s["name"],
                    "freq_hz": s["freq"],
                    "task": task,
                    "t_since_rest_s": tm.loc[task, "t_since_rest_mid_s"],
                    "rms_dv_counts": float(np.sqrt(np.mean(dv**2))),
                    "n_strong": int(strong.sum()),
                    "median_abs_dz_pct_strong": float(np.median(a)),
                    "p90_abs_dz_pct_strong": float(np.percentile(a, 90)),
                    "median_abs_dz_pct_ge100": float(np.median(100 * np.abs(dz[np.abs(v0) >= 100]))),
                    "median_re_dz_pct_strong": float(np.median(100 * dz[strong].real)),
                    "median_phase_change_deg_strong": float(np.degrees(np.median(np.angle(1 + dz[strong])))),
                    **{
                        f"n_strong_gt_{t:g}pct": int((a > t).sum()) for t in REL_THRESHOLDS_PCT
                    },
                    "pct_strong_gt_2pct": float(100 * np.mean(a > 2.0)),
                    "n_all_dv_gt_3x2p9_counts": int((dv > 3 * NOISE_COUNTS_MAX).sum()),
                }
            )
    return pd.DataFrame(rows)


def table_t3(sessions, timings) -> pd.DataFrame:
    rows = []
    for s in sessions:
        seq, strong = s["seq"], strong_mask(s)
        left, right = side_masks(seq)
        pairs = [(i, j) for i, j in mirror_pairs(seq) if strong[i] and strong[j]]
        f0 = timings[s["name"]].set_index("task")["frame_start_s"]
        for task in TASKS:
            d = 100 * np.abs(dz_of(s, task))
            lv, rv = np.median(d[left & strong]), np.median(d[right & strong])
            paired = np.array([d[i] - d[j] for i, j in pairs])
            t = s["t_mid"][task] - f0[task]
            rows.append(
                {
                    "session": s["name"],
                    "freq_hz": s["freq"],
                    "task": task,
                    "n_left_strong": int((left & strong).sum()),
                    "n_right_strong": int((right & strong).sum()),
                    "L_median_abs_dz_pct": lv,
                    "R_median_abs_dz_pct": rv,
                    "L_minus_R_pctpt": lv - rv,
                    "LI": (lv - rv) / (lv + rv),
                    "mirror_pairs_both_strong": len(pairs),
                    "mirror_median_L_minus_R_pctpt": float(np.median(paired)),
                    "mirror_n_L_gt_R": int((paired > 0).sum()),
                    "t_left_patterns_mean_s": float(t[left].mean()),
                    "t_right_patterns_mean_s": float(t[right].mean()),
                }
            )
    return pd.DataFrame(rows)


def feature_vector(s: dict, task: str, sel: np.ndarray) -> np.ndarray:
    dz = dz_of(s, task)[sel]
    return np.r_[dz.real, dz.imag]


def common_strong(sessions) -> np.ndarray:
    return np.all([strong_mask(s) for s in sessions], axis=0)


def table_t4(sessions) -> pd.DataFrame:
    sel = common_strong(sessions)
    rows = []
    for task in TASKS:
        for s1, s2 in itertools.combinations(sessions, 2):
            same = np.corrcoef(feature_vector(s1, task, sel), feature_vector(s2, task, sel))[0, 1]
            other = [
                np.corrcoef(feature_vector(s1, task, sel), feature_vector(s2, t2, sel))[0, 1]
                for t2 in TASKS
                if t2 != task
            ]
            all_sel = np.ones(N_PAT, bool)
            same_all = np.corrcoef(feature_vector(s1, task, all_sel), feature_vector(s2, task, all_sel))[0, 1]
            rows.append(
                {
                    "task": task,
                    "freq_a_hz": s1["freq"],
                    "freq_b_hz": s2["freq"],
                    "r_same_task_common_strong": same,
                    "r_other_tasks_mean": float(np.mean(other)),
                    "r_other_tasks_max": float(np.max(other)),
                    "r_same_task_all_208": same_all,
                    "n_patterns": int(sel.sum()),
                }
            )
    return pd.DataFrame(rows)


def table_t8_additivity(sessions) -> pd.DataFrame:
    """Least squares dz_BOTH = a dz_LEFT + b dz_RIGHT on common strong patterns."""
    sel = common_strong(sessions)
    rows = []
    for s in sessions:
        for kind in ("SMILE", "PUFF"):
            y = feature_vector(s, f"{kind}_BOTH", sel)
            x = np.c_[feature_vector(s, f"{kind}_LEFT", sel), feature_vector(s, f"{kind}_RIGHT", sel)]
            coef = np.linalg.lstsq(x, y, rcond=None)[0]
            resid = y - x @ coef
            rows.append(
                {
                    "session": s["name"],
                    "freq_hz": s["freq"],
                    "task": kind,
                    "a_left": coef[0],
                    "b_right": coef[1],
                    "r2": 1 - np.sum(resid**2) / np.sum((y - y.mean()) ** 2),
                    "r_left_right": np.corrcoef(x[:, 0], x[:, 1])[0, 1],
                    "n_patterns": int(sel.sum()),
                }
            )
    return pd.DataFrame(rows)


def loso(sessions) -> dict:
    """Leave-one-session-out nearest centroid on correlation of dz features."""
    sel = common_strong(sessions)
    feats = {(s["freq"], t): feature_vector(s, t, sel) for s in sessions for t in TASKS}
    freqs = [s["freq"] for s in sessions]

    def accuracy(label_perm):
        conf = np.zeros((len(TASKS), len(TASKS)), int)
        for test in freqs:
            train = [f for f in freqs if f != test]
            cents = [np.mean([feats[(f, label_perm[f][t])] for f in train], axis=0) for t in TASKS]
            for ti, t in enumerate(TASKS):
                r = [np.corrcoef(feats[(test, t)], c)[0, 1] for c in cents]
                conf[ti, int(np.argmax(r))] += 1
        return conf

    identity = {f: {t: t for t in TASKS} for f in freqs}
    conf = accuracy(identity)
    acc = np.trace(conf) / conf.sum()
    rng = np.random.default_rng(0)
    null = []
    for _ in range(2000):
        perm = {f: dict(zip(TASKS, rng.permutation(TASKS))) for f in freqs}
        c = accuracy(perm)
        null.append(np.trace(c) / c.sum())
    null = np.array(null)
    return {
        "confusion": conf,
        "accuracy": float(acc),
        "chance": 1 / len(TASKS),
        "perm_p": float((np.sum(null >= acc) + 1) / (len(null) + 1)),
        "n_patterns": int(sel.sum()),
    }


def involvement(s: dict, task: str) -> np.ndarray:
    """Mean |dz| (%) of strong patterns that use each cup in any role."""
    d = 100 * np.abs(dz_of(s, task))
    strong = strong_mask(s)
    out = np.full(N_EL, np.nan)
    for e in range(N_EL):
        use = strong & np.any(s["seq"] == e, axis=1)
        if use.any():
            out[e] = d[use].mean()
    return out


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------


def freq_label(f):
    return f"{f // 1000} kHz"


def save(fig, path: Path):
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_timeline(sessions, timings, out):
    fig, ax = plt.subplots(figsize=(11, 3.2))
    for row, s in enumerate(sessions):
        tm = timings[s["name"]]
        y = len(sessions) - 1 - row
        for _, r in tm.iterrows():
            ax.barh(y, r.next_cue_s - r.cue_s, left=r.cue_s, height=0.7, color=GRID, edgecolor=SURFACE, lw=2)
            ax.barh(
                y, r.frame_end_s - r.frame_start_s, left=r.frame_start_s, height=0.36,
                color=FREQ_COLORS[s["freq"]], edgecolor=SURFACE, lw=1,
            )
            ax.text((r.cue_s + r.next_cue_s) / 2, y + 0.42, r.task.replace("_", " ").title(), ha="center",
                    va="bottom", fontsize=6.5, color=INK2)
    ax.set_yticks(range(len(sessions)))
    ax.set_yticklabels([freq_label(s["freq"]) for s in reversed(sessions)])
    ax.set_xlabel("Time from session start (s)")
    ax.set_ylim(-0.6, len(sessions) - 0.1)
    ax.set_title("F1  Timeline: state hold (grey, cue to next cue) and the single 208-pattern frame (colour)", loc="left")
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    save(fig, out / "F1_timeline.png")


def matrix_axes(ax, sites, title, label_every=1):
    labels = [pair_label(sites, i) for i in range(N_EL)]
    ax.set_xticks(range(N_EL))
    ax.set_xticklabels(labels, rotation=90, fontsize=5.5)
    ax.set_yticks(range(N_EL))
    ax.set_yticklabels(labels, fontsize=5.5)
    ax.set_xlabel("Sense pair (S+ - S-)", fontsize=7)
    ax.set_ylabel("Drive pair (F+ -> F-)", fontsize=7)
    ax.set_title(title, fontsize=8.5)
    for sp in ax.spines.values():
        sp.set_visible(False)


def fig_baseline(sessions, out):
    sites = sessions[0]["sites"]
    fig, axes = plt.subplots(3, 3, figsize=(13, 13), constrained_layout=True)
    absmax = max(np.abs(s["v"]["REST"]).max() for s in sessions)
    for c, s in enumerate(sessions):
        mat = to_matrix(np.abs(s["v"]["REST"]), s["seq"])
        im = axes[0, c].imshow(np.ma.masked_invalid(mat), cmap=SEQ, norm=LogNorm(1, absmax))
        matrix_axes(axes[0, c], sites, f"|v_REST| (counts, log) - {freq_label(s['freq'])}")
    fig.colorbar(im, ax=axes[0, :], shrink=0.7, label="|v_REST| counts")
    base = sessions[0]
    for c, s in enumerate(sessions[1:]):
        ratio = np.log2(np.abs(s["v"]["REST"]) / np.abs(base["v"]["REST"]))
        im = axes[1, c].imshow(np.ma.masked_invalid(to_matrix(ratio, s["seq"])), cmap=DIV, norm=TwoSlopeNorm(0, -1, 1))
        matrix_axes(axes[1, c], sites, f"log2 |v| ratio {freq_label(s['freq'])} / {freq_label(base['freq'])}")
    fig.colorbar(im, ax=axes[1, :2], shrink=0.7, label="log2 ratio (+1 = doubled)")
    common = common_strong(sessions).astype(float)
    im = axes[1, 2].imshow(np.ma.masked_invalid(to_matrix(common, base["seq"])), cmap=SEQ, vmin=0, vmax=1.4)
    matrix_axes(axes[1, 2], sites, f"Strong in all 3 sessions (|v|>={STRONG_COUNTS:g}): n={int(common.sum())}")
    for c, s in enumerate(sessions):
        v0 = s["v"]["REST"]
        dphi = np.degrees(np.angle(v0 * np.exp(-1j * np.median(np.angle(v0)))))
        dphi[np.abs(v0) < STRONG_COUNTS] = np.nan
        im = axes[2, c].imshow(np.ma.masked_invalid(to_matrix(dphi, s["seq"])), cmap=DIV, norm=TwoSlopeNorm(0, -180, 180))
        matrix_axes(axes[2, c], sites, f"REST phase - session median (deg, strong only) - {freq_label(s['freq'])}")
    fig.colorbar(im, ax=axes[2, :], shrink=0.7, label="deg (+-180 = sign flip)")
    fig.suptitle("F2  Baseline (REST) maps: 16 drive pairs x 16 sense positions (grey = touches drive or masked)", x=0.01, ha="left")
    save(fig, out / "F2_baseline_maps.png")


def fig_dz_heatmap(sessions, out, vmax=10.0):
    sites = sessions[0]["sites"]
    fig, axes = plt.subplots(3, 1, figsize=(14, 7.5), sharex=True, constrained_layout=True)
    for ax, s in zip(axes, sessions):
        strong = strong_mask(s)
        mat = np.array([100 * np.abs(dz_of(s, t)) for t in TASKS])
        mat[:, ~strong] = np.nan
        im = ax.imshow(np.ma.masked_invalid(mat), aspect="auto", cmap=SEQ, vmin=0, vmax=vmax, interpolation="none")
        ax.set_yticks(range(len(TASKS)))
        ax.set_yticklabels(TASKS, fontsize=7)
        ax.set_title(f"{freq_label(s['freq'])}  (grey = |v_REST| < {STRONG_COUNTS:g} counts, n weak = {int((~strong).sum())})", loc="left", fontsize=8.5)
        for g in range(1, N_EL):
            ax.axvline(g * 13 - 0.5, color=SURFACE, lw=1)
    axes[-1].set_xticks([g * 13 + 6 for g in range(N_EL)])
    axes[-1].set_xticklabels([pair_label(sites, g) for g in range(N_EL)], rotation=90, fontsize=7)
    axes[-1].set_xlabel("Pattern ID grouped by drive pair (13 sense pairs each, scan order left to right)")
    fig.colorbar(im, ax=axes, shrink=0.6, label=f"|dz| (%), capped at {vmax:g}", extend="max")
    fig.suptitle("F3a  |dz| = |(v_task - v_REST)/v_REST| per pattern, same colour scale for all panels", x=0.01, ha="left")
    save(fig, out / "F3a_dz_heatmap_208.png")

    fig, axes = plt.subplots(len(sessions), len(TASKS), figsize=(18, 9.5), constrained_layout=True)
    for r, s in enumerate(sessions):
        strong = strong_mask(s)
        for c, t in enumerate(TASKS):
            d = 100 * np.abs(dz_of(s, t))
            d[~strong] = np.nan
            ax = axes[r, c]
            im = ax.imshow(np.ma.masked_invalid(to_matrix(d, s["seq"])), cmap=SEQ, vmin=0, vmax=vmax)
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(False)
            if r == 0:
                ax.set_title(t, fontsize=9)
            if c == 0:
                ax.set_ylabel(f"{freq_label(s['freq'])}\ndrive pair L1-L2 (top) ... R1-L1", fontsize=7.5)
            if r == len(sessions) - 1:
                ax.set_xlabel("sense pair L1-L2 ... R1-L1", fontsize=7)
    fig.colorbar(im, ax=axes, shrink=0.6, label=f"|dz| (%), capped at {vmax:g}", extend="max")
    fig.suptitle("F3b  |dz| as 16x16 drive x sense matrices (same layout as F2; grey = weak or touches drive)", x=0.01, ha="left")
    save(fig, out / "F3b_dz_maps_16x16.png")


def fig_lateralization(t3, out):
    freqs = sorted(t3.freq_hz.unique())
    fig, axes = plt.subplots(1, len(freqs), figsize=(13, 3.8), sharey=True, constrained_layout=True)
    x = np.arange(len(TASKS))
    top = max(t3.L_median_abs_dz_pct.max(), t3.R_median_abs_dz_pct.max())
    for ax, f in zip(axes, freqs):
        d = t3[t3.freq_hz == f].set_index("task").loc[list(TASKS)]
        ax.bar(x - 0.2, d.L_median_abs_dz_pct, 0.38, color=SIDE_COLORS["L"], label="L-only patterns")
        ax.bar(x + 0.2, d.R_median_abs_dz_pct, 0.38, color=SIDE_COLORS["R"], label="R-only patterns")
        for xi, li in zip(x, d.LI):
            ax.text(xi, top * 1.08, f"{li:+.2f}", ha="center", fontsize=7, color=INK2)
        ax.set_ylim(0, top * 1.18)
        ax.set_xticks(x)
        ax.set_xticklabels([t.replace("_", "\n") for t in TASKS], fontsize=7)
        ax.set_title(f"{freq_label(f)}   (numbers = LI)", fontsize=9)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("median |dz| on strong patterns (%)")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper right", ncol=2)
    fig.suptitle("F4  Lateralization: patterns using only left cups vs only right cups; LI = (L-R)/(L+R)", x=0.01, ha="left")
    save(fig, out / "F4_lateralization.png")


def corr_heatmap(ax, mat, labels, annotate=True, fs=7):
    im = ax.imshow(mat, cmap=DIV, norm=TwoSlopeNorm(0, -1, 1))
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=fs)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=fs)
    for sp in ax.spines.values():
        sp.set_visible(False)
    if annotate:
        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=fs - 1.5,
                        color=SURFACE if abs(mat[i, j]) > 0.6 else INK)
    return im


def fig_correlations(sessions, out):
    sel = common_strong(sessions)
    fig, axes = plt.subplots(1, len(sessions), figsize=(15, 5), constrained_layout=True)
    short = [t.replace("SMILE_", "S_").replace("PUFF_", "P_") for t in TASKS]
    mats = {}
    for ax, s in zip(axes, sessions):
        f = np.array([feature_vector(s, t, sel) for t in TASKS])
        mats[s["freq"]] = np.corrcoef(f)
        im = corr_heatmap(ax, mats[s["freq"]], short, fs=8)
        ax.set_title(freq_label(s["freq"]))
    fig.colorbar(im, ax=axes, shrink=0.8, label="Pearson r of [Re dz, Im dz]")
    fig.suptitle(f"F5a  Task x task correlation of dz within each session (n={int(sel.sum())} patterns strong in all sessions)", x=0.01, ha="left")
    save(fig, out / "F5a_task_corr_6x6.png")

    labels, feats = [], []
    for t, st in zip(TASKS, short):
        for s in sessions:
            labels.append(f"{st} {s['freq'] // 1000}k")
            feats.append(feature_vector(s, t, sel))
    big = np.corrcoef(np.array(feats))
    fig, ax = plt.subplots(figsize=(11, 10), constrained_layout=True)
    im = corr_heatmap(ax, big, labels, fs=7)
    for k in range(1, len(TASKS)):
        ax.axhline(3 * k - 0.5, color=SURFACE, lw=2)
        ax.axvline(3 * k - 0.5, color=SURFACE, lw=2)
    fig.colorbar(im, ax=ax, shrink=0.7, label="Pearson r")
    ax.set_title("F5b  18x18 correlation (task x frequency); 3x3 diagonal blocks = same task at 10/50/80 kHz", loc="left")
    save(fig, out / "F5b_task_freq_corr_18x18.png")
    return mats, big, labels


def fig_re_im(sessions, out):
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), sharex=True, sharey=True, constrained_layout=True)
    for ax, t in zip(axes.flat, TASKS):
        for s in sessions:
            st = strong_mask(s)
            d = 100 * dz_of(s, t)[st]
            ax.scatter(d.real, d.imag, s=14, color=FREQ_COLORS[s["freq"]], edgecolor=SURFACE, lw=0.6,
                       label=f"{freq_label(s['freq'])} (n={int(st.sum())})", alpha=0.9)
        ax.axhline(0, color=INK2, lw=0.6)
        ax.axvline(0, color=INK2, lw=0.6)
        ax.set_title(t)
        ax.grid(color=GRID, lw=0.5)
        ax.set_axisbelow(True)
    for ax in axes[1]:
        ax.set_xlabel("Re(dz) %  (~ relative |v| change)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Im(dz) %  (~ phase change; 1% = 0.57 deg)")
    axes[0, 0].legend(frameon=False, fontsize=7.5)
    fig.suptitle("F6  Amplitude vs phase component of dz, strong patterns of each session", x=0.01, ha="left")
    save(fig, out / "F6_re_vs_im.png")


def fig_frequency_effect(sessions, out):
    fig, axes = plt.subplots(1, len(TASKS), figsize=(15, 3.4), sharey=True, constrained_layout=True)
    xs = np.arange(len(sessions))
    for ax, t in zip(axes, TASKS):
        med, q1, q3 = [], [], []
        for s in sessions:
            d = 100 * np.abs(dz_of(s, t)[strong_mask(s)])
            med.append(np.median(d))
            q1.append(np.percentile(d, 25))
            q3.append(np.percentile(d, 75))
        ax.fill_between(xs, q1, q3, color="#cde2fb", lw=0)
        ax.plot(xs, med, color="#184f95", lw=2, marker="o", ms=6, mec=SURFACE, mew=1.5)
        for xi, m in zip(xs, med):
            ax.annotate(f"{m:.1f}", (xi, m), xytext=(5, 5), textcoords="offset points", fontsize=7, color=INK2)
        ax.set_xticks(xs)
        ax.set_xticklabels([freq_label(s["freq"]) for s in sessions])
        ax.set_title(t, fontsize=9)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("|dz| % on strong patterns\n(line = median, band = IQR)")
    fig.suptitle("F7  Task effect vs excitation frequency (each point is a different session/frame)", x=0.01, ha="left")
    save(fig, out / "F7_frequency_effect.png")


def ring_xy():
    ang = np.deg2rad(np.r_[101.25 + 22.5 * np.arange(8), 281.25 + 22.5 * np.arange(8)])
    return np.c_[np.cos(ang), np.sin(ang)]


def fig_involvement(sessions, out):
    xy = ring_xy()
    sites = sessions[0]["sites"]
    vals = {(s["freq"], t): involvement(s, t) for s in sessions for t in TASKS}
    vmax = np.nanmax(list(vals.values()))
    fig, axes = plt.subplots(len(sessions), len(TASKS), figsize=(17, 9), constrained_layout=True)
    for r, s in enumerate(sessions):
        for c, t in enumerate(TASKS):
            ax = axes[r, c]
            ax.plot(np.r_[xy[:, 0], xy[0, 0]], np.r_[xy[:, 1], xy[0, 1]], color=GRID, lw=1, zorder=0)
            sc = ax.scatter(xy[:, 0], xy[:, 1], c=vals[(s["freq"], t)], cmap=SEQ, vmin=0, vmax=vmax, s=170,
                            edgecolor=INK2, lw=0.6)
            for i, (x, y) in enumerate(xy):
                ax.text(1.28 * x, 1.28 * y, sites[i], ha="center", va="center", fontsize=6, color=INK2)
            ax.text(-1.45, 0, "L", fontsize=9, color=SIDE_COLORS["L"], ha="center", va="center", weight="bold")
            ax.text(1.45, 0, "R", fontsize=9, color=SIDE_COLORS["R"], ha="center", va="center", weight="bold")
            ax.set_xlim(-1.6, 1.6)
            ax.set_ylim(-1.45, 1.45)
            ax.set_aspect("equal")
            ax.axis("off")
            if r == 0:
                ax.set_title(t, fontsize=9)
            if c == 0:
                ax.text(-1.75, 0, freq_label(s["freq"]), rotation=90, va="center", ha="center", fontsize=9)
    fig.colorbar(sc, ax=axes, shrink=0.6, label="mean |dz| % of strong patterns using that cup")
    fig.suptitle("F8  Electrode involvement HEURISTIC (ring schematic, subject's left drawn left; top = forehead, bottom = chin). "
                 "NOT muscle localisation.", x=0.01, ha="left")
    save(fig, out / "F8_electrode_involvement.png")
    return vals


def fig_loso(res, out):
    fig, ax = plt.subplots(figsize=(6.2, 5.4), constrained_layout=True)
    conf = res["confusion"]
    im = ax.imshow(conf, cmap=SEQ, vmin=0, vmax=3)
    for i in range(len(TASKS)):
        for j in range(len(TASKS)):
            ax.text(j, i, str(conf[i, j]), ha="center", va="center", color=SURFACE if conf[i, j] >= 2 else INK)
    ax.set_xticks(range(len(TASKS)))
    ax.set_xticklabels(TASKS, rotation=45, ha="right", fontsize=7.5)
    ax.set_yticks(range(len(TASKS)))
    ax.set_yticklabels(TASKS, fontsize=7.5)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Cued task")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(
        f"F9  Leave-one-session-out nearest centroid\n"
        f"accuracy {res['accuracy']:.2f} (chance {res['chance']:.2f}), label-permutation p = {res['perm_p']:.4f} (2000 perms)\n"
        f"18 test frames, 3 folds, n={res['n_patterns']} patterns; task order identical in every session",
        loc="left", fontsize=8.5,
    )
    fig.colorbar(im, ax=ax, shrink=0.7, label="count")
    save(fig, out / "F9_loso_confusion.png")


# --------------------------------------------------------------------------
# Exploratory reconstruction (2-D disk, pyEIT FEM)
# --------------------------------------------------------------------------


class DiskModel:
    """Time-difference, noise-weighted one-step linear inverse on a 2-D disk.

    J_rel[i] = d ln v_i / d sigma (pyEIT Jacobian sign-corrected and divided by
    the simulated homogeneous v0). Data y = Re(dz) (sign, gain and phase of each
    measured channel cancel). Weights 1/sigma_i^2 with
    sigma_i = sqrt((NOISE_COUNTS/|v_REST,i|)^2 + floor^2) down-weight weak patterns.
    ds = (J^T W J + lambda R)^-1 J^T W y, R = diag(diag(J^T W J))^p.
    """

    def __init__(self):
        import pyeit.eit.protocol as protocol
        import pyeit.mesh as mesh
        from pyeit.eit.fem import EITForward

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.mesh = mesh.create(N_EL, h0=RECON_H0, p_fix=ring_xy())
            proto = protocol.create(N_EL, 1, 1, "std")
            self.fwd = EITForward(self.mesh, proto)
            jac, v0 = self.fwd.compute_jac(perm=1.0)
        self.v0 = np.real(v0)
        self.jrel = -np.real(jac) / self.v0[:, None]
        self.xy = self.mesh.node[:, :2]
        self.centroid = self.xy[self.mesh.element].mean(axis=1)

    def sigma(self, v_rest_abs):
        return np.sqrt((NOISE_COUNTS / v_rest_abs) ** 2 + RECON_REL_FLOOR**2)

    def inverse(self, v_rest_abs):
        sig = self.sigma(v_rest_abs)
        w = 1 / sig**2
        a = self.jrel.T @ (w[:, None] * self.jrel)
        r = np.diag(np.diag(a) ** RECON_P)
        lam = RECON_LAMBDA_FRAC * np.trace(a) / np.trace(r)
        return np.linalg.solve(a + lam * r, self.jrel.T * w), sig

    def simulate_rel(self, perm):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            v1 = np.real(self.fwd.solve_eit(perm=perm))
        return (v1 - self.v0) / self.v0


def reconstruct_all(sessions, model: DiskModel):
    images, rows = {}, []
    rng = np.random.default_rng(1)
    for s in sessions:
        v_rest_abs = np.abs(s["v"]["REST"])
        h, sig = model.inverse(v_rest_abs)
        noise_norms = [np.linalg.norm(h @ (rng.normal(size=N_PAT) * sig)) for _ in range(RECON_NOISE_DRAWS)]
        left = model.centroid[:, 0] < 0
        for t in TASKS:
            ds = h @ np.real(dz_of(s, t))
            images[(s["freq"], t)] = ds
            rows.append(
                {
                    "session": s["name"],
                    "freq_hz": s["freq"],
                    "task": t,
                    "image_norm": float(np.linalg.norm(ds)),
                    "noise_image_norm_median": float(np.median(noise_norms)),
                    "image_to_noise_ratio": float(np.linalg.norm(ds) / np.median(noise_norms)),
                    "left_energy_fraction": float(np.sum(ds[left] ** 2) / np.sum(ds**2)),
                }
            )
    t5 = pd.DataFrame(rows)
    fit = []
    for s in sessions:
        fit.append(
            {
                "session": s["name"],
                "freq_hz": s["freq"],
                "spearman_log_abs_v_rest_vs_disk_model": float(
                    pd.Series(np.log(np.abs(s["v"]["REST"]))).corr(pd.Series(np.log(np.abs(model.v0))), method="spearman")
                ),
            }
        )
    xcorr = []
    for t in TASKS:
        for s1, s2 in itertools.combinations(sessions, 2):
            xcorr.append(
                {
                    "task": t,
                    "freq_a_hz": s1["freq"],
                    "freq_b_hz": s2["freq"],
                    "image_corr": float(np.corrcoef(images[(s1["freq"], t)], images[(s2["freq"], t)])[0, 1]),
                }
            )
    return images, t5, pd.DataFrame(fit), pd.DataFrame(xcorr)


def draw_disk(ax, model, values, norm, sites, labels=False):
    tp = ax.tripcolor(model.xy[:, 0], model.xy[:, 1], model.mesh.element, facecolors=values, cmap=DIV, norm=norm,
                      shading="flat")
    el = model.xy[model.mesh.el_pos]
    ax.scatter(el[:, 0], el[:, 1], s=10, color=INK, zorder=3)
    if labels:
        for i, (x, y) in enumerate(el):
            ax.text(1.2 * x, 1.2 * y, sites[i], ha="center", va="center", fontsize=6, color=INK2)
    ax.set_aspect("equal")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.axis("off")
    return tp


def fig_reconstruction(sessions, model, images, t5, out):
    sites = sessions[0]["sites"]
    lim = np.percentile(np.abs(np.concatenate(list(images.values()))), 99)
    norm = TwoSlopeNorm(0, -lim, lim)
    fig, axes = plt.subplots(len(TASKS), len(sessions), figsize=(9.5, 18), constrained_layout=True)
    snr = t5.set_index(["freq_hz", "task"])["image_to_noise_ratio"]
    for r, t in enumerate(TASKS):
        for c, s in enumerate(sessions):
            ax = axes[r, c]
            tp = draw_disk(ax, model, images[(s["freq"], t)], norm, sites, labels=(r == 0 and c == 0))
            ax.set_title(f"{t} - {freq_label(s['freq'])}\nimage/noise = {snr[(s['freq'], t)]:.1f}", fontsize=8)
    fig.colorbar(tp, ax=axes, shrink=0.3, label="reconstructed d(sigma) (a.u.; red = more conductive)")
    fig.suptitle(
        "F10  EXPLORATORY 2-D disk projection (NOT anatomy): time-difference, REST reference, noise-weighted JAC\n"
        "ring order L1..L8 down the left, R8..R1 up the right; top = forehead pair, bottom = chin pair",
        x=0.01, ha="left", fontsize=9,
    )
    save(fig, out / "F10_reconstruction_exploratory.png")


def fig_reconstruction_sanity(sessions, model, images, out):
    """What the same pipeline does with (a) a known blob, (b) noise only, (c) one drive-current change."""
    from pyeit.mesh.wrapper import PyEITAnomaly_Circle, set_perm

    sites = sessions[0]["sites"]
    s = sessions[0]
    v_rest_abs = np.abs(s["v"]["REST"])
    h, sig = model.inverse(v_rest_abs)
    rng = np.random.default_rng(7)

    blob = PyEITAnomaly_Circle(center=[-0.45, -0.45], r=0.25, perm=1.1)
    perm = np.real(set_perm(model.mesh, anomaly=blob, background=1.0).perm)
    y_blob = model.simulate_rel(perm)
    img_blob = h @ y_blob
    noise_norm = np.median([np.linalg.norm(h @ (rng.normal(size=N_PAT) * sig)) for _ in range(RECON_NOISE_DRAWS)])
    img_blob_noisy = h @ (y_blob + rng.normal(size=N_PAT) * sig)
    img_noise = h @ (rng.normal(size=N_PAT) * sig)
    y_drive = np.zeros(N_PAT)
    y_drive[15 * 13:16 * 13] = 0.03
    img_drive = h @ y_drive
    strong = strong_mask(s)
    blob_med = 100 * np.median(np.abs(y_blob[strong]))
    task_meds = [100 * np.median(np.abs(dz_of(x, t)[strong_mask(x)])) for x in sessions for t in TASKS]

    lim = np.percentile(np.abs(np.concatenate(list(images.values()))), 99)
    norm = TwoSlopeNorm(0, -lim, lim)
    fig, axes = plt.subplots(1, 5, figsize=(17, 4.4), constrained_layout=True)
    draw_disk(axes[0], model, perm - 1.0, TwoSlopeNorm(0, -0.1, 0.1), sites, labels=True)
    axes[0].set_title("(a) truth: +10% conductivity blob (r=0.25)\n"
                      f"-> median |dz| on strong patterns = {blob_med:.2f}%\n"
                      f"(measured tasks: {min(task_meds):.1f}-{max(task_meds):.1f}%)", fontsize=8.5)
    blim = np.abs(img_blob).max()
    draw_disk(axes[1], model, img_blob, TwoSlopeNorm(0, -blim, blim), sites)
    axes[1].set_title("(b) reconstruction of (a), no noise\n(own colour scale)", fontsize=8.5)
    draw_disk(axes[2], model, img_blob_noisy, TwoSlopeNorm(0, -blim, blim), sites)
    axes[2].set_title("(c) (a) + measured-level noise, scale of (b)\n"
                      f"image/noise = {np.linalg.norm(img_blob) / noise_norm:.2f}", fontsize=8.5)
    draw_disk(axes[3], model, img_noise, norm, sites)
    axes[3].set_title("(d) noise only, SAME scale as F10\n(what 'nothing happened' looks like)", fontsize=8.5)
    tp = draw_disk(axes[4], model, img_drive, norm, sites)
    axes[4].set_title(f"(e) +3% current change on ONE drive pair\n({pair_label(sites, 15)}), SAME scale as F10", fontsize=8.5)
    fig.colorbar(tp, ax=axes[3:], shrink=0.8, label="d(sigma) a.u.")
    fig.suptitle("F11  Sanity checks of the exploratory reconstruction (ideal disk model, same inverse as F10)", x=0.01, ha="left")
    save(fig, out / "F11_reconstruction_sanity.png")
    left = model.centroid[:, 0] < 0
    lower = model.centroid[:, 1] < 0
    return {
        "blob_peak_xy": model.centroid[int(np.argmax(img_blob))].tolist(),
        "blob_true_xy": [-0.45, -0.45],
        "blob_median_abs_dz_pct_strong": float(blob_med),
        "blob_image_to_noise": float(np.linalg.norm(img_blob) / noise_norm),
        "blob_noisy_lower_left_energy_fraction": float(np.sum(img_blob_noisy[left & lower] ** 2) / np.sum(img_blob_noisy**2)),
        "noise_image_norm_median": float(noise_norm),
        "drive_artifact_norm": float(np.linalg.norm(img_drive)),
    }


# --------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions", nargs="+", default=list(SESSION_NAMES))
    ap.add_argument("--out", default=str(REPO / "data/processed/pilot"))
    ap.add_argument("--no-recon", action="store_true", help="skip the pyEIT reconstruction section")
    args = ap.parse_args()

    sessions = sorted((load_session(resolve_session(n)) for n in args.sessions), key=lambda s: s["freq"])
    out_root = Path(args.out)
    out = out_root / "three-frequency-20261005"
    out.mkdir(parents=True, exist_ok=True)
    hashes = {s["meta"]["protocol_hash"] for s in sessions}
    if len(hashes) != 1:
        raise SystemExit(f"protocol hash differs between sessions: {hashes}")

    timings = {s["name"]: timing(s) for s in sessions}
    for s in sessions:
        sdir = out_root / s["name"]
        sdir.mkdir(parents=True, exist_ok=True)
        session_pattern_table(s, timings[s["name"]]).to_csv(sdir / "pattern_dz.csv", index=False)
        timings[s["name"]].to_csv(sdir / "timeline.csv", index=False)

    t1 = table_t1(sessions, timings)
    t2 = table_t2(sessions, timings)
    t3 = table_t3(sessions, timings)
    t4 = table_t4(sessions)
    for s in sessions:
        t2[t2.session == s["name"]].to_csv(out_root / s["name"] / "task_features.csv", index=False)
    t1.to_csv(out / "T1_qc_timing.csv", index=False)
    pd.concat(timings.values()).to_csv(out / "T1b_trial_timeline.csv", index=False)
    t2.to_csv(out / "T2_task_features.csv", index=False)
    t3.to_csv(out / "T3_lateralization.csv", index=False)
    t4.to_csv(out / "T4_crossfreq_correlation.csv", index=False)
    table_t8_additivity(sessions).to_csv(out / "T8_bilateral_additivity.csv", index=False)

    drive_rows = []
    for s in sessions:
        _, _, c_rest = reciprocity(s, "REST", True)
        for t in STATES:
            before, after, c = reciprocity(s, t, True)
            drive_rows.append(
                {
                    "session": s["name"], "freq_hz": s["freq"], "state": t,
                    "recip_err_median_pct": 100 * before, "recip_err_after_fit_pct": 100 * after,
                    **{f"dln_gain_vs_rest_pct_{pair_label(s['sites'], g)}": 100 * (c[g] - c_rest[g]) for g in range(N_EL)},
                }
            )
    pd.DataFrame(drive_rows).to_csv(out / "T6_reciprocity_drive_gain.csv", index=False)

    fig_timeline(sessions, timings, out)
    fig_baseline(sessions, out)
    fig_dz_heatmap(sessions, out)
    fig_lateralization(t3, out)
    corr6, corr18, corr18_labels = fig_correlations(sessions, out)
    pd.DataFrame(corr18, index=corr18_labels, columns=corr18_labels).to_csv(out / "T4b_corr_18x18.csv")
    fig_re_im(sessions, out)
    fig_frequency_effect(sessions, out)
    inv = fig_involvement(sessions, out)
    pd.DataFrame(
        [{"freq_hz": f, "task": t, **dict(zip(sessions[0]["sites"], v))} for (f, t), v in inv.items()]
    ).to_csv(out / "T7_electrode_involvement.csv", index=False)
    loso_res = loso(sessions)
    fig_loso(loso_res, out)

    summary = {
        "sessions": [s["name"] for s in sessions],
        "strong_threshold_counts": STRONG_COUNTS,
        "common_strong_patterns": int(common_strong(sessions).sum()),
        "loso": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in loso_res.items()},
        "task_corr_6x6": {str(f): m.round(3).tolist() for f, m in corr6.items()},
    }

    if not args.no_recon:
        model = DiskModel()
        images, t5, fit, xcorr = reconstruct_all(sessions, model)
        t5.to_csv(out / "T5_reconstruction_metrics.csv", index=False)
        fit.to_csv(out / "T5b_disk_model_fit.csv", index=False)
        xcorr.to_csv(out / "T5c_reconstruction_crossfreq_corr.csv", index=False)
        fig_reconstruction(sessions, model, images, t5, out)
        summary["recon_sanity"] = fig_reconstruction_sanity(sessions, model, images, out)
        summary["recon_settings"] = {
            "h0": RECON_H0, "p": RECON_P, "lambda_frac": RECON_LAMBDA_FRAC,
            "noise_counts": NOISE_COUNTS, "rel_floor": RECON_REL_FLOOR, "n_elements": int(model.mesh.n_elems),
        }

    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    pd.set_option("display.width", 200)
    print(t1.T.to_string())
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
