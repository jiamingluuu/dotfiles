#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const schemaPath = path.resolve(
  scriptDirectory,
  "..",
  "assets",
  "schemas",
  "task-analysis.schema.json",
);
const reportSchema = JSON.parse(fs.readFileSync(schemaPath, "utf8"));
const analyzerRunSchema = reportSchema.$defs.analyzerRun;
const analyzerRunProperties = analyzerRunSchema.properties;
const analyzerRunRequiredKeys = new Set(analyzerRunSchema.required);
const ROOT_CAUSE_TYPES = reportSchema.$defs.rootCauseType.enum;
const CONFIDENCE_LEVELS = reportSchema.$defs.confidence.enum;
const EXPECTEDNESS_VALUES = reportSchema.$defs.expectedness.enum;
const FINDING_REASON_VALUES = reportSchema.$defs.findingReason.enum;
const CODE_CORRELATIONS = reportSchema.$defs.codeCorrelation.enum;
const ANALYZER_STATES = reportSchema.$defs.analyzerState.enum;
const TASK_VALIDITY_VALUES = reportSchema.$defs.taskValidity.enum;
const ATTRIBUTION_VALUES = reportSchema.$defs.attributionCompleteness.enum;
const RELEASE_ADVICE_VALUES = reportSchema.$defs.releaseAdvice.enum;
const EVIDENCE_KINDS = reportSchema.$defs.evidenceKind.enum;
const SEVERITY_LEVELS = reportSchema.$defs.severity.enum;
const SIMPLE_EVIDENCE_KINDS = ["requirement", "merge_request"];
const ROOT_KEYS = reportSchema.required;
const FINDING_KEYS = reportSchema.$defs.finding.required;
const FINDING_ALLOWED_KEYS = Object.keys(reportSchema.$defs.finding.properties);
const ADMISSION_KEYS = reportSchema.$defs.admission.oneOf[1].required;
const ANALYZER_RUN_REQUIRED_KEYS = analyzerRunSchema.required;
const ANALYZER_RUN_ALLOWED_KEYS = Object.keys(analyzerRunProperties);
const ANALYZER_STATE_FIELDS = [
  ...new Set(
    analyzerRunSchema.oneOf.flatMap((variant) => [
      ...(variant.required ?? []),
      ...(variant.not?.anyOf ?? []).flatMap((constraint) => constraint.required ?? []),
    ]),
  ),
];
const ANALYZER_STATE_LABELS = {
  invalid_observation: "输入观察无效",
  analysis_incomplete: "分析未完成",
  evidence_blocked: "证据受阻",
  proven_code_caused: "已证明由代码变更导致",
  proven_not_code_caused: "已证明非代码变更导致",
  runtime_unresolved: "运行时未决",
};
const ANALYZER_OPTIONAL_SUMMARY_FIELDS = Object.keys(analyzerRunProperties).filter(
  (key) => !analyzerRunRequiredKeys.has(key) && !ANALYZER_STATE_FIELDS.includes(key),
);
const TERMINAL_SELF_PROOF = Object.fromEntries(
  Object.entries(analyzerRunProperties.self_proof.properties).map(([key, definition]) => [
    key,
    definition.const,
  ]),
);
const IMMUTABLE_COMMIT_PATTERN = /^[0-9a-f]{40}(?:[0-9a-f]{24})?$/iu;
const ANALYZER_COMMIT_PATTERN = /^[0-9a-f]{40}$/u;
const ANALYZER_REPOSITORY_PATTERN = new RegExp(analyzerRunProperties.repository.pattern, "u");
const SHA256_PATTERN = new RegExp(
  analyzerRunProperties.result_artifact.properties.sha256.pattern,
  "u",
);
const ISO_DATE_TIME_PATTERN =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/u;
const ADMISSION_EVIDENCE_KINDS = {
  behavior_anomaly_evidence_ids: new Set(["flow"]),
  business_ownership_evidence_ids: new Set(["code"]),
  real_trigger_evidence_ids: new Set(["flow", "log", "trace"]),
  producer_transport_evidence_ids: new Set(["flow", "code", "log", "trace"]),
  consumer_impact_evidence_ids: new Set(["flow", "code", "log", "trace"]),
  code_causality_evidence_ids: new Set(["code"]),
  counterexample_evidence_ids: new Set([
    "flow",
    "code",
    "log",
    "trace",
    "config",
    "deployment",
    "requirement",
    "merge_request",
  ]),
};
const SENSITIVE_PATTERNS = [
  /\bauthorization\s*[:=]\s*\S+/iu,
  /\bcookie\s*[:=]\s*\S+/iu,
  /\bbearer\s+[A-Za-z0-9._~+/=-]{8,}/iu,
  /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b/u,
  /[?&](?:access[_-]?token|token|signature|secret|x-amz-signature)=[^&#\s]+/iu,
  /\bdisposable_login_token\b/iu,
];
const PLACEHOLDER_PATTERN = /\{\{[A-Z0-9_]+\}\}|(?:IF|REPEAT)_[A-Z0-9_]+/u;
const PLACEHOLDER_FLOW_ID_PATTERN =
  /^(?:unknown|unresolved|pending|placeholder|未解析(?:失败)?(?:流量|台账)?|失败台账|待补(?:充)?(?:流量)?)(?:[-_: \u3000]*\d+)?$/iu;
const templateDirectory = path.resolve(scriptDirectory, "..", "assets", "templates");
const FINDING_SUMMARY_MAX_LENGTH = 200;
const INVESTIGATION_OUTCOME_MAX_LENGTH = 300;
const SAMPLE_DISPLAY_NAME_MAX_LENGTH = 30;
const MAX_RENDERED_SAMPLES = 10;
const INVESTIGATION_SOURCES = ["code", "log", "trace", "response", "configuration", "deployment"];
const SEVERITY_RANK = new Map([
  ["P0", 0],
  ["P1", 1],
  ["P2", 2],
  ["P3", 3],
]);
const CONFIDENCE_RANK = new Map([
  ["高", 0],
  ["低", 1],
]);
const EVIDENCE_PRIORITY = new Map([
  ["code", 0],
  ["task_config", 0],
  ["config", 0],
  ["deployment", 0],
  ["log", 1],
  ["trace", 1],
  ["flow", 2],
  ["requirement", 4],
  ["merge_request", 4],
  ["error_catalog", 5],
  ["evidence_boundary", 6],
]);
const ROOT_CAUSE_EVIDENCE_KINDS = new Set([
  "code",
  "log",
  "trace",
  "task_config",
  "config",
  "deployment",
]);
const REPLAY_REPORT_ORIGINS = new Map([
  ["tesla-x.bytedance.net", "https://tesla-x.bytedance.net"],
  ["tesla-x-zg.bytedance.net", "https://tesla-x-zg.bytedance.net"],
  ["tesla-x-us.tiktok-row.net", "https://tesla-x-us.tiktok-row.net"],
  ["tesla-x-mycis.bytedance.net", "https://tesla-x-mycis.bytedance.net"],
  ["teslax-boe.bytedance.net", "https://teslax-boe.bytedance.net"],
]);

export function classifyFindingSeverity(findingReason, confidence) {
  const severityByReason = {
    业务缺陷: { 高: "P0", 低: "P1" },
    预期变更: { 高: "P2", 低: "P1" },
    噪音: { 高: "P2", 低: "P1" },
    FTF平台问题: { 高: "P3", 低: "P2" },
  };
  const severityByConfidence = severityByReason[findingReason];
  if (!severityByConfidence) {
    fail(`unknown Finding reason: ${findingReason}`);
  }
  const severity = severityByConfidence[confidence];
  if (!severity) {
    fail(`unknown Finding confidence: ${confidence}`);
  }
  return severity;
}

function fail(message) {
  throw new Error(message);
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireObject(value, at) {
  if (!isObject(value)) {
    fail(`${at} must be an object`);
  }
  return value;
}

function requireArray(value, at) {
  if (!Array.isArray(value)) {
    fail(`${at} must be an array`);
  }
  return value;
}

function requireString(value, at, { nullable = false } = {}) {
  if (nullable && value === null) {
    return value;
  }
  if (typeof value !== "string" || value.length === 0) {
    fail(`${at} must be a non-empty string`);
  }
  return value;
}

function requireStringWithin(value, at, maxLength) {
  requireString(value, at);
  if ([...value].length > maxLength) {
    fail(`${at} must contain at most ${maxLength} characters`);
  }
  return value;
}

function requireInteger(value, at, { nullable = false } = {}) {
  if (nullable && value === null) {
    return value;
  }
  if (!Number.isInteger(value) || value < 0) {
    fail(`${at} must be a non-negative integer`);
  }
  return value;
}

function requireRatio(value, at) {
  if (value === null) {
    return;
  }
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) {
    fail(`${at} must be null or a number between 0 and 1`);
  }
}

function requireBoolean(value, at) {
  if (typeof value !== "boolean") {
    fail(`${at} must be a boolean`);
  }
}

function requireEnum(value, allowed, at) {
  if (!allowed.includes(value)) {
    fail(`${at} must be one of: ${allowed.join(", ")}`);
  }
}

function requireExactKeys(value, required, at, allowed = required) {
  const keys = Object.keys(requireObject(value, at));
  const missing = required.filter((key) => !Object.hasOwn(value, key));
  const extra = keys.filter((key) => !allowed.includes(key));
  if (missing.length > 0) {
    fail(`${at}.${missing[0]} is required`);
  }
  if (extra.length > 0) {
    fail(`${at}.${extra[0]} is not allowed`);
  }
}

function requireUniqueStrings(value, at) {
  const items = requireArray(value, at);
  const seen = new Set();
  for (const [index, item] of items.entries()) {
    requireString(item, `${at}[${index}]`);
    if (seen.has(item)) {
      fail(`${at} must contain unique values`);
    }
    seen.add(item);
  }
  return items;
}

function requireStrings(value, at) {
  const items = requireArray(value, at);
  for (const [index, item] of items.entries()) {
    requireString(item, `${at}[${index}]`);
  }
  return items;
}

function requireRealFlowId(value, at) {
  requireString(value, at);
  if (PLACEHOLDER_FLOW_ID_PATTERN.test(value.trim())) {
    fail(`${at} must be a real Flow ID from the frozen task inventory, not a placeholder`);
  }
}

function canonicalize(value) {
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

function sameObject(left, right) {
  return JSON.stringify(canonicalize(left)) === JSON.stringify(canonicalize(right));
}

function requireDateTime(value, at) {
  requireString(value, at);
  if (!ISO_DATE_TIME_PATTERN.test(value) || Number.isNaN(Date.parse(value))) {
    fail(`${at} must be an ISO date-time`);
  }
}

function requireImmutableCommit(value, at, { nullable = false } = {}) {
  if (nullable && value === null) {
    return value;
  }
  requireString(value, at);
  if (!IMMUTABLE_COMMIT_PATTERN.test(value)) {
    fail(`${at} must be a full immutable commit`);
  }
  return value;
}

// metadata identity 允许 40 位或 64 位、大小写混合的 commit，analyzer refs 只接受 40 位小写。
// 比对前把 metadata 侧收敛到 analyzer 形态，避免两侧约束互斥导致无法满足的状态。
// 经 wrapper 产出的报告不会命中该互斥（wrapper 已强制 analyzer commit 为 40 位小写），
// 这里防御的是离线重放、人工编辑等绕过 wrapper 的报告来源。
function normalizeAnalyzerCommit(value) {
  return value.toLowerCase().slice(0, 40);
}

function normalizeCodebaseRepository(value, at) {
  requireString(value, at);
  let repositoryPath = value;
  if (value.startsWith("git@code.byted.org:")) {
    repositoryPath = value.slice("git@code.byted.org:".length);
    if (/[?#]/u.test(repositoryPath)) {
      fail(`${at} must be a canonical Codebase repository`);
    }
  } else if (value.startsWith("https://")) {
    let repositoryUrl;
    try {
      repositoryUrl = new URL(value);
    } catch {
      fail(`${at} must be a canonical Codebase repository`);
    }
    if (
      repositoryUrl.hostname !== "code.byted.org" ||
      repositoryUrl.port ||
      repositoryUrl.username ||
      repositoryUrl.password ||
      repositoryUrl.search ||
      repositoryUrl.hash
    ) {
      fail(`${at} must be a canonical Codebase repository`);
    }
    repositoryPath = repositoryUrl.pathname.slice(1);
  }
  const repository = repositoryPath.replace(/\.git$/u, "");
  const segments = repository.split("/");
  if (
    !ANALYZER_REPOSITORY_PATTERN.test(repository) ||
    segments.some((segment) => segment === "." || segment === "..")
  ) {
    fail(`${at} must be a canonical Codebase repository`);
  }
  return repository;
}

function matchesCodebaseRepository(repository, identityRepository, at) {
  return (
    identityRepository !== null &&
    repository === normalizeCodebaseRepository(identityRepository, at)
  );
}

function validateIdentity(identity, at) {
  requireExactKeys(identity, ["psm", "repository", "branch", "commit", "environment"], at);
  requireString(identity.psm, `${at}.psm`);
  requireString(identity.repository, `${at}.repository`, { nullable: true });
  requireString(identity.branch, `${at}.branch`, { nullable: true });
  requireImmutableCommit(identity.commit, `${at}.commit`, { nullable: true });
  requireString(identity.environment, `${at}.environment`);
}

function validateMetadata(metadata) {
  const at = "metadata";
  requireExactKeys(
    metadata,
    [
      "task_id",
      "task_url",
      "snapshot_time",
      "task_update_time",
      "space_id",
      "psm",
      "environment",
      "target_identity",
      "base_identity",
      "filters",
    ],
    at,
  );
  for (const key of ["task_id", "task_url", "space_id", "psm", "environment"]) {
    requireString(metadata[key], `${at}.${key}`);
  }
  validateUrl(metadata.task_url, `${at}.task_url`, { httpsOnly: true });
  buildReplayReportUrl(metadata);
  requireDateTime(metadata.snapshot_time, `${at}.snapshot_time`);
  requireDateTime(metadata.task_update_time, `${at}.task_update_time`);
  validateIdentity(metadata.target_identity, `${at}.target_identity`);
  validateIdentity(metadata.base_identity, `${at}.base_identity`);
  requireUniqueStrings(metadata.filters, `${at}.filters`);
}

function validateVerdict(verdict) {
  const at = "verdict";
  requireExactKeys(
    verdict,
    [
      "confirmed_defect_count",
      "summary",
      "task_validity",
      "task_validity_reason",
      "attribution_completeness",
      "attribution_completeness_reason",
      "release_advice",
      "release_advice_reason",
    ],
    at,
  );
  requireInteger(verdict.confirmed_defect_count, `${at}.confirmed_defect_count`);
  requireString(verdict.summary, `${at}.summary`);
  requireEnum(verdict.task_validity, TASK_VALIDITY_VALUES, `${at}.task_validity`);
  requireString(verdict.task_validity_reason, `${at}.task_validity_reason`);
  requireEnum(
    verdict.attribution_completeness,
    ATTRIBUTION_VALUES,
    `${at}.attribution_completeness`,
  );
  requireString(verdict.attribution_completeness_reason, `${at}.attribution_completeness_reason`);
  requireEnum(verdict.release_advice, RELEASE_ADVICE_VALUES, `${at}.release_advice`);
  requireString(verdict.release_advice_reason, `${at}.release_advice_reason`);
}

function validateInventory(inventory, at, idKey, unresolvedKey) {
  requireExactKeys(inventory, ["total", idKey, unresolvedKey], at);
  requireInteger(inventory.total, `${at}.total`);
  const ids = requireUniqueStrings(inventory[idKey], `${at}.${idKey}`);
  const unresolved = requireUniqueStrings(inventory[unresolvedKey], `${at}.${unresolvedKey}`);
  if (inventory.total !== ids.length) {
    fail(`${at}.total must equal ${at}.${idKey}.length`);
  }
  for (const id of unresolved) {
    if (!ids.includes(id)) {
      fail(`${at}.${unresolvedKey} contains unknown ID ${id}`);
    }
  }
}

function validateScope(scope) {
  const at = "scope";
  requireExactKeys(
    scope,
    ["analysis_methods", "diff_inventory", "replay_failure_inventory", "final_task_update_time"],
    at,
  );
  requireUniqueStrings(scope.analysis_methods, `${at}.analysis_methods`);
  validateInventory(
    scope.diff_inventory,
    `${at}.diff_inventory`,
    "cluster_ids",
    "unresolved_cluster_ids",
  );
  validateInventory(
    scope.replay_failure_inventory,
    `${at}.replay_failure_inventory`,
    "flow_ids",
    "unresolved_flow_ids",
  );
  for (const [index, flowId] of scope.replay_failure_inventory.flow_ids.entries()) {
    requireRealFlowId(flowId, `${at}.replay_failure_inventory.flow_ids[${index}]`);
  }
  for (const [index, flowId] of scope.replay_failure_inventory.unresolved_flow_ids.entries()) {
    requireRealFlowId(flowId, `${at}.replay_failure_inventory.unresolved_flow_ids[${index}]`);
  }
  requireDateTime(scope.final_task_update_time, `${at}.final_task_update_time`);
}

function validateFunnel(funnel) {
  const at = "funnel";
  const keys = [
    "total_flows",
    "sent_success",
    "sent_failure",
    "abnormal_responses",
    "unasserted",
    "diff_flows",
    "pending_confirmation",
  ];
  requireExactKeys(funnel, keys, at);
  for (const key of keys) {
    requireInteger(funnel[key], `${at}.${key}`, { nullable: key === "unasserted" });
  }
  if (funnel.sent_success + funnel.sent_failure !== funnel.total_flows) {
    fail("funnel.sent_success + funnel.sent_failure must equal funnel.total_flows");
  }
  if (funnel.abnormal_responses > funnel.sent_success) {
    fail("funnel.abnormal_responses cannot exceed funnel.sent_success");
  }
  if (funnel.unasserted !== null && funnel.unasserted > funnel.sent_success) {
    fail("funnel.unasserted cannot exceed funnel.sent_success");
  }
  if (funnel.pending_confirmation > funnel.diff_flows) {
    fail("funnel.pending_confirmation cannot exceed funnel.diff_flows");
  }
}

function validateTestSufficiency(sufficiency) {
  const at = "test_sufficiency";
  requireExactKeys(
    sufficiency,
    [
      "expected_methods",
      "expected_method_keys",
      "actual_methods",
      "interface_coverage",
      "code_coverage",
      "scene_coverage",
      "method_coverage_details",
    ],
    at,
  );
  requireInteger(sufficiency.expected_methods, `${at}.expected_methods`, { nullable: true });
  requireInteger(sufficiency.actual_methods, `${at}.actual_methods`, { nullable: true });
  if (sufficiency.expected_method_keys === null) {
    if (
      sufficiency.expected_methods !== null ||
      sufficiency.actual_methods !== null ||
      sufficiency.interface_coverage !== null ||
      sufficiency.method_coverage_details !== null
    ) {
      fail(
        `${at}.expected_methods, ${at}.actual_methods, ${at}.interface_coverage, and ${at}.method_coverage_details must be null when expected_method_keys is null`,
      );
    }
  } else {
    const methodKeys = requireUniqueStrings(
      sufficiency.expected_method_keys,
      `${at}.expected_method_keys`,
    );
    if (sufficiency.expected_methods !== methodKeys.length) {
      fail(`${at}.expected_methods must equal expected_method_keys.length`);
    }
    const details = requireArray(
      sufficiency.method_coverage_details,
      `${at}.method_coverage_details`,
    );
    const detailMethods = new Set();
    let detailsComplete = true;
    let replayedMethods = 0;
    let effectivelyCoveredMethods = 0;
    for (const [index, detail] of details.entries()) {
      const detailAt = `${at}.method_coverage_details[${index}]`;
      requireExactKeys(detail, ["method", "total_flows", "failed_flows"], detailAt);
      requireString(detail.method, `${detailAt}.method`);
      requireInteger(detail.total_flows, `${detailAt}.total_flows`, { nullable: true });
      requireInteger(detail.failed_flows, `${detailAt}.failed_flows`, { nullable: true });
      if (!methodKeys.includes(detail.method)) {
        fail(`${detailAt}.method must identify an expected method`);
      }
      if (detailMethods.has(detail.method)) {
        fail(`${at}.method_coverage_details contains duplicate method ${detail.method}`);
      }
      detailMethods.add(detail.method);
      if (detail.total_flows === null || detail.failed_flows === null) {
        if (detail.total_flows !== null || detail.failed_flows !== null) {
          fail(`${detailAt}.total_flows and ${detailAt}.failed_flows must both be known or null`);
        }
        detailsComplete = false;
      } else {
        if (detail.failed_flows > detail.total_flows) {
          fail(`${detailAt}.failed_flows cannot exceed total_flows`);
        }
        if (detail.total_flows > 0) {
          replayedMethods += 1;
        }
        if (detail.total_flows - detail.failed_flows > 0) {
          effectivelyCoveredMethods += 1;
        }
      }
    }
    if (!sameObject([...detailMethods].sort(), [...methodKeys].sort())) {
      fail(`${at}.method_coverage_details must cover every expected method exactly once`);
    }
    if (methodKeys.length === 0) {
      if (sufficiency.actual_methods !== 0 || sufficiency.interface_coverage !== null) {
        fail(
          `${at}.actual_methods must be 0 and interface_coverage must be null when expected_method_keys is empty`,
        );
      }
    } else if (!detailsComplete) {
      if (sufficiency.actual_methods !== null || sufficiency.interface_coverage !== null) {
        fail(
          `${at}.actual_methods and ${at}.interface_coverage must be null when method coverage details are incomplete`,
        );
      }
    } else {
      if (sufficiency.actual_methods !== replayedMethods) {
        fail(`${at}.actual_methods must equal replayed method count`);
      }
      const expectedCoverage = effectivelyCoveredMethods / methodKeys.length;
      if (
        sufficiency.interface_coverage === null ||
        Math.abs(sufficiency.interface_coverage - expectedCoverage) > Number.EPSILON * 16
      ) {
        fail(
          `${at}.interface_coverage must equal effectively covered method count / expected_method_keys.length`,
        );
      }
    }
  }
  for (const key of ["interface_coverage", "code_coverage", "scene_coverage"]) {
    requireRatio(sufficiency[key], `${at}.${key}`);
  }
}

function validateUrl(value, at, { httpsOnly = false } = {}) {
  requireString(value, at);
  let url;
  try {
    url = new URL(value);
  } catch {
    fail(`${at} must be a valid URL`);
  }
  const allowed = httpsOnly ? ["https:"] : ["https:", "file:"];
  if (!allowed.includes(url.protocol)) {
    fail(`${at} URL must use ${httpsOnly ? "https://" : "https:// or file://"}`);
  }
  if (url.username || url.password) {
    fail(`${at} URL must not contain credentials`);
  }
  if (url.href !== value) {
    fail(`${at} must be a canonical percent-encoded URL`);
  }
  if (url.protocol === "file:") {
    if (url.hostname || url.search || url.hash) {
      fail(`${at} file URL must identify a local absolute path without query or fragment`);
    }
  }
  validateSafeString(value, at);
  return url;
}

export function buildReplayReportUrl(metadata) {
  const taskUrl = new URL(metadata.task_url);
  const origin = REPLAY_REPORT_ORIGINS.get(taskUrl.hostname);
  if (!origin) {
    fail(`metadata.task_url host is not supported for replay reports: ${taskUrl.hostname}`);
  }
  return `${origin}/space/${encodeURIComponent(metadata.space_id)}/case/report/ftf/task/new/${encodeURIComponent(metadata.task_id)}`;
}

function validateSafeString(value, at) {
  if (typeof value !== "string") {
    return;
  }
  for (const pattern of SENSITIVE_PATTERNS) {
    if (pattern.test(value)) {
      fail(`${at} contains credential-shaped content`);
    }
  }
}

function scanSensitive(value, at = "$") {
  if (typeof value === "string") {
    validateSafeString(value, at);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => scanSensitive(item, `${at}[${index}]`));
    return;
  }
  if (isObject(value)) {
    for (const [key, item] of Object.entries(value)) {
      scanSensitive(item, `${at}.${key}`);
    }
  }
}

function memberIdentity(sourceType, sourceId) {
  return `${sourceType}\u0000${sourceId}`;
}

function validateEvidenceMemberRefs(memberRefs, at) {
  const refs = requireArray(memberRefs, at);
  if (refs.length === 0) {
    fail(`${at} must contain at least one attribution member reference`);
  }
  const identities = new Set();
  for (const [index, ref] of refs.entries()) {
    const refAt = `${at}[${index}]`;
    requireExactKeys(ref, ["source_type", "source_id"], refAt);
    requireEnum(ref.source_type, ["diff_cluster", "replay_failure"], `${refAt}.source_type`);
    requireString(ref.source_id, `${refAt}.source_id`);
    const identity = memberIdentity(ref.source_type, ref.source_id);
    if (identities.has(identity)) {
      fail(`${at} must contain unique attribution member references`);
    }
    identities.add(identity);
  }
}

function validateCodeEvidence(evidence, at) {
  requireExactKeys(
    evidence,
    [
      "id",
      "kind",
      "summary",
      "url",
      "psm",
      "repository",
      "ref",
      "member_refs",
      "file",
      "line_start",
      "line_end",
      "symbol",
      "logic",
      ...(Object.hasOwn(evidence, "excerpt") ? ["excerpt"] : []),
    ],
    at,
  );
  for (const key of ["id", "summary", "psm", "repository", "ref", "file", "symbol", "logic"]) {
    requireString(evidence[key], `${at}.${key}`);
  }
  requireImmutableCommit(evidence.ref, `${at}.ref`);
  validateEvidenceMemberRefs(evidence.member_refs, `${at}.member_refs`);
  requireEnum(evidence.kind, ["code", "error_catalog"], `${at}.kind`);
  requireInteger(evidence.line_start, `${at}.line_start`);
  requireInteger(evidence.line_end, `${at}.line_end`);
  if (evidence.line_start < 1 || evidence.line_end < evidence.line_start) {
    fail(`${at} line range is invalid`);
  }
  const url = validateUrl(evidence.url, `${at}.url`, { httpsOnly: true });
  const expectedPath = `/${evidence.repository}/blob/${evidence.ref}/${evidence.file}`;
  const expectedHash = `#L${evidence.line_start}-L${evidence.line_end}`;
  if (
    url.hostname !== "code.byted.org" ||
    decodeURIComponent(url.pathname) !== expectedPath ||
    url.hash !== expectedHash
  ) {
    fail(`${at}.url must deep-link repository, ref, file, and line range`);
  }
  if (Object.hasOwn(evidence, "excerpt")) {
    requireString(evidence.excerpt, `${at}.excerpt`);
    const excerptLines = evidence.excerpt.split(/\r?\n/u).length;
    if (excerptLines > 20) {
      fail(`${at}.excerpt must contain at most 20 lines`);
    }
    if (excerptLines > evidence.line_end - evidence.line_start + 1) {
      fail(`${at}.excerpt cannot exceed the declared source line range`);
    }
  }
}

function validateRuntimeEvidence(evidence, at) {
  requireExactKeys(
    evidence,
    [
      "id",
      "kind",
      "summary",
      "url",
      "psm",
      "log_id_or_trace_id",
      "member_refs",
      "flow_ids",
      "time_window",
      "observation",
    ],
    at,
  );
  requireEnum(evidence.kind, ["log", "trace"], `${at}.kind`);
  for (const key of ["id", "summary", "psm", "log_id_or_trace_id", "time_window", "observation"]) {
    requireString(evidence[key], `${at}.${key}`);
  }
  validateEvidenceMemberRefs(evidence.member_refs, `${at}.member_refs`);
  const flowIds = requireUniqueStrings(evidence.flow_ids, `${at}.flow_ids`);
  if (flowIds.length === 0) {
    fail(`${at}.flow_ids must contain at least one Flow ID`);
  }
  flowIds.forEach((flowId, index) => requireRealFlowId(flowId, `${at}.flow_ids[${index}]`));
  if (evidence.url !== null) {
    try {
      const url = validateUrl(evidence.url, `${at}.${evidence.kind}.url`, { httpsOnly: true });
      if (
        url.hostname.startsWith("tesla-x") ||
        url.pathname.includes("/case/report/ftf/") ||
        url.pathname.includes("/f_app/task/new/diff/") ||
        url.pathname.includes("/f_app/task/diff/")
      ) {
        fail(`${at}.${evidence.kind}.url must deep-link runtime evidence, not an FTF detail page`);
      }
    } catch (error) {
      fail(`${at}.${evidence.kind}.url is invalid: ${error.message}`);
    }
  }
  const [start, end, ...extra] = evidence.time_window.split("/");
  if (extra.length > 0 || !start || !end) {
    fail(`${at}.time_window must be an ISO date-time interval`);
  }
  requireDateTime(start, `${at}.time_window start`);
  requireDateTime(end, `${at}.time_window end`);
  if (Date.parse(start) > Date.parse(end)) {
    fail(`${at}.time_window start must not be after end`);
  }
}

function validateMechanismEvidence(evidence, at) {
  requireExactKeys(
    evidence,
    [
      "id",
      "kind",
      "summary",
      "url",
      "psm",
      "subject",
      "effective_time_window",
      "observed_value",
      "logic",
    ],
    at,
  );
  requireEnum(evidence.kind, ["task_config", "config", "deployment"], `${at}.kind`);
  for (const key of [
    "id",
    "summary",
    "psm",
    "subject",
    "effective_time_window",
    "observed_value",
    "logic",
  ]) {
    requireString(evidence[key], `${at}.${key}`);
  }
  const url = validateUrl(evidence.url, `${at}.${evidence.kind}.url`);
  if (
    evidence.kind !== "task_config" &&
    (url.hostname.startsWith("tesla-x") ||
      url.pathname.includes("/case/report/ftf/") ||
      url.pathname.includes("/f_app/task/new/diff/") ||
      url.pathname.includes("/f_app/task/diff/"))
  ) {
    fail(`${at}.${evidence.kind}.url must deep-link mechanism evidence, not an FTF detail page`);
  }
  const [start, end, ...extra] = evidence.effective_time_window.split("/");
  if (extra.length > 0 || !start || !end) {
    fail(`${at}.effective_time_window must be an ISO date-time interval`);
  }
  requireDateTime(start, `${at}.effective_time_window start`);
  requireDateTime(end, `${at}.effective_time_window end`);
  if (Date.parse(start) > Date.parse(end)) {
    fail(`${at}.effective_time_window start must not be after end`);
  }
}

function validateFlowEvidence(evidence, at) {
  requireExactKeys(
    evidence,
    [
      "id",
      "kind",
      "summary",
      "url",
      "psm",
      "method",
      "direction",
      "observable_result",
      "source_id",
      "flow_id",
    ],
    at,
  );
  for (const key of [
    "id",
    "summary",
    "psm",
    "method",
    "observable_result",
    "source_id",
    "flow_id",
  ]) {
    requireString(evidence[key], `${at}.${key}`);
  }
  if (evidence.kind !== "flow") {
    fail(`${at}.kind must be flow`);
  }
  requireEnum(evidence.direction, ["inbound", "outbound"], `${at}.direction`);
  validateUrl(evidence.url, `${at}.url`, { httpsOnly: true });
}

function validateSimpleEvidence(evidence, at) {
  requireExactKeys(evidence, ["id", "kind", "summary", "url"], at);
  requireString(evidence.id, `${at}.id`);
  requireEnum(evidence.kind, SIMPLE_EVIDENCE_KINDS, `${at}.kind`);
  requireString(evidence.summary, `${at}.summary`);
  validateUrl(evidence.url, `${at}.url`);
}

function validateEvidenceBoundary(evidence, at) {
  requireExactKeys(
    evidence,
    ["id", "kind", "summary", "url", "reason", "recovery_action", "material"],
    at,
  );
  for (const key of ["id", "summary", "reason", "recovery_action"]) {
    requireString(evidence[key], `${at}.${key}`);
  }
  if (evidence.kind !== "evidence_boundary") {
    fail(`${at}.kind must be evidence_boundary`);
  }
  if (evidence.url !== null) {
    fail(`${at}.url must be null`);
  }
  requireBoolean(evidence.material, `${at}.material`);
}

function validateEvidence(evidence, at) {
  requireObject(evidence, at);
  requireEnum(evidence.kind, EVIDENCE_KINDS, `${at}.kind`);
  if (evidence.kind === "flow") {
    validateFlowEvidence(evidence, at);
  } else if (evidence.kind === "code" || evidence.kind === "error_catalog") {
    validateCodeEvidence(evidence, at);
  } else if (evidence.kind === "log" || evidence.kind === "trace") {
    validateRuntimeEvidence(evidence, at);
  } else if (
    evidence.kind === "task_config" ||
    evidence.kind === "config" ||
    evidence.kind === "deployment"
  ) {
    validateMechanismEvidence(evidence, at);
  } else if (evidence.kind === "evidence_boundary") {
    validateEvidenceBoundary(evidence, at);
  } else {
    validateSimpleEvidence(evidence, at);
  }
}

function validateRecommendation(recommendation, at) {
  requireExactKeys(
    recommendation,
    ["owner", "target", "change", "verification", "evidence_ids"],
    at,
  );
  for (const key of ["owner", "target", "change", "verification"]) {
    requireString(recommendation[key], `${at}.${key}`);
  }
  const evidenceIds = requireUniqueStrings(recommendation.evidence_ids, `${at}.evidence_ids`);
  if (evidenceIds.length === 0) {
    fail(`${at}.evidence_ids must contain at least one evidence ID`);
  }
}

function validateAdmission(admission, evidenceById, at) {
  if (admission === null) {
    return;
  }
  requireExactKeys(admission, ADMISSION_KEYS, at);
  for (const key of ADMISSION_KEYS) {
    const evidenceIds = requireUniqueStrings(admission[key], `${at}.${key}`);
    if (evidenceIds.length === 0) {
      fail(`${at}.${key} must contain at least one evidence ID`);
    }
    for (const id of evidenceIds) {
      const evidence = evidenceById.get(id);
      if (!evidence) {
        fail(`${at}.${key} contains unknown evidence ID ${id}`);
      }
      if (!ADMISSION_EVIDENCE_KINDS[key].has(evidence.kind)) {
        fail(`${at}.${key} cannot be proven by ${evidence.kind} evidence ${id}`);
      }
    }
  }
  if (!admission.code_causality_evidence_ids.some((id) => evidenceById.get(id)?.kind === "code")) {
    fail(`${at}.code_causality_evidence_ids must reference code evidence`);
  }
}

function validateAnalyzerRun(run, at, metadata, coveredClusterIds) {
  requireExactKeys(run, ANALYZER_RUN_REQUIRED_KEYS, at, ANALYZER_RUN_ALLOWED_KEYS);
  for (const key of ["task_id", "similar_diff_id", "repository", "path"]) {
    requireString(run[key], `${at}.${key}`);
  }
  requireEnum(run.analysis_state, ANALYZER_STATES, `${at}.analysis_state`);
  if (
    !ANALYZER_COMMIT_PATTERN.test(run.base_ref) ||
    !ANALYZER_COMMIT_PATTERN.test(run.target_ref)
  ) {
    fail(`${at} analyzer refs must be 40-character lowercase commits`);
  }
  if (
    !ANALYZER_REPOSITORY_PATTERN.test(run.repository) ||
    run.repository.split("/").some((segment) => segment === "." || segment === "..") ||
    run.repository.endsWith(".git")
  ) {
    fail(`${at}.repository must be a canonical Codebase repository path`);
  }
  requireEnum(run.op, ["add", "delete", "modify"], `${at}.op`);
  requireEnum(run.verdict, ["unknown", "caused", "not_caused"], `${at}.verdict`);
  if (run.caused_by_code_change !== null && typeof run.caused_by_code_change !== "boolean") {
    fail(`${at}.caused_by_code_change must be a boolean or null`);
  }
  requireEnum(run.confidence, ["high", "low"], `${at}.confidence`);
  requireExactKeys(
    run.aggregate,
    ["attribution_type", "caused_by_code_change", "confidence"],
    `${at}.aggregate`,
  );
  requireEnum(
    run.aggregate.attribution_type,
    ["bug_code", "not_code_related", "unknown"],
    `${at}.aggregate.attribution_type`,
  );
  if (
    run.aggregate.caused_by_code_change !== null &&
    typeof run.aggregate.caused_by_code_change !== "boolean"
  ) {
    fail(`${at}.aggregate.caused_by_code_change must be a boolean or null`);
  }
  requireRatio(run.aggregate.confidence, `${at}.aggregate.confidence`);
  if (run.aggregate.confidence === null) {
    fail(`${at}.aggregate.confidence must be a number between 0 and 1`);
  }
  const missingEvidence = requireStrings(run.missing_evidence, `${at}.missing_evidence`);
  const neededEvidence = requireStrings(run.needed_evidence, `${at}.needed_evidence`);
  requireUniqueStrings(run.warnings, `${at}.warnings`);
  for (const key of ANALYZER_OPTIONAL_SUMMARY_FIELDS) {
    if (Object.hasOwn(run, key)) {
      requireObject(run[key], `${at}.${key}`);
    }
  }
  requireExactKeys(run.result_artifact, ["bytes", "sha256"], `${at}.result_artifact`);
  requireInteger(run.result_artifact.bytes, `${at}.result_artifact.bytes`);
  if (run.result_artifact.bytes <= 0) {
    fail(`${at}.result_artifact.bytes must be greater than zero`);
  }
  requireString(run.result_artifact.sha256, `${at}.result_artifact.sha256`);
  if (!SHA256_PATTERN.test(run.result_artifact.sha256)) {
    fail(`${at}.result_artifact.sha256 must be a full SHA-256 digest`);
  }
  if (run.task_id !== metadata.task_id || !coveredClusterIds.includes(run.similar_diff_id)) {
    fail(`${at} analyzer request identity must match the task and a covered DIFF cluster`);
  }
  if (
    metadata.target_identity.repository !== null &&
    run.repository !==
      normalizeCodebaseRepository(
        metadata.target_identity.repository,
        `${at}.metadata.target_identity.repository`,
      )
  ) {
    fail(`${at} analyzer repository must match the task target identity`);
  }
  if (
    metadata.base_identity.commit !== null &&
    run.base_ref !== normalizeAnalyzerCommit(metadata.base_identity.commit)
  ) {
    fail(`${at} analyzer base ref must match the task base identity`);
  }
  if (
    metadata.target_identity.commit !== null &&
    run.target_ref !== normalizeAnalyzerCommit(metadata.target_identity.commit)
  ) {
    fail(`${at} analyzer target ref must match the task target identity`);
  }

  const expected = {
    invalid_observation: ["unknown", null, "low"],
    analysis_incomplete: ["unknown", null, "low"],
    evidence_blocked: ["unknown", null, "low"],
    proven_code_caused: ["caused", true, "high"],
    proven_not_code_caused: ["not_caused", false, "high"],
    runtime_unresolved: ["unknown", null, "low"],
  }[run.analysis_state];
  const aggregateExpected =
    run.analysis_state === "proven_code_caused"
      ? ["bug_code", true]
      : run.analysis_state === "proven_not_code_caused"
        ? ["not_code_related", false]
        : ["unknown", null];
  if (
    run.verdict !== expected[0] ||
    run.caused_by_code_change !== expected[1] ||
    run.confidence !== expected[2] ||
    run.aggregate.attribution_type !== aggregateExpected[0] ||
    run.aggregate.caused_by_code_change !== aggregateExpected[1]
  ) {
    fail(`${at} analyzer state projections are inconsistent`);
  }
  if (
    run.analysis_state !== "runtime_unresolved" &&
    (missingEvidence.length || neededEvidence.length)
  ) {
    fail(`${at} non-runtime evidence projections must be empty`);
  }

  const allowedStateFields = new Set();
  const requireNonEmptyObject = (value, field) => {
    if (!isObject(value) || Object.keys(value).length === 0) {
      fail(`${at}.${field} must be a non-empty object`);
    }
  };
  const requireNonEmptyObjectArray = (value, field) => {
    const items = requireArray(value, `${at}.${field}`);
    if (items.length === 0) {
      fail(`${at}.${field} must contain at least one item`);
    }
    items.forEach((item) => requireNonEmptyObject(item, field));
  };
  if (run.analysis_state === "invalid_observation") {
    requireNonEmptyObjectArray(run.invalid_observation_details, "invalid_observation_details");
    allowedStateFields.add("invalid_observation_details");
  } else if (run.analysis_state === "analysis_incomplete") {
    requireNonEmptyObjectArray(run.incomplete_stages, "incomplete_stages");
    allowedStateFields.add("incomplete_stages");
  } else if (run.analysis_state === "evidence_blocked") {
    requireNonEmptyObjectArray(run.evidence_blockers, "evidence_blockers");
    allowedStateFields.add("evidence_blockers");
    if (Object.hasOwn(run, "incomplete_stages")) {
      if (!Array.isArray(run.incomplete_stages) || run.incomplete_stages.length !== 0) {
        fail(`${at}.incomplete_stages must be empty for evidence_blocked`);
      }
      allowedStateFields.add("incomplete_stages");
    }
  } else if (run.analysis_state === "proven_code_caused") {
    requireNonEmptyObject(run.causal_proof, "causal_proof");
    if (!sameObject(run.self_proof, TERMINAL_SELF_PROOF)) {
      fail(`${at}.self_proof must contain the terminal proof checks`);
    }
    allowedStateFields.add("causal_proof");
    allowedStateFields.add("self_proof");
  } else if (run.analysis_state === "proven_not_code_caused") {
    requireNonEmptyObject(run.exclusion_proof, "exclusion_proof");
    if (!sameObject(run.self_proof, TERMINAL_SELF_PROOF)) {
      fail(`${at}.self_proof must contain the terminal proof checks`);
    }
    allowedStateFields.add("exclusion_proof");
    allowedStateFields.add("self_proof");
    if (Object.hasOwn(run, "alternative_runtime_proof")) {
      requireNonEmptyObject(run.alternative_runtime_proof, "alternative_runtime_proof");
      if (
        typeof run.exclusion_proof.proof_id !== "string" ||
        run.alternative_runtime_proof.code_exclusion_ref !== run.exclusion_proof.proof_id
      ) {
        fail(`${at}.alternative_runtime_proof must reference exclusion_proof.proof_id`);
      }
      allowedStateFields.add("alternative_runtime_proof");
    }
  } else {
    requireNonEmptyObjectArray(run.evidence_gaps, "evidence_gaps");
    if (!sameObject(run.self_proof, TERMINAL_SELF_PROOF)) {
      fail(`${at}.self_proof must contain the terminal proof checks`);
    }
    allowedStateFields.add("evidence_gaps");
    allowedStateFields.add("self_proof");
    if (Object.hasOwn(run, "incomplete_stages")) {
      if (!Array.isArray(run.incomplete_stages) || run.incomplete_stages.length !== 0) {
        fail(`${at}.incomplete_stages must be empty for runtime_unresolved`);
      }
      allowedStateFields.add("incomplete_stages");
    }
  }
  for (const field of ANALYZER_STATE_FIELDS) {
    if (!allowedStateFields.has(field) && Object.hasOwn(run, field)) {
      fail(`${at}.${field} is not allowed for ${run.analysis_state}`);
    }
  }
}

function validateCauseSignature(signature, at) {
  requireExactKeys(
    signature,
    ["mechanism", "responsible_psm", "repair_target", "expectedness"],
    at,
  );
  for (const key of ["mechanism", "responsible_psm", "repair_target"]) {
    requireString(signature[key], `${at}.${key}`);
  }
  requireEnum(signature.expectedness, EXPECTEDNESS_VALUES, `${at}.expectedness`);
  const normalizedMechanism = signature.mechanism
    .trim()
    .replace(/[。.!！?？]+$/gu, "")
    .trim();
  if (
    /^(?:unknown|unresolved|other|multiple|未知|暂未定位|其他|多种)$/iu.test(normalizedMechanism)
  ) {
    fail(`${at}.mechanism must identify one homogeneous mechanism or symptom family`);
  }
}

function validateAttributionMembers(finding, at, collection) {
  validateCauseSignature(finding.cause_signature, `${at}.cause_signature`);
  if (finding.cause_signature.expectedness !== finding.expectedness) {
    fail(`${at}.cause_signature.expectedness must equal ${at}.expectedness`);
  }
  if (finding.cause_signature.responsible_psm !== finding.responsible_party) {
    fail(`${at}.cause_signature.responsible_psm must equal ${at}.responsible_party`);
  }
  if (finding.cause_signature.repair_target !== finding.recommendation.target) {
    fail(`${at}.cause_signature.repair_target must equal ${at}.recommendation.target`);
  }

  const members = requireArray(finding.attribution_members, `${at}.attribution_members`);
  if (members.length === 0) {
    fail(`${at}.attribution_members must contain at least one item`);
  }
  const sourceIdentities = new Set();
  const memberFlowIds = new Set();
  const replayFailureFlowOwners = new Map();
  const methods = new Set();
  const diffClusterIds = [];
  for (const [index, member] of members.entries()) {
    const memberAt = `${at}.attribution_members[${index}]`;
    requireExactKeys(
      member,
      [
        "source_type",
        "source_id",
        "flow_ids",
        "method",
        "direction_or_stage",
        "diff_path_or_reason",
        "response_signature",
        "value_shape",
        "candidate_responsible_psm",
        "cause_signature",
      ],
      memberAt,
    );
    requireEnum(member.source_type, ["diff_cluster", "replay_failure"], `${memberAt}.source_type`);
    if (collection === "diff_attributions" && member.source_type !== "diff_cluster") {
      fail(`${memberAt}.source_type must be diff_cluster in DIFF attribution`);
    }
    if (collection === "replay_failures" && member.source_type !== "replay_failure") {
      fail(`${memberAt}.source_type must be replay_failure in replay-failure attribution`);
    }
    for (const key of [
      "source_id",
      "method",
      "direction_or_stage",
      "diff_path_or_reason",
      "response_signature",
      "value_shape",
      "candidate_responsible_psm",
    ]) {
      requireString(member[key], `${memberAt}.${key}`);
    }
    const sourceIdentity = `${member.source_type}\u0000${member.source_id}`;
    if (sourceIdentities.has(sourceIdentity)) {
      fail(
        `${at}.attribution_members contains duplicate source identity ${member.source_type}:${member.source_id}`,
      );
    }
    sourceIdentities.add(sourceIdentity);
    const flowIds = requireUniqueStrings(member.flow_ids, `${memberAt}.flow_ids`);
    if (flowIds.length === 0) {
      fail(`${memberAt}.flow_ids must contain at least one item`);
    }
    for (const [flowIndex, flowId] of flowIds.entries()) {
      requireRealFlowId(flowId, `${memberAt}.flow_ids[${flowIndex}]`);
      if (collection === "replay_failures") {
        const owner = replayFailureFlowOwners.get(flowId);
        if (owner) {
          fail(
            `${at}.attribution_members replay-failure Flow ${flowId} is claimed by both ${owner} and ${member.source_id}`,
          );
        }
        replayFailureFlowOwners.set(flowId, member.source_id);
      }
      memberFlowIds.add(flowId);
    }
    methods.add(member.method);
    validateCauseSignature(member.cause_signature, `${memberAt}.cause_signature`);
    if (!sameObject(member.cause_signature, finding.cause_signature)) {
      fail(`${memberAt}.cause_signature must equal the Finding cause_signature`);
    }
    if (member.candidate_responsible_psm !== finding.cause_signature.responsible_psm) {
      fail(`${memberAt}.candidate_responsible_psm must equal the Finding responsible PSM`);
    }
    if (member.source_type === "diff_cluster") {
      diffClusterIds.push(member.source_id);
    } else if (!flowIds.includes(member.source_id)) {
      fail(`${memberAt}.source_id must identify one of its replay-failure Flow IDs`);
    }
  }

  const expectedClusters = [...diffClusterIds].sort();
  const actualClusters = [...finding.covered_cluster_ids].sort();
  if (!sameObject(expectedClusters, actualClusters)) {
    fail(`${at}.covered_cluster_ids must exactly match diff-cluster attribution members`);
  }
  const expectedFlows = [...memberFlowIds].sort();
  const actualFlows = [...finding.covered_flow_ids].sort();
  if (!sameObject(expectedFlows, actualFlows)) {
    fail(`${at}.covered_flow_ids must exactly match attribution member Flow IDs`);
  }
  if (finding.impact_counts.methods !== methods.size) {
    fail(`${at}.impact_counts.methods must equal distinct attribution member methods`);
  }
  if (finding.impact_counts.flows !== memberFlowIds.size) {
    fail(`${at}.impact_counts.flows must equal distinct attribution member Flow IDs`);
  }

  return members;
}

function validateInvestigation(
  finding,
  at,
  metadata,
  evidenceById,
  codeEvidence,
  runtimeEvidence,
  rootCauseEvidence,
  boundaries,
  collection,
) {
  const investigation = finding.investigation;
  requireExactKeys(
    investigation,
    ["status", "sources", "introduced_by_current_change", "broad_impact"],
    `${at}.investigation`,
  );
  requireEnum(
    investigation.status,
    ["root_cause_proven", "exhausted_unresolved", "evidence_blocked"],
    `${at}.investigation.status`,
  );
  requireBoolean(
    investigation.introduced_by_current_change,
    `${at}.investigation.introduced_by_current_change`,
  );
  requireBoolean(investigation.broad_impact, `${at}.investigation.broad_impact`);
  const sources = requireArray(investigation.sources, `${at}.investigation.sources`);
  if (sources.length !== INVESTIGATION_SOURCES.length) {
    fail(`${at}.investigation.sources must classify every supported evidence source`);
  }
  const seenSources = new Set();
  const attributionMemberByIdentity = new Map();
  for (const member of finding.attribution_members) {
    attributionMemberByIdentity.set(memberIdentity(member.source_type, member.source_id), member);
  }
  const memberIdentities = new Set(attributionMemberByIdentity.keys());
  for (const evidence of evidenceById.values()) {
    if (!["code", "error_catalog", "log", "trace"].includes(evidence.kind)) {
      continue;
    }
    for (const ref of evidence.member_refs) {
      const identity = memberIdentity(ref.source_type, ref.source_id);
      if (!memberIdentities.has(identity)) {
        fail(
          `${at}.evidence ${evidence.id} member_refs must identify attribution members in this Finding`,
        );
      }
      if (["log", "trace"].includes(evidence.kind)) {
        const member = attributionMemberByIdentity.get(identity);
        if (!evidence.flow_ids.some((flowId) => member.flow_ids.includes(flowId))) {
          fail(`${at}.evidence ${evidence.id} must cover a Flow of every declared member`);
        }
      }
    }
  }
  const evidenceSourceKinds = new Map([
    ["code", new Set(["code", "error_catalog"])],
    ["log", new Set(["log"])],
    ["trace", new Set(["trace"])],
    ["response", new Set(["flow"])],
    ["configuration", new Set(["task_config", "config"])],
    ["deployment", new Set(["deployment"])],
  ]);
  for (const [index, source] of sources.entries()) {
    const sourceAt = `${at}.investigation.sources[${index}]`;
    requireExactKeys(source, ["source", "members"], sourceAt);
    requireEnum(source.source, INVESTIGATION_SOURCES, `${sourceAt}.source`);
    if (seenSources.has(source.source)) {
      fail(`${at}.investigation.sources contains duplicate source ${source.source}`);
    }
    seenSources.add(source.source);
    const sourceMembers = requireArray(source.members, `${sourceAt}.members`);
    const seenMemberIds = new Set();
    for (const [memberIndex, result] of sourceMembers.entries()) {
      const resultAt = `${sourceAt}.members[${memberIndex}]`;
      requireExactKeys(
        result,
        [
          "source_type",
          "source_id",
          "available",
          "checked",
          "evidence_ids",
          "acquisition_attempt",
          "blocker",
          "recovery_action",
          "outcome",
        ],
        resultAt,
      );
      requireEnum(
        result.source_type,
        ["diff_cluster", "replay_failure"],
        `${resultAt}.source_type`,
      );
      requireString(result.source_id, `${resultAt}.source_id`);
      requireBoolean(result.available, `${resultAt}.available`);
      requireBoolean(result.checked, `${resultAt}.checked`);
      const evidenceIds = requireUniqueStrings(result.evidence_ids, `${resultAt}.evidence_ids`);
      requireStringWithin(result.outcome, `${resultAt}.outcome`, INVESTIGATION_OUTCOME_MAX_LENGTH);
      const resultIdentity = memberIdentity(result.source_type, result.source_id);
      if (!memberIdentities.has(resultIdentity)) {
        fail(`${resultAt} must identify an attribution member in this Finding`);
      }
      if (seenMemberIds.has(resultIdentity)) {
        fail(
          `${sourceAt}.members contains duplicate source identity ${result.source_type}:${result.source_id}`,
        );
      }
      seenMemberIds.add(resultIdentity);
      const normalizedOutcome = result.outcome.trim().replace(/[\s\p{P}]+$/gu, "");
      if (
        normalizedOutcome.length === 0 ||
        /^(?:暂无|暂未定位|未知|未检查|待检查|无)$/u.test(normalizedOutcome)
      ) {
        fail(`${resultAt}.outcome must state what was checked or why the source is unavailable`);
      }
      if (result.available && !result.checked) {
        fail(`${resultAt} is available and must be checked before attribution completes`);
      }
      if (!result.available && result.checked) {
        fail(`${resultAt} cannot be checked when it is unavailable`);
      }
      if (!result.checked && evidenceIds.length > 0) {
        fail(`${resultAt}.evidence_ids must be empty when the source was not checked`);
      }
      if (result.checked && evidenceIds.length === 0) {
        fail(`${resultAt}.evidence_ids must reference evidence when the source was checked`);
      }
      const member = attributionMemberByIdentity.get(resultIdentity);
      for (const evidenceId of evidenceIds) {
        const evidence = evidenceById.get(evidenceId);
        if (!evidence) {
          fail(`${resultAt}.evidence_ids contains unknown ID ${evidenceId}`);
        }
        if (!evidenceSourceKinds.get(source.source).has(evidence.kind)) {
          fail(
            `${resultAt}.evidence_ids must reference ${source.source} evidence, not ${evidence.kind}`,
          );
        }
        if (source.source === "code") {
          const target = metadata.target_identity;
          if (
            evidence.psm !== target.psm ||
            (target.repository !== null &&
              !matchesCodebaseRepository(
                evidence.repository,
                target.repository,
                `${resultAt}.metadata.target_identity.repository`,
              )) ||
            (target.commit !== null && evidence.ref !== target.commit)
          ) {
            fail(`${resultAt}.evidence_ids must reference code matching the task target identity`);
          }
        }
        if (
          ["code", "log", "trace"].includes(source.source) &&
          !evidence.member_refs.some(
            (ref) => ref.source_type === result.source_type && ref.source_id === result.source_id,
          )
        ) {
          fail(`${resultAt}.evidence_ids must reference evidence covering this attribution member`);
        }
        if (
          ["log", "trace"].includes(source.source) &&
          !evidence.flow_ids.some((flowId) => member.flow_ids.includes(flowId))
        ) {
          fail(`${resultAt}.evidence_ids must reference runtime evidence for this member's Flow`);
        }
        if (
          source.source === "response" &&
          (evidence.source_id !== result.source_id || !member.flow_ids.includes(evidence.flow_id))
        ) {
          fail(`${resultAt}.evidence_ids must reference Flow evidence for this attribution member`);
        }
      }
      if (result.available) {
        for (const key of ["acquisition_attempt", "blocker", "recovery_action"]) {
          if (result[key] !== null) {
            fail(`${resultAt}.${key} must be null when the source is available`);
          }
        }
      } else {
        for (const key of ["acquisition_attempt", "blocker", "recovery_action"]) {
          requireStringWithin(result[key], `${resultAt}.${key}`, INVESTIGATION_OUTCOME_MAX_LENGTH);
        }
      }
    }
    if (!sameObject([...seenMemberIds].sort(), [...memberIdentities].sort())) {
      fail(`${sourceAt}.members must cover every attribution member exactly once`);
    }
  }
  if (INVESTIGATION_SOURCES.some((source) => !seenSources.has(source))) {
    fail(`${at}.investigation.sources must classify every supported evidence source`);
  }
  const sourceByName = new Map(sources.map((source) => [source.source, source]));
  for (const evidence of evidenceById.values()) {
    if (!["code", "error_catalog", "log", "trace"].includes(evidence.kind)) {
      continue;
    }
    const source = sourceByName.get(evidence.kind === "error_catalog" ? "code" : evidence.kind);
    const declaredFlowIds = new Set();
    for (const ref of evidence.member_refs) {
      const identity = memberIdentity(ref.source_type, ref.source_id);
      const result = source.members.find(
        (candidate) => memberIdentity(candidate.source_type, candidate.source_id) === identity,
      );
      if (!result?.available || !result.checked || !result.evidence_ids.includes(evidence.id)) {
        fail(
          `${at}.evidence ${evidence.id} member_refs must be cited by the matching checked investigation member`,
        );
      }
      if (["log", "trace"].includes(evidence.kind)) {
        for (const flowId of attributionMemberByIdentity.get(identity).flow_ids) {
          declaredFlowIds.add(flowId);
        }
      }
    }
    if (
      ["log", "trace"].includes(evidence.kind) &&
      evidence.flow_ids.some((flowId) => !declaredFlowIds.has(flowId))
    ) {
      fail(
        `${at}.evidence ${evidence.id} flow_ids must belong to its declared attribution members`,
      );
    }
  }
  for (const [sourceName, evidenceKinds] of evidenceSourceKinds) {
    if (finding.evidence.some((evidence) => evidenceKinds.has(evidence.kind))) {
      const source = sourceByName.get(sourceName);
      if (!source.members.some((result) => result.available && result.checked)) {
        fail(`${at}.investigation source ${sourceName} must reflect the supplied evidence`);
      }
    }
  }

  const broadImpact =
    finding.impact_counts.methods >= 2 ||
    finding.impact_counts.flows >= 10 ||
    finding.impact_counts.field_clusters >= 10;
  if (investigation.broad_impact !== broadImpact) {
    fail(`${at}.investigation.broad_impact must match the report-wide impact threshold`);
  }
  if (collection !== "defects" && investigation.introduced_by_current_change) {
    fail(`${at}.investigation.introduced_by_current_change is only valid for confirmed defects`);
  }
  const expectedSeverity = classifyFindingSeverity(finding.finding_reason, finding.confidence);
  if (finding.severity !== expectedSeverity) {
    fail(`${at}.severity must be ${expectedSeverity} for its finding reason and confidence`);
  }

  if (investigation.status === "root_cause_proven" && rootCauseEvidence.length === 0) {
    fail(`${at}.investigation cannot prove a root cause without mechanism evidence`);
  }
  if (investigation.status === "evidence_blocked") {
    if (finding.root_cause !== "现有证据不足，尚不能确认根因。" || finding.confidence !== "低") {
      fail(
        `${at} evidence-blocked attribution requires a clear evidence-limited root cause and low confidence`,
      );
    }
    if (!boundaries.some((boundary) => boundary.material)) {
      fail(`${at} evidence-blocked attribution requires a material evidence boundary`);
    }
    fail(`${at} evidence-blocked attribution is private and cannot be rendered as a final report`);
  }
  const checkedMemberIdentities = (sourceName) =>
    new Set(
      sourceByName
        .get(sourceName)
        .members.filter((result) => result.available && result.checked)
        .map((result) => memberIdentity(result.source_type, result.source_id)),
    );
  const checkedCodeMemberIdentities = checkedMemberIdentities("code");
  const checkedLogMemberIdentities = checkedMemberIdentities("log");
  const checkedTraceMemberIdentities = checkedMemberIdentities("trace");
  const criticalEvidenceComplete = [...memberIdentities].every(
    (identity) =>
      checkedCodeMemberIdentities.has(identity) &&
      (checkedLogMemberIdentities.has(identity) || checkedTraceMemberIdentities.has(identity)),
  );
  if (!criticalEvidenceComplete || codeEvidence.length === 0 || runtimeEvidence.length === 0) {
    fail(
      `${at} critical code and runtime evidence is blocked; final attribution report cannot be rendered`,
    );
  }
  if (investigation.status === "exhausted_unresolved") {
    const fingerprintKeys = [
      "direction_or_stage",
      "response_signature",
      "value_shape",
      "candidate_responsible_psm",
    ];
    const [firstMember, ...remainingMembers] = finding.attribution_members;
    if (
      remainingMembers.some((member) =>
        fingerprintKeys.some((key) => member[key] !== firstMember[key]),
      )
    ) {
      fail(`${at} unresolved attribution members must share one homogeneous symptom fingerprint`);
    }
    if (finding.root_cause !== "现有证据不足，尚不能确认根因。" || finding.confidence !== "低") {
      fail(
        `${at} exhausted unresolved attribution requires a clear evidence-limited root cause and low confidence`,
      );
    }
    if (!boundaries.some((boundary) => boundary.material)) {
      fail(`${at} exhausted unresolved attribution requires a material evidence boundary`);
    }
  }
}

function validateFinding(finding, at, metadata, collection) {
  requireExactKeys(finding, FINDING_KEYS, at, FINDING_ALLOWED_KEYS);
  for (const key of ["id", "title", "subtype", "responsible_party", "phenomenon", "root_cause"]) {
    requireString(finding[key], `${at}.${key}`);
  }
  requireStringWithin(finding.phenomenon, `${at}.phenomenon`, FINDING_SUMMARY_MAX_LENGTH);
  requireStringWithin(finding.root_cause, `${at}.root_cause`, FINDING_SUMMARY_MAX_LENGTH);
  requireEnum(finding.root_cause_type, ROOT_CAUSE_TYPES, `${at}.root_cause_type`);
  requireEnum(finding.confidence, CONFIDENCE_LEVELS, `${at}.confidence`);
  requireEnum(finding.finding_reason, FINDING_REASON_VALUES, `${at}.finding_reason`);
  requireEnum(finding.expectedness, EXPECTEDNESS_VALUES, `${at}.expectedness`);
  requireEnum(finding.code_correlation, CODE_CORRELATIONS, `${at}.code_correlation`);
  requireEnum(finding.severity, SEVERITY_LEVELS, `${at}.severity`);
  requireUniqueStrings(finding.covered_cluster_ids, `${at}.covered_cluster_ids`);
  requireUniqueStrings(finding.covered_flow_ids, `${at}.covered_flow_ids`);
  requireExactKeys(
    finding.impact_counts,
    ["methods", "flows", "field_clusters"],
    `${at}.impact_counts`,
  );
  for (const key of ["methods", "flows", "field_clusters"]) {
    requireInteger(finding.impact_counts[key], `${at}.impact_counts.${key}`);
  }
  if (finding.impact_counts.field_clusters !== finding.covered_cluster_ids.length) {
    fail(`${at}.impact_counts.field_clusters must equal covered_cluster_ids.length`);
  }
  const attributionMembers = validateAttributionMembers(finding, at, collection);
  validateRecommendation(finding.recommendation, `${at}.recommendation`);

  const evidenceItems = requireArray(finding.evidence, `${at}.evidence`);
  if (evidenceItems.length === 0) {
    fail(`${at}.evidence must contain at least one item`);
  }
  const evidenceById = new Map();
  for (const [index, evidence] of evidenceItems.entries()) {
    validateEvidence(evidence, `${at}.evidence[${index}]`);
    if (evidenceById.has(evidence.id)) {
      fail(`${at}.evidence contains duplicate ID ${evidence.id}`);
    }
    evidenceById.set(evidence.id, evidence);
  }

  const samples = requireArray(finding.samples, `${at}.samples`);
  if (samples.length > MAX_RENDERED_SAMPLES) {
    fail(`${at}.samples must contain at most ${MAX_RENDERED_SAMPLES} items`);
  }
  for (const [index, sample] of samples.entries()) {
    const sampleAt = `${at}.samples[${index}]`;
    requireExactKeys(
      sample,
      ["display_name", "difference", "subject", "evidence_id", "source_id", "flow_id"],
      sampleAt,
    );
    requireStringWithin(
      sample.display_name,
      `${sampleAt}.display_name`,
      SAMPLE_DISPLAY_NAME_MAX_LENGTH,
    );
    for (const key of ["difference", "subject", "evidence_id", "source_id", "flow_id"]) {
      requireString(sample[key], `${sampleAt}.${key}`);
    }
    const normalizedDisplayName = sample.display_name.trim().toLowerCase();
    if (
      normalizedDisplayName.length === 0 ||
      /^(?:代表流量|流量样本|样本\s*\d*|sample\s*\d*)$/iu.test(normalizedDisplayName) ||
      normalizedDisplayName.startsWith("/")
    ) {
      fail(`${sampleAt}.display_name must be a semantic name instead of an ID or placeholder`);
    }
    const normalizedDifference = sample.difference.trim().toLowerCase();
    const normalizedSubject = sample.subject.trim().toLowerCase();
    if (
      normalizedDifference.length === 0 ||
      /^(?:代表流量|流量样本|样本\s*\d*|sample\s*\d*)$/iu.test(normalizedDifference) ||
      normalizedDifference.startsWith("/") ||
      normalizedDifference === normalizedSubject
    ) {
      fail(`${sampleAt}.difference must describe the observable difference`);
    }
    if (
      normalizedSubject.length === 0 ||
      normalizedSubject.startsWith("/") ||
      /^(?:接口|方法|代表流量|流量样本|样本\s*\d*|sample\s*\d*|flow[-_:]?\w+|log[-_:]?\w+)$/iu.test(
        normalizedSubject,
      )
    ) {
      fail(`${sampleAt}.subject must identify the affected interface or method semantically`);
    }
    const sampleEvidence = evidenceById.get(sample.evidence_id);
    if (!sampleEvidence || sampleEvidence.kind !== "flow") {
      fail(`${sampleAt}.evidence_id must resolve to Flow evidence`);
    }
    const matchingMembers = attributionMembers.filter(
      (member) => member.source_id === sample.source_id && member.flow_ids.includes(sample.flow_id),
    );
    if (matchingMembers.length !== 1) {
      fail(`${sampleAt} must belong to an attribution member in this Finding`);
    }
    const [member] = matchingMembers;
    if (
      sampleEvidence.source_id !== sample.source_id ||
      sampleEvidence.flow_id !== sample.flow_id ||
      sampleEvidence.method !== member.method
    ) {
      fail(`${sampleAt} must match its Flow evidence and attribution member identity`);
    }
  }

  const boundaries = evidenceItems.filter((item) => item.kind === "evidence_boundary");
  if (samples.length === 0 && boundaries.length === 0) {
    fail(`${at} must contain at least one sample or evidence boundary`);
  }
  if (boundaries.some((item) => item.material) && finding.confidence === "高") {
    fail(`${at} has a material evidence boundary and confidence cannot remain high`);
  }

  for (const evidenceId of finding.recommendation.evidence_ids) {
    if (!evidenceById.has(evidenceId)) {
      fail(`${at}.recommendation.evidence_ids contains unknown ID ${evidenceId}`);
    }
  }
  const codeEvidence = evidenceItems.filter(
    (item) => item.kind === "code" || item.kind === "error_catalog",
  );
  const runtimeEvidence = evidenceItems.filter(
    (item) => item.kind === "log" || item.kind === "trace",
  );
  const flowEvidence = evidenceItems.filter((item) => item.kind === "flow");
  const rootCauseEvidence = evidenceItems.filter((item) =>
    ROOT_CAUSE_EVIDENCE_KINDS.has(item.kind),
  );
  validateInvestigation(
    finding,
    at,
    metadata,
    evidenceById,
    codeEvidence,
    runtimeEvidence,
    rootCauseEvidence,
    boundaries,
    collection,
  );
  if (rootCauseEvidence.length === 0) {
    if (!boundaries.some((item) => item.material)) {
      fail(`${at} Flow-only evidence requires a material evidence boundary`);
    }
    if (finding.confidence !== "低") {
      fail(`${at} Flow-only evidence requires low confidence`);
    }
    if (finding.root_cause !== "现有证据不足，尚不能确认根因。") {
      fail(`${at}.root_cause must state that current evidence cannot confirm the cause`);
    }
  }
  if (finding.code_correlation !== "not_applicable" && codeEvidence.length === 0) {
    fail(`${at}.code_correlation requires code evidence`);
  }
  if (
    codeEvidence.length > 0 &&
    !codeEvidence.some((item) => finding.recommendation.evidence_ids.includes(item.id))
  ) {
    fail(`${at}.recommendation.evidence_ids must reference applicable code evidence`);
  }
  if (
    runtimeEvidence.length > 0 &&
    !runtimeEvidence.some((item) => finding.recommendation.evidence_ids.includes(item.id))
  ) {
    fail(`${at}.recommendation.evidence_ids must reference applicable runtime evidence`);
  }
  if (finding.root_cause_type === "稳定性问题" && runtimeEvidence.length === 0) {
    if (!boundaries.some((item) => item.material)) {
      fail(`${at} runtime cause requires log or trace evidence`);
    }
  }

  validateAdmission(finding.admission, evidenceById, `${at}.admission`);
  const analyzerRuns = requireArray(finding.analyzer_runs, `${at}.analyzer_runs`);
  const analyzerDiffIds = new Set();
  for (const [index, run] of analyzerRuns.entries()) {
    validateAnalyzerRun(
      run,
      `${at}.analyzer_runs[${index}]`,
      metadata,
      finding.covered_cluster_ids,
    );
    if (analyzerDiffIds.has(run.similar_diff_id)) {
      fail(`${at}.analyzer_runs contains duplicate analyzer proof for ${run.similar_diff_id}`);
    }
    analyzerDiffIds.add(run.similar_diff_id);
  }
  const sameCommit =
    metadata.base_identity.commit !== null &&
    metadata.base_identity.commit === metadata.target_identity.commit;
  const hasIndependentIdentity =
    metadata.target_identity.repository !== null &&
    metadata.base_identity.commit !== null &&
    metadata.target_identity.commit !== null;
  if (sameCommit && analyzerRuns.length > 0) {
    fail(`${at}.analyzer_runs must be empty for same-commit runtime causality`);
  }
  if (finding.code_correlation === "strong") {
    if (!hasIndependentIdentity) {
      fail(`${at} strong code correlation requires independent repository and revision identity`);
    }
    const target = metadata.target_identity;
    if (
      !codeEvidence.some(
        (evidence) =>
          evidence.kind === "code" &&
          evidence.psm === target.psm &&
          matchesCodebaseRepository(
            evidence.repository,
            target.repository,
            `${at}.metadata.target_identity.repository`,
          ) &&
          evidence.ref === target.commit,
      )
    ) {
      fail(`${at} strong code evidence must match the task target identity`);
    }
    if (sameCommit) {
      if (runtimeEvidence.length === 0) {
        fail(`${at} same-commit strong correlation requires task-window log or trace evidence`);
      }
    } else {
      for (const clusterId of finding.covered_cluster_ids) {
        if (
          !analyzerRuns.some(
            (run) =>
              run.similar_diff_id === clusterId && run.analysis_state === "proven_code_caused",
          )
        ) {
          fail(`${at}.analyzer_runs requires proven_code_caused analyzer proof for ${clusterId}`);
        }
      }
    }
  }

  return {
    evidenceById,
    codeEvidence,
    runtimeEvidence,
    flowEvidence,
    rootCauseEvidence,
    boundaries,
    analyzerRuns,
  };
}

function requireUniqueFindingIds(report) {
  const seen = new Set();
  for (const collection of ["defects", "diff_attributions", "replay_failures"]) {
    for (const finding of report[collection]) {
      if (seen.has(finding.id)) {
        fail(`finding ID ${finding.id} must be globally unique`);
      }
      seen.add(finding.id);
    }
  }
}

function validateDefect(defect, detail, metadata, at) {
  if (defect.admission === null) {
    fail(`${at}.admission is required for a confirmed defect`);
  }
  if (!["业务变更", "稳定性问题"].includes(defect.root_cause_type)) {
    fail(`${at}.root_cause_type must be 业务变更 or a proven business-code 稳定性问题`);
  }
  if (defect.code_correlation !== "strong") {
    fail(`${at}.code_correlation must be strong`);
  }
  if (defect.expectedness !== "非预期") {
    fail(`${at}.expectedness must be 非预期`);
  }
  if (defect.finding_reason !== "业务缺陷") {
    fail(`${at}.finding_reason must be 业务缺陷`);
  }
  if (detail.codeEvidence.length === 0) {
    fail(`${at} requires code evidence`);
  }
  if (detail.flowEvidence.length === 0) {
    fail(`${at} requires Flow evidence`);
  }
  if (detail.boundaries.some((item) => item.material)) {
    fail(`${at} cannot contain a material evidence boundary`);
  }
  if (defect.covered_cluster_ids.length + defect.covered_flow_ids.length === 0) {
    fail(`${at} must cover at least one attribution ID`);
  }
  const target = metadata.target_identity;
  if (
    !detail.codeEvidence.some(
      (evidence) =>
        evidence.kind === "code" &&
        evidence.psm === target.psm &&
        matchesCodebaseRepository(
          evidence.repository,
          target.repository,
          `${at}.metadata.target_identity.repository`,
        ) &&
        evidence.ref === target.commit,
    )
  ) {
    fail(`${at} requires code evidence matching the task target identity`);
  }
  const sameCommit =
    metadata.base_identity.commit !== null &&
    metadata.base_identity.commit === metadata.target_identity.commit;
  if (sameCommit) {
    const evidenceById = detail.evidenceById;
    const containsKind = (ids, kinds) => ids.some((id) => kinds.has(evidenceById.get(id)?.kind));
    if (!containsKind(defect.admission.real_trigger_evidence_ids, new Set(["log", "trace"]))) {
      fail(`${at} same-commit defect requires task-window runtime trigger evidence`);
    }
    if (
      !containsKind(defect.admission.producer_transport_evidence_ids, new Set(["code"])) ||
      !containsKind(defect.admission.producer_transport_evidence_ids, new Set(["log", "trace"]))
    ) {
      fail(`${at} same-commit defect requires code and runtime producer/transport evidence`);
    }
    if (
      !containsKind(defect.admission.consumer_impact_evidence_ids, new Set(["code"])) ||
      !containsKind(
        defect.admission.consumer_impact_evidence_ids,
        new Set(["flow", "log", "trace"]),
      )
    ) {
      fail(`${at} same-commit defect requires code and observable consumer/impact evidence`);
    }
  }
}

function assertExactReconciliation(label, inventoryIds, classifiedIds, unresolvedIds) {
  const duplicate = classifiedIds.find((id, index) => classifiedIds.indexOf(id) !== index);
  if (duplicate) {
    fail(`${label} reconciliation classifies ${duplicate} more than once`);
  }
  const classified = new Set(classifiedIds);
  const unresolved = new Set(unresolvedIds);
  for (const id of classified) {
    if (unresolved.has(id)) {
      fail(`${label} reconciliation classifies and leaves ${id} unresolved`);
    }
  }
  const actual = [...classified, ...unresolved].sort();
  const expected = [...inventoryIds].sort();
  if (actual.length !== expected.length || actual.some((id, index) => id !== expected[index])) {
    fail(`${label} reconciliation does not match the frozen inventory`);
  }
}

export function validateReport(report) {
  requireExactKeys(report, ROOT_KEYS, "$");
  if (report.schema_version !== 12) {
    fail("schema_version must be 12");
  }
  validateMetadata(report.metadata);
  validateVerdict(report.verdict);
  validateScope(report.scope);
  validateFunnel(report.funnel);
  validateTestSufficiency(report.test_sufficiency);
  for (const collection of ["defects", "diff_attributions", "replay_failures"]) {
    requireArray(report[collection], collection);
  }
  requireArray(report.actions, "actions");
  requireArray(report.evidence_boundaries, "evidence_boundaries");
  if (report.actions.length > 3) {
    fail("actions must contain at most 3 items");
  }

  requireUniqueFindingIds(report);
  const allEvidence = new Map();
  let hasMaterialFindingBoundary = false;
  for (const collection of ["defects", "diff_attributions", "replay_failures"]) {
    for (const [index, finding] of report[collection].entries()) {
      const at = `${collection}[${index}]`;
      const detail = validateFinding(finding, at, report.metadata, collection);
      if (collection === "defects") {
        validateDefect(finding, detail, report.metadata, at);
      } else {
        if (finding.admission !== null) {
          fail(`${at}.admission must be null outside the defect list`);
        }
      }
      hasMaterialFindingBoundary ||= detail.boundaries.some((boundary) => boundary.material);
      for (const [id, evidence] of detail.evidenceById) {
        if (allEvidence.has(id)) {
          fail(`evidence ID ${id} must be globally unique`);
        }
        allEvidence.set(id, evidence);
      }
    }
  }
  for (const [index, boundary] of report.evidence_boundaries.entries()) {
    validateEvidenceBoundary(boundary, `evidence_boundaries[${index}]`);
    if (allEvidence.has(boundary.id)) {
      fail(`evidence ID ${boundary.id} must be globally unique`);
    }
    allEvidence.set(boundary.id, boundary);
  }
  for (const [index, action] of report.actions.entries()) {
    validateRecommendation(action, `actions[${index}]`);
    for (const id of action.evidence_ids) {
      if (!allEvidence.has(id)) {
        fail(`actions[${index}].evidence_ids contains unknown ID ${id}`);
      }
    }
  }

  if (report.verdict.confirmed_defect_count !== report.defects.length) {
    fail("verdict.confirmed_defect_count must equal defects.length");
  }
  const expectedSummary =
    report.defects.length === 0 ? "未发现缺陷。" : `发现 ${report.defects.length} 个缺陷。`;
  if (report.verdict.summary !== expectedSummary) {
    fail(`verdict.summary must be ${JSON.stringify(expectedSummary)}`);
  }
  if (report.defects.length > 0 && report.verdict.release_advice !== "不通过") {
    fail("verdict.release_advice must be 不通过 when confirmed defects exist");
  }
  if (
    report.verdict.release_advice === "通过" &&
    (report.defects.length > 0 ||
      report.verdict.task_validity !== "有效" ||
      report.verdict.attribution_completeness !== "完整")
  ) {
    fail("verdict.release_advice 通过 requires a valid, complete, no-defect report");
  }
  if (report.verdict.release_advice === "有条件通过" && report.defects.length > 0) {
    fail("verdict.release_advice 有条件通过 requires no confirmed defects");
  }
  if (
    (["无效", "无法确认"].includes(report.verdict.task_validity) ||
      report.verdict.attribution_completeness === "失败") &&
    report.verdict.release_advice !== "不可据此判断"
  ) {
    fail("invalid, unconfirmed, or failed attribution requires 不可据此判断");
  }

  const diffIds = report.scope.diff_inventory.cluster_ids;
  const failureIds = report.scope.replay_failure_inventory.flow_ids;
  const classifiedDiffIds = report.diff_attributions.flatMap(
    (finding) => finding.covered_cluster_ids,
  );
  const classifiedFailureIds = report.replay_failures.flatMap(
    (finding) => finding.covered_flow_ids,
  );
  assertExactReconciliation(
    "DIFF",
    diffIds,
    classifiedDiffIds,
    report.scope.diff_inventory.unresolved_cluster_ids,
  );
  const sampleOwners = new Map();
  for (const collection of ["diff_attributions", "replay_failures"]) {
    for (const finding of report[collection]) {
      for (const sample of finding.samples) {
        const member = finding.attribution_members.find(
          (candidate) =>
            candidate.source_id === sample.source_id && candidate.flow_ids.includes(sample.flow_id),
        );
        const sourceType = member?.source_type ?? "unknown";
        const sampleIdentity = `${sourceType}\u0000${sample.source_id}\u0000${sample.flow_id}`;
        const owner = sampleOwners.get(sampleIdentity);
        if (owner && owner !== finding.id) {
          fail(
            `sample identity ${sourceType}:${sample.source_id}:${sample.flow_id} must not appear in multiple attribution Findings`,
          );
        }
        sampleOwners.set(sampleIdentity, finding.id);
      }
    }
  }
  assertExactReconciliation(
    "replay failure",
    failureIds,
    classifiedFailureIds,
    report.scope.replay_failure_inventory.unresolved_flow_ids,
  );
  if (report.funnel.sent_failure !== report.scope.replay_failure_inventory.total) {
    fail("funnel.sent_failure must equal replay failure inventory total");
  }
  if (
    report.verdict.attribution_completeness === "完整" &&
    (report.scope.diff_inventory.unresolved_cluster_ids.length > 0 ||
      report.scope.replay_failure_inventory.unresolved_flow_ids.length > 0)
  ) {
    fail("complete attribution cannot contain unresolved inventory IDs");
  }
  if (
    (report.evidence_boundaries.some((boundary) => boundary.material) ||
      hasMaterialFindingBoundary) &&
    (report.verdict.attribution_completeness === "完整" ||
      ["通过", "有条件通过"].includes(report.verdict.release_advice))
  ) {
    fail(
      "material task evidence boundaries or material finding boundary require partial attribution and non-passing advice",
    );
  }
  const defectMemberOwners = new Map();
  for (const [index, defect] of report.defects.entries()) {
    const diffMemberIds = defect.attribution_members
      .filter((member) => member.source_type === "diff_cluster")
      .map((member) => member.source_id);
    const failureMemberIds = defect.attribution_members
      .filter((member) => member.source_type === "replay_failure")
      .flatMap((member) => member.flow_ids);
    for (const id of diffMemberIds) {
      if (!classifiedDiffIds.includes(id)) {
        fail(`defects[${index}].attribution_members contains unclassified DIFF ID ${id}`);
      }
    }
    for (const id of failureMemberIds) {
      if (!classifiedFailureIds.includes(id)) {
        fail(`defects[${index}].attribution_members contains unclassified failure ID ${id}`);
      }
    }

    const canonicalMembers = new Map();
    for (const finding of [...report.diff_attributions, ...report.replay_failures]) {
      for (const member of finding.attribution_members) {
        const identity = `${member.source_type}\u0000${member.source_id}`;
        if (canonicalMembers.has(identity)) {
          fail(
            `base attribution member identity ${member.source_type}:${member.source_id} must be unique`,
          );
        }
        canonicalMembers.set(identity, member);
      }
    }
    for (const [memberIndex, member] of defect.attribution_members.entries()) {
      const identity = `${member.source_type}\u0000${member.source_id}`;
      const canonicalMember = canonicalMembers.get(identity);
      if (!canonicalMember || !sameObject(member, canonicalMember)) {
        fail(
          `defects[${index}].attribution_members[${memberIndex}] must exactly match its classified base attribution member`,
        );
      }
      const owner = defectMemberOwners.get(identity);
      if (owner) {
        fail(
          `base attribution member ${member.source_type}:${member.source_id} must not belong to multiple defects (${owner} and ${defect.id})`,
        );
      }
      defectMemberOwners.set(identity, defect.id);
    }
  }
  if (
    report.metadata.task_update_time !== report.scope.final_task_update_time &&
    report.verdict.attribution_completeness === "完整"
  ) {
    fail("changed task update_time requires partial or failed attribution");
  }

  scanSensitive(report);
  return report;
}

function escapeMarkdownText(value) {
  return String(value)
    .replace(/\s+/gu, " ")
    .trim()
    .replaceAll("\\", "\\\\")
    .replaceAll("`", "\\`")
    .replaceAll("*", "\\*")
    .replaceAll("_", "\\_")
    .replaceAll("~", "\\~")
    .replaceAll("#", "\\#")
    .replaceAll("!", "\\!")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("[", "\\[")
    .replaceAll("]", "\\]")
    .replaceAll("(", "\\(")
    .replaceAll(")", "\\)")
    .replaceAll("|", "\\|");
}

function inlineCode(value) {
  return `\`${String(value).replace(/\s+/gu, " ").trim().replaceAll("`", "&#96;")}\``;
}

function trimTerminalPunctuation(value) {
  return String(value)
    .replace(/\s+/gu, " ")
    .trim()
    .replace(/[。.!！？?；;]+$/gu, "");
}

function markdownLink(label, url) {
  return `[${escapeMarkdownText(label)}](${String(url).replaceAll("(", "%28").replaceAll(")", "%29")})`;
}

function evidenceLabel(evidence) {
  if (evidence.kind === "code" || evidence.kind === "error_catalog") {
    return `${evidence.repository}@${evidence.ref.slice(0, 12)}/${evidence.file}:L${evidence.line_start}-L${evidence.line_end}`;
  }
  if (evidence.kind === "log" || evidence.kind === "trace") {
    return `${evidence.kind === "log" ? "LogID" : "Trace"} ${evidence.log_id_or_trace_id}`;
  }
  if (evidence.kind === "flow") {
    return `${evidence.method} Flow`;
  }
  if (evidence.kind === "task_config") {
    return `${evidence.psm} 任务执行配置 ${evidence.subject}`;
  }
  if (evidence.kind === "config") {
    return `${evidence.psm} 配置 ${evidence.subject}`;
  }
  if (evidence.kind === "deployment") {
    return `${evidence.psm} 部署 ${evidence.subject}`;
  }
  if (evidence.kind === "requirement") {
    return "任务范围";
  }
  if (evidence.kind === "merge_request") {
    return "合并请求";
  }
  return evidence.kind;
}

function renderMarkdownEvidence(evidence) {
  const link = evidence.url
    ? markdownLink(evidenceLabel(evidence), evidence.url)
    : inlineCode(evidenceLabel(evidence));
  if (evidence.kind === "code" || evidence.kind === "error_catalog") {
    return `服务 ${inlineCode(evidence.psm)} 的 ${link} 在 ${inlineCode(evidence.symbol)} 中${escapeMarkdownText(trimTerminalPunctuation(evidence.logic))}；${escapeMarkdownText(trimTerminalPunctuation(evidence.summary))}。`;
  }
  if (evidence.kind === "log" || evidence.kind === "trace") {
    return `任务时间窗 ${inlineCode(evidence.time_window)} 内，服务 ${inlineCode(evidence.psm)} 的 ${link} 命中“${escapeMarkdownText(trimTerminalPunctuation(evidence.observation))}”，印证该执行路径；${escapeMarkdownText(trimTerminalPunctuation(evidence.summary))}。`;
  }
  if (evidence.kind === "flow") {
    return `结果印证：${link} 中服务 ${inlineCode(evidence.psm)} 的回放响应 / DIFF 显示${escapeMarkdownText(trimTerminalPunctuation(evidence.observable_result))}。`;
  }
  if (
    evidence.kind === "task_config" ||
    evidence.kind === "config" ||
    evidence.kind === "deployment"
  ) {
    return `${markdownLink(evidenceLabel(evidence), evidence.url)} 证明 ${inlineCode(evidence.effective_time_window)} 内实际值为“${escapeMarkdownText(trimTerminalPunctuation(evidence.observed_value))}”，${escapeMarkdownText(trimTerminalPunctuation(evidence.logic))}；${escapeMarkdownText(trimTerminalPunctuation(evidence.summary))}。`;
  }
  return `上下文：${markdownLink(evidenceLabel(evidence), evidence.url)}：${escapeMarkdownText(trimTerminalPunctuation(evidence.summary))}。`;
}

function evidencePriority(evidence) {
  return EVIDENCE_PRIORITY.get(evidence.kind) ?? Number.MAX_SAFE_INTEGER;
}

function orderedEvidence(finding) {
  return [...finding.evidence].sort(
    (left, right) => evidencePriority(left) - evidencePriority(right),
  );
}

function narrativeEvidence(finding) {
  if (finding.investigation.status !== "root_cause_proven") {
    return [];
  }
  const ordered = orderedEvidence(finding);
  const mechanismEvidence = ordered.filter((item) => ROOT_CAUSE_EVIDENCE_KINDS.has(item.kind));
  if (mechanismEvidence.length === 0) {
    return [];
  }
  const representativeFlowId = finding.samples[0]?.evidence_id;
  const representativeFlow =
    ordered.find((item) => item.kind === "flow" && item.id === representativeFlowId) ??
    ordered.find((item) => item.kind === "flow");
  return ordered.filter(
    (item) =>
      ROOT_CAUSE_EVIDENCE_KINDS.has(item.kind) ||
      (item.kind === "flow" && item === representativeFlow),
  );
}

function groupEvidenceNarratives(items, renderItem) {
  const groups = [];
  for (const item of items) {
    const priority = evidencePriority(item);
    const current = groups.at(-1);
    if (!current || current.priority !== priority) {
      groups.push({ priority, narratives: [renderItem(item)] });
    } else {
      current.narratives.push(renderItem(item));
    }
  }
  return groups.map((group) => group.narratives.join(" "));
}

function analyzerNarrative(run) {
  const details = [
    `canonical Analyzer 状态 ${run.analysis_state}（${ANALYZER_STATE_LABELS[run.analysis_state]}）`,
    `版本 ${run.repository}@${run.base_ref}..${run.target_ref}`,
    `字段 ${run.path} / 操作 ${run.op} / 判定 ${run.verdict} / 置信度 ${run.confidence}`,
  ];
  details.push(
    `artifact ${run.result_artifact.bytes} bytes / SHA-256 ${run.result_artifact.sha256}`,
  );
  const stateDisplay = {
    invalid_observation: [run.invalid_observation_details, ["invalid_kind"]],
    analysis_incomplete: [run.incomplete_stages, ["stage", "error_type"]],
    evidence_blocked: [
      run.evidence_blockers,
      ["blocker_type", "requested_action", "requested_resource", "error_code"],
    ],
    proven_code_caused: [
      run.causal_proof,
      ["change_origin", "effect_stage", "writer", "serialization_field", "proof_evidence_refs"],
    ],
    proven_not_code_caused: [
      run.exclusion_proof,
      ["proof_type", "code_exclusion_basis", "proof_evidence_refs"],
    ],
    runtime_unresolved: [
      run.evidence_gaps,
      ["category", "subject", "last_proven_node", "runtime_value_or_artifact_needed"],
    ],
  }[run.analysis_state];
  if (stateDisplay) {
    const [value, fields] = stateDisplay;
    const pickFields = (item) =>
      Object.fromEntries(
        fields.filter((field) => Object.hasOwn(item, field)).map((field) => [field, item[field]]),
      );
    const summary = Array.isArray(value) ? value.map(pickFields) : pickFields(value);
    details.push(`关键事实 ${JSON.stringify(summary)}`);
  }
  if (run.warnings.length > 0) {
    details.push(`警告：${run.warnings.join("；")}`);
  }
  return details.join("；");
}

function renderMarkdownAnalyzer(run) {
  return `canonical Analyzer：${escapeMarkdownText(analyzerNarrative(run))}。`;
}

function renderMarkdownRecommendation(finding) {
  const recommendation = finding.recommendation;
  const evidenceById = new Map(finding.evidence.map((evidence) => [evidence.id, evidence]));
  const links = recommendation.evidence_ids
    .map((id) => evidenceById.get(id))
    .filter((evidence) => evidence && evidence.url)
    .map((evidence) => markdownLink(evidenceLabel(evidence), evidence.url));
  const suffix = links.length > 0 ? ` 复验证据：${links.join("、")}。` : "";
  const boundaryAdvice = materialBoundaries(finding)
    .map(
      (boundary) =>
        `当前受阻：${escapeMarkdownText(trimTerminalPunctuation(boundary.reason))}；补齐方式：${escapeMarkdownText(trimTerminalPunctuation(boundary.recovery_action))}。`,
    )
    .join(" ");
  return `${escapeMarkdownText(recommendation.owner)} 负责 ${escapeMarkdownText(recommendation.target)}：${escapeMarkdownText(trimTerminalPunctuation(recommendation.change))}；验收标准：${escapeMarkdownText(trimTerminalPunctuation(recommendation.verification))}。${boundaryAdvice ? ` ${boundaryAdvice}` : ""}${suffix}`;
}

function materialBoundaries(finding) {
  return finding.evidence.filter(
    (evidence) => evidence.kind === "evidence_boundary" && evidence.material,
  );
}

function renderMarkdownActionEvidence(action, allEvidence) {
  return action.evidence_ids
    .map((id) => allEvidence.get(id))
    .filter(Boolean)
    .map((evidence) => {
      if (evidence.url) {
        return markdownLink(evidenceLabel(evidence), evidence.url);
      }
      if (evidence.kind === "evidence_boundary") {
        return `证据边界：${escapeMarkdownText(trimTerminalPunctuation(evidence.reason))}；补证动作：${escapeMarkdownText(trimTerminalPunctuation(evidence.recovery_action))}`;
      }
      return inlineCode(evidenceLabel(evidence));
    });
}

function renderMarkdownFinding(finding) {
  const samples = finding.samples.slice(0, MAX_RENDERED_SAMPLES).map((sample) => {
    const evidence = finding.evidence.find((item) => item.id === sample.evidence_id);
    return markdownLink(sample.display_name, evidence.url);
  });
  const evidenceParagraphs = groupEvidenceNarratives(
    narrativeEvidence(finding),
    renderMarkdownEvidence,
  );
  if (finding.analyzer_runs.length > 0) {
    evidenceParagraphs.splice(
      Math.min(1, evidenceParagraphs.length),
      0,
      finding.analyzer_runs.map(renderMarkdownAnalyzer).join(" "),
    );
  }
  const evidenceLines = evidenceParagraphs.flatMap((paragraph, index) =>
    index === 0 ? [`- 判断依据：${paragraph}`] : ["", `  ${paragraph}`],
  );
  if (evidenceLines.length === 0) {
    evidenceLines.push("- 判断依据：当前没有能证明根因的直接证据。");
  }
  const excerpts = narrativeEvidence(finding)
    .filter((evidence) => evidence.excerpt)
    .map((evidence) => {
      const longestRun = Math.max(
        2,
        ...[...evidence.excerpt.matchAll(/`+/gu)].map((match) => match[0].length),
      );
      const fence = "`".repeat(longestRun + 1);
      return (
        `  ${inlineCode(evidence.symbol)} 关键代码：\n\n` +
        `    ${fence}text\n${evidence.excerpt
          .split(/\r?\n/u)
          .map((line) => `    ${line}`)
          .join("\n")}\n    ${fence}`
      );
    });
  return [
    `### ${escapeMarkdownText(finding.severity)} · ${inlineCode(finding.title)}`,
    "",
    `- 现象：${escapeMarkdownText(finding.phenomenon)}`,
    `- 流量样本：${samples.length > 0 ? samples.join("、") : "无可用 Flow，见证据边界。"}`,
    `- 问题根因：${escapeMarkdownText(finding.root_cause)}`,
    ...evidenceLines,
    ...excerpts,
    `- 影响范围：${escapeMarkdownText(impactSummary(finding))}`,
    `- 处理建议：${renderMarkdownRecommendation(finding)}`,
  ].join("\n");
}

function renderMarkdownTable(headers, values, { rawValues = false } = {}) {
  return [
    `| ${headers.join(" | ")} |`,
    `| ${headers.map(() => "---:").join(" | ")} |`,
    `| ${values.map((value) => (rawValues ? value : escapeMarkdownText(value))).join(" | ")} |`,
  ].join("\n");
}

function displayCount(value, unavailableText = "暂无") {
  return value === null ? unavailableText : String(value);
}

function effectiveFlows(funnel) {
  return Math.max(0, funnel.total_flows - funnel.sent_failure);
}

function displayRatio(value, unavailableText = "暂无") {
  if (value === null) {
    return unavailableText;
  }
  return `${Number((value * 100).toFixed(2))}%`;
}

function impactSummary(finding) {
  const counts = finding.impact_counts;
  return `影响 ${counts.methods} 个接口/方法、${counts.flows} 条流量、${counts.field_clusters} 个字段聚类。`;
}

function sortFindings(findings) {
  return findings
    .map((finding, index) => ({ finding, index }))
    .sort(
      (left, right) =>
        SEVERITY_RANK.get(left.finding.severity) - SEVERITY_RANK.get(right.finding.severity) ||
        CONFIDENCE_RANK.get(left.finding.confidence) -
          CONFIDENCE_RANK.get(right.finding.confidence) ||
        right.finding.impact_counts.flows - left.finding.impact_counts.flows ||
        left.index - right.index,
    )
    .map(({ finding }) => finding);
}

function collectEvidence(report) {
  const result = new Map();
  for (const collection of ["defects", "diff_attributions", "replay_failures"]) {
    for (const finding of report[collection]) {
      for (const evidence of finding.evidence) {
        result.set(evidence.id, evidence);
      }
    }
  }
  for (const evidence of report.evidence_boundaries) {
    result.set(evidence.id, evidence);
  }
  return result;
}

function replaceTemplate(template, replacements) {
  let result = template;
  for (const [key, value] of Object.entries(replacements)) {
    result = result.replaceAll(`{{${key}}}`, value);
  }
  return result;
}

export function renderMarkdown(report, template) {
  const defects = sortFindings(report.defects);
  const diffAttributions = sortFindings(report.diff_attributions);
  const replayFailures = sortFindings(report.replay_failures);
  const defectSection =
    defects.length === 0
      ? ""
      : `## 问题汇总\n\n${defects.map(renderMarkdownFinding).join("\n\n")}\n\n`;
  const funnel = report.funnel;
  const sufficiency = report.test_sufficiency;
  const renderCollection = (items, emptyText) =>
    items.length === 0 ? emptyText : items.map(renderMarkdownFinding).join("\n\n");
  const allEvidence = collectEvidence(report);
  const actionSection =
    report.actions.length === 0
      ? "无。"
      : report.actions
          .map((action, index) => {
            const links = renderMarkdownActionEvidence(action, allEvidence);
            return (
              `${index + 1}. ${escapeMarkdownText(action.owner)}：${escapeMarkdownText(trimTerminalPunctuation(action.change))}；` +
              `对象：${escapeMarkdownText(action.target)}；验收：${escapeMarkdownText(trimTerminalPunctuation(action.verification))}。` +
              (links.length > 0 ? ` 证据：${links.join("、")}。` : "")
            );
          })
          .join("\n");

  return `${replaceTemplate(template, {
    TASK_ID: escapeMarkdownText(report.metadata.task_id),
    METRIC_TABLE: renderMarkdownTable(
      ["有效流量", "DIFF 流量", "缺陷", "接口覆盖率", "代码覆盖率"],
      [
        displayCount(effectiveFlows(funnel)),
        displayCount(funnel.diff_flows),
        String(defects.length),
        displayRatio(sufficiency.interface_coverage, "暂无"),
        displayRatio(sufficiency.code_coverage, "暂无"),
      ],
    ),
    OVERALL_CONCLUSION: report.verdict.summary,
    DEFECT_SECTION: defectSection.trimEnd(),
    DIFF_SECTION: renderCollection(diffAttributions, "无 DIFF 流量"),
    REPLAY_FAILURE_SECTION: renderCollection(replayFailures, "无回放失败流量"),
    ACTION_SECTION: actionSection,
  }).trim()}\n`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function htmlLink(evidence, label = evidenceLabel(evidence)) {
  return `<a href="${escapeHtml(evidence.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

function renderHtmlEvidence(evidence) {
  let detail;
  if (evidence.kind === "code" || evidence.kind === "error_catalog") {
    detail = `服务 <code>${escapeHtml(evidence.psm)}</code> 的 ${htmlLink(evidence)} 在 <code>${escapeHtml(evidence.symbol)}</code> 中${escapeHtml(trimTerminalPunctuation(evidence.logic))}；${escapeHtml(trimTerminalPunctuation(evidence.summary))}。`;
  } else if (evidence.kind === "log" || evidence.kind === "trace") {
    const reference = evidence.url
      ? htmlLink(evidence)
      : `<code>${escapeHtml(evidenceLabel(evidence))}</code>`;
    detail = `任务时间窗 <code>${escapeHtml(evidence.time_window)}</code> 内，服务 <code>${escapeHtml(evidence.psm)}</code> 的 ${reference} 命中“${escapeHtml(trimTerminalPunctuation(evidence.observation))}”，印证该执行路径；${escapeHtml(trimTerminalPunctuation(evidence.summary))}。`;
  } else if (evidence.kind === "flow") {
    detail = `结果印证：${htmlLink(evidence)} 中服务 <code>${escapeHtml(evidence.psm)}</code> 的回放响应 / DIFF 显示${escapeHtml(trimTerminalPunctuation(evidence.observable_result))}。`;
  } else if (
    evidence.kind === "task_config" ||
    evidence.kind === "config" ||
    evidence.kind === "deployment"
  ) {
    detail = `${htmlLink(evidence)} 证明 <code>${escapeHtml(evidence.effective_time_window)}</code> 内实际值为“${escapeHtml(trimTerminalPunctuation(evidence.observed_value))}”，${escapeHtml(trimTerminalPunctuation(evidence.logic))}；${escapeHtml(trimTerminalPunctuation(evidence.summary))}。`;
  } else {
    detail = `上下文：${htmlLink(evidence)}：${escapeHtml(trimTerminalPunctuation(evidence.summary))}。`;
  }
  const excerpt = evidence.excerpt
    ? `<pre class="code-excerpt"><code>${escapeHtml(evidence.excerpt)}</code></pre>`
    : "";
  return `${detail}${excerpt}`;
}

function renderHtmlAnalyzer(run) {
  return `<strong>canonical Analyzer</strong>：${escapeHtml(analyzerNarrative(run))}。`;
}

function renderHtmlEvidenceNarrative(finding) {
  const paragraphs = groupEvidenceNarratives(narrativeEvidence(finding), renderHtmlEvidence);
  if (finding.analyzer_runs.length > 0) {
    paragraphs.splice(
      Math.min(1, paragraphs.length),
      0,
      finding.analyzer_runs.map(renderHtmlAnalyzer).join(" "),
    );
  }
  if (paragraphs.length === 0) {
    return "<p>当前没有能证明根因的直接证据。</p>";
  }
  return paragraphs.map((paragraph) => `<p>${paragraph}</p>`).join("");
}

function renderHtmlRecommendation(finding) {
  const recommendation = finding.recommendation;
  const evidenceById = new Map(finding.evidence.map((evidence) => [evidence.id, evidence]));
  const links = recommendation.evidence_ids
    .map((id) => evidenceById.get(id))
    .filter((evidence) => evidence && evidence.url)
    .map((evidence) => htmlLink(evidence))
    .join("、");
  const boundaryAdvice = materialBoundaries(finding)
    .map(
      (boundary) =>
        `当前受阻：${escapeHtml(trimTerminalPunctuation(boundary.reason))}；` +
        `补齐方式：${escapeHtml(trimTerminalPunctuation(boundary.recovery_action))}。`,
    )
    .join(" ");
  return [
    `<strong>${escapeHtml(recommendation.owner)}</strong> 负责 ${escapeHtml(recommendation.target)}：`,
    `${escapeHtml(trimTerminalPunctuation(recommendation.change))}；`,
    `验收标准：${escapeHtml(trimTerminalPunctuation(recommendation.verification))}。`,
    boundaryAdvice,
    links ? `复验证据：${links}。` : "",
  ].join(" ");
}

function renderHtmlActionEvidence(action, allEvidence) {
  return action.evidence_ids
    .map((id) => allEvidence.get(id))
    .filter(Boolean)
    .map((evidence) => {
      if (evidence.url) {
        return htmlLink(evidence);
      }
      if (evidence.kind === "evidence_boundary") {
        return `<span class="evidence-boundary-inline">证据边界：${escapeHtml(trimTerminalPunctuation(evidence.reason))}；补证动作：${escapeHtml(trimTerminalPunctuation(evidence.recovery_action))}</span>`;
      }
      return `<code>${escapeHtml(evidenceLabel(evidence))}</code>`;
    });
}

function findingTone(finding, kind) {
  if (kind === "defect") {
    return "danger";
  }
  if (finding.root_cause_type === "系统噪音" || finding.expectedness === "预期内") {
    return "success";
  }
  if (finding.confidence === "低" || finding.root_cause_type === "稳定性问题") {
    return "warning";
  }
  return "info";
}

function renderHtmlFindingBadges(finding) {
  return `<span class="badge badge--reason" data-reason="${escapeHtml(finding.finding_reason)}">${escapeHtml(finding.finding_reason)}</span>`;
}

function renderHtmlFinding(finding, kind) {
  const samples = finding.samples
    .slice(0, MAX_RENDERED_SAMPLES)
    .map((sample) => {
      const evidence = finding.evidence.find((item) => item.id === sample.evidence_id);
      return htmlLink(evidence, sample.display_name);
    })
    .join("");
  return `
    <article class="finding" data-kind="${escapeHtml(kind)}" data-tone="${findingTone(finding, kind)}">
      <header class="finding-header">
        <h3>${escapeHtml(finding.severity)} · ${escapeHtml(finding.title)}</h3>
        <div class="badges">
          ${renderHtmlFindingBadges(finding)}
        </div>
      </header>
      <dl class="finding-details">
        <dt>现象</dt>
        <dd><p>${escapeHtml(finding.phenomenon)}</p></dd>
        <dt>流量样本</dt>
        <dd class="sample-links">${samples || "无可用 Flow，见证据边界。"}</dd>
        <dt>问题根因</dt>
        <dd><p>${escapeHtml(finding.root_cause)}</p></dd>
        <dt>判断依据</dt>
        <dd><div class="evidence-narrative">${renderHtmlEvidenceNarrative(finding)}</div></dd>
        <dt>影响范围</dt>
        <dd><p>${escapeHtml(impactSummary(finding))}</p></dd>
        <dt>处理建议</dt>
        <dd><p>${renderHtmlRecommendation(finding)}</p></dd>
      </dl>
    </article>`;
}

function renderHtmlSection(id, title, findings, kind, emptyText) {
  const content =
    findings.length === 0
      ? `<p class="empty-state">${escapeHtml(emptyText)}</p>`
      : `<div class="finding-list">${findings
          .map((finding) => renderHtmlFinding(finding, kind))
          .join("")}</div>`;
  return `
    <section class="report-section" id="${id}" aria-labelledby="${id}-title">
      <h2 class="section-heading" id="${id}-title">${title}</h2>
      ${content}
    </section>`;
}

function coverageTone(value) {
  if (value === null) {
    return "warning";
  }
  return value < 0.5 ? "danger" : value < 0.8 ? "warning" : "info";
}

function verdictTone(report) {
  return report.defects.length > 0 ? "danger" : "success";
}

function renderMetric(label, value, tone = "neutral") {
  return `<div class="metric" data-tone="${tone}"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`;
}

function renderCoverageState(detail) {
  if (detail.total_flows === null || detail.failed_flows === null) {
    return { value: "未知", state: "unknown" };
  }
  const covered = detail.total_flows - detail.failed_flows > 0;
  return { value: covered ? "是" : "否", state: String(covered) };
}

function renderInterfaceCoverageMetric(sufficiency) {
  const details = sufficiency.method_coverage_details ?? [];
  const rows = details
    .map((detail) => {
      const coverage = renderCoverageState(detail);
      return (
        `<tr><td>${escapeHtml(detail.method)}</td>` +
        `<td>${escapeHtml(displayCount(detail.total_flows, "暂无"))}</td>` +
        `<td>${escapeHtml(displayCount(detail.failed_flows, "暂无"))}</td>` +
        `<td><span class="coverage-state" data-covered="${coverage.state}">${coverage.value}</span></td></tr>`
      );
    })
    .join("");
  const expected = displayCount(sufficiency.expected_methods, "暂无");
  const actual = displayCount(sufficiency.actual_methods, "暂无");
  const table =
    rows.length === 0
      ? '<p class="coverage-empty">暂无预期回放接口明细。</p>'
      : '<table class="coverage-table">' +
        '<thead><tr><th scope="col">预期回放的接口</th><th scope="col">回放流量总数</th>' +
        '<th scope="col">回放失败流量数</th><th scope="col">是否有效覆盖</th></tr></thead>' +
        `<tbody>${rows}</tbody></table>`;
  return (
    `<div class="metric metric--coverage" data-tone="${coverageTone(sufficiency.interface_coverage)}" ` +
    'tabindex="0" aria-controls="interface-coverage-detail">' +
    "<dt>接口覆盖率</dt>" +
    `<dd><span class="metric-value">${escapeHtml(displayRatio(sufficiency.interface_coverage, "暂无"))}</span>` +
    '<div class="coverage-popover" id="interface-coverage-detail" role="region" aria-label="接口覆盖率明细">' +
    `<p class="coverage-summary">本次预期回放 ${escapeHtml(expected)} 个接口，实际回放 ${escapeHtml(actual)} 个接口。</p>` +
    `${table}</div></dd></div>`
  );
}

export function renderHtml(report, template) {
  const funnel = report.funnel;
  const sufficiency = report.test_sufficiency;
  const defects = sortFindings(report.defects);
  const diffAttributions = sortFindings(report.diff_attributions);
  const replayFailures = sortFindings(report.replay_failures);
  const allEvidence = collectEvidence(report);
  const replayReportUrl = buildReplayReportUrl(report.metadata);
  const body = `
    <header class="report-header">
      <div class="report-header-main">
        <h1>FTF 任务 ${escapeHtml(report.metadata.task_id)} 任务级归因报告</h1>
      </div>
      <a class="report-link" href="${escapeHtml(replayReportUrl)}" target="_blank" rel="noopener noreferrer">回放报告</a>
    </header>
    <main id="report">
      <section class="report-metrics" aria-label="任务关键指标">
        <dl class="metric-grid">
          ${renderMetric("有效流量", displayCount(effectiveFlows(funnel)), "info")}
          ${renderMetric("DIFF 流量", displayCount(funnel.diff_flows), "warning")}
          ${renderMetric("缺陷", String(defects.length), "danger")}
          ${renderInterfaceCoverageMetric(sufficiency)}
          ${renderMetric("代码覆盖率", displayRatio(sufficiency.code_coverage, "暂无"), coverageTone(sufficiency.code_coverage))}
        </dl>
      </section>
      <section class="report-section" aria-labelledby="conclusion-title">
        <h2 class="section-heading" id="conclusion-title">总体结论</h2>
        <div class="status-panel" data-tone="${verdictTone(report)}">
          <p class="status-copy">${escapeHtml(report.verdict.summary)}</p>
        </div>
      </section>
      ${defects.length === 0 ? "" : renderHtmlSection("defects", "问题汇总", defects, "defect", "")}
      ${renderHtmlSection("diff-attribution", "DIFF 归因分析", diffAttributions, "diff", "无 DIFF 流量")}
      ${renderHtmlSection("replay-failure-attribution", "回放失败归因分析", replayFailures, "failure", "无回放失败流量")}
      <section class="report-section" id="actions" aria-labelledby="actions-title">
        <h2 class="section-heading" id="actions-title">其他建议项</h2>
        ${
          report.actions.length === 0
            ? '<p class="empty-state">无。</p>'
            : `<ol class="action-list">${report.actions
                .map((action) => {
                  const links = renderHtmlActionEvidence(action, allEvidence).join("、");
                  return (
                    `<li><strong>${escapeHtml(action.owner)}</strong>：${escapeHtml(trimTerminalPunctuation(action.change))}；` +
                    `对象：${escapeHtml(action.target)}；验收：${escapeHtml(trimTerminalPunctuation(action.verification))}。` +
                    (links ? ` 证据：${links}。` : "") +
                    "</li>"
                  );
                })
                .join("")}</ol>`
        }
      </section>
    </main>`;

  return replaceTemplate(template, {
    DOCUMENT_TITLE: `FTF 任务 ${escapeHtml(report.metadata.task_id)} 任务级归因报告`,
    REPORT_BODY: body,
    TASK_ID: escapeHtml(report.metadata.task_id),
    SNAPSHOT_TIME: escapeHtml(report.metadata.snapshot_time),
  });
}

function validateRenderedOutput(content, format, report) {
  if (PLACEHOLDER_PATTERN.test(content)) {
    fail("rendered output contains a template placeholder");
  }
  for (const pattern of SENSITIVE_PATTERNS) {
    if (pattern.test(content)) {
      fail("rendered output contains credential-shaped content");
    }
  }
  if (format === "html") {
    if (/<script\b[^>]*\bsrc=/iu.test(content) || /<link\b[^>]*\bhref=/iu.test(content)) {
      fail("rendered HTML contains an external resource");
    }
    if (/\son[a-z]+\s*=/iu.test(content)) {
      fail("rendered HTML contains an inline event handler");
    }
    if (!/^<!doctype html>/iu.test(content)) {
      fail("rendered HTML is not a complete document");
    }
    if (!/<meta\s+name="referrer"\s+content="no-referrer"\s*\/>/iu.test(content)) {
      fail("rendered HTML must use a no-referrer policy");
    }
    if (/<script\b/iu.test(content)) {
      fail("rendered HTML must not contain scripts");
    }
  }
}

function parseArgs(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--validate-only") {
      if (options.validateOnly) {
        fail("--validate-only may be supplied only once");
      }
      options.validateOnly = true;
      continue;
    }
    if (!["--input", "--format", "--output", "--output-base", "--output-dir"].includes(argument)) {
      fail(`unknown argument: ${argument}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      fail(`${argument} requires a value`);
    }
    const key = argument.slice(2);
    if (Object.hasOwn(options, key)) {
      fail(`${argument} may be supplied only once`);
    }
    options[key] = value;
    index += 1;
  }
  requireString(options.input, "--input");
  if (options.validateOnly) {
    if (options.format || options.output || options["output-base"] || options["output-dir"]) {
      fail("--validate-only cannot be combined with output options");
    }
    return options;
  }
  if (options["output-dir"]) {
    if (options.format || options.output || options["output-base"]) {
      fail("--output-dir cannot be combined with --format, --output, or --output-base");
    }
    return options;
  }
  if (options["output-base"]) {
    if (options.format || options.output) {
      fail("--output-base cannot be combined with --format or --output");
    }
    if (/\.(?:md|html)$/iu.test(options["output-base"])) {
      fail("--output-base must not include a .md or .html extension");
    }
    return options;
  }
  requireEnum(options.format, ["markdown", "html"], "--format");
  requireString(options.output, "--output");
  const expectedExtension = options.format === "markdown" ? ".md" : ".html";
  if (path.extname(options.output).toLowerCase() !== expectedExtension) {
    fail(`output extension must be ${expectedExtension} for ${options.format}`);
  }
  return options;
}

function readReport(inputPath) {
  let source;
  try {
    source = fs.readFileSync(inputPath, "utf8");
  } catch (error) {
    fail(`cannot read input ${inputPath}: ${error.message}`);
  }
  try {
    return JSON.parse(source);
  } catch (error) {
    fail(`invalid JSON in ${inputPath}: ${error.message}`);
  }
}

function writeAtomicBatch(outputs) {
  const nonce = `${process.pid}.${Date.now()}`;
  const staged = outputs.map(({ outputPath, content }, index) => {
    const absolute = path.resolve(outputPath);
    fs.mkdirSync(path.dirname(absolute), { recursive: true });
    if (fs.existsSync(absolute) && !fs.lstatSync(absolute).isFile()) {
      fail(`output path must be a regular file: ${absolute}`);
    }
    return {
      absolute,
      content,
      temporary: path.join(
        path.dirname(absolute),
        `.${path.basename(absolute)}.${nonce}.${index}.tmp`,
      ),
      backup: path.join(
        path.dirname(absolute),
        `.${path.basename(absolute)}.${nonce}.${index}.bak`,
      ),
      hadOriginal: fs.existsSync(absolute),
      published: false,
    };
  });
  if (new Set(staged.map(({ absolute }) => absolute)).size !== staged.length) {
    fail("output paths must be unique");
  }
  try {
    for (const item of staged) {
      fs.writeFileSync(item.temporary, item.content, { encoding: "utf8", mode: 0o600 });
    }
    for (const item of staged) {
      if (item.hadOriginal) {
        fs.renameSync(item.absolute, item.backup);
      }
    }
    for (const item of staged) {
      fs.renameSync(item.temporary, item.absolute);
      item.published = true;
    }
  } catch (error) {
    for (const item of [...staged].reverse()) {
      if (item.published) {
        fs.rmSync(item.absolute, { force: true });
      }
      if (fs.existsSync(item.backup)) {
        fs.renameSync(item.backup, item.absolute);
      }
      fs.rmSync(item.temporary, { force: true });
    }
    throw error;
  }
  for (const item of staged) {
    fs.rmSync(item.backup, { force: true });
  }
}

function renderOutput(report, format) {
  const templateName = format === "markdown" ? "task-analysis.md" : "task-analysis.html";
  const template = fs.readFileSync(path.join(templateDirectory, templateName), "utf8");
  const content =
    format === "markdown" ? renderMarkdown(report, template) : renderHtml(report, template);
  validateRenderedOutput(content, format, report);
  return content;
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const report = validateReport(readReport(path.resolve(options.input)));
  if (options.validateOnly) {
    return;
  }
  if (options["output-dir"]) {
    const outputDirectory = options["output-dir"];
    const outputs = [
      {
        outputPath: path.join(outputDirectory, "ftf-report.md"),
        content: renderOutput(report, "markdown"),
      },
      {
        outputPath: path.join(outputDirectory, "ftf-report.html"),
        content: renderOutput(report, "html"),
      },
    ];
    writeAtomicBatch(outputs);
    return;
  }
  if (options["output-base"]) {
    const outputBase = options["output-base"];
    const outputs = [
      { outputPath: `${outputBase}.md`, content: renderOutput(report, "markdown") },
      { outputPath: `${outputBase}.html`, content: renderOutput(report, "html") },
    ];
    writeAtomicBatch(outputs);
    return;
  }
  writeAtomicBatch([{ outputPath: options.output, content: renderOutput(report, options.format) }]);
}

function invokedHrefs(argvPath) {
  if (!argvPath) {
    return [];
  }
  const absolutePath = path.resolve(argvPath);
  // import.meta.url resolves symlinks by default, but keeps the symlinked path under
  // --preserve-symlinks-main. Accept either form so the main guard fires in both modes.
  const hrefs = [pathToFileURL(absolutePath).href];
  try {
    hrefs.push(pathToFileURL(fs.realpathSync(absolutePath)).href);
  } catch {
    // argv[1] is not resolvable (e.g. a placeholder when imported as a library).
  }
  return hrefs;
}

if (invokedHrefs(process.argv[1]).includes(import.meta.url)) {
  main().catch((error) => {
    process.stderr.write(`render-task-analysis: ${error.message}\n`);
    process.exitCode = 1;
  });
}
