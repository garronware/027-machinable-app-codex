# Machinable Application Launch Checklist

Use this checklist in order. Update the boxes and notes as work proceeds. The first launch must not change runtime code.

## 1. Protect the working application

- [x] Confirm the repository path is `/Users/garronware/dev/my-repos/027-machinable-for-build-week`.
- [x] Read `AGENTS.md`, `README.md`, `LAUNCH-PLAN.md`, and `LAUNCH-CHECKLIST.md`.
- [x] Check Git status and preserve all existing user work.
- [x] Record the current branch and commit.
- [x] Record the current Vercel production URL and deployment.
- [x] Record the current Railway URL and deployment.
- [x] Record the current allowed frontend origins without exposing secrets.
- [x] Confirm the enforced OpenAI monthly cap is $25.
- [x] Do not change the OpenAI project or keys for this launch.

## 2. Verify the current baseline

- [x] Run the existing deterministic offline checks.
- [x] Do not run paid evaluations without approval.
- [x] Open the current production application.
- [x] Run the user-approved public sample.
- [x] Save the expected finished dimensions, returned stock recommendation, warnings, and screenshot.
- [x] Confirm `part_print_mm_in_round_29507460.pdf` has an expected 18.966 mm finished diameter and 121.5 mm finished length.
- [x] Confirm the current app returns 1215 Steel round bar, 7/8-inch stock diameter, and 4.908-inch cut length.
- [x] Report any mismatch before changing production configuration. No mismatch was found.

Stop if the current application is not working. Troubleshoot the existing deployment before adding a domain.

## 3. Confirm first-launch exclusions

- [x] Do not change application runtime code.
- [x] Do not change prompts, models, or reasoning effort.
- [x] Do not change upload validation or PDF processing.
- [x] Do not change bounding-dimension or stock calculations.
- [x] Do not add authentication or email verification.
- [x] Do not add per-user quotas.
- [x] Do not add Redis.
- [x] Do not add Turnstile.
- [x] Do not add a quota hook or kill switch.
- [x] Do not add new application rate limits.
- [x] Do not add payment.
- [x] Do not add a one-click sample runner.

## 4. Prepare the application domain

- [x] Inspect the existing Vercel application project without changing it.
- [x] Ask for approval before adding a production domain.
- [x] Add `app.machinable.ai` to the existing Vercel application project.
- [x] Copy Vercel's exact DNS and verification records.
- [x] Ask for approval before changing Cloudflare.
- [x] Add only Vercel's required records in Cloudflare.
- [x] Wait for Vercel to verify the domain.
- [x] Confirm HTTPS works.

## 5. Update the allowed origin

- [x] Record the current Railway `ALLOWED_ORIGINS` value.
- [x] Confirm the existing Vercel origin remains in the new value.
- [x] Add `https://app.machinable.ai`.
- [x] Ask for approval before changing Railway production settings.
- [x] Apply the approved setting.
- [x] Confirm the Railway backend remains healthy.
- [x] Confirm the old frontend origin still reaches the backend.
- [x] Confirm the new frontend origin reaches the backend.

## 6. Verify both application URLs

- [x] Load the existing Vercel application URL over HTTPS.
- [x] Load `https://app.machinable.ai` over HTTPS.
- [x] Test file selection and upload on both URLs.
- [x] Run the same approved samples on both URLs.
- [x] Compare dimensions, stock recommendations, and warnings with the baseline.
- [x] Confirm invalid and oversized files still behave as before.
- [ ] Confirm correction and recalculation still work in the production UI.
  The existing backend recalculation endpoint returns the expected deterministic
  result, but the existing frontend has no correction or recalculation controls.
  This pre-existing gap was recorded without changing runtime code.
- [x] Confirm no browser CORS errors appear.
- [x] Record the completed domain configuration.

The domain launch is complete. The first application launch remains open only
on the pre-existing correction-controls item above. Do not begin visual
alignment until the website design receives explicit approval.

## 7. Approve the shared visual system

- [ ] Obtain explicit approval of the website design.
- [ ] Record the exact website commit used as the visual source.
- [ ] Create an app-facing design specification from that approved commit.
- [ ] Record color values and uses.
- [ ] Record fonts, sizes, weights, and line heights.
- [ ] Record spacing, content widths, borders, and corner radii.
- [ ] Record button, input, upload, status, warning, and focus states.
- [ ] Record responsive breakpoints and motion rules.
- [ ] Obtain user approval of the design specification.

## 8. Capture the app before visual changes

