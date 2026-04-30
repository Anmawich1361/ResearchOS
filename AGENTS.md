# AGENTS.md

## Project identity

ResearchOS / Financial Research OS is an agentic financial research workbench and macro-transmission research demo.

It helps users understand how a macro, policy, industry, or narrative shock flows into sector/company fundamentals and valuation drivers.

It is not:

- a stock picker
- a trading terminal
- an investment-advice product
- a generic chatbot

The product should feel like a research command center: structured, visual, source-aware, and reliable.

## Core product constraints

These constraints are non-negotiable:

- Do not add buy/sell recommendations.
- Do not add price targets.
- Do not imply personalized investment advice.
- Preserve deterministic fallback behavior.
- Preserve the existing evidence labels exactly:
  - Data
  - Source claim
  - Framework inference
  - Narrative signal
  - Open question
- Avoid changing the `/research/run` response schema unless the task explicitly requires it.
- Avoid frontend changes unless the task explicitly requires them.
- Prefer small, reviewable PRs over broad multi-feature PRs.
- Do not remove or weaken the golden-path demo behavior.
- Do not rely on live external APIs for app correctness.
- Any live-data integration must fall back safely to deterministic demo data.

## Current architecture

Repo structure:

- `frontend/`
  - Next.js
  - TypeScript
  - Tailwind
  - shadcn-style components
  - React Flow
  - Recharts
- `backend/`
  - Python
  - FastAPI
  - Pydantic
  - Uvicorn
- `docs/`
  - Deployment notes
  - Workflow notes
  - Project documentation

Deployment:

- Backend is deployed on Render.
- Frontend is deployed on Vercel.
- Frontend calls backend using `NEXT_PUBLIC_API_BASE_URL`.
- Backend CORS is configured with `ALLOWED_ORIGINS` and `ALLOWED_ORIGIN_REGEX`.

## Strategic project documents

For product, architecture, or agentic-research changes, consult
`docs/project-strategy.md`, `docs/agentic-research-roadmap.md`, and
`docs/reflection-log.md`. If these docs conflict with `AGENTS.md`, `AGENTS.md`
wins.

For meaningful product or architecture changes, update the relevant strategy
docs or add a reflection-log entry. Do not require reflection-log updates for
tiny typo fixes or narrow docs-only PRs.

## Parallel implementation preflight

Before implementation edits, Codex must read `docs/codex-app-worktrees.md` and
complete this preflight:

1. Check the current branch and working tree. Use a clean worktree when local
   changes are unrelated.
2. Identify the files likely to be modified and files that are explicitly
   off-limits.
3. Check open PRs, active Codex threads, and known team notes for overlapping
   ownership.
4. Avoid overlapping files unless the user explicitly instructs it or the
   active owner coordinates the split.
5. Proceed with the smallest scoped change that satisfies the task.
6. For implementation work, open or update a draft PR early and keep its
   `Active Work Scope` block current so it acts as the live ownership record.

Use this block in implementation draft PR descriptions and coordination notes:

```markdown
## Active Work Scope

- Branch:
- Worktree:
- Mode: review-only | docs-only | implementation
- Goal:
- Currently touched files:
- Files/directories expected to edit:
- Files/directories explicitly off-limits:
- Safe areas:
- ResearchOS work zone: green | yellow | red
- Protected surfaces touched:
  - /research/run behavior: yes/no
  - ResearchRun schema: yes/no
  - Evidence labels: yes/no
  - Deterministic fallback behavior: yes/no
  - Frontend/backend contract: yes/no
- Overlap checked against open PRs/active notes: yes/no
- PR scope/non-goals:
```

Protected ResearchOS areas require explicit coordination before edits:

- `/research/run` behavior.
- `ResearchRun` schema and frontend/backend response contracts.
- Deterministic fallback behavior, including golden-path and unknown/custom
  question fallback.
- Evidence labels, which must remain exactly: `Data`, `Source claim`,
  `Framework inference`, `Narrative signal`, and `Open question`.
- The product boundary against buy/sell recommendations, price targets, and
  personalized investment advice.
- Any file or directory already declared by another active Codex session.

Review-only tasks may inspect the whole repo and run read-only commands, but
must not modify files, stage changes, commit, push, merge, or open
implementation PRs. If review finds a needed fix, hand it off as a separate
scoped implementation task.

## Current backend behavior

The backend supports deterministic golden-path demos for:

1. `How would rate cuts affect Canadian banks?`
2. `What happens to airlines if oil prices rise while consumer demand weakens?`
3. `Is AI capex becoming a risk for semiconductors and hyperscalers?`

Unknown or custom questions intentionally fall back to the Canadian banks demo for reliability.

Do not change this fallback behavior unless explicitly instructed.

## Backend development rules

Before changing backend behavior:

1. Read `README.md`.
2. Read `backend/README.md` if it exists.
3. Inspect `backend/app/orchestrator.py`.
4. Inspect `backend/app/schemas.py` or `backend/app/schemas/`, depending on the current schema layout.
5. Inspect existing tests before adding new ones.

Use standard-library Python where reasonable.

Avoid adding new production dependencies unless the task explicitly requires them.

For external data clients:

- Use timeouts.
- Avoid disabling TLS verification.
- Cache successful responses when appropriate.
- Add failure cooldown or backoff when appropriate.
- Return deterministic fallback data when live data fails.
- Add fixture-based tests.
- Do not require live network access for tests.

Required backend checks when backend files change:

```bash
cd backend && python3 -m compileall app
```

If `backend/tests` exists, also run:

```bash
cd backend && python3 -m unittest discover -s tests
```

Run a backend orchestrator smoke test that covers all golden paths plus an unknown custom question:

```bash
cd backend && python3 - <<'PY'
from app.orchestrator import run_research_pipeline
from app.schemas import ResearchRunRequest

questions = [
    "How would rate cuts affect Canadian banks?",
    "What happens to airlines if oil prices rise while consumer demand weakens?",
    "Is AI capex becoming a risk for semiconductors and hyperscalers?",
    "Unknown custom question",
]

allowed_evidence_labels = {
    "Data",
    "Source claim",
    "Framework inference",
    "Narrative signal",
    "Open question",
}

for question in questions:
    run = run_research_pipeline(ResearchRunRequest(question=question))
    assert run.question == question
    assert run.transmissionNodes
    assert run.charts
    assert run.evidence

    for item in run.evidence:
        assert item.type in allowed_evidence_labels, item.type

print("backend orchestrator smoke test passed")
PY
```

Always run the whitespace and conflict-marker check before committing:

```bash
git diff --check
```

## Frontend development rules

Avoid frontend changes unless the task explicitly requires them.

Before changing frontend behavior:

1. Read `README.md`.
2. Inspect the relevant components, API helpers, and shared types.
3. Preserve the existing `/research/run` response contract unless the task explicitly requires a coordinated backend/frontend schema change.
4. Preserve deterministic frontend fallback behavior.
5. Preserve the golden-path demo experience.

Frontend changes should keep the product feeling like a research command center: structured, visual, source-aware, and reliable.

Do not turn the product into:

- a generic chatbot interface
- a trading terminal
- an investment recommendation page
- a market-data dashboard without research workflow context

When frontend files change, run the applicable checks from `frontend/package.json`, typically:

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

If local dependency, cache, or file-watcher issues block these commands, report the exact command and error.

## Git and PR rules

- Work on the branch requested by the task.
- Do not push directly to `main` unless explicitly instructed.
- Keep changes scoped to the task.
- Do not mix documentation-only changes with runtime behavior changes.
- Do not stage unrelated user changes.
- Prefer explicit paths when staging files.
- Keep commits small, descriptive, and reviewable.
- Do not include stale PR numbers, temporary commit SHAs, local paths, or machine-specific details in documentation.
- If the worktree already contains unrelated changes, leave them untouched and report them separately.

## PR reporting requirements

When finishing a change, report:

- PR link, if one exists or was created
- branch name
- commit SHA
- files changed
- checks run
- known issues or blockers

For documentation-only changes, explicitly state that no backend or frontend runtime behavior changed.

## Review checklist

Before asking for review, confirm:

- The task scope was followed.
- Only intended files changed.
- Evidence labels remain exactly unchanged.
- `/research/run` schema was not changed unless explicitly required.
- Golden-path demo behavior was not removed or weakened.
- Unknown/custom-question fallback behavior was not removed or weakened.
- Live API failures cannot break app correctness.
- Required checks were run, or blockers were reported with exact errors.
- Documentation does not contain stale PR numbers, temporary SHAs, local-only assumptions, or hidden formatting characters.

## Review guidelines

Codex reviewers should prioritize ResearchOS product constraints and regression risks over general style preferences.

For product and runtime changes, focus review on:

- new buy/sell recommendations
- price targets
- personalized investment-advice behavior
- deterministic fallback regressions
- live external APIs becoming required for correctness
- accidental `/research/run` schema changes
- frontend/backend contract mismatches
- evidence label drift
- golden-path demo regressions
- unknown/custom-question fallback regressions
- missing tests for backend behavior changes
- external data-source clients missing timeout, fallback, or fixture tests
- tests requiring live network access
- unnecessary production dependencies
- broad scope creep

For documentation-only changes, verify:

- no backend or frontend runtime behavior changed
- docs do not contradict `AGENTS.md` or deployment docs
- docs do not include stale PR numbers, temporary SHAs, or machine-specific paths

Do not block PRs for pure style preferences unless the style issue creates ambiguity, weakens reviewability, or increases regression risk.

## Definition of done

A change is done when:

- The implementation or documentation addresses the requested task.
- The diff is scoped and reviewable.
- Required validation has passed, or any blocker is clearly reported.
- Backend and frontend behavior remain unchanged for documentation-only tasks.
- The branch is ready for PR review or has been pushed to the requested PR branch.
- The final report includes branch, commit, files changed, checks, and known issues.

## Known anti-patterns

Avoid these:

- Adding buy/sell calls, price targets, or personalized investment advice.
- Changing fallback behavior while working on unrelated tasks.
- Renaming evidence labels or adding near-duplicate labels.
- Changing `/research/run` schema casually.
- Adding live API dependencies without deterministic fallback.
- Requiring network access in tests.
- Disabling TLS verification to make an integration pass.
- Combining frontend redesign, backend refactor, and data integration in one broad PR.
- Replacing the research workflow with a generic chat experience.
- Removing the Canadian banks golden path or making it less reliable.
- Committing unrelated local files or generated artifacts.
