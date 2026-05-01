"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ArrowRight,
  BarChart3,
  Blocks,
  CircuitBoard,
  Gauge,
  Landmark,
  type LucideIcon,
  RadioTower,
} from "lucide-react";

import { AgentTimeline } from "@/components/AgentTimeline";
import { BullBearPanel } from "@/components/BullBearPanel";
import { DataChartPanel } from "@/components/DataChartPanel";
import {
  DemoCaseSelector,
  type DemoCaseId,
} from "@/components/DemoCaseSelector";
import { EvidenceBoard } from "@/components/EvidenceBoard";
import { MemoViewer } from "@/components/MemoViewer";
import { OpenQuestions } from "@/components/OpenQuestions";
import { ResearchInput } from "@/components/ResearchInput";
import {
  ResearchSourceStatus,
  type ResearchSourceMode,
} from "@/components/ResearchSourceStatus";
import { TransmissionMap } from "@/components/TransmissionMap";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  getAgenticResearchStatus,
  getResearchDataStatus,
  runAgenticResearch,
  runResearch,
} from "@/lib/api";
import { demoResearchRun } from "@/lib/demoData";
import { usesBankOfCanadaValetData } from "@/lib/sourceMarkers";
import type {
  AgenticResearchStatus,
  DemoResearchRun,
  ResearchDataSource,
  ResearchDataStatus,
} from "@/lib/types";

type ResearchMode = "demo" | "agentic";

