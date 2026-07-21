"""Create company-identity-redacted copies of the approved evaluation PDFs.

This utility is deliberately specific to the ten reviewed drawings. It removes
underlying text, image pixels, and vector paths in narrowly mapped identity
regions; it does not paint a cosmetic overlay over intact source content.
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(frozen=True)
class Area:
    page: int
    rect: tuple[float, float, float, float]
    reason: str


@dataclass(frozen=True)
class Phrase:
    query: str
    pages: tuple[int, ...] | None = None


@dataclass(frozen=True)
class WordRule:
    page: int
    zone: tuple[float, float, float, float]
    words: frozenset[str]


@dataclass(frozen=True)
class DrawingSpec:
    company_identity: str
    areas: tuple[Area, ...] = ()
    phrases: tuple[Phrase, ...] = ()
    word_rules: tuple[WordRule, ...] = ()
    forbidden_extracted_text: tuple[str, ...] = ()
    graphics_mode: int = pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED
    max_legacy_vector_edge_pixels: int = 0


TITAN_LOGO = (891.7, 623.4, 1176.0, 734.9)
TITAN_QR = (256.0, 622.5, 358.4, 726.6)
TITAN_LEGAL_PHRASE = (Phrase("TITANS of CNC: Academy"),)


SPECS: dict[str, DrawingSpec] = {
    "Titan-129LM.pdf": DrawingSpec(
        company_identity="TITANS of CNC",
        areas=(
            Area(0, (483.0, 503.0, 625.0, 586.0), "company logo"),
            Area(0, (28.9, 527.1, 83.3, 581.5), "company QR code"),
            Area(0, (265.0, 535.0, 380.0, 585.0), "company legal-notice body"),
        ),
        forbidden_extracted_text=("titans of cnc",),
    ),
    "Titan-400-Subplate.pdf": DrawingSpec(
        company_identity="TITANS of CNC: Academy",
        areas=(
            Area(0, (887.7, 658.1, 1177.7, 732.5), "company logo"),
            Area(0, (54.9, 659.1, 127.2, 731.4), "company QR code"),
        ),
        phrases=TITAN_LEGAL_PHRASE,
        forbidden_extracted_text=("titans of cnc", "titans of cnc: academy"),
    ),
    "part_print_in_flat_titan_7m.pdf": DrawingSpec(
        company_identity="TITANS of CNC: Academy",
        areas=tuple(
            area
            for page in range(3)
            for area in (
                Area(page, TITAN_LOGO, "company logo"),
                Area(page, TITAN_QR, "company QR code"),
            )
        ),
        phrases=TITAN_LEGAL_PHRASE,
        forbidden_extracted_text=("titans of cnc", "titans of cnc: academy"),
    ),
    "part_print_in_round_Titan_84L.pdf": DrawingSpec(
        company_identity="TITANS of CNC: Academy",
        areas=(
            Area(0, TITAN_LOGO, "company logo"),
            Area(0, TITAN_QR, "company QR code"),
        ),
        phrases=TITAN_LEGAL_PHRASE,
        forbidden_extracted_text=("titans of cnc", "titans of cnc: academy"),
    ),
    "part_print_in_round_Titan_87L.pdf": DrawingSpec(
        company_identity="TITANS of CNC: Academy",
        areas=(
            Area(0, TITAN_LOGO, "company logo"),
            Area(0, TITAN_QR, "company QR code"),
        ),
        phrases=TITAN_LEGAL_PHRASE,
        forbidden_extracted_text=("titans of cnc", "titans of cnc: academy"),
    ),
    "part_print_in_round_Titan_90L.pdf": DrawingSpec(
        company_identity="TITANS of CNC: Academy",
        areas=(
            Area(0, TITAN_LOGO, "company logo"),
            Area(0, TITAN_QR, "company QR code"),
        ),
        phrases=TITAN_LEGAL_PHRASE,
        forbidden_extracted_text=("titans of cnc", "titans of cnc: academy"),
    ),
    "part_print_mm_round_3026166.pdf": DrawingSpec(
        company_identity="Cummins Inc.",
        areas=(
            Area(0, (2200.0, 1338.0, 2425.0, 1364.0), "company name in legal notice"),
            Area(0, (1960.0, 1369.0, 2290.0, 1410.0), "company name in title block"),
        ),
    ),
    "part_print_in_flat_2017GC2001_19.pdf": DrawingSpec(
        company_identity="Abrams Airborne Manufacturing, Inc.",
        areas=(
            Area(0, (937.5, 657.2, 1053.7, 685.5), "company logo"),
            Area(0, (1065.0, 650.0, 1180.0, 678.5), "company name in title block"),
        ),
        word_rules=(
            WordRule(
                0,
                (665.0, 665.0, 810.0, 706.0),
                frozenset({"ABRAMS", "AIRBORNE", "MFG", "MFG.", "INC", "INC."}),
            ),
        ),
        forbidden_extracted_text=("abrams airborne", "abrams mfg"),
    ),
    "part_print_in_round_200082_012.pdf": DrawingSpec(
        company_identity="Jus-Rite Engineering",
        areas=(
            Area(0, (466.5, 632.9, 692.8, 792.0), "company logo"),
        ),
        word_rules=(
            WordRule(
                0,
                (688.0, 693.0, 802.0, 739.0),
                frozenset({"JUS-RITE", "ENGINEERING", "ENGINEERING."}),
            ),
        ),
        forbidden_extracted_text=("jus-rite engineering",),
    ),
    "part_print_in_round_5D7304.pdf": DrawingSpec(
        company_identity="Globe Motors, Inc.",
        areas=tuple(
            area
            for page in range(2)
            for area in (
                Area(page, (918.0, 34.0, 985.0, 41.5), "company name in copyright line"),
                Area(page, (1047.0, 662.5, 1131.0, 670.5), "company name in title block"),
            )
        ),
        graphics_mode=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
        max_legacy_vector_edge_pixels=250,
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_word(word: str) -> str:
    return word.strip().upper()


def _intersects(a: pymupdf.Rect, b: pymupdf.Rect) -> bool:
    return not (a & b).is_empty


def _collect_areas(document: pymupdf.Document, spec: DrawingSpec) -> list[Area]:
    areas = list(spec.areas)

    for phrase in spec.phrases:
        page_numbers = (
            phrase.pages
            if phrase.pages is not None
            else tuple(range(document.page_count))
        )
        for page_number in page_numbers:
            for rect in document[page_number].search_for(phrase.query):
                areas.append(Area(page_number, tuple(rect), f"company phrase: {phrase.query}"))

    for rule in spec.word_rules:
        zone = pymupdf.Rect(rule.zone)
        for word in document[rule.page].get_text("words"):
            rect = pymupdf.Rect(word[:4])
            if _intersects(rect, zone) and _normalize_word(word[4]) in rule.words:
                areas.append(Area(rule.page, tuple(rect), f"company word: {word[4]}"))

    return areas


def _render_diff_is_confined(
    source: pymupdf.Document,
    output: pymupdf.Document,
    areas: list[Area],
    max_legacy_vector_edge_pixels: int,
) -> tuple[bool, list[str]]:
    scale = 1.25
    matrix = pymupdf.Matrix(scale, scale)
    messages: list[str] = []

    def has_nearby_dark_pixel(
        samples: memoryview,
        x: int,
        y: int,
        width: int,
        height: int,
        channels: int,
    ) -> bool:
        for near_y in range(max(0, y - 1), min(height, y + 2)):
            for near_x in range(max(0, x - 1), min(width, x + 2)):
                start = (near_y * width + near_x) * channels
                if min(samples[start : start + min(3, channels)]) < 128:
                    return True
        return False

    for page_number in range(source.page_count):
        before = source[page_number].get_pixmap(matrix=matrix, alpha=False)
        after = output[page_number].get_pixmap(matrix=matrix, alpha=False)
        if (before.width, before.height, before.n) != (after.width, after.height, after.n):
            messages.append(f"page {page_number + 1}: rendered dimensions changed")
            continue

        allowed = [
            pymupdf.Rect(area.rect) * matrix
            for area in areas
            if area.page == page_number
        ]
        changed = 0
        outside = 0
        first_outside: tuple[int, int] | None = None
        before_samples = memoryview(before.samples)
        after_samples = memoryview(after.samples)
        channels = before.n

        for pixel in range(before.width * before.height):
            start = pixel * channels
            if all(
                abs(before_samples[start + channel] - after_samples[start + channel]) <= 32
                for channel in range(channels)
            ):
                continue
            changed += 1
            x = pixel % before.width
            y = pixel // before.width
            # PDF text clipping can remove a complete glyph whose side bearing
            # extends a few points beyond the search rectangle.
            inside_mapped_area = any(
                rect.x0 - 48 <= x <= rect.x1 + 48 and rect.y0 - 48 <= y <= rect.y1 + 48
                for rect in allowed
            )
            if inside_mapped_area:
                continue

            # Rewriting old rotated vector PDFs can move antialiased edge
            # pixels by one pixel without changing visible content. Count only
            # changes where one rendering no longer has the same nearby line.
            before_has_line = has_nearby_dark_pixel(
                before_samples, x, y, before.width, before.height, channels
            )
            after_has_line = has_nearby_dark_pixel(
                after_samples, x, y, after.width, after.height, channels
            )
            if before_has_line != after_has_line:
                outside += 1
                first_outside = first_outside or (x, y)

        if changed == 0:
            messages.append(f"page {page_number + 1}: no visible pixels changed")
        elif outside > max_legacy_vector_edge_pixels:
            messages.append(
                f"page {page_number + 1}: {outside} changed pixels outside mapped areas; "
                f"first at {first_outside}"
            )
        else:
            noise_note = (
                f"; {outside} legacy vector edge pixels within tolerance"
                if outside
                else ""
            )
            messages.append(
                f"page {page_number + 1}: {changed} changed pixels, all confined to mapped areas"
                f"{noise_note}"
            )

    ok = all("all confined" in message for message in messages)
    return ok, messages


def redact_one(source_path: Path, output_path: Path, spec: DrawingSpec) -> list[str]:
    source_hash = _sha256(source_path)
    source = pymupdf.open(source_path)
    original_page_rects = [tuple(page.rect) for page in source]
    areas = _collect_areas(source, spec)

    if not areas:
        raise RuntimeError(f"No redaction areas found for {source_path.name}")

    for area in areas:
        page = source[area.page]
        rect = pymupdf.Rect(area.rect)
        if page.rotation:
            rect = rect * page.derotation_matrix
        page.add_redact_annot(
            rect,
            fill=(1, 1, 1),
            cross_out=False,
        )

    for page in source:
        page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_PIXELS,
            graphics=spec.graphics_mode,
            text=pymupdf.PDF_REDACT_TEXT_REMOVE,
        )

    metadata = source.metadata
    metadata["author"] = ""
    metadata["keywords"] = ""
    metadata["subject"] = ""
    source.set_metadata(metadata)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    source.save(
        output_path,
        garbage=4,
        clean=False,
        deflate=True,
        encryption=pymupdf.PDF_ENCRYPT_NONE,
    )
    source.close()

    if _sha256(source_path) != source_hash:
        raise RuntimeError(f"Source file changed while processing: {source_path}")

    original = pymupdf.open(source_path)
    redacted = pymupdf.open(output_path)
    if redacted.page_count != original.page_count:
        raise RuntimeError(f"Page count changed for {source_path.name}")
    if [tuple(page.rect) for page in redacted] != original_page_rects:
        raise RuntimeError(f"Page dimensions changed for {source_path.name}")

    extracted_text = "\n".join(page.get_text() for page in redacted).casefold()
    remaining = [term for term in spec.forbidden_extracted_text if term in extracted_text]
    if remaining:
        raise RuntimeError(f"Company text remained in {source_path.name}: {remaining}")

    confined, diff_messages = _render_diff_is_confined(
        original,
        redacted,
        areas,
        spec.max_legacy_vector_edge_pixels,
    )
    original.close()
    redacted.close()
    if not confined:
        raise RuntimeError(
            f"Visual changes escaped mapped areas in {source_path.name}: "
            f"{diff_messages}"
        )

    return [
        f"{source_path.name}: removed {spec.company_identity}",
        f"  pages/dimensions preserved; {len(areas)} underlying-content redaction areas",
        *(f"  {message}" for message in diff_messages),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("part-prints"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("part-prints/redacted-eval"),
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Redact one exact PDF filename. Repeat for a controlled subset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for filename, spec in SPECS.items():
        if args.only and filename not in args.only:
            continue
        source_path = args.input_dir / filename
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        for message in redact_one(source_path, args.output_dir / filename, spec):
            print(message)


if __name__ == "__main__":
    main()
