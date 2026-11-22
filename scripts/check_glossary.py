#!/usr/bin/env python
"""Validate a glossary built from a .pptx extraction.

Checks structure, duplicate terms, bilingual completeness, whether every term is
actually grounded in slides.md, whether figure references resolve, and optionally
compares Chinese renderings against a bilingual reference TSV (e.g. MeSpEn).

Exit code 0 = pass, 1 = at least one error.

Usage:
  python check_glossary.py --glossary glossary.csv --slides slides.md
  python check_glossary.py --glossary glossary.csv --slides slides.md --mespen refs.tsv
  python check_glossary.py ... --strict
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REQUIRED = [
    "term_en", "term_zh", "definition_en", "definition_zh",
    "slide", "figure", "cross_check", "confidence",
]
CONFIDENCE = {"high", "medium", "low"}


def norm(text: str) -> str:
    text = text.lower().replace("–", "-").replace("—", "-")
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def variants(term: str) -> set[str]:
    base = norm(term)
    out = {base}
    if base.endswith("s"):
        out.add(base[:-1])
    else:
        out.add(base + "s")
    if " " in base:
        out.add(base.replace(" ", ""))
    return {v for v in out if v}


def read_slides(path: Path) -> tuple[str, dict[int, str]]:
    if not path.exists():
        sys.exit(f"slides.md not found: {path}")
    text = path.read_text(encoding="utf-8")
    chunks = re.split(r"^## Slide (\d+)\s*—.*$", text, flags=re.M)
    whole = norm(text)
    per_slide: dict[int, str] = {}
    # chunks: [preamble, "1", body1, "2", body2, ...]
    for i in range(1, len(chunks) - 1, 2):
        per_slide[int(chunks[i])] = norm(chunks[i + 1])
    return whole, per_slide


def read_mespen(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        print(f"warn: cannot decode {path}, skipping reference check")
        return mapping

    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        en, zh = parts[0].strip(), parts[1].strip()
        if not en or not zh or en.lower() in {"en", "english", "term", "source"}:
            continue
        key = norm(en)
        mapping.setdefault(key, zh)
    return mapping


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glossary", type=Path, required=True)
    ap.add_argument("--slides", type=Path, required=True)
    ap.add_argument("--mespen", type=Path)
    ap.add_argument("--allow-new-terms", action="store_true",
                    help="downgrade ungrounded terms to warnings (for supplement-only entries)")
    ap.add_argument("--strict", action="store_true",
                    help="treat slide mismatch, high-confidence Unverified and coverage gaps as errors")
    args = ap.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    if not args.glossary.exists():
        sys.exit(f"glossary not found: {args.glossary}")

    with args.glossary.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        headers = reader.fieldnames or []

    missing = [c for c in REQUIRED if c not in headers]
    if missing:
        print("ERROR missing columns: " + ", ".join(missing))
        return 1

    whole, per_slide = read_slides(args.slides)
    mespen = read_mespen(args.mespen) if args.mespen else {}

    seen: dict[str, int] = {}
    covered: set[int] = set()
    base = args.glossary.parent
    deck_root = args.slides.parent

    for lineno, row in enumerate(rows, start=2):
        term = (row.get("term_en") or "").strip()
        zh = (row.get("term_zh") or "").strip()
        conf = (row.get("confidence") or "").strip().lower()
        check = (row.get("cross_check") or "").strip()
        slide_raw = (row.get("slide") or "").strip()
        figure = (row.get("figure") or "").strip()

        if not term or not zh:
            errors.append(f"L{lineno}: empty term_en or term_zh")
            continue

        key = norm(term)
        if key in seen:
            errors.append(f"L{lineno}: duplicate of L{seen[key]} -> {term}")
        else:
            seen[key] = lineno

        if not (row.get("definition_en") or "").strip():
            errors.append(f"L{lineno}: {term}: missing definition_en")
        if not (row.get("definition_zh") or "").strip():
            errors.append(f"L{lineno}: {term}: missing definition_zh")

        if norm(zh) == key:
            warnings.append(f"L{lineno}: {term}: term_zh equals term_en (untranslated?)")

        if conf and conf not in CONFIDENCE:
            errors.append(f"L{lineno}: {term}: confidence must be high/medium/low, got '{conf}'")
        if conf == "high" and check.lower().startswith("unverified"):
            msg = f"L{lineno}: {term}: confidence=high but cross_check=Unverified"
            (errors if args.strict else warnings).append(msg)

        hits = [v for v in variants(term) if f" {v} " in f" {whole} "]
        if not hits:
            msg = f"L{lineno}: {term}: not found in slides.md (hallucinated or paraphrase?)"
            if args.allow_new_terms:
                warnings.append(msg)
            else:
                errors.append(msg)
            continue

        try:
            slide_no = int(re.sub(r"\D", "", slide_raw) or 0)
        except ValueError:
            slide_no = 0
        if slide_no <= 0:
            warnings.append(f"L{lineno}: {term}: missing slide number")
        else:
            body = per_slide.get(slide_no, "")
            if not any(f" {v} " in f" {body} " for v in variants(term)):
                all_hits = [n for n, txt in per_slide.items()
                            if any(f" {v} " in f" {txt} " for v in variants(term))]
                where = f" (found on slide {', '.join(map(str, all_hits))})" if all_hits else ""
                msg = f"L{lineno}: {term}: declared slide {slide_no} does not contain it{where}"
                (errors if args.strict else warnings).append(msg)
            covered.add(slide_no)

        if figure:
            candidates = [base / figure, deck_root / figure]
            if not any(p.exists() for p in candidates):
                errors.append(f"L{lineno}: {term}: figure not found -> {figure}")

        if mespen:
            ref = mespen.get(key)
            if ref and norm(ref) != norm(zh):
                warnings.append(f"L{lineno}: {term}: term_zh '{zh}' != reference '{ref}'")

    total_slides = max(per_slide) if per_slide else 0
    # title / agenda / reference slides have no glossary traffic; don't gate on them
    def is_boilerplate(body: str) -> bool:
        words = body.split()
        if len(words) < 25:
            return True
        head = " ".join(words[:6])
        return bool(re.search(r"\b(title|agenda|outline|contents|thank|references|summary)\b", head))

    empty = [n for n in range(1, total_slides + 1)
             if n not in covered and not is_boilerplate(per_slide.get(n, ""))]
    if empty:
        msg = f"slides with no glossary term: {', '.join(map(str, empty))}"
        (errors if args.strict else warnings).append(msg)

    for msg in errors:
        print("ERROR " + msg)
    for msg in warnings:
        print("WARN  " + msg)

    print()
    print(f"terms: {len(rows)}  slides: {total_slides}  "
          f"covered: {total_slides - len(empty)}  errors: {len(errors)}  warnings: {len(warnings)}")
    print("PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
