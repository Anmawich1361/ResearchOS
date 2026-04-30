# Agentic Research Roadmap

## Purpose

This roadmap describes how ResearchOS should evolve from deterministic demos
toward source-aware agentic research without weakening the stable product
contract.

The goal is not to replace the deterministic demo path. The goal is to build an
experimental beta path that can turn a user question into a structured
transmission map, evidence ledger, skeptic pass, memo, and open questions while
falling back safely when agentic research is unavailable or unreliable.

## Current state

- `/research/run` remains deterministic and stable.
- `/research/run` is the golden-path demo and regression baseline.
- `/research/agentic-run` is the experimental beta path.
- Agentic failures should fall back safely to deterministic demo data.
- Tests should not require live OpenAI or web access.
- Outputs must not include buy/sell recommendations or price targets.
- The ResearchRun schema should remain stable unless a task explicitly requires
  a coordinated backend/frontend contract change.

## Milestone 1: Safe agentic beta

- Keep `/research/agentic-run` isolated from deterministic `/research/run`.
- Normalize successful beta output into the existing ResearchRun shape.
- Add fixture-based tests for successful, failed, and unavailable agentic
  execution.
- Ensure failures produce deterministic fallback output with visible fallback
  status.
- Keep server-side credentials optional and never required for app correctness.

## Milestone 2: Source provenance v1

- Track whether each major output element came from deterministic fixture data,
  official data, source text, or model-generated framework inference.
- Add internal provenance structures before expanding public response contracts.
- Preserve existing evidence labels exactly: Data, Source claim, Framework
  inference, Narrative signal, Open question.
- Make source/fallback status clear enough for users and reviewers to audit.
- Avoid live data coupling by using timeouts, fixture tests, and deterministic
  fallback.

## Milestone 3: Claim-level evidence discipline

- Tie important claims to evidence items, sources, or explicit framework
  inferences.
- Flag unsupported claims as open questions instead of presenting them as
  sourced conclusions.
- Add tests that catch evidence-label drift and unsupported claim patterns.
- Keep memo language non-advisory and avoid personalized recommendations.
- Preserve the distinction between source claims, data, inference, narrative
  signals, and open questions.

## Milestone 4: Adversarial safety and eval tests

- Add adversarial prompts that request investment advice, price targets,
  unsupported certainty, fabricated sources, or schema-breaking output.
- Run these tests without live OpenAI or web access by using fixtures and
  deterministic stubs.
- Verify fallback behavior when model output is malformed, unsafe, slow, or
  unavailable.
- Add regression tests for the three golden paths and an unknown custom
  question.
- Treat deterministic demos as eval fixtures, not just UI examples.

## Milestone 5: Frontend beta UX hardening

- Keep the interface focused on the research workflow rather than raw model
  chat.
- Make beta/fallback/source status visible without cluttering the primary
  research panels.
- Preserve the transmission map, evidence board, skeptic pass, memo, and open
  questions as the main workflow artifacts.
- Add smoke coverage for critical frontend flows once the UI stabilizes.
- Avoid adding market-terminal features that distract from transmission
  analysis.

## Milestone 6: Research artifact export

- Provide a polished export of the structured research output.
- Include the research question, transmission map summary, evidence ledger,
  skeptic pass, memo, open questions, and source/fallback notes.
- Preserve non-advisory language in exported artifacts.
- Keep source provenance visible enough for review.
- Avoid adding price targets, buy/sell calls, or personalized advice in export
  templates.

## Milestone 7: Async/background research runs, later

- Move longer agentic research into async/background jobs only after the
  synchronous beta path is safe and useful.
- Add run status, trace, and failure state models before exposing long-running
  jobs broadly.
- Keep deterministic `/research/run` available as the stable immediate path.
- Design timeouts, retries, cancellation, and fallback behavior before adding
  expensive or slow research workflows.
- Treat cost and latency as product constraints, not implementation details.

## Non-goals

- Do not make `/research/run` depend on live model calls.
- Do not require live OpenAI or web access for tests.
- Do not add buy/sell recommendations.
- Do not add price targets.
- Do not imply personalized investment advice.
- Do not turn ResearchOS into a generic chatbot.
- Do not turn ResearchOS into a market-data terminal.
- Do not expand public schemas casually.
- Do not let agentic beta behavior weaken deterministic fallback.
