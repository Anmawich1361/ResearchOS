# Codebase Review Backlog

This document tracks curated findings from full-codebase reviews of ResearchOS.
It is a backlog of code-review findings, not a live active-work ownership
registry. Active work ownership should remain in draft PR descriptions,
`Active Work Scope` blocks, task threads, and issue notes.

Backlog entries preserve review meaning, affected areas, overlap risk, and
suggested follow-up scope. They do not authorize broad implementation PRs.
Implementation work should still follow `AGENTS.md` and
`docs/codex-app-worktrees.md`.

## Status Definitions

- Open: confirmed or plausible finding awaiting a scoped follow-up.
- In progress: a scoped PR is actively addressing the finding.
- Fixed: the finding has been resolved and verified.
- Deferred: valid but intentionally lower priority or cleanup-oriented.
- False positive: reviewed and determined not to be an issue.

## Severity Definitions

- Blocker: must be fixed before the related work can safely proceed.
- Should fix: important correctness, safety, contract, reliability, testing, or
  maintainability issue.
- Defer: lower-priority cleanup or follow-up that should not interrupt higher
  risk work.
- False positive / non-issue: reviewed and determined not to require action.

## Overlap-Risk Definitions

- Red: overlaps an active PR or protected surface.
- Yellow: adjacent to a protected or recently changed area.
- Green: safe candidate for an independent scoped PR.

## Summary

