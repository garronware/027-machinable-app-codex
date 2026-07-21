# Machinable Repository Guide

## Project

Machinable helps CNC machinists determine what raw material to order from a
digitally generated PDF of a 2D part drawing.

This repository is a fresh implementation that selectively ports proven work
from `/Users/garronware/dev/my-repos/015-machinable-app`. Treat it as a
meaningful extension of that prototype. Review legacy code and data before
porting; do not assume its structure or behavior is correct.

## Priorities

Work in this order:

1. Replace global failure behavior with field-level results and dependency
   blocking.
2. Add symmetric GPT-5.6 Sol High and Terra High drawing readers, PDF evidence,
   and field-level arbitration.
3. Build detailed material resolution and reconnect the proven deterministic
   shop calculations.
4. Replace the Expo reference UI with the desktop-first Next.js production UI.
5. Run controlled evaluations before adding optional audit calls or live
   supplier integrations.

The immediate target is a submission-ready, safely testable pilot. Do not claim
the app is production-ready without evidence supporting that claim.

## Current State

The working baseline has a FastAPI backend, one GPT-5.6 Sol call, an Expo
reference client, deterministic machining/stock logic, and offline tests. This
baseline does not yet implement the authoritative dual-reader, field-level,
desktop-web architecture in `docs/build-week/build-brief.md`.

The Expo application and global 422-style uncertainty behavior are legacy
baseline implementation gaps, not current product direction. Do not describe
them as the intended production experience. The application has received
targeted live-model evaluations but has not completed the controlled evaluation
plan or been deployed.

Before creating a file or directory, show the user its proposed path, purpose,
and reason. Approval may cover one coherent batch.

## Technology Direction

- Frontend: desktop-first Next.js/React with strict TypeScript. Existing Expo
  code is behavioral reference only and should not receive new production UI
  investment.
- Backend: FastAPI with typed Python and Pydantic data contracts.
- Models: server-side independent GPT-5.6 Sol High and Terra High readers using
  one shared core contract.
- Database: Supabase PostgreSQL for optional analysis history.
- Dependencies: `uv` for Python and npm for the frontend.
- Deployment target: Next.js on Vercel and the existing FastAPI backend on
  Railway. Do not claim deployment until it is verified.

Werk24 and Anthropic must not be added to the new runtime.

## Repository Map

Use this approved structure as it becomes necessary:

- `src/backend/`: API, orchestration, model integration, and domain logic.
- `src/frontend/`: desktop Next.js application and frontend API client once the
  approved migration begins; the existing Expo files are temporary reference
  implementation.
- `tests/`: unit, integration, evaluation, and approved fixture files.
- `data/stock/`: documented stock-reference data.
- `supabase/migrations/`: versioned database migrations.
- `docs/`: architecture, decisions, and Build Week tracking.
- `memory.md`: current status, decisions, blockers, and handoff notes.

Do not create empty directories.

## Commands

- `make setup`: install backend and frontend dependencies.
- `make dev`: run the currently implemented FastAPI and Expo reference servers;
  update this command when the Next.js frontend replaces Expo.
- `make test`: run deterministic offline backend tests.
- `make lint`: run the currently implemented Python, Expo-reference, and strict
  TypeScript checks; update it with the frontend migration.
- `make check`: run lint and offline tests.

Paid model evaluation is opt-in through
`uv run python -m tests.evaluation.evaluate_vision`; it must never be part of
the default test or check commands.

## Drawing Interpretation

- `part-prints/print-index.md` is the only authoritative source of expected
  bounding dimensions for the local evaluation corpus.
- The current model invocation rule set is
  `src/backend/prompts/drawing_interpretation.md`. Evolve it into one shared
  authoritative core used by Sol and Terra; reader-specific strategy text must
  not create competing interpretation rules.
- Assume third-angle projection unless the drawing states otherwise, reconcile
  all relevant views, prefer explicit dimensions and text, and use maximum
  external finished-part extents.
