"""Bridge libiio TCP traffic to a TinyIIOD serial device.

The ADuCM3029 UART implementation can lose an attribute WRITE payload when it
arrives immediately after the command header.  This proxy preserves the IIOD
protocol while inserting a small delay before serial payload writes.
"""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import time

import serial


def read_exact(stream, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise EOFError(f"connection closed with {remaining} payload byte(s) missing")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def payload_size(command: bytes) -> int | None:
    stripped = command.rstrip(b"\r\n")
    if not (stripped.startswith(b"WRITE ") or stripped.startswith(b"WRITEBUF ")):
        return None
    try:
        return int(stripped.rsplit(b" ", 1)[1])
    except (IndexError, ValueError):
        return None


def serial_to_socket(
    port: serial.Serial, connection: socket.socket, stop: threading.Event
) -> None:
    try:
        while not stop.is_set():
            data = port.read(4096)
            if data:
                connection.sendall(data)
    except (AttributeError, OSError, serial.SerialException):
        pass
    finally:
        stop.set()


def serve_client(
    connection: socket.socket,
    address: tuple[str, int],
    serial_port: str,
    baud: int,
    delay_ms: float,
) -> None:
    print(f"Client connected: {address[0]}:{address[1]}", flush=True)
    stop = threading.Event()

    try:
        with serial.Serial(
            port=serial_port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.05,
            write_timeout=5,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        ) as port:
            time.sleep(0.2)
            port.reset_input_buffer()
            response_thread = threading.Thread(
                target=serial_to_socket,
                args=(port, connection, stop),
                daemon=True,
            )
            response_thread.start()

            stream = connection.makefile("rb", buffering=0)
            while not stop.is_set():
                command = stream.readline(4096)
                if not command:
                    break
                if len(command) >= 4096 and not command.endswith(b"\n"):
                    raise RuntimeError("IIOD command header is too long")

                printable = command.rstrip(b"\r\n").decode("ascii", errors="replace")
                print(f"TCP -> serial: {printable}", flush=True)

                # The libiio IP backend sends connection-management commands
                # that this CN0565 TinyIIOD UART build does not implement.
                # Handle them locally so they do not fail or stop the target.
                stripped = command.lstrip(b"\r\n")
                if stripped.startswith(b"TIMEOUT "):
                    print("Proxy response: TIMEOUT accepted", flush=True)
                    connection.sendall(b"0\n")
                    continue
                if stripped.startswith(b"EXIT"):
                    print("Proxy response: EXIT accepted (target kept running)", flush=True)
                    connection.sendall(b"0\n")
                    continue

                port.write(command)
                port.flush()

                size = payload_size(command)
                if size is not None and size > 0:
                    if delay_ms:
                        time.sleep(delay_ms / 1000.0)
                    data = read_exact(stream, size)
                    print(
                        f"TCP -> serial: {len(data)} payload byte(s) "
                        f"after {delay_ms:g} ms",
                        flush=True,
                    )
                    port.write(data)
                    port.flush()
            stop.set()
            response_thread.join(timeout=1.0)
    except (EOFError, OSError, RuntimeError, serial.SerialException) as exc:
        print(f"Client session ended: {exc}", flush=True)
    finally:
        stop.set()
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        connection.close()
        print("Client disconnected", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IIOD TCP-to-serial timing proxy")
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM7")
    parser.add_argument("--baud", type=int, default=230400)
    parser.add_argument("--listen", default="127.0.0.1")
    parser.add_argument("--tcp-port", type=int, default=30431)
    parser.add_argument("--delay-ms", type=float, default=100.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((args.listen, args.tcp_port))
        server.listen(1)
        print(
            f"Listening on ip:{args.listen}:{args.tcp_port} -> "
            f"serial:{args.port},{args.baud},8n1n; WRITE delay={args.delay_ms:g} ms",
            flush=True,
        )
        print("Press Ctrl+C to stop.", flush=True)
        try:
            while True:
                connection, address = server.accept()
                serve_client(
                    connection,
                    address,
                    args.port,
                    args.baud,
                    args.delay_ms,
                )
        except KeyboardInterrupt:
            print("Stopping proxy.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
