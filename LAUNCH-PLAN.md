# Machinable Application Launch Plan

## Goal

Keep the working Machinable application stable while adding `app.machinable.ai`. After the website design is approved, align the application's appearance with the website without changing print processing.

## Non-negotiable launch rule

Do not change application runtime code for the first domain launch.

Do not change:

- model selection;
- model prompts;
- reasoning effort;
- PDF upload or validation;
- analysis orchestration;
- bounding-dimension extraction or recovery;
- material extraction;
- stock calculations;
- correction and recalculation;
- response contracts;
- result rendering behavior; or
- backend routes.

The existing application works. The domain launch must preserve that behavior.

## Approved access decision

The first public version will use the current unrestricted application.

Do not add authentication, email verification, per-user limits, Redis, Turnstile, payment, manual approval, a quota hook, a kill switch, new application rate limits, or a one-click sample runner.

The existing enforced $25 monthly OpenAI cap is the temporary cost limit. The user accepts that one visitor could exhaust the cap and make new analyses unavailable until the cap resets or changes.

The centralized `/analyze` route gives a future implementation one place to add usage and abuse checks without rebuilding the model pipeline. Do not add those checks now.

## First launch scope

The application work for the first launch is limited to deployment configuration:

1. Record the current working commit and production deployment.
2. Verify the existing application URL with approved drawings.
3. Add `app.machinable.ai` to the existing Vercel application project.
4. Add Vercel's exact DNS and verification records in Cloudflare.
5. Add `https://app.machinable.ai` to Railway's `ALLOWED_ORIGINS` while preserving the current Vercel origin.
6. Verify the old and new application URLs with the same approved drawings.

Do not deploy new runtime code to accomplish these steps.

## Approved sample workflow

The marketing website will host a growing library of approved sample PDFs. A visitor will download a sample, open `app.machinable.ai`, and upload the PDF through the existing application flow.

The application will not receive special sample-selection logic during the first launch.

Keep `sample-dwg-1.pdf` and its public label `Sample Drawing 1`. The label does not determine display order on the website. Do not call it a trick drawing.

The verified values for that sample are:

- finished overall length: 5.567 inches;
- Machinable stock length: 5.692 inches.

## Design alignment follows website approval

The website will establish the shared Machinable visual system. Do not redesign the application while the website design is still changing.

The website may launch before the application receives visual changes. A temporary difference in appearance is safer than combining a domain launch with application code changes.

### Shared design specification

After the user approves the website, record the exact design choices in a short app-facing specification. Include:

- color values and their uses;
- font families and fallbacks;
- type sizes, weights, and line heights;
- spacing scale;
- content widths;
- border widths and colors;
- corner radii;
- button styles and states;
- input and upload-area styles and states;
- status, warning, error, and success colors;
- focus states;
- responsive breakpoints; and
- motion and reduced-motion behavior.

Use the website as the source of truth. Do not copy the website's page layout into the application when the application's workflow needs a different layout.

### Application surfaces to align

Change presentation only:

- global page background and text colors;
- Machinable wordmark and header;
- navigation or utility links;
- main content width and spacing;
- upload area;
- primary and secondary buttons;
- file metadata and validation messages;
- loading and analysis-progress states;
- PDF preview frame and controls;
- result headings and field labels;
- result values, evidence, warnings, and unresolved states;
- correction inputs and recalculation controls;
- expandable evidence sections;
- empty and error states;
- mobile behavior; and
- keyboard focus states.

Preserve the application's split-view workflow unless the user separately approves a structural redesign.

### Visual alignment does not mean identical pages

Match the brand elements that should feel shared:

- warm white, graphite, and muted cobalt;
- IBM Plex Sans and restrained mono labels;
- thin rules;
- square or lightly rounded controls;
- direct hierarchy;
- concise shop-floor language; and
- restrained movement.

Keep workflow-specific differences where they help a machinist review a drawing and result. The website sells and explains the product. The application helps a machinist upload, inspect, correct, and verify a result.

## Safe design-change sequence

1. Wait for explicit website design approval.
2. Record the application branch, commit, Vercel deployment, Railway deployment, and production URLs.
3. Capture desktop and mobile screenshots of every important application state.
4. Run the approved sample set and save the returned values, warnings, and screenshots as the functional baseline.
5. Create a separate branch for visual alignment.
6. Write the shared design specification from the approved website styles.
7. Map existing application components to the shared styles.
8. Change CSS, visual tokens, and presentation components in small commits.
9. Do not edit backend files, model prompts, calculation code, API contracts, or upload validation.
10. Run offline tests and strict frontend checks after each coherent group of changes.
11. Run the approved samples again only after the local visual work passes offline checks. Paid calls require explicit approval.
12. Compare the returned values and warnings with the saved baseline.
13. Deploy a Vercel preview, not production.
14. Test desktop, mobile, keyboard, upload, loading, error, correction, and result states on the preview.
15. Ask the user to approve the preview.
16. Merge and publish only after approval.

## Regression protection

Use these boundaries during visual alignment:

- Prefer existing CSS variables or add a small set of visual tokens.
- Keep data fetching and application state unchanged.
- Keep component props and API types unchanged unless a visual requirement makes a change necessary and the user approves it.
- Do not move calculations into frontend components.
- Do not rename API fields.
- Do not change when model calls run.
- Do not change success, partial-success, or failure rules.
- Do not hide safety warnings to make the screen cleaner.
- Do not reduce the original drawing's visibility.
- Keep manual correction and deterministic recalculation working.
- Make each commit easy to reverse.

## Required baseline states

Capture and retest:

- empty upload state;
- selected-file state;
- invalid-file state;
- oversized-file state;
- multi-page rejection if the current application rejects it;
- analysis loading state;
- complete result;
- partial result with unresolved fields;
- warning state;
- corrected result;
- recalculated result;
- backend error; and
- narrow-screen behavior.

Do not invent expected behavior. Record what the current application actually does before changing styles.

## Future abuse protection

Do not implement this section for the first launch.

If public usage or cost requires more control, add checks at the centralized `/analyze` route in separate, tested work. Possible layers include:

1. request logging and cost visibility;
2. a global server-side usage ceiling below the provider cap;
3. IP or browser-session throttling;
4. Turnstile;
5. email-based accounts and per-account successful-run limits; and
6. an owner bypass for normal use.

Keep failed validation and rejected files outside any future successful-run count. Design and test each layer separately so access control cannot silently break print processing.

## Production approval gates

Stop and ask the user before:

- changing runtime code;
- running paid model evaluations;
- deploying code;
- adding the Vercel production domain;
- changing Railway environment settings;
- changing Cloudflare DNS;
- changing production state;
- merging visual changes; or
- adding any usage-control layer.

## Definition of done

The domain launch is complete when:

- the existing application URL still works;
- `app.machinable.ai` works over HTTPS;
- Railway accepts both approved frontend origins;
- approved samples return the expected results from both URLs; and
- no runtime code changed.

The later visual alignment is complete when:

- the user has approved the shared design specification and preview;
- the application and website clearly belong to the same product;
- the upload and review workflow remains easy to use;
- approved sample results match the saved baseline;
- offline tests and frontend checks pass;
- accessibility and responsive checks pass; and
- no model, calculation, validation, or API behavior changed.
