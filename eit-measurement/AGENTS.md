# EIT Measurement Studio — Project-Wide Engineering Guidelines

> **Purpose:** Single source of truth for AI coding agents and developers building and maintaining the EIT Measurement Studio application.
>
> **Audience:** Codex, Claude Code, Cursor, and human maintainers.
>
> **Priority:** Existing verified hardware behavior, electrical safety, measurement-data integrity, and user requirements take precedence over examples in this document.
>
> **Location:** this file is `eit-measurement/AGENTS.md`. The folder `eit-measurement/` is the application root (desktop interface, backend, hardware communication, analysis, data). It sits inside the research repository `eit-cn0565/`, which also holds research notes (`docs/`), references (`reference/`), slides and the Windows hardware toolkit (`scripts/`, `examples/`, `bootstrap-cn0565-env.ps1`). All paths in this document are relative to `eit-measurement/` unless they say "repository root". Short paths `features/…` and `widgets/…` are under `frontend/`; short paths `schemas/…`, `services/…`, `hardware/…`, `eit/…`, `core/…` are under `backend/app/`.

## 0. Operating Instructions for Coding Agents

**Read this entire document before planning or modifying the application.** Treat it as the project's durable engineering specification and design guideline. Implement real, maintainable functionality rather than a static mockup. Work within the existing repository; don't rebuild working modules; extend the layout in §8.1 (✓ exists, ○ planned).

On each task:

1. Inspect the relevant existing source files, tests, and device/driver APIs before modifying anything.
2. Identify the *owning feature/module*, affected backend contracts, and hardware constraints.
3. State a concise plan for changes that affect several parts of the system. For small changes, implement directly.
4. Make the smallest coherent change that fulfills the requirement, keeping behavior and types aligned across layers.
5. Run targeted tests, lint/type-check/build where available; report exactly what was verified and what requires real hardware.
6. Summarize changed files, behavior, known limitations, and any unverified hardware assumptions.

**Never:** invent hardware calls or fake a successful measurement; conflate demo data with device data; claim an untested electrical configuration is safe; modify unrelated features; add needless dependencies, abstractions, pages, animations, or components; or stop after providing a plan when implementation is requested.

### Current state of this project (read before planning)

- **Built and tested:** `backend/app/eit/` (the analysis package, formerly `eitpilot`: measurement sequence, session reader, QC, relative change, features, BP/JAC/GREIT reconstruction, report), `backend/app/schemas/models.py` (measurement configuration, wiring, study design), `backend/app/services/protocol_runner.py` (study design → session schedule and its validation), the command line `python -m app {design,check,study,hash}`, and 41 backend tests including a regression test against the published pilot analysis.
- **Desktop interface (`frontend/`, PySide6):** window shell built (header with device status and clock, exactly three tabs, read-only configuration column, honest empty states; `python -m frontend`), with 5 offscreen tests.
- **Not built yet:** `backend/app/hardware/`, the device and session services, the live part of the protocol runner, `services/acquisition.py`, `services/session_manager.py`, the editing panels, the guidance/announcement widgets, Results/Sessions content, `packaging/`.
- **Progress, pipeline and the build plan:** `docs/architecture.md` (update its progress table and change log after every step). Verified hardware facts: `docs/hardware-mapping.md`. Data-collection procedure with the current Windows pilot software: `docs/pipeline.md`.
- The user builds this step by step and must be able to follow every change: one step at a time, state which files changed and why, keep the folder map in `README.md` accurate.

---

## 1. Product Vision and Scope

Build **EIT Measurement Studio**, a **desktop application** (Python + PySide6) for running and reviewing **Electrical Impedance Tomography (EIT)** laboratory experiments. It starts as a Python app run from source and is later **packaged as one installer** that other researchers can install and use (§8.12).

An operator should immediately know:

- Is the instrument connected and ready?
- What excitation and routing parameters are configured?
- Is a measurement actively running, paused, stopping, completed, or in error?
- What must the operator do **now**, in clearly visible, step-by-step instructions? Is this a GET READY, HOLD, REST, or TRANSITION phase? What comes next?
- How long has the overall session and current task been active, and how long remains?
- What measurements were acquired, and which task interval produced each sample?
- Where can previous results and sessions be found?

### Primary workflow

`Connect device → Configure parameters → Select/edit guided protocol → Validate → Start measurement → Prepare → Ready countdown → Perform/HOLD countdown → Rest/transition countdown → Next task → Complete → Inspect results → Export/reopen session`

### Primary navigation — exactly three tabs

1. **Measurement:** connect/configure, control acquisition, and guide current experiment.
2. **Results:** inspect actual measurements, plots, EIT reconstructions (when available), and export.
3. **Sessions:** browse, select, and reopen saved experimental sessions.

Do **not** create Dashboard, Analytics, Reports, Settings, Administration, or other top-level pages without an explicit new requirement. Secondary controls should live in compact panels within these three tabs.

### Non-goals unless explicitly required

- Clinical diagnostic claims or regulated medical workflows.
- Social features, accounts/multi-tenancy, or complex role management.
- Marketing pages and decorative analytics dashboards.
- A drag-and-drop protocol canvas or generic workflow engine.
- New hardware drivers, acquisition modes, reconstruction algorithms, or transport features not justified by the verified device stack.

---

## 2. Real Hardware and Integration Constraints

### Target hardware

- **CN0565:** Analog Devices EIT reference/evaluation platform.
- **AD5940:** analog front end used for excitation and impedance/voltage acquisition.
- **ADG2128:** crosspoint switch devices for routing electrode connections; CN0565 reference designs may use two ADG2128 devices.
- **Controller/firmware:** inspect the actual board and firmware revision (e.g., EVAL-ADICUP3029 where applicable).
- **Python hardware libraries:** inspect the installed `pyadi-iio` and `libiio` APIs as well as firmware support; do not assume a name seen in documentation is available in this installation.

### Electrical meaning of the parameters

| Quantity | UI role | Units / cautions |
|---|---|---|
| Excitation amplitude | Editable if supported by the driver | Explicit `mVpp`, `Vpp`, RMS, or driver-native units — **never assume equivalence** |
| Excitation frequency | Editable if supported | Hz / kHz, convert carefully |
| Configured bias or other voltage | Editable **only** if an actual driver capability exists | Use its precise electrical meaning |
| Measured voltage | Read-only acquisition result | `mV`, `V`, magnitude/phase as appropriate |
| Measured current | Read-only only when measurable/derivable with validated calibration | `µA`/`mA` with provenance |
| Impedance | Read-only measurement/derived result | `Ω`, magnitude, real/imaginary components, phase if available |
| Electrode count/pattern | Editable within verified wiring/driver capabilities | Device-specific validation |
| F+/F− and S+/S− | Electrode routing configuration | Validate distinctness/overlap rules *for the chosen measurement mode* |

**Do not assume "amplitude" and "voltage" are independent writeable controls.** Determine whether amplitude is an excitation voltage, whether a separate bias/setpoint is exposed, and how measured voltages are returned. Expose only controls supported by verified firmware/driver capabilities.

**Electrode limits and mapping:** the CN0565 reference hardware is commonly described as supporting up to 24 electrodes, but actual wiring, active electrode set, selected pattern, driver index limits, and firmware may differ. Never hardcode the reference-board maximum as proof that all 24 are usable. Read device capabilities and document wiring assumptions. Preserve the real crosspoint topology; do not invent a direct one-to-one ADG2128-to-electrode mapping.

### Required integration architecture

```text
Desktop interface  frontend/  (PySide6 widgets, one process with the backend)
       │  direct Python calls: commands, configuration, history
       ▲  Qt signals: device state, stage changes, measurement progress, errors
       ▼
Backend  backend/app/
       ├── services/  session + protocol orchestration, acquisition + timestamps (worker thread)
       ├── eit/       scientific processing / reconstruction
       │
       ▼
Hardware adapter interface  backend/app/hardware/
       ├── Real CN0565 implementation
       │     └── pyadi-iio / libiio → serial proxy (inside the app) → firmware → AD5940 + ADG2128
       └── Explicit mock adapter (DEMO MODE ONLY)
```

The real transport might be serial/USB CDC/IIOD or another libiio backend. **Discover it from the connected device and deployed firmware. Do not assume a particular transport protocol or serial command format.** Driver APIs stay in `backend/app/hardware/`; the interface (`frontend/`) never imports `adi` or `iio` and never touches the serial port.

### Hardware capability discovery

Before implementing controls or acquisition, inspect or verify:

- Device discovery and connection method/URI.
- AD5940 excitation setpoints, units, supported ranges, readback, measurement format and timing.
- ADG2128 electrode routing API, actual device addresses, switch matrix mapping, valid indexes and conflicting paths.
- Whether the installed `adi.cn0565` wrapper exposes `excitation_frequency`, `electrode_count`, `force_distance`, `sense_distance`, `switch_sequence`, `all_voltages`, etc. **Treat these as candidates to inspect, not guaranteed API contracts.**
- Measurement semantics: per-point reads, sequences, batches, buffering, or true streaming; rate limits and settling requirements.
- Device cancellation, safe shutdown, disconnect handling, read timeouts, and firmware error reporting.
- Calibration requirements and whether reported voltages are raw ADC values, calibrated physical values, or complex phasors.

Present unsupported features as **unavailable**, not as controls that silently do nothing.

### Verified facts for this project's board (details and evidence: `docs/hardware-mapping.md`)

- **Transport:** `pyadi-iio` (`adi.cn0565`, version recorded per session) → libiio → serial `230400 8N1`. The firmware can silently drop a WRITE payload, so the pilot used the local proxy `scripts/iiod_serial_proxy.py` (repository root; URI `ip:127.0.0.1:30431`, 10 ms delay before each payload). A dropped payload measures the wrong electrodes without any error.
- **Writable settings (device `ad5940`):** `excitation_frequency` (Hz), `excitation_amplitude` (firmware command value, physical unit **not verified**: never label it mVpp at the electrodes), `impedance_mode`, `magnitude_mode` (must stay False), `gpio1_toggle` (resets all switches). Not available: RTIA, DFT length, waveform, excitation on/off. Python-only: `electrode_count`, `force_distance`, `sense_distance`, `switch_sequence`.
- **Measured value:** voltage mode returns a complex number of integer DFT counts (`real_raw`, `imag_raw`); label it "counts", never V, Ω or µA.
- **Electrodes:** 24 X lines on the board (two ADG2128); the driver property `electrode_count_available` returns [8, 16, 32], which is wrong for 32. The facial cable wires 16 cups (`data/hardware/C16-R-user-interleaved-TMJ5-v2-208.json`); fewer electrodes: a subset with a new wiring file (inferred, untested). Pilot routing as recorded in meta.json: F+ → Y0, S+ → Y6, S− → Y7, F− → Y3, `driver_index = (X + 12) % 24` (index rule and Y6/Y7 rails inferred from the netlist; confirm on a known load, `docs/hardware-mapping.md` §7). Never use the stock driver's Y1/Y2 sense rails.
- **Do not use `all_voltages` for sessions:** it caches the measurement list on its first call (changing the electrode count later is ignored) and cannot be stopped mid-frame. Use an explicit per-measurement loop that timestamps every measurement and can stop between measurements.
- **Timing:** ~0.099 s per measurement with the 10 ms proxy delay, independent of frequency; re-measure after any transport change and store it as `seconds_per_measurement`.
- The pilot acquisition program `cn0565_pilot.py` (contact QC, timing benchmark, per-measurement routing) is still on the Windows PC; obtain it before writing `hardware/cn0565.py`.

