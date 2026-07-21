# Machinable

Machinable is a desktop-first web application that reads a digitally generated
engineering-drawing PDF and returns the most useful raw-material information
the available evidence supports.

The authoritative product and implementation direction is
[`docs/build-week/build-brief.md`](docs/build-week/build-brief.md).

This is a safely testable pilot, not a production-ready ordering system. A
machinist must verify every result against the original drawing before material
is ordered or cut.

## Target workflow

- GPT-5.6 Sol High and Terra High independently read the same critical fields.
- PDF text and page coordinates provide an additional textual witness.
- Part identity, units, material, shape, dimensions, and drawing-specified stock
  callouts resolve independently.
- A dimension failure does not hide resolved material or shape.
- Detailed material resolution produces supplier-facing language while
  retaining the exact drawing callout and qualified uncertainty.
- Deterministic Python applies machining allowance, selects local standard
  stock, and calculates cut length, drop length, and yield when dependencies are
  resolved.
- The production frontend is a desktop-first Next.js application with PDF
  preview, field-level review, manual correction, and recalculation.

Werk24, Anthropic, and Claude are not part of the runtime. Phone-photo input,
live McMaster-Carr/Alro catalogs, and automatic persistence remain outside the
MVP.

## Current implementation baseline

The repository currently has:

- a FastAPI backend;
- one GPT-5.6 Sol structured PDF read;
- deterministic machining and stock calculations;
- an Expo client retained only as behavioral reference;
- offline tests and an opt-in paid evaluation harness; and
- `part-prints/print-index.md` as the sole dimensional evaluation truth.

The current single-reader route, global uncertainty error, and Expo UI are
known implementation gaps. They are not the current product design.

## Baseline setup

1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
2. Run `make setup`.
3. Run `make dev`.

At present, `make dev` starts FastAPI and the Expo reference client. The Expo
client reads `EXPO_PUBLIC_API_BASE_URL` from `src/frontend/.env`. These commands
must be updated when the approved Next.js migration is implemented.

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

Use `--all` only after approving the exact paid-call plan.
