import type { DemoResearchRun } from "@/lib/types";

export const BANK_OF_CANADA_VALET_MARKER = "Bank of Canada Valet API";

export function usesBankOfCanadaValetData(run: DemoResearchRun): boolean {
  return (
    run.charts.some((chart) =>
      chart.subtitle.includes(BANK_OF_CANADA_VALET_MARKER),
    ) ||
    run.evidence.some(
      (item) => item.sourceLabel === BANK_OF_CANADA_VALET_MARKER,
    )
  );
}
