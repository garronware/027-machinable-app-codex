# Machinable Application Launch Checklist

Use this checklist in order. Update the boxes and notes as work proceeds. The first launch must not change runtime code.

## 1. Protect the working application

- [ ] Confirm the repository path is `/Users/garronware/dev/my-repos/027-machinable-for-build-week`.
- [ ] Read `AGENTS.md`, `README.md`, `LAUNCH-PLAN.md`, and `LAUNCH-CHECKLIST.md`.
- [ ] Check Git status and preserve all existing user work.
- [ ] Record the current branch and commit.
- [ ] Record the current Vercel production URL and deployment.
- [ ] Record the current Railway URL and deployment.
- [ ] Record the current allowed frontend origins without exposing secrets.
- [ ] Confirm the enforced OpenAI monthly cap is $25.
- [ ] Do not change the OpenAI project or keys for this launch.

## 2. Verify the current baseline

- [ ] Run the existing deterministic offline checks.
- [ ] Do not run paid evaluations without approval.
- [ ] Open the current production application.
- [ ] Run each approved public sample.
- [ ] Save the returned dimensions, stock recommendation, warnings, and screenshots.
- [ ] Confirm `Sample Drawing 1` returns a 5.567-inch finished overall length.
- [ ] Confirm `Sample Drawing 1` returns a 5.692-inch stock length.
- [ ] Report any mismatch before changing production configuration.

Stop if the current application is not working. Troubleshoot the existing deployment before adding a domain.

## 3. Confirm first-launch exclusions

- [ ] Do not change application runtime code.
- [ ] Do not change prompts, models, or reasoning effort.
- [ ] Do not change upload validation or PDF processing.
- [ ] Do not change bounding-dimension or stock calculations.
- [ ] Do not add authentication or email verification.
- [ ] Do not add per-user quotas.
- [ ] Do not add Redis.
- [ ] Do not add Turnstile.
- [ ] Do not add a quota hook or kill switch.
- [ ] Do not add new application rate limits.
- [ ] Do not add payment.
- [ ] Do not add a one-click sample runner.

## 4. Prepare the application domain

- [ ] Inspect the existing Vercel application project without changing it.
- [ ] Ask for approval before adding a production domain.
- [ ] Add `app.machinable.ai` to the existing Vercel application project.
- [ ] Copy Vercel's exact DNS and verification records.
- [ ] Ask for approval before changing Cloudflare.
- [ ] Add only Vercel's required records in Cloudflare.
- [ ] Wait for Vercel to verify the domain.
- [ ] Confirm HTTPS works.

## 5. Update the allowed origin

- [ ] Record the current Railway `ALLOWED_ORIGINS` value.
- [ ] Confirm the existing Vercel origin remains in the new value.
- [ ] Add `https://app.machinable.ai`.
- [ ] Ask for approval before changing Railway production settings.
- [ ] Apply the approved setting.
- [ ] Confirm the Railway backend remains healthy.
- [ ] Confirm the old frontend origin still reaches the backend.
- [ ] Confirm the new frontend origin reaches the backend.

## 6. Verify both application URLs

- [ ] Load the existing Vercel application URL over HTTPS.
- [ ] Load `https://app.machinable.ai` over HTTPS.
- [ ] Test file selection and upload on both URLs.
- [ ] Run the same approved samples on both URLs.
- [ ] Compare dimensions, stock recommendations, and warnings with the baseline.
- [ ] Confirm invalid and oversized files still behave as before.
- [ ] Confirm correction and recalculation still work.
- [ ] Confirm no browser CORS errors appear.
- [ ] Record the completed domain configuration.

The first application launch is complete here. Do not begin visual alignment until the website design receives explicit approval.

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

- [ ] Leave abuse protection unimplemented for the first launch.
- [ ] Revisit usage controls after observing real traffic and cost.
- [ ] Add future controls at `/analyze` in separate work.
- [ ] Test each future control independently from print processing.
- [ ] Provide an owner path that does not interfere with normal use.
- [ ] Make sure failed or rejected files do not consume a future successful-run allowance.
