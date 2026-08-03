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
- GPT-5.6 Sol High reads stock shape and applicable bounding dimensions; Terra
  High reads material purchasing facts only.
- Part identity is deliberately non-gating and is not requested from either
  model.
- When Sol misses a stock-blocking cross-section dimension, one conditional
  Sol call reviews deterministic high-resolution crops around candidate
  callouts.
- PDF text tokens and page coordinates provide additional evidence.
- Results are field-level: units, material, shape, dimensions, and explicit
  drawing stock callouts resolve independently.
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
- GPT-5.6 Sol High geometry and Terra High material reads run concurrently with
  separate, short contracts.
- Missing stock cross-sections trigger at most one focused Sol recovery call;
  accepted dimensions are never overwritten by recovery.
- PDF text tokens, page coordinates, numeric witnesses, and page/region
  rendering are implemented with PyMuPDF.
- The pipeline preserves each specialized result and resolves fields
  independently.
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
- Offline tests and paid-evaluation tooling exist. A controlled 10-print
  specialized-reader evaluation ran on 2026-07-26.

## Recent evidence

- Targeted live runs showed direct part-number tabulated drawings working more
  reliably than AS4395 size-code drawings.
- The 2026-07-26 evaluation completed 20 calls with zero API errors. Sol matched
  16 dimensions, missed 3, undersized 3, and selected the correct shape on 9 of
  10 prints. The report is
  `tests/evaluation/runs/specialized-10-print-2026-07-26.json`.
- For 201533-020, Sol found the correct 12.700 mm callout in its uncertainty
  text but did not follow its arrowheaded leader to resolve plate thickness.
  The new conditional crop recovery targets that exact failure and has not yet
  received a paid call.
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

1. Run a controlled paid 201533-020 test of the focused geometry prompt and
   conditional crop recovery.
2. If the thickness is stable across repeated runs, rerun the same versioned
   10-print set to check for shape or dimension regressions.
3. Report every geometry result, recovery call, material result, latency, and
   cost before further hardening.

## Verification and known baseline issues

- The repository has 39 deterministic offline backend tests passing, and the
  Next.js production build, lint, and strict TypeScript checks pass.
- Backend packaging and Uvicorn startup were verified.
- The controlled 10-print specialized-reader evaluation ran on 2026-07-26; the
  focused-prompt and recovery changes made afterward are offline-verified only.
- The Next.js dependency tree currently reports two moderate npm audit findings;
  no forced breaking upgrade has been applied.
- This directory is an independent Git repository for project 027.
- `origin/main` is locally aligned with commit `976c0d5` at the configured
  GitHub URL; unauthenticated judge access and the repository license remain
  unverified.
