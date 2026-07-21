"""Deterministic text and rendering evidence for digital engineering PDFs."""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass

import pymupdf

from backend.domain.models import (
    AnalysisResponse,
    DimensionCandidate,
    DimensionFieldResult,
    DimensionSource,
    FieldStatus,
    Units,
)

NUMBER_PATTERN = re.compile(
    r"(?<![\w.])(?:(?:(\d+)\s+)?(\d+)/(\d+)|([-+]?(?:\d+(?:\.\d*)?|\.\d+)))"
)


class PdfEvidenceError(ValueError):
    """The supplied bytes cannot provide a usable digital-PDF witness."""


@dataclass(frozen=True)
class PdfToken:
    raw_text: str
    normalized_text: str
    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True)
class PdfPageEvidence:
    page_number: int
    width: float
    height: float
    text: str
    tokens: tuple[PdfToken, ...]


@dataclass(frozen=True)
class PdfEvidence:
    pages: tuple[PdfPageEvidence, ...]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def text(self) -> str:
        return "\n".join(page.text for page in self.pages)

    @property
    def tokens(self) -> tuple[PdfToken, ...]:
        return tuple(token for page in self.pages for token in page.tokens)


def normalize_text(value: str) -> str:
    """Normalize for comparison without replacing the preserved raw token."""

    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("⌀", "Ø").replace("∅", "Ø")
    return re.sub(r"\s+", " ", normalized).strip().upper()


