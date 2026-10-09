r"""BP vs JAC vs GREIT on the 10 / 50 / 80 kHz facial pilot sessions (2026-10-05).

EXPLORATORY 2-D disk projection, not facial anatomy. Same pyEIT solvers and
settings as ``scripts/eit_sim_playground.py`` (BP weight="none"; JAC kotre,
p=0.5, lambda=0.01; GREIT p=0.5, lambda=0.01, n=32, s=20, ratio=0.1;
perm=1, jac_normalized=True), on a unit disk with 16 point electrodes in ring
order L1..L8 (down the left), R8..R1 (up the right).

Time-difference imaging of the six tasks, each against the REST frame of the
same session (REST itself is the reference and is not plotted). Data handling
is identical for the three algorithms:

* relative change ``y = Re((v_task - v_REST) / v_REST)`` per pattern, so gain,
  phase and polarity of each measured channel cancel;
* "transplant" onto the model: the solvers see ``v0 = v0_sim`` and
  ``v1 = v0_sim * (1 + y)``, i.e. the measured relative change applied to the
  simulated homogeneous reference;
* rows with ``|v_REST| < 50`` counts (noise-dominated) are removed; each
  solver's H is recomputed from pyEIT's own J / B / grid weights with exactly
  pyEIT's formulas on the kept rows (checked against ``solver.solve`` with
  all rows kept).

macOS/Linux:  .venv-sim/bin/python scripts/analysis/algorithm_comparison.py
"""

from __future__ import annotations

import argparse
import itertools
import json
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from matplotlib.tri import LinearTriInterpolator, Triangulation

from three_frequency_report import (
    DIV,
    INK,
    INK2,
    N_EL,
    NOISE_COUNTS,
    REPO,
    SESSION_NAMES,
    STRONG_COUNTS,
    TASKS,
    freq_label,
    load_session,
    resolve_session,
    ring_xy,
    save,
)

H0 = 0.08
P_VAL = 0.5
LAMB_VAL = 0.01
JAC_METHOD = "kotre"
BP_WEIGHT = "none"
GREIT_N = 32
GREIT_S = 20.0
GREIT_RATIO = 0.1
NOISE_DRAWS = 200
ALGOS = ("BP", "JAC", "GREIT")
DIV_CLEAR = DIV.copy()
DIV_CLEAR.set_bad((0, 0, 0, 0))  # GREIT pixels outside the disk stay transparent


class Solvers:
    """pyEIT BP/JAC/GREIT on the ring disk, with H recomputable on a row subset."""

    def __init__(self):
        import pyeit.eit.bp as bp
        import pyeit.eit.greit as greit
        import pyeit.eit.jac as jac
        import pyeit.eit.protocol as protocol
        import pyeit.mesh as mesh
        from pyeit.eit.fem import EITForward

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.mesh = mesh.create(N_EL, h0=H0, p_fix=ring_xy())
            self.proto = protocol.create(N_EL, 1, 1, "std")
            self.bp = bp.BP(self.mesh, self.proto)
            self.bp.setup(weight=BP_WEIGHT)
            self.jac = jac.JAC(self.mesh, self.proto)
            self.jac.setup(p=P_VAL, lamb=LAMB_VAL, method=JAC_METHOD, perm=1.0, jac_normalized=True)
            self.greit = greit.GREIT(self.mesh, self.proto)
            self.greit.setup(p=P_VAL, lamb=LAMB_VAL, n=GREIT_N, s=GREIT_S, ratio=GREIT_RATIO, perm=1.0,
                             jac_normalized=True)
            self.fwd = EITForward(self.mesh, self.proto)
            self.v0 = np.real(self.fwd.solve_eit())
        self.xy = self.mesh.node[:, :2]
        self.tri = Triangulation(self.xy[:, 0], self.xy[:, 1], self.mesh.element)
        self.xg, self.yg, self.gmask = self.greit.get_grid()
        self.w_mat = self.greit._compute_grid_weights(self.xg, self.yg)
        self._cache = {}
        self._check_against_pyeit()

    # pyEIT formulas, restricted to rows ``keep``
    def h_matrices(self, keep: np.ndarray) -> dict:
        key = keep.tobytes()
        if key not in self._cache:
            jn = np.real(self.jac.J)[keep]
            jtj = jn.T @ jn
            h_jac = np.linalg.solve(jtj + LAMB_VAL * np.diag(np.diag(jtj) ** P_VAL), jn.T)
            jg = np.real(self.greit.J)[keep]
            jjt = jg @ jg.T
            h_greit = (self.w_mat.T @ jg.T) @ np.linalg.inv(jjt + LAMB_VAL * np.diag(np.diag(jjt) ** P_VAL))
            h_bp = np.real(self.bp.H)[:, keep]
            self._cache[key] = {"BP": h_bp, "JAC": h_jac, "GREIT": h_greit}
        return self._cache[key]

    def reconstruct(self, y: np.ndarray, keep: np.ndarray) -> dict:
        """y: relative change per pattern (208). Returns BP nodes, JAC elements, GREIT grid vector."""
        v0 = self.v0[keep]
        h = self.h_matrices(keep)
        dv_bp = (v0 * y[keep]) / np.sign(v0)  # BP._normalize: (v1 - v0) / sign(v0)
        dv = (v0 * y[keep]) / np.abs(v0)  # EitBase._normalize: (v1 - v0) / |v0|
        return {"BP": -h["BP"] @ dv_bp, "JAC": -h["JAC"] @ dv, "GREIT": -h["GREIT"] @ dv}

    def _check_against_pyeit(self):
        rng = np.random.default_rng(3)
        y = rng.normal(scale=0.01, size=self.v0.size)
        v1 = self.v0 * (1 + y)
        mine = self.reconstruct(y, np.ones(self.v0.size, bool))
        ref = {
            "BP": np.real(self.bp.solve(v1, self.v0, normalize=True)),
            "JAC": np.real(self.jac.solve(v1, self.v0, normalize=True)),
            "GREIT": np.real(self.greit.solve(v1, self.v0, normalize=True)),
        }
        for a in ALGOS:
            if not np.allclose(mine[a], ref[a], rtol=1e-6, atol=1e-9 * np.abs(ref[a]).max()):
                raise RuntimeError(f"{a}: subset formula does not reproduce pyEIT solve()")

    # common grid (GREIT pixels inside the disk) for metrics and cross-algorithm comparison
    def on_grid(self, algo: str, values: np.ndarray) -> np.ndarray:
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


