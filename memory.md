# Machinable handoff

## Authoritative direction

- `docs/build-week/build-brief.md` is the single current build brief.
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

## Current implementation baseline

- FastAPI accepts digitally generated PDFs.
- One GPT-5.6 Sol call extracts a single drawing interpretation.
- Missing or disputed required facts currently become a global 422 response.
- Deterministic machining and stock calculations are implemented.
- The current Expo client is behavioral reference only; it is not the
  production frontend direction.
- Offline tests and targeted paid-evaluation tooling exist.

These baseline facts are implementation gaps to migrate, not current product
decisions.

## Recent evidence

- Targeted live runs showed direct part-number tabulated drawings working more
  reliably than AS4395 size-code drawings.
- The current model can resolve material even when dimensions fail, but the
  current API discards that useful partial result.
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

1. Complete the Phase 1 read-only audit against the authoritative brief.
2. Propose exact backend-contract, PDF-evidence, reader, arbitration, material,
   and test changes before implementation.
3. Implement backend field-level contracts before additional frontend work.
4. Confirm the desktop split-screen structure and visual direction before
   styling the Next.js UI.
5. Request approval for the exact paid evaluation plan after offline checks.

## Verification and known baseline issues

- The last full baseline `make check` passed Python lint, Expo lint, strict
  TypeScript, and 13 offline tests.
- Backend packaging and Uvicorn startup were verified.
- Targeted paid calls have run, but the controlled dual-reader evaluation has
  not.
- The Expo 54 dependency tree has 14 moderate audit findings. Expo is being
  replaced rather than upgraded as the production UI.
- This directory currently has no `.git` metadata.
