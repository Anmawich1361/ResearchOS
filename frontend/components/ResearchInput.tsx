import { ArrowRight, DatabaseZap, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

type ResearchInputProps = {
  question: string;
  classification: string;
  timestamp: string;
};

export function ResearchInput({
  question,
  classification,
  timestamp,
}: ResearchInputProps) {
  return (
    <Card className="overflow-hidden border-white/10 bg-zinc-950/70">
      <div className="grid gap-4 p-4 md:grid-cols-[1fr_auto] md:items-center">
        <div className="min-w-0 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="data">
              <DatabaseZap />
              Frontend demo
            </Badge>
            <Badge variant="outline">{classification}</Badge>
            <span className="font-mono text-xs text-muted-foreground">
              {timestamp}
            </span>
          </div>
          <div className="flex min-w-0 flex-col gap-2 sm:flex-row">
            <Input
              aria-label="Research question"
              readOnly
              value={question}
              className="h-12 border-cyan-400/20 bg-black/35 font-mono text-sm text-cyan-50"
            />
            <Button className="h-12 bg-cyan-300 text-zinc-950 hover:bg-cyan-200">
              Run demo
              <ArrowRight />
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-md border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-sm text-emerald-100">
          <ShieldCheck className="size-4 shrink-0" />
          <span>No backend, no live data, no investment recommendations.</span>
        </div>
      </div>
    </Card>
  );
}
