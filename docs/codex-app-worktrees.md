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

## Pre-Flight Checklist

- Pull latest `main`.
- Confirm the repo is clean.
- Confirm there are no unrelated local changes.
- Use a separate worktree or separate Codex app task.
- Keep the Mac awake if running locally.
- Do not close the laptop if it would stop the task.

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
cd ~/Desktop/Codex/ResearchOS
git fetch origin
git worktree add ../ResearchOS-task-name origin/main
cd ../ResearchOS-task-name
git switch -c docs/example-branch
```

Use a descriptive worktree directory and branch name that match the single task.
When the PR is merged or abandoned, remove the worktree deliberately:

```bash
cd ~/Desktop/Codex/ResearchOS
git worktree remove ../ResearchOS-task-name
```

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