- [ ] Create a separate visual-alignment branch.
- [ ] Capture the empty upload screen.
- [ ] Capture selected, invalid, and oversized file states.
- [ ] Capture the loading state.
- [ ] Capture a complete result.
- [ ] Capture a partial result with unresolved fields.
- [ ] Capture warnings and errors.
- [ ] Capture correction and recalculation.
- [ ] Capture desktop and narrow-screen layouts.
- [ ] Save the approved sample results as the functional baseline.

## 9. Map website styles to application surfaces

- [ ] Map the website background and text colors to the app shell.
- [ ] Map the wordmark and header treatment.
- [ ] Map typography to headings, labels, values, and supporting text.
- [ ] Map buttons and interaction states.
- [ ] Map inputs and the upload area.
- [ ] Map rules, panels, and content spacing.
- [ ] Map status, warning, error, and success colors without weakening meaning.
- [ ] Map focus states and reduced-motion behavior.
- [ ] Decide which split-view elements should remain app-specific.
- [ ] Ask the user before changing workflow structure.

## 10. Implement presentation changes safely

- [ ] Change visual tokens and CSS first.
- [ ] Keep changes in small, reversible commits.
- [ ] Do not edit backend files.
- [ ] Do not edit model prompts.
- [ ] Do not edit calculation code.
- [ ] Do not edit upload validation.
- [ ] Do not rename API fields.
- [ ] Do not change when model calls run.
- [ ] Keep complete, partial, warning, and error behavior unchanged.
- [ ] Keep the original drawing visible.
- [ ] Keep correction and recalculation available.
- [ ] Run offline tests and strict frontend checks after each coherent change.

## 11. Verify the visual-alignment branch

- [ ] Compare every required state with the before screenshots.
- [ ] Test desktop and narrow-screen layouts.
- [ ] Navigate every control with the keyboard.
- [ ] Confirm focus states remain visible.
- [ ] Check color contrast.
- [ ] Confirm screen-reader names and status messages.
- [ ] Check the browser console for errors.
- [ ] Run the complete deterministic offline test and lint suite.
- [ ] Ask for approval before any paid model calls.
- [ ] If approved, run the same public samples.
- [ ] Compare all returned values and warnings with the functional baseline.
- [ ] Stop and investigate any behavioral difference.

## 12. Preview and approve the aligned app

- [ ] Ask for approval before deploying a preview.
- [ ] Deploy the visual branch to a Vercel preview, not production.
- [ ] Test upload, loading, complete, partial, warning, error, correction, and recalculation states.
- [ ] Test desktop and mobile layouts.
- [ ] Present the preview to the user.
- [ ] Record requested changes.
- [ ] Make and verify approved revisions.
- [ ] Obtain explicit production approval.

## 13. Publish the aligned app

- [ ] Merge only the approved visual changes.
- [ ] Record the merge commit.
- [ ] Deploy to production.
- [ ] Verify the existing Vercel URL.
- [ ] Verify `https://app.machinable.ai`.
- [ ] Run the approved smoke-test samples.
- [ ] Confirm results match the baseline.
- [ ] Confirm the website and app share the approved brand system.
- [ ] Record any known visual limitations.

## Deferred abuse protection

- [x] Leave abuse protection unimplemented for the first launch.
- [ ] Revisit usage controls after observing real traffic and cost.
- [ ] Add future controls at `/analyze` in separate work.
- [ ] Test each future control independently from print processing.
- [ ] Provide an owner path that does not interfere with normal use.
- [ ] Make sure failed or rejected files do not consume a future successful-run allowance.

## Launch work log — 2026-08-24

- Baseline evidence: [`docs/launch/2026-08-24-launch-baseline.md`](docs/launch/2026-08-24-launch-baseline.md).
- Repository baseline: clean `main` at
  `9c002c60f95562f780e650ad1f953551503bec4f`, one commit ahead of
  `origin/main` before these checklist/evidence edits.
- Vercel baseline: production alias
  `https://027-machinable-for-build-week.vercel.app`, deployment
  `dpl_gQadZkDcSGHana6ivhnwZSqKsv9Q`, source commit
  `13d0fadd8a50de6a6754d1cae7d11ac78b930997`.
- Railway baseline: `https://machinable-api.up.railway.app`, active deployment
  `ff6b6640-83cb-405e-8056-fa04708ff729`, HTTP 200 health check, and
  `ALLOWED_ORIGINS=https://027-machinable-for-build-week.vercel.app`.
