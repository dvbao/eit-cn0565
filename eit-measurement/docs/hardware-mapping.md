# CN0565 hardware mapping and capabilities

Verified facts about how software talks to the board in this repository, for the hardware adapter
(`backend/app/hardware/`, not built yet) and the configuration model (`backend/app/schemas/models.py`).
Status: **verified** = seen in the driver source, the firmware image, the board netlist or the recorded pilot
sessions; **inferred** = consistent with the evidence but not tested on the board; **open** = unknown.

Paths: `backend/…` and `data/…` are inside `eit-measurement/`; `reference/…`, `work/…` and `scripts/…` are at the
repository root, one level above `eit-measurement/`.

Sources: pyadi-iio driver in `work/upstream-download/extracted/pyadi-iio-main/adi/` (byte-identical to the
driver used in the pilot: SHA-256 of `cn0565.py`, `ad5940.py`, `adg2128.py` match `adi_driver_sources` in the
session `meta.json`), the firmware image in `reference/firmware/`, the board files in
`reference/cn0565-designsupport/`, the circuit note `reference/cn0565 rev. a.pdf`, and the three sessions in
`data/sessions/`.

## 1. Transport (verified)

```
Python (pyadi-iio adi.cn0565) → libiio → URI → firmware (TinyIIOD on EVAL-ADICUP3029) → AD5940 + 2 × ADG2128
```

| Item | Value |
|---|---|
| Serial link | 230400 baud, 8N1, no flow control; boot banner at 115200 |
| Direct URI | `serial:COMx,230400,8n1n` |
| URI used in the pilot | `ip:127.0.0.1:30431` through `scripts/iiod_serial_proxy.py` |
| Why the proxy | the firmware can silently drop a WRITE payload that follows its header; the proxy waits `delay_ms` before each payload (default 100 ms, **10 ms in the pilot**). A dropped payload measures the wrong electrodes without any error |
| IIO devices | `ad5940` (iio:device0), `adg2128` (iio:device1); no `cn0565` device |
| Timeout | pyadi-iio sets none; the pilot recorded `timeout_ms = 5000`. Connection errors are replaced by "No device found" (keep the original libiio error) |

## 2. Settings the firmware exposes (verified)

| Attribute (device `ad5940`) | Meaning | Notes |
|---|---|---|
| `excitation_frequency` | Hz | pilot 10 000 / 50 000 / 80 000 read back exactly; no range check in Python. The ADI GUI slider (10–80) writes Hz, probably a GUI bug |
| `excitation_amplitude` | **firmware command value** (DacVoltPP), unit not verified | pilot 600, read back 600.0. Never label it mVpp at the electrodes |
| `impedance_mode` | True: voltage and current → impedance; False: voltage only | pilot False |
| `magnitude_mode` | True: magnitude only; False: real + imaginary | must be False (otherwise Re/Im are lost silently) |
| `gpio1_toggle` | resets all crosspoint switches (GP1 → pin 31 of both ADG2128) | before every measurement |
| channel `voltage0` (`bia`) `raw` | one measurement | voltage mode: complex of **integer DFT counts**, no physical unit |
| `adg2128` `direct_reg_access` | switch register write | used by the driver to close X/Y switches |

Not available from the firmware: RTIA, DFT length, waveform, an excitation on/off switch. Present them as
unavailable. `electrode_count`, `force_distance`, `sense_distance` and `switch_sequence` exist only in Python.

Circuit note limits (verified): voltage source up to ±607 mV through R_LIMIT = 1 kΩ, 0.015 Hz–200 kHz, AC current
designed ≤ 400 µA RMS, 0.47 µF isolation (no DC). Tested band in this project: 10–80 kHz at command 600.

## 3. One measurement (verified for the stock driver)

Stock `all_voltages`, per measurement: write `gpio1_toggle`, four switch writes (F+→Y0, S+→Y1, S−→Y2, F−→Y3),
read `raw`, read both mode flags (5 writes + 3 reads). Two consequences:

