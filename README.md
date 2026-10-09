# eit-cn0565: facial EIT research workspace

Facial EIT research with the Analog Devices CN0565 board. The repository has two parts:

1. **`eit-measurement/` — the application** (everything you build, run and control): frontend, backend,
   communication, hardware adapter, analysis, configuration and data. Start with
   **[eit-measurement/README.md](eit-measurement/README.md)**.
2. **Everything around it** — research notes, references, slides and the Windows hardware toolkit.

```
eit-cn0565/
├── eit-measurement/     THE APPLICATION (see eit-measurement/README.md)
│   ├── AGENTS.md          project rules for people and coding agents
│   ├── frontend/          desktop interface (Python + PySide6): python -m frontend
│   ├── backend/           analysis (app/eit), configuration (app/schemas), session planning (app/services);
│   │                      hardware adapter + live session (not built yet)
│   ├── data/              hardware/, protocols/, studies/, sessions/, results/, bench/
│   └── docs/              architecture.md (big picture + progress), pipeline.md, hardware-mapping.md
├── docs/                research notes, reports, Windows connection guides
├── reference/           datasheets, circuit note, board design files, firmware, papers, diagrams
├── presentations/       slide decks and the template
├── archive/             superseded scripts, outputs and scratch (kept, not used)
└── Windows hardware toolkit (kept at the root because the Windows PC uses these paths):
    bootstrap-cn0565-env.ps1, requirements.txt, cn0565-env/, scripts/, examples/, work/
```

Main commands (from this folder, after the one-time setup in
[eit-measurement/README.md](eit-measurement/README.md)):

```bash
.venv-sim/bin/python -m frontend                                    # open the app
.venv-sim/bin/python -m app design --design data/protocols/facial-rest-task-rest-v1.json \
    --measurement data/hardware/measurement-16el-50kHz.json      # session schedule, validated
.venv-sim/bin/python -m app check data/sessions/<session>           # QC right after a session
.venv-sim/bin/python -m app study data/studies/three-frequency-20261005.json   # full analysis
```

Background reading: [docs/README.md](docs/README.md) (index), [EIT noise sources](docs/eit-noise-sources.md),
[facial environment and forward models](docs/facial-environment-and-forward-models.md).

## Current connection path

`EVAL-CN0565-ARDZ` → `EVAL-ADICUP3029` → USB → Windows

The DAPLINK drive confirms the programmer/debug interface is connected. It does **not** confirm that the CN0565 IIO firmware is running or that the host can communicate with it.

For a valid host connection, the CN0565 firmware must be flashed to the DAPLINK drive. After the automatic DAPLINK reconnect, Windows should expose a serial COM port. The test uses that port at **230400 baud, 8N1**.

## First-time environment setup

1. Place the CN0565 `.hex` firmware in `reference/firmware/`.
2. Copy it to the DAPLINK drive. A brief disconnect/reconnect is expected after a successful flash.
3. With Python 3.11 installed, create the source-matched environment:

   ```powershell
   .\bootstrap-cn0565-env.ps1
   ```

   The environment is created at `cn0565-env/`. This script checks for Python 3.11, installs the `pyadi-iio` `main` branch directly from its GitHub archive, and installs both the repository and CN0565 example requirements. A local Git installation is not required.

4. Identify the board's COM port:

   ```powershell
   python scripts\list_serial_ports.py
   ```

5. Test the IIO context (replace `COM5`):

   ```powershell
   python scripts\check_connection.py --port COM5
   ```

An OK result lists the IIO context and its devices. Only after this test passes should measurement or reconstruction work begin.

For the normal startup sequence after rebooting Windows, reset behavior, and timeout recovery, see `docs/connection-checklist.md`.

## Simulation only on macOS/Linux

The checked-in `cn0565-env/` is a Windows environment: its interpreter is
`cn0565-env/Scripts/python.exe`. It cannot run on macOS/Linux. For the
hardware-free reconstruction sandbox, create a native environment instead:

```bash
python3 -m venv .venv-sim
source .venv-sim/bin/activate
python -m pip install -r requirements-sim.txt   # or eit-measurement/backend/requirements.txt (pinned superset; same .venv-sim as in eit-measurement/README.md)
python scripts/eit_sim_playground.py --preset null
python scripts/eit_sim_playground.py --noise-rel 0.001 --seed 1
```

After the first setup, either activate it again or call its interpreter
directly:

```bash
.venv-sim/bin/python scripts/eit_sim_playground.py
```

## Reference commands

The official production test script uses a URI of the form:

```python
adi.cn0565(uri="serial:COM5,230400,8n1n")
```

The number after `COM` is machine-specific. Keep the port as a command-line option; do not hard-code it into measurement code.
