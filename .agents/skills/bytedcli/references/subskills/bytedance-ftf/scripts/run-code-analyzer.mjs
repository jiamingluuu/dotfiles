#!/usr/bin/env node

import { spawn } from "node:child_process";
import { constants as bufferConstants } from "node:buffer";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDirectory = path.dirname(fs.realpathSync(fileURLToPath(import.meta.url)));
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
const CLI_IDENTIFIER_PATTERN = /^[A-Za-z0-9._-]+$/u;
const COMMIT_PATTERN = /^[0-9a-f]{40}$/u;
const ANALYZER_REPOSITORY_PATTERN = new RegExp(analyzerRunProperties.repository.pattern, "u");
const SHA256_PATTERN = new RegExp(
  analyzerRunProperties.result_artifact.properties.sha256.pattern,
  "u",
);
const CONTRACT_VERSION = "ftf-code-analysis/v1";
const WRAPPER_TIMEOUT_MS = 870 * 1000;
const HOST_WRAPPER_TIMEOUT_SECONDS = 450;
const TERMINATION_GRACE_MS = 2000;
const FORCE_KILL_WAIT_MS = 2000;
const PROCESS_EXIT_POLL_MS = 25;
const STDERR_TAIL_BYTES = 8 * 1024;
const MAX_STDOUT_BYTES = 64 * 1024;
const ANALYZER_STATES = new Set(reportSchema.$defs.analyzerState.enum);
const STATE_FIELDS = [
  ...new Set(
    analyzerRunSchema.oneOf.flatMap((variant) => [
      ...(variant.required ?? []),
      ...(variant.not?.anyOf ?? []).flatMap((constraint) => constraint.required ?? []),
    ]),
  ),
];
const OPTIONAL_SUMMARY_FIELDS = Object.keys(analyzerRunProperties).filter(
  (key) => !analyzerRunRequiredKeys.has(key) && !STATE_FIELDS.includes(key),
);
const TERMINAL_SELF_PROOF = Object.fromEntries(
  Object.entries(analyzerRunProperties.self_proof.properties).map(([key, definition]) => [
    key,
    definition.const,
  ]),
);
const REGION_PAIRS = new Set(["cn\0China-North", "i18n-tt\0Singapore-Central"]);
const RECOVERY_ACTIONS = {
  dependency_unavailable: "修复 Analyzer 依赖后，针对同一任务与 DIFF 重新发起分析",
  unsupported_region: "补充受支持的任务地域后，针对同一任务与 DIFF 重新发起分析",
  permission_denied:
    "为 Analyzer 运行身份补充 evidence resolver 权限后，针对同一任务与 DIFF 重新发起分析",
  repository_permission_denied:
    "为 Analyzer 运行身份补充目标 Codebase 仓库读取权限后，针对同一任务与 DIFF 重新发起分析",
  repository_identity_mismatch:
    "清理或重建 Analyzer 共享仓库后，针对同一任务与 DIFF 重新发起分析",
  runner_failed: "修复 Analyzer 执行失败后，针对同一任务与 DIFF 重新发起分析",
  runner_interrupted: "确认运行环境稳定后，针对同一任务与 DIFF 重新发起分析",
  stdout_invalid: "修复 Analyzer canonical 输出后，针对同一任务与 DIFF 重新发起分析",
  identity_mismatch: "修复任务或 DIFF 身份不一致后，针对同一目标重新发起分析",
  revision_mismatch: "修复代码版本身份后，针对同一任务与 DIFF 重新发起分析",
  state_contract_invalid: "修复 Analyzer 六态契约后，针对同一任务与 DIFF 重新发起分析",
  artifact_integrity_failed: "修复 Analyzer 产物完整性后，针对同一任务与 DIFF 重新发起分析",
};

class AdmissionError extends Error {
  constructor(category, message) {
    super(message);
    this.name = "AdmissionError";
    this.category = category;
  }
}

class ArgumentError extends Error {
  constructor() {
    super("invalid arguments");
    this.name = "ArgumentError";
  }
}

function reject(category, message, diffId) {
  return {
    contract_version: CONTRACT_VERSION,
    status: "rejected",
    evidence_boundary: {
      id: `analyzer-boundary-${diffId}`,
      kind: "evidence_boundary",
      summary: "Analyzer 未形成可准入的 canonical 结果",
      url: null,
      reason: `[${category}] ${message}`,
      recovery_action: RECOVERY_ACTIONS[category],
      material: true,
    },
  };
}

