# Stock recommendation follow-up decisions

Status: Approved product direction from the 2026-08-17 troubleshooting
conversation. No application code was changed as part of this decision record.

This document is the implementation handoff for the stock-recommendation
follow-up. It incorporates the original Flat Bar versus Plate decisions from
the Codex task titled `simplify-raw-matls-thread` and the later troubleshooting
of `part-prints/Titan-400-Subplate.pdf`.

## Objective

Return as much useful raw-stock information as the drawing supports without
turning a missing field into a reason to discard unrelated valid fields. Keep
the current restrained results UI and make rare drawing-specified stock
callouts first-class recommendations.

## Approved behavior

### Preserve useful partial results

- Resolve and return material, geometry, stock form, and applicable dimensions
  independently.
- A missing overall length must not suppress a resolved thickness, width,
  material, or stock form.
- If focused length recovery fails, return the useful partial result rather
  than treating the entire analysis as a failure.
- An unknown dimension is not evidence that custom stock is required. Custom
  stock requires a known requirement that does not fit the approved common
  stock defaults.

### Preserve the existing UI treatment

- Default to the existing result-ticket UI.
- Use the existing empty-field or em-dash treatment for unavailable values.
- Do not add red or yellow flags, warning badges, error colors, or an
  error-heavy presentation for an otherwise useful partial result.
- Show an error only when no stock recommendation can be returned.
- A concise neutral explanatory sentence may remain where the existing UI
  already uses one.
- The user-facing result must display stock dimensions only. Finished-part
  dimensions may be used internally for calculation and validation but must
  never be added to the result ticket.

### Add focused recovery for overall length

- The initial Sol geometry read continues to attempt every applicable bounding
  dimension.
- When overall length is missing, the conditional focused Sol pass must be
  allowed to attempt that axis for both Flat and Round geometry.
- Recovery means rereading focused, high-resolution regions rendered from the
  uploaded PDF. It must not replace a missing value with an expected answer
  from `part-prints/print-index.md`.
- A recovered value may fill only a previously unresolved field. It must not
  overwrite an already accepted dimension.
- A failed recovery attempt leaves length unresolved and preserves every other
  valid result.

### Keep the approved Flat Bar versus Plate rule

`FLAT` remains the broad geometry category. The purchasing form remains a
deterministic decision based on the adjusted thickness and width.

Use the existing approved order:

1. If an approved common `Thk x W` flat-bar pair contains the required section,
   return Flat Bar.
2. If no pair fits and `W <= 2 x Thk`, return an approximate custom Flat Bar.
3. Otherwise, return Plate.
4. Equal sides are square bar and remain Flat Bar.

The `2:1` ratio is a fallback for custom dimensions outside the common
flat-bar table. It must not be moved ahead of the approved pair lookup.

Overall length does not change the Flat Bar versus Plate taxonomy. It remains
important for stock length, cut length, drop selection, bar yield, and whether
the recommendation is complete.

### Honor explicit drawing-specified stock

An explicit stock-size callout is unusual. When the drawing supplies a
complete, internally consistent stock callout with no known containment
conflict:

- Use it as the primary stock recommendation instead of the generic common
  stock lookup result.
- Preserve the drawing-specified purchasing form, including `PLATE`.
- Populate the app's normal structured stock fields rather than displaying the
  callout only as prose.
- Format each dimension with the app's existing conventions.
- Add a concise neutral note explaining that the stock size is specified on
  the drawing.
- Keep the stock callout separate from finished-part dimensions internally.

Validate containment on every comparable resolved required axis. An unresolved
finished-part axis does not suppress an otherwise complete explicit stock
callout; focused recovery continues independently for that finished dimension.

If the drawing-specified stock is undersized, ambiguous, or conflicts with the
calculated required envelope, do not silently accept it. Preserve the evidence
and require review under the app's existing safety behavior.

Use the generic catalog-selection flow only when no complete, safe explicit
stock recommendation is available.

## Titan-400-Subplate acceptance case

Source drawing: `part-prints/Titan-400-Subplate.pdf`

The drawing contains the explicit callout:

`STOCK SIZE: 1.5" X 9.25" X 18.9" PLATE`

The customer-facing result must use the existing stock fields and formatting:

- Material: `6061-T6 Aluminum`
- Stock: `Plate`
- Stock Thk: `1-1/2 in`
- Stock W: `9-1/4 in`
- Stock L: `18.9 in`
- Neutral note: stock size is specified on the drawing

Do not display the finished-part size on the result ticket. The finished
`18.800 in` overall length remains an internal extraction and validation fact.
Length recovery should still attempt to resolve it because finished dimensions
support internal containment and dependent calculations.

## Required implementation checks

The future coding task should add or update deterministic offline tests for at
least these cases:

1. Titan's complete drawing stock callout produces Plate and the three expected
   formatted stock dimensions.
2. A complete, safe drawing stock callout takes precedence over a generic
   common-stock recommendation.
3. A complete explicit stock callout remains present when a finished-part axis
   is unresolved, while containment is checked on every comparable axis.
4. An undersized or conflicting drawing stock callout is not silently accepted.
5. Missing Flat length triggers one focused length-recovery attempt.
6. Missing Round length triggers one focused length-recovery attempt.
7. Failed length recovery preserves resolved material, form, and cross-section
   fields without producing a new UI error treatment.
8. Successful length recovery unlocks only the dependent length calculations.
9. Without an explicit stock callout, an approved flat-bar pair still wins
   before the `2:1` custom-size fallback.
10. The result ticket does not display finished-part dimensions or introduce
   unapproved styling.

Use fakes or fixtures for default model-client tests. Paid model evaluation
remains opt-in and must not become part of `make test`, `make lint`,
`make check`, or another default check.

## Non-goals

- Do not change machining-allowance values or arithmetic.
- Do not change the approved common-stock tables as part of this follow-up.
- Do not convert the form-selection policy to ratio-first.
- Do not redesign the results UI.
- Do not add new warning colors, badges, or error states for partial results.
- Do not display finished-part dimensions in the UI.
- Do not use `part-prints/print-index.md` to populate runtime answers.
- Do not add supplier integrations, live availability claims, or production
  readiness claims.
- Do not deploy or change production without explicit user approval.

## Likely implementation areas

Verify the current code before editing, but the expected seams are:

- `src/backend/clients/openai_vision.py`: conditional missing-axis selection and
  focused recovery merging.
- `src/backend/domain/pipeline.py`: explicit stock-callout precedence,
  containment validation, and dependent-output behavior.
- `src/backend/domain/stock.py`: preserve the approved pair-first selection and
  formatting conventions.
- `src/frontend/app/page.tsx`: preserve the current UI while presenting the
  structured drawing-specified stock result and neutral note.
- Backend and frontend tests covering the acceptance cases above.

## Prompt for the later coding task

> Read `AGENTS.md`, `memory.md`, and
> `docs/stock-recommendation-decisions.md`. Implement the approved
> stock-recommendation changes exactly as documented. Preserve the existing UI
> and pair-first Flat Bar/Plate logic. Add proportionate offline tests, verify
> the Titan-400-Subplate acceptance case, and do not deploy or change
> production without my explicit approval.
