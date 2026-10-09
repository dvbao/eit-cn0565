"""Electrode ring, measurement sequence and site helpers (no pyEIT dependency)."""

from __future__ import annotations

import numpy as np


def make_sequence(n_el: int, force_distance: int = 1, sense_distance: int = 1) -> np.ndarray:
    """Measurement sequence of a ring protocol as (A, B, M, N) rows on the logical ring.

    A/B = drive pair (F+, F-) with B = A + force_distance; M/N = sense pair (S+, S-) with
    N = M + sense_distance; sense pairs touching the drive are skipped. Same rows in the same
    order as the ADI driver's ``adi.cn0565.switch_sequence`` (which lists them as F+, S+, S-, F-)
    and as pyEIT ``protocol.create(n_el, force_distance, sense_distance, "std")``.
    pyEIT computes V[N] - V[M]; relative changes are used downstream, so the sign cancels.
    """
    if n_el < 4:
        raise ValueError(f"need at least 4 electrodes, got {n_el}")
    for name, d in (("force_distance", force_distance), ("sense_distance", sense_distance)):
        if not 1 <= d < n_el:
            raise ValueError(f"{name} must be between 1 and {n_el - 1}, got {d}")
    rows = []
    for a in range(n_el):
        b = (a + force_distance) % n_el
        for m in range(n_el):
            n = (m + sense_distance) % n_el
            if m not in (a, b) and n not in (a, b):
                rows.append((a, b, m, n))
    return np.array(rows)


def std_sequence(n_el: int) -> np.ndarray:
    """Adjacent drive, adjacent sense: make_sequence(n_el, 1, 1); n_el * (n_el - 3) rows."""
    return make_sequence(n_el, 1, 1)


def ring_distances(seq: np.ndarray, n_el: int):
    """(force_distance, sense_distance) if ``seq`` is exactly make_sequence(n_el, f, s), else None."""
    seq = np.asarray(seq)
    if seq.ndim != 2 or seq.shape[1] != 4 or not len(seq):
        return None
    f, s = int((seq[0, 1] - seq[0, 0]) % n_el), int((seq[0, 3] - seq[0, 2]) % n_el)
    if 1 <= f < n_el and 1 <= s < n_el and np.array_equal(seq, make_sequence(n_el, f, s)):
        return f, s
    return None


def frame_duration_s(n_measurements: int, seconds_per_measurement: float) -> float:
    """Duration of one frame: the measurements are taken one after another, not simultaneously."""
    return n_measurements * seconds_per_measurement


def pair_label(sites, i: int, distance: int = 1) -> str:
    """Label of the pair that starts at ring index i, e.g. "L1-L2" (distance = force or sense distance)."""
    return f"{sites[i]}-{sites[(i + distance) % len(sites)]}"


def to_matrix(values: np.ndarray, seq: np.ndarray, n_el: int) -> np.ndarray:
    """Per-measurement values -> drive pair x sense position matrix (NaN where sense touches drive)."""
    mat = np.full((n_el, n_el), np.nan)
    for k, (a, _, m, _) in enumerate(seq):
        mat[a, m] = values[k]
    return mat


def side_of(site: str) -> str:
    return site[:1].upper() if site[:1].upper() in ("L", "R") else "?"


def side_masks(seq: np.ndarray, sites) -> tuple:
    """Measurements whose four electrodes are all on the left / all on the right."""
    side = np.array([side_of(s) for s in sites])
    return np.all(side[seq] == "L", axis=1), np.all(side[seq] == "R", axis=1)


def mirror_index(sites) -> dict:
    """Logical index -> index of the mirrored site (L3 <-> R3)."""
    where = {s: i for i, s in enumerate(sites)}
    out = {}
    for i, s in enumerate(sites):
        twin = {"L": "R", "R": "L"}.get(side_of(s))
        if twin and twin + s[1:] in where:
            out[i] = where[twin + s[1:]]
    return out


def mirror_pairs(seq: np.ndarray, sites) -> list:
    """(i_left, i_right): each left-only measurement with its mirrored right-only measurement.
    Measurements using a site without a mirrored twin (e.g. L5 when there is no R5) are skipped."""
    mirror = mirror_index(sites)
    index = {(frozenset(r[:2]), frozenset(r[2:])): k for k, r in enumerate(seq)}
    left, _ = side_masks(seq, sites)
    pairs = []
    for i in np.flatnonzero(left):
        if any(int(x) not in mirror for x in seq[i]):
            continue
        a, b, m, n = (mirror[x] for x in seq[i])
        j = index.get((frozenset((a, b)), frozenset((m, n))))
        if j is not None:
            pairs.append((int(i), int(j)))
    return pairs


def ring_xy(n_el: int, start_deg=None) -> np.ndarray:
    """Equally spaced electrode positions on the unit circle, counter-clockwise.

    Default start: half a step left of the top, so with the ring order L1..L8, R8..R1 the
    left side is drawn on the left, the forehead at the top and the chin at the bottom.
    """
    start = 90.0 + 180.0 / n_el if start_deg is None else float(start_deg)
    ang = np.deg2rad(start + 360.0 / n_el * np.arange(n_el))
    return np.c_[np.cos(ang), np.sin(ang)]
