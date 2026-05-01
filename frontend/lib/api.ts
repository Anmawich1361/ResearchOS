import type {
  AgenticResearchStatus,
  DemoResearchRun,
  ResearchDataStatus,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type JsonRecord = Record<string, unknown>;

const EVIDENCE_LABELS = new Set<string>([
  "Data",
  "Source claim",
  "Framework inference",
  "Narrative signal",
  "Open question",
]);

const AGENTIC_STATUS_MODES = new Set<string>([
  "disabled",
  "fallback",
  "configured",
]);

const POLICY_RATE_RESULTS = new Set<string>([
  "not_requested",
  "live",
  "cached",
  "fallback",
  "cooldown",
]);

const RESEARCH_RUN_STRING_FIELDS = [
  "question",
  "classification",
  "timestamp",
  "scenario",
  "headline",
  "thesis",
];

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

  return validateResearchRun(
    await readJson(response, "Research API response"),
    "Research API response",
  );
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

  return validateResearchRun(
    await readJson(response, "Agentic research API response"),
    "Agentic research API response",
  );
}

export async function getResearchDataStatus(): Promise<ResearchDataStatus> {
  const response = await fetch(`${API_BASE_URL}/research/data-status`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Research data status request failed: ${response.status}`);
  }

  return validateResearchDataStatus(
    await readJson(response, "Research data status response"),
    "Research data status response",
  );
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

  return validateAgenticResearchStatus(
    await readJson(response, "Agentic research status response"),
    "Agentic research status response",
  );
}

async function readJson(response: Response, label: string): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new Error(`${label} returned invalid JSON`);
  }
}

function validateResearchRun(
  payload: unknown,
  label: string,
): DemoResearchRun {
  const run = requireRecord(payload, label);
  requireStringFields(run, label, RESEARCH_RUN_STRING_FIELDS);
  requireStringArrayField(run, "keyDrivers", label);

  const judgment = requireRecordField(run, "judgment", label);
  requireStringFields(judgment, `${label}.judgment`, [
    "title",
    "stance",
    "summary",
  ]);
  requireStringArrayField(judgment, "watchItems", `${label}.judgment`);

  validatePanel(requireRecordField(run, "bullCase", label), `${label}.bullCase`);
  validatePanel(requireRecordField(run, "bearCase", label), `${label}.bearCase`);
  validateMetrics(run, label);
  validateAgents(run, label);
  validateTransmissionNodes(run, label);
  validateTransmissionEdges(run, label);
  validateCharts(run, label);
  validateEvidence(run, label);
  validateMemo(run, label);
  validateOpenQuestions(run, label);

  return payload as DemoResearchRun;
}

function validateAgenticResearchStatus(
  payload: unknown,
  label: string,
): AgenticResearchStatus {
  const status = requireRecord(payload, label);
  requireBooleanField(status, "enabled", label);
  requireBooleanField(status, "configured", label);
  requireStringField(status, "model", label);
  requireBooleanField(status, "webSearchEnabled", label);
  requireOneOfField(status, "mode", AGENTIC_STATUS_MODES, label);
  requireStringArrayField(status, "notes", label);

  return payload as AgenticResearchStatus;
}

function validateResearchDataStatus(
  payload: unknown,
  label: string,
): ResearchDataStatus {
  const status = requireRecord(payload, label);
  const policyRate = requireRecordField(
    status,
    "bankOfCanadaPolicyRate",
    label,
  );
  const path = `${label}.bankOfCanadaPolicyRate`;

  requireStringFields(policyRate, path, ["source", "series", "url"]);
  requireNumberField(policyRate, "cacheTtlSeconds", path);
  requireOptionalNumberField(policyRate, "failureCooldownSeconds", path);
  requireBooleanField(policyRate, "cached", path);
  requireOptionalBooleanField(policyRate, "inFailureCooldown", path);
  requireOptionalStringOrNullField(policyRate, "nextRetryAt", path);
  requireOneOfField(policyRate, "lastResult", POLICY_RATE_RESULTS, path);
  requireStringOrNullField(policyRate, "lastAttemptAt", path);
  requireStringOrNullField(policyRate, "lastLiveFetchAt", path);
  requireStringOrNullField(policyRate, "lastError", path);

  return payload as ResearchDataStatus;
}

function validatePanel(panel: JsonRecord, path: string) {
  requireStringField(panel, "title", path);
  requireStringArrayField(panel, "points", path);
}

function validateMetrics(run: JsonRecord, label: string) {
  validateObjectArrayField(run, "metrics", label, (metric, path) => {
    requireStringFields(metric, path, ["label", "value", "detail", "tone"]);
  });
}

function validateAgents(run: JsonRecord, label: string) {
  validateObjectArrayField(run, "agents", label, (agent, path) => {
    requireStringFields(agent, path, ["name", "role", "status", "duration"]);
    requireStringArrayField(agent, "output", path);
  });
}

function validateTransmissionNodes(run: JsonRecord, label: string) {
  validateObjectArrayField(run, "transmissionNodes", label, (node, path) => {
    requireStringFields(node, path, [
      "id",
      "label",
      "subtitle",
      "driver",
      "confidence",
      "researchImplication",
      "whyItMatters",
      "polarity",
    ]);
    requireOneOfField(node, "evidenceType", EVIDENCE_LABELS, path);
    requireNumberField(node, "x", path);
    requireNumberField(node, "y", path);
  });
}

function validateTransmissionEdges(run: JsonRecord, label: string) {
  validateObjectArrayField(run, "transmissionEdges", label, (edge, path) => {
    requireStringFields(edge, path, [
      "id",
      "source",
      "target",
      "label",
      "polarity",
    ]);
  });
}

function validateCharts(run: JsonRecord, label: string) {
  validateObjectArrayField(run, "charts", label, (chart, path) => {
    requireStringFields(chart, path, ["title", "subtitle", "unit", "tone"]);
    requireArrayField(chart, "data", path).forEach((point, index) => {
      const pointPath = `${path}.data[${index}]`;
      const pointRecord = requireRecord(point, pointPath);
      requireStringField(pointRecord, "period", pointPath);
      requireNumberField(pointRecord, "value", pointPath);
      requireOptionalNumberField(pointRecord, "comparison", pointPath);
    });
  });
}

function validateEvidence(run: JsonRecord, label: string) {
  validateObjectArrayField(run, "evidence", label, (item, path) => {
    requireStringFields(item, path, [
      "claim",
      "confidence",
      "importance",
      "driver",
    ]);
    requireOneOfField(item, "type", EVIDENCE_LABELS, path);
    requireOptionalStringField(item, "sourceLabel", path);
    requireOptionalStringField(item, "sourceType", path);
    requireOptionalStringField(item, "sourceQuality", path);
  });
}

function validateMemo(run: JsonRecord, label: string) {
  validateObjectArrayField(run, "memo", label, (section, path) => {
    requireStringFields(section, path, ["title", "body"]);
  });
}

function validateOpenQuestions(run: JsonRecord, label: string) {
  validateObjectArrayField(run, "openQuestions", label, (question, path) => {
    requireStringFields(question, path, ["question", "whyItMatters", "owner"]);
  });
}

function validateObjectArrayField(
  record: JsonRecord,
  field: string,
  path: string,
  validateItem: (item: JsonRecord, itemPath: string) => void,
) {
  requireArrayField(record, field, path).forEach((value, index) => {
    const itemPath = `${path}.${field}[${index}]`;
    validateItem(requireRecord(value, itemPath), itemPath);
  });
}

function requireRecord(value: unknown, path: string): JsonRecord {
  if (!isRecord(value)) {
    throwInvalidPayload(path, "object");
  }
  return value;
}

function requireRecordField(
  record: JsonRecord,
  field: string,
  path: string,
): JsonRecord {
  return requireRecord(record[field], `${path}.${field}`);
}

function requireArrayField(
  record: JsonRecord,
  field: string,
  path: string,
): unknown[] {
  const value = record[field];
  if (!Array.isArray(value)) {
    throwInvalidPayload(`${path}.${field}`, "array");
  }
  return value;
}

function requireStringArrayField(
  record: JsonRecord,
  field: string,
  path: string,
) {
  requireArrayField(record, field, path).forEach((value, index) => {
    if (typeof value !== "string") {
      throwInvalidPayload(`${path}.${field}[${index}]`, "string");
    }
  });
}

function requireStringFields(
  record: JsonRecord,
  path: string,
  fields: string[],
) {
  fields.forEach((field) => requireStringField(record, field, path));
}

function requireStringField(record: JsonRecord, field: string, path: string) {
  if (typeof record[field] !== "string") {
    throwInvalidPayload(`${path}.${field}`, "string");
  }
}

function requireOptionalStringField(
  record: JsonRecord,
  field: string,
  path: string,
) {
  if (record[field] !== undefined && typeof record[field] !== "string") {
    throwInvalidPayload(`${path}.${field}`, "string when present");
  }
}

function requireStringOrNullField(
  record: JsonRecord,
  field: string,
  path: string,
) {
  const value = record[field];
  if (typeof value !== "string" && value !== null) {
    throwInvalidPayload(`${path}.${field}`, "string or null");
  }
}

function requireOptionalStringOrNullField(
  record: JsonRecord,
  field: string,
  path: string,
) {
  const value = record[field];
  if (value !== undefined && typeof value !== "string" && value !== null) {
    throwInvalidPayload(`${path}.${field}`, "string or null when present");
  }
}

function requireNumberField(record: JsonRecord, field: string, path: string) {
  if (typeof record[field] !== "number") {
    throwInvalidPayload(`${path}.${field}`, "number");
  }
}

function requireOptionalNumberField(
  record: JsonRecord,
  field: string,
  path: string,
) {
  if (record[field] !== undefined && typeof record[field] !== "number") {
    throwInvalidPayload(`${path}.${field}`, "number when present");
  }
}

function requireBooleanField(record: JsonRecord, field: string, path: string) {
  if (typeof record[field] !== "boolean") {
    throwInvalidPayload(`${path}.${field}`, "boolean");
  }
}

function requireOptionalBooleanField(
  record: JsonRecord,
  field: string,
  path: string,
) {
  if (record[field] !== undefined && typeof record[field] !== "boolean") {
    throwInvalidPayload(`${path}.${field}`, "boolean when present");
  }
}

function requireOneOfField(
  record: JsonRecord,
  field: string,
  allowedValues: Set<string>,
  path: string,
) {
  const value = record[field];
  if (typeof value !== "string" || !allowedValues.has(value)) {
    throwInvalidPayload(`${path}.${field}`, "allowed value");
  }
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function throwInvalidPayload(path: string, expected: string): never {
  throw new Error(`${path} is malformed; expected ${expected}`);
}
