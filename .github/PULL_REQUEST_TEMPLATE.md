## Summary

<!-- What changed? Keep this concise. -->

## Active Work Scope

<!-- Keep this current while the PR is active so other Codex sessions can detect overlap. -->

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

## Type of change

- [ ] Backend
- [ ] Frontend
- [ ] Docs
- [ ] Tests
- [ ] Deployment/config
- [ ] Data source
- [ ] Workflow/tooling

## Product constraints

Confirm the ResearchOS constraints were preserved:

- [ ] No buy/sell recommendations added
- [ ] No price targets added
- [ ] No personalized investment advice added
- [ ] Deterministic fallback behavior preserved
- [ ] Evidence labels preserved exactly:
  - `Data`
  - `Source claim`
  - `Framework inference`
  - `Narrative signal`
  - `Open question`
- [ ] `/research/run` response schema unchanged, or schema change is explicitly documented
- [ ] Golden-path demo behavior preserved
- [ ] Unknown/custom-question fallback behavior preserved
- [ ] Live external APIs are not required for app correctness

## Scope control

- [ ] This PR is limited to the requested task
- [ ] No unrelated local files were committed
- [ ] Overlapping active work was checked and disclosed, if applicable
- [ ] No unnecessary dependencies were added
- [ ] Backend/frontend contracts remain aligned

## Parallel-work checklist

- [ ] Current branch and working tree were checked before edits
- [ ] Files likely to be modified were identified before edits
- [ ] Open PRs or active-session notes were checked for overlap
- [ ] Active Work Scope section is complete and current
- [ ] Draft PR is being used as the live ownership record, or this is not implementation work
- [ ] No overlapping files were edited without explicit coordination

## Checks run

<!-- Mark only what was actually run. Include exact errors for failed or blocked commands. -->

- [ ] `git diff --check`
- [ ] `cd backend && python3 -m compileall app`
- [ ] `cd backend && python3 -m unittest discover -s tests`
- [ ] Backend orchestrator smoke test
- [ ] Frontend lint/typecheck/build, if frontend files changed and scripts exist
- [ ] Other:

## Manual verification

<!-- Describe manual checks, demo flows, screenshots, preview URLs, or API calls. -->

## Deployment / preview verification

- [ ] Vercel preview checked, if frontend changed
- [ ] Render preview or backend deployment checked, if backend/deployment changed
- [ ] `/health` checked, if backend changed
- [ ] `/research/run` checked, if backend changed

Preview/deployment links:

<!-- Add links here. -->

## Screenshots

<!-- Required for visible UI changes. -->

## Known issues

<!-- Be explicit. Use "None" only if there are no known issues. -->

## Final report

- Branch:
- Commit SHA:
- Files changed:
- Checks run:
- Known issues:
