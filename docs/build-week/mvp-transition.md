# Historical scaffold transition: GPT-5.6 Sol, PDF first

> **Status:** This document records the initial 027 scaffold transition and its
> baseline verification. It is not the current product plan. The authoritative
> direction is `docs/build-week/build-brief.md`, which requires symmetric Sol
> High/Terra High readers, field-level partial results, detailed material
> resolution, and a desktop Next.js production frontend.

## What changed in the initial scaffold

The 027 pilot selectively ports the useful deterministic stock-sizing behavior
from 015 while replacing its extraction pipeline.

- One `gpt-5.6-sol` Responses call reads a high-detail digital PDF.
- The response is parsed directly into a Pydantic schema with evidence,
  dimension paths, warnings, and conflicts.
- The drawing rules live only in
  `src/backend/prompts/drawing_interpretation.md`, which is sent with every
  interpretation call.
- Werk24, Anthropic, the second Claude material call, and two-sample vision
  reconciliation are absent.
- Only PDF uploads were accepted. The Expo UI used a document picker and is now
  retained only as behavioral reference.
- Machining allowance and stock lookup remain deterministic and use the proven
  015 stock tables.

## Dimensional truth audit

The 015 implementation contained several dimensional surfaces:

| Surface | Previous role | MVP treatment |
|---|---|---|
| `print-index.md` | Machinist-entered evaluation truth | Copied to `part-prints/print-index.md`; sole expected bounding truth |
| Claude vision response | Primary runtime dimensions | Replaced in the initial scaffold by one GPT-5.6 Sol structured response; the current plan adds a symmetric Terra reader |
| Werk24 response | Fallback and cross-check | Removed; no runtime code, configuration, capture, dependency, or docs |
| Second Claude sample | Same-model consistency check | Not copied; the current design instead uses independent Sol and Terra readers with field-level arbitration |
| Hand-edited and untouched Werk24 JSON | Cached third-party results | Historical legacy data; not copied |
| Vision JSON/HTML reports | Historical model outputs plus copied truth | Historical legacy data; not copied |
| Multiple legacy prompt variants | Competing extraction instructions | Not copied; replaced by the one invocation prompt under `src/backend/prompts/` |
| Expected final-output fixtures | Downstream regression values that duplicated dimensions | Not copied; new tests derive expectations from the live index or explicit synthetic cases |
| Frontend encoded-response snapshots | UI fixtures containing cached analysis results | Not copied; the MVP displays only the current API response |
| Supabase `full_output` | Optional run snapshot | History persistence deferred; runtime retains neither drawing nor raw response |
| Stock CSVs | Purchasable stock reference, not finished-part truth | Ported unchanged |
| Machining allowance tables | Deterministic derived rule | Ported and covered by offline tests |

Runtime output is never compared with `print-index.md`. The index exists only
for tests and evaluations, so known sample answers cannot leak into production
analysis.

## Interpretation assumptions preserved in the current brief

- Input is a digitally generated PDF.
- Clear vector/text dimensions, title-block fields, and notes outrank visual
  inference.
- Third-angle projection is assumed unless explicitly contradicted.
- Orthographic, section, detail, and auxiliary views are reconciled before
  assigning axes.
- Explicit overall dimensions outrank outermost feature dimensions, which
  outrank cross-view reconciliation, which outranks outlines.
- Finished-part maximum external extents define the envelope. Internal features
  do not.
- A missing overall may be derived from same-axis dimensions on the same
  external path, with operands and arithmetic preserved when a chain is used.
  Explicit overall dimensions remain preferred; full chain reconstruction is
  not required before unrelated fields can resolve.
- Conflicts, missing facts, and outline-only numeric inference block only the
  affected fields and their dependent calculations. Resolved identity,
  material, shape, units, and explicit stock callouts remain available.
- Evaluation reports extracted/index differences. It never rewrites extraction
  output to agree with the index.

## Current exclusions and later integrations

- Phone photos and image preprocessing.
- The optional third targeted disagreement audit remains evaluation-dependent;
  the two independent Sol/Terra readers are now required MVP architecture.
- Werk24 or another extraction provider.
- Supabase analysis history and an approved retention policy.
- Live McMaster-Carr or Alro inventory.

Before any recommendation is used, a machinist must verify it against the
original drawing.

## Initial scaffold verification status

- `make check` passes Python lint, Expo lint, strict TypeScript checking, and 13
  deterministic offline tests.
- The backend package imports normally and the Uvicorn development server
  starts successfully.
- The copied corpus contains 166 PDFs. The live index currently provides 33
  complete, non-excluded dimensional evaluation cases.
- Targeted live GPT-5.6 Sol evaluations were later run and saved under
  `tests/evaluation/runs/`; the controlled dual-reader evaluation remains
  pending. No paid call is part of default checks.
- `npm audit --omit=dev` reports 14 moderate findings in the Expo 54
  transitive toolchain. Expo is now a behavioral reference and will be replaced
  by the desktop Next.js production frontend rather than upgraded in place.
