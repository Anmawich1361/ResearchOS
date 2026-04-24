import { LibraryBig } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvidenceItem, EvidenceType } from "@/lib/types";

function evidenceVariant(type: EvidenceType) {
  if (type === "Data") return "data";
  if (type === "Framework inference") return "inference";
  if (type === "Narrative signal") return "narrative";
  if (type === "Open question") return "question";
  return "outline";
}

type EvidenceBoardProps = {
  evidence: EvidenceItem[];
};

export function EvidenceBoard({ evidence }: EvidenceBoardProps) {
  return (
    <Card className="bg-zinc-950/70">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2">
            <LibraryBig className="size-4 text-cyan-300" />
            Evidence board
          </CardTitle>
          <Badge variant="secondary">Strict labels</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-md border border-white/10">
          <div className="grid grid-cols-[1.6fr_0.8fr_0.6fr_0.6fr_0.7fr] bg-white/[0.04] px-3 py-2 font-mono text-xs uppercase text-muted-foreground max-lg:hidden">
            <div>Claim</div>
            <div>Type</div>
            <div>Confidence</div>
            <div>Importance</div>
            <div>Driver</div>
          </div>
          <div className="divide-y divide-white/10">
            {evidence.map((item) => (
              <div
                key={item.claim}
                className="grid gap-3 px-3 py-3 text-sm lg:grid-cols-[1.6fr_0.8fr_0.6fr_0.6fr_0.7fr] lg:items-center"
              >
                <div className="leading-6 text-zinc-100">{item.claim}</div>
                <div>
                  <Badge variant={evidenceVariant(item.type)}>{item.type}</Badge>
                </div>
                <div className="text-muted-foreground">{item.confidence}</div>
                <div className="text-muted-foreground">{item.importance}</div>
                <div className="font-mono text-xs text-cyan-200">{item.driver}</div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
