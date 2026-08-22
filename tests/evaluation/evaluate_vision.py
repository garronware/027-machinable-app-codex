"""Opt-in paid Sol/Terra evaluation against the live print index."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from backend.clients.openai_vision import OpenAISpecializedReaderClient
from backend.core.config import settings
from backend.domain.models import (
    Shape,
    SpecializedReaderBatch,
    TitleBlockInterpretation,
)
from backend.domain.pdf_evidence import extract_pdf_evidence
from backend.domain.pipeline import build_analysis_response
from tests.evaluation.print_index import (
    PART_PRINTS_DIR,
    TruthCase,
    compare_interpretation,
    load_truth_cases,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        help="Run cases whose filename or part number contains this text.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help=(
            "Run one exact filename or part number. Repeat for a controlled set; "
            "the normal limit is ignored."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help=(
            "Maximum parts (default: 3; two paid calls per part plus conditional "
            "dimension recovery). Ignored with --all."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Intentionally run every populated, non-excluded index case.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional historical JSON report path; no file is written by default.",
    )
    parser.add_argument(
        "--prints-dir",
        type=Path,
        default=PART_PRINTS_DIR,
        help=(
            "Directory containing the PDF copies to send. Dimensional truth still "
            "comes only from part-prints/print-index.md."
        ),
    )
    return parser


def compare_title_block(
    case: TruthCase,
    interpretation: TitleBlockInterpretation,
) -> dict:
    """Record Terra's focused material result without inventing material truth."""

    return {
        "expected_material": case.material,
        "actual_material_callout_raw": interpretation.material_callout_raw,
        "actual_material_name": interpretation.material_name,
        "material_callout_evidence": interpretation.material_callout_evidence,
        "warnings": interpretation.warnings,
    }


def build_reader_reports(
    case: TruthCase,
    batch: SpecializedReaderBatch,
    *,
    title_model: str,
    geometry_model: str,
) -> list[dict]:
    """Keep the two specialized duties distinct in one historical report."""

    reports: list[dict] = []
    if batch.title is not None:
        reports.append(
            {
                "task": "TITLE_MATERIAL",
                "model": batch.title.reader_model,
                "error": None,
                "interpretation": batch.title.interpretation.model_dump(mode="json"),
                "comparison": compare_title_block(case, batch.title.interpretation),
            }
        )
    if batch.geometry is not None:
        reports.append(
            {
                "task": "SHAPE_GEOMETRY",
                "model": batch.geometry.reader_model,
                "error": None,
                "recovered_axes": [axis.value for axis in batch.geometry.recovered_axes],
                "interpretation": batch.geometry.interpretation.model_dump(mode="json"),
                "comparison": compare_interpretation(
                    case,
                    batch.geometry.interpretation,
                ),
            }
        )
    for failure in batch.failures:
        task = (
            "TITLE_MATERIAL"
            if failure.reader_model == title_model
            else "SHAPE_GEOMETRY"
            if failure.reader_model == geometry_model
            else "UNKNOWN"
        )
        reports.append(
            {
                "task": task,
                "model": failure.reader_model,
                "error": failure.error,
                "interpretation": None,
                "comparison": None,
            }
        )
    return reports


