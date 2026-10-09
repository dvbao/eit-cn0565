# CLAUDE.md — read this first (loaded automatically by Claude Code)

Facial EIT research with the Analog Devices CN0565 board, and the desktop app **EIT Measurement Studio** that is
being built step by step with the user.

## How to work with this user

- Explain in **Vietnamese** with English technical terms. All text in figures/plots is **English**; app UI text is English.
- The user gets overwhelmed by long dumps and scattered files. Work **one step at a time**; after each step give a
  short table "đã đổi gì" (file, new/changed, why) and the single next step; keep the folder structure clean.
- After every step update `eit-measurement/docs/architecture.md` (§4 progress table, §6 change log).
- Ask before committing/pushing, large restructures or deleting files. Never fake hardware results.

## Where things are

- `eit-measurement/` — **the application** (desktop app + backend + data + docs). Rules: `eit-measurement/AGENTS.md`
  (read §0 "Current state", §2 "EIT acquisition semantics", §3 stack, §8 folder tree before coding).
- Big picture, pipeline, build plan and progress: `eit-measurement/docs/architecture.md`.
- Verified hardware facts (transport, attributes, wiring, timing): `eit-measurement/docs/hardware-mapping.md`.
- Data collection / analysis procedure: `eit-measurement/docs/pipeline.md`.
- **Latest handoff (what happened, decisions, open items, next step):** `docs/handoffs/2026-10-09-eit-measurement-studio.md`.
- Research notes and reports: `docs/` (index `docs/README.md`); references: `reference/`; slides: `presentations/`;
  superseded material: `archive/`.
- Windows hardware toolkit stays at the repository root (the Windows PC uses these paths): `scripts/`, `examples/`,
  `work/`, `bootstrap-cn0565-env.ps1`, `requirements.txt`, `cn0565-env/`.

## Setup on a new machine (once)

macOS / Linux, from the repository root:

```bash
python3 -m venv .venv-sim
.venv-sim/bin/python -m pip install -r eit-measurement/requirements.txt
printf "%s\n%s\n" "$PWD/eit-measurement/backend" "$PWD/eit-measurement" \
  > "$(.venv-sim/bin/python -c 'import site; print(site.getsitepackages()[0])')/eit_studio_backend.pth"
```

Windows (PowerShell, Python 3.11), from the repository root:

```powershell
py -3.11 -m venv .venv-sim
.venv-sim\Scripts\python.exe -m pip install -r eit-measurement\requirements.txt
"$PWD\eit-measurement\backend`n$PWD\eit-measurement" | Set-Content .venv-sim\Lib\site-packages\eit_studio_backend.pth
```

## Commands (repository root; on Windows use `.venv-sim\Scripts\python.exe`)

```bash
.venv-sim/bin/python -m frontend                                                  # open the desktop app
.venv-sim/bin/python -m app design --design data/protocols/facial-rest-task-rest-v1.json \
    --measurement data/hardware/measurement-16el-50kHz.json                       # session schedule
.venv-sim/bin/python -m app check data/sessions/<session>                         # QC one session
.venv-sim/bin/python -m app study data/studies/three-frequency-20261005.json      # full analysis
.venv-sim/bin/python -m unittest discover -s eit-measurement/backend/tests -p "test_*.py"    # 43 tests
.venv-sim/bin/python -m unittest discover -s eit-measurement/frontend/tests -p "test_*.py"   # 5 tests (offscreen)
.venv-sim/bin/python -m unittest discover -s scripts -p "test_*.py"                          # 8 legacy tests
```

`data/...` paths are resolved inside `eit-measurement/` whichever folder the command runs from.

## Current status (2026-10-09)

- Done (architecture.md §4): 0 pilot analysis · 1 hardware discovery · 2 configurable measurement settings + study
  design · 3 repository organisation · 4 PySide6 window shell (`python -m frontend`).
- **Next: step 5 — configuration panel** (choose/edit measurement settings in the app; backend validates; frames
  and session length update live).
- Teaching walkthrough "frontend → backend → pyadi-iio → libiio → firmware → chips": step 1 explained (Python
  property → IIOD WRITE/READ commands, 9 commands per measurement); **step 2 pending** (how the IIOD text travels
  through the TCP proxy and serial port, the firmware reply, and why the proxy waits 10 ms).
