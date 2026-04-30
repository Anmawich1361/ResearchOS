# Financial Research OS — Macro Transmission Demo

## Project thesis

Financial Research OS is an agentic financial research workbench that helps finance users understand how a macro, policy, industry, or narrative shock flows through the economy into sector/company fundamentals and valuation drivers.

The first-month MVP is intentionally focused:

> Take a financial shock or research question, decompose it into an agentic workflow, pull relevant data/sources, apply economic frameworks, build an interactive transmission map, label evidence, generate bull/bear implications, and produce a structured memo.

This is not a generic AI chatbot, stock picker, or investment recommendation tool. It is a visually polished research workflow system.

---

## Project strategy

For durable product direction, agentic-research sequencing, and recurring
project reflections, see:

- `docs/project-strategy.md`
- `docs/agentic-research-roadmap.md`
- `docs/reflection-log.md`

---

## MVP name

**Financial Research OS — Macro Transmission Demo**

Long-term vision: a broader financial research operating system.

Month-one goal: a beautiful, focused macro-transmission research demo.

---

## Live deployment

- Frontend: https://research-os-rust.vercel.app
- Backend API: https://researchos-api.onrender.com
- Backend health: https://researchos-api.onrender.com/health

The backend analysis remains deterministic. The Canadian banks demo may replace
the policy-rate chart with official Bank of Canada Valet API data when
available, and otherwise falls back to deterministic demo data. ResearchOS is
not investment advice, a live market-data terminal, or a source of buy/sell
recommendations.

For deployed source checks, see `docs/boc-verification.md` or run:

```bash
./scripts/verify_research_api.sh
```

---

## Live demo script

1. Open https://research-os-rust.vercel.app and point out the visible research
   workflow: question input, demo selector, agents, transmission map, evidence,
   bull/bear framing, and memo.
2. Click **Rate cuts / Canadian banks** and describe the monetary-transmission
   tradeoff: credit relief versus NII, provisions, and valuation sensitivity.
3. Click **Oil shock / Airlines** and show how a fuel-cost shock combines with
   weaker consumer demand, load-factor risk, and operating leverage.
4. Click **AI capex / Semis / hyperscalers** and frame the debate as supplier
   tailwinds versus hyperscaler ROI and free-cash-flow pressure.
5. Mention that custom questions can still be typed, but unknown questions
   intentionally fall back to the Canadian banks golden path for demo reliability.
6. Close by noting that outputs use strict evidence labels, official data is
   explicitly labeled when shown, and the app is not a live market-data terminal
   or an investment recommendation product.

---

## Core user workflow

The user enters a question such as:

- `How would rate cuts affect Canadian banks?`
- `What happens to airlines if oil prices rise while consumer demand weakens?`
- `Is AI capex becoming a risk for semiconductors and hyperscalers?`

The system then runs a visible research workflow:

```text
Research question
→ Planner Agent
→ Data Agent
→ Framework Agent
→ Skeptic Agent
→ Synthesis Agent
→ Transmission Map + Evidence Board + Bull/Bear + Memo
```

The canonical MVP workflow is:

```text
1. Classify the question
2. Identify shock variables
3. Pull relevant macro/source data
4. Choose an economic/financial framework
5. Build a transmission map
6. Generate bull/bear implications
7. Label evidence
8. Produce a structured memo
```

---

## What makes this different from a chatbot wrapper

A chatbot wrapper:

```text
User asks question → AI writes answer
```

This product:

```text
User asks question
→ system classifies the research problem
→ agents produce structured artifacts
→ data/tools provide evidence
→ economic framework is selected
→ transmission channels are mapped visually
→ claims are labeled by evidence type
→ skeptic agent challenges the conclusion
→ synthesis agent creates final research output
```

The main product is the **visible research pipeline**, especially the **Transmission Map**.

---

## First-month MVP scope

### Include

- Polished Next.js frontend
- Research question input
- Agent workflow timeline
- Interactive transmission map
- Evidence board with strict evidence labels
- Bull/bear case panel
- Data/chart panel
- Final memo panel
- Open questions panel
- Three polished golden-path demos
- Five-stage agent workflow
- Basic FRED integration later in the MVP
- Hardcoded sector-driver maps for reliability
- Basic source upload or pasted text ingestion if time allows

### Defer

- Full FRB/US macro model
- BEA input-output engine
- ALFRED vintage macro module
- Reddit/X ingestion
- Full SEC/XBRL company automation
- Full valuation model
- User accounts
- Real-time market feeds
- Buy/sell recommendations
- Price targets

---

## Frontend stack

Use:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- React Flow
- Recharts

Reason: the product needs to look polished and visually impressive. The UI is part of the core product.

---

## Backend stack

Use:

- Python
- FastAPI
- pandas
- SQLite for local persistence
- Pydantic schemas
- OpenAI API for structured agent outputs
- FRED API client
- Local JSON maps for sectors/frameworks
- Optional document parser for PDFs/text later

---

## MVP design principle

The first version should be built around three **golden paths**, not full generality.