### EIT acquisition semantics (binding for every layer)

1. **A frame is sequential.** One frame = the measurement sequence of the configured ring (`n × (n − 3)` measurements for adjacent drive and sense: 8 → 40, 16 → 208), taken one after another, `frame_s = n_measurements × seconds_per_measurement` (16 electrodes ≈ 20.6 s). It is not a snapshot.
2. **HOLD is derived, not free.** The measured frames must lie entirely inside HOLD: `HOLD ≥ settle + frames × frame_s + margin`. The configuration panel shows `n_measurements` and `frame_s` read-only; the protocol editor computes the minimum HOLD and rejects designs that do not fit or exceed the comfort cap (30 s in the pilot). Every HOLD duration in the generic examples below (20 s, 30 s) is illustrative; in this project HOLD = max(task `hold_s`, settle + frames × frame_s + margin) ≤ `hold_cap_s` (16 electrodes: ≥ 23.1 s; 8 electrodes: ≥ 6.5 s).
3. **REST is a measured block** (the baseline every task is compared with). The unmeasured stage after HOLD is called **RELEASE** in this project. In the generic sections below, every *stage* named Rest, REST, Rest/Transition, `rest_transition`, `resting/transitioning` or `"type": "rest"` means RELEASE; it never means the measured REST block. Never merge the two.
4. **Every measurement keeps its own timestamps** (start/end), its routing (F+, F−, S+, S−) and its task/stage; analysis depends on them.
5. **Pause and Stop act between measurements**, never inside one; Stop resets the switches (`gpio1_toggle`), marks the frame incomplete and keeps the data. Whether excitation stops is not verified.
6. **Configuration is frozen during a session** and saved with it (measurement configuration, wiring, expanded schedule, driver/firmware identity).

### Safety boundary

If electrodes are used on human participants, require an appropriately reviewed experimental setup and validated current/voltage/frequency limits and isolation/protection independent of UI code. The frontend may enforce additional guardrails but cannot be the sole safety mechanism. Stop controls initiate a safe backend/firmware shutdown; do not claim hardware excitation is off until confirmed using the available mechanisms. Do not represent this software as a clinical device.

---

## 3. Approved Stack and Engineering Approach

**Decision (2026-10-09):** one Python desktop application now; a distributable installer later. No browser, no web server, no HTTP API: the interface calls backend functions directly and receives events as Qt signals. A web version can be added later on top of the same services without changing them.

### Interface (`frontend/`)

- **Python + PySide6** (Qt for Python, LGPL — allowed in a distributed closed-source installer; do not switch to PyQt, which is GPL).
- Plain Qt widgets and layouts; styling only through `frontend/theme.py` (design tokens → one Qt stylesheet).
- Plots: Matplotlib (already used by the analysis) embedded with its Qt backend, or `pyqtgraph` only if live plotting needs it.
- **Inter** or **Geist** typeface when installed, otherwise the system sans-serif font.

### Backend (`backend/app/`)

- Python (3.11 on the Windows acquisition PC; 3.9+ supported for development on macOS).
- Existing modules: `eit/` (analysis), `schemas/` (contracts), `services/` (protocol runner, configuration), `core/` (data folder).
- Verified `pyadi-iio` / `libiio` integration in `hardware/` (to be built).
- Long operations (connecting, a frame of measurements, a whole session) run in a **worker thread** (`QThread` or a Python thread bridged with Qt signals) so the window never freezes.

### Mapping of the generic web terms in this document

Sections 4–13 were written for a React + FastAPI stack. In this project read them as follows:

| Web term in this document | In this project |
|---|---|
| React component / `X.tsx`, hook `useX.ts` | PySide6 widget class in the Python module listed in §8.3 |
| `theme.css`, `globals.css`, Tailwind/shadcn tokens | `frontend/theme.py` (`TOKENS`, `stylesheet()`, `tabular()`) |
| REST endpoint (`GET/POST /api/...`) | direct call of a backend service function (§7) |
| WebSocket event | Qt signal emitted by a backend worker, received in the interface thread (§7) |
| "backend unavailable" | backend call failed or worker stopped: show Disconnected / error states, never fake success |
| `prefers-reduced-motion` | an app setting "Reduce motion" (default off) that replaces the pop-up animation by a direct change |
| `aria-live`, focus, keyboard | Qt accessibility (`setAccessibleName`, `QAccessible` announcements once per stage change), keyboard focus order, shortcuts |
| browser refresh / reconnect / tab throttling | reopening the window or restarting the app: recover state from the backend, never restart a countdown |
| `npm run build`, type-check | `python -m unittest` (offscreen Qt), and the packaging smoke test (§8.12) |

### Decisions

- Reuse the repository's existing library versions and conventions; avoid duplicate libraries for the same job.
- The interface must remain usable without a device: show **Disconnected**/empty states rather than fabricating successful acquisition.
- Keep all logic out of `frontend/`: if a widget needs a computed value, add a backend function and call it.

---

## 4. Information Architecture and UI Layout

### Overall visual style

**Minimal Scientific Instrument Interface**: content-first, compact, readable, restrained. Inspiration: Linear-like information density, Vercel-like subtle borders, Notion-like white space, and a real scientific acquisition tool's clear status feedback.

Main header contains:

- App title **EIT Measurement Studio**.
- Device connection indicator/status (always visible).
- Active session ID/name (when applicable).
- Current wall-clock time `HH:mm:ss` (local timezone; timestamped events should retain timezone/UTC info).
- Only minimal additional actions.

### Measurement tab layout — GUIDED TASK FIRST (HIGH PRIORITY)

The **Measurement** page is an operator guidance screen, not merely a compact control dashboard. The active task must visually dominate the main viewport. Build a **large, legible, instruction-first Guided Task Panel** occupying approximately **65–75% of the available content area** (beside the narrow configuration column) and the majority of the main panel's vertical emphasis.

Desktop layout (1366–1440 px, illustrative only):

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ EIT Measurement Studio      Session EIT-###      ● Connected       14:23:15 │
├──────────────────────────────────────────────────────────────────────────────┤
│ Measurement                Results                 Sessions                  │
├───────────────────────┬──────────────────────────────────────────────────────┤
│ CONFIGURATION         │               GUIDED EXPERIMENT                      │
│ 260–300 px            │   TASK 2 OF 5  •  STAGE: HOLD                        │
│                       │                                                      │
│ Device / Connect      │              KEEP YOUR ARM STILL                     │
│ Amplitude             │   Hold your position without moving.                │
│ Frequency             │                                                      │
│ Electrode pattern     │                       HOLD                           │
│ Protocol selection    │                      00:20                           │
│                       │            ███████░░░  progress                      │
│ Advanced ▼            │                                                      │
│                       │  Up next: Relax and wait for the next task          │
│                       │  Session 02:45 · Task 00:10 · Phase 00:10           │
│                       │  [Pause / Resume]                     [Stop]         │
├───────────────────────┴──────────────────────────────────────────────────────┤
│ TASK SEQUENCE:  Baseline ✓   Hold ●   Relax ○   Repeat ○   Complete ○        │
├──────────────────────────────────────────────────────────────────────────────┤
│ Minimal acquisition status • latest confirmed measurement • safety/error    │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Important:** The sample text, times, actions and task names shown above are illustrative. The actual task, wording and hold duration must come from the configured protocol.

**UX priority order:** Current stage/action → very large remaining countdown → clear step-by-step instruction → next stage preview → Stop/control buttons → timeline → configuration details → diagnostics.

- The task title/instruction must not be buried inside a small card, an accordion, or a side panel.
- Keep the active instruction, big countdown, current stage, and Stop visible **without scrolling** at common desktop resolutions.
- On tablet/mobile, stack configuration below or collapse it so that task guidance is first; keep Stop accessible.
- Offer an optional **Focus Mode** (expand main guidance within Measurement; **not** a fourth tab), hiding non-essential configuration and diagnostics while retaining device status, current action, countdown, Pause/Stop and next step.
- Do not produce layout jumps when stage instructions change. Reserve space for 2–3 lines of instructions and a stable-size timer.

### Configuration panel requirements

- Connect/Disconnect, device selector/URI and explicit connection errors.
- Excitation amplitude with actual verified unit/limits.
- Excitation frequency with selectable Hz/kHz presentation as appropriate.
- Separate voltage/bias setting **only if actually writeable**; measured voltage is read-only.
- Active electrode count and injection/measurement pattern.
- F+/F−/S+/S− routing summary; optional collapsible advanced mapping.
- Measurement mode, if supported.
- Protocol selector and a compact editor.
- Validate before applying settings and starting measurements.
- Lock or explain unavailable configuration actions while a session is active.

### Measurement controls

- **Start Measurement:** prominent only in valid Ready/Idle state. Requires connected device, valid configuration, valid protocol, backend readiness, and start acknowledgment.
- **Pause:** offered only if meaningful and supported. Separate *protocol pause* from *physical acquisition pause*. Never fake device pausing.
- **Resume:** only when paused under defined semantics.
- **Stop:** always discoverable during an active acquisition; quickly dispatches request, blocks further task transitions, asks backend for safe termination and preserves data. Avoid a blocking confirmation modal that delays stopping.

Button appearance and enabled/disabled states must match backend-confirmed state. One dominant primary action at a time.

### Protocol/task editor

Support editable, ordered experimental tasks. Each task may contain **multiple timed guidance stages**, not just one title and one duration.

**In this project** the editor edits a **study design** (`data/protocols/*.json`, model `StudyDesign` in `backend/app/schemas/models.py`): the task list with instructions, REST and REST_CONTROL blocks, number of rounds, randomisation seed, initial REST frames, frames per task and the stage timing (GET READY, settle, HOLD margin, RELEASE, HOLD cap). `services/protocol_runner.expand()` turns it into the ordered session schedule (REST → TASK → REST …, one block per row, with its stages); that expanded schedule is what the runner executes and what is saved with the session. Per-stage announcement settings below are added to this model when the editor is built.

For each task, support as appropriate:

- Task name, concise purpose and clear instruction(s).
- **Prepare** instruction (optional): tell the operator what action/equipment/position to prepare.
- **Ready** instruction + countdown (e.g., `Get ready — 5 seconds`).
- **Perform / HOLD** action instruction + configured hold duration (e.g., `Hold your position — 20 seconds`).
- **Rest / Transition** instruction + configured rest/wait duration (e.g., `Relax — next task starts in 5 seconds`).
- Auto-advance or manual operator confirmation, chosen in the protocol and validated by the backend.
- Add/edit/remove/reorder tasks, save/load protocols and validate durations/instructions.
- **Edit the one-shot pop-up announcement for each stage**, including announcement text, visibility duration in seconds, and whether the announcement overlays the active stage or serves as a pre-stage reading/lead-in period.
- Show an in-editor preview of each stage's pop-up, persistent instruction, and stage timer; display the expected total task runtime before saving.

