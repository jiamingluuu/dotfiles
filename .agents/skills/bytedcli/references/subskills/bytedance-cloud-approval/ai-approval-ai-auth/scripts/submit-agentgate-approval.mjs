#!/usr/bin/env node

import fs from "node:fs";
import https from "node:https";
import { pathToFileURL } from "node:url";

const AGENTGATE_SUBMIT_URL = new URL(
  "https://cloud.bytedance.net/api/v1/agentgate/openapi/v1/approval/strategy/submit",
);
const MAX_INPUT_BYTES = 64 * 1024;
const MAX_RESPONSE_BYTES = 1024 * 1024;
const REQUEST_TIMEOUT_MS = 20_000;

class PublicError extends Error {
  constructor(message, exitCode) {
    super(message);
    this.name = "PublicError";
    this.exitCode = exitCode;
  }
}

function requireObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new PublicError(`${label} must be a JSON object`, 2);
  }
  return value;
}

function requireString(value, label, maxLength) {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > maxLength
  ) {
    throw new PublicError(
      `${label} must be a non-empty string up to ${maxLength} characters`,
      2,
    );
  }
  if (/\p{Cc}/u.test(value)) {
    throw new PublicError(`${label} must not contain control characters`, 2);
  }
  return value;
}

function requireSingleQueryParam(url, name, maxLength) {
  const values = url.searchParams.getAll(name);
  if (values.length !== 1) {
    throw new PublicError(`RecoveryURL must contain exactly one ${name}`, 2);
  }
  return requireString(values[0], `RecoveryURL ${name}`, maxLength);
}

export function parseRecoveryURL(rawURL) {
  const value = requireString(rawURL, "RecoveryURL", 4096);
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new PublicError("RecoveryURL is not a valid URL", 2);
  }

  if (
    url.protocol !== "https:" ||
    url.hostname !== "cloud.bytedance.net" ||
    url.port !== "" ||
    url.username !== "" ||
    url.password !== "" ||
    url.pathname !== "/open/explorer/ai-policy/apply"
  ) {
    throw new PublicError(
      "RecoveryURL is outside the trusted AgentGate apply origin",
      2,
    );
  }

  const type = requireSingleQueryParam(url, "type", 32);
  if (type !== "openapi") {
    throw new PublicError("RecoveryURL type must be openapi", 2);
  }

  const strategyIDText = requireSingleQueryParam(url, "strategy_id", 16);
  if (!/^[1-9][0-9]{0,15}$/u.test(strategyIDText)) {
    throw new PublicError(
      "RecoveryURL strategy_id must be a positive integer",
      2,
    );
  }
  const strategyID = Number(strategyIDText);
  if (!Number.isSafeInteger(strategyID)) {
    throw new PublicError(
      "RecoveryURL strategy_id exceeds the safe integer range",
      2,
    );
  }

  return {
    strategyID,
    accountID: requireSingleQueryParam(url, "account_id", 256),
    apiID: requireSingleQueryParam(url, "api_id", 256),
  };
}

function requireInteger(value, label) {
  if (!Number.isSafeInteger(value)) {
    throw new PublicError(`${label} must be an integer`, 2);
  }
  return value;
}

export function validateSubmissionInput(rawInput) {
  const input = requireObject(rawInput, "input");
  const allowedKeys = new Set([
    "RecoveryURL",
    "Username",
    "EscapeType",
    "EscapeTime",
    "EscapeCount",
    "Reason",
  ]);
  for (const key of Object.keys(input)) {
    if (!allowedKeys.has(key)) {
      throw new PublicError(`input contains unsupported field ${key}`, 2);
    }
  }

  const { strategyID, accountID, apiID } = parseRecoveryURL(input.RecoveryURL);
  const username = requireString(input.Username, "Username", 128);
  if (!/^[A-Za-z0-9._-]+$/u.test(username)) {
    throw new PublicError("Username contains unsupported characters", 2);
  }
  const reason = requireString(input.Reason, "Reason", 2000);
  const escapeType = requireString(input.EscapeType, "EscapeType", 32);

  const body = {
    AccountID: accountID,
    Username: username,
    APIID: apiID,
    StrategyID: strategyID,
    EscapeType: escapeType,
    Reason: reason,
  };

  if (escapeType === "escape_duration") {
    const escapeTime = requireInteger(input.EscapeTime, "EscapeTime");
    if (escapeTime !== -1 && (escapeTime < 1 || escapeTime > 525_600)) {
      throw new PublicError(
        "EscapeTime must be -1 or between 1 and 525600 minutes",
        2,
      );
    }
    if (input.EscapeCount !== undefined) {
      throw new PublicError(
        "EscapeCount must be omitted for escape_duration",
        2,
      );
    }
    return { ...body, EscapeTime: escapeTime, EscapeStartTime: 0 };
  }

  if (escapeType === "escape_count") {
    const escapeCount = requireInteger(input.EscapeCount, "EscapeCount");
    if (escapeCount < 1 || escapeCount > 1_000_000) {
      throw new PublicError("EscapeCount must be between 1 and 1000000", 2);
    }
    if (input.EscapeTime !== undefined) {
      throw new PublicError("EscapeTime must be omitted for escape_count", 2);
    }
    return { ...body, EscapeCount: escapeCount };
  }

  throw new PublicError(
    "EscapeType must be escape_duration or escape_count",
    2,
  );
}

