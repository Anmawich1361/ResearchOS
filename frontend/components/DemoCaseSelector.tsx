import {
  ArrowUpRight,
  Banknote,
  Cpu,
  Fuel,
  LoaderCircle,
  type LucideIcon,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type DemoCaseId = "canadian-banks" | "oil-airlines" | "ai-capex";

export type DemoCasePreset = {
  id: DemoCaseId;
  title: string;
  subtitle: string;
  question: string;
  badge: string;
  icon: LucideIcon;
};

export const DEMO_CASE_PRESETS: DemoCasePreset[] = [
  {
    id: "canadian-banks",
    title: "Rate cuts",
    subtitle: "Canadian banks",
    question: "How would rate cuts affect Canadian banks?",
    badge: "Banks",
    icon: Banknote,
  },
  {
    id: "oil-airlines",
    title: "Oil shock",
    subtitle: "Airlines",
    question:
      "What happens to airlines if oil prices rise while consumer demand weakens?",
    badge: "Airlines",
    icon: Fuel,
  },
  {
    id: "ai-capex",
    title: "AI capex",
    subtitle: "Semis / hyperscalers",
    question: "Is AI capex becoming a risk for semiconductors and hyperscalers?",
    badge: "AI cycle",
    icon: Cpu,
  },
];

type DemoCaseSelectorProps = {
  activeCaseId: DemoCaseId | null;
  isLoading: boolean;
  onSelect: (question: string) => void;
};

export function DemoCaseSelector({
  activeCaseId,
  isLoading,
  onSelect,
}: DemoCaseSelectorProps) {
  return (
    <Card className="overflow-hidden border-cyan-300/15 bg-zinc-950/75">
      <div className="flex flex-col gap-3 border-b border-white/10 px-4 py-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="size-1.5 rounded-full bg-cyan-300 shadow-[0_0_18px_rgba(103,232,249,0.8)]" />
            <h2 className="font-mono text-xs uppercase tracking-normal text-cyan-100">
              Golden-path demos
            </h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            One-click deterministic scenarios for live demo flow.
          </p>
        </div>
        <Badge variant="outline">3 presets</Badge>
      </div>
      <div className="grid gap-2 p-3 lg:grid-cols-3">
        {DEMO_CASE_PRESETS.map((preset) => {
          const Icon = preset.icon;
          const isActive = preset.id === activeCaseId;

          return (
            <button
              key={preset.id}
              type="button"
              disabled={isLoading}
              onClick={() => onSelect(preset.question)}
              className={cn(
                "group flex min-h-28 w-full flex-col justify-between rounded-md border p-3 text-left transition",
                "disabled:cursor-not-allowed disabled:opacity-70",
                isActive
                  ? "border-cyan-300/70 bg-cyan-300/10 shadow-[0_0_0_1px_rgba(103,232,249,0.24),0_18px_50px_rgba(8,145,178,0.12)]"
                  : "border-white/10 bg-black/25 hover:border-cyan-300/35 hover:bg-cyan-300/5",
              )}
              aria-pressed={isActive}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div
                    className={cn(
                      "flex size-9 shrink-0 items-center justify-center rounded-md border",
                      isActive
                        ? "border-cyan-300/45 bg-cyan-300/15 text-cyan-100"
                        : "border-white/10 bg-zinc-950/75 text-zinc-300 group-hover:text-cyan-100",
                    )}
                  >
                    <Icon className="size-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-zinc-50">
                      {preset.title}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {preset.subtitle}
                    </div>
                  </div>
                </div>
                {isLoading && isActive ? (
                  <LoaderCircle className="size-4 shrink-0 animate-spin text-cyan-200" />
                ) : (
                  <ArrowUpRight
                    className={cn(
                      "size-4 shrink-0 transition",
                      isActive
                        ? "text-cyan-200"
                        : "text-muted-foreground group-hover:text-cyan-200",
                    )}
                  />
                )}
              </div>
              <div className="mt-4 flex items-center justify-between gap-3">
                <Badge variant={isActive ? "data" : "outline"}>
                  {isActive ? "Active" : preset.badge}
                </Badge>
                <span
                  className={cn(
                    "inline-flex h-7 items-center justify-center rounded-md px-2 text-xs font-medium",
                    isActive
                      ? "bg-cyan-300 text-zinc-950"
                      : "text-muted-foreground group-hover:text-cyan-100",
                  )}
                >
                  Run
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </Card>
  );
}
