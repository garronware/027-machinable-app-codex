# Machinable Build Week evidence

## Status and authority

This is the sole repository record for Build Week provenance, dated development
evidence, compliance status, and submission blockers. It records verified facts
and distinguishes committed work from uncommitted working-tree work.

The [official rules](https://openai.devpost.com/rules) and
[challenge page](https://openai.devpost.com/) are authoritative if this record
conflicts with them. They were last checked on July 21, 2026.

Evidence entries are append-only except for clearly labeled factual
corrections. A plan, file timestamp, or Codex statement alone is not proof that
functionality works.

## Competition window

- Submission period: July 13, 2026 at 9:00 a.m. Pacific through July 21, 2026
  at 5:00 p.m. Pacific.
- Judging period: July 22, 2026 at 10:00 a.m. Pacific through August 5, 2026 at
  5:00 p.m. Pacific.
- Submission category: Work & Productivity.
- Project treatment: meaningful extension of a pre-existing project.

## Provenance classifications

Every material capability uses one of these classifications:

- **Pre-existing and reused:** carried forward without a meaningful new
  capability claim.
- **Pre-existing and materially modified:** an earlier capability exists, but
  Build Week work substantially changes how it works or what it can do.
- **Newly created during Build Week:** no equivalent capability existed in the
  pre-window baseline.
- **Planned but not implemented:** design intent only; it must not appear in a
  shipped-feature claim or demo narration.

## Pre-Build Week baseline

The source project is the local `015-machinable-app` repository. The latest
verified commit before the submission window is `bcc229d`, dated July 11, 2026.
The user must attest to ownership and any right to publish reused data or
assets; the local path alone is not proof of publication rights.

Capabilities present before the submission window included:

- a Python/FastAPI drawing-analysis pipeline;
- Werk24 and Anthropic/Claude drawing interpretation;
- deterministic machining allowance, unit conversion, stock selection,
  cut/drop length, saw kerf, end trim, and bar-yield logic;
- flat and round stock-reference CSV files;
- an Expo/React Native interface;
- private drawing fixtures and evaluation outputs; and
- dimensional evaluation work with multiple historical truth surfaces.

Project 027 is an independent Git repository created during the submission
window. It selectively ports earlier work. A file created in 027 during Build
Week is not automatically classified as new if its behavior or data came from
015.

## Capability comparison

| Capability | Before Build Week | Current 027 result | Classification | Evidence/status |
|---|---|---|---|---|
| Drawing perception | Werk24 plus Anthropic/Claude paths | Symmetric GPT-5.6 Sol High and Terra High readers using one contract | Pre-existing and materially modified | Implemented and offline-tested in working tree; not yet committed or controlled live-evaluated |
| Result failure behavior | Pipeline-level/global failure could erase useful fields | Field-level arbitration returns useful partial results and blocks only dependents | Pre-existing and materially modified | Offline API and arbitration tests pass; uncommitted |
| PDF evidence | Provider/model output was primary evidence | Text tokens, coordinates, numeric witnesses, page rendering, and claim checks | Newly created during Build Week | Synthetic-PDF tests pass; uncommitted |
| Material interpretation | Provider-shaped interpretation and broad substitutions | Conservative explicit-grade resolution, supplier language, and unresolved proprietary codes | Pre-existing and materially modified | Offline material tests pass; uncommitted |
| Shop calculations | Deterministic allowance, stock lookup, cut/drop, kerf, trim, and yield | Ported into typed domain modules and gated by resolved dependencies | Pre-existing and materially modified | Earlier behavior ported; offline tests pass; uncommitted changes after bootstrap |
| Stock-reference CSVs | Flat and round reference data in 015 | Same CSV data under `data/stock/` | Pre-existing and reused | Byte-identical comparison previously verified |
| User correction | No typed correction-only server operation | `/recalculate` applies confirmed facts without rerunning the readers | Newly created during Build Week | Offline API tests pass; uncommitted |
| Interface | Expo/mobile ticket-style flow | Desktop Next.js split-view review interface | Pre-existing and materially modified | Production build, lint, and typecheck pass; uncommitted and not deployed |
| Dimensional evaluation truth | Historical duplicated/dirty truth surfaces | `part-prints/print-index.md` is the sole evaluation truth and never runtime input | Pre-existing and materially modified | Legacy consolidation commits plus 027 tests; local PDFs remain private |
| Deployment | No verified judge-accessible 027 deployment | Planned Vercel frontend and Railway backend | Planned but not implemented | No deployment URL verified |
| Controlled dual-reader evaluation | No Sol/Terra comparison | Planned same-case Sol, Terra, and agreement treatments | Planned but not implemented | Paid evaluation requires explicit approval |

## Dated development record

### July 20, 2026 — evaluation truth cleanup in the legacy project

- Classification: pre-existing and materially modified during Build Week.
- Previous behavior: the legacy project had multiple, inconsistent dimensional
  truth surfaces and scattered print fixtures.
- New behavior: legacy commits including `e51f008` consolidated the print
  corpus and made one index the dimensional evaluation truth; later July 20
  commits refined the index and fixture organization.
- Codex contribution: repository analysis and evaluation support occurred in
  earlier tasks, but this record does not claim a `/feedback` identifier.
- Risk: private drawings and local legacy changes are not authorized for public
  release merely because they were used for evaluation.

### July 21, 2026 — project 027 bootstrap

- Classification: mixed; each capability is classified in the comparison
  table above.
- Commit: `9cdeb98` (`feat: bootstrap Machinable build-week app`), committed at
  1:29:43 p.m. EDT.
- Previous behavior: development lived in the legacy 015 repository.
- New behavior: independent 027 repository with FastAPI, one GPT-5.6 Sol PDF
  reader, a strict structured contract, ported deterministic shop logic, an
  Expo reference client, offline tests, and private-file exclusions.
- Codex task: `019f80bf-25ba-7050-b676-0761f0b74e25`.
- Verification at commit handoff: clean worktree, secrets/private PDFs/local
  evaluation reports excluded, and 13 offline tests passing.
- Risk: a single bootstrap commit does not prove every added file was newly
  invented during Build Week.

### July 21, 2026 — dual-reader, evidence, partial-result, material, and web upgrade

- Classification: mixed materially modified and newly created capabilities as
  shown above.
- Previous behavior: one Sol reader, global uncertainty failure, no
  deterministic PDF witness, limited material detail, no correction-only API,
  and an Expo reference frontend.
- New behavior in the current working tree: independent Sol/Terra readers,
  field-level arbitration, PDF evidence, conservative material resolution,
  dependency blocking, `/recalculate`, and a Next.js desktop interface.
- User decisions: use symmetric readers; preserve useful partial results;
  retain deterministic shop math; make undersized stock the primary safety
  concern; use the approved desktop split view; exclude private drawings.
- Codex contribution: implementation, test construction, legacy-path analysis,
  prompt/schema consolidation, frontend migration, and documentation updates.
- Codex task: `019f80bf-25ba-7050-b676-0761f0b74e25`.
- Verification on July 21 at approximately 3:23 p.m. EDT: `make check` passed
  Ruff, ESLint, strict TypeScript, and 25 deterministic offline tests. `npm run
  build` completed successfully with Next.js 16.2.11.
- Commit: missing. All work after `9cdeb98` is still uncommitted at this entry.
- Risks: no controlled paid dual-reader evaluation; no deployment; offline
  tests do not represent 25 real drawing/model runs.

### July 21, 2026 — automatic documentation system

- Classification: newly created during Build Week.
- Previous behavior: product direction and current handoff existed, but there
  was no consolidated provenance/compliance record or recurring reconciler.
- New behavior: this evidence record, a submission draft, lean agent
  maintenance rules, README provenance, and a time-bounded documentation
  reconciler.
- Codex task: `019f85ca-a6bb-7483-bfdd-10eba95c5d18`.
- Commit: missing at this entry.
- Verification: documentation links and repository checks will be verified in
  the task handoff.
- Risk: automation can maintain repository evidence but cannot attest to user
  eligibility, authorize IP, upload a video, publish a repository, deploy the
  application, submit Devpost, or generate the required `/feedback` result on
  the user's behalf.

### July 21, 2026 — recurring evidence reconciliation

- Classification: pre-existing and reused documentation maintenance; no product
  capability was added or reclassified.
- Previous behavior: the working-tree evidence record already reported the
  current implementation and an earlier local verification.
- New behavior: none; this run independently reconfirmed the existing local
  verification and submission blockers.
- Codex contribution: recurring documentation reconciliation. No completed
  Codex-task result or `/feedback` Session ID is claimed by this entry.
- Commit: none. The only repository commit remains `9cdeb98`; the documented
  implementation and documentation changes remain uncommitted working-tree
  evidence.
- Verification at 4:01 p.m. EDT: `make check` passed Ruff, ESLint, strict
  TypeScript, and 25 deterministic offline tests. `npm run build` then
  completed successfully with Next.js 16.2.11. `git diff --check` passed, no
  Git remote was configured, and the tracked-file scan found environment
  templates only—no tracked PDF or saved evaluation-run path matched.
- Remaining blockers: controlled paid dual-reader evaluation, an authorized
  judge drawing or test path, repository access and license decisions,
  deployment, video, user attestations, and a real `/feedback` result remain
  unresolved.

### July 21, 2026 — material evidence outside the title block

- Classification: materially modified extraction and arbitration behavior.
- Previous behavior: the readers could disagree on the exact material wording
  when a material clause appeared in numbered drawing notes, leaving both the
  raw callout and its broader material class unresolved.
- New behavior: the shared drawing prompt explicitly searches the entire print,
  including numbered notes and specification blocks, preserves alternative
  material clauses and standards, and classifies their shared material family.
  Field arbitration can now resolve an independently agreed material class such
  as `TOOL_STEEL` while leaving disputed exact wording marked for review.
- Codex contribution: prompt clarification, field-level material-class
  arbitration, and focused regression tests.
- Commit: missing. The change is uncommitted at this entry.
- Verification: `make check` passed Ruff, ESLint, strict TypeScript, and 27
  deterministic offline tests; `git diff --check` passed.
- Remaining risk: the same authorized PDF must be rerun through the live model
  path. Exact material wording still requires review when the readers disagree,
  and no controlled paid corpus evaluation has been completed.

### July 21, 2026 — factual correction: material identity normalization

- Correction to the immediately preceding entry: final behavior does not make
  equivalent raw wording a customer-facing conflict. Deterministic resolution
  compares recognized grades across both reader candidates despite punctuation,
  spacing, abbreviation, and standard-format variations.
- Customer-facing behavior: the API and desktop UI return a specific normalized
  identity such as `A2 Tool Steel`. The broader `TOOL_STEEL` classification is
  retained only as an internal machining-allowance input and is no longer shown
  as a customer field.
- Safety behavior: the decisive normalized grade and condition must still be
  supported by the PDF text evidence; genuinely different or unsupported grades
  remain unresolved.
- Commit: missing. The change is uncommitted at this entry.
- Verification: Ruff, ESLint, strict TypeScript, and 29 deterministic offline
  tests passed. The same authorized PDF still needs a live rerun.

### July 21, 2026 — stock recommendation completion and display

- Classification: materially modified orchestration and desktop presentation.
- Previous behavior: shape-inapplicable dimensions appeared as missing errors;
  the stock recommendation or its blocked state was placed below the full fact
  review; and a dual-dimension reader disagreement could block deterministic
  stock sizing despite an explicit primary-unit statement in the PDF.
- New behavior: flat parts show diameter as not applicable; ordinary round
  parts show thickness and width as not applicable; the order recommendation is
  the first result under the analysis header; and explicit PDF text such as
  `DIMENSIONS ARE IN INCHES` resolves primary units while retaining reader
  candidates and normalizing the accepted dimension values to those units.
- Preserved behavior: deterministic Python still adds material-specific
  machining allowance, selects the smallest containing common stock size, and
  calculates cut length, drop length, and 12-foot bar yield.
- Commit: missing. The change is uncommitted at this entry.
- Verification: Ruff, ESLint, strict TypeScript, `git diff --check`, and 30
  deterministic offline tests passed. No additional paid model call was made.
- Remaining risk: rerun the authorized live drawing to confirm the updated
  result presentation with real Sol and Terra output.

### July 21, 2026 — outlined-text PDFs and confirmation-to-stock handoff

- Classification: materially modified validation and completion UX.
- Previous behavior: a digitally generated vector PDF with outlined lettering
  produced zero searchable text tokens. Text-only validation then rejected
  otherwise usable visual-reader fields, preventing the preserved machining and
  stock scripts from running. Candidate values were visible but had no clear
  confirmation action when a required field genuinely remained disputed.
- New behavior: an absent searchable text layer is recorded as a validation
  limitation rather than evidence that the visual readers are wrong. A2 is
  normalized as the customer purchasing identity when an explicit material
  clause permits broad high-speed tool-steel alternatives or A2. When a true
  required-field disagreement remains, the desktop UI names the exact blocker
  and offers one explicit confirmation action that runs `/recalculate` without
  another model call.
- Preserved behavior: unconfirmed disputed dimensions never flow silently into
  purchasing output; confirmed facts use the existing deterministic allowance,
  common-stock lookup, cut-length, drop-length, and bar-yield sequence.
- Commit: missing. The change is uncommitted at this entry.
- Verification: Ruff, ESLint, strict TypeScript, `git diff --check`, and 32
  deterministic offline tests passed. The known 0.378-inch by 1.5625-inch A2
  case deterministically selects 9/16-inch round bar cut to 1.688 inches.
- Remaining risk: the authorized PDF needs one live rerun to exercise the
  corrected no-text-layer path and, if the readers still disagree on diameter,
  the explicit user-confirmation path.

### July 21, 2026 — factual correction: recalculation is not verification

- Correction to the preceding entry: calculating stock from displayed or
  edited browser values does not prove that the user verified those values
  against the drawing.
- Corrected behavior: recalculated output is labeled `Unverified estimate`,
  participating fields are labeled `Used for calculation`, and the API warning
  says the values are browser-supplied and still require drawing verification.
- Deferred: a future explicit verification control may record actual machinist
  attestation. The MVP does not claim that attestation occurred.
- Verification: Ruff, ESLint, strict TypeScript, `git diff --check`, and 32
  deterministic offline tests passed. The change is uncommitted.

### July 21, 2026 — deployment preparation

- Classification: newly created deployment packaging and materially updated
  handoff documentation.
- New behavior: the repository contains a minimal Railway backend `Dockerfile`,
  a `.dockerignore` that excludes secrets and private drawings, and exact
  Railway/Vercel environment-variable instructions.
- Verification: the Next.js production build passed; Ruff, ESLint, strict
  TypeScript, 32 deterministic offline tests, tracked-secret scanning, ignored
  private-drawing checks, and `git diff --check` passed.
- Skipped check: the container image was not built locally because Docker
  Desktop was not running. Railway deployment remains the first real container
  verification.
- Remaining work: commit and push, deploy Railway, verify `/health`, deploy
  Vercel, set exact cross-origin values, and complete one deployed PDF run.

### July 21, 2026 — repository checkpoint

- Commit `10c4a11` records the Build Week pilot implementation, desktop UI,
  offline tests, deployment packaging, and submission documentation described
  above.
- The commit excludes `.env`, private drawings, redacted evaluation copies,
  saved model runs, local build output, and dependency directories.
- Remaining work: publish the repository, deploy and verify both services, run
  one authorized end-to-end deployed drawing, and complete the submission.

### July 21, 2026 — GitHub publication checkpoint

- The committed `main` branch was pushed to
  `https://github.com/garronware/027-machinable-for-build-week`.
- Final pushed head before deployment is `e0d7435`; a later documentation-only
  commit may supersede that hash without changing application behavior.
- Remaining work: confirm unauthenticated judge access, deploy Railway and
  Vercel, verify cross-origin configuration, and run one authorized deployed
  drawing.

### July 21, 2026 — recurring evidence reconciliation at 5:28 p.m. EDT

- Classification: pre-existing and reused documentation maintenance; no product
  capability was added or reclassified by this reconciliation.
- Previous behavior: the working tree already contained the uncommitted
  material-evidence and normalized-material-identity changes recorded above.
- New behavior: none. This run independently verified the current offline
  working-tree state and preserved its uncommitted status.
- Codex contribution: recurring documentation reconciliation. The completed
  task-history lookup did not return before its read timeout, so this entry
  makes no completed-task claim and does not treat any raw task ID as a
  `/feedback` result.
- Commit: none. The only repository commit remains `9cdeb98`; all newer
  implementation and documentation work remains uncommitted working-tree
  evidence.
- Verification at 5:28 p.m. EDT: `make check` passed Ruff, ESLint, strict
  TypeScript, and 29 deterministic offline tests (with five PyMuPDF-related
  deprecation warnings). `git diff --check` passed. No Git remote is
  configured, and the tracked-file scan found no PDF, saved evaluation-run, or
  `.env` path.
- Remaining blockers: controlled paid dual-reader evaluation, an authorized
  judge drawing or test path, repository access and license decisions,
  deployment, video, user attestations, and a real `/feedback` result remain
  unresolved.

### July 21, 2026 — recurring evidence reconciliation at 5:59 p.m. EDT

- Classification: pre-existing and reused documentation maintenance; this
  reconciliation added no product capability or provenance reclassification.
- Previous behavior: the repository already contained the uncommitted
  outlined-text validation and confirmation-to-stock changes recorded above.
- New behavior: none. This run independently verified the current local
  working tree and preserved its uncommitted status.
- Codex contribution: recurring documentation reconciliation. The completed
  task-history lookup did not return before its read timeout, so this entry
  makes no completed-task claim and does not treat a raw task ID as a
  `/feedback` result.
- Commit: none. The only repository commit remains `9cdeb98`; all newer
  implementation and documentation work remains uncommitted working-tree
  evidence.
- Verification at 5:59 p.m. EDT: `make check` passed Ruff, ESLint, strict
  TypeScript, and 32 deterministic offline tests (with five PyMuPDF-related
  deprecation warnings). `npm run build` completed successfully with Next.js
  16.2.11. `git diff --check` passed. No Git remote is configured, and the
  tracked-file scan found only `.env.example` templates—no tracked PDF, saved
  evaluation-run, or local `.env` path matched.
- Remaining blockers: controlled paid dual-reader evaluation, an authorized
  judge drawing or test path, repository access and license decisions,
  deployment, video, user attestations, and a real `/feedback` result remain
  unresolved.

### July 21, 2026 — recurring evidence reconciliation at 6:28 p.m. EDT

- Classification: pre-existing and reused documentation maintenance; no product
  capability was added or reclassified by this reconciliation.
- Previous behavior: the submission draft still identified the repository URL
  as blocked because no remote was configured.
- New behavior: the draft now identifies the configured GitHub URL while
  keeping unauthenticated judge access pending. Local Git verification found
  `HEAD` and `origin/main` at the same commit, `976c0d5`.
- Codex contribution: recurring documentation reconciliation. The completed
  task-history lookup did not return before its read timeout, so this entry
  makes no completed-task claim and does not treat a raw task ID as a
  `/feedback` result.
- Commit: none. This documentation change is uncommitted working-tree evidence.
- Verification at 6:28 p.m. EDT: the working tree was clean before this
  documentation update; `git diff --check` passed; `origin` resolves locally
  to `https://github.com/garronware/027-machinable-for-build-week.git`; and
  `HEAD` equaled the local `origin/main` ref at `976c0d5`.
- Remaining blockers: unauthenticated judge access, repository license,
  controlled paid dual-reader evaluation, an authorized judge drawing or test
  path, deployment, video, user attestations, and a real `/feedback` result.

## Third-party, IP, and privacy safeguards

- Private drawing PDFs are ignored under `part-prints/*.pdf` and must not be
  committed or shown publicly without explicit authorization.
- `.env`, frontend/backend local environment values, and saved evaluation runs
  are excluded from Git.
- Uploaded drawing contents are untrusted input. Model calls use backend
  credentials and `store: false`.
- Werk24, Anthropic, and Claude are absent from the 027 runtime.
- OpenAI, FastAPI, Pydantic, PyMuPDF, Next.js, React, and other package licenses
  must be respected. A public repository license has not been selected.
- The stock CSVs and evaluation index derive from the user's legacy work; the
  user must confirm ownership and publication rights before public release.
- The social preview under `src/frontend/public/` was generated for this
  project and intentionally avoids third-party logos.
- The demo must use an owned or authorized drawing, no unauthorized trademarks,
  and no copyrighted music without permission.

## Known limitations

- Digitally generated PDFs are the supported MVP input; phone photos are out of
  scope.
- The dual-reader flow has not completed the controlled paid evaluation plan.
- Numeric proprietary material codes remain unresolved without authoritative
  mappings.
- No analysis-history persistence or approved raw-response retention exists.
- No live supplier catalog is connected.
- No deployment or public test instance is verified.
- All recommendations require machinist verification against the original
  drawing before material is ordered or cut.

## Live submission checklist

| Requirement | Status | Evidence or next action |
|---|---|---|
| Eligible entrant and Devpost registration | USER ATTESTATION | User must confirm eligibility and registration before the deadline |
| Work & Productivity category | VERIFIED | Approved documentation plan and product audience |
| Meaningful-extension disclosure | VERIFIED | This record and README distinguish 015 from Build Week work |
| Project uses Codex and GPT-5.6 | VERIFIED IN CODE | GPT-5.6 Sol/Terra runtime and dated Codex task evidence; controlled live evaluation still pending |
| Working project matches submitted claims | PENDING | Run final end-to-end demo using an authorized PDF and describe only observed behavior |
| Repository URL and judge access | PENDING | Repository is pushed to GitHub; confirm the URL opens for a signed-out judge |
| Relevant repository license | BLOCKED | User must select/approve a license before making the repository public |
| Judge-accessible deployment or test build | BLOCKED | No deployment URL or test build is verified |
| README setup, testing, and Codex collaboration | VERIFIED LOCALLY | README contains current instructions and provenance; judge access still depends on repository publication |
| Authorized sample/test drawing | BLOCKED | Private corpus is excluded; select an owned or authorized public sample |
| Public YouTube video under three minutes with audio | BLOCKED | Record and upload after final end-to-end verification |
| Video explains Codex and GPT-5.6 usage | PENDING | Use the reviewed storyboard in `submission-draft.md` |
| `/feedback` Codex Session ID | BLOCKED | Generate from the task where most core functionality was built; raw task IDs are not substitutes |
| Third-party APIs/data/assets authorized | USER ATTESTATION | Review package licenses, stock data rights, drawing permission, and demo assets |
| English submission materials | VERIFIED | Repository and draft materials are in English |
| Secrets/private drawings absent from tracked files | VERIFIED LOCALLY | Git ignore rules and tracked-file inspection; repeat before final commit/push |
| Final deterministic checks | VERIFIED LOCALLY | Equivalent checks passed with 32 tests; Next.js production build succeeded on July 21 |
| Submission completed by 5:00 p.m. PDT | BLOCKED | User must complete and submit the Devpost entry before the deadline |
