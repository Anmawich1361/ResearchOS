import { CheckCircle2, CircleDashed } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AgentStage } from "@/lib/types";

type AgentTimelineProps = {
  agents: AgentStage[];
};

export function AgentTimeline({ agents }: AgentTimelineProps) {
  return (
    <Card className="bg-zinc-950/70">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle>Five-stage agent workflow</CardTitle>
          <Badge variant="secondary">Visible pipeline</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 md:grid-cols-5">
          {agents.map((agent, index) => (
            <div
              key={agent.name}
              className="relative min-h-44 rounded-md border border-white/10 bg-black/25 p-3"
            >
              {index < agents.length - 1 ? (
                <div className="absolute left-[calc(100%-0.75rem)] top-7 hidden h-px w-6 bg-cyan-400/40 md:block" />
              ) : null}
              <div className="mb-3 flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  {agent.status === "complete" ? (
                    <CheckCircle2 className="size-4 text-emerald-300" />
                  ) : (
                    <CircleDashed className="size-4 text-cyan-300" />
                  )}
                  <span className="font-mono text-xs text-muted-foreground">
                    {agent.duration}
                  </span>
                </div>
                <span className="font-mono text-xs text-cyan-200">
                  0{index + 1}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-zinc-50">{agent.name}</h3>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                {agent.role}
              </p>
              <ul className="mt-3 space-y-1.5 text-xs text-zinc-300">
                {agent.output.slice(0, 3).map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="mt-1.5 size-1 shrink-0 rounded-full bg-cyan-300" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
