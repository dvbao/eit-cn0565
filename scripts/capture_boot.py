"""Capture raw UART output while the ADICUP3029 is reset manually."""

from __future__ import annotations

import argparse
import time

import serial


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="Windows COM port, for example COM7")
    parser.add_argument("--baud", type=int, required=True, help="Baud rate to monitor")
    parser.add_argument("--seconds", type=float, default=15, help="Capture duration")
    args = parser.parse_args()

    print(f"Opening {args.port} at {args.baud} baud.")
    print("Press the physical 3029_RESET/S1 button now...")

    received = bytearray()
    with serial.Serial(
        port=args.port,
        baudrate=args.baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.2,
    ) as connection:
        connection.reset_input_buffer()
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            chunk = connection.read(connection.in_waiting or 1)
            if chunk:
                received.extend(chunk)
                print(chunk.decode("utf-8", errors="backslashreplace"), end="", flush=True)

    if not received:
        print("\nNO DATA: no UART bytes were received after reset.")
        return 1

    print(f"\nRECEIVED: {len(received)} byte(s).")
    print(f"RAW: {bytes(received)!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
