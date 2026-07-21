"""Opt-in paid GPT-5.6 Sol evaluation against the live print index."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from backend.clients.openai_vision import OpenAIVisionClient
from backend.core.config import settings
from tests.evaluation.print_index import (
    PART_PRINTS_DIR,
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
        "--limit",
        type=int,
        default=3,
        help="Maximum paid calls (default: 3). Ignored with --all.",
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
    return parser


async def run(args: argparse.Namespace) -> int:
    if not settings.openai_api_key:
        print("OPENAI_API_KEY is missing; no paid calls were made.", file=sys.stderr)
        return 2

    cases = load_truth_cases()
    if args.only:
        needle = args.only.lower()
        cases = [
            case
            for case in cases
            if needle in case.filename.lower()
            or needle in case.part_number.lower()
        ]
    if not args.all:
        cases = cases[: max(args.limit, 0)]

    client = OpenAIVisionClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        reasoning_effort=settings.openai_reasoning_effort,
    )
    reports: list[dict] = []
    for case in cases:
        path = PART_PRINTS_DIR / case.filename
        print(f"evaluate {case.filename}")
        try:
            interpretation = await client.interpret_pdf(
                path.read_bytes(), case.filename
            )
            comparison = compare_interpretation(case, interpretation)
            reports.append(
                {
                    "file": case.filename,
                    "error": None,
                    "interpretation": interpretation.model_dump(mode="json"),
                    "comparison": comparison,
                }
            )
        except Exception as exc:  # continue to preserve evidence from other cases
            reports.append(
                {
                    "file": case.filename,
                    "error": f"{type(exc).__name__}: {exc}",
                    "interpretation": None,
                    "comparison": None,
                }
            )
            print(f"error    {case.filename}: {exc}", file=sys.stderr)

    buckets: dict[str, int] = {}
    for report in reports:
        comparison = report["comparison"]
        if not comparison:
            continue
        print(f"\n{report['file']}")
        print(
            "  shape: "
            f"{comparison['actual_shape']} "
            f"(expected {comparison['expected_shape']})"
        )
        for dimension in comparison["dimensions"]:
            bucket = dimension["bucket"]
            buckets[bucket] = buckets.get(bucket, 0) + 1
            print(
                f"  {dimension['axis']}: "
                f"returned {dimension['actual']!r}, "
                f"expected {dimension['expected']!r} "
                f"[{bucket}]"
            )
            if dimension["dimension_path"]:
                print(f"    path: {dimension['dimension_path']}")
            if dimension["evidence"]:
                print(f"    evidence: {dimension['evidence']}")

    payload = {
        "historical_report": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "model": settings.openai_model,
        "reasoning_effort": settings.openai_reasoning_effort,
        "prompt_sha256": hashlib.sha256(
            client.prompt.encode("utf-8")
        ).hexdigest(),
        "truth_source": "part-prints/print-index.md (read live for this run)",
        "summary": {
            "parts": len(reports),
            "errors": sum(1 for report in reports if report["error"]),
            "dimension_buckets": buckets,
        },
        "reports": reports,
    }
    print(json.dumps(payload["summary"], indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {args.output}")
    return 0 if not payload["summary"]["errors"] else 1


def main() -> None:
    raise SystemExit(asyncio.run(run(build_parser().parse_args())))


if __name__ == "__main__":
    main()
