import {
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
import { EvidenceBoard } from "@/components/EvidenceBoard";
import { MemoViewer } from "@/components/MemoViewer";
import { OpenQuestions } from "@/components/OpenQuestions";
import { ResearchInput } from "@/components/ResearchInput";
import { TransmissionMap } from "@/components/TransmissionMap";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { demoResearchRun } from "@/lib/demoData";

export default function Home() {
  const run = demoResearchRun;

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
            <HeaderStat icon={RadioTower} label="Backend" value="Off" />
            <HeaderStat icon={CircuitBoard} label="Agents" value="Staged" />
            <HeaderStat icon={Blocks} label="Data" value="Hardcoded" />
          </div>
        </header>

        <ResearchInput
          question={run.question}
          classification={run.classification}
          timestamp={run.timestamp}
        />

        <section className="grid gap-4 lg:grid-cols-[1fr_420px]">
          <div className="space-y-4">
            <div className="rounded-lg border border-white/10 bg-zinc-950/70 p-5">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{run.scenario}</Badge>
                <Badge variant="inference">Monetary transmission</Badge>
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
          <DriverPanel drivers={run.keyDrivers} />
        </section>

        <ResearchJudgmentCard judgment={run.judgment} />

        <TransmissionMap
          nodes={run.transmissionNodes}
          edges={run.transmissionEdges}
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
  metrics: Array<{
    label: string;
    value: string;
    detail: string;
    tone: "cyan" | "emerald" | "amber" | "rose";
  }>;
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

function DriverPanel({ drivers }: { drivers: string[] }) {
  return (
    <div className="rounded-lg border border-white/10 bg-zinc-950/70 p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-zinc-50">
          <BarChart3 className="size-4 text-cyan-300" />
          Sector driver map
        </div>
        <Badge variant="secondary">Banks</Badge>
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
        The prototype reasons over a structured bank driver list instead of
        presenting a free-form assistant answer.
      </p>
    </div>
  );
}

function ResearchJudgmentCard({
  judgment,
}: {
  judgment: {
    title: string;
    stance: string;
    summary: string;
    watchItems: string[];
  };
}) {
  return (
    <section className="grid gap-4 rounded-lg border border-cyan-300/15 bg-zinc-950/80 p-5 lg:grid-cols-[1fr_420px]">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="data">
            <Gauge />
            {judgment.title}
          </Badge>
          <Badge variant="outline">Frontend demo | no live data</Badge>
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