function readBoundedFile(file, maxBytes) {
  const chunks = [];
  let total = 0;
  while (true) {
    const buffer = Buffer.allocUnsafe(Math.min(8192, maxBytes + 1 - total));
    const bytesRead = fs.readSync(file, buffer, 0, buffer.length, null);
    if (bytesRead === 0) break;
    total += bytesRead;
    if (total > maxBytes) {
      throw new PublicError(`input file exceeds ${maxBytes} bytes`, 2);
    }
    chunks.push(buffer.subarray(0, bytesRead));
  }
  return Buffer.concat(chunks).toString("utf8");
}

function consumeOpenedInput(inputPath, openedStat) {
  let currentStat;
  try {
    currentStat = fs.lstatSync(inputPath);
  } catch {
    throw new PublicError(
      "input file disappeared before it could be consumed",
      2,
    );
  }
  if (
    currentStat.isSymbolicLink() ||
    !currentStat.isFile() ||
    currentStat.dev !== openedStat.dev ||
    currentStat.ino !== openedStat.ino
  ) {
    throw new PublicError(
      "input file changed during validation; refusing to submit",
      2,
    );
  }
  fs.unlinkSync(inputPath);
}

export function readPrivateInputFile(inputPath, { consume = false } = {}) {
  let file;
  let openedStat;
  let result;
  let pendingError;
  let validatedForConsumption = false;
  try {
    file = fs.openSync(
      inputPath,
      fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW,
    );
    openedStat = fs.fstatSync(file);
    if (!openedStat.isFile()) {
      throw new PublicError("input must be a regular file, not a symlink", 2);
    }
    if ((openedStat.mode & 0o077) !== 0) {
      throw new PublicError("input file permissions must be 0600", 2);
    }
    const source = readBoundedFile(file, MAX_INPUT_BYTES);
    let parsed;
    try {
      parsed = JSON.parse(source);
    } catch {
      throw new PublicError("input file is not valid JSON", 2);
    }
    result = validateSubmissionInput(parsed);
    validatedForConsumption = true;
  } catch (error) {
    pendingError =
      error instanceof PublicError
        ? error
        : new PublicError(
            "input must be a readable regular file, not a symlink",
            2,
          );
  } finally {
    if (
      consume &&
      validatedForConsumption &&
      file !== undefined &&
      openedStat?.isFile()
    ) {
      try {
        consumeOpenedInput(inputPath, openedStat);
      } catch (error) {
        pendingError =
          error instanceof PublicError
            ? error
            : new PublicError("input file could not be consumed safely", 2);
      }
    }
    if (file !== undefined) fs.closeSync(file);
  }
  if (pendingError) throw pendingError;
  return result;
}

export function validateToken(rawToken) {
  const token = rawToken.trim();
  if (
    token.length < 16 ||
    token.length > 64 * 1024 ||
    /\s/u.test(token) ||
    !/^[A-Za-z0-9._~-]+$/u.test(token)
  ) {
    throw new PublicError("ByteCloud JWT input is empty or malformed", 3);
  }
  return token;
}

export function buildRequest(body, token) {
  const payload = JSON.stringify(body);
  return {
    url: AGENTGATE_SUBMIT_URL,
    options: {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "content-length": Buffer.byteLength(payload),
        "x-jwt-token": token,
        "x-bcgw-tenant-id": "bytedance",
        origin: "https://cloud.bytedance.net",
        referer: "https://cloud.bytedance.net/",
      },
    },
    payload,
  };
}

function isPlainObject(value) {
  return Boolean(
    value &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    Object.getPrototypeOf(value) === Object.prototype,
  );
}

function formatBusinessCode(value) {
  if (
    (typeof value === "number" && Number.isSafeInteger(value)) ||
    (typeof value === "string" && /^[A-Za-z0-9_-]{1,32}$/u.test(value))
  ) {
    return String(value);
  }
  return "unknown";
}

export function parseTicketID(value) {
  if (
    typeof value !== "string" ||
    value.length > 128 ||
    !/^[A-Za-z0-9_-]+$/u.test(value)
  ) {
    throw new PublicError(
      "AgentGate response is missing a valid string TicketID",
      4,
    );
  }
  return value;
}