def compute(sessions, solvers: Solvers):
    gx, gy = solvers.grid_xy()
    left, lower = gx < 0, gy < 0
    images, rows = {}, []
    rng = np.random.default_rng(11)
    for s in sessions:
        v_rest = s["v"]["REST"]
        keep = np.abs(v_rest) >= STRONG_COUNTS
        sig = NOISE_COUNTS / np.abs(v_rest)
        noise_norm = {a: [] for a in ALGOS}
        for _ in range(NOISE_DRAWS):
            rec = solvers.reconstruct(rng.normal(size=sig.size) * sig, keep)
            for a in ALGOS:
                noise_norm[a].append(np.linalg.norm(solvers.on_grid(a, rec[a])))
        for task in TASKS:
            y = np.real((s["v"][task] - v_rest) / v_rest)
            rec = solvers.reconstruct(y, keep)
            for a in ALGOS:
                images[(a, s["freq"], task)] = rec[a]
                g = solvers.on_grid(a, rec[a])
                rows.append(
                    {
                        "algorithm": a,
                        "freq_hz": s["freq"],
                        "task": task,
                        "n_patterns_used": int(keep.sum()),
                        "left_energy_fraction": np.sum(g[left] ** 2) / np.sum(g**2),
                        "lower_energy_fraction": np.sum(g[lower] ** 2) / np.sum(g**2),
                        "image_to_noise": np.linalg.norm(g) / np.median(noise_norm[a]),
                    }
                )
    return images, pd.DataFrame(rows)


def correlations(sessions, solvers, images):
    freqs = [s["freq"] for s in sessions]
    xf, xa = [], []
    for task in TASKS:
        for a in ALGOS:
            for f1, f2 in itertools.combinations(freqs, 2):
                g1 = solvers.on_grid(a, images[(a, f1, task)])
                g2 = solvers.on_grid(a, images[(a, f2, task)])
                xf.append({"algorithm": a, "task": task, "freq_a_hz": f1, "freq_b_hz": f2,
                           "image_corr": np.corrcoef(g1, g2)[0, 1]})
        for f in freqs:
            for a1, a2 in itertools.combinations(ALGOS, 2):
                g1 = solvers.on_grid(a1, images[(a1, f, task)])
                g2 = solvers.on_grid(a2, images[(a2, f, task)])
                xa.append({"freq_hz": f, "task": task, "algo_a": a1, "algo_b": a2,
                           "image_corr": np.corrcoef(g1, g2)[0, 1]})
    return pd.DataFrame(xf), pd.DataFrame(xa)


