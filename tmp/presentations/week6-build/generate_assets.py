from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Circle, FancyArrowPatch
import numpy as np
import pyeit.eit.protocol as protocol
import pyeit.mesh as mesh
from pyeit.eit.fem import EITForward
from pyeit.mesh.wrapper import PyEITAnomaly_Circle

WORKSPACE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE_DIR))

from scripts.eit_sim_playground import (
    BACKGROUND_SIGMA,
    DIST_EXC,
    FIG14_ANOMALIES,
    H0,
    N_EL,
    PARSER_MEAS,
    STEP_MEAS,
    reconstruct_all,
    add_relative_noise,
)


def clean_axis(ax):
    ax.set_aspect("equal")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_xlabel("x / tank radius")
    ax.set_ylabel("y / tank radius")


def save_eit_setup(out_dir: Path):
    """Draw a conceptual 16-electrode EIT measurement, not a field solution."""
    fig, ax = plt.subplots(figsize=(8.4, 6.0), constrained_layout=True)
    ax.add_patch(Circle((0, 0), 1.0, facecolor="#EDF1F4", edgecolor="#34495E", lw=2.2))
    ax.add_patch(Circle((0.25, 0.10), 0.22, facecolor="#E85D75", edgecolor="#8C1D40", lw=1.5))
    ax.text(0.25, 0.10, "object\n$\\sigma_{target} \\ne \\sigma_{bg}$", ha="center", va="center", fontsize=12, weight="bold")

    theta = np.pi / 2 - np.arange(16) * 2 * np.pi / 16
    xy = np.column_stack((np.cos(theta), np.sin(theta)))
    drive = {0: "+I", 1: "−I"}
    sense = {5: "V+", 6: "V−"}
    for i, (x, y) in enumerate(xy):
        color = "#C51B3A" if i in drive else "#276FBF" if i in sense else "#FFFFFF"
        ax.add_patch(Circle((x, y), 0.075, facecolor=color, edgecolor="#263238", lw=1.0, zorder=5))
        ax.text(1.16 * x, 1.16 * y, str(i + 1), ha="center", va="center", fontsize=9, color="#263238")
        if i in drive:
            ax.text(x, y, drive[i], ha="center", va="center", fontsize=9, color="white", weight="bold", zorder=6)
        if i in sense:
            ax.text(x, y, sense[i], ha="center", va="center", fontsize=8, color="white", weight="bold", zorder=6)

    source = xy[0]
    sink = xy[1]
    for rad, alpha in ((0.35, 0.65), (0.75, 0.42), (-0.42, 0.36)):
        ax.add_patch(
            FancyArrowPatch(
                source * 0.94,
                sink * 0.94,
                connectionstyle=f"arc3,rad={rad}",
                arrowstyle="-|>",
                mutation_scale=12,
                color="#C51B3A",
                lw=1.5,
                alpha=alpha,
            )
        )
    ax.plot([xy[5, 0], xy[6, 0]], [xy[5, 1], xy[6, 1]], color="#276FBF", lw=3.0, zorder=4)
    ax.text(-0.32, -0.42, "conductive medium  $\\sigma_{bg}$", ha="center", va="center", fontsize=13, color="#34495E")
    ax.text(0, -1.35, "Red: one adjacent current-drive pair    Blue: one adjacent voltage-sense pair", ha="center", fontsize=11)
    ax.text(0, -1.53, "Illustration only: reconstruction uses all drive and sense combinations", ha="center", fontsize=10, color="#666666")
    ax.set_title("EIT sees boundary-voltage changes, not the object directly", fontsize=17)
    ax.set_aspect("equal")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.62, 1.30)
    ax.axis("off")
    fig.savefig(out_dir / "eit_setup.png", dpi=190, facecolor="white")
    plt.close(fig)


