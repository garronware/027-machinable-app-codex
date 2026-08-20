# Machinable

Machinable is a desktop-first web application that reads a digitally generated
engineering-drawing PDF and returns the most useful raw-material information
the available evidence supports.

The Build Week implementation brief is
[`docs/build-week/build-brief.md`](docs/build-week/build-brief.md); current
repository behavior and engineering constraints are maintained in
[`AGENTS.md`](AGENTS.md).
Build Week provenance and submission readiness are maintained in
[`docs/build-week/build-week-evidence.md`](docs/build-week/build-week-evidence.md).

This is a safely testable pilot, not a production-ready ordering system. A
machinist must verify every result against the original drawing before material
is ordered or cut.

## Target workflow

- GPT-5.6 Sol High reads stock shape and applicable bounding dimensions.
- GPT-5.6 Terra High reads material purchasing facts only.
- If Sol misses a stock-blocking cross-section dimension or overall length, one
  conditional Sol call reviews focused high-resolution crops around the
  candidate callouts.
- PDF text and page coordinates provide an additional textual witness.
- Part identity is non-gating and is not requested from either model.
- Units, material, shape, dimensions, and drawing-specified stock callouts
  resolve independently.
- A dimension failure does not hide resolved material or shape.
- Detailed material resolution produces supplier-facing language while
  retaining the exact drawing callout and qualified uncertainty.
- Deterministic Python applies machining allowance, selects local standard
  stock, and calculates cut length, drop length, and yield when dependencies are
  resolved.
- A complete, safe drawing-specified stock size takes precedence over the
  generic catalog result while remaining separate from finished dimensions.
- The production frontend is a desktop-first Next.js application with PDF
  preview, field-level review, manual correction, and recalculation.

Werk24, Anthropic, and Claude are not part of the runtime. Phone-photo input,
live McMaster-Carr/Alro catalogs, and automatic persistence remain outside the
MVP.

## Current implementation

The repository currently has:

- a FastAPI backend;
- focused GPT-5.6 Sol High geometry and Terra High material reads;
- conditional high-resolution Sol recovery for missing stock cross-sections or
  overall length;
- field-level arbitration and HTTP 200 partial-success responses;
- deterministic PDF text tokens, page coordinates, and claim checks;
- conservative material and supplier-language resolution;
- deterministic machining and stock calculations;
- a typed correction/recalculation endpoint that does not rerun model calls;
- a desktop-first Next.js review UI with PDF preview, field-level status,
  correction, recalculation, and expandable evidence;
- offline tests and an opt-in paid evaluation harness; and
- `part-prints/print-index.md` as the sole dimensional evaluation truth.

A 10-print paid evaluation of the first specialized-reader implementation is
saved at
`tests/evaluation/runs/specialized-10-print-2026-07-26.json`. The focused prompt
and conditional recovery changes made after that run still require controlled
paid evaluation before any production-readiness claim.

## Baseline setup

1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
2. Run `make setup`.
3. Run `make dev`.

`make dev` starts FastAPI on port 8000 and Next.js on port 3000. The frontend
uses `NEXT_PUBLIC_API_BASE_URL`, defaulting locally to `http://localhost:8000`.

## Deployment

Deploy the backend to Railway from the repository root. Railway will use the
root `Dockerfile`. Set these server-side variables:

- `OPENAI_API_KEY`
- `OPENAI_SOL_MODEL=gpt-5.6-sol`
- `OPENAI_TERRA_MODEL=gpt-5.6-terra`
- `OPENAI_REASONING_EFFORT=high`
- `ALLOWED_ORIGINS=https://<your-vercel-domain>`

Verify `https://<your-railway-domain>/health` before deploying the frontend.

Deploy the frontend to Vercel with `src/frontend` as the project root. Set
`NEXT_PUBLIC_API_BASE_URL=https://<your-railway-domain>`, deploy, then ensure
Railway's `ALLOWED_ORIGINS` exactly matches the final Vercel origin.

## Checks

```sh
make test
make lint
make check
```

Default checks are deterministic, offline, and make no paid model calls.

Paid evaluation is opt-in:

```sh
make eval-help
uv run python -m tests.evaluation.evaluate_vision --limit 3
```

Each part normally makes two paid calls. A third Sol call is made only when a
stock-blocking cross-section dimension or overall length is missing. Use
`--all` only after approving the exact paid-call plan.

## Build Week provenance

Machinable is a meaningful extension of the earlier `015-machinable-app`, not
an application created entirely during Build Week. The earlier project already
contained a FastAPI workflow, deterministic machining and stock calculations,
stock tables, an Expo interface, and a drawing-evaluation corpus. Project 027
selectively ported proven deterministic work while replacing the old
Werk24/Anthropic perception path and mobile-oriented product direction.

During the Build Week submission period, Codex was used to audit the legacy
pipeline, establish the dimensional evaluation source of truth, build the
GPT-5.6 PDF-reading path, implement field-level evidence and dependency
blocking, add conservative material resolution and correction-only
recalculation, migrate the product to Next.js, and maintain offline tests and
submission evidence. The user made the key safety and product decisions,
including treating undersized stock as the highest-risk error, requiring useful
partial results, keeping deterministic shop math outside the models, excluding
private drawings, and choosing a desktop review workflow.

The detailed before/after classification, dated evidence, verification results,
and unresolved submission blockers are in the
[Build Week evidence record](docs/build-week/build-week-evidence.md). The
[submission draft](docs/build-week/submission-draft.md) is working copy for the
Devpost description and demo video; it is not evidence that a deployment,
video, repository URL, or `/feedback` Session ID exists.

## Judge testing notes

No private production drawing is included in Git. Judges will need an
authorized, digitally generated engineering-drawing PDF or an approved public
sample that has not yet been selected. The application should be treated as a
safely testable pilot: every result must be checked against the original
drawing before material is ordered or cut.
