# CN0565 C16-R: pin map, raw acquisition and image gates

**Status: proposed bench workflow, 2026-10-02. Not a human-use approval or a validated facial-EIT reconstruction.**

This document links the [C16-R pilot](facial-bioimpedance-pilot-01.md), the
[P1 wiring proposal](protocols/c16r-p1-wiring-proposal.json), and the
[raw-frame collector](../scripts/cn0565_capture.py). It deliberately keeps
electrode sites, software indices, P1 pins, data rows and reconstruction
protocol as separate concepts.

**Current first objective:** the professor requests resting-reference and
task recordings, then a comparison. Start with the simpler
[rest–task–rest workflow and plots](cn0565-rest-task-first-look.md).
An anatomically validated reconstruction is a later objective, not a
prerequisite for inspecting raw task-associated voltage changes.

## 1. Physical mapping is proposed, not measured

The EVAL-CN0565-ARDZ schematic Rev B, sheet 2, labels P1 pins 3–14 as
X0–X11 and 17–28 as X12–X23. Pins 1, 2, 15, 16, 29 and 30 are GND_ISO, not
extra sensing or body-ground contacts. The 16-cup proposal uses X0–X15:

| Software index | Site | X line | P1 pin | Software index | Site | X line | P1 pin |
|---:|---|---|---:|---:|---|---|---:|
| 0 | L1 | X0 | 3 | 8 | R8 | X8 | 11 |
| 1 | L2 | X1 | 4 | 9 | R7 | X9 | 12 |
| 2 | L3 | X2 | 5 | 10 | R6 | X10 | 13 |
| 3 | L4 | X3 | 6 | 11 | R5 | X11 | 14 |
| 4 | L5 | X4 | 7 | 12 | R4 | X12 | 17 |
| 5 | L6 | X5 | 8 | 13 | R3 | X13 | 18 |
| 6 | L7 | X6 | 9 | 14 | R2 | X14 | 19 |
| 7 | L8 | X7 | 10 | 15 | R1 | X15 | 20 |

The index order follows a candidate outer path. It is **not** a coplanar,
complete EIT ring. Before connecting any person: identify physical pin 1 on
the actual mating connector, continuity-test each lead to its P1 pin, then
use known resistor loads to verify the software index and F/S polarity. Do
not connect a cup to any GND_ISO pin. Record measured lead IDs and mark the
mapping as verified in a versioned copy; do not silently change this draft.

## 2. What one `all_voltages` call actually captures

In the local pyadi-iio CN0565 implementation, `switch_sequence` orders each
row as `(F+, S+, S-, F-)`. At 16 contacts with both distances set to 1 it has
16 drive pairs × 13 sense pairs = 208 **sequential** measurements. The
`all_voltages` property loops across those rows and returns a `(208, 2)`
array of real/imaginary *voltage readings*. The code does not expose the time
of each pattern; a timestamp just before and after the call bounds a frame.
After it returns, the next call starts again at row 0, provided the sequence
and configuration have not changed. A `CUE` printed between calls is a
**software frame-boundary cue**, not proof that the participant's muscle
changed at that exact instant. The first frame after a movement cue must be
treated as transitional until video or another marker verifies a stable pose.

The source caches the sequence on first `all_voltages`. Set electrode count
and distances before the first call; restart the board object after changing
them. The stock adjacent sequence is a circular-index pattern, not an
optimized facial-current protocol. Do not interpret index adjacency as
anatomical adjacency without the map above, and do not treat that map as a
validated 2D boundary geometry.

## 3. Raw logger and timing bench check

The collector is intentionally standard-library-only in mock mode and
imports `adi` only for a live board:

```sh
python3 scripts/cn0565_capture.py --mock --frames 3 \
  --output-prefix /tmp/cn0565-mock-01
```

For a live **bench fixture** after a known-load and safety review, use the
actual URI and explicitly reviewed frequency/amplitude. No human values are
recommended by this document:

```sh
python3 scripts/cn0565_capture.py \
  --uri 'serial:/dev/ttyACM0,230400,8n1n' \
  --frequency-hz FREQ_FROM_BENCH_REVIEW \
  --amplitude-mv AMPLITUDE_FROM_BENCH_REVIEW \
  --frames 20 --output-prefix data/raw/bench-01
```

The literal placeholders must be replaced; the command will reject them as
non-numeric. The collector never overwrites existing files and writes:

- `PREFIX.voltages.csv`: one row per pattern, with frame number, pattern
  number, all four electrode indices/sites/P1 pins, and raw real/imaginary
  voltage-channel values (units not independently calibrated);
- `PREFIX.frames.csv`: start/end monotonic and UTC times for each complete
  frame, plus duration and pattern count;