def save_ground_truth(out_dir: Path, mesh_obj, mesh_target):
    nodes = mesh_obj.node
    elements = mesh_obj.element
    log_ratio = np.log10(np.real(mesh_target.perm) / BACKGROUND_SIGMA)
    fig, ax = plt.subplots(figsize=(8.2, 6.2), constrained_layout=True)
    im = ax.tripcolor(
        nodes[:, 0],
        nodes[:, 1],
        elements,
        facecolors=log_ratio,
        shading="flat",
        cmap="coolwarm",
        norm=TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0),
    )
    labels = (
        (-0.50, 0.50, "0.1×"),
        (0.50, 0.50, "10×"),
        (-0.50, -0.50, "5×"),
        (0.50, -0.50, "0.1×"),
    )
    for x, y, label in labels:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=15,
            weight="bold",
            color="white" if label != "5×" else "black",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "black", "alpha": 0.28, "edgecolor": "none"},
        )
    clean_axis(ax)
    ax.set_title("Ground truth: conductivity ratio relative to background", fontsize=17)
    cbar = fig.colorbar(im, ax=ax, fraction=0.048, pad=0.04)
    cbar.set_label(r"$\log_{10}(\sigma/\sigma_{bg})$")
    fig.savefig(out_dir / "ground_truth.png", dpi=180, facecolor="white")
    plt.close(fig)


def save_mesh(out_dir: Path, mesh_obj):
    nodes = mesh_obj.node
    elements = mesh_obj.element
    el_nodes = mesh_obj.el_pos
    fig, ax = plt.subplots(figsize=(8.2, 6.2), constrained_layout=True)
    ax.triplot(nodes[:, 0], nodes[:, 1], elements, color="#4A6478", linewidth=0.45)
    ax.scatter(nodes[:, 0], nodes[:, 1], s=3, color="#1C3445", alpha=0.55)
    ep = nodes[el_nodes, :2]
    ax.scatter(ep[:, 0], ep[:, 1], s=55, color="#C51B3A", edgecolor="white", linewidth=0.8, zorder=3)
    clean_axis(ax)
    ax.set_title(f"{mesh_obj.n_nodes} nodes and {mesh_obj.n_elems} triangular elements", fontsize=17)
    fig.savefig(out_dir / "mesh.png", dpi=180, facecolor="white")
    plt.close(fig)


def save_mesh_sweep(out_dir: Path):
    values = (0.16, 0.12, 0.08, 0.06)
    fig, axes = plt.subplots(1, 4, figsize=(14.2, 3.8), constrained_layout=True)
    for ax, h0 in zip(axes, values):
        candidate = mesh.create(N_EL, h0=h0)
        nodes = candidate.node
        elements = candidate.element
        ax.triplot(nodes[:, 0], nodes[:, 1], elements, color="#4A6478", linewidth=0.35)
        ep = nodes[candidate.el_pos, :2]
        ax.scatter(ep[:, 0], ep[:, 1], s=18, color="#C51B3A", zorder=3)
        ax.set_title(f"h0 = {h0:g}\n{candidate.n_nodes} nodes, {candidate.n_elems} elements", fontsize=10.5)
        ax.set_aspect("equal")
        ax.set_xlim(-1.04, 1.04)
        ax.set_ylim(-1.04, 1.04)
        ax.axis("off")
    fig.suptitle("Smaller h0 requests a finer triangular mesh", fontsize=16)
    fig.savefig(out_dir / "mesh_sweep.png", dpi=190, facecolor="white")
    plt.close(fig)