**Three different settings must never be confused:**

1. `stage.durationSeconds`: actual time allocated to GET READY, HOLD/PERFORM, REST, etc. (the real HOLD lasts the full configured duration).
2. `announcement.displaySeconds`: how long the large instruction pop-up stays visible; it is a **presentation duration**, not automatically added to the active stage.
3. `announcement.leadInSeconds`: optional time **before** an active stage starts, used when the operator needs additional reading/positioning time. This is part of the protocol's timed event sequence and must be stored by the backend.

The editor should expose two understandable timing modes: **Overlay during stage** (`displaySeconds` does not extend stage duration) and **Read before stage** (`leadInSeconds` precedes actual stage activation; `displaySeconds` must fit within that lead-in). For manual PREPARE, a pop-up can dismiss without automatically releasing the `I'm ready` gate.

Allow phase duration `0` only when that stage is intentionally disabled; never silently use an invalid zero-length HOLD stage. Display duration values and units in the editor (seconds). Planned task runtime includes active stage durations **plus explicitly configured pre-stage lead-ins**, not pop-up display time counted twice; manual waits remain indeterminate until completed. Do not silently equate `holdSeconds` with the entire task duration.

**Illustrative editable demo protocol (not a validated clinical or human-subject protocol):**

| Task | Ready | Action/HOLD | Wait/rest | Operator guidance |
|---|---:|---:|---:|---|
| Baseline | 5 s | 30 s | 5 s | Prepare → remain still → relax |
| First action | 5 s | 20 s | 5 s | Get ready → hold the assigned position → release |
| Second action | 5 s | 20 s | 5 s | Get ready → perform/hold assigned action → wait |
| Recovery | 5 s | 30 s | 0 s | Prepare → remain at rest → complete |

All values and wording above are placeholders for Demo Mode only. Protocol authors must define the actual tasks and timings appropriate to the experiment.

**Task statuses:** pending, active, paused, completed (and skipped only if explicitly supported). **Stage statuses:** preparing, ready, holding/performing, resting/transitioning, awaiting confirmation, completed. The backend owns the exact stage/task transition sequence and event timestamps.

### LARGE Guided Task Panel — mandatory primary interaction

Implement a visually dominant **step-by-step measurement coach** on the Measurement tab. It should help a participant or operator execute an experimental protocol *without having to interpret small status labels*.

**The center of the screen must answer five questions at a glance:**

1. **WHAT NOW?** e.g., `GET READY`, `RAISE YOUR ARM`, `HOLD`, `RELAX`, `WAIT`.
2. **HOW?** A large, plain-language instruction, e.g., `Keep your arm still until the timer reaches zero.`
3. **HOW LONG?** A very large stage countdown (`00:20`), optionally a progress ring/bar (not both unless justified).
4. **WHAT NEXT?** e.g., `Next: Release your arm and wait 5 seconds`.
5. **WHICH TASK?** `Task 2 of 5`, plus a compact task timeline.

#### Required guidance sequence

The protocol should support this configurable sequence **for each task**:

```text
PREPARE (instruction shown; optional manual Ready button)
       ↓
GET READY (countdown 00:05, say what action is coming)
       ↓
PERFORM / HOLD (large countdown 00:20, active instruction)
       ↓
RELEASE / WAIT (countdown 00:05; tell the participant to stop the action)
       ↓
NEXT TASK (automatic after backend confirmation, or manual if configured)
       ↓
... until PROTOCOL COMPLETE
```

**Stage-specific UI copy examples** (not hardcoded):

| Stage | Main title | Supporting instruction | Big timer |
|---|---|---|---|
| Prepare | `PREPARE FOR THE NEXT TASK` | `Position yourself as instructed. Press I'm ready when prepared.` | `—` or optional time |
| Ready | `GET READY` | `In 5 seconds, raise your arm.` | `00:05` |
| Hold | `HOLD YOUR POSITION` | `Keep your arm raised and still.` | `00:20` |
| Rest | `RELAX AND WAIT` | `Lower your arm. The next task begins shortly.` | `00:05` |
| Await confirmation | `READY TO CONTINUE` | `Check your position, then select Next task.` | `—` (never a false countdown) |
| Complete | `MEASUREMENT COMPLETE` | `The protocol has finished. Review your results.` | No active countdown |

The text `HOLD` is only appropriate when the task instructs the operator to maintain a pose/condition; general actions may instead use `PERFORM` or task-specific wording. Never force every task to have a HOLD stage.

#### Mandatory LIVE step announcement animation and editable reading time (highest-priority guidance behavior)

**For every new task/stage, show a prominent temporary pop-up that tells the participant precisely what to do NOW.** The intent is to guide a participant *while they are performing the experiment*, not merely to provide a static dashboard. This is a **functional, high-salience transition announcement**, explicitly allowed despite the general prohibition on unnecessary animation.

**The required experience for each configurable task:**

```text
Backend signals current stage changed
      ↓
Large announcement POPS into the center of the guidance area
      ↓
Stage-specific action appears in huge legible text (1–2 lines)
      ↓
Short explanatory instruction and planned duration appear below
      ↓
After the protocol-configured announcement display time (e.g. 3–5 s
for reading, shorter for immediate action cues), it fades automatically
      ↓
Persistent main guidance remains visible, showing the SAME instruction,
large live countdown, stage progress and next step
      ↓
In the final ~3 seconds, quietly preview the upcoming action
      ↓
Next backend-confirmed stage → fresh action pop-up → repeat
```

**Required phase announcements (text comes from the protocol, examples below):**

| State | Entry announcement (large) | Supporting command | After pop-up disappears |
|---|---|---|---|
| `PREPARE` | `NEW TASK — PREPARE` | `Move into the starting position.` | Show persistent preparation instruction and `I'm ready`. No artificial timer for manual gate |
| `GET READY` | `GET READY` | `Raise your arm when the countdown ends.` | Show big countdown, e.g. `00:05`, plus next: `HOLD for 20 s` |
| `HOLD` | `HOLD NOW` or task-specific `PERFORM NOW` | `Keep your arm still until the time ends.` | Show main action + big countdown, e.g. `00:20` |
| `RELEASE` | `RELEASE & RELAX` | `Lower your arm. Wait for the next task.` | Show remaining rest time, e.g. `00:05`, plus next task name |
| Protocol end | `ALL TASKS COMPLETE` | `Measurement guidance is finished.` | Show a persistent completion panel; do not auto-start a new protocol |

- The **pop-up should cover most or all of the instruction/timer content area** in a solid, high-contrast surface for a short time (not a tiny toast in a corner). It must not cover Stop or critical device/error messages.
- Pop-up **display time is configurable in Edit Protocol** per stage, not hardcoded at 1.5 seconds. Defaults are examples only: PREPARE 5 s, GET READY 3 s, immediate HOLD NOW 1–1.5 s, REST 2–3 s. Validate a sensible range against the selected stage/lead-in mode. Long instructions may need more reading time.
- Animate entry with a restrained opacity/scale transition (**150–250 ms**), keep text stable and readable for the configured period, then fade out (**200–350 ms**). Do not bounce repeatedly, strobe, or flash. The small entrance/exit animation must not change the protocol's official timestamps.
- **Timing mode matters:** In `overlay`, the stage starts when the backend confirms it and its stage countdown runs while the announcement is displayed; the pop-up must never steal additional HOLD time. In `before_stage`, the protocol runner emits a separate timed lead-in event, displays anticipatory text such as `HOLD BEGINS IN 3 S` (not `HOLD NOW`), and starts the full HOLD countdown only **after** the backend confirms the lead-in completed.
- For tasks requiring 3–5 seconds to read or prepare before HOLD, prefer `before_stage` or allocate sufficient GET READY time. Reserve `HOLD NOW` for the actual active stage onset. Do not use one ambiguous timer to represent both reading time and active action time.
- Distinguish stages with accessible high-contrast visual styles (e.g. warm/amber for GET READY, green/teal for HOLD, blue for REST) but always include a **plain-text action command**. Colors alone must never carry meaning.
- **The pop-up is not the only instruction.** After it disappears, the main task title, full instruction, and live remaining countdown must stay continuously visible until the next stage.
- For `overlay` announcements, the countdown starts from the authoritative backend stage timestamp; **never delay it only because an animation is playing**. For `before_stage` announcements, a separate backend-confirmed lead-in interval completes *before* the action-stage countdown begins. A short stage must still transition correctly if an overlay is truncated.
- Only announce a **newly confirmed state/event ID**. Do not replay the pop-up on each event update or widget repaint. Do not replay it merely because the page refreshed or a client reconnected to an already active stage; show the recovered live state unless a genuinely new stage transition arrives.
- When task/stage advances while an earlier pop-up is still visible, **cancel the previous announcement** so stale instructions never remain over a newer action.
- PREPARE is a manual gate when configured. Acknowledge `I'm ready` via backend before starting GET READY; do not automatically begin just because the PREPARE pop-up faded.
- For time-bound phases, preview the upcoming action in the **last 3 seconds** using small stable text such as `Next: RELEASE & RELAX in 3s`. Never conceal the active countdown during this cue.
- Pause must freeze protocol-relative countdowns when defined by the backend; on Resume show the correct remaining time without restarting the current stage pop-up as though a new stage began.
- Respect `prefers-reduced-motion`: replace scale animation with a short stable announcement (or a direct state change according to user preference), while retaining the clear visible text. No automatic sounds. Optional beeps/voice cues require explicit opt-in and accessible volume/mute controls.
- Keep the overlay **non-interactive** and position it inside the guidance panel (not over measurement control buttons). Avoid layout shifts while it appears or exits; ensure the underlying timer keeps updating.
- Expose stage changes through an appropriate `aria-live` announcement **once per transition**, not on every timer tick; avoid focus theft.
- If hardware/backend disconnects or returns an error, interrupt non-essential pop-ups and show the error/recovery instructions immediately.

**Do not implement the stage announcement as a decorative toast.** This is a primary operator-facing cue, intended to be readable at a distance while participants are moving or holding position.

#### Large-format design specification

