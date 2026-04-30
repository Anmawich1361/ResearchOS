# Codex App Worktree Workflow

## Purpose

Codex app can be used for local ResearchOS task execution, including
documentation updates, tests, and small scoped fixes. For unattended local work,
each task should be isolated in its own worktree and its own Codex app thread so
the diff remains scoped, reviewable, and easy to abandon if the task goes off
track.

This workflow is for local execution safety. It does not change the ResearchOS
product contract, deterministic fallback behavior, evidence labels, or
deployment process.

## Core Rule

One task. One worktree. One branch. One PR. No merge.

For parallel Codex work, the rule expands to:

- One implementation owner per active work zone.
- One active PR scope per Codex session.
- No edits to another active session's declared files without explicit
  coordination.
- Review-only sessions may inspect the whole codebase, but must not modify
  files.

## Pre-Flight Checklist

- Pull latest `main`.
- Confirm the repo is clean.
- Confirm there are no unrelated local changes.
- Use a separate worktree or separate Codex app task.
- Check open PRs, active Codex threads, and team notes for overlapping work.
- Share the status block below before starting work that could overlap another
  session.
- Keep the Mac awake if running locally.
- Do not close the laptop if it would stop the task.

## Parallel Session Status Block

Before overlapping work begins, every active Codex session should report this
status block in its task thread, issue, PR, or other shared coordination place:

```markdown
## Codex session status

- Session owner:
- Branch:
- Worktree:
- Mode: review-only | docs-only | implementation
- Objective:
- Files/directories expected to edit:
- Files/directories explicitly off-limits:
- ResearchOS work zone: green | yellow | red
- Contract surfaces touched:
  - /research/run behavior: yes/no
  - ResearchRun schema: yes/no
  - Evidence labels: yes/no
  - Deterministic fallback behavior: yes/no
  - Frontend/backend contract: yes/no
- Active dependencies or blockers:
- Checks planned:
- PR scope/non-goals:
```

If the expected edit set is unclear, pause before implementation and narrow the
task. If another session has declared ownership of the same files, coordinate
before editing or move the work to a follow-up PR.

## ResearchOS Work Zones

Use these zones to decide whether parallel work is safe.

### Green Zone

Green-zone work is usually safe to run in parallel when the worktree is clean
and the diff stays scoped.

- Narrow docs-only wording updates outside active feature docs.
- README or workflow clarifications that do not change product direction.
- Test-only additions for unchanged behavior, when no active session owns the
  same test files.
- Read-only audits, reviews, and architecture notes.

Green-zone implementation still needs its own branch, worktree, PR, and final
validation.

### Yellow Zone

Yellow-zone work can run in parallel only after the status block is shared and
the touched files are clearly disjoint from active sessions.

- Strategy, roadmap, deployment, or workflow docs that may affect future
  implementation.
- Tests near active backend or frontend work.
- Frontend copy or source-status UI that may affect product positioning.
- Data-source docs, verification scripts, or CI workflow changes.
- Changes near frontend/backend contract boundaries, even if they appear small.

Yellow-zone PRs should be small and should name the boundaries they intentionally
do not touch.

### Red Zone

Red-zone work requires explicit coordination before edits. Do not start these
changes in parallel with an active owner unless the owner confirms the file
split and PR order.

- `backend/app/agentic/`
- `backend/tests/test_agentic_*.py`
- `docs/agentic-research.md` when agentic backend work is active.
- Agentic diagnostic scripts, including `scripts/debug_agentic_local.sh` and
  `scripts/debug_agentic_openai_adapter.py`.
- `backend/requirements.txt`
- `/research/run` behavior.
- `ResearchRun` schema or frontend/backend response contracts.
- Deterministic fallback behavior, including unknown/custom-question fallback.
- Evidence label definitions or wording. The labels must remain exactly:
  `Data`, `Source claim`, `Framework inference`, `Narrative signal`, and
  `Open question`.
- Backend requirements, OpenAI transport, agentic diagnostics, prompt logic, or
  safety checks.
- Deployment/CORS changes.
- Any file already declared by another active Codex session.

If a red-zone edit is unavoidable, stop and create a coordination note before
changing files. Include the branch, intended file set, expected PR order, and
the exact contract surfaces that will remain unchanged.

## macOS Keep-Awake Command

Run this in a separate terminal before starting a long local Codex task:

```bash
caffeinate -dimsu
```

Stop it later with `Ctrl+C`.

## Safe Task Types

- Docs cleanup.
- Stale wording cleanup.
- Tests for existing behavior.
- Small bug fixes with clear acceptance criteria.
- Read-only audits that open issues or PRs.

## Unsafe Unattended Task Types

- Frontend redesign.
- New data-source integrations.
- Schema changes.
- Routing changes.
- Deployment/CORS changes.
- Broad refactors.
- Multiple dependent PRs.
- Anything requiring product judgment.

## Worktree Pattern

Create a fresh worktree from the current remote `main`, then create the task
branch inside that worktree:

```bash
cd <repo>
git fetch origin
git worktree add ../ResearchOS-task-name origin/main
cd ../ResearchOS-task-name
git switch -c docs/example-branch
```

Use a descriptive worktree directory and branch name that match the single task.
When the PR is merged or abandoned, remove the worktree deliberately:

```bash
cd <repo>
git worktree remove ../ResearchOS-task-name
```

## Implementation PR Scope

Implementation PRs must be small, scoped, and easy to review against the
ResearchOS product constraints.

- Edit only files needed for the stated task.
- Avoid active session files unless explicit coordination happened first.
- Keep docs-only changes separate from runtime behavior changes.
- Do not bundle frontend redesign, backend refactor, data integration, and
  safety changes in one PR.
- Do not change `/research/run`, the `ResearchRun` schema, deterministic
  fallback behavior, frontend/backend contracts, or evidence labels unless the
  task explicitly requires it.
- If implementation reveals a larger problem, document the follow-up instead of
  widening the PR.

## Review-Only Work

Review-only Codex sessions may inspect the whole codebase, run read-only
commands, and report findings across backend, frontend, docs, tests, scripts,
and deployment configuration.

Review-only sessions must not:

- Modify files.
- Stage or commit changes.
- Reformat files as part of the review.
- Push branches or open implementation PRs.

If a review-only session identifies a fix, open a separate implementation task
or hand off a scoped finding with suggested files and tests.

## PR Expectations

Each Codex task must report:

- PR link.
- Branch.
- Commit SHA.
- Files changed.
- Checks run.
- Known issues.

## Review Sequence

1. CI first.
2. `@codex` review second.
3. Architecture/product review third.
4. Merge only after checks and review are clean.

Codex should not merge the PR while unattended.

## Anti-Patterns

- Running multiple Codex tasks in the same checkout.
- Asking one Codex thread to do several sequential PRs.
- Letting Codex merge while unattended.
- Broad prompts like "improve ResearchOS".
- Editing active feature branches unintentionally.
- Popping stashes onto unrelated branches.