- CORS baseline: the existing Vercel origin passes preflight; the planned app
  origin is rejected until the approved Railway update.
- DNS baseline: `app.machinable.ai` has no A, AAAA, or CNAME record;
  `machinable.ai` uses Cloudflare nameservers.
- Offline verification: `make check` passed Ruff, ESLint, strict TypeScript,
  and 68 pytest tests. No paid evaluation ran.
- Production UI baseline: the empty upload state loaded over HTTPS without app
  console warnings or errors.
- Sample baseline: the user approved
  `part_print_mm_in_round_29507460.pdf` for this live test. The app returned
  1215 Steel, Round Bar, 7/8-inch stock diameter, 4.908-inch cut length, a
  1-foot drop length, and 28 parts per 12-foot bar, with no browser warnings or
  errors. The result matches the approved expected dimensions and deterministic
  allowance. Screenshot:
  [`docs/launch/2026-08-24-existing-production-sample-29507460.jpg`](docs/launch/2026-08-24-existing-production-sample-29507460.jpg).
- OpenAI cap: the user confirmed the enforced monthly limit is $25.
- Vercel domain change: after explicit approval, `app.machinable.ai` was added
  to the existing Vercel project. Vercel reports ownership verified and requires
  one DNS record: `A app.machinable.ai 76.76.21.21`. No separate verification
  record was requested.
- Post-Vercel check: the existing URL returned HTTP 200 and the approved sample
  returned the same 1215 Steel, 7/8-inch round-bar, and 4.908-inch cut-length
  result. The new address cannot resolve until Cloudflare is updated. Screenshot:
  [`docs/launch/2026-08-24-after-vercel-domain-old-url-sample-29507460.jpg`](docs/launch/2026-08-24-after-vercel-domain-old-url-sample-29507460.jpg).
- Cloudflare DNS change: after explicit approval, the single Vercel-requested
  DNS-only record `A app.machinable.ai 76.76.21.21` was added. Vercel verified
  the domain and generated its HTTPS certificate; the new address returns HTTP
  200 over HTTPS.
- Post-Cloudflare check: the existing address still returned the baseline
  sample result. The new address loaded and accepted file selection, but its
  analysis request was blocked as expected because the separately approval-gated
  Railway origin setting has not yet been changed. Screenshots:
  [`docs/launch/2026-08-24-after-cloudflare-old-url-sample-29507460.jpg`](docs/launch/2026-08-24-after-cloudflare-old-url-sample-29507460.jpg)
  and
  [`docs/launch/2026-08-24-after-cloudflare-new-url-sample-29507460.jpg`](docs/launch/2026-08-24-after-cloudflare-new-url-sample-29507460.jpg).
- Railway origin change: after explicit approval, `ALLOWED_ORIGINS` was changed
  to `https://027-machinable-for-build-week.vercel.app,https://app.machinable.ai`.
  The old address was preserved. Railway applied the setting using the same
  application source and activated deployment
  `f870dfeb-f39d-4435-96a7-d8cfe2cbcbaa`.
- Post-Railway checks: backend health returned HTTP 200; both exact origins
  passed the browser preflight check; both addresses analyzed the approved
  sample without browser warnings or errors and returned the baseline 1215
  Steel, 7/8-inch round-bar, 4.908-inch cut-length, 1-foot drop, and 28-part
  yield result. Screenshots:
  [`docs/launch/2026-08-24-after-railway-old-url-sample-29507460.jpg`](docs/launch/2026-08-24-after-railway-old-url-sample-29507460.jpg)
  and
  [`docs/launch/2026-08-24-after-railway-new-url-sample-29507460.jpg`](docs/launch/2026-08-24-after-railway-new-url-sample-29507460.jpg).
- Upload safety check: both addresses rejected a non-PDF with the existing
  digitally-generated-PDF message and rejected a 50-MB-plus PDF with the
  existing size-limit message. Temporary test files were deleted afterward.
- Existing behavior note: static review confirms no durable uploaded-PDF or
  raw-model-response persistence. It also found that `/recalculate` exists and
  passed a production smoke check using synthetic values without a PDF or model
  call, but the current frontend does not expose correction or recalculation
  controls. No runtime code was changed to address that existing discrepancy.
- Production changes: only the approved Vercel domain assignment, approved
  Cloudflare DNS record, and approved Railway origin setting were changed. No
  runtime application code changed.
- Final local verification: `make check` passed Ruff, ESLint, strict
  TypeScript, and all 68 offline tests after the configuration work.
