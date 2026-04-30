# Reflection Log

This log captures recurring product and codebase reflections so future Codex
runs and contributors can understand why ResearchOS is evolving in its current
direction.

## 2026-04-30 - Post-BoC integration and Agentic Beta reflection

### What changed

- The deterministic demo path gained stronger source/fallback observability
  around official Bank of Canada data for the Canadian banks scenario.
- The Agentic beta path became a more explicit experimental route for custom
  research while the deterministic `/research/run` path remained the stable
  baseline.
- The project direction sharpened around source-aware agentic research:
  transmission map, evidence ledger, skeptic pass, memo, and open questions.

### Product reflection

The strongest product identity is a source-aware research workbench, not a
chatbot, stock picker, or market-data terminal. The golden-path demos remain
important because they show the intended user experience and provide regression
baselines for workflow quality.

The Agentic beta is valuable because it points toward custom research, but it
must not weaken the reliability of the deterministic experience. Users should
be able to tell when a result came from deterministic fallback, official source
data, or an experimental agentic pass.

### Codebase reflection

The split between deterministic `/research/run` and experimental
`/research/agentic-run` is the right boundary. It keeps the core schema and demo
stable while allowing the agentic workflow to improve behind a beta route.

The codebase risk is that source handling, prompt logic, fallback behavior, and
frontend state can become tangled if each feature adds its own local pattern.
Future work should keep source adapters, provenance metadata, and normalized
ResearchRun output disciplined.

### What improved

- Clearer source/fallback status for the flagship demo.
- Better separation between stable deterministic behavior and agentic beta
  behavior.
- Stronger language around the non-advisory product boundary.
- A clearer strategic frame for turning deterministic demos into eval fixtures.

### What got riskier

- More moving parts now sit around data sources, source status, and beta
  agentic behavior.
- Agentic output quality can disappoint if source provenance, refusal behavior,
  or fallback handling is weak.
- Frontend panels can become cluttered as source status, evidence, charts,
  agents, and memo output all compete for attention.
- Manual schema sync between backend and frontend remains a recurring risk.

### Next priorities

1. Harden `/research/agentic-run` with safe fallback behavior and fixture-based
   tests.
2. Improve source provenance so claims can be traced to data, source text, or
   framework inference.
3. Add adversarial safety and eval tests that do not require live OpenAI or web
   access.
4. Protect the frontend research workflow from becoming too dense.
5. Preserve `/research/run` and the ResearchRun schema as stable contracts.
6. Start designing a polished research artifact export.

### Open questions

- What is the smallest source-provenance model that supports claim-level
  evidence without bloating the public ResearchRun contract?
- Should source adapters share a common interface before more domains are
  added?
- Which adversarial prompts should become permanent eval fixtures?
- What frontend affordance best explains evidence labels without adding visual
  clutter?
- When should agentic research move from synchronous beta calls to async jobs?

## Reflection template

Use this template for meaningful product, architecture, agentic-research, or
workflow changes. Tiny typo fixes and narrow docs-only edits do not require a
new reflection entry.

```markdown
## YYYY-MM-DD - Title

### What changed

- TBD

### Product reflection

- TBD

### Codebase reflection

- TBD

### What improved

- TBD

### What got riskier

- TBD

### Next priorities

- TBD

### Open questions

- TBD
```
