import { FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { MemoSection } from "@/lib/types";

type MemoViewerProps = {
  memo: MemoSection[];
};

const memoGuideItems = [
  {
    label: "Research synthesis",
    description: "Synthesizes thesis, map, evidence, data cards, and scenarios.",
  },
  {
    label: "Workflow output",
    description: "Structured from artifacts and open questions, not free-form prose.",
  },
  {
    label: "Not a recommendation",
    description: "No portfolio action, price forecast, or individualized guidance.",
  },
];

export function MemoViewer({ memo }: MemoViewerProps) {
  return (
    <Card className="bg-zinc-950/70">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2">
            <FileText className="size-4 text-cyan-300" />
            Memo panel
          </CardTitle>
          <Badge variant="outline">Structured output</Badge>
        </div>
        <div className="grid gap-2 rounded-md border border-white/10 bg-black/25 p-3 md:grid-cols-3">
          {memoGuideItems.map((item) => (
            <div key={item.label} className="min-w-0">
              <Badge variant="outline">{item.label}</Badge>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {memo.map((section) => (
          <section
            key={section.title}
            className="rounded-md border border-white/10 bg-black/25 p-4"
          >
            <h3 className="text-sm font-semibold text-zinc-50">
              {section.title}
            </h3>
            <p className="mt-2 text-sm leading-6 text-zinc-300">{section.body}</p>
          </section>
        ))}
      </CardContent>
    </Card>
  );
}
