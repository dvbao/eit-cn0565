from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("no-notes", "slides-a", "slides-b", "slide"),
        required=True,
    )
    parser.add_argument("--slide-number", type=int)
    args = parser.parse_args()

    with ZipFile(args.source) as z:
        source = {name: z.read(name) for name in z.namelist()}
    with ZipFile(args.candidate) as z:
        candidate = {name: z.read(name) for name in z.namelist()}
        infos = {info.filename: info for info in z.infolist()}

    if args.mode == "no-notes":
        candidate["[Content_Types].xml"] = source["[Content_Types].xml"]
        for number in range(10, 17):
            name = f"ppt/notesSlides/notesSlide{number}.xml"
            candidate[name] = source[name]
        for slide_number in (19, 20):
            name = f"ppt/slides/_rels/slide{slide_number}.xml.rels"
            candidate[name] = source[name]
        for number in (17, 18):
            candidate.pop(f"ppt/notesSlides/notesSlide{number}.xml", None)
            candidate.pop(f"ppt/notesSlides/_rels/notesSlide{number}.xml.rels", None)
    else:
        # Start from the known-good source and copy only the requested edited
        # slide parts. This supports binary isolation of any Open XML defect.
        edited = candidate
        candidate = dict(source)
        if args.mode == "slides-a":
            slide_numbers = range(12, 17)
            media = ("image8.png", "image9.png", "image11.png")
        elif args.mode == "slides-b":
            slide_numbers = range(17, 22)
            media = ("image12.png",)
        else:
            if args.slide_number is None:
                parser.error("--slide-number is required for --mode slide")
            slide_numbers = (args.slide_number,)
            media_by_slide = {
                14: ("image8.png",),
                15: ("image9.png",),
                16: ("image11.png",),
                18: ("image12.png",),
            }
            media = media_by_slide.get(args.slide_number, ())
        for number in slide_numbers:
            name = f"ppt/slides/slide{number}.xml"
            candidate[name] = edited[name]
        for filename in media:
            name = f"ppt/media/{filename}"
            candidate[name] = edited[name]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", compression=ZIP_DEFLATED) as z:
        for name, data in candidate.items():
            old = infos.get(name)
            if old is None:
                z.writestr(name, data)
                continue
            info = ZipInfo(name, date_time=old.date_time)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = old.external_attr
            z.writestr(info, data)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