export function submitAgentGate(
  body,
  token,
  transport = https,
  timeoutMs = REQUEST_TIMEOUT_MS,
) {
  const request = buildRequest(body, token);
  return new Promise((resolve, reject) => {
    let settled = false;
    let deadline;
    const finish = (callback, value) => {
      if (settled) return;
      settled = true;
      if (deadline) clearTimeout(deadline);
      callback(value);
    };

    const req = transport.request(request.url, request.options, (response) => {
      const chunks = [];
      let total = 0;
      response.on("data", (chunk) => {
        total += chunk.length;
        if (total > MAX_RESPONSE_BYTES) {
          const error = new PublicError(
            "AgentGate response exceeded the size limit",
            4,
          );
          finish(reject, error);
          response.destroy(error);
          return;
        }
        chunks.push(chunk);
      });
      response.on("error", (error) =>
        finish(
          reject,
          error instanceof PublicError
            ? error
            : new PublicError("AgentGate response failed", 4),
        ),
      );
      response.on("end", () => {
        if (settled) return;
        const responseText = Buffer.concat(chunks).toString("utf8");
        if (
          !response.statusCode ||
          response.statusCode < 200 ||
          response.statusCode >= 300
        ) {
          finish(
            reject,
            new PublicError(
              `AgentGate returned HTTP ${response.statusCode ?? "unknown"}`,
              4,
            ),
          );
          return;
        }
        let decoded;
        try {
          decoded = JSON.parse(responseText);
        } catch {
          finish(reject, new PublicError("AgentGate returned invalid JSON", 4));
          return;
        }
        if (!isPlainObject(decoded) || decoded.Code !== 0) {
          const code = formatBusinessCode(decoded?.Code);
          const message =
            code === "100012"
              ? "AgentGate rejected the request (code 100012): policy expired, duplicate request, or approval configuration missing"
              : `AgentGate rejected the request (code ${code})`;
          finish(reject, new PublicError(message, 4));
          return;
        }
        if (!isPlainObject(decoded.Result)) {
          finish(
            reject,
            new PublicError("AgentGate response is missing Result", 4),
          );
          return;
        }
        let ticketID;
        try {
          ticketID = parseTicketID(decoded.Result.TicketID);
        } catch (error) {
          finish(reject, error);
          return;
        }
        finish(resolve, {
          ticketID,
          ticketURL: `https://cloud.bytedance.net/open/explorer/ai-policy/ticket/${encodeURIComponent(ticketID)}`,
        });
      });
    });
    req.setTimeout(timeoutMs, () => {
      req.destroy(new PublicError("AgentGate request timed out", 4));
    });
    deadline = setTimeout(() => {
      const error = new PublicError(
        "AgentGate request exceeded the total time limit",
        4,
      );
      finish(reject, error);
      req.destroy(error);
    }, timeoutMs);
    deadline.unref?.();
    req.on("error", (error) =>
      finish(
        reject,
        error instanceof PublicError
          ? error
          : new PublicError("AgentGate request failed", 4),
      ),
    );
    req.end(request.payload);
  });
}

async function readTokenFromStdin() {
  const chunks = [];
  let total = 0;
  for await (const chunk of process.stdin) {
    total += chunk.length;
    if (total > 64 * 1024) {
      throw new PublicError("ByteCloud JWT input exceeds the size limit", 3);
    }
    chunks.push(chunk);
  }
  return validateToken(Buffer.concat(chunks).toString("utf8"));
}

function parseArgs(argv) {
  if (
    (argv.length !== 2 && argv.length !== 3) ||
    argv[0] !== "--input" ||
    !argv[1] ||
    (argv.length === 3 && argv[2] !== "--validate-only")
  ) {
    throw new PublicError(
      "usage: submit-agentgate-approval.mjs --input <private-json-file> [--validate-only]",
      2,
    );
  }
  return { inputPath: argv[1], validateOnly: argv[2] === "--validate-only" };
}

export async function main(argv = process.argv.slice(2)) {
  const { inputPath, validateOnly } = parseArgs(argv);
  const body = readPrivateInputFile(inputPath, { consume: !validateOnly });
  if (validateOnly) {
    process.stdout.write(
      `${JSON.stringify({ status: "validated", request: body })}\n`,
    );
    return;
  }
  const token = await readTokenFromStdin();
  const result = await submitAgentGate(body, token);
  process.stdout.write(
    `${JSON.stringify({
      status: "ok",
      ticket_id: result.ticketID,
      ticket_url: result.ticketURL,
      escape_type: body.EscapeType,
      escape_time: body.EscapeTime,
      escape_count: body.EscapeCount,
    })}\n`,
  );
}

const invokedDirectly =
  process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (invokedDirectly) {
  main().catch((error) => {
    const publicError =
      error instanceof PublicError
        ? error
        : new PublicError("AgentGate submission failed unexpectedly", 1);
    process.stderr.write(`${publicError.message}\n`);
    process.exitCode = publicError.exitCode;
  });
}
