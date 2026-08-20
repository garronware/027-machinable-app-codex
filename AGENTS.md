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

1. Run controlled evaluations of focused Sol geometry, Terra material, and
   conditional Sol dimension recovery against the same approved cases.
2. Extend material-code resolution only with authoritative mappings.
3. Harden and deploy only after evaluation, before adding optional audit calls or live
   supplier integrations.

The immediate target is a submission-ready, safely testable pilot. Do not claim
the app is production-ready without evidence supporting that claim.

## Current State

The backend now uses GPT-5.6 Sol High for stock shape and applicable bounding
dimensions and Terra High for material only. Part identity is deliberately
non-gating and is not requested from either model. When Sol leaves a
stock-blocking cross-section dimension or overall length unresolved, one
conditional Sol call receives deterministic high-resolution PDF crops focused
around the candidate callouts. Deterministic PDF evidence, shop math, stock selection, and
correction-only recalculation remain outside the models.

The Expo reference application has been replaced by the approved desktop
Next.js split-view UI. It displays complete and partial results together,
supports corrections and deterministic recalculation, and uses the contemporary
B2B visual direction. A controlled 10-print specialized-reader evaluation ran
on 2026-07-26; its report is
`tests/evaluation/runs/specialized-10-print-2026-07-26.json`. The focused prompt
and conditional recovery changes made afterward have not yet received paid
evaluation. The application has been deployed, but no production-readiness
claim is supported.

Before creating a file or directory, show the user its proposed path, purpose,
and reason. Approval may cover one coherent batch.

## Technology Direction

- Frontend: desktop-first Next.js/React with strict TypeScript.
- Backend: FastAPI with typed Python and Pydantic data contracts.
- Models: server-side GPT-5.6 Sol High for stock geometry, Terra High for
  material, and a conditional focused Sol recovery call only when a required
  stock cross-section dimension or overall length remains missing.
- Database: Supabase PostgreSQL for optional analysis history.
- Dependencies: `uv` for Python and npm for the frontend.
- Deployment target: Next.js on Vercel and the existing FastAPI backend on
  Railway. Do not claim deployment until it is verified.

Werk24 and Anthropic must not be added to the new runtime.

## Repository Map

Use this approved structure as it becomes necessary:

- `src/backend/`: API, orchestration, model integration, and domain logic.
- `src/frontend/`: desktop Next.js application and typed frontend API client.
- `tests/`: unit, integration, evaluation, and approved fixture files.
- `data/stock/`: documented stock-reference data.
- `supabase/migrations/`: versioned database migrations.
- `docs/`: architecture, decisions, and Build Week tracking.
- `memory.md`: current status, decisions, blockers, and handoff notes.

Do not create empty directories.

## Commands

- `make setup`: install backend and frontend dependencies.
- `make dev`: run FastAPI and the Next.js desktop frontend.
- `make test`: run deterministic offline backend tests.
- `make lint`: run Python lint, Next.js lint, and strict TypeScript checks.
- `make check`: run lint and offline tests.

Paid model evaluation is opt-in through
`uv run python -m tests.evaluation.evaluate_vision`; it must never be part of
the default test or check commands.

## Drawing Interpretation

- `part-prints/print-index.md` is the only authoritative source of expected
  bounding dimensions for the local evaluation corpus.
- Current model invocation rules are deliberately separated by duty:
  `src/backend/prompts/shape_geometry.md`,
  `src/backend/prompts/title_material.md`, and
  `src/backend/prompts/dimension_recovery.md`.
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

- Use Sol to extract stock shape and applicable bounding dimensions and Terra
  to extract material. Do not spend model effort resolving part name or part
  number.
- Preserve model results, PDF text evidence, focused-recovery provenance, and
  evaluation evidence.
- Resolve units, material, shape, dimensions, and explicit stock callouts
  independently. Never discard resolved fields because another field failed.
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
- Test useful incomplete results: dimensions may remain unresolved while
  material, shape, units, and explicit drawing stock callouts remain visible.
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

- Keep the specialized GPT-5.6 Sol High geometry and Terra High material roles
  central to the submitted workflow.
- Treat Machinable as a meaningfully extended pre-existing project; never imply
  that the entire application was created during Build Week.
- `docs/build-week/build-week-evidence.md` is the sole provenance and
  submission-readiness record. Classify material work as reused, materially
  modified, newly created, or planned, and record previous behavior, new
  behavior, completed Codex task, commit when available, verification, and
  remaining risk.
- Evidence entries are append-only except for clearly labeled factual
  corrections.
- Update the build brief, README, or memory only when that document's own
  responsibility changes; do not mirror the same status across documents.
- Do not invent dates, results, permissions, commits, repository or deployment
  URLs, demo links, or a `/feedback` Codex Session ID.

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
