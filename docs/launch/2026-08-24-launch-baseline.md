# Machinable launch baseline — 2026-08-24

This record supports the first-domain launch checklist. No runtime code, model
configuration, deployment, or other external production state was changed
while collecting it.

## Repository

- Path: `/Users/garronware/dev/my-repos/027-machinable-for-build-week`
- Branch: `main`
- Working commit: `9c002c60f95562f780e650ad1f953551503bec4f`
- Commit subject: `docs: add launch and design alignment plan`
- Initial status: clean, with `main` one commit ahead of `origin/main`

## Current deployments

- Vercel project: `027-machinable-for-build-week`
- Vercel production URL:
  `https://027-machinable-for-build-week.vercel.app`
- Vercel production deployment: `dpl_gQadZkDcSGHana6ivhnwZSqKsv9Q`
- Vercel deployment URL:
  `https://027-machinable-for-build-week-q725u9rcw-garron.vercel.app`
- Vercel deployment source commit:
  `13d0fadd8a50de6a6754d1cae7d11ac78b930997`
- Railway production URL: `https://machinable-api.up.railway.app`
- Railway active deployment: `ff6b6640-83cb-405e-8056-fa04708ff729`
- Railway deployment source message:
  `fix: preserve bounds before shape inference`
- Railway health check: HTTP 200 with Sol `gpt-5.6-sol`, Terra
  `gpt-5.6-terra`, and digitally generated PDF scope.

## Current origin and DNS state

- Railway `ALLOWED_ORIGINS`:
  `https://027-machinable-for-build-week.vercel.app`
- Existing Vercel-origin preflight: HTTP 200 with the matching
  `Access-Control-Allow-Origin` header.
- Planned `https://app.machinable.ai` preflight: HTTP 400, `Disallowed CORS
  origin`, as expected before the approved Railway change.
- `app.machinable.ai` has no public A, AAAA, or CNAME record.
- `machinable.ai` uses Cloudflare nameservers `koa.ns.cloudflare.com` and
  `wanda.ns.cloudflare.com`.

## Verification

- `make check`: passed.
- Ruff: passed.
- Frontend ESLint: passed.
- Strict TypeScript: passed.
- Pytest: 68 passed with five SWIG-related deprecation warnings.
- Paid evaluation: not run.
- Existing production empty state: loaded over HTTPS without application
  console warnings or errors.
- Production `/recalculate` smoke check: HTTP 200 for synthetic confirmed
  values, with deterministic flat-stock output and the expected warning that
  drawing readers were not rerun. No PDF or model call was involved.
- Empty-state screenshot:
  [`2026-08-24-existing-production-empty.jpg`](2026-08-24-existing-production-empty.jpg)

## Approved sample baseline

- The user approved `part_print_mm_in_round_29507460.pdf` for live testing.
- Expected finished diameter: 18.966 mm / 0.7466 in.
- Expected finished length: 121.5 mm / 4.783 in.
- Expected material: 1215 Steel.
- Current live result: 1215 Steel, Round Bar, 7/8 in / 22.2 mm stock
  diameter, 4.908 in / 124.7 mm cut length, 1 ft / 304.8 mm drop length, and
  28 parts per 12-foot bar.
- The result matches the expected dimensions plus the deterministic 0.125-inch
  lathe allowance. No browser warning or error was recorded.
- Result screenshot:
  [`2026-08-24-existing-production-sample-29507460.jpg`](2026-08-24-existing-production-sample-29507460.jpg)

## Retention and flow review

- The application code keeps uploaded PDFs in request/browser memory and does
  not durably save them.
- Both original-PDF and focused-crop OpenAI calls use `store=False`.
- The application does not persist raw model responses.
- The checked-in backend exposes deterministic `/recalculate`, but the current
  frontend does not wire the correction/recalculation helper into the page.
  The production endpoint itself passed a synthetic smoke check. This existing
  UI discrepancy was recorded without changing runtime code.

## Approval gate before a domain change

- The user confirmed the enforced OpenAI monthly limit is $25.
- The available browser session is not signed in to Cloudflare. Vercel's exact
  DNS instructions can only be copied after the production domain is added,
  and the subsequent Cloudflare change remains separately approval-gated.

## Approved changes after baseline

- The user approved adding `app.machinable.ai` to the existing Vercel project.
- Vercel accepted the domain and reports ownership verified.
- Vercel's exact required DNS record is
  `A app.machinable.ai 76.76.21.21`.
- Vercel requested no additional ownership-verification record.
- After separate explicit approval, Cloudflare received only Vercel's requested
  DNS-only record: `A app.machinable.ai 76.76.21.21`.
- Vercel verified the record and generated the HTTPS certificate.
- Railway had not yet been changed at this checkpoint.
- After the Vercel change, the existing URL returned HTTP 200 and the approved
  sample returned the same 1215 Steel, Round Bar, 7/8-inch stock diameter, and
  4.908-inch cut length.
- `app.machinable.ai` still did not resolve, as expected before the Cloudflare
  record is added.
- Post-change old-URL screenshot:
  [`2026-08-24-after-vercel-domain-old-url-sample-29507460.jpg`](2026-08-24-after-vercel-domain-old-url-sample-29507460.jpg)
- After the Cloudflare change, both addresses loaded over HTTPS. The old address
  returned the same approved sample result. The new address accepted file
  selection but could not reach analysis because the separately approval-gated
  Railway origin setting still rejects it.
- Post-Cloudflare screenshots:
  [`2026-08-24-after-cloudflare-old-url-sample-29507460.jpg`](2026-08-24-after-cloudflare-old-url-sample-29507460.jpg)
  and
  [`2026-08-24-after-cloudflare-new-url-sample-29507460.jpg`](2026-08-24-after-cloudflare-new-url-sample-29507460.jpg)
- After separate explicit approval, Railway `ALLOWED_ORIGINS` was updated to
  `https://027-machinable-for-build-week.vercel.app,https://app.machinable.ai`.
  Railway activated setting-only deployment
  `f870dfeb-f39d-4435-96a7-d8cfe2cbcbaa` from the same application source.
- Railway health and both exact origin checks returned HTTP 200.
- Both addresses analyzed the approved sample and returned the baseline result
  with no browser warning or error. Final screenshots:
  [`2026-08-24-after-railway-old-url-sample-29507460.jpg`](2026-08-24-after-railway-old-url-sample-29507460.jpg)
  and
  [`2026-08-24-after-railway-new-url-sample-29507460.jpg`](2026-08-24-after-railway-new-url-sample-29507460.jpg)
- Both addresses rejected a non-PDF and a PDF over 50 MB with the existing
  validation messages. The temporary test files were deleted.
- The backend `/recalculate` endpoint still returned its expected deterministic
  result after the setting change. The production UI still has no correction
  controls, so that existing checklist gap remains open.
- Final local `make check` passed Ruff, ESLint, strict TypeScript, and all 68
  offline tests after the configuration work.
