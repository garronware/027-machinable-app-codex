# Machinable handoff

## Authoritative direction

- `docs/build-week/build-brief.md` is the single current build brief.
- `docs/build-week/build-week-evidence.md` is the sole Build Week provenance,
  dated evidence, compliance-status, and submission-blocker record.
- `docs/build-week/submission-draft.md` is working Devpost and demo-video copy,
  not proof that an external submission artifact exists.
- `docs/stock-recommendation-decisions.md` is the approved implementation
  handoff for length recovery and drawing-specified stock recommendations.
- `README.md` is the current judge-facing setup, testing, limitation, and Codex
  collaboration guide.
- The product is a desktop-first Next.js web application backed by FastAPI.
- A single-purpose GPT-5.6 Sol High call reads only the maximum external
  finished-part bounding dimensions. The application infers Round versus Flat
  from the applicable returned dimension set.
- The bounding contract requires a best-fit choice of inches or millimeters;
  `UNKNOWN` is not accepted from that focused read.
- A separate Sol read preserves explicit drawing-stock callouts; Terra High
  reads the material callout for display only.
- Part identity is deliberately non-gating and is not requested from either
  model.
- When Sol misses a stock-blocking cross-section dimension or overall length,
  one conditional Sol call reviews deterministic high-resolution crops around
  candidate callouts.
- PDF text tokens and page coordinates support focused recovery. The
  single-purpose model dimensions are not deleted for lacking a text token.
- Results are field-level: units, material, shape, dimensions, and explicit
  drawing stock callouts resolve independently.
- Unresolved dimensions must not hide resolved material or shape.
- Material never selects the machining allowance and never blocks a stock
  recommendation. An unreadable callout is displayed neutrally.
- Deterministic Python applies one general material-independent allowance and
  remains responsible for conversion, stock selection, cut/drop length, kerf,
  end trim, and yield.
- `part-prints/print-index.md` is the sole dimensional evaluation truth and is
  never used at runtime.
- Werk24, Anthropic, and Claude must remain absent from the runtime.

## Current implementation

- FastAPI accepts digitally generated PDFs.
- A single-purpose Sol bounding read, separate Sol drawing-stock read, and Terra
  material read run concurrently. The simple bounds are authoritative when
  they form one unambiguous round or prismatic envelope.
- Missing stock cross-sections or overall length trigger at most one focused Sol
  recovery call; accepted dimensions are never overwritten by recovery.
- PDF text tokens, page coordinates, numeric witnesses, and page/region
  rendering are implemented with PyMuPDF.
- The pipeline preserves each specialized result and resolves fields
  independently.
- Missing or disputed facts return HTTP 200 partial success and block only
  dependent calculations.
- Material is display-only. The stock calculation proceeds with one general
  allowance when the material callout is missing or unreadable.
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

1. Run controlled paid tests of the single-purpose Sol bounding prompt on the
   recent failing round prints.
2. Compare the same prompt and response fields with Gemini 3.1 Pro in the
   separate simplified-version project.
3. Rerun the same versioned print set before selecting a primary provider or
   changing production.

## Implemented stock-recommendation follow-up

- Product decisions from the 2026-08-17 Titan-400-Subplate troubleshooting are
  recorded in `docs/stock-recommendation-decisions.md`.
- Missing Flat and Round length now participates in the existing one-call
  focused recovery pass without overwriting accepted dimensions.
- A complete, safe drawing-specified stock callout now populates the normal
  recommendation fields and takes precedence over generic catalog selection.
- Incomplete or conflicting callouts remain visible for review and fall back to
  generic selection only when its independent inputs are resolved.
- The pair-first Flat Bar/Plate policy and restrained result-ticket UI remain in
  place. The Titan-400-Subplate case is verified offline with deterministic
  fakes; no paid model evaluation or production change was made.

## Verification and known baseline issues

- The repository has 66 deterministic offline backend tests passing, and the
  Next.js production build, lint, and strict TypeScript checks pass.
- Backend packaging and Uvicorn startup were verified.
- The controlled 10-print specialized-reader evaluation ran on 2026-07-26; the
  focused-prompt and recovery changes made afterward are offline-verified only.
- The Next.js dependency tree currently reports two moderate npm audit findings;
  no forced breaking upgrade has been applied.
- This directory is an independent Git repository for project 027.
- `origin/main` is locally aligned with commit `0080043` at the configured
  GitHub URL; unauthenticated judge access and the repository license remain
  unverified.