- Guidance area: primary focal panel; **minimum 65% of usable main horizontal content area** on desktop when screen width allows, and effectively full width in Focus Mode.
- **Current stage label:** `16–20px`, semibold, uppercase only for short commands.
- **Current instruction/title:** `28–36px` (up to `40px` in Focus Mode), semibold; strong contrast and 2–3-line capacity.
- **Stage countdown:** **`64–96px`** with tabular numerals (`font-variant-numeric: tabular-nums`); `96–120px` in Focus Mode when viewport allows.
- **Support text / next step:** `16–18px` for readability at a practical working distance.
- Keep ample whitespace *within* the guidance panel; avoid nested cards, dense text blocks and decorative UI.
- Use concise plain-language verbs. Display the action and stage timer as stable, clear elements.
- The countdown must be labeled `Time remaining for this step` or similarly specific, **not** ambiguously `Time remaining`.
- A stage progress bar is optional; use one restrained accent color and real progress data.
- Use green/amber/red only for meaningful confirmed status; never rely on colors alone.
- Allow the mandatory **one-shot operator stage pop-up** described above; otherwise limit animation to subtle functional transitions. No flashing effects, repetitive motion, or sudden reflow.
- Add optional audio cues (countdown beeps / start / end) **only if explicitly enabled**, using permission-aware APIs and respecting accessibility. No automatic loud sound.

#### Focus Mode (optional but recommended)

Provide a `Focus Mode` / `Exit Focus` control within the Measurement tab:

- Expand the Guided Task Panel into a distraction-free workspace; do not create a new route or tab.
- Hide configuration forms and non-essential acquisition details.
- Keep header device status, task number, **current instruction**, **very large countdown**, next step, Stop, and supported Pause/Resume.
- Show whether the session is live, paused, disconnected, or in error.
- Allow Esc to exit Focus Mode if practical; never make Esc stop hardware acquisition.
- No full-screen browser API dependency is required; a responsive expanded-panel state is sufficient.

#### Stage transition and timing rules

- Each task may have a **ready countdown**, an **active action/HOLD countdown**, and a **rest/transition countdown** with distinct labels, instructions, durations, and authoritative start/end timestamps.
- **Prepare** may wait for an explicit `I'm ready` operator action. No countdown should begin before the backend accepts readiness when confirmation is required.
- **Ready countdown** means the action has **not yet** started; do not label measurement samples as active/HOLD merely because the task is selected.
- At HOLD start, switch the screen clearly to the active instruction, start the hold countdown from backend timing, and record a stage event/marker.
- At HOLD end, tell the user **Release / Relax** immediately. Record the active-end marker even if the next phase is a waiting interval.
- During Rest/Transition, show what the user should do and the seconds remaining **until the next stage**. Do not display the previous hold instruction during rest.
- On a timed boundary, do not advance solely because a browser timer reaches `00:00`. The backend protocol runner confirms stage changes and supplies authoritative timestamps. Show `Transitioning…` briefly if the backend update is late; never display negative seconds.
- For manual transitions, show a deliberate `I'm ready` / `Next task` button and wait indefinitely without fake countdown. Confirm button actions through the backend.
- Pause must freeze the applicable protocol stage timers; whether physical excitation or acquisition pauses is a distinct, verified hardware decision. The UI must say when *guidance is paused but acquisition remains active*.
- Stop must remain visible in every active guided stage. If the backend reports a device error/disconnection, halt task advancement and replace the guidance screen with a clear error/recovery instruction, without claiming that excitation safely ended.
- Preserve stage start/end timestamps, `taskId`, `stageId`, operator acknowledgments, pause intervals, and actual vs planned durations; correlate sample timestamps with active HOLD and rest intervals.
- During reconnection/browser refresh, recover the correct task **and** stage plus authoritative remaining time. Never restart a countdown merely because the component remounted.

**Example operator-visible sequence, all timings configurable:**

```text
Task 2 of 5 — Arm movement
[PREPARE]          Put your arm in the starting position.   [I'm ready]
[GET READY]        Raise your arm in...                     00:05
[HOLD]             Keep your arm raised and still.         00:20
[RELAX / WAIT]     Lower your arm; next task in...          00:05
[NEXT TASK]        Task 3 of 5 — Breathe normally.
```

The most important feature is the **correct, easy-to-follow sequence of human instructions**, not a dashboard full of metrics.

### Results tab

**Do not show fake scientific results in production mode.** Results view should include:

1. **Session summary:** session ID/date, protocol, duration, configuration snapshot, number of valid measurements, completion status.
2. **EIT reconstruction:** actual reconstructed image if an algorithm and data are available; correct geometry, physical or relative value labeling, explicit colormap and legend, time/frame selector, reconstruction method, baseline/reference context. If unavailable: `Reconstruction not available`.
3. **Time-series chart:** select one meaningful metric at a time (e.g. measured voltage, Re(Z), Im(Z), |Z|, phase), contingent on actual available values and correct units. Axis labels, sample timing, gaps/missing values, and selected electrode/path must be clear.
4. **Task annotations:** draw task intervals/events on the time axis to correlate activities with measurements.
5. **Export:** raw records, timing/events, electrode routing, excitation settings, configuration snapshot, processed/reconstructed data as available. CSV/JSON for structured data, image export for actual rendered outputs.

Use scientific colormaps for encoded data where warranted; the 'no gradients' rule applies to ornamental UI surfaces, not scientifically valid heatmaps.

### Sessions tab

A simple table: Session ID, date/time, protocol, duration, status, View Results. Optional compact filtering by date/status/protocol. Save and reopen sessions without accidentally restarting acquisition. Avoid KPI cards and analytics sections.

### Responsiveness/accessibility

- Desktop-first at 1366 / 1440 px; functional at ~1024 px and smaller.
- On narrower screens, stack configuration and task panels without hiding the critical task/timer/stop controls.
- Semantic HTML, proper labels/units, keyboard-accessible controls, visible focus indicators and meaningful status text (not color alone).
- Ensure the guidance panel is legible from a practical working distance; avoid excessive scrolling, automatic scrolling, and visual reflow.

---

## 5. Design Tokens and CSS Rules

Use a **single** global theme source of truth: `frontend/theme.py`.

| Token | Default |
|---|---|
| `--background` | `#FFFFFF` |
| `--surface` | `#F9FAFB` |
| `--foreground` | `#111827` |
| `--muted-foreground` | `#6B7280` |
| `--border` | `#E5E7EB` |
| `--primary` | `#2563EB` |
| `--success` | `#16A34A` |
| `--warning` | `#D97706` |
| `--danger` | `#DC2626` |
| Body typography | Inter/Geist/system sans, `14px`, line-height `1.5` |
| Secondary labels | `12–13px` |
| Section headings | `16–18px`, weight `600` |
| Page headings | `20–24px`, weight `600` |
| Primary guided-stage countdown | `64–96px`, tabular numerals; `96–120px` in Focus Mode where space allows |
| Main active task instruction | `28–36px` (up to `40px` in Focus Mode) |
| Stage commands / next-step helper | `16–20px` / `16–18px` |
| Font weights | `400`, `500`, `600` |
| Spacing scale | `4, 8, 12, 16, 24, 32px` |
| Button/input radius | `6px` |
| Panel radius | `8px` (absolute typical max `12px`) |
| Border | `1px solid var(--border)` |
| Shadow | None or extremely subtle |
| Transition | `150–200ms` for interaction feedback only |
| Config panel width | `260–300px` (may collapse in Focus Mode) |
| Content max width | ~`1440px` or available width needed for plots |

In this project the tokens above live in `frontend/theme.py` (`TOKENS`), are turned into one Qt stylesheet by `stylesheet()` and applied once to the `QApplication` (`frontend/app.py`). Widgets choose a style through `setObjectName(...)` (for example `Countdown`, `Instruction`, `Primary`), never through hardcoded colors. Timers use `theme.tabular(label)` for tabular digits. A disabled primary button must look disabled.

**Forbidden ornamentation:** background gradients, glassmorphism/backdrop blur, neon/glow, oversized headings, decorative illustrations, heavy drop shadows, excessive rounding, gratuitous chart widgets, animation without a functional state cue, more than one primary action per panel, nested cards where whitespace works, needless icons, and excessive wrapper `<div>` elements.

---

## 6. State Machines, Timing, and Workflow Semantics

### Device states

`disconnected → connecting → connected`; `error` may occur from any failed connection/operation. Recovery is explicit and stateful.

### Measurement states

`idle → preparing → running → completed`

Additional supported transitions: `running ↔ paused` (only where pause semantics are defined), `preparing/running/paused → stopping → completed` (or another explicit stopped terminal state), and failures to `error` with saved partial data where possible. Represent user-stopped sessions distinctly from naturally completed sessions in persisted metadata, even if the UI groups them.

### Task and guidance-stage states

Task states: `pending → active → completed`; `active ↔ paused` if supported; `skipped` only if expressly allowed.

For the active task, persist an **independent guidance-stage state**:

`prepare/awaiting_ready → ready_countdown → action_or_hold → rest_transition → completed`

An optional **`announcement_lead_in` sub-state/event** may precede an active stage when the protocol has `announcement.mode = before_stage`. It has its own confirmed start/end timestamps and does **not** reduce the following HOLD/REST/READY active duration. In contrast, an `overlay` announcement is UI presentation concurrent with its stage, not an extra state transition.

Allow optional stages to be skipped when intentionally disabled in a validated protocol. An explicit manual gate may be inserted before stage/task advancement. Store task ID and stage ID separately; a task remains active throughout its configured phases. **The backend protocol runner is authoritative** for both task and stage transitions and saved event timestamps.

### Timer definitions

- **Wall clock:** current system time, `HH:mm:ss`. Pure display, not experimental elapsed time.
- **Session elapsed:** accumulated active session duration according to the project's explicitly defined pause policy.
- **Task elapsed:** active duration since task start, excluding task pause durations when relevant.
- **Stage remaining (dominant):** `max(0, stage planned duration − stage active elapsed)` for Ready, HOLD/Perform and Rest/Transition. Show the label for the current stage. During a `before_stage` lead-in, label its countdown **Starting in** rather than showing the not-yet-started HOLD time as running.
- **Task remaining (optional secondary):** total remaining *timed* duration for the current task where calculable; do not make it the large main timer in a multi-stage task.
- Optionally display overall protocol progress only when durations/completion criteria are known.

**Timing correctness requirements:**

- Persist authoritative server timestamps, task event timestamps, pause intervals, and session identifiers.
- Use an appropriate backend monotonic clock for in-process duration measurement; use UTC timestamps for durable correlation and local time for display.
- On frontend, derive smooth display ticks from confirmed timestamps plus a local monotonic clock such as `performance.now()`, resynchronizing on events/reconnect; do **not** count `setInterval` calls as the source of truth.
- Handle browser tab throttling, disconnects, refreshes, pause/resume, backend restarts, and duplicate events without drift or duplicate state transitions.
- Associate every sample or sample batch with acquisition timestamps (or a documented sample clock/timebase) and the corresponding task interval. Identify clock synchronization uncertainty when backend/device and browser clocks differ.
- If acquisition and task protocol are decoupled, model that explicitly; pausing a task must not imply that physical excitation has paused.
- Never transition a protocol **stage or task** solely because the browser countdown hit zero; reconcile with backend-confirmed progress.
- Stage events must distinguish Ready start/end, HOLD/Perform start/end and Rest start/end; task annotations on plots can therefore show each interval correctly.

### UI states

Start disabled until backend confirms connected/ready and configuration/protocol validity. Pause and Resume available only in their valid states. Stop remains easily accessible during acquisition. Expose *preparing*, *stopping*, *stale*, and *error* explicitly; do not optimistically show *running*, *connected*, or *completed* before acknowledgment.

