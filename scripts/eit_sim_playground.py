"""Sandbox to learn EIT reconstruction WITHOUT hardware.

Branch A only (see cn0565_2_pipeline.svg): builds a mesh, plants a KNOWN
conductivity anomaly, forward-simulates the boundary voltages that anomaly
would produce, then reconstructs an image from those simulated voltages and
compares it to the known ground truth.

Because the anomaly is known, you can tell whether a bad-looking result is
the ALGORITHM/PARAMETERS or your own hardware/data — this script never
touches Branch B (no COM port, no adi.cn0565).

Change the CONFIG block below and re-run. One variable at a time so you know
which change caused which effect.
"""

import matplotlib.pyplot as plt
import numpy as np
import pyeit.eit.bp as bp
import pyeit.eit.greit as greit
import pyeit.eit.jac as jac
import pyeit.eit.protocol as protocol
import pyeit.mesh as mesh
from pyeit.eit.fem import EITForward
from pyeit.eit.interp2d import sim2pts
from pyeit.mesh.wrapper import PyEITAnomaly_Circle

# ---------------------------------------------------------------- CONFIG ---
ALGORITHM = "jac"  # "bp" | "jac" | "greit"
N_EL = 16
H0 = 0.08  # mesh density; smaller = finer/slower, does not change physics
DIST_EXC = 1  # must match force_distance if you later compare to real data
STEP_MEAS = 1  # must match sense_distance if you later compare to real data

# JAC / GREIT regularization (see docs/reconstruction-and-config-guide.md #4)
P_VAL = 0.5
LAMB_VAL = 0.01
JAC_METHOD = "kotre"  # "kotre" | "lm" | "dgn"

# Known anomaly you are planting (the "ground truth")
ANOMALY_CENTER = [0.5, 0.5]
ANOMALY_RADIUS = 0.2
ANOMALY_PERM = 10.0  # conductivity of the anomaly; background is 1.0
# -----------------------------------------------------------------------------

mesh_obj = mesh.create(N_EL, h0=H0)
protocol_obj = protocol.create(N_EL, dist_exc=DIST_EXC, step_meas=STEP_MEAS, parser_meas="std")
fwd = EITForward(mesh_obj, protocol_obj)

# v0: baseline, uniform background (mesh_obj.perm defaults to 1.0 everywhere)
v0 = fwd.solve_eit()

# v1: same mesh, but with the known anomaly planted
anomaly = PyEITAnomaly_Circle(center=ANOMALY_CENTER, r=ANOMALY_RADIUS, perm=ANOMALY_PERM)
mesh_anomaly = mesh.set_perm(mesh_obj, anomaly=anomaly, background=1.0)
v1 = fwd.solve_eit(perm=mesh_anomaly.perm)

if ALGORITHM == "bp":
    eit = bp.BP(mesh_obj, protocol_obj)
    eit.setup(weight="none")
    ds = eit.solve(v1, v0, normalize=True)
    ds_for_plot = ds
elif ALGORITHM == "jac":
    eit = jac.JAC(mesh_obj, protocol_obj)
    eit.setup(p=P_VAL, lamb=LAMB_VAL, method=JAC_METHOD, perm=1, jac_normalized=True)
    ds = eit.solve(v1, v0, normalize=True)
    ds_for_plot = sim2pts(mesh_obj.node, mesh_obj.element, ds)
else:
    eit = greit.GREIT(mesh_obj, protocol_obj)
    eit.setup(p=P_VAL, lamb=LAMB_VAL, perm=1, jac_normalized=True)
    ds = eit.solve(v1, v0, normalize=True)
    _, _, ds_for_plot = eit.mask_value(ds, mask_value=np.nan)

fig, axes = plt.subplots(1, 2, figsize=(10, 5))

axes[0].set_title("Ground truth (anomaly bạn đặt)")
axes[0].tripcolor(
    mesh_anomaly.node[:, 0], mesh_anomaly.node[:, 1], mesh_anomaly.element, mesh_anomaly.perm
)
axes[0].axis("equal")

axes[1].set_title(f"Tái tạo bằng {ALGORITHM.upper()} (p={P_VAL}, lamb={LAMB_VAL})")
if ALGORITHM == "greit":
    axes[1].imshow(np.real(ds_for_plot))
else:
    axes[1].tripcolor(mesh_obj.node[:, 0], mesh_obj.node[:, 1], mesh_obj.element, np.real(ds_for_plot))
axes[1].axis("equal")

fig.tight_layout()
plt.show()
