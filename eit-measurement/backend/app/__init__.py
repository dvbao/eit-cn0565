"""EIT Measurement Studio backend (rules: eit-measurement/AGENTS.md).

    app.eit        scientific analysis: sequences, QC, relative change, features, reconstruction, report
    app.schemas    data contracts: measurement configuration, wiring, study design
    app.services   protocol runner (session schedule); acquisition and session manager come later
    app.hardware   CN0565 adapter and demo adapter (not built yet)

Command line: ``python -m app --help`` (see eit-measurement/README.md and docs/pipeline.md).
"""
