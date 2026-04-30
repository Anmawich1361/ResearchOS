# Project Strategy

## Product north star

ResearchOS is a source-aware financial research workbench for macro, policy,
industry, and company transmission analysis.

The product should help a user turn a research question into a structured
workflow: transmission map, evidence ledger, skeptic pass, memo, and open
questions. It should feel like a research command center: visual, structured,
source-aware, reliable, and clear about what is known versus inferred.

The deterministic demos are not disposable mock data. They are fallback
fixtures, UI examples, and regression baselines for the product experience.

## Non-goals

ResearchOS is not:

- a generic chatbot
- a stock picker
- a Bloomberg clone
- a trading terminal
- an investment-advice product
- a source of buy/sell recommendations
- a source of price targets

Future work should preserve the non-advisory boundary and avoid personalized
investment advice. The product should support research judgment without making
the judgment for the user.

## Product SWOT

### Strengths

- Clear research command-center identity.
- Non-advisory boundary.
- Visual transmission-map metaphor.
- Evidence board and evidence-label taxonomy.
- Source/fallback observability.
- Agentic beta isolated from deterministic `/research/run`.

### Weaknesses

- Still demo-heavy.
- Custom questions currently depend on beta/fallback behavior.
- UI can become information-dense.
- Evidence labels need user education.
- Agentic beta may disappoint if unavailable.
- No polished research artifact export yet.

### Opportunities

- Turn deterministic demos into eval fixtures.
- Build source provenance as the core wedge.
- Develop the staged agentic research workflow.
- Add analyst workflow features such as saved runs, editable assumptions,
  source packs, and memo export.
- Use non-advisory guardrails as a product strength.
- Add domain-specific source adapters over time.

### Threats

- Trust failure from fabricated or weakly sourced answers.
- Drift into a generic chatbot.
- Drift into a market-data terminal.
- Compliance/product-positioning risk.
- Agentic latency/cost.
- UI complexity.

## Codebase SWOT

### Strengths

- Stable deterministic `/research/run` separate from agentic beta.
- Clear backend/frontend split.
- ResearchRun schema discipline.
- Deterministic fallback philosophy.
- Improving tests and CI.
- Emerging data-source adapter pattern.
- Strong workflow guardrails.

### Weaknesses

- Demo content may become too embedded in Python modules.
- Module-level data-source state can create testing/deployment complexity.
- Agentic safety is fragile by nature.
- Frontend state is becoming more complex.
- Backend/frontend schema sync is manual.
- Local environment friction.
- Broad Codex PRs can create review debt.

### Opportunities

- Treat ResearchRun as durable normalized output contract.
- Add source/provenance internal models.
- Add adversarial agentic evals.
- Add Playwright smoke tests.
- Create a common source adapter interface.
- Move to async agentic jobs later.
- Tighten type sharing.
- Add internal run traces.

### Threats

- Schema drift.
- Safety bypasses.
- Evidence-label degradation.
- Live API coupling.
- Frontend/backend mismatch.
- Prompt sprawl.
- AI-generated code accumulation.
- Cost and timeout risk.

## Strategic diagnosis

ResearchOS has a strong product shape because it is not trying to be a broad
chat interface or a live market-data surface. Its advantage is the structured
research workflow: a question becomes a visible chain of transmission logic,
source-backed claims, framework inference, skeptic review, and a memo.

The main strategic risk is trust. If the product produces weakly sourced,
overconfident, or advisory outputs, the command-center identity breaks. The
second risk is product drift: adding generic chat, terminal-like market widgets,
or broad agent features can blur the reason ResearchOS exists.

The codebase should therefore preserve a stable deterministic path while the
agentic beta evolves separately. `/research/run` should remain predictable and
useful as the demo and regression baseline. Experimental agentic research should
improve source provenance and reasoning quality without forcing the core demo to
depend on live APIs, live model calls, or fragile network conditions.

## Current priorities

1. Finish and harden the agentic beta path.
2. Preserve deterministic fallback.
3. Improve source provenance and claim-level evidence discipline.
4. Add adversarial safety/eval tests.
5. Protect frontend UX from becoming too cluttered.
6. Keep `/research/run` stable while agentic research evolves separately.

## Decision principles for future Codex work

- Treat `AGENTS.md` as the controlling instruction source when documents
  disagree.
- Keep `/research/run` deterministic and stable unless a task explicitly
  requires a coordinated contract change.
- Keep `/research/agentic-run` as the experimental beta path.
- Preserve the exact evidence labels: Data, Source claim, Framework inference,
  Narrative signal, Open question.
- Prefer source provenance, fallback behavior, and eval coverage over broader
  feature scope.
- Do not introduce live API requirements for app correctness or tests.
- Keep frontend changes focused on research workflow clarity rather than visual
  density.
- Keep PRs small enough that reviewers can check product constraints, schema
  stability, and fallback behavior directly.
- Update strategy, roadmap, or reflection docs when a meaningful product or
  architecture decision changes.
