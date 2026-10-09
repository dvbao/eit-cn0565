"""Exploratory time-difference reconstruction (BP / JAC / GREIT, pyEIT) on a 2-D disk.

The disk is NOT the face: electrodes are placed equally spaced on a unit circle in ring
order. Input is the measured relative change y = Re(dz) "transplanted" onto the model's own
homogeneous reference (v1 = v0_sim * (1 + y)), so the unknown gain/phase/polarity of each
measured channel cancels. Noise-dominated channels are removed; each solver's H is
recomputed from pyEIT's own J / B / grid weights with pyEIT's formulas on the kept rows,
which reproduces ``solver.solve`` exactly when all rows are kept (checked at start-up).
"""

from __future__ import annotations

import itertools
import warnings

import numpy as np
import pandas as pd
from matplotlib.tri import LinearTriInterpolator, Triangulation

from .protocol import ring_xy

ALGOS = ("BP", "JAC", "GREIT")


class Solvers:
    def __init__(self, n_el: int, rc: dict, force_distance: int = 1, sense_distance: int = 1):
        import pyeit.eit.bp as bp
        import pyeit.eit.greit as greit
        import pyeit.eit.jac as jac
        import pyeit.eit.protocol as protocol
        import pyeit.mesh as mesh
        from pyeit.eit.fem import EITForward

        self.rc = rc
        self.n_el = n_el
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.mesh = mesh.create(n_el, h0=rc["h0"], p_fix=ring_xy(n_el, rc.get("ring_start_deg")))
            # same measurement order as protocol.make_sequence(n_el, force_distance, sense_distance)
            self.proto = protocol.create(n_el, force_distance, sense_distance, "std")
            self.bp = bp.BP(self.mesh, self.proto)
            self.bp.setup(weight=rc["bp_weight"])
            self.jac = jac.JAC(self.mesh, self.proto)
            self.jac.setup(p=rc["p"], lamb=rc["lambda"], method=rc["jac_method"], perm=1.0, jac_normalized=True)
            self.greit = greit.GREIT(self.mesh, self.proto)
            self.greit.setup(p=rc["p"], lamb=rc["lambda"], n=rc["greit_n"], s=rc["greit_s"], ratio=rc["greit_ratio"],
                             perm=1.0, jac_normalized=True)
            self.fwd = EITForward(self.mesh, self.proto)
            self.v0 = np.real(self.fwd.solve_eit())
        self.xy = self.mesh.node[:, :2]
        self.tri = Triangulation(self.xy[:, 0], self.xy[:, 1], self.mesh.element)
        self.xg, self.yg, self.gmask = self.greit.get_grid()
        self.w_mat = self.greit._compute_grid_weights(self.xg, self.yg)
        self._cache = {}
        self._check_against_pyeit()

    def h_matrices(self, keep: np.ndarray) -> dict:
        key = keep.tobytes()
        if key not in self._cache:
            p, lamb = self.rc["p"], self.rc["lambda"]
            jn = np.real(self.jac.J)[keep]
            jtj = jn.T @ jn
            if self.rc["jac_method"] == "kotre":
                r_jac = np.diag(np.diag(jtj) ** p)
            elif self.rc["jac_method"] == "lm":
                r_jac = np.diag(np.diag(jtj))
            else:
                r_jac = np.eye(jtj.shape[0])
            h_jac = np.linalg.solve(jtj + lamb * r_jac, jn.T)
            jg = np.real(self.greit.J)[keep]
            jjt = jg @ jg.T
            h_greit = (self.w_mat.T @ jg.T) @ np.linalg.inv(jjt + lamb * np.diag(np.diag(jjt) ** p))
            self._cache[key] = {"BP": np.real(self.bp.H)[:, keep], "JAC": h_jac, "GREIT": h_greit}
        return self._cache[key]

    def reconstruct(self, y: np.ndarray, keep: np.ndarray) -> dict:
        """y = relative change per measurement. Returns BP (nodes), JAC (elements), GREIT (grid)."""
        v0 = self.v0[keep]
        h = self.h_matrices(keep)
        dv_bp = (v0 * y[keep]) / np.sign(v0)       # BP._normalize: (v1 - v0) / sign(v0)
        dv = (v0 * y[keep]) / np.abs(v0)           # EitBase._normalize: (v1 - v0) / |v0|
        return {"BP": -h["BP"] @ dv_bp, "JAC": -h["JAC"] @ dv, "GREIT": -h["GREIT"] @ dv}

    def _check_against_pyeit(self):
        rng = np.random.default_rng(3)
        y = rng.normal(scale=0.01, size=self.v0.size)
        v1 = self.v0 * (1 + y)
        mine = self.reconstruct(y, np.ones(self.v0.size, bool))
        ref = {"BP": np.real(self.bp.solve(v1, self.v0, normalize=True)),
               "JAC": np.real(self.jac.solve(v1, self.v0, normalize=True)),
               "GREIT": np.real(self.greit.solve(v1, self.v0, normalize=True))}
        for a in ALGOS:
            if not np.allclose(mine[a], ref[a], rtol=1e-6, atol=1e-9 * np.abs(ref[a]).max()):
                raise RuntimeError(f"{a}: subset formula does not reproduce pyEIT solve()")

    def on_grid(self, algo: str, values: np.ndarray) -> np.ndarray:
        """Values on the GREIT pixels inside the disk (common support for metrics/comparisons)."""
        inside = ~self.gmask
        if algo == "GREIT":
            return values[inside]
        if algo == "JAC":
            from pyeit.eit.interp2d import sim2pts

            values = sim2pts(self.mesh.node, self.mesh.element, values)
        interp = LinearTriInterpolator(self.tri, values)
        return np.asarray(interp(self.xg.ravel()[inside], self.yg.ravel()[inside]).filled(0.0))

    def grid_xy(self):
        inside = ~self.gmask
        return self.xg.ravel()[inside], self.yg.ravel()[inside]

    def simulate_relative(self, perm: np.ndarray) -> np.ndarray:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            v1 = np.real(self.fwd.solve_eit(perm=perm))
        return (v1 - self.v0) / self.v0


def reconstruct_study(solvers: Solvers, labels: list, aggs: list, masks: list, refs_abs: list, tasks: list, rc: dict):
    """Images for every (algorithm, session label, task) + metrics table."""
    gx, gy = solvers.grid_xy()
    left, lower = gx < 0, gy < 0
    rng = np.random.default_rng(rc["noise_seed"])
    images, rows = {}, []
    for lab, agg, keep, ref_abs in zip(labels, aggs, masks, refs_abs):
        sig = rc["noise_counts"] / ref_abs
        noise = {a: [] for a in ALGOS}
        for _ in range(rc["noise_draws"]):
            rec = solvers.reconstruct(rng.normal(size=sig.size) * sig, keep)
            for a in ALGOS:
                noise[a].append(np.linalg.norm(solvers.on_grid(a, rec[a])))
        for t in tasks:
            if t not in agg:
                continue
            rec = solvers.reconstruct(np.real(agg[t]), keep)
            for a in ALGOS:
                images[(a, lab, t)] = rec[a]
                g = solvers.on_grid(a, rec[a])
                rows.append({"algorithm": a, "label": lab, "task": t, "n_patterns_used": int(keep.sum()),
                             "left_energy_fraction": np.sum(g[left] ** 2) / np.sum(g ** 2),
                             "lower_energy_fraction": np.sum(g[lower] ** 2) / np.sum(g ** 2),
                             "image_to_noise": np.linalg.norm(g) / np.median(noise[a])})
    return images, pd.DataFrame(rows)


def image_correlations(solvers: Solvers, images: dict, labels: list, tasks: list):
    across, between = [], []
    for t in tasks:
        for a in ALGOS:
            for la, lb in itertools.combinations(labels, 2):
                if (a, la, t) in images and (a, lb, t) in images:
                    r = np.corrcoef(solvers.on_grid(a, images[(a, la, t)]), solvers.on_grid(a, images[(a, lb, t)]))[0, 1]
                    across.append({"algorithm": a, "task": t, "session_a": la, "session_b": lb, "image_corr": r})
        for lab in labels:
            for a1, a2 in itertools.combinations(ALGOS, 2):
                if (a1, lab, t) in images:
                    r = np.corrcoef(solvers.on_grid(a1, images[(a1, lab, t)]), solvers.on_grid(a2, images[(a2, lab, t)]))[0, 1]
                    between.append({"label": lab, "task": t, "algo_a": a1, "algo_b": a2, "image_corr": r})
    return pd.DataFrame(across), pd.DataFrame(between)


def disk_model_fit(solvers: Solvers, labels: list, refs: list) -> pd.DataFrame:
    """How well the homogeneous disk reproduces the measured rest pattern (Spearman rho of log|V|)."""
    sim = pd.Series(np.log(np.abs(solvers.v0)))
    return pd.DataFrame([{"label": lab, "spearman_log_abs_v_rest_vs_disk": float(
        pd.Series(np.log(np.abs(ref))).corr(sim, method="spearman"))} for lab, ref in zip(labels, refs)])


def known_target(solvers: Solvers, keep: np.ndarray, ref_abs: np.ndarray, noise_counts: float,
                 center=(-0.45, -0.45), radius=0.25, contrast=1.5, seed=5):
    """Forward-simulate a known conductivity blob in the disk and reconstruct it (clean and noisy)."""
    from pyeit.mesh.wrapper import PyEITAnomaly_Circle, set_perm

    blob = PyEITAnomaly_Circle(center=list(center), r=radius, perm=contrast)
    perm = np.real(set_perm(solvers.mesh, anomaly=blob, background=1.0).perm)
    y = solvers.simulate_relative(perm)
    rng = np.random.default_rng(seed)
    noisy = y + rng.normal(size=y.size) * (noise_counts / ref_abs)
    return {"perm": perm, "y": y, "clean": solvers.reconstruct(y, keep), "noisy": solvers.reconstruct(noisy, keep),
            "median_abs_change_pct": float(100 * np.median(np.abs(y[keep])))}
