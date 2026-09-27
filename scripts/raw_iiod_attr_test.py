"""Test a CN0565 TinyIIOD attribute without libiio or PyADI-IIO.

This isolates the target firmware/UART protocol from the Windows libiio and
libserialport DLLs.  Run this only when no terminal, GUI, or other process has
COM7 open.
"""

from __future__ import annotations

import argparse
import sys
import time

import serial


# TinyIIOD addresses devices by the XML device ID, not the display name.
# The CN0565 firmware exposes ad5940 as iio:device0.
DEVICE = "iio:device0"
ATTRIBUTE = "excitation_frequency"


def receive_line(port: serial.Serial, label: str) -> bytes:
    line = port.readline()
    print(f"RX {label}: {line!r}")
    if not line:
        raise TimeoutError(f"No response while waiting for {label}")
    return line


def read_version(port: serial.Serial) -> bytes:
    command = b"VERSION\r\n"
    print(f"TX VERSION: {command!r}")
    port.write(command)
    port.flush()
    return receive_line(port, "VERSION")


def read_attribute(port: serial.Serial) -> bytes:
    command = f"READ {DEVICE} {ATTRIBUTE}\r\n".encode("ascii")
    print(f"TX READ header: {command!r}")
    port.write(command)
    port.flush()

    length_line = receive_line(port, "READ length")
    try:
        length = int(length_line.strip())
    except ValueError as exc:
        raise RuntimeError(f"Invalid READ length: {length_line!r}") from exc
    if length < 0:
        raise RuntimeError(f"Target returned READ error {length}")

    value = port.read(length)
    print(f"RX READ value ({length} byte(s)): {value!r}")
    if len(value) != length:
        raise TimeoutError(
            f"READ value timed out: expected {length} byte(s), got {len(value)}"
        )

    terminator = port.read(1)
    print(f"RX READ terminator: {terminator!r}")
    if terminator != b"\n":
        raise RuntimeError(f"Expected newline after READ value, got {terminator!r}")
    return value


def write_attribute(
    port: serial.Serial, mode: str, delay_ms: float, value: bytes
) -> int:
    header = (
        f"WRITE {DEVICE} {ATTRIBUTE} {len(value)}\r\n".encode("ascii")
    )
    print(f"TX WRITE header: {header!r}")
    print(f"TX WRITE value:  {value!r}")

    if mode == "combined":
        # One OS write helps reveal a header/payload packet-boundary problem.
        port.write(header + value)
        port.flush()
    else:
        # This more closely resembles clients that transmit header and data
        # through separate write calls.
        port.write(header)
        port.flush()
        if delay_ms:
            print(f"Waiting {delay_ms:g} ms before WRITE value")
            time.sleep(delay_ms / 1000.0)
        port.write(value)
        port.flush()

    response = receive_line(port, "WRITE result")
    try:
        result = int(response.strip())
    except ValueError as exc:
        raise RuntimeError(f"Invalid WRITE result: {response!r}") from exc
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Raw TinyIIOD READ/WRITE diagnostic for CN0565"
    )
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM7")
    parser.add_argument("--baud", type=int, default=230400)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument(
        "--mode",
        choices=("combined", "split"),
        default="combined",
        help="Send WRITE header and value in one call or two calls",
    )
    parser.add_argument(
        "--delay-ms",
        type=float,
        default=0.0,
        help="Delay between WRITE header and value in split mode",
    )
    parser.add_argument(
        "--value",
        type=int,
        default=12000,
        help="Excitation frequency to write and verify (default: 12000)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(
        f"Opening {args.port} at {args.baud}, 8N1, no flow control "
        f"(timeout {args.timeout:g}s)"
    )

    try:
        with serial.Serial(
            port=args.port,
            baudrate=args.baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=args.timeout,
            write_timeout=args.timeout,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        ) as port:
            time.sleep(0.2)
            port.reset_input_buffer()
            version = read_version(port)
            print(f"TinyIIOD version: {version.decode('ascii', errors='replace').strip()}")
            current = read_attribute(port)
            print(f"Current {ATTRIBUTE}: {current.decode('ascii', errors='replace')}")

            value = str(args.value).encode("ascii")
            result = write_attribute(port, args.mode, args.delay_ms, value)
            # no-OS attribute store callbacks return 0 on success. Some IIOD
            # implementations instead return the number of consumed bytes.
            if result not in (0, len(value)):
                print(
                    f"FAILED: target returned {result}; expected 0 or {len(value)}."
                )
                return 3

            updated = read_attribute(port)
            if updated != value:
                print(f"FAILED: read-back is {updated!r}; expected {value!r}.")
                return 4

            print(
                f"OK: raw TinyIIOD READ and {args.mode} WRITE both succeeded "
                f"(WRITE returned {result}); read-back is {updated!r}."
            )
            return 0
    except serial.SerialException as exc:
        print(f"SERIAL ERROR: {exc}")
        return 2
    except (TimeoutError, RuntimeError) as exc:
        print(f"FAILED: {exc}")
        print(
            "No valid TinyIIOD response was received. Close every program using "
            "the COM port, press S1, wait for the IIOD server to start, and retry."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