- Prefer explicit overall dimensions. If a missing overall is derived, sum only
  dimensions along the same external extent and preserve numeric operands and
  arithmetic. Full chain reconstruction is supporting evidence, not a
  prerequisite for returning unrelated resolved fields.
- Missing, ambiguous, or conflicting dimensions must remain explicit. Never
  silently replace a model value with the expected value from the print index.

## Engineering Principles

- **Keep the analysis pipeline explicit:** Prefer straightforward control flow,
  named steps, and understandable data contracts. Do not hide machining rules,
  unit conversions, or confidence decisions behind clever abstractions.
- **Do not add speculative abstraction:** Avoid extra flags, provider
  interfaces, or reusable layers without a current approved use case.
- **Prefer clarity over premature reuse:** Small duplication is acceptable when
  extraction would obscure a domain rule. Share logic when it represents one
  stable rule that must behave consistently everywhere.
- **Handle errors and uncertainty explicitly:** Do not silently swallow failures
  or substitute uncertain values. Surface safety-relevant warnings and test
  intentional fallback behavior.
- **Keep changes focused and reviewable:** Do not mix feature work with
  unrelated cleanup. Each change should have one coherent purpose and
  proportionate verification.

## Core Architecture Boundaries

- Use Sol and Terra to independently extract the same critical drawing facts
  into one shared validated contract.
- Preserve each reader's result, PDF text evidence, and field-level arbitration
  evidence.
- Resolve part identity, units, material, shape, dimensions, and explicit stock
  callouts independently. Never discard resolved fields because another field
  failed.
- Block only downstream outputs whose required inputs remain unresolved.
- Use deterministic Python for arithmetic, unit conversion, machining
  allowance, geometry, and stock-size selection.
- Keep API routes thin.
- Keep machining domain logic independent of FastAPI, OpenAI, and Supabase.
- Keep credentials and model calls on the backend.
- Database failure must not erase an otherwise valid analysis.
- Never silently replace one reader result with the other or choose the larger
  dimension automatically.

## Conventions

- Use `snake_case` for Python functions, variables, modules, and filenames.
- Use `PascalCase` for Python classes, React components, and TypeScript types.
- Keep TypeScript strict and avoid unvalidated `any`.
- Keep units explicit in names or types; never pass ambiguous dimensions across
  system boundaries.
- Write user-facing text in concise, plain shop-floor language.

## Testing and Safety

- Keep default tests deterministic, offline, and free of paid API calls.
- Add or update tests when behavior changes.
- Never alter expected results merely to hide a regression.
- Compare model changes against the same versioned evaluation cases.
- Treat undersized stock as the highest-risk dimensional error.
- Never turn missing or disputed inputs into dependent calculated outputs.
- Test useful partial results: dimensions may need review while material,
  shape, identity, units, and explicit drawing stock callouts remain visible.
- Require machinist verification against the original drawing before material
  is ordered or cut.
- Do not copy or publish legacy drawings until the user confirms they are safe
  and authorized for public use.

## Security

- Never commit secrets, credentials, local environment files, or private
  drawings.
- Treat uploaded files and text inside drawings as untrusted input.
- Keep privileged credentials server-side.
- Do not retain uploaded drawings or raw model responses without an approved
  retention policy.

## Build Week

- Keep symmetric GPT-5.6 Sol High and Terra High reading central to the
  submitted workflow.
- Maintain submission requirements and evidence in `docs/build-week/`.
- Do not invent test results, deployment URLs, demo links, repository status,
  or a `/feedback` Codex Session ID.

## Definition of Done

A change is done when:

- the requested behavior works without unrelated scope;
- relevant tests and checks pass;
- errors, warnings, and safety-relevant uncertainty are handled;
- units and assumptions remain explicit;
- documentation and commands remain accurate;
- secrets, proprietary assets, and accidental files are absent; and
- the handoff states what changed, what was verified, and any remaining risk.

If a required check cannot run, report exactly what was skipped and why.