---

## 7. Backend, Live Events, and Persistence Contracts

### Service interface (what the interface calls)

The interface calls plain Python functions/objects in `backend/app/services/` (✓ exists, ○ planned; names are fixed when the step is built):

| Purpose | Call |
|---|---|
| Settings and designs in the data folder | `configuration.list_measurement_files()`, `list_design_files()`, `describe_measurement(path)`, `describe_design(design, measurement)` ✓ |
| Schedule of a design | `protocol_runner.expand(design, frame_s)`, `validate(...)`, `schedule_summary(design, measurement)` ✓ |
| Device | `DeviceService.connect(uri)`, `disconnect()`, `capabilities()`, `apply(config)`, `read_back()` ○ |
| Session control | `SessionService.start(config, design)`, `pause()`, `resume()`, `stop()` ○ |
| History and results | `sessions.list()`, `sessions.open(id)`, `sessions.export(id)` ○; analysis through `eit.report.check_session` / `run_study` ✓ |

These are **application contracts**, not device API method names.

### Live events (Qt signals emitted by backend workers)

- `device_status(state, detail)` — disconnected / connecting / connected / error
- `measurement_status(state)` — idle / preparing / running / paused / stopping / completed / error
- `measurement_progress(frame, index, total)` and, when useful, `measurement_batch(records)`
- `stage_changed(event)` — task ID, stage ID (PREPARE / GET READY / HOLD / RELEASE), authoritative start time (monotonic + UTC), planned duration, sequence number
- `session_timing(...)`, `error(message, recoverable)`

Each event carries a sequence number so the interface ignores stale or duplicated events. Signals are emitted from the worker thread and delivered to the interface thread by Qt (queued connection); widgets never read hardware state directly. Do not push every raw sample through widget updates if a batch is enough.

### Commands and integrity

- Acknowledge start/stop/configure commands with real backend state, including errors.
- Guard against duplicated commands and conflicting concurrent sessions; use session IDs and idempotency protections where appropriate.
- Don't pretend REST request completion means the analog hardware has finished its physical transition unless the backend verifies it.
- Store immutable snapshots of configuration and protocol used by each session.
- Preserve raw measurement records separately from processed results and visualization state.
- Persist electrode routing, excitation settings, calibration/version info when available, measurement values/units, timestamps, and task events.
- Make missing/invalid data explicit (`null`, gap, error code), not fake zeros or invented readings.
- Choose an appropriately simple storage mechanism for the existing codebase. A small local database plus files is acceptable; don't add a distributed system or complex infrastructure unnecessarily.

### Session storage format in this project

Sessions are written to `data/sessions/<session>/` in the format of the 2026-10-05 pilot, because the analysis (`backend/app/eit/io.py`, commands `check` and `study`) reads it and old and new sessions must be analysed together: `meta.json` (settings, wiring, sequence, timing, versions, status), `patterns.csv` (one row per measurement: frame, task, routing, `real_raw`, `imag_raw`, start/end time, error), `frames.csv`, `events.csv` (cues and stage changes), `plan.csv` and `schedule.csv` (the expanded schedule: block order, instructions, planned cue and capture times), `configuration_checks.csv` and `.json` (read-back before/after frames), optional `trial_windows.csv` (operator confirmation, `valid` flag). A new **live** session is accepted only when `python -m app check` passes on it. Demo sessions carry the pilot's marker (`meta.json` `source` = `settings.mode` = `"mock"`), which `eit/io.py` refuses to analyse; keep them apart from real sessions (a demo option for `check` may be added when the demo adapter exists). Raw session folders are never modified after recording; analysis output goes to `data/results/`.

### Demo mode

Mock device/acquisition is allowed **only in an explicitly labeled Demo Mode**. Distinguish it throughout the UI, API metadata, exports, and saved session records. Never make demo start/stop appear to be a successful physical hardware action. Synthetic reconstructions must be labeled illustrative, not real measured images.

---

## 8. Folder Structure and Source Ownership — DETAILED PROJECT GUIDE

**This section is mandatory for coding agents.** Use a **feature-based frontend** and **layered backend** so that changing the timer, stage pop-up, CN0565 hardware driver, protocol definitions, scientific algorithm, or session storage does not require rewriting unrelated modules. The tree below is the **actual layout of this project** (`✓` exists, `○` planned). Add a planned file only when its responsibility is implemented; never create empty placeholders.

### 8.1. Repository tree of this project

```text
eit-measurement/                           # application root (inside the research repo eit-cn0565/)
├── AGENTS.md                              ✓ THIS project-wide coding guide
├── README.md                              ✓ Folder map, setup, commands, where to change what
│
├── requirements.txt                       ✓ Everything the app needs (backend + PySide6)
├── frontend/                              ✓ PySide6 desktop interface; no hardware calls, no logic (run: python -m frontend)
│   ├── __main__.py, app.py                ✓ start: QApplication, theme, main window
│   ├── main_window.py                     ✓ header (title, session, device status, clock) + EXACTLY 3 tabs
│   ├── theme.py                           ✓ ONE source of design tokens → Qt stylesheet
│   ├── features/
│   │   ├── measurement/  measurement_page.py ✓ (config column + guidance panel, read-only);
│   │   │                 controls.py, experiment_timer.py, session_clock.py ○
│   │   ├── device/       device_connection.py ○
│   │   ├── configuration/ configuration_panel.py ○
│   │   ├── protocol/     protocol_editor.py, task_guidance_panel.py, stage_announcement.py, task_timeline.py ○
│   │   ├── results/      results_page.py ✓ (empty state), eit_viewer.py, signal_chart.py ○
│   │   └── sessions/     sessions_page.py ✓ (empty state), sessions_table.py ○
│   ├── widgets/                           ○ shared generic widgets only (no EIT knowledge)
│   └── tests/                             ✓ offscreen Qt tests (test_shell.py)
│
├── backend/
│   ├── requirements.txt                   ✓ Pinned analysis packages (also used by the command line)
│   ├── app/
│   │   ├── __init__.py                    ✓
│   │   ├── __main__.py                    ✓ Command line: python -m app {design, check, study, hash}
│   │   ├── schemas/
│   │   │   └── models.py                  ✓ MeasurementConfig, wiring loaders, StudyDesign/TaskSpec/StageTiming
│   │   │                                    (dataclasses now; Pydantic models when the API exists)
│   │   ├── hardware/                      ○ base.py (adapter contract), cn0565.py (real board), mock.py (demo)
│   │   ├── services/
│   │   │   ├── configuration.py           ✓ settings/designs in the data folder, described for the interface
│   │   │   ├── protocol_runner.py         ✓ expand()/validate()/schedule_summary(); ○ live stage machine
│   │   │   ├── acquisition.py             ○ per-measurement loop, timestamps, read-back, errors
│   │   │   └── session_manager.py         ○ session lifecycle; writes the pilot session format (§7)
│   │   ├── eit/                           ✓ Pure scientific analysis (formerly `eitpilot`)
│   │   │   ├── protocol.py                ✓ make_sequence(n, force, sense), ring geometry, frame duration
│   │   │   ├── io.py                      ✓ reads a session folder (meta.json, patterns.csv, ...)
│   │   │   ├── qc.py                      ✓ audit, timeline, reciprocity + drive-gain null test, REST noise
│   │   │   ├── features.py                ✓ relative change dz, baselines, lateralisation, involvement, recognition
│   │   │   ├── recon.py                   ✓ BP / JAC / GREIT (pyEIT 1.2.4), metrics, known-target check
│   │   │   ├── plots.py                   ✓ figures (English text only)
│   │   │   ├── report.py                  ✓ `check` and `study` orchestration, manifest, auto README
│   │   │   └── config.py                  ✓ analysis defaults, project root, path resolution
│   │   └── core/                          ✓ config.py (data folder: EIT_DATA_ROOT or data/); ○ logging.py
│   └── tests/                             ✓ test_core, test_configuration, test_pipeline_synthetic,
│                                            test_regression (+ fixtures/); add test_api_*, test_hardware_mock
│
├── data/                                  # Everything the user edits or the system produces; never code
│   ├── hardware/                          ✓ wiring files + measurement settings presets
│   ├── protocols/                         ✓ study designs (+ schedules/ printed by `app design --out`)
│   ├── studies/                           ✓ analysis configurations
│   ├── sessions/                          ✓ raw sessions (pilot format, §7), never edited
│   ├── bench/                             ○ raw output of the Windows toolkit (bench checks, ADI examples; created on first use)
│   └── results/                           ✓ analysis outputs (regenerated), checks/<session>/
│
├── packaging/                             ○ PyInstaller spec + Inno Setup script (§8.12)
│
└── docs/
    ├── architecture.md                    ✓ Big picture, pipeline, build plan + progress, change log
    ├── pipeline.md                        ✓ Data collection → QC → analysis procedure
    └── hardware-mapping.md                ✓ Verified CN0565 transport, attributes, wiring, timing
```

Outside `eit-measurement/` (repository root, not part of the application): `docs/` (research notes, reports, Windows connection guides), `reference/` (datasheets, circuit note, board files, firmware, papers), `presentations/`, `archive/`, and the Windows hardware toolkit (`scripts/`, `examples/`, `work/`, `bootstrap-cn0565-env.ps1`, `requirements.txt`, `cn0565-env/`). The toolkit stays there because the Windows PC uses those paths; its board-communication parts (serial proxy, connection check) move into `backend/app/hardware/` when the hardware adapter is built.

**Optional extensions only when justified:** `frontend/features/*/test_*.py` for colocated UI tests; `backend/app/storage/` for a real persistence adapter when `session_manager.py` becomes too large; `backend/app/hardware/ad5940.py` or `adg2128.py` only if these separate adapters reflect the real driver responsibilities. Do not introduce these folders/files as empty placeholders. Existing monorepo tooling or package managers may use different configuration filenames—reuse them.

### 8.2. Responsibility of each top-level folder

| Folder | Owns | Must NOT own |
|---|---|---|
| `frontend/` | PySide6 presentation, accessible controls, forms, rendering confirmed state, stage-entry animation | Direct `adi.*`/`iio` calls, serial ports, measurement/timing logic, analysis |
| `backend/app/hardware/` | Physical CN0565/AD5940/ADG2128 interface, capability discovery, firmware transport adaptation (serial proxy) | Widgets, protocol wording, chart styles |
| `backend/app/services/` | Acquisition, task timing, session state, consistency, orchestration | UI component code, unverified hardware assumptions |
| `backend/app/eit/` | Pure scientific analysis (existing package: sequence, session reader, QC, features, reconstruction, report) | Qt, widgets, UI colors, driver connection lifecycle |
| `backend/app/schemas/` | Stable data contracts (configuration, design, later events/records) and their validation | Business workflow implementation |
| `backend/app/core/` | Runtime settings: data folder (`EIT_DATA_ROOT`), later logging | Measurement or UI logic |
| `data/hardware/` | Wiring files and measurement-settings presets | Code; unverified limits presented as verified |
| `data/protocols/` | Study designs (file based) and printed schedules | Executable application code |
| `data/studies/` | Analysis configurations (which sessions are analysed together) | Raw data |
| `data/sessions/` | Raw sessions in the pilot format (§7), never edited | Frontend source files or hardcoded demo datasets passed off as real |
| `data/results/` | Analysis outputs regenerated by `python -m app study` / `check` | Hand-edited results |
| `data/bench/` | Raw output of the Windows toolkit scripts (bench checks, ADI examples) | Pilot-format sessions (those belong in `data/sessions/`) |
| `docs/` | Verified architecture/driver/wiring notes | Duplicated full specifications already contained in `AGENTS.md` |