function fail(category, message) {
  throw new AdmissionError(category, message);
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isNonEmptyObject(value) {
  return isObject(value) && Object.keys(value).length > 0;
}

function canonicalize(value) {
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }
  if (isObject(value)) {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

function sameValue(left, right) {
  return JSON.stringify(canonicalize(left)) === JSON.stringify(canonicalize(right));
}

function requireIdentifier(value) {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > 256 ||
    value === "." ||
    value === ".." ||
    // 首字符必须是字母数字：以 - 开头的标识符会被下游 argparse 当作 flag 解析。
    !/^[A-Za-z0-9]/u.test(value) ||
    !CLI_IDENTIFIER_PATTERN.test(value)
  ) {
    throw new ArgumentError();
  }
  return value;
}

function requireStringArray(value, at, { empty = true } = {}) {
  if (
    !Array.isArray(value) ||
    (!empty && value.length === 0) ||
    value.some((item) => typeof item !== "string" || item.length === 0)
  ) {
    fail("state_contract_invalid", `${at} 必须是${empty ? "" : "非空"}字符串数组`);
  }
}

function requireObjectArray(value, at, { empty = false } = {}) {
  if (
    !Array.isArray(value) ||
    (!empty && value.length === 0) ||
    value.some((item) => !isNonEmptyObject(item))
  ) {
    fail("state_contract_invalid", `${at} 必须是${empty ? "" : "非空"}对象数组`);
  }
}

function requireAbsent(value, key, at) {
  if (Object.hasOwn(value, key)) {
    fail("state_contract_invalid", `${at}.${key} 不属于当前状态`);
  }
}

export function normalizeCodebaseRepository(value) {
  if (typeof value !== "string" || value.length === 0) {
    fail("identity_mismatch", "repository 为空");
  }
  let repositoryPath;
  if (value.startsWith("git@code.byted.org:")) {
    repositoryPath = value.slice("git@code.byted.org:".length);
    if (/[?#]/u.test(repositoryPath)) {
      fail("identity_mismatch", "repository 不是受支持的 Codebase 地址");
    }
  } else {
    let parsed;
    try {
      parsed = new URL(value);
    } catch {
      fail("identity_mismatch", "repository 不是受支持的 Codebase 地址");
    }
    if (
      parsed.protocol !== "https:" ||
      parsed.hostname !== "code.byted.org" ||
      parsed.port ||
      parsed.username ||
      parsed.password ||
      parsed.search ||
      parsed.hash
    ) {
      fail("identity_mismatch", "repository 不是受支持的 Codebase 地址");
    }
    repositoryPath = parsed.pathname.slice(1);
  }
  const repository = repositoryPath.replace(/\.git$/u, "");
  const segments = repository.split("/");
  if (
    !ANALYZER_REPOSITORY_PATTERN.test(repository) ||
    segments.some((segment) => segment === "." || segment === "..")
  ) {
    fail("identity_mismatch", "repository 路径不合法");
  }
  return repository;
}

export function parseCanonicalStdout(stdoutBuffer) {
  let parsed;
  try {
    parsed = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(stdoutBuffer));
  } catch {
    fail("stdout_invalid", "stdout 不是单一完整 JSON 对象");
  }
  if (!isObject(parsed)) {
    fail("stdout_invalid", "stdout 顶层必须是对象");
  }
  return parsed;
}

function classifyRunnerFailure(stdoutBuffer) {
  let failure;
  try {
    failure = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(stdoutBuffer));
  } catch {
    return null;
  }
  if (!isObject(failure)) {
    return null;
  }
  if (failure.error === "repo preparation failed: repository read permission denied") {
    return {
      category: "repository_permission_denied",
      message: "Codebase 仓库读取权限不足",
    };
  }
  if (failure.error === "repo preparation failed: shared repository identity mismatch") {
    return {
      category: "repository_identity_mismatch",
      message: "Analyzer 共享仓库与任务目标仓库不一致",
    };
  }
  const repositoryPermissionDenied =
    Array.isArray(failure.diff_results) &&
    failure.diff_results.some(
      (diffResult) =>
        isObject(diffResult) &&
        diffResult.analysis_state === "evidence_blocked" &&
        Array.isArray(diffResult.evidence_blockers) &&
        diffResult.evidence_blockers.some(
          (candidate) =>
            isObject(candidate) &&
            candidate.blocker_type === "source_access" &&
            candidate.error_code === "permission_denied" &&
            candidate.analysis_boundary === "repository_source_unavailable",
        ),
    );
  if (repositoryPermissionDenied) {
    return {
      category: "repository_permission_denied",
      message: "Codebase 仓库读取权限不足",
    };
  }
  const blocker = failure.blocker;
  if (
    failure.analysis_state === "evidence_blocked" &&
    isObject(blocker) &&
    blocker.stage === "evidence_resolve" &&
    (blocker.upstream_code === "PERMISSION_DENIED" || blocker.status_code === 403)
  ) {
    return { category: "permission_denied", message: "Evidence resolver 权限不足" };
  }
  return null;
}

function serializedStdout(stdoutBuffer) {
  if (stdoutBuffer.at(-1) !== 0x0a) {
    return stdoutBuffer;
  }
  const withoutLf = stdoutBuffer.subarray(0, stdoutBuffer.length - 1);
  return withoutLf.at(-1) === 0x0d ? withoutLf.subarray(0, withoutLf.length - 1) : withoutLf;
}

function validateProjectionEnvelope(value, stdoutBuffer) {
  for (const key of [
    "task_id",
    "attribution_type",
    "caused_by_code_change",
    "diff_results",
    "result_artifact",
    "projection",
  ]) {
    if (!Object.hasOwn(value, key)) {
      fail("stdout_invalid", `stdout.${key} 缺失`);
    }
  }
  if (
    typeof value.task_id !== "string" ||
    !Array.isArray(value.diff_results) ||
    !isObject(value.result_artifact)
  ) {
    fail("stdout_invalid", "stdout 成功信封字段类型不合法");
  }
  const projection = value.projection;
  if (
    !isObject(projection) ||
    projection.strategy !== "bounded_artifact_backed" ||
    !Number.isSafeInteger(projection.serialized_bytes) ||
    projection.serialized_bytes <= 0 ||
    !Number.isSafeInteger(projection.max_bytes) ||
    projection.max_bytes <= 0 ||
    projection.max_bytes > MAX_STDOUT_BYTES
  ) {
    fail("stdout_invalid", "stdout.projection 元信息不合法");
  }
  const serialized = serializedStdout(stdoutBuffer);
  if (
    serialized.length !== projection.serialized_bytes ||
    serialized.length > projection.max_bytes
  ) {
    fail("stdout_invalid", "stdout.projection 字节声明与实际输出不一致");
  }
}

