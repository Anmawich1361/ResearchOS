import { SearchCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { OpenQuestion } from "@/lib/types";

type OpenQuestionsProps = {
  questions: OpenQuestion[];
};

const openQuestionGuideItems = [
  {
    label: "Diligence queue",
    description: "Unresolved research checks to verify after the run.",
  },
  {
    label: "Follow-up checks",
    description: "Next items that would sharpen the synthesis.",
  },
  {
    label: "Not a failure state",
    description: "Open items are intentional, not missing output.",
  },
];

export function OpenQuestions({ questions }: OpenQuestionsProps) {
  return (
    <Card className="bg-zinc-950/70">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2">
            <SearchCheck className="size-4 text-cyan-300" />
            Open questions
          </CardTitle>
          <Badge variant="question">Needs research</Badge>
        </div>
        <div className="grid gap-2 rounded-md border border-white/10 bg-black/25 p-3 md:grid-cols-3">
          {openQuestionGuideItems.map((item) => (
            <div key={item.label} className="min-w-0">
              <Badge variant="outline">{item.label}</Badge>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {questions.map((item) => (
          <div
            key={item.question}
            className="rounded-md border border-violet-300/20 bg-violet-400/10 p-4"
          >
            <div className="text-sm font-semibold text-violet-100">
              {item.question}
            </div>
            <p className="mt-2 text-sm leading-6 text-zinc-300">
              {item.whyItMatters}
            </p>
            <div className="mt-3 font-mono text-xs text-violet-200">
              {item.owner}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