### 8.3. Frontend: what belongs in each specific file

The left column gives the generic (React) name used elsewhere in this document; the PySide6 module is the file to edit.

| Generic name in this document | PySide6 module (under `frontend/`) | Edit it when | Do not put here |
|---|---|---|---|
| `App.tsx` + `AppLayout.tsx` | `main_window.py` (`MainWindow`, `AppHeader`) | tabs, header, device badge, clock, Focus Mode shell | countdown math, AD5940 logic, persistence |
| `DeviceConnection.tsx` | `features/device/device_connection.py` | port/URI selector, Connect/Disconnect, feedback | serial or firmware transport code |
| `ConfigurationPanel.tsx`, `configSchema.ts` | `features/configuration/configuration_panel.py` | amplitude/frequency/electrode inputs, showing backend validation | invented hardware limits or safety claims |
| `MeasurementPage.tsx` | `features/measurement/measurement_page.py` | arrangement of config column, dominant guidance, controls, timeline | the state machine or sampling |
| `MeasurementControls.tsx` | `features/measurement/controls.py` | Start/Pause/Resume/Stop and their acknowledged states | optimistic hardware transitions |
| `ExperimentTimer.tsx`, `useSessionClock.ts` | `features/measurement/experiment_timer.py`, `session_clock.py` | countdown display from backend timestamps (`QTimer` ticks + monotonic clock) | authoritative transitions |
| `ProtocolEditor.tsx` | `features/protocol/protocol_editor.py` | task text, durations, pop-up and lead-in settings, preview | acquisition loops |
| `TaskGuidancePanel.tsx` | `features/protocol/task_guidance_panel.py` (today: `GuidancePanel` in `measurement_page.py`) | large live instruction, next step, persistent timer | scheduling independent of the backend |
| `StageAnnouncement.tsx` + `stage-announcement.css` | `features/protocol/stage_announcement.py` (`QPropertyAnimation` for scale/opacity) | one-shot pop-up text, visibility, dismissal, deduplication, reduce-motion fallback | deciding when HOLD begins |
| `TaskTimeline.tsx` | `features/protocol/task_timeline.py` | sequence/status of all blocks | deciding task completion |
| `EITViewer.tsx`, `SignalChart.tsx` | `features/results/eit_viewer.py`, `signal_chart.py` | labelled image/colour scale, signal axes, task markers | reconstruction or acquisition |
| `SessionsTable.tsx` | `features/sessions/sessions_table.py` | columns, selection, open/export actions | writing experimental data |
| `theme.css` | `theme.py` | colours, typography, spacing tokens | feature logic |
| `lib/apiClient.ts`, `lib/websocket.ts` | (none) — direct calls into `backend/app/services/` and Qt signal connections | — | business decisions such as "next task now" |

**Explicit file locations:** the stage pop-up is `frontend/features/protocol/stage_announcement.py`; the large persistent instruction panel is `frontend/features/protocol/task_guidance_panel.py` (until it is built, `GuidancePanel` in `frontend/features/measurement/measurement_page.py`). The authoritative runner is `backend/app/services/protocol_runner.py`.

**Cross-feature UI policy:** Place a component under the feature it belongs to by default. Only move it to `frontend/widgets/` if it is genuinely generic (Button/Input/Dialog/Select) and does not know anything about EIT, protocols, devices, or sessions.

### 8.4. Backend: what belongs in each specific file

| File | Purpose | Key rule |
|---|---|---|
| `core/config.py` | Data folder: `data_root()` = `EIT_DATA_ROOT` or `eit-measurement/data/`, `data_path(...)` | Every data path goes through it (installed app → user folder) |
| `services/configuration.py` | Lists settings/designs in the data folder and describes them for the interface | Return values and problems; no widgets |
| `schemas/models.py` | Now: `MeasurementConfig`, wiring loaders, `StudyDesign`, `TaskSpec`, `StageTiming`. Later: `Session`, `Event`, `Sample`, announcements | One contract, version as needed; split only when unwieldy |
| `hardware/base.py` | Minimum adapter interface for real and demo devices | Do not commit to fictional pyadi-iio function signatures |
| `hardware/cn0565.py` | Real device connection, excitation and verified electrode routing/reading | Check AD5940 and ADG2128 APIs and units against installed code |
| `hardware/mock.py` | Deterministic synthetic device responses for demo/tests | Demo marker in every record (`source: "mock"` in meta.json, as in the pilot format) |
| `services/acquisition.py` | Acquisition schedule, sample timestamps, quality/error flags | Separate acquisition timebase from UI rendering time |
| `services/protocol_runner.py` | Now: `expand()` (study design → schedule), `validate()` (HOLD fits the frames and the cap). Later: manual PREPARE gate, GET READY, HOLD, RELEASE, announcement lead-in, task transitions | **Only backend decides stage boundaries** |
| `services/session_manager.py` | Session IDs, snapshots, lifecycle and persistence | Keep partial measurements on Stop/error |
| `eit/protocol.py` | Measurement sequence from (electrodes, force distance, sense distance); frame duration | Same rows and order as the ADI driver and pyEIT (tested) |
| `eit/io.py`, `eit/qc.py` | Read a session folder; integrity audit, timing, reciprocity, noise | Never modify raw files |
| `eit/features.py` | Relative change dz = (V − V_REST)/V_REST, baselines, lateralisation, involvement, recognition | No hidden rescaling or assumed units |
| `eit/recon.py` | BP/JAC/GREIT with pyEIT on a 2-D disk; metrics; known-target check | Images are exploratory 2-D projections, label them so |
| `eit/report.py`, `__main__.py` | `check` / `study` outputs, manifest (git commit, versions, hashes), auto README; command line | Analysis outputs only under `data/results/`; printed schedules under `data/protocols/schedules/`; a relative `--out` is taken from `eit-measurement/` |
| `core/config.py` | Runtime settings (device URI, demo mode); data paths reuse `eit/config.py` (`REPO`, `resolve()`, `resolve_out()`) | No secrets embedded in source |

**AD5940 / ADG2128 separation:** `cn0565.py` may coordinate both chips through the existing pyadi-iio CN0565 wrapper. Only split chip-specific code into separate files once the actual implementation is large enough and the methods can be tested independently. Never create fake low-level chip drivers solely to match a folder tree.

### 8.5. Protocol configuration, announcement popup and ownership

**In this project** the JSON shape in this section describes **one block of the expanded schedule** produced by `services/protocol_runner.expand()` and saved with each session; it is not the file in `data/protocols/` (that file is a `StudyDesign`, see §4). Its HOLD duration is derived (§2, rule 2) and its `rest` stage is RELEASE. Announcement fields (`displaySeconds`, `mode`, `leadInSeconds`) are added to the study design when the editor is built.

The **protocol definition**, not a widget, must define task text, phase durations, configured announcement visibility, and optional pre-stage lead-in time. Persist it via backend protocol storage/API. The frontend editor consumes/updates it; the backend validates and enforces phase/lead-in semantics; the pop-up component handles only visual presentation.

#### Suggested portable JSON shape (illustrative, not a driver API)

```json
{
  "id": "arm-hold-demo",
  "name": "Arm movement example",
  "revision": 1,
  "tasks": [
    {
      "id": "arm-position-01",
      "title": "Raise and hold arm",
      "stages": [
        {
          "id": "prepare",
          "type": "prepare",
          "instruction": "Move your arm to the starting position.",
          "durationSeconds": null,
          "requiresConfirmation": true,
          "announcement": {"text": "PREPARE", "displaySeconds": 5, "mode": "overlay", "leadInSeconds": 0}
        },
        {
          "id": "ready",
          "type": "get_ready",
          "instruction": "The movement will begin shortly.",
          "durationSeconds": 5,
          "announcement": {"text": "GET READY", "displaySeconds": 3, "mode": "overlay", "leadInSeconds": 0}
        },
        {
          "id": "hold",
          "type": "hold",
          "instruction": "Keep your arm raised and still.",
          "durationSeconds": 20,
          "announcement": {"text": "HOLD BEGINS IN 3 SECONDS", "displaySeconds": 3, "mode": "before_stage", "leadInSeconds": 3}
        },
        {
          "id": "rest",
          "type": "rest",
          "instruction": "Lower your arm and relax.",
          "durationSeconds": 5,
          "announcement": {"text": "RELAX", "displaySeconds": 2, "mode": "overlay", "leadInSeconds": 0}
        }
      ]
    }
  ]
}
```

**Interpretation:** PREPARE waits for operator acknowledgment; its 5 s pop-up does not trigger stage advancement. GET READY lasts 5 s total, with its pop-up visible for 3 s concurrently. The additional HOLD reading cue appears for 3 s *before HOLD begins*, then the operator receives the **full 20 s HOLD**. REST lasts 5 s with its 2 s pop-up during the rest interval. The backend records distinct events for the lead-in and actual HOLD onset. This example is only a demo protocol and is not a validated human-subject procedure.

**Validation rules:** `displaySeconds >= 0`; active timed stages have valid positive durations; `before_stage` requires `leadInSeconds >= displaySeconds > 0`; `overlay` has `leadInSeconds = 0`; long overlay pop-ups should not exceed an active stage's duration (either reject or show a clear warning and truncate with authoritative transitions). PREPARE manual gates never release themselves when a pop-up fades. Skip optional stages only with an explicitly validated zero/disabled setting. Do not double count the lead-in inside GET READY if a protocol author has already allocated that time there.

**Editing workflow:** User changes durations/announcements in `frontend/features/protocol/protocol_editor.py` → a backend service validates with `schemas/models.py` / `protocol_runner.validate()` → study design saved in `data/protocols/` → `protocol_runner.expand()` → the runner (worker thread) executes the expanded schedule snapshot → Qt signal `stage_changed` carries stage/lead-in IDs and timestamps → `stage_announcement.py` animates once → `task_guidance_panel.py` / `experiment_timer.py` render the current state and accurate countdown.

### 8.6. Where to store protocols, results, exports and configuration

**Source code never lives under `data/`.** Actual layout of this project:

```text
data/
├── hardware/
│   ├── C16-R-user-interleaved-TMJ5-v2-208.json   # wiring of the 16-cup facial cable
│   └── measurement-16el-50kHz.json               # measurement settings preset
├── protocols/
│   ├── facial-rest-task-rest-v1.json              # study design (edited in the app later)
│   └── schedules/                                 # printed schedules (created by `app design --out data/protocols/schedules/<name>`)
├── studies/
│   └── three-frequency-20261005.json              # analysis configuration
├── sessions/
│   └── <session>/                                 # meta.json, patterns.csv, frames.csv, events.csv, ... (§7)
├── bench/                                         # Windows-toolkit output (old PREFIX.voltages.csv format), not sessions
└── results/
    ├── <study_id>/                                # tables/, figures/, slides/, clean/, manifest.json, README.md
    └── checks/<session>/                          # output of `app check`
```

- Treat protocol files as **data**, not as source for hardcoded component behavior. Prefer editing protocols through the app, with schema validation.
- Session snapshots must be immutable after creation except for defined lifecycle updates; changes to a protocol must not retroactively change the timeline of past sessions.
- Save raw measurement values with timestamps/timebases, units, routing and applied excitation metadata. Keep raw, processed and reconstructed data distinguishable.
- A `data/exports/` folder is optional for generated CSV/JSON/image exports; use it only if exports are stored rather than streamed.
- Settings come from environment variables read in `backend/app/core/config.py`: `EIT_DATA_ROOT` (data folder; the installed app sets it to the user's documents folder); later device URI and demo mode.
- Never commit `.env`, participant-identifying records, actual raw experiments, device credentials, large binary reconstructions, caches or log files by default. Use `.gitignore`, controlled retention, and appropriate access controls.
- For larger measurement sets, choose an efficient durable format and document its schema; avoid forcing all high-rate raw samples into one growing JSON file.

### 8.7. Module dependency direction

```text
frontend/main_window ──> frontend/features ──(direct calls)──> backend/app/services
        ▲                                                         │            │
        └──────────────(Qt signals from worker threads)──────────┤            │
                                                                  ▼            ▼
                                                  backend/app/hardware   backend/app/eit
                                                                  │
                                                                  ▼
                                   pyadi-iio / libiio → serial proxy → real CN0565
```

`backend/app/schemas` defines the contracts shared by all layers; `backend/app/core` gives the data folder; `data/` is owned by backend persistence. `eit/` must not import `services/`, `hardware/`, `frontend/` or Qt. `backend/` must not import `frontend/` (the backend stays usable from the command line and by a future web interface). Hardware code must not import frontend code. Services may call hardware and pure scientific functions; the reverse must not happen.

### 8.8. Where to edit what — QUICK LOOKUP

| User request | Primary files to edit | Extra check |
|---|---|---|
| Change number of electrodes, drive/sense distance, frequency, amplitude preset | `data/hardware/measurement-*.json` (validation: `schemas/models.py`) | Derived frame time and HOLD change everywhere |
| Change tasks, instructions, stage timing, rounds, seed | `data/protocols/*.json` (rules: `services/protocol_runner.py`) | Run `python -m app design … --measurement …` |
| Change the measurement sequence math | `backend/app/eit/protocol.py` | Keep it identical to the driver/pyEIT order (tests) |
| Change analysis, QC or figures | `backend/app/eit/` | Regression test must still pass, or update its fixture deliberately |
| Change whole UI color/font/spacing | `frontend/theme.py` | No duplicate hardcoded colors |
| Change the top 3 tabs/header | `frontend/main_window.py` | Remain exactly three tabs |
| Change CN0565 connection UI | `frontend/features/device/device_connection.py` (+ device service) | Backend actually connected |
| Change amplitude/frequency/electrode controls | `frontend/features/configuration/configuration_panel.py` | Backend capability-driven limits |
| Change AD5940 amplitude/frequency operations | `backend/app/hardware/cn0565.py` | Verify actual driver/firmware calls |
| Change ADG2128 crosspoint routing | `backend/app/hardware/cn0565.py` or existing split driver, `docs/hardware-mapping.md` | Verify topology/wiring |
| Make task instruction/countdown **bigger** | `frontend/features/protocol/task_guidance_panel.py`, `frontend/features/measurement/experiment_timer.py`, `frontend/theme.py` | Keep Stop visible |
| Edit task names, duration, instructions | `data/protocols/*.json`; later `frontend/features/protocol/protocol_editor.py` + `schemas/models.py` | Backend validation |
| **Edit pop-up visibility 2s/3s/5s/8s** | `protocol_editor.py`, study-design model/storage, `stage_announcement.py` | `displaySeconds` is not HOLD duration |
| **Give more reading time BEFORE HOLD** | `protocol_editor.py`, `backend/app/services/protocol_runner.py`, study-design model | Separate `leadInSeconds` from HOLD duration |
| Change stage pop animation style | `frontend/features/protocol/stage_announcement.py` | No flashing; reduce-motion setting; no backend timing changes |
| Change which step comes next | `backend/app/services/protocol_runner.py` | Backend source of truth |
| Fix timer drift / pause behavior | `backend/app/services/protocol_runner.py`, `frontend/features/measurement/session_clock.py` | Test restart and exact stage boundary |
| Change Start/Pause/Resume/Stop UI | `frontend/features/measurement/controls.py` | Stop always available during active acquisition |
| Change acquisition sequence or sample metadata | `backend/app/services/acquisition.py`, hardware adapter as needed | Preserve raw timestamps and routing |
| Change Results visuals | `frontend/features/results/` | Correct physical units and task markers |
| Change EIT algorithm | `backend/app/eit/` | Never place reconstruction in the interface |
| Change session storage | `backend/app/services/session_manager.py` or `storage/` if created | Old sessions still load |
| Change a service function or signal the interface uses | `backend/app/services/`, `schemas/`, and the calling widget | Update both sides and their tests |
| Change where data is stored | `backend/app/core/config.py` | Installed app writes only to the user data folder |
| Change packaging/installer | `packaging/` (§8.12) | Run the packaging smoke test |
| Add automated test | `backend/tests/`, `frontend/tests/` | Use mock device; hardware tests separately |

### 8.9. Rules for creating, moving and naming files

1. **Inspect before creating**: search the repo for an existing owner; edit it if appropriate.
2. **One responsibility per module**: interface renders and calls; services validate and orchestrate; hardware communicates; EIT computes; storage persists.
3. **Name files for functionality**: Python modules `snake_case.py`; Qt widget classes `PascalCase`; signals `snake_case` past-tense events (`stage_changed`).
4. **No monolithic files**: avoid a huge `main_window.py`, `measurement_page.py`, `protocol_runner.py` or `utils.py` with unrelated behaviors. Refactor only when cohesion or testability materially improves.
5. **Keep complexity local**: feature-private UI helpers stay in that feature folder. Promote to shared only when at least two features benefit and there is a stable interface.
6. **No circular imports**, deep nested folders, placeholder adapters or parallel theme systems.
7. **No speculative splitting**: don't make one file per trivial function or a separate file per ADG2128 chip without a real reason. Aim for readable components (~100–250 lines when practical, but not a hard rule).
8. **Atomic feature changes**: when one change spans frontend, API contract, backend service and tests, make the minimal coordinated changes in those owning locations; don't mix unrelated visual refactors.
9. **Maintain one source of truth** for validated hardware limits, authoritative protocol timing, server session state, stored raw values and global design tokens.
10. **Preserve working code**: the tree in §8.1 is the agreed layout; extend it, do not rebuild or rename functioning modules (`backend/app/eit/` keeps its tested behavior; change it only with tests).

### 8.10. Short developer recipes

**A. Change HOLD:** change `frames`/`frames_per_task` or a task's `hold_s` in `data/protocols/*.json` (through Edit Protocol when it exists); `hold_s` must be ≥ the derived minimum and ≤ `hold_cap_s`, otherwise `validate()` rejects the design; the session uses its schedule snapshot; no CSS or AD5940 code changes.

**B. Show PREPARE pop-up for 8 seconds:** Change `announcement.displaySeconds` in the protocol; `stage_announcement.py` reads the confirmed event/config and auto-dismisses without releasing manual readiness. No timer is fabricated for PREPARE.

**C. Allow 5 seconds to read before a 20-second HOLD:** Set `hold.announcement.mode = before_stage`, `displaySeconds = 5`, `leadInSeconds = 5`, `hold.durationSeconds = 20`. Backend schedules 5 s anticipation plus full 20 s actual HOLD and stores their event boundaries. Announcement says `HOLD STARTS IN 5 S`, not `HOLD NOW`.

**D. Change the appearance of the pop-up:** Edit `frontend/features/protocol/stage_announcement.py` only. Do not touch `protocol_runner.py` unless stage timing semantics themselves change.

**E. Replace reconstruction algorithm:** Edit `backend/app/eit/`, update scientific metadata/contract and tests; results UI consumes algorithm outputs without assuming their origin.

**F. Connect a different verified device transport:** Modify the hardware adapter or connection configuration; keep frontend feature contracts stable where possible. Do not invent transport protocol implementation.

### 8.11. Required repository checks after a change

- Frontend: from the repository root run `.venv-sim/bin/python -m unittest discover -s eit-measurement/frontend/tests -p "test_*.py"` (Qt runs offscreen, no screen needed), and start the app once with `.venv-sim/bin/python -m frontend` when the layout changed.
- Backend: from the repository root run `.venv-sim/bin/python -m unittest discover -s eit-measurement/backend/tests -p "test_*.py"` (unittest; pytest is not installed), plus import/API contract checks. Never claim unexecuted hardware tests passed.
- Guide workflow: verify PREPARE/manual gate; popup show/dismiss; GET READY → HOLD → RELEASE → next task; pause/resume; Stop; fast stage transitions; reconnect; Focus Mode.
- Verify file placement: new code lives in the owning feature/layer, no duplicate configs or hidden data files in source folders.
- Update `README.md` when setup paths, environment variables or developer entry points actually change. Update `docs/hardware-mapping.md` only after verifying the mapping.

### 8.12. Packaging and distribution (target: one installer for other researchers)

```text
Python source ──PyInstaller──► folder with "EIT Measurement Studio.exe" ──Inno Setup──► EIT-Measurement-Studio-Setup-<version>.exe
```

- **Target:** Windows (the board is used there). Build on Windows with the same Python as `cn0565-env`.
- **Entry point:** `frontend/__main__.py`. Spec and installer script live in `packaging/` (built in a later step).
- **Must work from day one:** no logic in the interface; every data path through `backend/app/core/config.py`; the installed app sets `EIT_DATA_ROOT` to the user's documents folder and copies the default `data/hardware` and `data/protocols` there on first start; it never writes next to its program files.
- **The serial proxy runs inside the app** (started on Connect, stopped on Disconnect); users never run scripts.
- **Native libraries:** the package must include libiio (and its serial backend) for `pylibiio`; this is the most likely packaging failure, so a **packaging smoke test** (window + list COM ports + open the IIO context) is run early, before the full app exists.
- **Licences:** PySide6/Qt are LGPL (ship them as separate libraries, which PyInstaller does); pyEIT, numpy, scipy, pandas, matplotlib are permissive; pyadi-iio is ADI BSD. Keep a `THIRD_PARTY_NOTICES` file in the installer.
- **Identity and safety:** the window title and every saved session carry the app version; the app states "research use only, not a medical device" and enforces the validated excitation limits from the configuration; an unsigned installer triggers a Windows SmartScreen warning (code signing is optional, later).

**Default instruction when asked to add a feature:** *Identify the owner; modify the smallest relevant files; preserve public contracts and measurement integrity; add tests; explain exactly where future edits belong.*

---

## 9. Data Model Guidance

Define typed, serialized models (names illustrative; align with existing schema) for at least:

- `DeviceStatus`: connection state, device identity/URI, last verified heartbeat, capabilities/error.
- `DeviceCapabilities`: firmware/driver identity, excitation limits/units, supported patterns/electrodes, read/write capabilities, pause behavior.
- `MeasurementConfiguration`: excitation, frequency, routing/pattern, selected mode and immutable applied snapshot.
- `ElectrodeRouting`: force/sense electrode IDs and actual switch configuration/sequence identifier.
- `ExperimentProtocol`: ID, name, ordered `TaskDefinition[]`, revision.
- `TaskDefinition`: ID, title, ordered stage definitions (Prepare / Ready / Perform-HOLD / Rest), optional manual confirmation gates, and task transition policy.
- `GuidanceStageDefinition`: stage ID/type, operator-facing title/instruction, optional next-step preview, active duration in seconds (`null` for manual wait), completion policy, and optional `announcement` configuration.
- `AnnouncementConfiguration`: event-visible text, `displaySeconds`, `mode` (`overlay` or `before_stage`), and `leadInSeconds`; separate visual duration from actual phase duration.
- `AnnouncementLeadInEvent`: task/stage IDs, authoritative lead-in start/end, confirmation/event sequence and projected actual stage start.
- `GuidanceStageState`: active `taskId` + `stageId`, started-at, paused intervals, elapsed/remaining, optional await-confirmation and backend revision.
- `TaskEvent`: task ID, stage ID if applicable, ready/hold/rest/start/end/ack event type, authoritative timestamp, elapsed/pause accounting.
- `Session`: ID, protocol/config snapshots, device metadata, start/end/status, pause intervals, error/stop reason.
- `MeasurementRecord`: session ID, sequence number, acquisition timestamp/timebase, electrode mapping, raw/processed measurement and exact units/validity flags.
- `ReconstructionResult`: session/frame/time, array/grid/geometry, reconstruction method, reference, units/relative scale, validity and processing metadata.

Use the actual measurement representation supported by the device, including complex values where present. Represent invalid/nonfinite numbers safely for JSON serialization. Ensure export preserves unit conventions and parameter provenance.

---

## 10. Error, Status, and Failure UX

Show brief, actionable messages for:

- No device found / failed to connect.
- Invalid configuration or unsupported setting.
- Electrode routing conflict or unavailable electrode.
- Hardware communication timeout or acquisition failure.
- Device disconnected mid-session.
- Stale or invalid data.
- Session recoverability after process/browser interruption.
- Missing reference/baseline or unavailable reconstruction.

Never surface a raw Python traceback as normal UI text. Store useful diagnostics in backend logs (excluding unnecessary sensitive participant information). Display exact operator actions when known, e.g. `Check connection` or `Reconnect device`, but do not assert that reconnection or shutdown succeeded until confirmed.

---

## 11. Testing and Acceptance Criteria

### Automated tests (mock hardware)

- Device and measurement state transitions (including forbidden transitions).
- Limits, unit conversions, validation, electrode routing and capability mismatch.
- Start twice / stop twice / stale ACKs / duplicate events.
- Timed tasks, per-stage **Prepare → Ready → HOLD → Release → Next** transitions, optional omitted stages and manual gates.
- Editable stage announcement `displaySeconds`, overlay versus before-stage semantics, authoritative lead-in events, and full HOLD duration after reading time; test both 3-second and 5-second reading cues.
- Stage-specific instruction switches exactly when backend confirms transition; no hold instruction stays visible in Rest; a skipped/disabled stage does not create a bogus timer.
- Focus Mode always shows stage, large countdown and Stop; usable at 1366px without vertical scrolling.
- Pause/resume accounting, browser-refresh time reconciliation, no negative countdown, multiple reconnects.
- Device disconnect and measurement timeout with saved partial records.
- Timestamp ordering and correlation of measurements to tasks.
- Raw-data retention, exports with metadata and units, missing-data encoding.
- Reconstruction output schema and unavailable state.
- Accessible controls, disabled states, responsive layouts, and frontend build.

### Real hardware test plan (explicit/manual)

- Identify actual CN0565 firmware, driver and connection transport.
- Read verified device capabilities and electrode map.
- Configure supported excitation, run reference measurements, confirm calibrated units.
- Verify switch route sequence on actual connected electrodes (within validated safety limits).
- Check physical acquisition start/stop, failures, timing, and supported cancellation behavior.
- Check that disconnected/stale hardware cannot appear to be successfully measuring.

### Acceptance checklist

- [ ] Three tabs only: Measurement, Results, Sessions.
- [ ] Connected/Disconnected/Error status reflects actual backend state.
- [ ] Excitation parameters display correct units and validated capabilities.
- [ ] No unsupported standalone voltage or pause control is invented.
- [ ] Protocol editor supports ordered tasks, instructions and durations.
- [ ] **Edit Protocol can set pop-up reading/visibility seconds per stage, choose overlay or pre-stage lead-in, preview the result, and save/load without hardcoding.**
- [ ] **A configured 5-second pre-HOLD reading cue followed by a 20-second HOLD produces 5 seconds of lead-in plus the full 20-second active HOLD, with separate event timestamps.**
- [ ] **Large Guided Task Panel dominates Measurement; instruction + huge `64–96px` countdown are visible without scrolling.**
- [ ] Per-task **Prepare → Get Ready → Perform/HOLD → Relax/Wait → Next** flow is configurable, legible and backend-authoritative.
- [ ] Separate countdowns are shown for Ready, HOLD/Perform and Rest/Transition, with stage-specific instructions and next-step preview.
- [ ] Manual `I’m ready` / Next confirmations work when configured; optional Focus Mode keeps Stop visible.
- [ ] Pause/reconnect/refresh restores the correct stage and countdown without resetting or inventing a transition.
- [ ] Session elapsed, task elapsed, task remaining and wall clock are separate and correctly calculated.
- [ ] Backend owns real task/session state; UI reconciles after reconnect/refresh.
- [ ] Start/Stop and other controls reflect acknowledged hardware/session state.
- [ ] Task event timing can be correlated with measured sample timing.
- [ ] Results show real measurements; missing reconstruction shows an honest empty state.
- [ ] Demo data/mode is labeled and isolated.
- [ ] Sessions are preserved, browsable, and exportable with metadata.
- [ ] UI remains usable at desktop/tablet sizes and by keyboard.
- [ ] Errors are readable and do not imply unverified hardware safety.
- [ ] Critical logic has tests and the app can build/type-check.
- [ ] Folder organization makes ownership and edit locations obvious.
- [ ] No unnecessary cards, files, dependencies, animations, or abstractions remain.

---

## 12. Implementation Order

Progress for this project is tracked in `docs/architecture.md` §4, which uses its own numbering (0–12). Done there: 0 pilot analysis, 1 discovery (`docs/hardware-mapping.md`), 2 configuration and study-design contracts (`schemas/models.py`; device-capability, session/event and sample schemas are still open), 3 repository organisation. Step 3 below (UI skeleton) is architecture step 4; steps 4–8 below map to architecture steps 5–11.

1. **Discover/inspect:** inventory the repo, existing modules, driver methods, firmware capabilities, transport and measurement data representation.
2. **Document contracts:** minimal typed device capabilities, configuration, session/task/event and sample schemas; note any unresolved hardware dependencies.
3. **UI skeleton:** three tabs, global header, two-column Measurement layout, responsive theme; empty/disabled states rather than fake device claims.
4. **Device/config integration:** connection workflow, capability-driven form/validation, routing and amplitude/frequency setters where actually supported.
5. **Protocol/session logic:** backend-authoritative **multi-stage guided task runner**, configurable Ready/HOLD/Rest durations, manual gates, stage timestamps and start/stop/pause where valid.
6. **Real-time presentation:** implement the **large guided task screen FIRST**, stage-specific action text, huge Ready/HOLD/Rest countdown, next-step cue, Focus Mode if useful, stage event transport, timer synchronization and reconnect behavior.
7. **Results and persistence:** raw samples, task annotations, existing reconstruction if available, exports and session history.
8. **Tests/hardware verification:** automated tests against mocks; separately label hardware-only validations.
9. **Packaging:** smoke test early (window + COM ports + IIO context, §8.12); full installer when the app is usable.
10. **Simplification pass:** eliminate decorative UI, duplicate states, redundant wrappers, unnecessary abstractions and dependencies; update the change map and README.

Do not artificially block the entire interface on unavailable hardware: implement UI and explicitly labeled demo mode when useful, but clearly distinguish unimplemented/unsupported physical capabilities.

---

### Extra acceptance criteria for real-time stage pop-ups

- Verify all four stages (`PREPARE`, `GET READY`, `HOLD`, `RELEASE`) each show the **correct one-shot action pop-up** for the protocol-configured visibility time, then automatically dismiss to the persistent correct instruction and stage countdown.
- Verify that editing a pop-up to 2s, 5s, or 8s changes display behavior correctly; the saved protocol is the source of truth, not a frontend constant.
- Verify separate `overlay` versus `before_stage` lead-in semantics: no silent HOLD time loss, accurate anticipated command, persisted timestamps, valid pause/resume and back-to-back transitions.
- Check `Task 1 → Task 2` with a manual PREPARE gate: no task should start itself while waiting for user readiness.
- Check that configured stage durations, zero-duration optional phases, Pause/Resume, Stop, backend delays, and fast consecutive transitions do not show stale instruction pop-ups.
- Confirm remaining time is tied to backend stage timestamps and is not delayed by the animation duration.
- Confirm changing the animation does not modify the acquisition driver or protocol state machine.
- Confirm `prefers-reduced-motion`, keyboard controls and ARIA announcements work without auto-playing audio.
- Test Focus Mode at 1366×768 and 1440×900: cue is large, but measurement Stop controls remain unobscured.

## 13. Definition of Done for Each Coding Task

Before considering a feature complete:

1. Identify and modify the smallest appropriate set of files.
2. Confirm behavior for disconnected/idle/running/error where applicable.
3. Verify types, units, backend contracts, and measurement data provenance.
4. Add/update the smallest meaningful tests.
5. Run relevant checks; state explicitly if any could not run (especially hardware tests).
6. Keep design tokens and existing UI patterns consistent.
7. Update concise documentation only when architecture, wiring, or behavior actually changes.
8. In your final summary, list files changed and why, behavior implemented, how verified, and remaining hardware limitations.

**Final design rule:** Build software for **operating scientific equipment**, not for demonstrating frontend design techniques. Every visible element must have a functional purpose. Choose the simplest maintainable solution. **Do not overengineer.**
