import type {
  AgenticResearchStatus,
  DemoResearchRun,
  ResearchDataStatus,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function runResearch(question: string): Promise<DemoResearchRun> {
  const response = await fetch(`${API_BASE_URL}/research/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`Research API request failed: ${response.status}`);
  }

  return response.json() as Promise<DemoResearchRun>;
}

export async function runAgenticResearch(
  question: string,
): Promise<DemoResearchRun> {
  const response = await fetch(`${API_BASE_URL}/research/agentic-run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`Agentic research API request failed: ${response.status}`);
  }

  return response.json() as Promise<DemoResearchRun>;
}

export async function getResearchDataStatus(): Promise<ResearchDataStatus> {
  const response = await fetch(`${API_BASE_URL}/research/data-status`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Research data status request failed: ${response.status}`);
  }

  return response.json() as Promise<ResearchDataStatus>;
}

export async function getAgenticResearchStatus(): Promise<AgenticResearchStatus> {
  const response = await fetch(`${API_BASE_URL}/research/agentic-status`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `Agentic research status request failed: ${response.status}`,
    );
  }

  return response.json() as Promise<AgenticResearchStatus>;
}