function validateArtifactEnvelope(value) {
  for (const key of [
    "task_id",
    "repo_url",
    "base_commit_id",
    "target_commit_id",
    "attribution_type",
    "caused_by_code_change",
    "confidence",
    "diff_results",
    "warnings",
  ]) {
    if (!Object.hasOwn(value, key)) {
      fail("artifact_integrity_failed", `artifact.${key} 缺失`);
    }
  }
  requireStringArray(value.warnings, "artifact.warnings");
  if (new Set(value.warnings).size !== value.warnings.length) {
    fail("state_contract_invalid", "artifact.warnings 必须去重");
  }
}

function consumerCore(value) {
  const diff = value.diff_results[0];
  return {
    task_id: value.task_id,
    attribution_type: value.attribution_type,
    caused_by_code_change: value.caused_by_code_change,
    diff: {
      diff_id: diff.diff_id,
      path: diff.path,
      op: diff.op,
      analysis_state: diff.analysis_state,
      caused_by_code_change: diff.caused_by_code_change,
    },
  };
}

function validateState(diff) {
  if (!ANALYZER_STATES.has(diff.analysis_state)) {
    fail("state_contract_invalid", "analysis_state 不受支持");
  }
  if (typeof diff.path !== "string" || diff.path.length === 0) {
    fail("state_contract_invalid", "path 必须是非空字符串");
  }
  if (!["add", "delete", "modify"].includes(diff.op)) {
    fail("state_contract_invalid", "op 不受支持");
  }
  const expected = {
    invalid_observation: ["unknown", null, "low"],
    analysis_incomplete: ["unknown", null, "low"],
    evidence_blocked: ["unknown", null, "low"],
    proven_code_caused: ["caused", true, "high"],
    proven_not_code_caused: ["not_caused", false, "high"],
    runtime_unresolved: ["unknown", null, "low"],
  }[diff.analysis_state];
  if (
    diff.verdict !== expected[0] ||
    diff.caused_by_code_change !== expected[1] ||
    diff.confidence !== expected[2]
  ) {
    fail("state_contract_invalid", "六态与 verdict、因果值或 confidence 不一致");
  }
  requireStringArray(diff.missing_evidence, "diff.missing_evidence");
  requireStringArray(diff.needed_evidence, "diff.needed_evidence");
  if (diff.analysis_state !== "runtime_unresolved") {
    if (diff.missing_evidence.length > 0 || diff.needed_evidence.length > 0) {
      fail("state_contract_invalid", "非 runtime 状态的 evidence 兼容投影必须为空");
    }
  }
  for (const key of OPTIONAL_SUMMARY_FIELDS) {
    if (Object.hasOwn(diff, key) && !isObject(diff[key])) {
      fail("state_contract_invalid", `${key} 必须是对象`);
    }
  }

  const allowed = new Set();
  if (diff.analysis_state === "invalid_observation") {
    requireObjectArray(diff.invalid_observation_details, "diff.invalid_observation_details");
    allowed.add("invalid_observation_details");
  } else if (diff.analysis_state === "analysis_incomplete") {
    requireObjectArray(diff.incomplete_stages, "diff.incomplete_stages");
    allowed.add("incomplete_stages");
  } else if (diff.analysis_state === "evidence_blocked") {
    requireObjectArray(diff.evidence_blockers, "diff.evidence_blockers");
    allowed.add("evidence_blockers");
    if (Object.hasOwn(diff, "incomplete_stages")) {
      if (!Array.isArray(diff.incomplete_stages) || diff.incomplete_stages.length !== 0) {
        fail("state_contract_invalid", "evidence_blocked.incomplete_stages 只能为空数组");
      }
      allowed.add("incomplete_stages");
    }
  } else if (diff.analysis_state === "proven_code_caused") {
    if (!isNonEmptyObject(diff.causal_proof) || !sameValue(diff.self_proof, TERMINAL_SELF_PROOF)) {
      fail("state_contract_invalid", "proven_code_caused proof 不完整");
    }
    allowed.add("causal_proof");
    allowed.add("self_proof");
  } else if (diff.analysis_state === "proven_not_code_caused") {
    if (
      !isNonEmptyObject(diff.exclusion_proof) ||
      !sameValue(diff.self_proof, TERMINAL_SELF_PROOF)
    ) {
      fail("state_contract_invalid", "proven_not_code_caused proof 不完整");
    }
    allowed.add("exclusion_proof");
    allowed.add("self_proof");
    if (Object.hasOwn(diff, "alternative_runtime_proof")) {
      if (
        !isNonEmptyObject(diff.alternative_runtime_proof) ||
        typeof diff.exclusion_proof.proof_id !== "string" ||
        diff.alternative_runtime_proof.code_exclusion_ref !== diff.exclusion_proof.proof_id
      ) {
        fail("state_contract_invalid", "alternative_runtime_proof 与 exclusion_proof 不一致");
      }
      allowed.add("alternative_runtime_proof");
    }
  } else {
    requireObjectArray(diff.evidence_gaps, "diff.evidence_gaps");
    if (!sameValue(diff.self_proof, TERMINAL_SELF_PROOF)) {
      fail("state_contract_invalid", "runtime_unresolved self_proof 不完整");
    }
    allowed.add("evidence_gaps");
    allowed.add("self_proof");
    if (Object.hasOwn(diff, "incomplete_stages")) {
      if (!Array.isArray(diff.incomplete_stages) || diff.incomplete_stages.length !== 0) {
        fail("state_contract_invalid", "runtime_unresolved.incomplete_stages 只能为空数组");
      }
      allowed.add("incomplete_stages");
    }
  }
  for (const key of STATE_FIELDS) {
    if (!allowed.has(key)) {
      requireAbsent(diff, key, "diff");
    }
  }
}