### Golden path 1 — flagship demo

**Question:** `How would rate cuts affect Canadian banks?`

Shows:

- monetary transmission
- credit cycle
- NIM vs loan growth tradeoff
- valuation multiple effects
- mixed bull/bear implications

This should be the most polished demo.

### Golden path 2

**Question:** `What happens to airlines if oil prices rise while consumer demand weakens?`

Shows:

- input-cost shock
- consumer demand shock
- operating leverage
- margin compression

### Golden path 3

**Question:** `Is AI capex becoming a risk for semiconductors and hyperscalers?`

Shows:

- narrative analysis
- industry-cycle thinking
- capex ROI debate
- bull/bear framing

Custom questions should work eventually, but the golden paths should look excellent every time.

---

## Main visual centerpiece: Transmission Map

The Transmission Map is the killer visual.

Example for Canadian banks:

```text
Rate cuts
├── Lower short-term yields
│   └── Potential NIM pressure
├── Lower borrowing costs
│   └── Stronger loan demand
├── Easier financial conditions
│   └── Lower credit stress
├── Lower discount rates
│   └── Higher valuation multiples
└── Recession signal risk
    └── Higher provisions / weaker growth
```

Clicking a node should eventually show:

- explanation
- affected financial driver
- evidence type
- confidence
- source/data link if available
- bull/bear implication

---

## Five-stage visible agent workflow

Keep the UI clean. Show five stages:

### 1. Planner Agent

Breaks down the question.

Example output:

```json
{
  "research_type": "macro_to_sector_shock",
  "shock": "rate cuts",
  "affected_sector": "Canadian banks",
  "key_drivers": ["NIM", "loan_growth", "credit_losses", "deposit_costs", "valuation_multiples"]
}
```

### 2. Data Agent

Pulls relevant structured data.

Initial examples:

- policy rate
- yield curve
- inflation
- unemployment
- credit spreads
- oil prices if relevant

### 3. Framework Agent

Chooses the analytical lens.

Examples:

- monetary transmission
- credit cycle
- input-cost shock
- consumer demand shock
- valuation regime
- policy shock
- industry structure

### 4. Skeptic Agent

Challenges the analysis.

Examples:

- What could be wrong?
- What assumptions are weak?
- What evidence would disprove the view?
- What is the counter-thesis?

### 5. Synthesis Agent

Produces:

- transmission map
- evidence board
- bull/bear panel
- memo
- open questions

---

## Evidence board definitions

The evidence board must not pretend every AI inference is “evidence.” Use strict labels.

| Evidence Type | Meaning |
|---|---|
| Data | Pulled from FRED or another structured source |
| Source claim | Found in uploaded/source text |
| Framework inference | Derived from economic/financial logic |
| Narrative signal | Low-confidence market commentary |
| Open question | Needs more research |

Example table:

| Claim | Type | Confidence | Importance |
|---|---|---|---|
| Rate cuts can pressure bank NIMs | Framework inference | Medium | High |
| Lower rates may support loan growth | Framework inference | Medium | Medium |
| Unemployment trend affects credit losses | Data + framework inference | High | High |
| Investors are concerned about housing exposure | Narrative signal | Low/Medium | Medium |

---

## Hardcoded sector-driver maps

For the MVP, do not rely on AI to invent sector logic from scratch. Use structured maps.

Example: banks

```json
{
  "sector": "banks",
  "drivers": [
    "net_interest_margin",
    "deposit_costs",
    "loan_growth",
    "credit_losses",
    "provisions",
    "capital_markets_activity",
    "valuation_multiple"
  ],
  "macro_sensitivities": {
    "rate_cuts": {
      "positive": ["loan_growth", "credit_losses", "valuation_multiple"],
      "negative": ["net_interest_margin"],
      "mixed": ["deposit_costs", "provisions"]
    }
  }
}
```

Example: airlines

```json
{
  "sector": "airlines",
  "drivers": [
    "fuel_costs",
    "labor_costs",
    "capacity",
    "fares",
    "load_factor",
    "consumer_demand",
    "debt_refinancing"
  ]
}
```

Example: semis/cloud

```json
{
  "sector": "semis_cloud",
  "drivers": [
    "ai_capex",
    "data_center_demand",
    "inventory_cycle",
    "gross_margin",
    "export_controls",
    "customer_concentration",
    "capex_roi"
  ]
}
```

The AI should reason over these maps instead of free-styling.

---

## Guardrails

The MVP must avoid acting like a stock recommendation engine.

Rules:

- No buy/sell recommendations
- No price targets in the MVP
- No unsupported claims
- Every important claim should be labeled as data, source claim, framework inference, narrative signal, or open question
- Confidence levels should be shown where relevant
- Source quality should be visible where relevant
- Skeptic pass is required before final memo
- Clearly distinguish facts from interpretations

---

## Suggested repo structure