# --------------------------------------------------------------------------
# Plotting
# --------------------------------------------------------------------------


def draw(ax, solvers, algo, values, norm, label_sites=None):
    if algo == "GREIT":
        grid = values.copy()
        grid[solvers.gmask] = np.nan
        grid = grid.reshape(solvers.xg.shape)
        im = ax.imshow(np.ma.masked_invalid(grid), origin="lower", cmap=DIV_CLEAR, norm=norm, interpolation="none",
                       extent=[solvers.xg.min(), solvers.xg.max(), solvers.yg.min(), solvers.yg.max()])
    elif algo == "JAC":
        im = ax.tripcolor(solvers.tri, facecolors=values, cmap=DIV, norm=norm, shading="flat")
    else:
        im = ax.tripcolor(solvers.tri, values, cmap=DIV, norm=norm, shading="gouraud")
    el = solvers.xy[solvers.mesh.el_pos]
    ax.scatter(el[:, 0], el[:, 1], s=6, color=INK, zorder=3)
    if label_sites is not None:
        for i, (x, y) in enumerate(el):
            ax.text(1.22 * x, 1.22 * y, label_sites[i], ha="center", va="center", fontsize=5.5, color=INK2)
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")
    return im


def algo_norms(images, freqs):
    norms = {}
    for a in ALGOS:
        lim = float(np.percentile(np.concatenate([np.abs(images[(a, f, t)]) for f in freqs for t in TASKS]), 99))
        norms[a] = TwoSlopeNorm(0, -lim, lim)
    return norms


COLOR_NOTE = "blue = less conductive than at REST, red = more conductive (in the 2-D model)"


def fig_overview(sessions, solvers, images, metrics):
    freqs = [s["freq"] for s in sessions]
    norms = algo_norms(images, freqs)
    snr = metrics.set_index(["algorithm", "freq_hz", "task"])["image_to_noise"]
    ncol = len(ALGOS) * len(freqs)
    fig, axes = plt.subplots(len(TASKS), ncol, figsize=(1.75 * ncol + 1.2, 1.85 * len(TASKS) + 1.6),
                             constrained_layout=True)
    sites = sessions[0]["sites"]
    for ai, a in enumerate(ALGOS):
        for fi, f in enumerate(freqs):
            c = ai * len(freqs) + fi
            for r, task in enumerate(TASKS):
                ax = axes[r, c]
                im = draw(ax, solvers, a, images[(a, f, task)], norms[a],
                          label_sites=sites if (r == 0 and c == 0) else None)
                ax.text(0, -1.42, f"img/noise {snr[(a, f, task)]:.1f}", ha="center", va="top", fontsize=5.5,
                        color=INK2)
                if r == 0:
                    ax.set_title(f"{a}\n{freq_label(f)}", fontsize=8.5)
                if c == 0:
                    ax.text(-1.75, 0, task.replace("_", "\n"), ha="right", va="center", fontsize=7.5)
        cb = fig.colorbar(im, ax=axes[:, ai * len(freqs):(ai + 1) * len(freqs)], location="bottom", shrink=0.8,
                          aspect=30, pad=0.01)
        cb.set_label(f"{a}: d(sigma) vs REST, a.u.", fontsize=7)
        cb.ax.tick_params(labelsize=6)
    fig.suptitle(
        "BP vs JAC vs GREIT at 10 / 50 / 80 kHz: change of each task relative to REST (time-difference)\n"
        f"EXPLORATORY 2-D disk projection (NOT anatomy); {COLOR_NOTE}. Subject's left drawn left; "
        "top = forehead (L1/R1), bottom = chin (L8/R8). One colour scale per algorithm.",
        x=0.01, ha="left", fontsize=9,
    )
    return fig


def fig_per_frequency(sessions, solvers, images, metrics, s):
    norms = algo_norms(images, [x["freq"] for x in sessions])
    snr = metrics.set_index(["algorithm", "freq_hz", "task"])["image_to_noise"]
    f = s["freq"]
    fig, axes = plt.subplots(len(TASKS), len(ALGOS), figsize=(6.6, 13.5), constrained_layout=True)
    for c, a in enumerate(ALGOS):
        for r, task in enumerate(TASKS):
            ax = axes[r, c]
            im = draw(ax, solvers, a, images[(a, f, task)], norms[a],
                      label_sites=s["sites"] if (r == 0 and c == 0) else None)
            ax.text(0, -1.42, f"img/noise {snr[(a, f, task)]:.1f}", ha="center", va="top", fontsize=6.5, color=INK2)
            if r == 0:
                ax.set_title(a, fontsize=10)
            if c == 0:
                ax.text(-1.7, 0, task.replace("_", "\n"), ha="right", va="center", fontsize=8.5)
        cb = fig.colorbar(im, ax=axes[:, c], location="bottom", shrink=0.9, pad=0.01)
        cb.set_label(f"{a} d(sigma) vs REST, a.u.", fontsize=7)
        cb.ax.tick_params(labelsize=6)
    fig.suptitle(f"BP vs JAC vs GREIT, {freq_label(f)}: change of each task relative to REST\n"
                 f"EXPLORATORY 2-D disk projection, NOT anatomy\n{COLOR_NOTE}", x=0.01, ha="left", fontsize=9)
    return fig


