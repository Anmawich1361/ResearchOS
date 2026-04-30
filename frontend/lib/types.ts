export type EvidenceType =
  | "Data"
  | "Source claim"
  | "Framework inference"
  | "Narrative signal"
  | "Open question";

export type Confidence = "Low" | "Low/Medium" | "Medium" | "Medium/High" | "High";

export type ResearchDataSource = "Frontend fallback" | "Backend response";

export type BankOfCanadaPolicyRateStatus = {
  source: string;
  series: string;
  url: string;
  cacheTtlSeconds: number;
  failureCooldownSeconds?: number;
  cached: boolean;
  inFailureCooldown?: boolean;
  nextRetryAt?: string | null;
  lastResult: "not_requested" | "live" | "cached" | "fallback" | "cooldown";
  lastAttemptAt: string | null;
  lastLiveFetchAt: string | null;
  lastError: string | null;
};

export type ResearchDataStatus = {
  bankOfCanadaPolicyRate: BankOfCanadaPolicyRateStatus;
};

export type AgentStage = {
  name: string;
  role: string;
  status: "complete" | "active" | "queued";
  duration: string;
  output: string[];
};

export type TransmissionNode = {
  id: string;
  label: string;
  subtitle: string;
  driver: string;
  evidenceType: EvidenceType;
  confidence: Confidence;
  researchImplication: string;
  whyItMatters: string;
  polarity: "positive" | "negative" | "mixed" | "risk" | "neutral";
  x: number;
  y: number;
};

export type TransmissionEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
  polarity: "positive" | "negative" | "mixed" | "risk" | "neutral";
};

export type ChartSeries = {
  title: string;
  subtitle: string;
  unit: string;
  tone: "cyan" | "emerald" | "amber" | "rose";
  data: Array<{
    period: string;
    value: number;
    comparison?: number;
  }>;
};

export type EvidenceItem = {
  claim: string;
  type: EvidenceType;
  confidence: Confidence;
  importance: "Low" | "Medium" | "High";
  driver: string;
  sourceLabel?: string;
  sourceType?: string;
  sourceQuality?: "High" | "Medium" | "Low";
};

export type ResearchJudgment = {
  title: string;
  stance: string;
  summary: string;
  watchItems: string[];
};

export type BullBearCase = {
  title: string;
  points: string[];
};

export type MemoSection = {
  title: string;
  body: string;
};

export type OpenQuestion = {
  question: string;
  whyItMatters: string;
  owner: string;
};

export type DemoResearchRun = {
  question: string;
  classification: string;
  timestamp: string;
  scenario: string;
  headline: string;
  thesis: string;
  judgment: ResearchJudgment;
  keyDrivers: string[];
  metrics: Array<{
    label: string;
    value: string;
    detail: string;
    tone: "cyan" | "emerald" | "amber" | "rose";
  }>;
  agents: AgentStage[];
  transmissionNodes: TransmissionNode[];
  transmissionEdges: TransmissionEdge[];
  charts: ChartSeries[];
  evidence: EvidenceItem[];
  bullCase: BullBearCase;
  bearCase: BullBearCase;
  memo: MemoSection[];
  openQuestions: OpenQuestion[];
};