| ID | Severity | Status | Area | Finding | Files | Overlap risk | Confidence | Follow-up PR |
|---|---|---|---|---|---|---|---|---|
| RBUG-001 | Should fix | In progress | Agentic safety | Advisory prompt variants bypass agentic preflight | `backend/app/agentic/safety.py` | Red | High | TBD |
| RBUG-002 | Should fix | Open | Agentic trust / frontend evidence display | Model-authored source claims can appear provenance-verified | `backend/app/agentic/models.py`, `frontend/components/EvidenceBoard.tsx` | Red | High | Wait for active agentic backend PR (#27 at creation time) |
| RBUG-003 | Should fix | Open | Agentic reliability | Agentic request path can block synchronously for too long | `backend/app/agentic/pipeline.py`, `backend/app/agentic/config.py` | Red | High | Wait for active agentic backend PR (#27 at creation time) |
| RBUG-004 | Should fix | Open | Frontend contract boundary | Frontend blindly trusts backend response shapes | `frontend/lib/api.ts`, `frontend/lib/types.ts` | Yellow | High | TBD |
| RBUG-005 | Should fix | Open | Frontend source observability | Source status marks healthy non-BoC runs as fallback | `frontend/components/ResearchDashboard.tsx`, `frontend/components/ResearchSourceStatus.tsx` | Yellow | High | TBD |
| RBUG-006 | Should fix | In progress | Frontend fallback state | Frontend fallback discards the submitted question | `frontend/components/ResearchDashboard.tsx` | Green | High | TBD |
| RBUG-007 | Should fix | Open | Agentic tests / network isolation | Backend tests still hide live BoC access | `backend/tests/test_agentic_eval_harness.py`, `backend/tests/test_agentic_safety.py` | Red | High | Wait for active agentic backend PR (#27 at creation time) |
| RBUG-008 | Defer | Deferred | Backend maintainability | Legacy deterministic agent modules duplicate unused pipeline logic | `backend/app/agents/` | Green | Medium | TBD |
| RBUG-009 | Defer | Deferred | Repo hygiene | Local generated or duplicate artifacts are easy to stage accidentally | local checkout hygiene, optional `.gitignore` follow-up | Green | High | TBD |

## Details

### RBUG-001 - Advisory prompt variants bypass agentic preflight

- Severity: Should fix
- Status: In progress
- Area: Agentic safety
- Files: `backend/app/agentic/safety.py`
- Affected behavior: Advisory prompts such as "Should I add Nvidia to my
  portfolio?", "Should I trim my Nvidia position?", "Which bank stock should I
  purchase?", "Is RY worth buying?", and "Should I take profits on Nvidia?" were
  not detected by `contains_forbidden_research_intent` in the completed review.
- Why it matters: A configured `/research/agentic-run` can proceed to OpenAI for
  advisory or personalized investment prompts that should fall back before any
  model call.
- Minimal suggested fix: Extend the forbidden advisory verb and phrase coverage
  for add, trim, purchase, worth buying, reduce exposure, take profits, and
  equivalent personal-position language.
- Suggested test coverage: Add unit, pipeline, and API tests asserting these
  prompts fall back before `OpenAIResearchClient` is constructed or called.
- Overlap risk: Red - protected agentic safety surface. PR #27 has landed, so
  this scoped follow-up can intentionally address only the preflight matcher.
- Confidence: High
- Source review note: Full-codebase review found direct false negatives in the
  agentic safety matcher.
- Follow-up PR: TBD

### RBUG-002 - Model-authored source claims can appear provenance-verified

- Severity: Should fix
- Status: Open
- Area: Agentic trust / frontend evidence display
- Files: `backend/app/agentic/models.py`, `frontend/components/EvidenceBoard.tsx`
- Affected behavior: Agentic `Source claim` labels, source types, and source
  quality scores are model-authored strings, then rendered as source metadata.
- Why it matters: Fabricated but plausible labels can look source-backed to users
  even though only `Data` evidence is currently rejected for unverified agentic
  output.
- Minimal suggested fix: Downgrade, mark, or suppress agentic source metadata as
  unverified unless independently captured provenance exists.
- Suggested test coverage: Add a spoofed `Source claim` with a plausible official
  source label and verify it is not rendered or treated as verified high-quality
  provenance.
- Overlap risk: Red - overlaps active agentic backend/runtime and source-trust
  work. Implementation should wait until PR #27 lands or coordinate with its
  owner.
- Confidence: High
- Source review note: Full-codebase review found that model-authored source notes
  can still be accepted and rendered as source metadata after `Data` evidence is
  rejected.
- Follow-up PR: TBD

### RBUG-003 - Agentic request path can block synchronously for too long

- Severity: Should fix
- Status: Open
- Area: Agentic reliability
- Files: `backend/app/agentic/pipeline.py`, `backend/app/agentic/config.py`
- Affected behavior: The configured agentic endpoint runs five sequential model
  calls inside one HTTP request, each with a default per-call timeout.
- Why it matters: Worst-case latency can exceed common frontend, hosting, or
  platform request limits before deterministic fallback is returned.
- Minimal suggested fix: Add a pipeline-level deadline or move configured
  agentic runs to async/background orchestration after the current beta path is
  safe.
- Suggested test coverage: Use a fake slow client to verify the pipeline returns
  deterministic fallback before the request-level budget is exceeded.
- Overlap risk: Red - overlaps active agentic backend/runtime work.
  Implementation should wait until PR #27 lands or coordinate with its owner.
- Confidence: High
- Source review note: Full-codebase review confirmed the synchronous staged
  pipeline still runs the model stages sequentially.
- Follow-up PR: TBD

### RBUG-004 - Frontend blindly trusts backend response shapes

- Severity: Should fix
- Status: Open
- Area: Frontend contract boundary
- Files: `frontend/lib/api.ts`, `frontend/lib/types.ts`
- Affected behavior: `response.json()` is cast directly to frontend types for
  run and status endpoints.
- Why it matters: Backend/frontend contract drift or malformed fallback payloads
  can reach rendering code instead of failing safely at the API boundary.
- Minimal suggested fix: Add lightweight runtime validators for `ResearchRun` and
  status payloads before returning typed objects from API helpers.
- Suggested test coverage: Invalid or missing required fields should throw from
  the API helper and activate existing frontend fallback handling.
- Overlap risk: Yellow - adjacent to the protected frontend/backend contract
  boundary.
- Confidence: High
- Source review note: Full-codebase review found direct casts in all frontend API
  helpers.
- Follow-up PR: TBD

### RBUG-005 - Source status marks healthy non-BoC runs as fallback

- Severity: Should fix
- Status: Open
- Area: Frontend source observability
- Files: `frontend/components/ResearchDashboard.tsx`,
  `frontend/components/ResearchSourceStatus.tsx`
- Affected behavior: After any completed run, no exact Bank of Canada Valet API
  marker becomes `fallback`, including oil, AI capex, and custom agentic runs.
- Why it matters: Healthy backend responses can look like source failure or
  deterministic fallback, which weakens source/fallback observability.
- Minimal suggested fix: Separate "official BoC data used", "deterministic demo
  series", "backend response without BoC data", and true unavailable/failure
  states.
- Suggested test coverage: Cover source-mode behavior for all three deterministic
  demos plus a custom agentic-style run without the Bank of Canada marker.
- Overlap risk: Yellow - touches frontend source/fallback observability near
  protected product-contract surfaces.
- Confidence: High
- Source review note: Full-codebase review found source mode is derived only from
  run completion plus exact BoC marker presence.
- Follow-up PR: TBD

### RBUG-006 - Frontend fallback discards the submitted question

- Severity: Should fix
- Status: In progress
- Area: Frontend fallback state
- Files: `frontend/components/ResearchDashboard.tsx`
- Affected behavior: On backend request failure, the UI resets both the run and
  the input question to the hardcoded Canadian-banks fixture.
- Why it matters: The UI hides the user's submitted question and differs from
  backend fallback behavior, which preserves `run.question`.
- Minimal suggested fix: Preserve the submitted question in UI state when using
  frontend fallback.
- Suggested test coverage: Simulate a failed API request and assert the submitted
  question remains visible.
- Overlap risk: Green - small frontend-only fix candidate.
- Confidence: High
- Source review note: Full-codebase review found the catch branch resets
  `question` to the frontend fixture question.
- Follow-up PR: TBD

### RBUG-007 - Backend tests still hide live BoC access

- Severity: Should fix
- Status: Open
- Area: Agentic tests / network isolation
- Files: `backend/tests/test_agentic_eval_harness.py`,
  `backend/tests/test_agentic_safety.py`
- Affected behavior: Some agentic tests call the canonical Canadian-banks
  pipeline without mocking the Bank of Canada fetch path.
- Why it matters: The test suite can silently attempt live Bank of Canada access,
  and deterministic fallback can make those tests pass anyway.
- Minimal suggested fix: Patch `fetch_policy_rate_chart` to return `None` in
  these tests or add a no-network guard for backend test discovery.
- Suggested test coverage: Add a no-network guard that fails if unmocked Bank of
  Canada access is attempted by tests outside the data-source fixture tests.
- Overlap risk: Red - touches active `backend/tests/test_agentic_*.py` files.
  Implementation should wait until PR #27 lands or coordinate with its owner.
- Confidence: High
- Source review note: Full-codebase review used a guarded test run and observed
  unmocked BoC access attempts while the suite still passed.
- Follow-up PR: TBD

### RBUG-008 - Legacy deterministic agent modules duplicate unused pipeline logic

- Severity: Defer
- Status: Deferred
- Area: Backend maintainability
- Files: `backend/app/agents/`
- Affected behavior: Legacy deterministic agent modules appear self-contained
  and not used by the current orchestrator.
- Why it matters: Duplicate fixture-oriented logic can mislead future changes or
  preserve stale assumptions.
- Minimal suggested fix: Remove the modules after confirming no import users, or
  explicitly mark them as legacy if they are intentionally retained.
- Suggested test coverage: Existing backend compile and contract tests should
  cover removal or documentation of the dead path.
- Overlap risk: Green - safe candidate for an independent cleanup PR when higher
  risk items are clear.
- Confidence: Medium
- Source review note: Full-codebase review found no active references from the
  current orchestrator path.
- Follow-up PR: TBD

### RBUG-009 - Local generated or duplicate artifacts are easy to stage accidentally

- Severity: Defer
- Status: Deferred
- Area: Repo hygiene
- Files: local checkout hygiene, optional `.gitignore` follow-up
- Affected behavior: The review observed local generated or duplicate artifacts
  in the checkout that were not part of tracked source.
- Why it matters: Future PRs could accidentally stage unrelated generated or
  duplicate files if the worktree is not isolated or cleaned first.
- Minimal suggested fix: Clean local artifacts outside PR scope and consider a
  narrow ignore-rule follow-up only for recurring generated artifact patterns.
- Suggested test coverage: Confirm `git status --short` is clean except for
  intentional branch work before staging future PRs.
- Overlap risk: Green - safe cleanup when done separately.
- Confidence: High
- Source review note: Full-codebase review treated this as checkout hygiene, not
  a tracked code defect.
- Follow-up PR: TBD

## Safe Fix Candidates

These findings looked suitable for small, independent follow-up PRs during the
completed review:

1. RBUG-006 - Preserve the submitted question on frontend fallback.
2. RBUG-004 - Add frontend API payload validation at the API boundary.
3. RBUG-005 - Clarify frontend source-status modes for non-BoC runs.

RBUG-004 and RBUG-005 are yellow-zone because they are adjacent to protected
frontend/backend contract and source/fallback observability surfaces. They
should stay small and include focused validation.

## Wait For Active PRs

These findings should wait for the active agentic backend/runtime PR to land or
should be coordinated with its owner:

1. RBUG-001 - Advisory prompt variants bypass agentic preflight.
2. RBUG-002 - Model-authored source claims can appear provenance-verified.
3. RBUG-003 - Agentic request path can block synchronously for too long.
4. RBUG-007 - Backend tests still hide live BoC access.

## Deferred / Cleanup

These findings are valid but lower priority than the safety, contract, and
observability issues above:

1. RBUG-008 - Legacy deterministic agent modules duplicate unused pipeline logic.
2. RBUG-009 - Local generated or duplicate artifacts are easy to stage
   accidentally.
