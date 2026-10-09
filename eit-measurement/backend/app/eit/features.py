"""Relative change from rest (dz) and the features computed from it.

dz = (V_task - V_ref) / V_ref per measurement, complex. Dividing by the same measurement's
rest value cancels its unknown gain, phase and polarity (and the drive current, if constant).
Re(dz) ~ relative amplitude change; Im(dz) ~ phase change in rad.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .io import Session
from .protocol import mirror_pairs, side_masks

BASELINES = ("initial_rest", "preceding_rest", "bracketing_rest")


def relative_change(v: np.ndarray, ref: np.ndarray) -> np.ndarray:
    if not np.all(np.isfinite(ref)) or np.any(np.abs(ref) == 0):
        raise ValueError("reference has zero or non-finite values; select valid rest frames first")
    return (v - ref) / ref


# ---------------------------------------------------------------------------------------
# Blocks, references and per-task changes
# ---------------------------------------------------------------------------------------


def blocks(s: Session) -> list:
    """Time-ordered runs of frames: rest runs, and task runs (same trial and task).

    A block is valid unless one of its trials is marked valid=False in trial_windows.csv; invalid
    frames are dropped from rest runs, and invalid task runs are kept (so they still separate the rest
    runs around them) but skipped by ``changes``.
    """
    out, cur, key = [], [], None

    def close():
        frames = [int(f.frame_id) for f in cur if key[0] == "TASK" or f.valid]
        valid = all(f.valid for f in cur) if key[0] == "TASK" else bool(frames)
        out.append({"kind": key[0], "task": cur[0].task, "trial_id": cur[0].trial_id,
                    "frames": frames or [int(f.frame_id) for f in cur], "valid": valid})

    for fr in s.frames.sort_values("start_s").itertuples():
        k = ("REST",) if fr.is_rest else ("TASK", fr.trial_id, fr.task)
        if k != key and cur:
            close()
            cur = []
        key = k
        cur.append(fr)
    if cur:
        close()
    return out


def _mean(s: Session, frame_ids) -> np.ndarray:
    return np.mean([s.V[f] for f in frame_ids], axis=0)


def reference_for_block(s: Session, blist: list, i: int, policy: str, rest_k: int = None) -> list:
    """Rest frame ids used as reference for task block ``i`` (one list per rest block; the lists are
    averaged with equal weight).

    initial_rest: every rest frame before the first task. preceding_rest: the nearest rest block before
    the task (after it, if none). bracketing_rest: the nearest rest blocks before and after.
    ``rest_k`` (preceding/bracketing only): use only the last k frames of the block before and the first
    k frames of the block after, i.e. the rest frames closest in time; None = the whole block.
    """
    if policy not in BASELINES:
        raise ValueError(f"baseline must be one of {BASELINES}, got {policy!r}")
    rest_blocks = [j for j, b in enumerate(blist) if b["kind"] == "REST" and b.get("valid", True)]
    if not rest_blocks:
        raise ValueError(f"{s.name}: no valid rest frames to use as reference")
    first_task = next((j for j, b in enumerate(blist) if b["kind"] == "TASK"), len(blist))
    if policy == "initial_rest":
        chosen = [j for j in rest_blocks if j < first_task] or rest_blocks
        return [[f for j in chosen for f in blist[j]["frames"]]]

    def last(j):
        return blist[j]["frames"][-rest_k:] if rest_k else blist[j]["frames"]

    def first(j):
        return blist[j]["frames"][:rest_k] if rest_k else blist[j]["frames"]

    before = [j for j in rest_blocks if j < i]
    after = [j for j in rest_blocks if j > i]
    pre = [last(before[-1])] if before else []
    if policy == "preceding_rest":
        return pre or [first(after[0])]
    post = [first(after[0])] if after else []
    return (pre + post) or [blist[rest_blocks[0]]["frames"]]


@dataclass
class Change:
    session: str
    label: str
    task: str
    trial_id: str
    repetition: int
    frames: list
    ref_frames: list
    dz: np.ndarray
    t_since_ref_s: float
    t_rel_frame_start: np.ndarray = field(repr=False, default=None)


def changes(s: Session, policy: str = "initial_rest", drop_first: int = 0, rest_k: int = None) -> list:
    """One Change per valid task block (frames averaged after dropping ``drop_first`` transition frames)."""
    blist = blocks(s)
    out, reps = [], {}
    for i, b in enumerate(blist):
        if b["kind"] != "TASK" or not b["valid"]:
            continue
        frames = b["frames"][drop_first:] or b["frames"][-1:]
        ref_sets = reference_for_block(s, blist, i, policy, rest_k)
        ref = np.mean([_mean(s, rs) for rs in ref_sets], axis=0)
        dz = np.mean([relative_change(s.V[f], ref) for f in frames], axis=0)
        ref_ids = [f for rs in ref_sets for f in rs]
        # same weighting as ref: mean over rest blocks of each block's mean time
        t_ref = float(np.mean([np.mean([s.frame(f).mid_s for f in rs]) for rs in ref_sets]))
        t_task = float(np.mean([s.frame(f).mid_s for f in frames]))
        t_rel = np.mean([s.T[f] - s.frame(f).start_s for f in frames], axis=0)
        reps[b["task"]] = reps.get(b["task"], 0) + 1
        out.append(Change(s.name, s.label, b["task"], str(b["trial_id"]), reps[b["task"]], frames, ref_ids, dz,
                          t_task - t_ref, t_rel))
    return out


def task_order(sessions, cfg_tasks=None, all_changes=None) -> list:
    if cfg_tasks:
        return list(cfg_tasks)
    seen = []
    for chs in all_changes:
        for c in chs:
            if c.task not in seen:
                seen.append(c.task)
    return seen


def aggregate(chs: list) -> dict:
    """task -> mean dz over repetitions within one session."""
    by_task = {}
    for c in chs:
        by_task.setdefault(c.task, []).append(c.dz)
    return {t: np.mean(v, axis=0) for t, v in by_task.items()}


def strong_mask(s: Session, threshold: float) -> np.ndarray:
    return np.abs(s.rest_mean()) >= threshold


# ---------------------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------------------


def pattern_table(s: Session, chs: list, strong: np.ndarray) -> pd.DataFrame:
    ref_abs = np.abs(s.rest_mean())
    rows = []
    for c in chs:
        a, b, m, n = s.seq.T
        rows.append(pd.DataFrame({
            "session": s.name, "label": s.label, "task": c.task, "trial_id": c.trial_id,
            "repetition": c.repetition, "pattern_id": np.arange(s.n_pat),
            "drive_pair": [f"{s.sites[i]}->{s.sites[j]}" for i, j in zip(a, b)],
            "sense_pair": [f"{s.sites[i]}->{s.sites[j]}" for i, j in zip(m, n)],
            "rest_abs_counts": ref_abs, "strong": strong,
            "dz_abs_pct": 100 * np.abs(c.dz), "dz_re_pct": 100 * c.dz.real, "dz_im_pct": 100 * c.dz.imag,
            "dv_abs_counts": np.abs(c.dz) * ref_abs, "t_after_frame_start_s": c.t_rel_frame_start,
        }))
    return pd.concat(rows, ignore_index=True)


def task_features(s: Session, chs: list, agg: dict, tasks: list, cfg: dict) -> pd.DataFrame:
    ref_abs = np.abs(s.rest_mean())
    strong = ref_abs >= cfg["strong_counts"]
    big = ref_abs >= 100
    rows = []
    for t in tasks:
        if t not in agg:
            continue
        dz = agg[t]
        dv = np.abs(dz) * ref_abs
        a = 100 * np.abs(dz[strong])
        reps = [c for c in chs if c.task == t]
        rows.append({
            "session": s.name, "label": s.label, "freq_hz": s.freq, "task": t, "n_repetitions": len(reps),
            "t_since_ref_s": float(np.mean([c.t_since_ref_s for c in reps])),
            "rms_dv_counts": float(np.sqrt(np.mean(dv ** 2))),
            "n_strong": int(strong.sum()),
            "median_abs_dz_pct_strong": float(np.median(a)),
            "p90_abs_dz_pct_strong": float(np.percentile(a, 90)),
            "median_abs_dz_pct_ge100": float(np.median(100 * np.abs(dz[big]))) if big.any() else np.nan,
            "median_re_dz_pct_strong": float(np.median(100 * dz[strong].real)),
            "median_phase_change_deg_strong": float(np.degrees(np.median(np.angle(1 + dz[strong])))),
            **{f"n_strong_gt_{x:g}pct": int((a > x).sum()) for x in cfg["rel_thresholds_pct"]},
            "pct_strong_gt_2pct": float(100 * np.mean(a > 2.0)),
            "n_all_dv_gt_3x_noise_max": int((dv > 3 * cfg["noise_counts_max"]).sum()),
        })
    return pd.DataFrame(rows)


def lateralization(s: Session, chs: list, agg: dict, tasks: list, strong: np.ndarray) -> pd.DataFrame:
    left, right = side_masks(s.seq, s.sites)
    pairs = [(i, j) for i, j in mirror_pairs(s.seq, s.sites) if strong[i] and strong[j]]
    rows = []
    for t in tasks:
        if t not in agg:
            continue
        d = 100 * np.abs(agg[t])
        lv, rv = np.median(d[left & strong]), np.median(d[right & strong])
        paired = np.array([d[i] - d[j] for i, j in pairs])
        t_rel = np.mean([c.t_rel_frame_start for c in chs if c.task == t], axis=0)
        rows.append({
            "session": s.name, "label": s.label, "freq_hz": s.freq, "task": t,
            "n_left_strong": int((left & strong).sum()), "n_right_strong": int((right & strong).sum()),
            "L_median_abs_dz_pct": lv, "R_median_abs_dz_pct": rv, "L_minus_R_pctpt": lv - rv,
            "LI": (lv - rv) / (lv + rv), "mirror_pairs_both_strong": len(pairs),
            "mirror_median_L_minus_R_pctpt": float(np.median(paired)) if len(paired) else np.nan,
            "mirror_n_L_gt_R": int((paired > 0).sum()),
            "t_left_patterns_mean_s": float(t_rel[left].mean()), "t_right_patterns_mean_s": float(t_rel[right].mean()),
        })
    return pd.DataFrame(rows)


def feature_vector(dz: np.ndarray, sel: np.ndarray) -> np.ndarray:
    return np.r_[dz[sel].real, dz[sel].imag]


def cross_session_correlation(labels: list, aggs: list, tasks: list, sel: np.ndarray) -> pd.DataFrame:
    rows = []
    every = np.ones_like(sel)
    for t in tasks:
        for (la, aa), (lb, ab) in itertools.combinations(list(zip(labels, aggs)), 2):
            if t not in aa or t not in ab:
                continue
            same = np.corrcoef(feature_vector(aa[t], sel), feature_vector(ab[t], sel))[0, 1]
            other = [np.corrcoef(feature_vector(aa[t], sel), feature_vector(ab[u], sel))[0, 1]
                     for u in tasks if u != t and u in ab]
            rows.append({
                "task": t, "session_a": la, "session_b": lb, "r_same_task_common_strong": same,
                "r_other_tasks_mean": float(np.mean(other)) if other else np.nan,
                "r_other_tasks_max": float(np.max(other)) if other else np.nan,
                "r_same_task_all": np.corrcoef(feature_vector(aa[t], every), feature_vector(ab[t], every))[0, 1],
                "n_patterns": int(sel.sum()),
            })
    return pd.DataFrame(rows)


def correlation_matrix(labels: list, aggs: list, tasks: list, sel: np.ndarray):
    """Task-major (task x session) correlation matrix of dz feature vectors."""
    names, feats = [], []
    for t in tasks:
        for lab, agg in zip(labels, aggs):
            if t in agg:
                names.append(f"{t}|{lab}")
                feats.append(feature_vector(agg[t], sel))
    return names, np.atleast_2d(np.corrcoef(np.array(feats))) if feats else np.empty((0, 0))


def additivity(s: Session, agg: dict, sel: np.ndarray) -> pd.DataFrame:
    """dz_X_BOTH = a dz_X_LEFT + b dz_X_RIGHT (least squares) for every X with all three tasks."""
    rows = []
    bases = sorted({t.rsplit("_", 1)[0] for t in agg if t.endswith(("_LEFT", "_RIGHT", "_BOTH"))})
    for base in bases:
        names = [f"{base}_BOTH", f"{base}_LEFT", f"{base}_RIGHT"]
        if not all(n in agg for n in names):
            continue
        y = feature_vector(agg[names[0]], sel)
        x = np.c_[feature_vector(agg[names[1]], sel), feature_vector(agg[names[2]], sel)]
        coef = np.linalg.lstsq(x, y, rcond=None)[0]
        resid = y - x @ coef
        rows.append({"session": s.name, "label": s.label, "freq_hz": s.freq, "task": base,
                     "a_left": coef[0], "b_right": coef[1], "r2": 1 - np.sum(resid ** 2) / np.sum((y - y.mean()) ** 2),
                     "r_left_right": np.corrcoef(x[:, 0], x[:, 1])[0, 1], "n_patterns": int(sel.sum())})
    return pd.DataFrame(rows)


def involvement(s: Session, agg: dict, tasks: list, strong: np.ndarray) -> pd.DataFrame:
    """Electrode score I_e = mean |dz| (%) over strong measurements using electrode e in any role."""
    rows = []
    for t in tasks:
        if t not in agg:
            continue
        d = 100 * np.abs(agg[t])
        score = {}
        for e in range(s.n_el):
            use = strong & np.any(s.seq == e, axis=1)
            score[s.sites[e]] = float(d[use].mean()) if use.any() else np.nan
        rows.append({"session": s.name, "label": s.label, "freq_hz": s.freq, "task": t, **score})
    return pd.DataFrame(rows)


def recognition(groups: list, samples: dict, tasks: list, permutations: int = 2000, seed: int = 0) -> dict:
    """Leave-one-group-out nearest centroid (Pearson r) with a label-permutation test.

    groups: ordered group names (sessions, or repetitions); samples[(group, task)] = feature vector.
    """
    def confusion(label_perm):
        conf = np.zeros((len(tasks), len(tasks)), int)
        for test in groups:
            train = [g for g in groups if g != test]
            cents = [np.mean([samples[(g, label_perm[g][t])] for g in train], axis=0) for t in tasks]
            for ti, t in enumerate(tasks):
                r = [np.corrcoef(samples[(test, t)], c)[0, 1] for c in cents]
                conf[ti, int(np.argmax(r))] += 1
        return conf

    conf = confusion({g: {t: t for t in tasks} for g in groups})
    acc = float(np.trace(conf) / conf.sum())
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(permutations):
        perm = {g: dict(zip(tasks, rng.permutation(tasks))) for g in groups}
        c = confusion(perm)
        null.append(np.trace(c) / c.sum())
    null = np.array(null)
    return {"confusion": conf, "accuracy": acc, "chance": 1 / len(tasks),
            "perm_p": float((np.sum(null >= acc) + 1) / (len(null) + 1)), "permutations": permutations}
