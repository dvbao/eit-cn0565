# scripts/

| Script | Use | Status |
|---|---|---|
| `list_serial_ports.py`, `check_connection.py`, `startup_check.ps1`, `capture_boot.py`, `iiod_serial_proxy.py`, `raw_iiod_attr_test.py`, `repeat_pair_test.py` | Hardware connection and board checks (Windows); see `docs/connection-checklist.md` | current |
| `run_official_example.py`, `setup_official_examples.ps1` | Run the ADI CN0565 example GUI/scripts | current |
| `eit_sim_playground.py` | Simulation sandbox for BP / JAC / GREIT (same settings as the analysis pipeline) | current |
| `cn0565_capture.py`, `cn0565_prepare_difference.py`, `cn0565_plot_difference.py` | Earlier raw collector and difference plots (`PREFIX.voltages.csv` format) | legacy; superseded by the pilot acquisition software + `app.eit` |

Acquisition of pilot sessions uses `cn0565_pilot.py` on the Windows PC (not yet in this repository; see
`eit-measurement/docs/pipeline.md`). Analysis uses the `app.eit` package: `.venv-sim/bin/python -m app --help`.