```text
financial-research-os/
  frontend/
    app/
      page.tsx
      research/[id]/page.tsx
    components/
      ResearchInput.tsx
      AgentTimeline.tsx
      TransmissionMap.tsx
      EvidenceBoard.tsx
      DataChartPanel.tsx
      BullBearPanel.tsx
      MemoViewer.tsx
      OpenQuestions.tsx
    lib/
      api.ts
      types.ts
      demoData.ts

  backend/
    app/
      main.py
      config.py

      agents/
        planner.py
        data_agent.py
        framework_agent.py
        skeptic_agent.py
        synthesis_agent.py

      engines/
        macro_transmission.py
        framework_router.py
        sector_driver_map.py
        evidence_classifier.py

      schemas/
        research_run.py
        agent_outputs.py
        evidence.py
        transmission.py
        memo.py

      tools/
        fred_client.py
        source_parser.py

      storage/
        database.py
        models.py

      prompts/
        planner.md
        framework.md
        skeptic.md
        synthesis.md

  data/
    sector_maps/
      banks.json
      airlines.json
      semis_cloud.json
    demo_cases/
      canadian_banks_rate_cuts.json
      oil_airlines.json
      ai_capex_semis.json
    cached_fred/

  docs/
    product_spec.md
    demo_script.md
    architecture.md

  README.md
```

---

## Suggested build order

### Week 1 — Visual prototype first

Goal: make the app look impressive before backend complexity.

Build:

- Next.js app
- polished homepage
- research input
- dashboard layout
- hardcoded Canadian banks demo
- agent timeline
- transmission map
- evidence board
- bull/bear panel
- memo panel

Acceptance criteria:

- App runs locally
- Canadian banks demo is visible
- Transmission map is the visual centerpiece
- UI looks polished
- No backend required yet

---

### Week 2 — Agent workflow backend

Goal: replace hardcoded logic with structured backend outputs.

Build:

- FastAPI backend
- Pydantic schemas
- `/research/run` endpoint
- five-stage agent workflow:
  - Planner
  - Data
  - Framework
  - Skeptic
  - Synthesis
- SQLite storage for runs, if time allows

Acceptance criteria:

- User enters a question
- Backend returns a structured research run
- Frontend renders backend output
- Agents return structured JSON, not free-form prose

---

### Week 3 — Data and sector maps

Goal: make the app data-backed and less generic.

Build:

- FRED connector
- macro series library
- sector-driver maps
- framework router
- macro transmission engine
- chart panel
- basic evidence classifier

Acceptance criteria:

- App can pull at least some real macro data
- Research output uses sector-driver maps
- Evidence board distinguishes data vs inference
- Transmission map is generated from structured data

---

### Week 4 — Polish and demos

Goal: make it demo-ready.

Build:

- three golden-path demos
- better visual design
- source drawer if time allows
- memo export to Markdown/PDF if time allows
- README cleanup
- demo script
- screenshots

Acceptance criteria:

- Canadian banks demo looks excellent
- Oil/airlines demo works
- AI capex demo works
- App can be shown in a 2-minute demo
- README explains product and setup clearly

---

## Long-term roadmap

These are bigger differentiators after the MVP.

### 1. Full macro transmission engine

Better mapping of:

```text
macro shock → economic channels → sectors → company drivers → valuation implications
```

### 2. BEA input-output shock map

Use industry input-output tables to analyze how shocks propagate through industries.

Use cases:

- tariffs
- oil shocks
- wage shocks
- supply-chain disruptions

### 3. ALFRED real-time macro history module

Analyze historical periods using the macro data available at that time.

Purpose:

- reduce hindsight bias
- study historical market regimes
- compare original vs revised macro data

### 4. Narrative diffusion tracker

Track how narratives spread across sources.

Examples:

- AI capex bubble
- higher-for-longer
- consumer slowdown
- commercial real estate stress
- China stimulus
- tariffs

### 5. Valuation regime detector

Classify the market environment.

Examples:

- disinflation + resilient growth
- rising rates + slowing growth
- stagflation risk
- credit stress
- recession scare
- liquidity melt-up

### 6. Policy shock simulator

Map policy changes into economic and company-level effects.

Examples:

- tariffs
- tax changes
- fiscal stimulus
- immigration policy
- industrial policy
- banking regulation

### 7. FRB/US integration

Long-term possible integration with the Fed’s FRB/US macro model or a simplified internal macro-scenario module.

---

## Codex operating rules

Codex should follow these rules:

1. Build incrementally.
2. Prefer clean, modular code.
3. Do not overbuild.
4. Do not add features outside the current milestone.
5. Keep frontend polished.
6. Keep the transmission map central.
7. Use structured data and schemas.
8. Avoid unsupported investment recommendations.
9. Preserve the distinction between data, source claims, inferences, narrative signals, and open questions.
10. Optimize for a strong demo first, not total generality.

---

## Immediate next task

Start with **Milestone 1: Visual prototype**.

Create the initial Next.js frontend with hardcoded demo data for:

```text
How would rate cuts affect Canadian banks?
```

The first milestone should not include backend integration. The goal is to make the product visually real and demoable as quickly as possible.
