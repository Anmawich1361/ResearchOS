import {
  DatabaseZap,
  Server,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { ResearchDataSource, ResearchDataStatus } from "@/lib/types";

export type ResearchSourceMode =
  | "ready"
  | "official"
  | "fixture"
  | "backend"
  | "frontend-fallback";

type ResearchSourceStatusProps = {
  mode: ResearchSourceMode;
  dataSource: ResearchDataSource;
  dataStatus: ResearchDataStatus | null;
  isStatusUnavailable: boolean;
};

export function ResearchSourceStatus({
  mode,
  dataSource,
  dataStatus,
  isStatusUnavailable,
}: ResearchSourceStatusProps) {
  const config = sourceModeConfig[mode];
  const Icon = config.icon;
  const policyRateStatus = dataStatus?.bankOfCanadaPolicyRate;
  const statusText = getStatusText(mode, config.statusText, isStatusUnavailable);
  const sourceDetailText = policyRateStatus?.inFailureCooldown
    ? "Bank of Canada Valet API cooldown is active."
    : null;

  return (
    <Card className="border-cyan-300/15 bg-zinc-950/70 p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <div className={config.iconClassName}>
            <Icon className="size-4" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <div className="text-sm font-semibold text-zinc-50">
                {config.title}
              </div>
              <Badge variant={config.badgeVariant}>{dataSource}</Badge>
            </div>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              {config.detail}
            </p>
            {sourceDetailText ? (
              <p className="mt-1 font-mono text-xs text-amber-200">
                {sourceDetailText}
              </p>
            ) : null}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2 md:justify-end">
          <Badge variant={config.badgeVariant} title={config.title}>
            {config.badge}
          </Badge>
          <span className="font-mono text-xs text-muted-foreground">
            {statusText}
          </span>
        </div>
      </div>
    </Card>
  );
}

const sourceModeConfig: Record<
  ResearchSourceMode,
  {
    title: string;
    detail: string;
    statusText: string;
    badge: string;
    badgeVariant: "data" | "inference" | "outline" | "risk";
    icon: LucideIcon;
    iconClassName: string;
  }
> = {
  ready: {
    title: "Source readiness",
    detail:
      "Source status will be checked after a backend run. Demo data remains deterministic and usable.",
    statusText: "Ready: source status will be checked after a backend run",
    badge: "Ready",
    badgeVariant: "outline",
    icon: ShieldCheck,
    iconClassName:
      "flex size-9 shrink-0 items-center justify-center rounded-md border border-white/10 bg-black/30 text-zinc-300",
  },
  official: {
    title: "Official BoC data used",
    detail:
      "Exact Bank of Canada Valet API marker found in a chart or evidence row.",
    statusText: "Official: exact Bank of Canada Valet API marker found",
    badge: "Official BoC",
    badgeVariant: "data",
    icon: Server,
    iconClassName:
      "flex size-9 shrink-0 items-center justify-center rounded-md border border-cyan-300/30 bg-cyan-300/10 text-cyan-200",
  },
  fixture: {
    title: "Deterministic demo series",
    detail:
      "Fixture-backed demo data is active without the exact Bank of Canada Valet API marker.",
    statusText: "Demo fixture: no exact Bank of Canada Valet API marker found",
    badge: "Demo fixture",
    badgeVariant: "inference",
    icon: DatabaseZap,
    iconClassName:
      "flex size-9 shrink-0 items-center justify-center rounded-md border border-emerald-300/30 bg-emerald-300/10 text-emerald-200",
  },
  backend: {
    title: "Backend response without BoC data",
    detail:
      "The backend returned a structured research run without the exact Bank of Canada Valet API marker.",
    statusText: "Backend response: no exact Bank of Canada Valet API marker found",
    badge: "Backend no BoC",
    badgeVariant: "outline",
    icon: Server,
    iconClassName:
      "flex size-9 shrink-0 items-center justify-center rounded-md border border-white/10 bg-black/30 text-zinc-300",
  },
  "frontend-fallback": {
    title: "Frontend fallback active",
    detail:
      "The API request failed, so the hardcoded frontend fallback is showing.",
    statusText: "API unavailable: hardcoded frontend fallback active",
    badge: "API unavailable",
    badgeVariant: "risk",
    icon: DatabaseZap,
    iconClassName:
      "flex size-9 shrink-0 items-center justify-center rounded-md border border-rose-300/30 bg-rose-300/10 text-rose-200",
  },
};

function getStatusText(
  mode: ResearchSourceMode,
  defaultStatusText: string,
  isStatusUnavailable: boolean,
) {
  if (!isStatusUnavailable) {
    return defaultStatusText;
  }

  if (mode === "frontend-fallback") {
    return "API unavailable: backend source status could not be checked";
  }

  return "BoC status endpoint unavailable; completed run remains usable";
}