function validateAggregate(result, state) {
  const expected =
    state === "proven_code_caused"
      ? ["bug_code", true]
      : state === "proven_not_code_caused"
        ? ["not_code_related", false]
        : ["unknown", null];
  if (
    result.attribution_type !== expected[0] ||
    result.caused_by_code_change !== expected[1] ||
    typeof result.confidence !== "number" ||
    !Number.isFinite(result.confidence) ||
    result.confidence < 0 ||
    result.confidence > 1
  ) {
    fail("state_contract_invalid", "顶层聚合与目标六态不一致");
  }
}

function expectedArtifactDirectory(workspaceRoot, taskId, diffId) {
  return path.join(workspaceRoot, `task-${taskId}`, "result-artifacts", diffId);
}

export function readAndValidateArtifact(descriptor, workspaceRoot, taskId, diffId) {
  if (
    !isObject(descriptor) ||
    Object.keys(descriptor).length !== 3 ||
    !["path", "bytes", "sha256"].every((key) => Object.hasOwn(descriptor, key)) ||
    typeof descriptor.path !== "string" ||
    !path.isAbsolute(descriptor.path) ||
    !Number.isSafeInteger(descriptor.bytes) ||
    descriptor.bytes <= 0 ||
    descriptor.bytes > bufferConstants.MAX_LENGTH ||
    typeof descriptor.sha256 !== "string" ||
    !SHA256_PATTERN.test(descriptor.sha256)
  ) {
    fail("artifact_integrity_failed", "artifact 描述不合法");
  }
  try {
    const expectedDirectoryPath = expectedArtifactDirectory(workspaceRoot, taskId, diffId);
    const expectedDirectory = fs.realpathSync(expectedDirectoryPath);
    if (
      expectedDirectory !== expectedDirectoryPath ||
      !isInside(workspaceRoot, expectedDirectory)
    ) {
      fail("artifact_integrity_failed", "artifact 目录越界");
    }
    const directoryBefore = fs.statSync(expectedDirectory);
    const artifactPath = fs.realpathSync(descriptor.path);
    if (
      path.dirname(artifactPath) !== expectedDirectory ||
      fs.lstatSync(descriptor.path).isSymbolicLink()
    ) {
      fail("artifact_integrity_failed", "artifact 路径越界或为符号链接");
    }
    if (typeof fs.constants.O_NOFOLLOW !== "number") {
      fail("artifact_integrity_failed", "当前平台不支持安全打开 artifact");
    }
    const descriptorFd = fs.openSync(artifactPath, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
    try {
      const before = fs.fstatSync(descriptorFd);
      if (!before.isFile()) {
        fail("artifact_integrity_failed", "artifact 不是普通文件");
      }
      if (before.size !== descriptor.bytes) {
        fail("artifact_integrity_failed", "artifact 字节数与声明不一致");
      }
      const raw = fs.readFileSync(descriptorFd);
      const after = fs.fstatSync(descriptorFd);
      const directoryAfter = fs.statSync(expectedDirectory);
      if (
        before.dev !== after.dev ||
        before.ino !== after.ino ||
        before.size !== after.size ||
        before.mtimeMs !== after.mtimeMs ||
        directoryBefore.dev !== directoryAfter.dev ||
        directoryBefore.ino !== directoryAfter.ino
      ) {
        fail("artifact_integrity_failed", "artifact 在读取期间发生变化");
      }
      if (raw.length !== descriptor.bytes) {
        fail("artifact_integrity_failed", "artifact 字节数与声明不一致");
      }
      const sha256 = crypto.createHash("sha256").update(raw).digest("hex");
      if (sha256 !== descriptor.sha256) {
        fail("artifact_integrity_failed", "artifact SHA-256 与声明不一致");
      }
      let artifact;
      try {
        artifact = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(raw));
      } catch {
        fail("artifact_integrity_failed", "artifact 不是合法 JSON");
      }
      if (!isObject(artifact)) {
        fail("artifact_integrity_failed", "artifact 顶层必须是对象");
      }
      return artifact;
    } finally {
      fs.closeSync(descriptorFd);
    }
  } catch (error) {
    if (error instanceof AdmissionError) {
      throw error;
    }
    fail("artifact_integrity_failed", "artifact 无法安全读取");
  }
}

