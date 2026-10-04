r"""Compare CN0565/pyEIT reconstruction algorithms without hardware.

The default ``fig14`` preset is a *conceptual* reproduction of Figure 14 in
the CN0565 circuit note: a known conductivity distribution is forward-
simulated and the same voltage frames are reconstructed with BP, JAC, and
GREIT. The circuit note does not publish the exact target values or the code
used for its figure, so matching it pixel-for-pixel is not a valid goal.

This script models a 2-D unit-radius domain, point electrodes, ideal geometry,
unit-current FEM data, and (unless ``--noise-rel`` is used) no measurement
noise. It reconstructs *change from a reference frame*, not an absolute map.

Examples (Windows environment created by this repository):

    cn0565-env\Scripts\python.exe scripts\eit_sim_playground.py
    cn0565-env\Scripts\python.exe scripts\eit_sim_playground.py --preset single
    cn0565-env\Scripts\python.exe scripts\eit_sim_playground.py --noise-rel 0.001
    cn0565-env\Scripts\python.exe scripts\eit_sim_playground.py --save fig14.png --no-show
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pyeit.eit.bp as bp
import pyeit.eit.greit as greit
import pyeit.eit.jac as jac
import pyeit.eit.protocol as protocol
import pyeit.mesh as mesh
from pyeit.eit.fem import EITForward
from pyeit.eit.interp2d import sim2pts
from pyeit.mesh.wrapper import PyEITAnomaly_Circle


# Baseline configuration. Coordinates and radii are fractions of the unit
# domain radius. Conductivities are ratios relative to BACKGROUND_SIGMA=1.
N_EL = 16
H0 = 0.08
DIST_EXC = 1
STEP_MEAS = 1
PARSER_MEAS = "std"
BACKGROUND_SIGMA = 1.0

# In pyEIT 1.2.4, JAC uses R=diag(diag(J.T@J)**p) for method="kotre" and
# H=inv(J.T@J + lamb*R)@J.T. ``p`` is ignored by methods "lm" and "dgn".
P_VAL = 0.5
LAMB_VAL = 0.01
JAC_METHOD = "kotre"
BP_WEIGHT = "none"

# pyEIT's GREIT output/interpolation controls. n changes output sampling, not
# the amount of information measured by the electrodes.
GREIT_N = 32
GREIT_S = 20.0
GREIT_RATIO = 0.1

# Approximation of the four contrasts visible in CN0565 Figure 14. The paper
# does not publish the exact values. A value 10 means 10x the background
# conductivity (therefore 0.1x its resistivity), not "10 ohms".
FIG14_ANOMALIES = (
    PyEITAnomaly_Circle(center=[-0.50, 0.50], r=0.12, perm=0.10),
    PyEITAnomaly_Circle(center=[0.50, 0.50], r=0.12, perm=10.0),
    PyEITAnomaly_Circle(center=[-0.50, -0.50], r=0.12, perm=5.0),
    PyEITAnomaly_Circle(center=[0.50, -0.50], r=0.12, perm=0.10),
)
SINGLE_ANOMALY = (
    PyEITAnomaly_Circle(center=[0.50, 0.50], r=0.20, perm=10.0),
)


def add_relative_noise(
    values: np.ndarray, relative_std: float, rng: np.random.Generator
):
    """Add zero-mean noise whose std is relative to RMS(reference voltage)."""
    if relative_std == 0:
        return values.copy()
    scale = relative_std * np.sqrt(np.mean(np.abs(values) ** 2))
    if np.iscomplexobj(values):
        noise = (
            rng.normal(size=values.shape) + 1j * rng.normal(size=values.shape)
        ) / np.sqrt(2)
    else:
        noise = rng.normal(size=values.shape)
    return values + scale * noise


def symmetric_norm(values: np.ndarray) -> TwoSlopeNorm:
    """Return a zero-centred colour scale for one panel."""
    finite = np.asarray(values)[np.isfinite(values)]
    limit = float(np.max(np.abs(finite))) if finite.size else 1.0
    if limit == 0:
        limit = 1.0
    return TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit)


def reconstruct_all(mesh_obj, protocol_obj, v1: np.ndarray, v0: np.ndarray):
    """Reconstruct the same normalized difference data with all three solvers."""
    bp_solver = bp.BP(mesh_obj, protocol_obj)
    bp_solver.setup(weight=BP_WEIGHT)
    bp_nodes = np.real(bp_solver.solve(v1, v0, normalize=True))

    jac_solver = jac.JAC(mesh_obj, protocol_obj)
    jac_solver.setup(
        p=P_VAL,
        lamb=LAMB_VAL,
        method=JAC_METHOD,
        perm=BACKGROUND_SIGMA,
        jac_normalized=True,
    )
    jac_elements = np.real(jac_solver.solve(v1, v0, normalize=True))
    jac_nodes = sim2pts(mesh_obj.node, mesh_obj.element, jac_elements)

    greit_solver = greit.GREIT(mesh_obj, protocol_obj)
    greit_solver.setup(
        p=P_VAL,
        lamb=LAMB_VAL,
        n=GREIT_N,
        s=GREIT_S,
        ratio=GREIT_RATIO,
        perm=BACKGROUND_SIGMA,
        jac_normalized=True,
    )
    greit_vector = np.real(greit_solver.solve(v1, v0, normalize=True))
    xg, yg, greit_grid = greit_solver.mask_value(greit_vector, mask_value=np.nan)

    return bp_nodes, jac_nodes, (xg, yg, greit_grid)


def plot_comparison(mesh_obj, mesh_target, reconstructions, title: str):
    """Plot true conductivity change and the three reconstructed changes."""
    nodes = mesh_obj.node
    elements = mesh_obj.element
    delta_sigma = np.real(mesh_target.perm - BACKGROUND_SIGMA)
    bp_nodes, jac_nodes, (xg, yg, greit_grid) = reconstructions

    fig, axes = plt.subplots(2, 2, figsize=(10, 9), constrained_layout=True)
    fig.suptitle(title)

    ax = axes[0, 0]
    im = ax.tripcolor(
        nodes[:, 0],
        nodes[:, 1],
        elements,
        facecolors=delta_sigma,
        shading="flat",
        cmap="coolwarm",
        norm=symmetric_norm(delta_sigma),
    )
    ax.set_title(r"Ground truth: $\Delta\sigma/\sigma_{bg}$")
    fig.colorbar(im, ax=ax)

    for ax, values, label in (
        (axes[0, 1], bp_nodes, "Back projection (BP)"),
        (axes[1, 0], jac_nodes, f"JAC ({JAC_METHOD}, p={P_VAL}, lambda={LAMB_VAL})"),
    ):
        im = ax.tripcolor(
            nodes[:, 0],
            nodes[:, 1],
            elements,
            values,
            shading="flat",
            cmap="coolwarm",
            norm=symmetric_norm(values),
        )
        ax.set_title(label)
        fig.colorbar(im, ax=ax)

    ax = axes[1, 1]
    im = ax.imshow(
        greit_grid,
        origin="lower",
        extent=[xg.min(), xg.max(), yg.min(), yg.max()],
        interpolation="none",
        cmap="coolwarm",
        norm=symmetric_norm(greit_grid),
    )
    ax.set_title(
        f"pyEIT GREIT (p={P_VAL}, lambda={LAMB_VAL})\n"
        f"n={GREIT_N}, s={GREIT_S}, ratio={GREIT_RATIO}"
    )
    fig.colorbar(im, ax=ax)

    for ax in axes.flat:
        ax.set_aspect("equal")
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
        ax.set_xlabel("x / tank radius")
        ax.set_ylabel("y / tank radius")

    return fig


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preset",
        choices=("fig14", "single", "null"),
        default="fig14",
        help="Known target distribution; null verifies zero response (default: fig14).",
    )
    parser.add_argument(
        "--noise-rel",
        type=float,
        default=0.0,
        help="Gaussian noise std divided by RMS boundary voltage (default: 0).",
    )
    parser.add_argument("--seed", type=int, default=0, help="Noise random seed.")
    parser.add_argument("--save", type=Path, help="Optional output PNG/PDF path.")
    parser.add_argument(
        "--no-show", action="store_true", help="Do not open a plot window."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.noise_rel < 0:
        raise ValueError("--noise-rel must be >= 0")

    mesh_obj = mesh.create(N_EL, h0=H0)
    protocol_obj = protocol.create(
        N_EL,
        dist_exc=DIST_EXC,
        step_meas=STEP_MEAS,
        parser_meas=PARSER_MEAS,
    )
    if args.preset == "fig14":
        anomalies = FIG14_ANOMALIES
    elif args.preset == "single":
        anomalies = SINGLE_ANOMALY
    else:
        anomalies = ()
    mesh_target = mesh.set_perm(
        mesh_obj, anomaly=list(anomalies), background=BACKGROUND_SIGMA
    )

    forward = EITForward(mesh_obj, protocol_obj)
    v0_clean = forward.solve_eit()
    v1_clean = forward.solve_eit(perm=mesh_target.perm)
    rng = np.random.default_rng(args.seed)
    v0 = add_relative_noise(v0_clean, args.noise_rel, rng)
    v1 = add_relative_noise(v1_clean, args.noise_rel, rng)

    reconstructions = reconstruct_all(mesh_obj, protocol_obj, v1, v0)
    fig = plot_comparison(
        mesh_obj,
        mesh_target,
        reconstructions,
        title=(
            f"CN0565/pyEIT preset={args.preset} comparison | {N_EL} electrodes, "
            f"adjacent drive/measure, relative noise={args.noise_rel:g}"
        ),
    )

    print(
        f"mesh: {mesh_obj.n_nodes} nodes, {mesh_obj.n_elems} elements; "
        f"protocol: {protocol_obj.n_exc} excitations, "
        f"{protocol_obj.n_meas_tot} voltage differences"
    )
    print(f"reference voltage RMS: {np.sqrt(np.mean(np.abs(v0_clean) ** 2)):.6g}")
    for name, values in (
        ("BP", reconstructions[0]),
        ("JAC", reconstructions[1]),
        ("GREIT", reconstructions[2][2]),
    ):
        print(f"{name:5s}: min={np.nanmin(values): .6g}, max={np.nanmax(values): .6g}")

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.save, dpi=180)
        print(f"saved: {args.save}")
    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