def fig_known_blob(sessions, solvers):
    """What each algorithm does to a known target with this ring, mask and noise level."""
    from pyeit.mesh.wrapper import PyEITAnomaly_Circle, set_perm

    s = sessions[0]
    keep = np.abs(s["v"]["REST"]) >= STRONG_COUNTS
    sig = NOISE_COUNTS / np.abs(s["v"]["REST"])
    blob = PyEITAnomaly_Circle(center=[-0.45, -0.45], r=0.25, perm=1.5)
    perm = np.real(set_perm(solvers.mesh, anomaly=blob, background=1.0).perm)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        v1 = np.real(solvers.fwd.solve_eit(perm=perm))
    y = (v1 - solvers.v0) / solvers.v0
    rng = np.random.default_rng(5)
    noisy = y + rng.normal(size=y.size) * sig
    fig, axes = plt.subplots(2, 4, figsize=(11, 6), constrained_layout=True)
    for r, (data, label) in enumerate([(y, "no noise"), (noisy, "+ measured-level noise (2 counts/|v_REST|)")]):
        draw(axes[r, 0], solvers, "JAC", perm - 1.0, TwoSlopeNorm(0, -0.5, 0.5),
             label_sites=s["sites"] if r == 0 else None)
        axes[r, 0].set_title(f"truth: +50% blob\n({label})", fontsize=8)
        rec = solvers.reconstruct(data, keep)
        clean = solvers.reconstruct(y, keep)
        for c, a in enumerate(ALGOS, start=1):
            lim = np.abs(clean[a]).max()
            draw(axes[r, c], solvers, a, rec[a], TwoSlopeNorm(0, -lim, lim))
            axes[r, c].set_title(a, fontsize=9)
    fig.suptitle(
        f"Known-target check on the same disk, electrode ring and pattern mask as the 10 kHz data "
        f"(n={int(keep.sum())} patterns)\nmedian |dz| of this +50% blob on kept patterns = "
        f"{100 * np.median(np.abs(y[keep])):.2f}% (measured tasks: 1.8-5.1%)",
        x=0.01, ha="left", fontsize=9,
    )
    return fig


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions", nargs="+", default=list(SESSION_NAMES))
    ap.add_argument("--out", default=str(REPO / "data/processed/pilot/three-frequency-20261005/algorithms"))
    args = ap.parse_args()

    sessions = sorted((load_session(resolve_session(n)) for n in args.sessions), key=lambda s: s["freq"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    solvers = Solvers()
    images, metrics = compute(sessions, solvers)
    xf, xa = correlations(sessions, solvers, images)
    metrics.to_csv(out / "T9_algorithm_metrics.csv", index=False)
    xf.to_csv(out / "T9b_algorithm_crossfreq_corr.csv", index=False)
    xa.to_csv(out / "T9c_cross_algorithm_corr.csv", index=False)

    save(fig_overview(sessions, solvers, images, metrics), out / "F12_bp_jac_greit_overview.png")
    for s in sessions:
        save(fig_per_frequency(sessions, solvers, images, metrics, s), out / f"F12_{s['freq'] // 1000}kHz_bp_jac_greit.png")
    save(fig_known_blob(sessions, solvers), out / "F14_algorithms_known_blob.png")

    settings = {"h0": H0, "p": P_VAL, "lambda": LAMB_VAL, "jac_method": JAC_METHOD, "bp_weight": BP_WEIGHT,
                "greit_n": GREIT_N, "greit_s": GREIT_S, "greit_ratio": GREIT_RATIO,
                "strong_counts": STRONG_COUNTS, "noise_counts": NOISE_COUNTS,
                "n_elements": int(solvers.mesh.n_elems), "n_nodes": int(solvers.mesh.n_nodes)}
    (out / "settings.json").write_text(json.dumps(settings, indent=2))
    print(f"written to {out}")


if __name__ == "__main__":
    main()
