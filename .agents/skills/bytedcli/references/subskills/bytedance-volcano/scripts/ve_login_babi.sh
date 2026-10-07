#!/usr/bin/env bash
# 使用 bytedcli 缓存的 Babi 火山控制台登录态，自动批准 `ve login` 设备码请求。

set -euo pipefail

min_ve_version="1.1.5"
region="${VOLCENGINE_REGION:-cn-beijing}"
profile=""
volc_account_id=""
approval_timeout="${VE_LOGIN_APPROVAL_TIMEOUT:-60}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
remote_helper="${VE_LOGIN_REMOTE_HELPER:-${script_dir}/ve_login_remote.sh}"

usage() {
  local status="${1:-2}"
  cat <<'USAGE' >&2
用法：
  ve_login_babi.sh --profile <babi-name> [--region <region>] [--volc-account-id <account-id>]

默认地域为 VOLCENGINE_REGION，未设置时使用 cn-beijing。
--profile 必须是 `bytedcli volcano auth list-accounts` 返回的 Babi 账号名称；
登录成功后脚本会把该 ve profile 切换为当前生效 profile。
--volc-account-id 选择 Babi 火山账号。
未传 --volc-account-id 时，使用 `bytedcli volcano auth config` 保存的默认账号。
USAGE
  exit "$status"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --region)
      [[ $# -ge 2 ]] || usage
      region="$2"
      shift 2
      ;;
    --profile)
      [[ $# -ge 2 ]] || usage
      profile="$2"
      shift 2
      ;;
    --volc-account-id)
      [[ $# -ge 2 ]] || usage
      volc_account_id="$2"
      shift 2
      ;;
    -h|--help)
      usage 0
      ;;
    *)
      echo "错误：未知参数 $1" >&2
      usage
      ;;
  esac
done

if [[ -z "$profile" ]]; then
  echo "错误：必须通过 --profile 传入 Babi 火山账号名称。" >&2
  usage
fi
if [[ "$profile" == *$'\n'* || "$profile" == *$'\r'* || "$profile" == *$'\t'* ]]; then
  echo "错误：--profile 不能包含控制字符。" >&2
  exit 2
fi

version_at_least() {
  local actual="${1#v}" required="${2#v}"
  local actual_core="${actual%%[-+]*}" required_core="${required%%[-+]*}"
  local a_major a_minor a_patch r_major r_minor r_patch
  IFS=. read -r a_major a_minor a_patch <<<"$actual_core"
  IFS=. read -r r_major r_minor r_patch <<<"$required_core"
  for part in "$a_major" "$a_minor" "$a_patch" "$r_major" "$r_minor" "$r_patch"; do
    [[ "$part" =~ ^[0-9]+$ ]] || return 1
  done
  (( a_major > r_major )) && return 0
  (( a_major < r_major )) && return 1
  (( a_minor > r_minor )) && return 0
  (( a_minor < r_minor )) && return 1
  (( a_patch >= r_patch ))
}

if ! command -v ve >/dev/null 2>&1; then
  echo "错误：找不到 ve；请从 https://registry.npmjs.org 安装 @volcengine/cli，并设置 VOLCENGINE_CLI_SKIP_SKILLS=1。" >&2
  exit 4
fi
if ! command -v bytedcli >/dev/null 2>&1; then
  echo "错误：找不到 bytedcli，无法复用 Babi 火山控制台登录态。" >&2
  exit 4
fi
if [[ ! -x "$remote_helper" ]]; then
  echo "错误：登录辅助脚本不可执行：$remote_helper" >&2
  exit 4
fi

ve_version="$(ve version 2>/dev/null | awk 'NF { print $NF; exit }')"
if [[ -z "$ve_version" ]]; then
  ve_version="$(ve --version 2>/dev/null | awk 'NF { print $NF; exit }')"
fi
if ! version_at_least "$ve_version" "$min_ve_version"; then
  echo "错误：ve 版本必须不低于 ${min_ve_version}，当前为 ${ve_version:-unknown}。" >&2
  exit 4
fi
login_help="$(ve login --help 2>&1 || true)"
if ! grep -q -- '--no-browser' <<<"$login_help"; then
  echo "错误：当前 ve 不支持 --no-browser；请升级到 ${min_ve_version} 或更高版本。" >&2
  exit 4
fi

embedded_dist_is_valid() {
  local candidate="$1"
  [[ -f "$candidate/auth/volcano_session.js" ]] &&
    [[ -f "$candidate/auth/volcano_credentials.js" ]]
}

resolve_embedded_dist() {
  local bytedcli_path bytedcli_real bytedcli_bin_dir candidate
  bytedcli_dist=""
  command -v node >/dev/null 2>&1 || return 1

  if [[ -n "${VE_LOGIN_BYTEDCLI_DIST:-}" ]]; then
    if embedded_dist_is_valid "$VE_LOGIN_BYTEDCLI_DIST"; then
      bytedcli_dist="$VE_LOGIN_BYTEDCLI_DIST"
      return 0
    fi
    return 1
  fi

  bytedcli_path="$(command -v bytedcli)"
  if bytedcli_real="$(node -e 'process.stdout.write(require("node:fs").realpathSync(process.argv[1]))' "$bytedcli_path" 2>/dev/null)"; then
    candidate="$(dirname "$bytedcli_real")"
    if embedded_dist_is_valid "$candidate"; then
      bytedcli_dist="$candidate"
      return 0
    fi
  fi

  # Standalone bytedcli upgrades preserve the previous npm installation under
  # the sibling .local/lib tree. Reuse those modules for the embedded fallback.
  bytedcli_bin_dir="$(dirname "$bytedcli_path")"
  candidate="${bytedcli_bin_dir}/../lib/node_modules/@bytedance-dev/bytedcli/dist"
  if embedded_dist_is_valid "$candidate"; then
    bytedcli_dist="$candidate"
    return 0
  fi
  return 1
}

approve_mode="bytedcli"
bytedcli_dist=""
approve_help="$(bytedcli --no-auto-upgrade volcano auth approve-device --help 2>&1 || true)"
if ! grep -q -- '--trace-id' <<<"$approve_help"; then
  approve_mode="embedded"
  if ! resolve_embedded_dist; then
    echo "错误：当前 bytedcli 不支持 volcano auth approve-device，且不具备兼容登录模块；请升级 bytedcli。" >&2
    exit 4
  fi
fi
if ! [[ "$approval_timeout" =~ ^[0-9]+$ ]] || (( approval_timeout < 1 || approval_timeout > 300 )); then
  echo "错误：VE_LOGIN_APPROVAL_TIMEOUT 必须是 1 到 300 之间的整数秒数。" >&2
  exit 2
fi

abort_login() {
  "$remote_helper" abort >/dev/null 2>&1 || true
}
trap 'abort_login; exit 130' HUP INT TERM

activate_profile() {
  local output
  if ! output="$(ve configure profile --profile "$profile" 2>&1)"; then
    printf '%s\n' "$output" >&2
    echo "错误：Babi 登录已写入 ve profile ${profile}，但未能将它切换为当前 profile。" >&2
    exit 7
  fi
  if [[ -n "$output" ]]; then
    printf '%s\n' "$output"
  fi
  return 0
}

start_args=(start "$region")
[[ -n "$profile" ]] && start_args+=("$profile")
set +e
login_block="$($remote_helper "${start_args[@]}" 2>&1)"
start_status=$?
set -e
if (( start_status != 0 )); then
  printf '%s\n' "$login_block" >&2
  abort_login
  exit "$start_status"
fi

url="$(printf '%s\n' "$login_block" | sed -n 's/^URL=//p' | head -1)"
if [[ -z "$url" ]]; then
  set +e
  login_block="$($remote_helper url 2>&1)"
  url_status=$?
  set -e
  if (( url_status != 0 )); then
    printf '%s\n' "$login_block" >&2
    abort_login
    exit "$url_status"
  fi
  url="$(printf '%s\n' "$login_block" | sed -n 's/^URL=//p' | head -1)"
fi
trace_id="$(printf '%s\n' "$url" | sed -n 's/.*[?&]trace_id=\([^&[:space:]]*\).*/\1/p')"
if [[ -z "$trace_id" ]] || ! [[ "$trace_id" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo "错误：ve 登录 URL 中没有合法的 trace_id。" >&2
  abort_login
  exit 5
fi
user_code="$(printf '%s\n' "$login_block" | sed -n 's/^CODE=//p' | head -1)"
if [[ -z "$user_code" ]] || ! [[ "$user_code" =~ ^[a-zA-Z0-9]+-[a-zA-Z0-9]+$ ]]; then
  echo "错误：ve 登录输出中没有合法的设备码。" >&2
  abort_login
  exit 5
fi

approve_ok="false"
if [[ "$approve_mode" == "bytedcli" ]]; then
  approve_args=(--no-auto-upgrade volcano auth approve-device --trace-id "$trace_id")
  # Older bytedcli only accepts TraceId; preserve its embedded CSRF fallback.
  if grep -q -- '--user-code' <<<"$approve_help"; then
    approve_args+=(--user-code "$user_code")
  fi
  [[ -n "$volc_account_id" ]] && approve_args+=(--volc-account-id "$volc_account_id")
  approve_args+=(--yes)
  set +e
  approve_output="$(bytedcli "${approve_args[@]}" 2>&1)"
  approve_status=$?
  set -e
  if (( approve_status == 0 )); then
    [[ -z "$approve_output" ]] || printf '%s\n' "$approve_output"
    approve_ok="true"
  else
    [[ -z "$approve_output" ]] || printf '%s\n' "$approve_output" >&2
    if grep -q 'InvalidCSRFToken' <<<"$approve_output"; then
      if resolve_embedded_dist; then
        echo "提示：approve-device 的 CSRF 校验失败，改用 embedded 兼容路径重试一次。" >&2
        approve_mode="embedded"
      else
        echo "错误：approve-device 的 CSRF 校验失败，且本机没有可用的 embedded 兼容模块。" >&2
      fi
    fi
  fi
fi
if [[ "$approve_ok" != "true" && "$approve_mode" == "embedded" ]]; then
  if VE_DEVICE_TRACE_ID="$trace_id" \
     VE_DEVICE_USER_CODE="$user_code" \
     VE_DEVICE_LOGIN_URL="$url" \
     VE_DEVICE_VOLC_ACCOUNT_ID="$volc_account_id" \
     VE_DEVICE_BYTEDCLI_DIST="$bytedcli_dist" \
     node <<'NODE'
"use strict";

const path = require("node:path");

const traceId = process.env.VE_DEVICE_TRACE_ID || "";
const userCode = process.env.VE_DEVICE_USER_CODE || "";
const loginUrl = process.env.VE_DEVICE_LOGIN_URL || "";
const bytedcliDist = process.env.VE_DEVICE_BYTEDCLI_DIST || "";
let accountId = process.env.VE_DEVICE_VOLC_ACCOUNT_ID || "";

function fail(message, code = 6) {
  process.stderr.write(`错误：${message}\n`);
  process.exit(code);
}

if (!/^[a-zA-Z0-9_-]+$/.test(traceId)) fail("非法 trace_id", 2);
if (!/^[a-zA-Z0-9]+-[a-zA-Z0-9]+$/.test(userCode)) fail("非法设备码", 2);

let authorizationUrl;
try {
  authorizationUrl = new URL(loginUrl);
} catch {
  fail("设备授权链接格式无效", 3);
}
if (
  authorizationUrl.protocol !== "https:" ||
  authorizationUrl.hostname !== "signin.volcengine.com" ||
  authorizationUrl.pathname !== "/authorize/oauth/device" ||
  authorizationUrl.searchParams.get("trace_id") !== traceId
) {
  fail("设备授权链接与 trace_id 不匹配", 3);
}

let getOrCreateVolcanoSession;
try {
  ({ getOrCreateVolcanoSession } = require(
    path.join(bytedcliDist, "auth/volcano_session.js"),
  ));
  if (!accountId) {
    const { VolcanoCredentialsStorage } = require(
      path.join(bytedcliDist, "auth/volcano_credentials.js"),
    );
    accountId = new VolcanoCredentialsStorage().get()?.volcAccountId || "";
  }
} catch {
  fail("无法加载 bytedcli 火山登录模块", 4);
}
if (!/^\d+$/.test(accountId)) fail("未配置合法的火山账号 ID", 2);

function generateAuthSign(timestamp) {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let salt = "";
  for (let index = 0; index < 16; index += 1) {
    salt += chars[Math.floor(chars.length * Math.random())];
  }
  const reverse = (value) => value.split("").reverse().join("");
  const merged =
    `radomSalt=${encodeURIComponent(salt)}` +
    `&timeStamp=${encodeURIComponent(reverse(String(timestamp)))}`;
  const sign = reverse(Buffer.from(merged).toString("base64"));
  const content = JSON.stringify({ radomSalt: salt, timeStamp: timestamp });
  return `content=${encodeURIComponent(content)}&sign=${encodeURIComponent(sign)}`;
}

(async () => {
  const session = await getOrCreateVolcanoSession(accountId);
  let sessionConsoleUrl;
  try {
    sessionConsoleUrl = new URL(session.consoleHost || "");
  } catch {
    fail("Babi 火山登录态缺少可信的控制台域名");
  }
  if (
    sessionConsoleUrl.protocol !== "https:" ||
    sessionConsoleUrl.hostname !== "console.volcengine.com"
  ) {
    fail("仅支持使用 console.volcengine.com 的 Babi 火山登录态批准设备码");
  }
  const cookies = new Map(Object.entries(session.cookies || {}));
  if (cookies.size === 0) fail("火山登录态 Cookie 为空");
  const authorizationTimestamp = Date.now();

  const cookieHeader = () =>
    [...cookies.entries()].map(([name, value]) => `${name}=${value}`).join("; ");

  function collectCookies(response) {
    const values = response.headers.getSetCookie?.() || [];
    for (const value of values) {
      const first = value.split(";", 1)[0];
      const separator = first.indexOf("=");
      if (separator > 0) {
        cookies.set(first.slice(0, separator).trim(), first.slice(separator + 1).trim());
      }
    }
  }

  async function post(action, body) {
    const response = await fetch(
      `https://signin.volcengine.com/api/passport/sso/${action}`,
      {
        method: "POST",
        headers: {
          accept: "application/json",
          "accept-language": "zh",
          connection: "keep-alive",
          "content-type": "application/json",
          cookie: cookieHeader(),
          origin: "https://signin.volcengine.com",
          referer: authorizationUrl.href,
          "sec-fetch-dest": "empty",
          "sec-fetch-mode": "cors",
          "sec-fetch-site": "same-origin",
          "user-agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " +
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
          "x-authentication-sign": generateAuthSign(authorizationTimestamp),
          "sec-ch-ua":
            '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
          "sec-ch-ua-mobile": "?0",
          "sec-ch-ua-platform": '"macOS"',
          ...(cookies.get("csrfToken")
            ? { "x-csrf-token": cookies.get("csrfToken") }
            : {}),
        },
        body: JSON.stringify(body),
        redirect: "manual",
      },
    );
    collectCookies(response);
    const text = await response.text();
    let payload = {};
    try {
      payload = text ? JSON.parse(text) : {};
    } catch {
      // HTTP status remains authoritative for non-JSON responses.
    }
    if (response.status < 200 || response.status >= 300) {
      throw new Error(`${action} 返回 HTTP ${response.status}`);
    }
    const metadata = payload.ResponseMetadata || {};
    if (metadata.Error) {
      throw new Error(
        `${action} 失败：${metadata.Error.Message || metadata.Error.Code || "未知业务错误"}`,
      );
    }
    if (typeof metadata.Code === "number" && metadata.Code !== 0) {
      throw new Error(`${action} 失败：${metadata.Message || metadata.Code}`);
    }
  }

  await post("submitUserCode", { TraceId: traceId, UserCode: userCode });
  await post("confirmDeviceAuthorization", { TraceId: traceId, Approved: true });
  process.stdout.write("设备码已确认授权\n");
})().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  fail(message);
});
NODE
  then
    approve_ok="true"
  fi
fi
if [[ "$approve_ok" != "true" ]]; then
  echo "错误：Babi 火山会话未能批准 ve 设备码登录。" >&2
  abort_login
  exit 6
fi

deadline=$((SECONDS + approval_timeout))
while (( SECONDS < deadline )); do
  verify_args=(verify)
  [[ -n "$profile" ]] && verify_args+=("$profile")
  set +e
  verify_output="$($remote_helper "${verify_args[@]}" 2>&1)"
  verify_status=$?
  set -e
  case "$verify_status" in
    0)
      printf '%s\n' "$verify_output"
      activate_profile
      trap - HUP INT TERM
      exit 0
      ;;
    11)
      sleep 1
      ;;
    13)
      printf '%s\n' "$verify_output" >&2
      activate_profile
      trap - HUP INT TERM
      exit 13
      ;;
    *)
      printf '%s\n' "$verify_output" >&2
      abort_login
      exit "$verify_status"
      ;;
  esac
done

echo "错误：设备码已批准，但 ve 未在 ${approval_timeout} 秒内完成登录。" >&2
abort_login
exit 10