export function ResearchDashboard() {
  const [run, setRun] = useState<DemoResearchRun>(demoResearchRun);
  const [question, setQuestion] = useState(demoResearchRun.question);
  const [researchMode, setResearchMode] = useState<ResearchMode>("demo");
  const [completedResearchMode, setCompletedResearchMode] =
    useState<ResearchMode | null>(null);
  const [dataSource, setDataSource] =
    useState<ResearchDataSource>("Frontend fallback");
  const [dataStatus, setDataStatus] = useState<ResearchDataStatus | null>(null);
  const [agenticStatus, setAgenticStatus] =
    useState<AgenticResearchStatus | null>(null);
  const [isDataStatusUnavailable, setIsDataStatusUnavailable] = useState(false);
  const [isAgenticStatusUnavailable, setIsAgenticStatusUnavailable] =
    useState(false);
  const [hasRunCompleted, setHasRunCompleted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const caseDisplay = getCaseDisplay(run);
  const hasOfficialBocData = usesBankOfCanadaValetData(run);
  const isAgenticAvailable = agenticStatus?.mode === "configured";
  const isAgenticSelected = researchMode === "agentic";
  const activeResearchMode =
    isAgenticSelected && isAgenticAvailable ? "agentic" : "demo";
  const sourceMode = getResearchSourceMode({
    hasRunCompleted,
    hasOfficialBocData,
    dataSource,
    completedResearchMode,
  });

  const refreshDataStatus = useCallback(async () => {
    try {
      const nextDataStatus = await getResearchDataStatus();
      setDataStatus(nextDataStatus);
      setIsDataStatusUnavailable(false);
    } catch {
      setDataStatus(null);
      setIsDataStatusUnavailable(true);
    }
  }, []);

  const refreshAgenticStatus = useCallback(async () => {
    try {
      const nextAgenticStatus = await getAgenticResearchStatus();
      setAgenticStatus(nextAgenticStatus);
      setIsAgenticStatusUnavailable(false);
    } catch {
      setAgenticStatus(null);
      setIsAgenticStatusUnavailable(true);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    getAgenticResearchStatus()
      .then((nextAgenticStatus) => {
        if (!isMounted) {
          return;
        }
        setAgenticStatus(nextAgenticStatus);
        setIsAgenticStatusUnavailable(false);
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setAgenticStatus(null);
        setIsAgenticStatusUnavailable(true);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const runQuestion = useCallback(
    async (nextQuestion: string) => {
      const runMode = activeResearchMode;

      setIsLoading(true);
      setErrorMessage(null);
      setQuestion(nextQuestion);

      try {
        const backendRun =
          runMode === "agentic"
            ? await runAgenticResearch(nextQuestion)
            : await runResearch(nextQuestion);
        setRun(backendRun);
        setQuestion(backendRun.question);
        setCompletedResearchMode(runMode);
        setDataSource("Backend response");
        setHasRunCompleted(true);
        void refreshDataStatus();
        void refreshAgenticStatus();
      } catch {
        const fallbackQuestion = nextQuestion.trim() || demoResearchRun.question;
        setRun({ ...demoResearchRun, question: fallbackQuestion });
        setQuestion(fallbackQuestion);
        setCompletedResearchMode(null);
        setDataSource("Frontend fallback");
        setDataStatus(null);
        setIsDataStatusUnavailable(true);
        setHasRunCompleted(true);
        setErrorMessage(
          runMode === "agentic"
            ? "Agentic beta unavailable. Showing hardcoded frontend fallback."
            : "Backend unavailable. Showing hardcoded frontend fallback.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [activeResearchMode, refreshAgenticStatus, refreshDataStatus],
  );

  const handleRun = useCallback(() => {
    void runQuestion(question);
  }, [question, runQuestion]);

  const handlePresetSelect = useCallback(
    (presetQuestion: string) => {
      void runQuestion(presetQuestion);
    },
    [runQuestion],
  );

  return (
    <main className="min-h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none fixed inset-0 research-grid opacity-70" />
      <div className="relative mx-auto flex w-full max-w-[1680px] flex-col gap-5 px-4 py-4 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 rounded-lg border border-white/10 bg-zinc-950/70 p-4 backdrop-blur md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-3">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-md border border-cyan-300/25 bg-cyan-300/10">
              <Landmark className="size-5 text-cyan-200" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-semibold tracking-normal text-zinc-50 md:text-2xl">
                  Financial Research OS
                </h1>
                <Badge variant="data">Macro Transmission Demo</Badge>
              </div>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">
                A visible research workflow for tracing policy shocks into
                sector fundamentals, evidence labels, bull/bear implications,
                and memo output.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground">
            <HeaderStat
              icon={RadioTower}
              label="Backend"
              value={
                isLoading
                  ? "Calling"
                  : dataSource === "Backend response"
                    ? "Backend run"
                    : "Fallback"
              }
            />
            <HeaderStat
              icon={CircuitBoard}
              label="Mode"
              value={activeResearchMode === "agentic" ? "Agentic" : "Demo"}
            />
            <HeaderStat
              icon={Blocks}
              label="Data"
              value={hasOfficialBocData ? "Valet API" : "Demo"}
            />
          </div>
        </header>

        <ResearchInput
          question={question}
          classification={run.classification}
          timestamp={run.timestamp}
          dataSource={dataSource}
          isLoading={isLoading}
          runButtonLabel={
            activeResearchMode === "agentic" ? "Run agentic beta" : "Run demo"
          }
          errorMessage={errorMessage}
          onQuestionChange={setQuestion}
          onRun={handleRun}
        />

        <ResearchModeControl
          selectedMode={researchMode}
          activeMode={activeResearchMode}
          agenticStatus={agenticStatus}
          isAgenticStatusUnavailable={isAgenticStatusUnavailable}
          isLoading={isLoading}
          onModeChange={setResearchMode}
        />

        <ResearchSourceStatus
          mode={sourceMode}
          dataSource={dataSource}
          dataStatus={dataStatus}
          isStatusUnavailable={isDataStatusUnavailable}
        />

        <ReviewPathGuide />

        <DemoCaseSelector
          activeCaseId={caseDisplay.caseId}
          isLoading={isLoading}
          onSelect={handlePresetSelect}
        />

        <section className="grid gap-4 lg:grid-cols-[1fr_420px]">
          <div className="space-y-4">
            <div className="rounded-lg border border-white/10 bg-zinc-950/70 p-5">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{run.scenario}</Badge>
                <Badge variant="inference">{caseDisplay.framework}</Badge>
              </div>
              <h2 className="mt-4 max-w-5xl text-3xl font-semibold leading-tight tracking-normal text-zinc-50 md:text-5xl">
                {run.headline}
              </h2>
              <p className="mt-4 max-w-5xl text-base leading-7 text-zinc-300">
                {run.thesis}
              </p>
            </div>
            <MetricStrip metrics={run.metrics} />
          </div>
          <DriverPanel
            drivers={run.keyDrivers}
            label={caseDisplay.driverLabel}
            description={caseDisplay.driverDescription}
          />
        </section>

        <ResearchJudgmentCard
          judgment={run.judgment}
          dataSource={dataSource}
        />

        <TransmissionMap
          nodes={run.transmissionNodes}
          edges={run.transmissionEdges}
          description={caseDisplay.mapDescription}
        />

        <section className="grid gap-4 xl:grid-cols-[1fr_380px]">
          <div className="space-y-4">
            <AgentTimeline agents={run.agents} />
            <DataChartPanel charts={run.charts} />
            <EvidenceBoard evidence={run.evidence} />
          </div>

          <aside className="space-y-4">
            <BullBearPanel bullCase={run.bullCase} bearCase={run.bearCase} />
            <MemoViewer memo={run.memo} />
            <OpenQuestions questions={run.openQuestions} />
          </aside>
        </section>
      </div>
    </main>
  );
}

function getResearchSourceMode({
  hasRunCompleted,
  hasOfficialBocData,
  dataSource,
  completedResearchMode,
}: {
  hasRunCompleted: boolean;
  hasOfficialBocData: boolean;
  dataSource: ResearchDataSource;
  completedResearchMode: ResearchMode | null;
}): ResearchSourceMode {
  if (!hasRunCompleted) {
    return "ready";
  }

  if (dataSource === "Frontend fallback") {
    return "frontend-fallback";
  }

  if (hasOfficialBocData) {
    return "official";
  }

  if (completedResearchMode === "demo") {
    return "fixture";
  }

  return "backend";
}

const reviewPathSteps = [
  "Thesis / judgment",
  "Transmission map",
  "Evidence board",
  "Memo / open questions",
];

function ReviewPathGuide() {
  return (
    <section className="flex flex-col gap-2 rounded-lg border border-white/10 bg-zinc-950/70 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">Review path</Badge>
        <div className="flex flex-wrap items-center gap-1.5 text-sm text-zinc-100">
          {reviewPathSteps.map((item, index) => (
            <div key={item} className="flex items-center gap-1.5">
              <span>{item}</span>
              {index < reviewPathSteps.length - 1 ? (
                <ArrowRight className="size-3.5 text-cyan-300/70" />
              ) : null}
            </div>
          ))}
        </div>
      </div>
      <span className="text-xs leading-5 text-muted-foreground sm:text-right">
        Review interpretation, then inspect mechanism, evidence, and unresolved
        checks.
      </span>
    </section>
  );
}

function getCaseDisplay(run: DemoResearchRun) {
  if (run.scenario.includes("Oil shock")) {
    return {
      caseId: "oil-airlines" as DemoCaseId,
      framework: "Input-cost shock",
      driverLabel: "Airlines",
      driverDescription:
        "The prototype reasons over a structured airline driver list instead of presenting a free-form assistant answer.",
      mapDescription:
        "The primary research artifact: how oil and demand shocks move through fuel costs, fare elasticity, utilization, capacity, and cash flow.",
    };
  }

  if (run.scenario.includes("AI infrastructure")) {
    return {
      caseId: "ai-capex" as DemoCaseId,
      framework: "Industry cycle",
      driverLabel: "Semis / cloud",
      driverDescription:
        "The prototype reasons over a structured semiconductor and hyperscaler driver list instead of presenting a free-form assistant answer.",
      mapDescription:
        "The primary research artifact: how AI capex moves through supplier demand, hyperscaler budgets, ROI proof, and valuation expectations.",
    };
  }

  if (run.scenario.includes("Bank of Canada")) {
    return {
      caseId: "canadian-banks" as DemoCaseId,
      framework: "Monetary transmission",
      driverLabel: "Banks",
      driverDescription:
        "The prototype reasons over a structured bank driver list instead of presenting a free-form assistant answer.",
      mapDescription:
        "The primary research artifact: how rate cuts move through bank balance-sheet mechanics, credit quality, provisions, and valuation.",
    };
  }

  return {
    caseId: null,
    framework: "Agentic beta",
    driverLabel: "Custom",
    driverDescription:
      "Agentic beta uses a structured research workflow when configured.",
    mapDescription:
      "The primary research artifact: how the custom shock moves through channels, fundamentals, valuation drivers, and open questions.",
  };
}

function ResearchModeControl({
  selectedMode,
  activeMode,
  agenticStatus,
  isAgenticStatusUnavailable,
  isLoading,
  onModeChange,
}: {
  selectedMode: ResearchMode;
  activeMode: ResearchMode;
  agenticStatus: AgenticResearchStatus | null;
  isAgenticStatusUnavailable: boolean;
  isLoading: boolean;
  onModeChange: (mode: ResearchMode) => void;
}) {
  const isAgenticAvailable = agenticStatus?.mode === "configured";
  const agenticStatusLabel = isAgenticAvailable
    ? `${agenticStatus.model}${agenticStatus.webSearchEnabled ? " + web" : ""}`
    : isAgenticStatusUnavailable
      ? "Status unavailable"
      : "Not configured";
  const modeMessage = isAgenticAvailable
    ? "Agentic beta is configured. Select it to run the structured agentic workflow."
    : "Agentic beta is not configured. Runs will use deterministic demo mode.";

  return (
    <section className="flex flex-col gap-3 rounded-lg border border-white/10 bg-zinc-950/70 p-4 md:flex-row md:items-center md:justify-between">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={activeMode === "agentic" ? "inference" : "data"}>
            Active: {activeMode === "agentic" ? "Agentic beta" : "Demo mode"}
          </Badge>
          <Badge variant="outline">
            Selected:{" "}
            {selectedMode === "agentic" ? "Agentic beta" : "Demo mode"}
          </Badge>
          <Badge variant="outline">{agenticStatusLabel}</Badge>
        </div>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {modeMessage}
        </p>
        {isAgenticStatusUnavailable ? (
          <p className="mt-1 font-mono text-xs text-amber-200">
            Agentic beta status could not be checked. Demo mode remains
            available.
          </p>
        ) : null}
      </div>
      <div className="grid min-w-56 grid-cols-2 gap-2">
        <Button
          type="button"
          variant={selectedMode === "demo" ? "default" : "outline"}
          disabled={isLoading}
          aria-pressed={selectedMode === "demo"}
          onClick={() => onModeChange("demo")}
        >
          Demo mode
        </Button>
        <Button
          type="button"
          variant={selectedMode === "agentic" ? "default" : "outline"}
          disabled={isLoading || !isAgenticAvailable}
          aria-pressed={selectedMode === "agentic"}
          title={
            isAgenticAvailable
              ? "Run with Agentic beta"
              : "Agentic beta is not configured"
          }
          onClick={() => onModeChange("agentic")}
        >
          Agentic beta
        </Button>
      </div>
    </section>
  );
}

function HeaderStat({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border border-white/10 bg-black/30 px-3 py-2">
      <div className="flex items-center gap-1.5">
        <Icon className="size-3.5 text-cyan-300" />
        <span>{label}</span>
      </div>
      <div className="mt-1 font-mono text-sm text-zinc-50">{value}</div>
    </div>
  );
}

function MetricStrip({
  metrics,
}: {
  metrics: DemoResearchRun["metrics"];
}) {
  const toneClass = {
    cyan: "text-cyan-200 border-cyan-300/20 bg-cyan-300/10",
    emerald: "text-emerald-200 border-emerald-300/20 bg-emerald-300/10",
    amber: "text-amber-200 border-amber-300/20 bg-amber-300/10",
    rose: "text-rose-200 border-rose-300/20 bg-rose-300/10",
  };

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => (
        <Card
          key={metric.label}
          className={`p-4 ${toneClass[metric.tone]}`}
        >
          <div className="font-mono text-xs uppercase opacity-75">
            {metric.label}
          </div>
          <div className="mt-2 text-2xl font-semibold tracking-normal">
            {metric.value}
          </div>
          <p className="mt-1 text-xs leading-5 opacity-80">{metric.detail}</p>
        </Card>
      ))}
    </div>
  );
}

function DriverPanel({
  drivers,
  label,
  description,
}: {
  drivers: string[];
  label: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-zinc-950/70 p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-zinc-50">
          <BarChart3 className="size-4 text-cyan-300" />
          Sector driver map
        </div>
        <Badge variant="secondary">{label}</Badge>
      </div>
      <div className="mt-4 grid gap-2">
        {drivers.map((driver, index) => (
          <div
            key={driver}
            className="flex items-center justify-between rounded-md border border-white/10 bg-black/25 px-3 py-2"
          >
            <span className="text-sm text-zinc-200">{driver}</span>
            <span className="font-mono text-xs text-muted-foreground">
              D{index + 1}
            </span>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm leading-6 text-muted-foreground">
        {description}
      </p>
    </div>
  );
}

function ResearchJudgmentCard({
  judgment,
  dataSource,
}: {
  judgment: DemoResearchRun["judgment"];
  dataSource: ResearchDataSource;
}) {
  return (
    <section className="grid gap-4 rounded-lg border border-cyan-300/15 bg-zinc-950/80 p-5 lg:grid-cols-[1fr_420px]">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="data">
            <Gauge />
            {judgment.title}
          </Badge>
          <Badge variant="outline">{dataSource} | source-labeled claims</Badge>
        </div>
        <h3 className="mt-4 text-2xl font-semibold tracking-normal text-zinc-50">
          {judgment.stance}
        </h3>
        <p className="mt-3 max-w-4xl text-sm leading-7 text-zinc-300">
          {judgment.summary}
        </p>
      </div>
      <div className="rounded-md border border-white/10 bg-black/25 p-4">
        <div className="font-mono text-xs uppercase text-muted-foreground">
          Monitor before upgrading conviction
        </div>
        <div className="mt-3 grid gap-2">
          {judgment.watchItems.map((item) => (
            <div
              key={item}
              className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-zinc-950/65 px-3 py-2"
            >
              <span className="text-sm text-zinc-200">{item}</span>
              <span className="size-1.5 shrink-0 rounded-full bg-cyan-300" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