def save_voltage_frames(out_dir: Path, v0, v1):
    v0 = np.real(v0)
    v1 = np.real(v1)
    dv = v1 - v0
    idx = np.arange(v0.size)
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 5.7), sharex=True, constrained_layout=True)
    axes[0].plot(idx, v0, color="#4A6478", linewidth=1.35, label=r"Reference frame $v_0$")
    axes[0].plot(idx, v1, color="#C51B3A", linewidth=1.05, alpha=0.88, label=r"Target frame $v_1$")
    axes[0].set_ylabel("Model voltage\n(arbitrary units)")
    axes[0].legend(frameon=False, ncol=2, loc="upper right")
    axes[0].grid(alpha=0.18)
    axes[1].axhline(0, color="#777777", linewidth=0.8)
    axes[1].plot(idx, dv, color="#6E1738", linewidth=1.2)
    axes[1].fill_between(idx, 0, dv, color="#6E1738", alpha=0.18)
    axes[1].set_xlabel("Measurement index")
    axes[1].set_ylabel(r"$\Delta v=v_1-v_0$")
    axes[1].grid(alpha=0.18)
    fig.suptitle("Two 208-value frames produce one 208-value change vector", fontsize=17)
    fig.savefig(out_dir / "voltage_frames.png", dpi=180, facecolor="white")
    plt.close(fig)


def normalize(values):
    arr = np.real(np.asarray(values))
    scale = np.nanmax(np.abs(arr))
    return arr / scale if scale > 0 else arr


def save_reconstruction_comparison(out_dir: Path, mesh_obj, mesh_target, reconstructions):
    nodes = mesh_obj.node
    elements = mesh_obj.element
    truth = np.log10(np.real(mesh_target.perm) / BACKGROUND_SIGMA)
    bp_nodes, jac_nodes, (xg, yg, greit_grid) = reconstructions
    panels = (
        ("Ground truth\nlog conductivity ratio", "mesh", truth),
        ("BP\nnormalized output", "mesh", normalize(bp_nodes)),
        ("JAC\nnormalized output", "mesh", normalize(jac_nodes)),
        ("GREIT\nnormalized output", "grid", normalize(greit_grid)),
    )
    fig, axes = plt.subplots(1, 4, figsize=(14.4, 4.2), constrained_layout=True)
    for ax, (title, kind, values) in zip(axes, panels):
        if kind == "mesh":
            if values.size == mesh_obj.n_elems:
                im = ax.tripcolor(
                    nodes[:, 0], nodes[:, 1], elements,
                    facecolors=values, shading="flat", cmap="coolwarm", vmin=-1, vmax=1,
                )
            else:
                im = ax.tripcolor(
                    nodes[:, 0], nodes[:, 1], elements, values,
                    shading="gouraud", cmap="coolwarm", vmin=-1, vmax=1,
                )
        else:
            im = ax.imshow(
                values, origin="lower",
                extent=[xg.min(), xg.max(), yg.min(), yg.max()],
                interpolation="none", cmap="coolwarm", vmin=-1, vmax=1,
            )
        ax.set_title(title, fontsize=13)
        ax.set_aspect("equal")
        ax.set_xlim(-1.03, 1.03)
        ax.set_ylim(-1.03, 1.03)
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])
        ax.tick_params(labelsize=8)
    cbar = fig.colorbar(im, ax=axes, fraction=0.018, pad=0.018)
    cbar.set_label("Negative / positive conductivity change", fontsize=10)
    fig.suptitle(
        "Qualitative comparison: each reconstruction is normalized independently",
        fontsize=16,
    )
    fig.text(
        0.5,
        0.006,
        "Compare target location, sign, spatial spread, and artifacts. Do not compare raw amplitude from this figure.",
        ha="center",
        fontsize=10,
        color="#444444",
    )
    fig.savefig(out_dir / "reconstruction_comparison.png", dpi=180, facecolor="white")
    plt.close(fig)


