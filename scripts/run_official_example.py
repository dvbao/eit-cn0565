"""Run official CN0565 examples with a selectable Windows COM port."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import time


WORKSPACE = Path(__file__).resolve().parents[1]
EXAMPLES = WORKSPACE / "examples" / "cn0565"


def execute_example(script_name: str, argv: list[str], uri: str, cwd: Path) -> None:
    script_path = EXAMPLES / script_name
    if not script_path.exists():
        raise SystemExit(
            "Official examples are missing. Run: "
            ".\\scripts\\setup_official_examples.ps1"
        )

    source = script_path.read_text(encoding="utf-8")
    source, replacements = re.subn(
        r"serial:COM\d+,\d+,8n1n?",
        uri,
        source,
    )
    if script_name != "main.py" and replacements == 0:
        raise SystemExit(f"Could not locate the serial URI in {script_path.name}")

    cwd.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(EXAMPLES))
    previous_argv = sys.argv
    previous_cwd = Path.cwd()
    try:
        sys.argv = [str(script_path), *argv]
        os.chdir(cwd)
        exec(compile(source, str(script_path), "exec"), {"__name__": "__main__", "__file__": str(script_path)})
    finally:
        sys.argv = previous_argv
        os.chdir(previous_cwd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("single", "sweep", "gui", "prodtest"))
    parser.add_argument("--port", default="COM7")
    parser.add_argument("--baud", type=int, default=230400)
    parser.add_argument("--electrodes", type=int, choices=(8, 16, 32), default=16)
    parser.add_argument(
        "--proxy",
        action="store_true",
        help="Use the local timing proxy required by the ADuCM3029 UART firmware",
    )
    parser.add_argument("--proxy-delay-ms", type=float, default=100.0)
    parser.add_argument("--proxy-tcp-port", type=int, default=30431)
    parser.add_argument(
        "--pair",
        type=int,
        nargs=4,
        metavar=("F_PLUS", "F_MINUS", "S_PLUS", "S_MINUS"),
        default=(0, 3, 1, 2),
        help="Electrode assignment for single mode",
    )
    args = parser.parse_args()

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

        if args.mode == "single":
            execute_example(
                "cn0565_example_single.py",
                [str(value) for value in args.pair],
                uri,
                WORKSPACE / "data" / "raw",
            )
        elif args.mode == "sweep":
            execute_example(
                "cn0565_example.py",
                [],
                uri,
                WORKSPACE / "data" / "raw",
            )
        elif args.mode == "prodtest":
            execute_example(
                "cn0565_prod_tst.py",
                [],
                uri,
                WORKSPACE / "data" / "raw",
            )
        else:
            execute_example(
                "main.py",
                [
                    "--port",
                    args.port,
                    "--baudrate",
                    str(args.baud),
                    "--el",
                    str(args.electrodes),
                    "--uri",
                    uri,
                    "--iio",
                ],
                uri,
                EXAMPLES,
            )
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
