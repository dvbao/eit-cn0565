from __future__ import annotations

import argparse
from pathlib import Path

from pptx import Presentation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    presentation = Presentation(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(args.output)
    print(f"Normalized {args.input} -> {args.output}")


if __name__ == "__main__":
    main()