async def run(args: argparse.Namespace) -> int:
    if not settings.openai_api_key:
        print("OPENAI_API_KEY is missing; no paid calls were made.", file=sys.stderr)
        return 2

    cases = load_truth_cases()
    if args.case:
        selected = []
        missing = []
        for requested in args.case:
            matches = [
                case
                for case in cases
                if requested == case.filename or requested == case.part_number
            ]
            if not matches:
                missing.append(requested)
            selected.extend(matches)
        if missing:
            print(
                "No complete dimensional truth case for: " + ", ".join(missing),
                file=sys.stderr,
            )
            return 2
        cases = list(dict.fromkeys(selected))
    elif args.only:
        needle = args.only.lower()
        cases = [
            case
            for case in cases
            if needle in case.filename.lower() or needle in case.part_number.lower()
        ]
    if not args.all and not args.case:
        cases = cases[: max(args.limit, 0)]

    client = OpenAISpecializedReaderClient(
        api_key=settings.openai_api_key,
        sol_model=settings.openai_sol_model,
        terra_model=settings.openai_terra_model,
        reasoning_effort=settings.openai_reasoning_effort,
    )
    reports: list[dict] = []
    paid_model_calls_attempted = 0
    for case in cases:
        path = args.prints_dir / case.filename
        print(f"evaluate {case.filename}")
        try:
            pdf_bytes = path.read_bytes()
            paid_model_calls_attempted += 3
            batch = await client.interpret_pdf(pdf_bytes, case.filename)
            paid_model_calls_attempted += max(batch.model_calls_attempted - 3, 0)
            analysis = build_analysis_response(
                batch,
                extract_pdf_evidence(pdf_bytes),
            )
            reader_reports = build_reader_reports(
                case,
                batch,
                title_model=client.title_reader.model,
                geometry_model=client.bounds_reader.model,
            )
            reports.append(
                {
                    "file": case.filename,
                    "part_number": case.part_number,
                    "expected_shape": case.shape.value,
                    "error": None,
                    "readers": reader_reports,
                    "analysis": analysis.model_dump(mode="json"),
                }
            )
        except Exception as exc:  # continue to preserve evidence from other cases
            reports.append(
                {
                    "file": case.filename,
                    "part_number": case.part_number,
                    "expected_shape": case.shape.value,
                    "error": f"{type(exc).__name__}: {exc}",
                    "readers": [],
                    "analysis": None,
                }
            )
            print(f"error    {case.filename}: {exc}", file=sys.stderr)

    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    shape_results: dict[str, Counter[str]] = defaultdict(Counter)
    presentations: Counter[str] = Counter()
    material_statuses: Counter[str] = Counter()
    dimension_statuses: Counter[str] = Counter()
    recommendations = 0
    reader_errors = 0
    for report in reports:
        if report["error"]:
            continue
        print(f"\n{report['file']}")
        for reader in report["readers"]:
            if reader["error"]:
                reader_errors += 1
                print(f"  {reader['model']} {reader['task']}: ERROR {reader['error']}")
                continue
            comparison = reader["comparison"]
            if reader["task"] == "TITLE_MATERIAL":
                print(f"  {reader['model']} material: {comparison['actual_material_name']!r}")
                continue
            shape_results[reader["model"]][
                "MATCH" if comparison["shape_match"] else "MISMATCH"
            ] += 1
            print(
                f"  {reader['model']} shape: {comparison['actual_shape']} "
                f"(expected {comparison['expected_shape']})"
            )
            for dimension in comparison["dimensions"]:
                bucket = dimension["bucket"]
                buckets[reader["model"]][bucket] += 1
                print(
                    f"    {dimension['axis']}: returned {dimension['actual']!r}, "
                    f"expected {dimension['expected']!r} [{bucket}]"
                )
                if dimension["dimension_path"]:
                    print(f"      path: {dimension['dimension_path']}")
                if dimension["evidence"]:
                    print(f"      evidence: {dimension['evidence']}")

        analysis = report["analysis"]
        presentations[analysis["presentation_status"]] += 1
        material_statuses[analysis["material"]["status"]] += 1
        recommendations += int(analysis["recommendation"] is not None)
        required_axes = (
            ("diameter", "length")
            if report["expected_shape"] == Shape.ROUND.value
            else ("thickness", "width", "length")
        )
        for axis in required_axes:
            dimension_statuses[analysis["dimensions"][axis]["status"]] += 1
        print(
            "  combined: "
            f"{analysis['presentation_status']}; "
            f"recommendation={'yes' if analysis['recommendation'] else 'no'}"
        )

    payload = {
        "historical_report": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "models": [settings.openai_sol_model, settings.openai_terra_model],
        "model_roles": {
            "material": settings.openai_terra_model,
            "bounding_dimensions": settings.openai_sol_model,
            "drawing_stock": settings.openai_sol_model,
            "conditional_dimension_recovery": settings.openai_sol_model,
        },
        "reasoning_effort": settings.openai_reasoning_effort,
        "prompt_sha256": {
            "material": hashlib.sha256(client.title_reader.prompt.encode("utf-8")).hexdigest(),
            "bounding_dimensions": hashlib.sha256(
                client.bounds_reader.prompt.encode("utf-8")
            ).hexdigest(),
            "drawing_stock": hashlib.sha256(
                client.stock_reader.prompt.encode("utf-8")
            ).hexdigest(),
            "dimension_recovery": hashlib.sha256(
                client.recovery_reader.prompt.encode("utf-8")
            ).hexdigest(),
        },
        "task_prompt_sha256": {
            "material": hashlib.sha256(client.title_reader.task.encode("utf-8")).hexdigest(),
            "bounding_dimensions": hashlib.sha256(
                client.bounds_reader.task.encode("utf-8")
            ).hexdigest(),
            "drawing_stock": hashlib.sha256(
                client.stock_reader.task.encode("utf-8")
            ).hexdigest(),
        },
        "truth_source": "part-prints/print-index.md (read live for this run)",
        "input_directory": str(args.prints_dir),
        "summary": {
            "parts": len(reports),
            "errors": sum(1 for report in reports if report["error"]),
            "reader_errors": reader_errors,
            "paid_model_calls_attempted": paid_model_calls_attempted,
            "dimension_buckets_by_model": {
                model: dict(counts) for model, counts in buckets.items()
            },
            "shape_results_by_model": {
                model: dict(counts) for model, counts in shape_results.items()
            },
            "combined_dimension_statuses": dict(dimension_statuses),
            "combined_material_statuses": dict(material_statuses),
            "presentation_statuses": dict(presentations),
            "recommendations": recommendations,
        },
        "reports": reports,
    }
    print(json.dumps(payload["summary"], indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    return 0 if not payload["summary"]["errors"] else 1


def main() -> None:
    raise SystemExit(asyncio.run(run(build_parser().parse_args())))


if __name__ == "__main__":
    main()
