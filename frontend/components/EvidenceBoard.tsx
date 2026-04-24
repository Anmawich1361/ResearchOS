import { LibraryBig, ShieldCheck } from "lucide-react";

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
          <div>
            <CardTitle className="flex items-center gap-2">
              <LibraryBig className="size-4 text-cyan-300" />
              Evidence board
            </CardTitle>
            <p className="mt-2 text-sm text-muted-foreground">
              Source-ready claim ledger for future real data, filings, and
              research-source attachments.
            </p>
          </div>
          <Badge variant="secondary">
            <ShieldCheck />
            Strict labels
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-md border border-white/10">
          <div className="grid grid-cols-[1.55fr_0.75fr_0.7fr_0.55fr_0.7fr_0.9fr_0.65fr] bg-white/[0.04] px-3 py-2 font-mono text-xs uppercase text-muted-foreground max-xl:hidden">
            <div>Claim</div>
            <div>Type</div>
            <div>Confidence</div>
            <div>Importance</div>
            <div>Driver</div>
            <div>Source</div>
            <div>Quality</div>
          </div>
          <div className="divide-y divide-white/10">
            {evidence.map((item) => (
              <div
                key={item.claim}
                className="grid gap-3 px-3 py-3 text-sm xl:grid-cols-[1.55fr_0.75fr_0.7fr_0.55fr_0.7fr_0.9fr_0.65fr] xl:items-center"
              >
                <div className="leading-6 text-zinc-100">{item.claim}</div>
                <div>
                  <Badge variant={evidenceVariant(item.type)}>{item.type}</Badge>
                </div>
                <div className="text-muted-foreground">{item.confidence}</div>
                <div className="text-muted-foreground">{item.importance}</div>
                <div className="font-mono text-xs text-cyan-200">{item.driver}</div>
                <div>
                  {item.sourceLabel ? (
                    <div>
                      <div className="text-xs font-medium text-zinc-100">
                        {item.sourceLabel}
                      </div>
                      {item.sourceType ? (
                        <div className="mt-1 font-mono text-xs text-muted-foreground">
                          {item.sourceType}
                        </div>
                      ) : null}
                    </div>
                  ) : (
                    <span className="text-muted-foreground">Pending source</span>
                  )}
                </div>
                <div>
                  {item.sourceQuality ? (
                    <Badge variant={qualityVariant(item.sourceQuality)}>
                      {item.sourceQuality}
                    </Badge>
                  ) : (
                    <Badge variant="outline">Unscored</Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function qualityVariant(quality: NonNullable<EvidenceItem["sourceQuality"]>) {
  if (quality === "High") return "data";
  if (quality === "Medium") return "inference";
  return "narrative";
}