export function adaptCanonicalAnalyzerResult({
  requestIdentity,
  analyzerWorkspaceRoot,
  exitCode,
  interrupted,
  timedOut = false,
  stdoutTooLarge = false,
  stdoutBuffer,
}) {
  const diffId = requestIdentity.diffId;
  try {
    if (stdoutTooLarge || stdoutBuffer.length > MAX_STDOUT_BYTES) {
      fail("stdout_invalid", "Analyzer stdout 超过 64 KiB 上限");
    }
    if (timedOut) {
      fail("runner_failed", "Analyzer wrapper 执行超时");
    }
    if (interrupted || exitCode === null) {
      fail("runner_interrupted", "Analyzer 执行被中断");
    }
    if (exitCode !== 0) {
      const classified = classifyRunnerFailure(stdoutBuffer);
      if (classified) {
        fail(classified.category, classified.message);
      }
      fail("runner_failed", "Analyzer standard run 执行失败");
    }
    const result = parseCanonicalStdout(stdoutBuffer);
    validateProjectionEnvelope(result, stdoutBuffer);
    if (result.task_id !== requestIdentity.taskId) {
      fail("identity_mismatch", "task_id 与请求不一致");
    }
    if (
      !Array.isArray(result.diff_results) ||
      result.diff_results.length !== 1 ||
      !isObject(result.diff_results[0]) ||
      result.diff_results[0].diff_id !== diffId
    ) {
      fail("identity_mismatch", "目标 DIFF 不唯一或与请求不一致");
    }
    const artifact = readAndValidateArtifact(
      result.result_artifact,
      analyzerWorkspaceRoot,
      requestIdentity.taskId,
      diffId,
    );
    validateArtifactEnvelope(artifact);
    if (artifact.task_id !== requestIdentity.taskId) {
      fail("identity_mismatch", "artifact task_id 与请求不一致");
    }
    if (
      !COMMIT_PATTERN.test(artifact.base_commit_id) ||
      !COMMIT_PATTERN.test(artifact.target_commit_id)
    ) {
      fail("revision_mismatch", "base/target revision 必须是 40 位小写提交");
    }
    if (
      !Array.isArray(artifact.diff_results) ||
      artifact.diff_results.length !== 1 ||
      !isObject(artifact.diff_results[0]) ||
      artifact.diff_results[0].diff_id !== diffId
    ) {
      fail("identity_mismatch", "artifact 目标 DIFF 不唯一或与请求不一致");
    }
    const diff = artifact.diff_results[0];
    validateState(diff);
    validateAggregate(artifact, diff.analysis_state);
    if (!sameValue(consumerCore(result), consumerCore(artifact))) {
      fail("artifact_integrity_failed", "stdout 与 artifact 稳定核心字段不一致");
    }
    const repository = normalizeCodebaseRepository(artifact.repo_url);
    const resultArtifact = {
      bytes: result.result_artifact.bytes,
      sha256: result.result_artifact.sha256,
    };
    if (artifact.base_commit_id === artifact.target_commit_id) {
      if (
        diff.analysis_state !== "proven_not_code_caused" ||
        diff.verdict !== "not_caused" ||
        diff.caused_by_code_change !== false ||
        diff.exclusion_proof?.proof_type !== "revision_tree_delta_empty"
      ) {
        fail(
          "state_contract_invalid",
          "相同 revision 必须由 revision_tree_delta_empty 证明不可归因于代码变更",
        );
      }
      return {
        contract_version: CONTRACT_VERSION,
        status: "not_applicable",
        reason: "no_revision_delta",
        task_id: artifact.task_id,
        similar_diff_id: diff.diff_id,
        repository,
        revision: artifact.base_commit_id,
        result_artifact: resultArtifact,
      };
    }
    const analyzerRun = {
      task_id: artifact.task_id,
      similar_diff_id: diff.diff_id,
      repository,
      base_ref: artifact.base_commit_id,
      target_ref: artifact.target_commit_id,
      aggregate: {
        attribution_type: artifact.attribution_type,
        caused_by_code_change: artifact.caused_by_code_change,
        confidence: artifact.confidence,
      },
      path: diff.path,
      op: diff.op,
      analysis_state: diff.analysis_state,
      verdict: diff.verdict,
      caused_by_code_change: diff.caused_by_code_change,
      confidence: diff.confidence,
      missing_evidence: structuredClone(diff.missing_evidence),
      needed_evidence: structuredClone(diff.needed_evidence),
      warnings: structuredClone(artifact.warnings),
      result_artifact: resultArtifact,
    };
    for (const key of [...STATE_FIELDS, ...OPTIONAL_SUMMARY_FIELDS]) {
      if (Object.hasOwn(diff, key)) {
        analyzerRun[key] = structuredClone(diff[key]);
      }
    }
    return { contract_version: CONTRACT_VERSION, status: "accepted", analyzer_run: analyzerRun };
  } catch (error) {
    if (error instanceof AdmissionError) {
      return reject(error.category, error.message, diffId);
    }
    return reject("artifact_integrity_failed", "Analyzer 结果校验失败", diffId);
  }
}

function isInside(root, candidate) {
  const relative = path.relative(root, candidate);
  return (
    relative === "" ||
    (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative))
  );
}