def _compact_text(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", normalize_text(value))


def extract_pdf_evidence(pdf_bytes: bytes) -> PdfEvidence:
    """Extract raw words, normalized words, pages, and PDF coordinates."""

    try:
        document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:  # PyMuPDF exposes several parse exception types.
        raise PdfEvidenceError("The uploaded file is not a readable PDF.") from exc
    try:
        if document.page_count < 1:
            raise PdfEvidenceError("The uploaded PDF has no pages.")
        pages: list[PdfPageEvidence] = []
        for page_index, page in enumerate(document):
            tokens = tuple(
                PdfToken(
                    raw_text=str(word[4]),
                    normalized_text=normalize_text(str(word[4])),
                    page_number=page_index + 1,
                    x0=float(word[0]),
                    y0=float(word[1]),
                    x1=float(word[2]),
                    y1=float(word[3]),
                )
                for word in page.get_text("words", sort=True)
            )
            pages.append(
                PdfPageEvidence(
                    page_number=page_index + 1,
                    width=float(page.rect.width),
                    height=float(page.rect.height),
                    text=page.get_text("text", sort=True),
                    tokens=tokens,
                )
            )
        return PdfEvidence(pages=tuple(pages))
    finally:
        document.close()


def find_text(evidence: PdfEvidence, query: str) -> list[int]:
    """Return page numbers containing a normalized exact phrase."""

    compact_query = _compact_text(query)
    if not compact_query:
        return []
    return [
        page.page_number
        for page in evidence.pages
        if compact_query in _compact_text(page.text)
    ]


def _material_identity_is_supported(
    response: AnalysisResponse, evidence: PdfEvidence
) -> bool:
    """Accept equivalent wording while requiring the resolved grade facts."""

    material = response.material
    for phrase in (material.raw_callout, material.resolved_identity):
        if phrase and find_text(evidence, phrase):
            return True
    if not material.canonical_grade:
        return False
    grades = [item.strip() for item in material.canonical_grade.split("/") if item.strip()]
    if not grades or not all(find_text(evidence, grade) for grade in grades):
        return False
    return not material.temper_or_condition or bool(
        find_text(evidence, material.temper_or_condition)
    )


def numeric_values(text: str) -> list[float]:
    """Extract decimals, simple fractions, and mixed fractions from PDF text."""

    values: list[float] = []
    for match in NUMBER_PATTERN.finditer(text.replace(",", "")):
        whole, numerator, denominator, decimal = match.groups()
        if numerator is not None and denominator is not None:
            divisor = int(denominator)
            if divisor:
                values.append((int(whole) if whole else 0) + int(numerator) / divisor)
            continue
        assert decimal is not None
        values.append(float(decimal))
    return values


def contains_numeric(evidence: PdfEvidence, expected: float) -> bool:
    return any(
        math.isclose(value, expected, rel_tol=1e-7, abs_tol=1e-7)
        for value in numeric_values(evidence.text)
    )


def render_pdf_page(pdf_bytes: bytes, page_index: int, *, dpi: int = 200) -> bytes:
    """Render one full page to PNG bytes for preview or targeted inspection."""

    return render_pdf_region(pdf_bytes, page_index, region=None, dpi=dpi)


def render_pdf_region(
    pdf_bytes: bytes,
    page_index: int,
    *,
    region: tuple[float, float, float, float] | None,
    dpi: int = 200,
) -> bytes:
    """Render an optional PDF-coordinate crop while retaining full-page support."""

    if dpi < 72:
        raise ValueError("Render DPI must be at least 72.")
    try:
        document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise PdfEvidenceError("The uploaded file is not a readable PDF.") from exc
    try:
        if page_index < 0 or page_index >= document.page_count:
            raise IndexError("PDF page index is out of range.")
        page = document[page_index]
        clip = pymupdf.Rect(region) if region is not None else None
        if clip is not None and (clip.is_empty or clip.is_infinite):
            raise ValueError("Render region must have a positive finite area.")
        pixmap = page.get_pixmap(dpi=dpi, alpha=False, clip=clip)
        return pixmap.tobytes("png")
    finally:
        document.close()


def _candidate_values(candidate: DimensionCandidate) -> list[float]:
    if candidate.source is DimensionSource.CHAINED_DIMENSIONS:
        return [term.value for term in candidate.chain_terms]
    return [candidate.value] if candidate.value is not None else []


def _downgrade_missing_dimension_tokens(
    result: DimensionFieldResult,
    *,
    axis: str,
    evidence: PdfEvidence,
    validation: list[str],
) -> None:
    if result.status is not FieldStatus.RESOLVED:
        return
    accepted_candidates = [
        candidate
        for candidate in result.candidates
        if candidate.value == result.value and candidate.units == result.units
    ]
    missing = sorted(
        {
            value
            for candidate in accepted_candidates
            for value in _candidate_values(candidate)
            if not contains_numeric(evidence, value)
        }
    )
    if not missing:
        return
    result.status = FieldStatus.NEEDS_REVIEW
    result.value = None
    result.units = None
    result.source = None
    result.dimension_path = None
    detail = f"PDF text does not contain claimed {axis} value(s): {missing}."
    result.reasons.append(detail)
    validation.append(detail)


def _explicit_primary_units(evidence: PdfEvidence) -> Units | None:
    text = normalize_text(evidence.text)
    found: set[Units] = set()
    if re.search(r"\bDIMENSIONS\s+(?:ARE\s+)?IN\s+(?:INCHES|INCH)\b", text):
        found.add(Units.IN)
    if re.search(
        r"\bDIMENSIONS\s+(?:ARE\s+)?IN\s+(?:MILLIMETERS|MILLIMETRES|MM)\b",
        text,
    ):
        found.add(Units.MM)
    return next(iter(found)) if len(found) == 1 else None


def _apply_explicit_primary_units(
    response: AnalysisResponse, evidence: PdfEvidence
) -> None:
    primary_units = _explicit_primary_units(evidence)
    if primary_units is None:
        return

    response.units.status = FieldStatus.RESOLVED
    response.units.value = primary_units.value
    response.units.reasons = []
    for result in (
        response.dimensions.diameter,
        response.dimensions.thickness,
        response.dimensions.width,
        response.dimensions.length,
    ):
        if result.status is not FieldStatus.RESOLVED or result.units is primary_units:
            continue
        matching = next(
            (
                candidate
                for candidate in result.candidates
                if candidate.units is primary_units
                and candidate.value is not None
                and candidate.source is not DimensionSource.NOT_FOUND
            ),
            None,
        )
        if matching is None:
            result.status = FieldStatus.NEEDS_REVIEW
            result.value = None
            result.units = None
            result.source = None
            result.dimension_path = None
            result.reasons.append(
                "No reader supplied this dimension in the drawing's explicit primary units."
            )
            continue
        result.value = matching.value
        result.units = matching.units
        result.source = matching.source
        result.dimension_path = matching.dimension_path
    response.validation_summary.append(
        f"PDF text explicitly identifies {primary_units.value} as the primary units."
    )


def validate_response_against_pdf(
    response: AnalysisResponse, evidence: PdfEvidence
) -> None:
    """Downgrade unsupported claims; never replace them with expected values."""

    response.validation_summary.append(
        f"Digital PDF witness: {evidence.page_count} page(s), "
        f"{len(evidence.tokens)} text token(s)."
    )
    if not evidence.tokens or not evidence.text.strip():
        response.validation_summary.append(
            "The PDF has no searchable text layer; visual reader evidence was preserved "
            "instead of being rejected by text-only validation."
        )
        return
    _apply_explicit_primary_units(response, evidence)
    if (
        response.part_number.status is FieldStatus.RESOLVED
        and response.part_number.value
        and not find_text(evidence, response.part_number.value)
    ):
        response.part_number.status = FieldStatus.NEEDS_REVIEW
        response.part_number.reasons.append(
            "Accepted part number was not found in the PDF text layer."
        )
        response.part_number.value = None
    if response.material.status is FieldStatus.RESOLVED and not _material_identity_is_supported(
        response, evidence
    ):
        response.material.status = FieldStatus.NEEDS_REVIEW
        response.material.ambiguities.append(
            "The resolved material grade was not found in the PDF text layer."
        )
        response.material.allowance_class = None
        response.material.resolved_identity = None
        response.material.supplier_description = None
    for axis in ("diameter", "thickness", "width", "length"):
        _downgrade_missing_dimension_tokens(
            getattr(response.dimensions, axis),
            axis=axis,
            evidence=evidence,
            validation=response.validation_summary,
        )
