# CN0565 EIT workspace

This folder keeps the EIT experiment reproducible: firmware, connection checks, raw captures, processed results, and notes are separate.

## Current connection path

`EVAL-CN0565-ARDZ` → `EVAL-ADICUP3029` → USB → Windows

The DAPLINK drive confirms the programmer/debug interface is connected. It does **not** confirm that the CN0565 IIO firmware is running or that the host can communicate with it.

For a valid host connection, the CN0565 firmware must be flashed to the DAPLINK drive. After the automatic DAPLINK reconnect, Windows should expose a serial COM port. The test uses that port at **230400 baud, 8N1**.

## First-time environment setup

1. Place the CN0565 `.hex` firmware in `firmware/`.
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

## Contents

- `firmware/` — supplied or built `.hex` images; do not mix different builds.
- `scripts/` — repeatable host-side checks and acquisition scripts.
- `data/raw/` — untouched acquisition outputs.
- `data/processed/` — derived tables, images, and reconstructions.
- `logs/` — console captures and fault notes.
- `docs/` — setup notes and experimental record.
- `cn0565-env/` — local Python 3.11 virtual environment (created locally; ignored by Git).

## Reference commands

The official production test script uses a URI of the form:

```python
adi.cn0565(uri="serial:COM5,230400,8n1n")
```

The number after `COM` is machine-specific. Keep the port as a command-line option; do not hard-code it into measurement code.