- `all_voltages` **caches** the sequence on its first call: changing `electrode_count` later does not change what
  is measured. The new adapter must use its own per-measurement loop with an explicit sequence (this also gives
  per-measurement timestamps, errors and cancellation between measurements).
- A frame cannot be stopped inside `all_voltages`; with a per-measurement loop, Stop takes effect within ~0.1 s.
  After Stop, reset the switches; whether excitation continues is **open** (check CE0 with a scope).

## 4. Routing used by the pilot (verified from meta.json; driver mapping inferred)

| Item | Value |
|---|---|
| Role rails | F+ → Y0 (CE0 via C1 + 1 kΩ), S+ → Y6 (AIN2), S− → Y7 (AIN3), F− → Y3 (DE0). The stock driver's Y1/Y2 for S+/S− must not be used |
| Driver index | `driver_index = (X + 12) % 24` (the driver registers ADG2128 0x71 first). Inferred from netlist + ADI naming; confirm with one known-load pair (X0–X1 vs X12–X13) |
| Board lines | 24 X lines (X0–X11 on U1, X12–X23 on U2). **Maximum 24 electrodes; 32 is impossible** (the driver's `[8, 16, 32]` list is wrong) |

## 5. Wiring of the facial cable (verified from meta.json, not continuity-tested)

File: `data/hardware/C16-R-user-interleaved-TMJ5-v2-208.json` (copied verbatim from the 2026-10-05 sessions).

- 16 cups on X0–X15 (P1 pins 3–14 and 17–20), interleaved L1, R1, L2, R2, …, L8, R8.
- P1 pins 1, 2, 15, 16, 29, 30 are GND_ISO; X16–X23 (pins 21–28) are not wired.
- Ring order `logical_to_physical = [0, 2, 4, 6, 8, 10, 12, 14, 15, 13, 11, 9, 7, 5, 3, 1]`: L1 → L8 → R8 → R1.
- Wire colours repeat, so colour alone does not identify a lead.
- The mapping note "Pattern 0 … = sites L1, L2, R2, R1" describes an older protocol; pattern 0 of `perimeter208`
  is sites L1, L3, L4, L2.

Electrode counts possible with this cable: 16 (used); any n from 4 to 16 as a subset of these leads with a new
wiring file (inferred, untested); 24 needs 8 more leads; 32 is impossible.

## 6. Timing (verified)

| Quantity | Pilot value (proxy delay 10 ms) |
|---|---|
| One measurement | ~98 ms (medians 97.96 / 98.06 / 98.62 ms at 10 / 50 / 80 kHz), independent of frequency |
| One frame | n_measurements × ~0.099 s: 8 electrodes 40 → ~4 s; 16 → 208 → ~20.6 s; 24 → 504 → ~50 s |
| Frame start to next frame | ~22.8 s = 2 s settle + frame + ~0.1 s overhead |

Time per measurement is dominated by the 5 writes × proxy delay plus UART time: re-measure it (timing benchmark)
whenever the proxy delay, firmware or host changes, and store it in the measurement configuration
(`seconds_per_measurement`).

## 7. Open items before the hardware adapter is written

1. Copy `cn0565_pilot.py` (and its GUI guide) from the Windows PC: it is the only source for the per-measurement
   routing loop, contact QC, timing benchmark and timeout handling actually used in the pilot.
2. Record a `firmware_id` (hex file name + SHA-256) in every session; all pilot sessions say "unknown".
3. Confirm the driver index rule and the Y6/Y7 sense rails on a known load.
4. Continuity-test each lead to its P1 pin, then set the wiring status to verified.
5. Measure the real excitation voltage/current at the electrodes before raising amplitude or frequency.
6. `scripts/cn0565_capture.py` uses the stock routing (Y0–Y3, no +12 remap): do not use it with the facial cable.
