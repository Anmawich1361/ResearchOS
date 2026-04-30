import { Scale } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BullBearCase } from "@/lib/types";

type BullBearPanelProps = {
  bullCase: BullBearCase;
  bearCase: BullBearCase;
};

const scenarioGuideItems = [
  {
    label: "Scenario lens",
    description: "Compares upside and downside pressure paths.",
  },
  {
    label: "Sensitivity check",
    description: "Frames what would need to be true for each case.",
  },
  {
    label: "Research stress test",
    description: "Scenario implications only; no portfolio action is implied.",
  },
];

export function BullBearPanel({ bullCase, bearCase }: BullBearPanelProps) {
  return (
    <Card className="bg-zinc-950/70">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2">
            <Scale className="size-4 text-cyan-300" />
            Bull / bear
          </CardTitle>
          <Badge variant="risk">Skeptic pass</Badge>
        </div>
        <div className="grid gap-2 rounded-md border border-white/10 bg-black/25 p-3 md:grid-cols-3">
          {scenarioGuideItems.map((item) => (
            <div key={item.label} className="min-w-0">
              <Badge variant="outline">{item.label}</Badge>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 lg:grid-cols-2">
          <CaseCard tone="bull" item={bullCase} />
          <CaseCard tone="bear" item={bearCase} />
        </div>
      </CardContent>
    </Card>
  );
}

function CaseCard({
  item,
  tone,
}: {
  item: BullBearCase;
  tone: "bull" | "bear";
}) {
  return (
    <div className="rounded-md border border-white/10 bg-black/25 p-4">
      <div
        className={
          tone === "bull"
            ? "text-sm font-semibold text-emerald-200"
            : "text-sm font-semibold text-rose-200"
        }
      >
        {item.title}
      </div>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-300">
        {item.points.map((point) => (
          <li key={point} className="flex gap-2">
            <span
              className={
                tone === "bull"
                  ? "mt-2 size-1.5 shrink-0 rounded-full bg-emerald-300"
                  : "mt-2 size-1.5 shrink-0 rounded-full bg-rose-300"
              }
            />
            <span>{point}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