- `PREFIX.events.csv`: block-boundary cue time and first frame number;
- `PREFIX.meta.json`: mapping, exact sequence, settings, completion status,
  median/p95/max complete-frame durations and explicit measurement limits.

The collector also reports start-to-start median/p95/max intervals when at
least two frames are available. These include file/cue overhead; use them
alongside acquisition duration when estimating how many frames fit a hold.

Use p95 frame duration **measured on the same board, connection, settings and
pattern set** to choose task duration. A 5-second hold is not justified merely
because there are 16 electrodes. Plan enough time for movement onset plus
several *complete* stable-state frames. If frame time is too long, reduce or
optimize the pattern set and **version the acquisition and inverse protocols
together**; fewer patterns may reduce spatial information. The current
collector refuses a non-208 sequence rather than silently recording data it
cannot describe with this protocol version.

For automatic terminal cues at frame boundaries, a schedule JSON can contain
`{"blocks": [{"label": "rest", "frames": 6}, {"label": "task", "frames": 10},
{"label": "post_rest", "frames": 6}]}` and be passed as `--schedule FILE`.
These are example frame counts, **not** a human protocol. The cue is printed
only after the previous frame returns; record actual task onset with video or
another synchronised marker, and exclude transition frames. A separate
per-pattern-timestamp collector would require instrumenting the 208-step loop
instead of using the opaque `all_voltages` call.

## 4. Forearm is not a facial phantom

Forearm measurement is also human-use; it does not bypass the need to verify
electrical safety of the full assembled system. It can check whether a mounted electrode array produces
repeatable task-associated signals and whether motion/contact overwhelms
them. It does **not** establish where an unseen conductivity target was, does
not validate facial anatomy, and does not establish face-image localisation.
For known-location image validation, first use a resistor network and then a
simple conductive tank/gel phantom with a movable known inclusion. A circular
phantom may validate the stock 2D circular demo; a face-like/partial-boundary
geometry is needed to validate a facial claim.

## 5. When can BP, JAC and GREIT be called facial images?

The local CN0565 examples use `mesh.create(16, h0=0.08)` (default 2D disk),
`protocol.create(...adjacent...)`, and in static examples `v0=ones`. They
show how the software is connected, **not** a validated face model.

The raw data path is:

`site/P1 map -> exact switch sequence -> complete frames + events -> stable
rest and task frames -> v0[m], v1[m] -> model-matched inverse -> image`.

For one trial, compute `v0[m]` from pre-task rest frames and `v1[m]` from
frames entirely inside a stable hold, with the same pattern `m` and same
mount/settings. Check post-task rest for drift. Keep real/imaginary raw data;
do not call these calibrated impedances without a current/calibration check.
The [difference preparation script](../scripts/cn0565_prepare_difference.py)
does this alignment after the analyst selects valid complete frame IDs:

```sh
python3 scripts/cn0565_prepare_difference.py \
  --input-prefix data/raw/bench-01 \
  --rest-frames 1,2,3 --task-frames 7,8,9 \
  --output data/processed/bench-01-trial-01.json
```

This emits the 208-row `v0`, `v1` and `delta` vectors, preserving both real
and imaginary values and checking every pattern ID/order. The selected IDs
above are illustrative only. Check cue/video records, reject transition
frames, and never select rest and task from different mounts or layouts.

To compare the three **on a circular phantom**, the stock 2D mesh/protocol
can be an initial controlled demonstration after sequence and voltage-sign
checks. To compare them as **facial EIT**, one needs a forward model with
the actual 3D head/face geometry, finite cup positions/contact behaviour,
and the exact current/measurement protocol, plus known-target validation.
JAC-type sensitivity reconstruction may be adapted to that model; the
current BP and GREIT scripts, especially GREIT's 2D output grid, cannot be
claimed to reconstruct facial 3D anatomy unchanged. A pretty heatmap is not
proof of spatial correctness. A 2D facial projection, if attempted earlier,
must be labeled exploratory and tested for model-error artifacts.

The local pyEIT protocol stores voltage pair order as `[n, m]` while the
board sequence records `(S+, S-)`. **Do not assume the polarity matches.**
Known-load polarity and channel-order tests must resolve this before inverse
reconstruction; the collector stores raw values without flipping signs.

## 6. Gate before human acquisition

The user clarified that no lab is available for the present self-test.
Electrical safety of the *full* assembled system remains unverified:
isolation, fault/leakage/DC and per-path current, cabling, electrode
contact, power, and simultaneous video/EMG equipment. The software workflow
does not resolve these hardware checks or authorize human current injection.
The CN0565 circuit's isolated design is not by itself an approval of this
custom human experiment. Keep hardware settings fixed within a trial and
record firmware/software versions and all deviations.
