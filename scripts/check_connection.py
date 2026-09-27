"""Confirm that the CN0565 IIO firmware answers over the selected COM port."""

from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="Windows serial port, for example COM5")
    parser.add_argument("--baud", type=int, default=230400, help="CN0565 IIO baud rate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    uri = f"serial:{args.port},{args.baud},8n1n"
    print(f"Connecting to {uri} ...")

    try:
        import iio
    except ImportError:
        print("The libIIO Python binding is missing. Run: pip install -r requirements.txt")
        return 2

    try:
        context = iio.Context(uri)
    except Exception as error:  # libIIO error types vary across releases
        print(f"FAILED: Could not open an IIO context on {args.port}: {error}")
        print("Check that the CN0565 IIO .hex is flashed and that this is the board's COM port.")
        return 3

    print(f"OK: IIO context is open ({context.name or 'unnamed'}).")
    devices = list(context.devices)
    if not devices:
        print("FAILED: The serial connection opened but returned no IIO devices.")
        return 4

    print("Devices:")
    for device in devices:
        print(f"  - {device.name or '<unnamed>'} (id: {device.id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
