import {
  ArrowRight,
  DatabaseZap,
  LoaderCircle,
  Server,
  ShieldCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import type { ResearchDataSource } from "@/lib/types";

type ResearchInputProps = {
  question: string;
  classification: string;
  timestamp: string;
  dataSource: ResearchDataSource;
  isLoading: boolean;
  errorMessage?: string | null;
  onQuestionChange: (question: string) => void;
  onRun: () => void;
};

export function ResearchInput({
  question,
  classification,
  timestamp,
  dataSource,
  isLoading,
  errorMessage,
  onQuestionChange,
  onRun,
}: ResearchInputProps) {
  const isBackendResponse = dataSource === "Backend response";

  return (
    <Card className="overflow-hidden border-white/10 bg-zinc-950/70">
      <form
        className="grid gap-4 p-4 md:grid-cols-[1fr_auto] md:items-center"
        onSubmit={(event) => {
          event.preventDefault();
          onRun();
        }}
      >
        <div className="min-w-0 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={isBackendResponse ? "inference" : "data"}>
              {isBackendResponse ? <Server /> : <DatabaseZap />}
              {dataSource}
            </Badge>
            <Badge variant="outline">{classification}</Badge>
            <span className="font-mono text-xs text-muted-foreground">
              {timestamp}
            </span>
          </div>
          <div className="flex min-w-0 flex-col gap-2 sm:flex-row">
            <Input
              aria-label="Research question"
              disabled={isLoading}
              onChange={(event) => onQuestionChange(event.target.value)}
              value={question}
              className="h-12 border-cyan-400/20 bg-black/35 font-mono text-sm text-cyan-50"
            />
            <Button
              type="submit"
              disabled={isLoading}
              className="h-12 bg-cyan-300 text-zinc-950 hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isLoading ? "Running..." : "Run demo"}
              {isLoading ? (
                <LoaderCircle className="animate-spin" />
              ) : (
                <ArrowRight />
              )}
            </Button>
          </div>
          {errorMessage ? (
            <div className="font-mono text-xs text-amber-200">
              {errorMessage}
            </div>
          ) : null}
        </div>
        <div className="flex items-center gap-3 rounded-md border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-sm text-emerald-100">
          <ShieldCheck className="size-4 shrink-0" />
          <span>
            Official source-backed data may appear where explicitly labeled. No
            investment recommendations.
          </span>
        </div>
      </form>
    </Card>
  );
}
