"""Command line: python -m app {check,study,design,hash} ...

  check  <session_dir>        QC one raw session right after acquisition
  study  <config.json>        full reproducible analysis of a study (QC, features, images, figures, manifest)
  design --design D.json --measurement M.json   operator sheet of a study design (validated
         against the hardware configuration), or the shortcut  design --tasks ... --seed N
  hash   <session_dir>        SHA-256 of every raw file (provenance)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="QC one raw session")
    p.add_argument("session_dir")
    p.add_argument("--out", default=None)
    p.add_argument("--strong-counts", type=float, default=50.0)
    p.add_argument("--rest-label", default="REST")

    p = sub.add_parser("study", help="analyse a study described by a JSON config")
    p.add_argument("config")
    p.add_argument("--quick", action="store_true", help="fewer permutations/noise draws (for testing)")

    p = sub.add_parser("design", help="randomised operator sheet for a rest-task-rest session")
    p.add_argument("--design", default=None, help="study design JSON (data/protocols/*.json)")
    p.add_argument("--measurement", default=None,
                   help="measurement configuration JSON (data/hardware/measurement-*.json): sets the frame duration")
    p.add_argument("--tasks", nargs="+", default=None, help="shortcut without --design")
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--seed", type=int, default=None, help="required with --tasks; overrides the design's seed")
    p.add_argument("--controls-per-round", type=int, default=1)
    p.add_argument("--initial-rest-frames", type=int, default=3)
    p.add_argument("--frames-per-task", type=int, default=1)
    p.add_argument("--frame-s", type=float, default=20.6, help="frame duration when no --measurement is given")
    p.add_argument("--settle-s", type=float, default=2.0, help="cue-to-frame settle time for the time estimate")
    p.add_argument("--out", default=None, help="output prefix (writes .csv and .md)")

    p = sub.add_parser("hash", help="SHA-256 of a raw session folder")
    p.add_argument("session_dir")

    args = ap.parse_args(argv)
    from .eit.config import resolve, resolve_out

    if args.cmd == "check":
        from .eit.report import check_session

        res = check_session(args.session_dir, args.out, args.strong_counts, args.rest_label)
        s = res["summary"]
        keys = ["audit_pass", "status_complete", "frames_complete", "csv_matches_meta_sequence", "settings_constant",
                "n_frames", "n_rest_frames", "measurement_mode", "trial_windows", "frames_inside_hold",
                "rest_abs_median_counts", f"rest_n_ge_{args.strong_counts:g}", "recip_err_strong_median_pct",
                "recip_err_after_drive_gain_fit_pct", "drive_gain_fit_supported", "drive_gain_min",
                "drive_gain_min_pair", "settle_task_s_median", "rest_rest_pairs", "rest_rest_rms_counts",
                "rest_rest_inphase_rms_counts", "rest_across_task_pairs", "invalid_trials_excluded"]
        for k in keys:
            if k in s:
                print(f"{k:32s} {s[k]}")
        print(f"\nwritten to {res['out']}")
        return 0 if s["audit_pass"] else 1

    if args.cmd == "study":
        from .eit.config import load_config
        from .eit.report import run_study

        out = run_study(load_config(args.config), quick=args.quick)
        print((out / "README.md").read_text())
        print(f"written to {out}")
        return 0

    if args.cmd == "design":
        from .schemas.models import (CONTROL, StageTiming, StudyDesign, TaskSpec, load_design, load_measurement,
                                     load_wiring)
        from .services.protocol_runner import design_markdown, expand, validate

        if args.design:
            shortcut = {"--tasks": args.tasks, "--rounds": args.rounds != 2, "--controls-per-round": args.controls_per_round != 1,
                        "--initial-rest-frames": args.initial_rest_frames != 3, "--frames-per-task": args.frames_per_task != 1,
                        "--settle-s": args.settle_s != 2.0}
            used = [flag for flag, on in shortcut.items() if on]
            if used:
                ap.error(f"{', '.join(used)} only apply to the --tasks shortcut; edit the design file instead")
            design = load_design(resolve(args.design))
            if args.seed is not None:
                design.seed = args.seed
        elif args.tasks and args.seed is not None:
            design = StudyDesign(name="command-line", tasks=args.tasks, rounds=args.rounds, seed=args.seed,
                                 controls_per_round=args.controls_per_round,
                                 control=TaskSpec(CONTROL) if args.controls_per_round else None,
                                 initial_rest_frames=args.initial_rest_frames, frames_per_task=args.frames_per_task,
                                 timing=StageTiming(settle_s=args.settle_s))
        else:
            ap.error("design needs --design FILE, or --tasks ... with --seed N")
        frame_s = args.frame_s
        problems = []
        if args.measurement:
            mc = load_measurement(resolve(args.measurement))
            frame_s = mc.frame_s
            print(f"{mc.n_electrodes} electrodes, {mc.n_measurements} measurements per frame, "
                  f"{frame_s:.1f} s per frame")
            try:
                wiring = load_wiring(mc.wiring_file()) if mc.wiring else None
            except (OSError, ValueError, KeyError) as exc:
                wiring = None
                problems.append(f"wiring file {mc.wiring!r} cannot be read: {exc}")
            problems += mc.validate(wiring)
        else:
            print(f"no --measurement given: assuming {frame_s:.1f} s per frame (16 electrodes, pilot timing)")
        problems += validate(design, frame_s)
        if problems:
            print("design is not valid for this configuration:\n- " + "\n- ".join(problems), file=sys.stderr)
            return 1
        df = expand(design, frame_s)
        md = design_markdown(df, design.seed)
        if args.out:
            prefix = resolve_out(args.out)
            prefix.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(prefix.with_suffix(".csv"), index=False)
            prefix.with_suffix(".md").write_text(md)
            print(f"written {prefix.with_suffix('.csv')} and {prefix.with_suffix('.md')}")
        print(md)
        return 0

    if args.cmd == "hash":
        from .eit.io import sha256_tree

        print(json.dumps(sha256_tree(resolve(args.session_dir)), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
