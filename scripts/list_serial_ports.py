"""List serial ports so the ADICUP3029 IIO port can be identified."""

from serial.tools import list_ports


def main() -> int:
    ports = sorted(list_ports.comports(), key=lambda port: port.device)
    if not ports:
        print("No serial ports found. Flash the CN0565 IIO firmware, then reconnect the board.")
        return 1

    for port in ports:
        print(f"{port.device:8} {port.description}")
        if port.hwid:
            print(f"         {port.hwid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
