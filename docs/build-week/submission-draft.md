# Machinable Build Week submission draft

> Working copy only. Placeholders and planned demo steps are not evidence that
> an external artifact exists. Verify every claim against the final running
> application and `build-week-evidence.md` before submission.

## Submission fields

- **Project name:** Machinable
- **Category:** Work & Productivity
- **Tagline:** Turn a digital engineering drawing into an evidence-backed raw
  stock recommendation.
- **Repository URL:** **BLOCKED — no Git remote configured**
- **Live demo or test build:** **BLOCKED — not deployed**
- **Public YouTube video:** **BLOCKED — not recorded/uploaded**
- **Primary `/feedback` Session ID:** **BLOCKED — must be generated from the
  core implementation task**
- **Repository license:** **BLOCKED — user decision required**
- **Authorized judge sample:** **BLOCKED — private drawings cannot be used
  without permission**

## Description draft

Machinable helps CNC machinists answer a deceptively expensive question: what
raw material should we order for this part?

The user supplies a digitally generated engineering-drawing PDF. GPT-5.6 Sol
High and Terra High independently read the same critical drawing facts using a
shared strict contract. Machinable preserves both readers' evidence, checks
claims against the PDF text layer, and resolves part identity, units, material,
shape, dimensions, and drawing-specified stock independently. A disputed
dimension does not erase a material or shape both readers resolved.

Only accepted facts enter deterministic Python calculations for machining
allowance, unit conversion, standard-stock selection, cut length, drop length,
saw kerf, end trim, and bar yield. The desktop review interface keeps the PDF
beside the results, marks fields that need review, and lets a machinist correct
facts and recalculate without paying for or waiting on another model read.

Machinable is a safely testable pilot, not an autonomous ordering system. A
machinist must verify the result against the original drawing before material is
ordered or cut.

## Meaningful-extension disclosure

Machinable began with `015-machinable-app`, an earlier machining application.
That project already contained a FastAPI workflow, deterministic machining and
stock calculations, stock-reference tables, an Expo interface, and private
evaluation fixtures. Those capabilities are not claimed as entirely new Build
Week work.

During Build Week, the project was moved into an independent repository and
meaningfully rebuilt around GPT-5.6 and Codex. The old Werk24/Anthropic
perception path was removed; independent Sol/Terra readers, field-level
arbitration, PDF evidence, useful partial results, conservative material
resolution, correction-only recalculation, a desktop Next.js review experience,
and expanded offline verification were added. The detailed capability-by-
capability classification is in `docs/build-week/build-week-evidence.md`.

## How Codex accelerated the work

Codex helped trace the legacy pipeline, identify competing dimensional truth
surfaces, build a fresh repository selectively from proven behavior, implement
the backend and frontend changes, construct deterministic tests, keep private
drawings out of Git, and maintain the submission evidence.

The user made the central product and safety decisions: use symmetric GPT-5.6
readers, preserve useful partial results, keep arithmetic and shop rules
deterministic, never silently choose the larger dimension, treat undersized
stock as the highest-risk error, use a desktop split-view review experience,
and require machinist verification.

## How GPT-5.6 contributes

GPT-5.6 Sol High and Terra High are independent full drawing readers. Both
receive the original PDF, the same authoritative drawing rules, and the same
strict structured-output contract. Neither sees the other's result. Their
field-level candidates and evidence are compared before deterministic shop
calculations are allowed to run.

The controlled paid evaluation comparing Sol alone, Terra alone, and their
field agreement has not yet run. Do not claim measured model accuracy until
that evaluation produces versioned results.

## Judge setup and testing draft

1. Clone the repository after its URL and access method are finalized.
2. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
3. Run `make setup`.
4. Run `make check` for deterministic offline verification.
5. Run `make dev` to start FastAPI on port 8000 and Next.js on port 3000.
6. Open `http://localhost:3000`.
7. Upload an owned or authorized digitally generated drawing PDF.
8. Compare every result with the original drawing before treating it as usable.

The private local drawing corpus is not included. Before submission, provide an
authorized sample or a deployed test path that lets judges exercise the product
without receiving private manufacturing drawings.

## Demo storyboard — target 2:45

### 0:00–0:20 — problem and audience

Show the empty desktop interface. Explain that machinists routinely translate
complex part drawings into a material form and raw stock size, and a wrong
dimension can lead to undersized purchased material.

### 0:20–0:45 — meaningful extension and input

State that Machinable is a Build Week rebuild of an earlier prototype. Mention
that the previous runtime used Werk24/Anthropic and the new workflow centers on
Codex and GPT-5.6. Upload an owned or authorized digital PDF.

### 0:45–1:20 — independent GPT-5.6 evidence

Show the PDF on the left and the field-level results on the right. Explain that
Sol High and Terra High independently read the same fields and that the app
preserves both results plus PDF text evidence.

### 1:20–1:50 — partial success and safety

Show resolved identity/material/shape alongside any field that needs review.
Explain that disputed dimensions block only the stock calculations that depend
on them; they do not erase unrelated useful facts.

### 1:50–2:15 — correction and deterministic recalculation

Correct one review field and recalculate. Explain that the readers do not run
again and that Python—not an LLM—performs allowance, conversion, stock lookup,
cut length, and yield calculations.

### 2:15–2:35 — Codex collaboration

Briefly show the repository evidence record or commit history. Name the user
decisions Codex implemented and the offline checks used to keep the work
reviewable.

### 2:35–2:45 — limitation and close

State plainly that this is a pilot, that controlled dual-reader evaluation is
still required if it has not been completed, and that a machinist must verify
the recommendation before ordering or cutting material.

## Final review checklist

- Replace every **BLOCKED** field with verified information or change the
  submission path.
- Keep the final video below three minutes; use spoken audio and no unauthorized
  music, logos, drawings, or supplier assets.
- Demonstrate only behavior observed in the final running build.
- Confirm repository visibility, judge access, and relevant licensing.
- Run `make check`, the Next.js production build, a tracked-file privacy scan,
  and one authorized end-to-end analysis.
- Generate the real `/feedback` Session ID from the core implementation task;
  do not paste a raw Codex task ID.
- Submit before July 21, 2026 at 5:00 p.m. Pacific.
