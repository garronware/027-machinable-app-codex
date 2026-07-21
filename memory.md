# Machinable handoff

## Authoritative direction

- `docs/build-week/build-brief.md` is the single current build brief.
- `docs/build-week/build-week-evidence.md` is the sole Build Week provenance,
  dated evidence, compliance-status, and submission-blocker record.
- `docs/build-week/submission-draft.md` is working Devpost and demo-video copy,
  not proof that an external submission artifact exists.
- `README.md` is the current judge-facing setup, testing, limitation, and Codex
  collaboration guide.
- The product is a desktop-first Next.js web application backed by FastAPI.
- GPT-5.6 Sol High and Terra High independently read the same critical drawing
  fields using one shared structured contract.
- PDF text tokens and page coordinates provide additional evidence.
- Results are field-level: identity, units, material, shape, dimensions, and
  explicit drawing stock callouts resolve independently.
- Unresolved dimensions must not hide resolved material or shape.
- Detailed material resolution preserves the raw callout, grade, standard,
  condition, supplier language, confidence, and allowance class.
- Deterministic Python remains responsible for allowance, conversion, stock
  selection, cut/drop length, kerf, end trim, and yield.
- `part-prints/print-index.md` is the sole dimensional evaluation truth and is
  never used at runtime.
- Werk24, Anthropic, and Claude must remain absent from the runtime.

## Current implementation

- FastAPI accepts digitally generated PDFs.
- GPT-5.6 Sol High and Terra High independently return the same strict drawing
  contract and run concurrently.
- PDF text tokens, page coordinates, numeric witnesses, and page/region
  rendering are implemented with PyMuPDF.
- Arbitration preserves both readers and resolves fields independently.
- Missing or disputed facts return HTTP 200 partial success and block only
  dependent calculations.
- Common explicit material grades resolve deterministically into identity,
  purchasing language, and allowance class. Proprietary numeric material codes
  remain visible but unresolved without an authoritative mapping.
- Deterministic machining and stock calculations are implemented.
- Drawing-specified stock is preserved separately and checked against the
  calculated minimum.
- `/recalculate` accepts user-confirmed facts and reruns deterministic math
  without rerunning either reader.
- The production frontend is now a desktop-first Next.js split view with PDF
  preview, field-level review, correction, recalculation, recommendation, and
  expandable evidence. The Expo reference screens were removed.
- Offline tests and targeted paid-evaluation tooling exist. Controlled paid
  dual-reader evaluation has not run.

## Recent evidence

- Targeted live runs showed direct part-number tabulated drawings working more
  reliably than AS4395 size-code drawings.
- Backend tests now prove material and shape remain available when dimensions
  disagree.
- Saved local evaluation reports are under `tests/evaluation/runs/` and remain
  historical evidence.
- The current index includes harvested updates from the legacy 015 index,
  including Cummins 2899615 and corrected material code 31011 for 3026166.

## Safety and testing rules

- Never alter model output to match `print-index.md`.
- Treat undersized stock as the highest-risk dimensional failure.
- Never silently choose one reader's answer or the larger dimension.
- Block only calculations whose dependencies are unresolved.
- Preserve and display useful partial results and explicit uncertainty.
- Require machinist verification before ordering or cutting.
- Keep default tests offline and paid evaluations explicit.

## Next work

1. Request approval for an exact controlled paid evaluation plan.
2. Run Sol High, Terra High, and field-agreement treatments against the same
   versioned mix of straightforward and difficult prints.
3. Report every field result, partial-result usefulness, latency, and cost.
4. Harden and deploy only after the evaluated behavior is understood.

## Verification and known baseline issues

- The repository has 25 deterministic offline backend tests passing, and the
  Next.js production build, lint, and strict TypeScript checks pass.
- Backend packaging and Uvicorn startup were verified.
- Targeted paid calls have run, but the controlled dual-reader evaluation has
  not.
- The Next.js dependency tree currently reports two moderate npm audit findings;
  no forced breaking upgrade has been applied.
- This directory is an independent Git repository for project 027.