export function resolveAnalyzerSkillDirectory(inputDirectory) {
  if (typeof inputDirectory !== "string" || !path.isAbsolute(inputDirectory)) {
    fail("dependency_unavailable", "Analyzer Skill 目录必须是绝对路径");
  }
  try {
    const root = fs.realpathSync(inputDirectory);
    const rootStat = fs.statSync(root);
    if (!rootStat.isDirectory()) {
      fail("dependency_unavailable", "Analyzer Skill 目录不可用");
    }
    const skillPath = fs.realpathSync(path.join(root, "SKILL.md"));
    const runnerPath = fs.realpathSync(path.join(root, "scripts", "tool.py"));
    if (
      !isInside(root, skillPath) ||
      !isInside(root, runnerPath) ||
      !fs.statSync(skillPath).isFile() ||
      !fs.statSync(runnerPath).isFile()
    ) {
      fail("dependency_unavailable", "Analyzer Skill 文件不在同一目录树");
    }
    const frontmatter =
      fs.readFileSync(skillPath, "utf8").match(/^---\n([\s\S]*?)\n---/u)?.[1] ?? "";
    if (!/^name:\s*["']?ftf-code-analyzer["']?\s*$/mu.test(frontmatter)) {
      fail("dependency_unavailable", "Analyzer Skill 名称不匹配");
    }
    fs.accessSync(runnerPath, fs.constants.R_OK);
    return { root, runnerPath };
  } catch (error) {
    if (error instanceof AdmissionError) {
      throw error;
    }
    fail("dependency_unavailable", "Analyzer Skill 不可用");
  }
}

export function ensureAnalyzerWorkspaceRoot({ temporaryRoot = os.tmpdir() } = {}) {
  const uid = typeof process.getuid === "function" ? process.getuid() : os.userInfo().uid;
  let resolvedTemporaryRoot;
  try {
    resolvedTemporaryRoot = fs.realpathSync(temporaryRoot);
  } catch {
    fail("dependency_unavailable", "Analyzer workspace 无法创建");
  }
  const workspaceRoot = path.join(resolvedTemporaryRoot, `bytedance-ftf-code-analyzer-${uid}`);
  try {
    fs.mkdirSync(workspaceRoot, { mode: 0o700 });
  } catch (error) {
    if (error?.code !== "EEXIST") {
      fail("dependency_unavailable", "Analyzer workspace 无法创建");
    }
  }
  try {
    const stat = fs.lstatSync(workspaceRoot);
    if (
      !stat.isDirectory() ||
      stat.isSymbolicLink() ||
      stat.uid !== uid ||
      (stat.mode & 0o077) !== 0
    ) {
      fail("dependency_unavailable", "Analyzer workspace 权限或所有者不安全");
    }
    const resolved = fs.realpathSync(workspaceRoot);
    if (resolved !== workspaceRoot) {
      fail("dependency_unavailable", "Analyzer workspace 不能是符号链接");
    }
    return resolved;
  } catch (error) {
    if (error instanceof AdmissionError) {
      throw error;
    }
    fail("dependency_unavailable", "Analyzer workspace 不可用");
  }
}

export function validateHostWorkspaceRoot(inputDirectory) {
  if (typeof inputDirectory !== "string" || !path.isAbsolute(inputDirectory)) {
    fail("dependency_unavailable", "宿主 Analyzer workspace 必须是绝对路径");
  }
  const uid = typeof process.getuid === "function" ? process.getuid() : os.userInfo().uid;
  try {
    const stat = fs.lstatSync(inputDirectory);
    const normalized = path.resolve(inputDirectory);
    const resolved = fs.realpathSync(normalized);
    if (
      !stat.isDirectory() ||
      stat.isSymbolicLink() ||
      stat.uid !== uid ||
      (stat.mode & 0o077) !== 0 ||
      resolved !== normalized
    ) {
      fail("dependency_unavailable", "宿主 Analyzer workspace 权限或所有者不安全");
    }
    return resolved;
  } catch (error) {
    if (error instanceof AdmissionError) {
      throw error;
    }
    fail("dependency_unavailable", "宿主 Analyzer workspace 不可用");
  }
}

export function resolveExecutionContext(environment = process.env) {
  const hostWorkspace = environment.FTF_PREPARED_CONTEXT_DIR;
  const hostTimeout = environment.BYTEDANCE_FTF_WRAPPER_TIMEOUT_SECONDS;
  if (!hostWorkspace) {
    if (hostTimeout !== undefined) {
      fail("dependency_unavailable", "宿主 Analyzer 超时只能与宿主 workspace 一起配置");
    }
    return { workspaceRoot: ensureAnalyzerWorkspaceRoot(), timeoutMs: WRAPPER_TIMEOUT_MS };
  }
  if (hostTimeout !== String(HOST_WRAPPER_TIMEOUT_SECONDS)) {
    fail("dependency_unavailable", "宿主 Analyzer wrapper 超时必须为 450 秒");
  }
  return {
    workspaceRoot: validateHostWorkspaceRoot(hostWorkspace),
    timeoutMs: HOST_WRAPPER_TIMEOUT_SECONDS * 1000,
  };
}

export function buildAnalyzerInvocation({
  runnerPath,
  taskId,
  diffId,
  site,
  vregion,
  network,
  outputPath,
}) {
  const args = [
    runnerPath,
    "run",
    "--task-id",
    taskId,
    "--diff-id",
    diffId,
    "--site",
    site,
    "--vregion",
    vregion,
  ];
  if (network) {
    args.push("--network", network);
  }
  args.push("--timeout-seconds", "300");
  if (outputPath) {
    args.push("--output", outputPath);
  }
  return { command: "python3", args };
}

function parseArguments(argv) {
  const values = {};
  const allowed = new Set([
    "--analyzer-skill-dir",
    "--task-id",
    "--diff-id",
    "--site",
    "--vregion",
    "--network",
  ]);
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!allowed.has(key) || value === undefined || value.startsWith("-")) {
      throw new ArgumentError();
    }
    if (Object.hasOwn(values, key)) {
      throw new ArgumentError();
    }
    values[key] = value;
  }
  if (typeof values["--analyzer-skill-dir"] !== "string") {
    throw new ArgumentError();
  }
  return {
    analyzerSkillDir: values["--analyzer-skill-dir"],
    taskId: requireIdentifier(values["--task-id"]),
    diffId: requireIdentifier(values["--diff-id"]),
    site: values["--site"] ?? "",
    vregion: values["--vregion"] ?? "",
    network: values["--network"] ?? "",
  };
}

export function validateRegion(site, vregion, network) {
  if (!REGION_PAIRS.has(`${site}\0${vregion}`)) {
    fail("unsupported_region", "任务地域缺失、不匹配或不受支持");
  }
  if (network && !["office", "prod"].includes(network)) {
    fail("unsupported_region", "network 不受支持");
  }
}