def save_multi_case_results(out_dir: Path, mesh_obj, protocol_obj, forward, v0_clean):
    cases = (
        ("Center target", [PyEITAnomaly_Circle(center=[0.0, 0.0], r=0.16, perm=2.0)], 0.0, 1),
        ("Near boundary", [PyEITAnomaly_Circle(center=[0.65, 0.0], r=0.13, perm=2.0)], 0.0, 2),
        ("Two close targets", [
            PyEITAnomaly_Circle(center=[-0.18, 0.0], r=0.11, perm=2.0),
            PyEITAnomaly_Circle(center=[0.18, 0.0], r=0.11, perm=2.0),
        ], 0.0, 3),
        ("0.1% voltage noise", [PyEITAnomaly_Circle(center=[0.30, 0.25], r=0.16, perm=2.0)], 0.001, 4),
    )
    nodes = mesh_obj.node
    elements = mesh_obj.element
    fig, axes = plt.subplots(len(cases), 4, figsize=(11.8, 10.6), constrained_layout=True)
    for row, (label, anomalies, noise_rel, seed) in enumerate(cases):
        target = mesh.set_perm(mesh_obj, anomaly=anomalies, background=BACKGROUND_SIGMA)
        v1_clean = forward.solve_eit(perm=target.perm)
        rng = np.random.default_rng(seed)
        v0 = add_relative_noise(v0_clean, noise_rel, rng)
        v1 = add_relative_noise(v1_clean, noise_rel, rng)
        bp_nodes, jac_nodes, (xg, yg, greit_grid) = reconstruct_all(mesh_obj, protocol_obj, v1, v0)
        truth = np.real(target.perm - BACKGROUND_SIGMA)
        panels = (("truth", truth), ("mesh", bp_nodes), ("mesh", jac_nodes), ("grid", greit_grid))
        for col, (kind, values) in enumerate(panels):
            ax = axes[row, col]
            values = normalize(values)
            if kind in ("truth", "mesh"):
                if values.size == mesh_obj.n_elems:
                    ax.tripcolor(nodes[:, 0], nodes[:, 1], elements, facecolors=values, shading="flat", cmap="coolwarm", vmin=-1, vmax=1)
                else:
                    ax.tripcolor(nodes[:, 0], nodes[:, 1], elements, values, shading="gouraud", cmap="coolwarm", vmin=-1, vmax=1)
            else:
                ax.imshow(values, origin="lower", extent=[xg.min(), xg.max(), yg.min(), yg.max()], interpolation="none", cmap="coolwarm", vmin=-1, vmax=1)
            ax.set_aspect("equal")
            ax.set_xlim(-1.02, 1.02)
            ax.set_ylim(-1.02, 1.02)
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(("Ground truth", "BP", "JAC", "GREIT")[col], fontsize=12, weight="bold")
            if col == 0:
                ax.set_ylabel(label, fontsize=10.5, rotation=90, labelpad=10)
    fig.suptitle("Controlled cases reveal position, separation, and noise behaviour", fontsize=16)
    fig.savefig(out_dir / "multi_case_results.png", dpi=190, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    mesh_obj = mesh.create(N_EL, h0=H0)
    protocol_obj = protocol.create(
        N_EL,
        dist_exc=DIST_EXC,
        step_meas=STEP_MEAS,
        parser_meas=PARSER_MEAS,
    )
    mesh_target = mesh.set_perm(
        mesh_obj,
        anomaly=list(FIG14_ANOMALIES),
        background=BACKGROUND_SIGMA,
    )
    forward = EITForward(mesh_obj, protocol_obj)
    v0 = forward.solve_eit()
    v1 = forward.solve_eit(perm=mesh_target.perm)
    reconstructions = reconstruct_all(mesh_obj, protocol_obj, v1, v0)

    save_ground_truth(args.output_dir, mesh_obj, mesh_target)
    save_eit_setup(args.output_dir)
    save_mesh(args.output_dir, mesh_obj)
    save_mesh_sweep(args.output_dir)
    save_voltage_frames(args.output_dir, v0, v1)
    save_reconstruction_comparison(args.output_dir, mesh_obj, mesh_target, reconstructions)
    save_multi_case_results(args.output_dir, mesh_obj, protocol_obj, forward, v0)
    print(
        f"Generated assets with {mesh_obj.n_nodes} nodes, {mesh_obj.n_elems} elements, "
        f"and {protocol_obj.n_meas_tot} voltage differences per frame."
    )


if __name__ == "__main__":
    main()
