#!/usr/bin/env python
"""Extract text, speaker notes, tables and figures from a .pptx deck.

Outputs into the target directory:
  slides.md      human/LLM readable dump, one section per slide
  slides.json    structured equivalent (used by later steps)
  figures.csv    figure inventory (slide, file, width, height, alt, decorative)
  images/        de-duplicated figures; repeated decoration goes to images/_decor/

Usage:
  python extract_pptx.py lecture03.pptx -o out/lecture03
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
except ImportError:  # pragma: no cover
    sys.exit("python-pptx is required: pip install python-pptx")


def alt_text(shape) -> str:
    try:
        els = shape._element.xpath(".//p:cNvPr")
    except Exception:
        return ""
    for el in els:
        descr = (el.get("descr") or "").strip()
        # PowerPoint stores the bare file name when no alt text was written
        if descr and not re.match(r"^[\w\-. ]+\.(png|jpe?g|gif|bmp|emf|wmf|tiff?)$", descr, re.I):
            return descr
    return ""


def iter_shapes(shapes):
    for shape in shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from iter_shapes(shape.shapes)
        else:
            yield shape


def pos_key(shape):
    top = shape.top if shape.top is not None else 1 << 30
    left = shape.left if shape.left is not None else 1 << 30
    return (top, left)


def clean_line(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text.replace("\r", " "))
    return text.strip()


def shape_paragraphs(shape) -> list[str]:
    if not getattr(shape, "has_text_frame", False):
        return []
    out = []
    for para in shape.text_frame.paragraphs:
        line = clean_line("".join(run.text for run in para.runs) or para.text)
        if not line:
            continue
        indent = "  " * max(0, (para.level or 0))
        out.append(indent + line)
    return out


def table_rows(shape) -> list[list[str]] | None:
    if not getattr(shape, "has_table", False):
        return None
    rows = []
    for row in shape.table.rows:
        rows.append([clean_line(cell.text) for cell in row.cells])
    return rows


def slide_title(slide, shapes) -> str:
    try:
        if slide.shapes.title is not None:
            title = clean_line(slide.shapes.title.text)
            if title:
                return title
    except Exception:
        pass
    # no title placeholder: use the first short text line near the top of the slide
    for shape in shapes:
        for line in shape_paragraphs(shape):
            if line.strip() and len(line.strip()) <= 120:
                return line.strip()
    return ""


def notes_text(slide) -> str:
    try:
        if not slide.has_notes_slide:
            return ""
        text = slide.notes_slide.notes_text_frame.text
    except Exception:
        return ""
    return "\n".join(clean_line(l) for l in text.splitlines() if clean_line(l))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx", type=Path)
    ap.add_argument("-o", "--outdir", type=Path, required=True)
    ap.add_argument("--min-px", type=int, default=200, help="drop figures smaller than this in both dimensions")
    ap.add_argument("--min-bytes", type=int, default=12000, help="drop image blobs smaller than this")
    ap.add_argument("--no-notes", action="store_true")
    ap.add_argument("--keep-decor", action="store_true", help="keep repeated template art in the body")
    args = ap.parse_args()

    if not args.pptx.exists():
        sys.exit(f"not found: {args.pptx}")

    prs = Presentation(str(args.pptx))
    outdir: Path = args.outdir
    imgdir = outdir / "images"
    imgdir.mkdir(parents=True, exist_ok=True)

    slides = []
    figures = []  # flat inventory rows
    seen: dict[str, str] = {}  # sha1 -> relative file
    occurrences: dict[str, int] = {}

    for idx, slide in enumerate(prs.slides, start=1):
        shapes = sorted(iter_shapes(slide.shapes), key=pos_key)
        text, tables, figs = [], [], []

        for shape in shapes:
            text.extend(shape_paragraphs(shape))
            rows = table_rows(shape)
            if rows:
                tables.append(rows)

            image = getattr(shape, "image", None)
            if image is None:
                continue
            try:
                px_w, px_h = image.size
                blob = image.blob
            except Exception:
                continue
            if px_w < args.min_px and px_h < args.min_px:
                continue
            if len(blob) < args.min_bytes:
                continue

            digest = hashlib.sha1(blob).hexdigest()
            occurrences[digest] = occurrences.get(digest, 0) + 1
            if digest in seen:
                rel = seen[digest]
            else:
                ext = (image.ext or "png").lower().lstrip(".")
                name = f"slide{idx:02d}_{digest[:8]}.{ext}"
                (imgdir / name).write_bytes(blob)
                rel = f"images/{name}"
                seen[digest] = rel

            figs.append(
                {
                    "file": rel,
                    "width": int(px_w),
                    "height": int(px_h),
                    "bytes": len(blob),
                    "alt": alt_text(shape),
                    "sha1": digest,
                }
            )

        slides.append(
            {
                "index": idx,
                "title": slide_title(slide, shapes),
                "text": text,
                "tables": tables,
                "notes": "" if args.no_notes else notes_text(slide),
                "figures": figs,
            }
        )

    # figures repeated on most slides are template decoration, not content
    n = max(1, len(slides))
    threshold = max(3, int(n * 0.5))
    decor: set[str] = set()
    if not args.keep_decor:
        decor = {d for d, c in occurrences.items() if c >= threshold}
        if decor:
            deco_dir = imgdir / "_decor"
            deco_dir.mkdir(exist_ok=True)
            for digest in decor:
                src = outdir / seen[digest]
                if src.exists():
                    src.replace(deco_dir / src.name)
                    seen[digest] = f"images/_decor/{src.name}"

    lines = [
        f"# {args.pptx.stem}",
        "",
        f"> source: `{args.pptx.name}` | slides: {len(slides)} | "
        f"figures kept: {sum(1 for s in slides for f in s['figures'] if f['sha1'] not in decor)} | "
        f"decorative: {len(decor)} | extracted: {date.today().isoformat()}",
        "",
    ]

    for slide in slides:
        title = slide["title"] or "(untitled)"
        lines.append(f"## Slide {slide['index']} — {title}")
        lines.append("")
        if slide["text"]:
            lines.append("### Text")
            lines.extend(f"- {t}" for t in slide["text"])
            lines.append("")
        for table in slide["tables"]:
            lines.append("### Table")
            for i, row in enumerate(table):
                lines.append("| " + " | ".join(row) + " |")
                if i == 0:
                    lines.append("|" + "---|" * len(row))
            lines.append("")
        if slide["notes"]:
            lines.append("### Notes")
            lines.extend(f"> {l}" for l in slide["notes"].splitlines())
            lines.append("")
        live = [f for f in slide["figures"] if f["sha1"] not in decor]
        if live:
            lines.append("### Figures")
            for fig in live:
                alt = f' — alt: "{fig["alt"]}"' if fig["alt"] else ""
                lines.append(f"- `{fig['file']}` ({fig['width']}x{fig['height']}{alt})")
            lines.append("")

    (outdir / "slides.md").write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "source": str(args.pptx),
        "extracted_at": date.today().isoformat(),
        "slide_count": len(slides),
        "decorative_hashes": sorted(decor),
        "slides": [
            {
                **{k: v for k, v in s.items() if k != "figures"},
                "figures": [
                    {**{k: v for k, v in f.items() if k != "sha1"},
                     "decorative": f["sha1"] in decor}
                    for f in s["figures"]
                ],
            }
            for s in slides
        ],
    }
    (outdir / "slides.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with (outdir / "figures.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["slide", "file", "width_px", "height_px", "bytes", "alt", "decorative"])
        for slide in slides:
            for fig in slide["figures"]:
                writer.writerow(
                    [slide["index"], fig["file"], fig["width"], fig["height"],
                     fig["bytes"], fig["alt"], "yes" if fig["sha1"] in decor else "no"]
                )

    kept = sum(1 for s in slides for f in s["figures"] if f["sha1"] not in decor)
    print(f"slides: {len(slides)}  figures: {kept}  decorative: {len(decor)}")
    print(f"wrote: {outdir / 'slides.md'}")
    print(f"wrote: {outdir / 'slides.json'}")
    print(f"wrote: {outdir / 'figures.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())