function targetExists(child) {
  if (!child.pid) {
    return false;
  }
  if (process.platform !== "linux") {
    return child.exitCode === null && child.signalCode === null;
  }
  try {
    process.kill(-child.pid, 0);
    return true;
  } catch (error) {
    if (error?.code === "ESRCH") {
      return false;
    }
    if (error?.code === "EPERM") {
      return true;
    }
    throw error;
  }
}

function signalTarget(child, signal) {
  if (!child.pid) {
    return false;
  }
  try {
    process.kill(process.platform === "linux" ? -child.pid : child.pid, signal);
    return true;
  } catch (error) {
    if (error?.code === "ESRCH") {
      return false;
    }
    throw error;
  }
}

async function waitForTargetExit(child, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (targetExists(child) && Date.now() < deadline) {
    await new Promise((resolve) => {
      setTimeout(resolve, Math.min(PROCESS_EXIT_POLL_MS, Math.max(1, deadline - Date.now())));
    });
  }
  return !targetExists(child);
}

export async function terminateProcessGroup(child) {
  if (!targetExists(child)) {
    return true;
  }
  signalTarget(child, "SIGTERM");
  if (await waitForTargetExit(child, TERMINATION_GRACE_MS)) {
    return true;
  }
  signalTarget(child, "SIGKILL");
  return waitForTargetExit(child, FORCE_KILL_WAIT_MS);
}

function appendTail(current, chunk) {
  const bytes = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
  if (bytes.length >= STDERR_TAIL_BYTES) {
    return Buffer.from(bytes.subarray(bytes.length - STDERR_TAIL_BYTES));
  }
  const keep = Math.max(0, STDERR_TAIL_BYTES - bytes.length);
  return Buffer.concat([current.subarray(Math.max(0, current.length - keep)), bytes]);
}

function truncateUtf8(buffer, maxBytes) {
  for (let end = Math.min(buffer.length, maxBytes); end >= 0; end -= 1) {
    const value = new TextDecoder("utf-8").decode(buffer.subarray(0, end));
    if (Buffer.byteLength(value) <= maxBytes) {
      return value;
    }
  }
  return "";
}

