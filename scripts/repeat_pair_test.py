"""Repeat one 2-wire electrode-pair impedance reading N times, untouched.

Uses the same 2-wire wiring convention as cn0565_prod_tst.py: `--pos` is
routed to both F+ and S+, `--neg` to both S- and F-. Point this at whichever
pair looked borderline in prod_tst.py output to tell apart two things that
look identical from a single reading: genuine run-to-run instability
(contact/settling/noise) vs. a value that is simply stable but sits close to
the pass/fail threshold.

Example, for the Electrode 2 - Electrode 3 pair from cn0565_prod_tst.py:

    python scripts\\repeat_pair_test.py --port COM7 --pos 3 --neg 2 --count 10 --proxy
"""

from __future__ import annotations

import argparse
import statistics
import subprocess
import sys
import time
from pathlib import Path

import adi

WORKSPACE = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", default="COM7")
    parser.add_argument("--baud", type=int, default=230400)
    parser.add_argument("--pos", type=int, required=True, help="Electrode routed to F+ and S+")
    parser.add_argument("--neg", type=int, required=True, help="Electrode routed to S- and F-")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--freq", type=int, default=10000)
    parser.add_argument("--proxy", action="store_true", help="Route through the UART timing proxy")
    parser.add_argument("--proxy-tcp-port", type=int, default=30431)
    parser.add_argument("--proxy-delay-ms", type=float, default=100.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    proxy_process = None
    uri = f"serial:{args.port},{args.baud},8n1n"

    try:
        if args.proxy:
            uri = f"ip:127.0.0.1:{args.proxy_tcp_port}"
            proxy_process = subprocess.Popen(
                [
                    sys.executable,
                    str(WORKSPACE / "scripts" / "iiod_serial_proxy.py"),
                    "--port",
                    args.port,
                    "--baud",
                    str(args.baud),
                    "--tcp-port",
                    str(args.proxy_tcp_port),
                    "--delay-ms",
                    str(args.proxy_delay_ms),
                ],
                cwd=WORKSPACE,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            time.sleep(1.0)
            if proxy_process.poll() is not None:
                raise SystemExit("The local IIOD timing proxy could not be started")

        board = adi.cn0565(uri=uri)
        board.gpio1_toggle = True
        board.excitation_amplitude = 100
        board.excitation_frequency = args.freq
        board.magnitude_mode = False
        board.impedance_mode = True
        board.immediate = True
        board.add(0x71)
        board.add(0x70)

        board.open_all()
        board[args.pos][0] = True
        board[args.pos][1] = True
        board[args.neg][2] = True
        board[args.neg][3] = True

        reals: list[float] = []
        imags: list[float] = []
        for i in range(args.count):
            res = board.channel["voltage0"].raw
            reals.append(res.real)
            imags.append(res.imag)
            print(f"{i + 1:3d}: real={res.real:12.3f}  imag={res.imag:12.3f}  |Z|={abs(res):12.3f}")

        print()
        print(f"real: mean={statistics.mean(reals):.3f}  stdev={statistics.pstdev(reals):.3f}")
        print(f"imag: mean={statistics.mean(imags):.3f}  stdev={statistics.pstdev(imags):.3f}")
        mean_abs_imag = statistics.mean(abs(v) for v in imags)
        if mean_abs_imag:
            spread_pct = 100 * (max(imags) - min(imags)) / mean_abs_imag
            print(f"imag spread (max-min) as % of mean|imag|: {spread_pct:.1f}%")
    finally:
        if proxy_process is not None:
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proxy_process.kill()
                proxy_process.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
