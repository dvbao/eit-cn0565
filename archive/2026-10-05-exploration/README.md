# Archive: exploratory analysis of 2026-10-05 (superseded)

Kept for reference only. Nothing here is used by the current pipeline, and nothing was deleted.

| Path | What it was | Replaced by |
|---|---|---|
| `scripts/analysis/three_frequency_report.py` | First cross-frequency analysis (tables T1–T8, figures F1–F11, noise-weighted JAC) | `app.eit` (`python -m app study eit-measurement/data/studies/three-frequency-20261005.json`) |
| `scripts/analysis/algorithm_comparison.py` | BP / JAC / GREIT comparison (F12–F14, T9) | `app.eit.recon` + `app.eit.plots` |
| `scripts/analysis/slide_figures.py` | Slide-sized figures S1–S5 | `eit-measurement/data/results/<study>/slides/` |
| `scripts/analysis/clean_reconstruction_images.py` | Label-free images and grids | `eit-measurement/data/results/<study>/clean/` |
| `scripts/analysis/english_pilot_review.py`, `tests/test_english_pilot_review.py` | Parallel English review from another session (63 images incl. REST) | `app.eit`; report kept in `docs/reports/2026-10-05-three-frequency-analysis-english.md` |
| `data/processed/pilot/three-frequency-20261005/` | Outputs of the scripts above | `eit-measurement/data/results/three-frequency-20261005/` |
| `data/processed/pilot/english-review-20261005/` | Outputs of the English review (still linked from that report) | — |
| `data/processed/pilot/session-*/` | Per-session tables of the first script | `eit-measurement/data/results/three-frequency-20261005/tables/` |

The pipeline reproduces the key numbers of the first analysis to 1e-9 (QC, task features, lateralisation,
cross-session correlations, additivity, electrode involvement, recognition and reconstruction metrics). These
expected values were saved in `eit-measurement/backend/tests/fixtures/three_frequency_20261005_expected.json` before archiving, and
`eit-measurement/backend/tests/test_regression.py` checks them. Other numbers were not frozen in the fixture.

The archived scripts look for the raw sessions relative to their own location. To run one again, copy it back to
`scripts/analysis/`. The sessions now live in `eit-measurement/data/sessions/`, where the old `resolve_session()` also looks.