function sanitizeStderr(stderrBuffer, truncated) {
  let value = new TextDecoder("utf-8").decode(stderrBuffer);
  if (truncated) {
    const lineBoundary = value.match(/\r\n|[\r\n]/u);
    value = lineBoundary ? value.slice(lineBoundary.index + lineBoundary[0].length) : "";
  }
  const ansiPattern = new RegExp("\\x1B\\[[0-?]*[ -/]*[@-~]", "gu");
  value = value.replace(ansiPattern, "");
  value = Array.from(value, (character) => {
    const codePoint = character.codePointAt(0);
    return codePoint === 9 || codePoint === 10 || codePoint === 13 || codePoint >= 32
      ? character
      : " ";
  }).join("");
  value = value
    .replace(
      /\b(authorization|proxy-authorization|cookie|set-cookie)\s*[:=]\s*[^\r\n]*/giu,
      "$1: <REDACTED>",
    )
    .replace(/\bbearer\s+[A-Za-z0-9._~+/=-]{8,}/giu, "Bearer <REDACTED>")
    .replace(/\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b/gu, "<REDACTED>")
    .replace(
      /([?&](?:access[_-]?token|refresh[_-]?token|token|signature|secret|x-amz-signature)=)[^&#\s]+/giu,
      "$1<REDACTED>",
    )
    .replace(
      /\b(api[_-]?key|access[_-]?token|refresh[_-]?token|token|signature|secret)\s*[:=]\s*[^\s,;]+/giu,
      "$1=<REDACTED>",
    )
    .trim();
  const sanitized = Buffer.from(value);
  if (sanitized.length <= STDERR_TAIL_BYTES) {
    return value;
  }
  return truncateUtf8(sanitized, STDERR_TAIL_BYTES);
}

function writeChildDiagnostic(summary, { stderrTail, cleanupFailed }) {
  const details = [summary, stderrTail, cleanupFailed ? "Analyzer 进程清理未确认完成" : ""]
    .filter(Boolean)
    .join("\n");
  process.stderr.write(`run-code-analyzer: ${details}\n`);
}

export async function runChild(invocation, workspaceRoot, { timeoutMs = WRAPPER_TIMEOUT_MS } = {}) {
  const temporaryDirectory = fs.mkdtempSync(
    path.join(os.tmpdir(), "bytedance-ftf-analyzer-stdout-"),
  );
  fs.chmodSync(temporaryDirectory, 0o700);
  const stdoutPath = path.join(temporaryDirectory, "stdout.json");
  const stdoutFd = fs.openSync(
    stdoutPath,
    fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL,
    0o600,
  );
  let child;
  let terminalCause = null;
  let spawnError = null;
  let stderrTail = Buffer.alloc(0);
  let stderrTruncated = false;
  let cleanupFailed = false;
  let cleanupPromise = null;
  let watchdog;
  let resolveTerminal;
  let resolveChildClosed;
  const terminalPromise = new Promise((resolve) => {
    resolveTerminal = resolve;
  });
  const childClosedPromise = new Promise((resolve) => {
    resolveChildClosed = resolve;
  });
  const finish = (cause, terminal, { cleanup = false } = {}) => {
    if (terminalCause !== null) {
      return;
    }
    terminalCause = cause;
    clearTimeout(watchdog);
    if (!cleanup || !child) {
      resolveTerminal(terminal);
      return;
    }
    cleanupPromise ??= terminateProcessGroup(child)
      .then((cleaned) => {
        cleanupFailed = !cleaned;
      })
      .catch(() => {
        cleanupFailed = true;
      });
    resolveTerminal(terminal);
  };
  const signalHandler = () =>
    finish(
      "interrupted",
      { code: child?.exitCode ?? null, signal: child?.signalCode ?? null },
      {
        cleanup: true,
      },
    );
  try {
    child = spawn(invocation.command, invocation.args, {
      detached: process.platform === "linux",
      env: { ...process.env, FTF_PREPARED_CONTEXT_DIR: workspaceRoot },
      shell: false,
      stdio: ["ignore", stdoutFd, "pipe"],
    });
    child.stderr.on("data", (chunk) => {
      stderrTruncated ||= stderrTail.length + chunk.length > STDERR_TAIL_BYTES;
      stderrTail = appendTail(stderrTail, chunk);
    });
    process.on("SIGINT", signalHandler);
    process.on("SIGTERM", signalHandler);
    child.once("error", (error) => {
      spawnError = error;
      finish("spawn_error", { code: null, signal: null }, { cleanup: true });
    });
    child.once("exit", (code, signal) => {
      if (code !== 0 || signal !== null) {
        finish("child_failed", { code, signal }, { cleanup: true });
      }
    });
    child.once("close", (code, signal) => {
      resolveChildClosed();
      const abnormal = code !== 0 || signal !== null;
      finish(abnormal ? "child_failed" : "closed", { code, signal }, { cleanup: abnormal });
    });
    watchdog = setTimeout(() => {
      finish("timeout", { code: null, signal: null }, { cleanup: true });
    }, timeoutMs);
    const terminal = await terminalPromise;
    let closeWaitTimer;
    try {
      await Promise.all([
        cleanupPromise,
        Promise.race([
          childClosedPromise,
          new Promise((resolve) => {
            closeWaitTimer = setTimeout(resolve, FORCE_KILL_WAIT_MS);
          }),
        ]),
      ]);
    } finally {
      clearTimeout(closeWaitTimer);
    }
    // 在读取正文前检查文件大小，避免超限 stdout 进入进程内存。
    const stdoutTooLarge = fs.fstatSync(stdoutFd).size > MAX_STDOUT_BYTES;
    fs.closeSync(stdoutFd);
    const stdoutBuffer = stdoutTooLarge ? Buffer.alloc(0) : fs.readFileSync(stdoutPath);
    return {
      exitCode: terminal.code,
      interrupted: terminalCause === "interrupted" || terminal.signal !== null,
      timedOut: terminalCause === "timeout",
      stdoutTooLarge,
      stdoutBuffer,
      spawnError,
      stderrTail: sanitizeStderr(stderrTail, stderrTruncated),
      cleanupFailed,
    };
  } finally {
    clearTimeout(watchdog);
    process.removeListener("SIGINT", signalHandler);
    process.removeListener("SIGTERM", signalHandler);
    child?.stderr?.destroy();
    if (cleanupFailed) {
      child?.unref();
    }
    try {
      fs.closeSync(stdoutFd);
    } catch {}
    fs.rmSync(temporaryDirectory, { recursive: true, force: true });
  }
}

export async function runCanonicalAnalyzer(options) {
  const { taskId, diffId, site, vregion, network, analyzerSkillDir } = options;
  try {
    validateRegion(site, vregion, network);
    const { runnerPath } = resolveAnalyzerSkillDirectory(analyzerSkillDir);
    const { workspaceRoot, timeoutMs } = resolveExecutionContext();
    const outputPath = process.env.FTF_PREPARED_CONTEXT_DIR
      ? path.join(expectedArtifactDirectory(workspaceRoot, taskId, diffId), "result.json")
      : undefined;
    const invocation = buildAnalyzerInvocation({
      runnerPath,
      taskId,
      diffId,
      site,
      vregion,
      network,
      outputPath,
    });
    const terminal = await runChild(invocation, workspaceRoot, { timeoutMs });
    if (terminal.spawnError) {
      const category =
        terminal.spawnError.code === "ENOENT" ? "dependency_unavailable" : "runner_failed";
      writeChildDiagnostic("Analyzer 进程无法启动", terminal);
      return reject(category, "Analyzer 进程无法启动", diffId);
    }
    if (terminal.timedOut) {
      writeChildDiagnostic("Analyzer wrapper 执行超时", terminal);
    } else if (terminal.interrupted || terminal.exitCode === null) {
      writeChildDiagnostic("Analyzer 执行被中断", terminal);
    } else if (terminal.stdoutTooLarge) {
      writeChildDiagnostic("Analyzer stdout 超过 64 KiB 上限", terminal);
    } else if (terminal.exitCode !== 0) {
      writeChildDiagnostic("Analyzer standard run 执行失败", terminal);
    }
    return adaptCanonicalAnalyzerResult({
      requestIdentity: { taskId, diffId },
      analyzerWorkspaceRoot: workspaceRoot,
      exitCode: terminal.exitCode,
      interrupted: terminal.interrupted,
      timedOut: terminal.timedOut,
      stdoutTooLarge: terminal.stdoutTooLarge,
      stdoutBuffer: terminal.stdoutBuffer,
    });
  } catch (error) {
    if (error instanceof AdmissionError) {
      return reject(error.category, error.message, diffId);
    }
    throw error;
  }
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const result = await runCanonicalAnalyzer(options);
  process.stdout.write(`${JSON.stringify(result)}\n`);
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
    process.stderr.write(
      error instanceof ArgumentError
        ? "run-code-analyzer: invalid arguments\n"
        : "run-code-analyzer: unexpected failure\n",
    );
    process.exitCode = 1;
  });
}
