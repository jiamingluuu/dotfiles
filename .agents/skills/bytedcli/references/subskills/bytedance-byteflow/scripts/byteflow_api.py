#!/usr/bin/env python3
"""ByteFlow helper for safe query, workflow validation, and guarded writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from byteflow_workflow_validator import explain_workflow, load_workflow, validate_workflow


SITE_ORIGINS = {
    "cn": "https://cloud.bytedance.net",
    "boe": "https://cloud-boe.bytedance.net",
    "i18n": "https://cloud-i18n.bytedance.net",
    "i18n-tt": "https://bc-sg-gw.tiktok-row.net",
    "row": "https://bc-sg-gw.tiktok-row.net",
    "tiktok-row": "https://bc-sg-gw.tiktok-row.net",
    "eu": "https://cloud-eu.tiktok-row.net",
    "us-ttp": "https://cloud.tiktok-usts.net",
}

SENSITIVE_KEY_PARTS = ("token", "secret", "authorization", "cookie", "jwt")
LARGE_DEFINITION_KEYS = {"definition", "definition_str", "state_machine"}
REVISION_NAME_MAX_LEN = 30
CONSOLE_SITE_BY_HOST = {
    "cloud.bytedance.net": "cn",
    "cloud-boe.bytedance.net": "boe",
    "cloud-i18n.bytedance.net": "i18n",
    "cloud.tiktok-row.net": "i18n-tt",
    "cloud-eu.tiktok-row.net": "eu",
    "cloud.tiktok-usts.net": "us-ttp",
}
FIRST_REVISION_RISK_MESSAGE = (
    "online statemachine has no revisions; creating the first revision may change how production "
    "execution/release paths resolve this workflow. Ask the user for explicit consent before "
    "continuing, then rerun with --allow-first-revision-risk."
)
NO_REVISION_UPDATE_RISK_MESSAGE = (
    "online statemachine has no revisions; updating its definition before the first revision may "
    "change what later production execution/release paths snapshot. Ask the user for explicit "
    "consent before continuing, then rerun with --allow-first-revision-risk."
)


def json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def redact_json_string(value: str) -> str:
    stripped = value.strip()
    if not stripped.startswith(("{", "[")):
        return value
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    redacted = redact(parsed)
    if redacted == parsed:
        return value
    return json.dumps(redacted, ensure_ascii=False)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            lower = str(key).lower()
            if any(part in lower for part in SENSITIVE_KEY_PARTS):
                result[key] = "[REDACTED]"
            else:
                result[key] = redact(item)
        return result
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return redact_json_string(value)
    return value


def shrink_large_fields(value: Any, include_definition: bool = False) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in LARGE_DEFINITION_KEYS and not include_definition:
                if isinstance(item, str):
                    result[key] = f"[OMITTED: {len(item)} chars; pass --include-definition to print]"
                else:
                    result[key] = "[OMITTED: pass --include-definition to print]"
            else:
                result[key] = shrink_large_fields(item, include_definition)
        return result
    if isinstance(value, list):
        return [shrink_large_fields(item, include_definition) for item in value]
    return value


def safe_payload(value: Any, include_definition: bool = False) -> Any:
    return redact(shrink_large_fields(value, include_definition))


def auth_site_for_helper_site(site: str) -> str:
    """Return the bytedcli auth site that matches a ByteFlow helper site."""
    if site in {"i18n-tt", "row", "tiktok-row"}:
        return "i18n-tt"
    if site == "eu":
        return "eu-ttp"
    return site


def bytecloud_jwt(site: str) -> str:
    """Fetch a ByteCloud JWT from bytedcli for the helper's target site."""
    auth_site = auth_site_for_helper_site(site)
    try:
        token = subprocess.check_output(
            ["bytedcli", "--site", auth_site, "auth", "get-bytecloud-jwt-token"],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"failed to get ByteCloud JWT via bytedcli: {exc}") from exc
    if not token:
        raise SystemExit("bytedcli returned an empty ByteCloud JWT")
    return token


def api_base(site: str) -> str:
    origin = SITE_ORIGINS.get(site)
    if not origin:
        raise SystemExit(f"unsupported site {site!r}; choose one of {', '.join(SITE_ORIGINS)}")
    return f"{origin}/api/v1/byteflow/api/v1"


def region_params(args: argparse.Namespace) -> dict[str, str]:
    return {
        "x-resource-account": args.resource_account,
        "x-bc-region-id": args.region_id,
    }


def build_url(base: str, path: str, query: dict[str, Any] | None = None) -> str:
    url = f"{base}{path}"
    params: list[tuple[str, str]] = []
    for key, value in (query or {}).items():
        if value is None:
            continue
        if isinstance(value, bool):
            params.append((key, "true" if value else "false"))
        else:
            params.append((key, str(value)))
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    return url


def quote_path(value: Any) -> str:
    return urllib.parse.quote(str(value), safe="")


def pagination_query(args: argparse.Namespace, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    query: dict[str, Any] = {
        "page_no": args.page_no,
        "page_size": args.page_size,
    }
    for key, value in (extra or {}).items():
        if value == "":
            continue
        query[key] = value
    return query


def load_json_payload(path: str) -> Any:
    try:
        if path == "-":
            raw = sys.stdin.read()
        else:
            with open(path, encoding="utf-8") as handle:
                raw = handle.read()
    except OSError as exc:
        raise SystemExit(f"failed to read JSON payload file {path!r}: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON payload file {path!r}: {exc}") from exc


def payload_digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def request_json(
    url: str,
    headers: dict[str, str],
    method: str = "GET",
    body: Any | None = None,
    insecure: bool = False,
) -> Any:
    data = None
    request_headers = dict(headers)
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request_headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        context = ssl._create_unverified_context() if insecure else None
        with urllib.request.urlopen(req, timeout=30, context=context) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            if not raw.strip():
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                raise SystemExit(
                    json.dumps(
                        {
                            "ok": False,
                            "error_type": "INVALID_JSON_RESPONSE",
                            "http_status": getattr(resp, "status", None),
                            "content_type": resp.headers.get("content-type"),
                            "url": url,
                            "body": raw[:1000],
                        },
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    )
                ) from None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"body": body[:1000]}
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "http_status": exc.code,
                    "url": url,
                    "error": redact(payload),
                },
                ensure_ascii=False,
                indent=2,
            )
        ) from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        message = str(reason)
        payload: dict[str, Any] = {
            "ok": False,
            "error_type": "URL_ERROR",
            "url": url,
            "error": message,
        }
        if isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in message:
            payload["error_type"] = "TLS_CERTIFICATE_VERIFY_FAILED"
            payload["hint"] = "If this is an internal ByteDance CA chain mismatch, rerun with --insecure."
        raise SystemExit(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)) from exc


def app_headers(args: argparse.Namespace) -> dict[str, str]:
    return {"x-jwt-token": bytecloud_jwt(args.site), "accept": "application/json"}


def app_detail(args: argparse.Namespace, app: str) -> dict[str, Any]:
    headers = app_headers(args)
    url = build_url(api_base(args.site), f"/apps/{quote_path(app)}", region_params(args))
    payload = request_json(url, headers, insecure=args.insecure)
    if not isinstance(payload, dict) or payload.get("code") != 0:
        raise SystemExit(json.dumps({"ok": False, "response": redact(payload)}, ensure_ascii=False, indent=2))
    data = payload.get("data")
    if not isinstance(data, dict):
        raise SystemExit("invalid app detail response: data is not an object")
    return data


def statemachine_headers(args: argparse.Namespace, app: str) -> dict[str, str]:
    jwt = bytecloud_jwt(args.site)
    detail = app_detail(args, app)
    app_token = detail.get("token")
    if not isinstance(app_token, str) or not app_token:
        raise SystemExit(f"app {app!r} did not return a usable app token")
    return {
        "x-jwt-token": jwt,
        "Authorization": f"Bearer {app_token}",
        "Bf-Cluster": args.cluster,
        "accept": "application/json",
    }


def cmd_app_list(args: argparse.Namespace) -> None:
    query = {
        **region_params(args),
        "page_no": args.page_no,
        "page_size": args.page_size,
        "subscribed_only": args.subscribed_only,
        "name": args.name or "",
    }
    url = build_url(api_base(args.site), "/apps", query)
    json_print(safe_payload(request_json(url, app_headers(args), insecure=args.insecure), args.include_definition))


def cmd_app_get(args: argparse.Namespace) -> None:
    json_print(safe_payload({"code": 0, "data": app_detail(args, args.app)}, args.include_definition))


def cmd_statemachine_list(args: argparse.Namespace) -> None:
    query = {**region_params(args), "page_no": args.page_no, "page_size": args.page_size}
    url = build_url(api_base(args.site), "/statemachines", query)
    json_print(
        safe_payload(
            request_json(url, statemachine_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_statemachine_get(args: argparse.Namespace) -> None:
    url = build_url(api_base(args.site), f"/statemachines/{quote_path(args.id)}", region_params(args))
    json_print(
        safe_payload(
            request_json(url, statemachine_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_revision_list(args: argparse.Namespace) -> None:
    query = {**region_params(args), "page_no": args.page_no, "page_size": args.page_size}
    path = f"/statemachines/{quote_path(args.statemachine_id)}/revisions"
    url = build_url(api_base(args.site), path, query)
    json_print(
        safe_payload(
            request_json(url, statemachine_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def parse_execution_console_url(url: str) -> dict[str, str]:
    parsed = urllib.parse.urlparse(url)
    parts = [urllib.parse.unquote(part) for part in parsed.path.split("/") if part]
    for index, part in enumerate(parts):
        if part != "byteflow":
            continue
        expected = parts[index : index + 5]
        if len(expected) == 5 and expected[1] == "app" and expected[3] == "execution":
            app = expected[2]
            execution_id = expected[4]
            if not app or not execution_id:
                break
            return {
                "app": app,
                "execution_id": execution_id,
                "site": CONSOLE_SITE_BY_HOST.get(parsed.hostname or "", ""),
            }
    raise SystemExit(
        "invalid ByteFlow execution URL; expected /byteflow/app/<app>/execution/<execution_id>"
    )


def resolve_execution_target(args: argparse.Namespace) -> tuple[str, str, str]:
    app = getattr(args, "app", "") or ""
    execution_id = getattr(args, "id", "") or ""
    inferred_site = ""

    if getattr(args, "url", ""):
        parsed = parse_execution_console_url(args.url)
        if app and app != parsed["app"]:
            raise SystemExit(f"--app {app!r} does not match URL app {parsed['app']!r}")
        if execution_id and execution_id != parsed["execution_id"]:
            raise SystemExit(
                f"--id {execution_id!r} does not match URL execution id {parsed['execution_id']!r}"
            )
        app = parsed["app"]
        execution_id = parsed["execution_id"]
        inferred_site = parsed["site"]
        if inferred_site and getattr(args, "site", "cn") == "cn":
            args.site = inferred_site

    if not app or not execution_id:
        raise SystemExit("provide --url or both --app and --id")
    return app, execution_id, inferred_site


def checked_response_data(payload: Any, label: str) -> Any:
    if not isinstance(payload, dict) or payload.get("code") != 0:
        raise SystemExit(json.dumps({"ok": False, "response": redact(payload)}, ensure_ascii=False, indent=2))
    return payload.get("data")


def fetch_execution_detail(
    args: argparse.Namespace,
    headers: dict[str, str],
    execution_id: str,
) -> dict[str, Any]:
    url = build_url(api_base(args.site), f"/executions/{quote_path(execution_id)}")
    data = checked_response_data(request_json(url, headers, insecure=args.insecure), "execution detail")
    if not isinstance(data, dict):
        raise SystemExit("invalid execution detail response: data is not an object")
    return data


def fetch_execution_events(
    args: argparse.Namespace,
    headers: dict[str, str],
    execution_id: str,
) -> list[dict[str, Any]]:
    query = {
        "page_no": args.page_no,
        "page_size": args.page_size,
    }
    url = build_url(api_base(args.site), f"/executions/{quote_path(execution_id)}/events", query)
    data = checked_response_data(request_json(url, headers, insecure=args.insecure), "execution events")
    if not isinstance(data, list):
        raise SystemExit("invalid execution events response: data is not a list")
    return [event for event in data if isinstance(event, dict)]


def execution_detail_summary(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "status": data.get("status"),
        "started": data.get("started"),
        "stopped": data.get("stopped"),
        "state_machine_id": data.get("state_machine_id"),
    }


def event_summary(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("event_id"),
        "previous_event_id": event.get("previous_event_id"),
        "event_type": event.get("event_type"),
        "state_name": event.get("state_name"),
        "timestamp": event.get("timestamp"),
    }


def active_states_from_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active_by_state: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        event_type = str(event.get("event_type") or "")
        state_name = str(event.get("state_name") or "")
        if not state_name:
            continue
        if event_type.endswith("StateEntered"):
            active_by_state.setdefault(state_name, []).append(event)
            continue
        if (
            event_type.endswith("StateExited")
            or event_type.endswith("StateFailed")
            or event_type.endswith("StateSucceeded")
            or event_type.endswith("StateTimedOut")
        ):
            stack = active_by_state.get(state_name)
            if stack:
                stack.pop()
                if not stack:
                    active_by_state.pop(state_name, None)

    active_events: list[dict[str, Any]] = []
    for stack in active_by_state.values():
        active_events.extend(stack)
    active_events.sort(key=lambda event: (str(event.get("timestamp") or ""), int(event.get("event_id") or 0)))
    return [event_summary(event) for event in active_events]


def execution_headers(args: argparse.Namespace, app: str) -> dict[str, str]:
    return statemachine_headers(args, app)


def cmd_execution_get(args: argparse.Namespace) -> None:
    app, execution_id, inferred_site = resolve_execution_target(args)
    headers = execution_headers(args, app)
    detail = fetch_execution_detail(args, headers, execution_id)
    json_print(
        safe_payload(
            {
                "ok": True,
                "app": app,
                "site": args.site,
                "site_inferred_from_url": inferred_site or None,
                "data": detail,
            },
            args.include_definition,
        )
    )


def cmd_execution_events(args: argparse.Namespace) -> None:
    app, execution_id, inferred_site = resolve_execution_target(args)
    headers = execution_headers(args, app)
    events = fetch_execution_events(args, headers, execution_id)
    json_print(
        safe_payload(
            {
                "ok": True,
                "app": app,
                "site": args.site,
                "site_inferred_from_url": inferred_site or None,
                "execution_id": execution_id,
                "event_count": len(events),
                "data": events,
            },
            args.include_definition,
        )
    )


def cmd_execution_current(args: argparse.Namespace) -> None:
    app, execution_id, inferred_site = resolve_execution_target(args)
    headers = execution_headers(args, app)
    detail = fetch_execution_detail(args, headers, execution_id)
    events = fetch_execution_events(args, headers, execution_id)
    last_events = [event_summary(event) for event in events[-args.last_events :]] if args.last_events else []
    output = {
        "ok": True,
        "app": app,
        "site": args.site,
        "site_inferred_from_url": inferred_site or None,
        "execution_id": detail.get("id", execution_id),
        "name": detail.get("name"),
        "status": detail.get("status"),
        "started": detail.get("started"),
        "stopped": detail.get("stopped"),
        "state_machine_id": detail.get("state_machine_id"),
        "event_count": len(events),
        "active_states": active_states_from_events(events),
        "last_events": last_events,
    }
    json_print(safe_payload(output, args.include_definition))


def cmd_execution_list(args: argparse.Namespace) -> None:
    path = "/executions"
    if args.statemachine_id:
        path = f"/statemachines/{quote_path(args.statemachine_id)}/executions"
    url = build_url(api_base(args.site), path, pagination_query(args))
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_express_list(args: argparse.Namespace) -> None:
    url = build_url(api_base(args.site), "/express", pagination_query(args))
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_express_events(args: argparse.Namespace) -> None:
    path = f"/express/{quote_path(args.id)}/events"
    url = build_url(api_base(args.site), path, pagination_query(args))
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_activity_list(args: argparse.Namespace) -> None:
    url = build_url(api_base(args.site), "/activities", pagination_query(args, {"name": args.name}))
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_activity_get(args: argparse.Namespace) -> None:
    path = f"/activities/{quote_path(args.name)}"
    url = build_url(api_base(args.site), path, {"name": args.name})
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_dag_list(args: argparse.Namespace) -> None:
    url = build_url(api_base(args.site), "/dags", pagination_query(args, {"name": args.name}))
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_dag_get(args: argparse.Namespace) -> None:
    path = f"/dags/{quote_path(args.id)}"
    url = build_url(api_base(args.site), path)
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_dag_execution_list(args: argparse.Namespace) -> None:
    url = build_url(api_base(args.site), "/dagexecutions", pagination_query(args))
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_dag_execution_get(args: argparse.Namespace) -> None:
    path = f"/dagexecutions/{quote_path(args.id)}"
    url = build_url(api_base(args.site), path)
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def cmd_dag_execution_events(args: argparse.Namespace) -> None:
    path = f"/dagexecutions/{quote_path(args.id)}/events"
    url = build_url(api_base(args.site), path, pagination_query(args))
    json_print(
        safe_payload(
            request_json(url, execution_headers(args, args.app), insecure=args.insecure),
            args.include_definition,
        )
    )


def confirm_phrase(action: str, *parts: Any) -> str:
    return ":".join([action, *[str(part) for part in parts]])


def write_confirm_phrase(action: str, args: argparse.Namespace) -> str:
    if action == "statemachine-create":
        raise SystemExit("statemachine-create confirmation must include workflow_sha256")
    if action == "statemachine-update":
        raise SystemExit("statemachine-update confirmation must include workflow_sha256")
    if action == "statemachine-delete":
        return confirm_phrase(action, args.app, args.id)
    if action == "revision-create":
        return confirm_phrase(action, args.app, args.statemachine_id, args.name)
    if action == "revision-delete":
        return confirm_phrase(action, args.app, args.statemachine_id, args.revision_number)
    if action in {"activity-create", "activity-update", "activity-delete"}:
        return confirm_phrase(action, args.app, args.name)
    if action in {"dag-update", "dag-delete", "dag-execution-stop"}:
        return confirm_phrase(action, args.app, args.id)
    if action in {"dag-create", "dag-execution-start"}:
        return confirm_phrase(action, args.app)
    return confirm_phrase(action, getattr(args, "app", ""))


def workflow_write_confirm_phrase(action: str, args: argparse.Namespace, workflow_sha256: str) -> str:
    if action == "statemachine-create":
        return confirm_phrase(action, args.app, args.name, workflow_sha256)
    if action == "statemachine-update":
        return confirm_phrase(action, args.app, args.id, workflow_sha256)
    raise SystemExit(f"{action} is not a workflow definition write")


def require_write_confirmation(args: argparse.Namespace, action: str, confirm_phrase: str) -> None:
    if args.dry_run:
        return
    if not args.yes:
        raise SystemExit(
            f"{action} is a write operation; pass --dry-run first, then rerun with --yes "
            "and the exact --confirm-write value from the dry-run output"
        )
    if getattr(args, "confirm_write", "") != confirm_phrase:
        raise SystemExit(
            f"{action} requires per-operation user confirmation. Run the same command with "
            "--dry-run, show the risk and target to the user, then rerun with the exact "
            "--confirm-write value from the dry-run output."
        )


def guarded_write(
    args: argparse.Namespace,
    action: str,
    path: str,
    method: str,
    headers: dict[str, str],
    body: Any | None = None,
    query: dict[str, Any] | None = None,
    target: dict[str, Any] | None = None,
    confirm: str | None = None,
) -> None:
    confirm_value = confirm or write_confirm_phrase(action, args)
    target_data = target or {}
    app_value = getattr(args, "app", None) or target_data.get("app")
    preview: dict[str, Any] = {
        "write": f"{method} {path}",
        "app": app_value,
        "target": target_data,
        "required_confirm_write": confirm_value,
        "requires_human_confirmation": True,
    }
    if query:
        preview["query"] = query
    if body is not None:
        preview["payload"] = body
    if args.dry_run:
        json_print(safe_payload({"ok": True, "dry_run": True, **preview}, args.include_definition))
        return

    require_write_confirmation(args, action, confirm_value)
    url = build_url(api_base(args.site), path, query)
    response = request_json(url, headers, method=method, body=body, insecure=args.insecure)
    json_print(safe_payload({"ok": True, "request": preview, "response": response}, args.include_definition))


def enforce_live_status_guard(
    args: argparse.Namespace,
    action: str,
    status: Any,
    allowed_statuses: set[str],
    target: dict[str, Any],
) -> None:
    if args.dry_run or getattr(args, "allow_status_risk", False):
        return
    status_text = str(status or "")
    if status_text in allowed_statuses:
        return
    raise SystemExit(
        json.dumps(
            {
                "ok": False,
                "blocked": True,
                "reason": "STATUS_GUARD_REQUIRES_USER_CONSENT",
                "action": action,
                "current_status": status,
                "allowed_statuses": sorted(allowed_statuses),
                "target": target,
                "required_next_step": (
                    "Show this status mismatch to the user. Only rerun with --allow-status-risk "
                    "after the user explicitly confirms this specific write despite the status."
                ),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


def fetch_dag_execution_detail(
    args: argparse.Namespace,
    headers: dict[str, str],
    dag_execution_id: str,
) -> dict[str, Any]:
    url = build_url(api_base(args.site), f"/dagexecutions/{quote_path(dag_execution_id)}")
    data = checked_response_data(request_json(url, headers, insecure=args.insecure), "dag execution detail")
    if not isinstance(data, dict):
        raise SystemExit("invalid DAG execution detail response: data is not an object")
    return data


def cmd_app_subscribe(args: argparse.Namespace) -> None:
    guarded_write(
        args,
        "app-subscribe",
        f"/apps/{quote_path(args.app)}/subscribe",
        "POST",
        app_headers(args),
        target={"app": args.app},
        confirm=confirm_phrase("app-subscribe", args.app),
    )


def cmd_app_unsubscribe(args: argparse.Namespace) -> None:
    guarded_write(
        args,
        "app-unsubscribe",
        f"/apps/{quote_path(args.app)}/unsubscribe",
        "POST",
        app_headers(args),
        target={"app": args.app},
        confirm=confirm_phrase("app-unsubscribe", args.app),
    )


def cmd_statemachine_delete(args: argparse.Namespace) -> None:
    headers = statemachine_headers(args, args.app)
    current = fetch_statemachine_detail(args, headers, args.id)
    revision_guard = fetch_revision_guard_for_id(args, headers, args.id)
    guarded_write(
        args,
        "statemachine-delete",
        f"/statemachines/{quote_path(args.id)}",
        "DELETE",
        headers,
        target={
            "state_machine_id": args.id,
            "current": statemachine_summary(current),
            "revision_guard": revision_guard,
        },
    )


def cmd_revision_delete(args: argparse.Namespace) -> None:
    headers = statemachine_headers(args, args.app)
    current = fetch_statemachine_detail(args, headers, args.statemachine_id)
    query = {"revision_number": args.revision_number}
    guarded_write(
        args,
        "revision-delete",
        f"/statemachines/{quote_path(args.statemachine_id)}/revisions",
        "DELETE",
        headers,
        query=query,
        target={
            "state_machine_id": args.statemachine_id,
            "revision_number": args.revision_number,
            "current": statemachine_summary(current),
        },
    )


def cmd_execution_start(args: argparse.Namespace) -> None:
    body = load_json_payload(args.payload_file)
    digest = payload_digest(body)
    guarded_write(
        args,
        "execution-start",
        "/executions",
        "POST",
        execution_headers(args, args.app),
        body=body,
        target={"payload_file": args.payload_file, "payload_sha256": digest},
        confirm=confirm_phrase("execution-start", args.app, digest),
    )


def cmd_express_start(args: argparse.Namespace) -> None:
    body = load_json_payload(args.payload_file)
    digest = payload_digest(body)
    guarded_write(
        args,
        "express-start",
        "/express",
        "POST",
        execution_headers(args, args.app),
        body=body,
        target={"payload_file": args.payload_file, "payload_sha256": digest},
        confirm=confirm_phrase("express-start", args.app, digest),
    )


def cmd_execution_retry(args: argparse.Namespace) -> None:
    app, execution_id, inferred_site = resolve_execution_target(args)
    headers = execution_headers(args, app)
    detail = fetch_execution_detail(args, headers, execution_id)
    target = {
        "app": app,
        "site": args.site,
        "site_inferred_from_url": inferred_site or None,
        "execution": execution_detail_summary(detail),
    }
    enforce_live_status_guard(args, "execution-retry", detail.get("status"), {"Cancelled", "Canceled", "Failed"}, target)
    guarded_write(
        args,
        "execution-retry",
        f"/executions/{quote_path(execution_id)}/retry",
        "POST",
        headers,
        body={},
        target=target,
        confirm=confirm_phrase("execution-retry", app, execution_id),
    )


def cmd_execution_stop(args: argparse.Namespace) -> None:
    app, execution_id, inferred_site = resolve_execution_target(args)
    headers = execution_headers(args, app)
    detail = fetch_execution_detail(args, headers, execution_id)
    target = {
        "app": app,
        "site": args.site,
        "site_inferred_from_url": inferred_site or None,
        "execution": execution_detail_summary(detail),
    }
    enforce_live_status_guard(args, "execution-stop", detail.get("status"), {"Running"}, target)
    guarded_write(
        args,
        "execution-stop",
        f"/executions/{quote_path(execution_id)}/stop",
        "POST",
        headers,
        target=target,
        confirm=confirm_phrase("execution-stop", app, execution_id),
    )


def cmd_execution_delete(args: argparse.Namespace) -> None:
    app, execution_id, inferred_site = resolve_execution_target(args)
    headers = execution_headers(args, app)
    detail = fetch_execution_detail(args, headers, execution_id)
    target = {
        "app": app,
        "site": args.site,
        "site_inferred_from_url": inferred_site or None,
        "execution": execution_detail_summary(detail),
    }
    enforce_live_status_guard(
        args,
        "execution-delete",
        detail.get("status"),
        {"Cancelled", "Canceled", "Failed", "Succeed", "Succeeded"},
        target,
    )
    guarded_write(
        args,
        "execution-delete",
        f"/executions/{quote_path(execution_id)}",
        "DELETE",
        headers,
        target=target,
        confirm=confirm_phrase("execution-delete", app, execution_id),
    )


def cmd_activity_create(args: argparse.Namespace) -> None:
    body = load_json_payload(args.payload_file)
    digest = payload_digest(body)
    guarded_write(
        args,
        "activity-create",
        f"/activities/{quote_path(args.name)}",
        "POST",
        execution_headers(args, args.app),
        body=body,
        target={"activity_name": args.name, "payload_file": args.payload_file, "payload_sha256": digest},
        confirm=confirm_phrase("activity-create", args.app, args.name, digest),
    )


def cmd_activity_update(args: argparse.Namespace) -> None:
    body = load_json_payload(args.payload_file)
    digest = payload_digest(body)
    headers = execution_headers(args, args.app)
    current_url = build_url(api_base(args.site), f"/activities/{quote_path(args.name)}", {"name": args.name})
    current = request_json(current_url, headers, insecure=args.insecure)
    guarded_write(
        args,
        "activity-update",
        f"/activities/{quote_path(args.name)}",
        "PUT",
        headers,
        body=body,
        target={
            "activity_name": args.name,
            "payload_sha256": digest,
            "current": current.get("data") if isinstance(current, dict) else current,
        },
        confirm=confirm_phrase("activity-update", args.app, args.name, digest),
    )


def cmd_activity_delete(args: argparse.Namespace) -> None:
    headers = execution_headers(args, args.app)
    current_url = build_url(api_base(args.site), f"/activities/{quote_path(args.name)}", {"name": args.name})
    current = request_json(current_url, headers, insecure=args.insecure)
    guarded_write(
        args,
        "activity-delete",
        f"/activities/{quote_path(args.name)}",
        "DELETE",
        headers,
        target={"activity_name": args.name, "current": current.get("data") if isinstance(current, dict) else current},
    )


def cmd_dag_create(args: argparse.Namespace) -> None:
    body = load_json_payload(args.payload_file)
    digest = payload_digest(body)
    guarded_write(
        args,
        "dag-create",
        "/dags",
        "POST",
        execution_headers(args, args.app),
        body=body,
        target={"payload_file": args.payload_file, "payload_sha256": digest},
        confirm=confirm_phrase("dag-create", args.app, digest),
    )


def cmd_dag_update(args: argparse.Namespace) -> None:
    body = load_json_payload(args.payload_file)
    digest = payload_digest(body)
    headers = execution_headers(args, args.app)
    current_url = build_url(api_base(args.site), f"/dags/{quote_path(args.id)}")
    current = request_json(current_url, headers, insecure=args.insecure)
    guarded_write(
        args,
        "dag-update",
        f"/dags/{quote_path(args.id)}",
        "PUT",
        headers,
        body=body,
        target={
            "dag_id": args.id,
            "payload_sha256": digest,
            "current": current.get("data") if isinstance(current, dict) else current,
        },
        confirm=confirm_phrase("dag-update", args.app, args.id, digest),
    )


def cmd_dag_delete(args: argparse.Namespace) -> None:
    headers = execution_headers(args, args.app)
    current_url = build_url(api_base(args.site), f"/dags/{quote_path(args.id)}")
    current = request_json(current_url, headers, insecure=args.insecure)
    guarded_write(
        args,
        "dag-delete",
        f"/dags/{quote_path(args.id)}",
        "DELETE",
        headers,
        target={"dag_id": args.id, "current": current.get("data") if isinstance(current, dict) else current},
    )


def cmd_dag_execution_start(args: argparse.Namespace) -> None:
    body = load_json_payload(args.payload_file)
    digest = payload_digest(body)
    guarded_write(
        args,
        "dag-execution-start",
        "/dagexecutions",
        "POST",
        execution_headers(args, args.app),
        body=body,
        target={"payload_file": args.payload_file, "payload_sha256": digest},
        confirm=confirm_phrase("dag-execution-start", args.app, digest),
    )


def cmd_dag_execution_stop(args: argparse.Namespace) -> None:
    headers = execution_headers(args, args.app)
    detail = fetch_dag_execution_detail(args, headers, args.id)
    target = {"dag_execution": {"id": detail.get("id", args.id), "name": detail.get("name"), "status": detail.get("status")}}
    enforce_live_status_guard(args, "dag-execution-stop", detail.get("status"), {"Running"}, target)
    guarded_write(
        args,
        "dag-execution-stop",
        f"/dagexecutions/{quote_path(args.id)}/stop",
        "POST",
        headers,
        target=target,
    )


def revision_list_path(statemachine_id: str) -> str:
    return f"/statemachines/{quote_path(statemachine_id)}/revisions"


def revision_count_from_payload(payload: Any) -> int:
    if not isinstance(payload, dict):
        return 0
    pagination = payload.get("pagination")
    if isinstance(pagination, dict):
        total = pagination.get("total")
        if isinstance(total, int):
            return total
        if isinstance(total, str) and total.isdigit():
            return int(total)
    data = payload.get("data")
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ("total", "count"):
            total = data.get(key)
            if isinstance(total, int):
                return total
            if isinstance(total, str) and total.isdigit():
                return int(total)
        for key in ("data", "items", "list"):
            rows = data.get(key)
            if isinstance(rows, list):
                return len(rows)
    return 0


def fetch_revision_guard_for_id(
    args: argparse.Namespace,
    headers: dict[str, str],
    statemachine_id: str,
) -> dict[str, Any]:
    query = {**region_params(args), "page_no": 1, "page_size": 1}
    path = revision_list_path(statemachine_id)
    url = build_url(api_base(args.site), path, query)
    payload = request_json(url, headers, insecure=args.insecure)
    count = revision_count_from_payload(payload)
    return {
        "revision_count": count,
        "has_revision": count > 0,
        "checked_endpoint": path,
    }


def fetch_revision_guard(args: argparse.Namespace, headers: dict[str, str]) -> dict[str, Any]:
    return fetch_revision_guard_for_id(args, headers, args.statemachine_id)


def fetch_statemachine_detail(
    args: argparse.Namespace,
    headers: dict[str, str],
    statemachine_id: str,
) -> dict[str, Any]:
    url = build_url(api_base(args.site), f"/statemachines/{quote_path(statemachine_id)}", region_params(args))
    payload = request_json(url, headers, insecure=args.insecure)
    if not isinstance(payload, dict) or payload.get("code") != 0:
        raise SystemExit(json.dumps({"ok": False, "response": redact(payload)}, ensure_ascii=False, indent=2))
    data = payload.get("data")
    if not isinstance(data, dict):
        raise SystemExit("invalid statemachine response: data is not an object")
    return data


def statemachine_summary(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "type": data.get("type"),
        "latest_revision": data.get("latest_revision"),
        "updated": data.get("updated"),
        "username": data.get("username"),
    }


def enforce_no_revision_guard(
    args: argparse.Namespace,
    guard: dict[str, Any],
    statemachine_id: str,
    message_text: str,
) -> None:
    if guard["has_revision"]:
        return
    if getattr(args, "allow_first_revision_risk", False):
        return
    message = {
        "ok": False,
        "blocked": True,
        "reason": "FIRST_REVISION_REQUIRES_USER_CONSENT",
        "message": message_text,
        "app": args.app,
        "state_machine_id": statemachine_id,
        "revision_guard": guard,
        "required_next_step": (
            "Tell the user this statemachine currently has no revisions and that this operation "
            "may introduce online risk. Only rerun with --allow-first-revision-risk after "
            "the user explicitly agrees."
        ),
    }
    raise SystemExit(json.dumps(message, ensure_ascii=False, indent=2, sort_keys=True))


def enforce_first_revision_guard(args: argparse.Namespace, guard: dict[str, Any]) -> None:
    enforce_no_revision_guard(args, guard, args.statemachine_id, FIRST_REVISION_RISK_MESSAGE)


def definition_string_from_file(path: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    workflow = load_workflow(path)
    validation = validate_workflow(workflow)
    if not validation["ok"]:
        raise SystemExit(json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True))
    return workflow, json.dumps(workflow, ensure_ascii=False, indent=2), validation


def cmd_statemachine_create(args: argparse.Namespace) -> None:
    workflow, definition_str, validation = definition_string_from_file(args.file)
    workflow_sha256 = payload_digest(workflow)
    confirm_phrase = workflow_write_confirm_phrase("statemachine-create", args, workflow_sha256)
    require_write_confirmation(args, "statemachine-create", confirm_phrase)
    payload: dict[str, Any] = {
        "name": args.name,
        "type": args.type,
        "definition_str": definition_str,
    }
    if args.sa_secret:
        payload["sa_secret"] = args.sa_secret
    preview = {
        "write": "POST /statemachines",
        "app": args.app,
        "name": args.name,
        "type": args.type,
        "workflow_sha256": workflow_sha256,
        "workflow_summary": validation["summary"],
        "required_confirm_write": confirm_phrase,
        "payload": payload,
    }
    if args.dry_run:
        json_print(safe_payload({"ok": True, "dry_run": True, **preview}, args.include_definition))
        return
    url = build_url(api_base(args.site), "/statemachines", region_params(args))
    response = request_json(
        url,
        statemachine_headers(args, args.app),
        method="POST",
        body=payload,
        insecure=args.insecure,
    )
    json_print(safe_payload({"ok": True, "request": preview, "response": response}, args.include_definition))


def cmd_statemachine_update(args: argparse.Namespace) -> None:
    workflow, definition_str, validation = definition_string_from_file(args.file)
    workflow_sha256 = payload_digest(workflow)
    confirm_phrase = workflow_write_confirm_phrase("statemachine-update", args, workflow_sha256)
    require_write_confirmation(args, "statemachine-update", confirm_phrase)
    headers = statemachine_headers(args, args.app)
    current = fetch_statemachine_detail(args, headers, args.id)
    revision_guard = fetch_revision_guard_for_id(args, headers, args.id)
    name = current.get("name")
    sm_type = current.get("type")
    if not isinstance(name, str) or not name:
        raise SystemExit("cannot update: current statemachine response has no usable name")
    if sm_type not in {"standard", "express"}:
        raise SystemExit(f"cannot update: unsupported current statemachine type {sm_type!r}")
    payload: dict[str, Any] = {
        "name": name,
        "type": sm_type,
        "definition_str": definition_str,
    }
    if isinstance(current.get("sa_secret"), str) and current.get("sa_secret"):
        payload["sa_secret"] = current["sa_secret"]
    preview = {
        "write": f"PUT /statemachines/{args.id}",
        "app": args.app,
        "state_machine_id": args.id,
        "current": statemachine_summary(current),
        "revision_guard": revision_guard,
        "workflow_sha256": workflow_sha256,
        "workflow_summary": validation["summary"],
        "required_confirm_write": confirm_phrase,
        "payload": payload,
    }
    if args.dry_run:
        output = {"ok": True, "dry_run": True, **preview}
        if not revision_guard["has_revision"]:
            output["warning"] = NO_REVISION_UPDATE_RISK_MESSAGE
            output["requires_user_consent"] = True
        json_print(safe_payload(output, args.include_definition))
        return
    enforce_no_revision_guard(args, revision_guard, args.id, NO_REVISION_UPDATE_RISK_MESSAGE)
    url = build_url(api_base(args.site), f"/statemachines/{quote_path(args.id)}", region_params(args))
    response = request_json(url, headers, method="PUT", body=payload, insecure=args.insecure)
    json_print(safe_payload({"ok": True, "request": preview, "response": response}, args.include_definition))


def cmd_revision_create(args: argparse.Namespace) -> None:
    confirm_phrase = write_confirm_phrase("revision-create", args)
    require_write_confirmation(args, "revision-create", confirm_phrase)
    if len(args.name) > REVISION_NAME_MAX_LEN:
        raise SystemExit(
            f"revision name is too long: {len(args.name)} chars; use <= {REVISION_NAME_MAX_LEN}"
        )
    headers = statemachine_headers(args, args.app)
    revision_guard = fetch_revision_guard(args, headers)
    payload = {
        "revision_name": args.name,
        "description": args.description or "",
    }
    preview = {
        "write": f"POST /statemachines/{args.statemachine_id}/revisions",
        "app": args.app,
        "state_machine_id": args.statemachine_id,
        "revision_guard": revision_guard,
        "required_confirm_write": confirm_phrase,
        "payload": payload,
    }
    if args.dry_run:
        output = {"ok": True, "dry_run": True, **preview}
        if not revision_guard["has_revision"]:
            output["warning"] = FIRST_REVISION_RISK_MESSAGE
            output["requires_user_consent"] = True
        json_print(safe_payload(output, args.include_definition))
        return
    enforce_first_revision_guard(args, revision_guard)
    path = f"/statemachines/{quote_path(args.statemachine_id)}/revisions"
    url = build_url(api_base(args.site), path, region_params(args))
    response = request_json(url, headers, method="POST", body=payload, insecure=args.insecure)
    json_print(safe_payload({"ok": True, "request": preview, "response": response}, args.include_definition))


def cmd_workflow_validate(args: argparse.Namespace) -> None:
    json_print(validate_workflow(load_workflow(args.file)))


def cmd_workflow_explain(args: argparse.Namespace) -> None:
    json_print(redact(explain_workflow(load_workflow(args.file))))


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--site", default="cn", choices=sorted(SITE_ORIGINS), help="ByteCloud site")
    parser.add_argument("--resource-account", default="public")
    parser.add_argument("--region-id", default="bytedance")
    parser.add_argument("--cluster", default="default")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification for internal CA-chain mismatches",
    )
    parser.add_argument(
        "--include-definition",
        action="store_true",
        help="Print full workflow definition fields instead of omitting them",
    )


def add_execution_target_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--url", default="", help="ByteFlow console execution URL")
    parser.add_argument("--app", default="", help="ByteFlow app name")
    parser.add_argument("--id", default="", help="Execution ID")


def add_pagination_args(parser: argparse.ArgumentParser, page_size: int = 20) -> None:
    parser.add_argument("--page-no", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=page_size)


def add_write_guard_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true", help="Execute the write operation")
    parser.add_argument("--confirm-write", default="", help="Exact confirmation phrase from dry-run output")


def add_payload_file_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--payload-file", required=True, help="JSON request body file, or '-' for stdin")


def add_status_risk_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--allow-status-risk",
        action="store_true",
        help="Allow a status-sensitive write after explicit user consent",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ByteFlow helper for safe query, workflow validation, and guarded writes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  python3 scripts/byteflow_api.py app-list --subscribed-only --name example
  python3 scripts/byteflow_api.py statemachine-get --app example_app --id 12345
  python3 scripts/byteflow_api.py execution-current --url https://example.test/byteflow/app/example_app/execution/12345
  python3 scripts/byteflow_api.py activity-list --app example_app
  python3 scripts/byteflow_api.py dag-list --app example_app
  python3 scripts/byteflow_api.py statemachine-update --app demo_workflow --id 12345 --file workflow.json --dry-run
  python3 scripts/byteflow_api.py execution-stop --app example_app --id 12345 --dry-run
  python3 scripts/byteflow_api.py revision-create --app demo_workflow --statemachine-id 12345 --name r1 --dry-run
""",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    app_list = sub.add_parser("app-list")
    add_common(app_list)
    add_pagination_args(app_list)
    app_list.add_argument("--name", default="")
    app_list.add_argument("--subscribed-only", action="store_true")
    app_list.set_defaults(func=cmd_app_list)

    app_get = sub.add_parser("app-get")
    add_common(app_get)
    app_get.add_argument("--app", required=True)
    app_get.set_defaults(func=cmd_app_get)

    app_subscribe = sub.add_parser("app-subscribe", help="Subscribe to an app after confirmation")
    add_common(app_subscribe)
    app_subscribe.add_argument("--app", required=True)
    add_write_guard_args(app_subscribe)
    app_subscribe.set_defaults(func=cmd_app_subscribe)

    app_unsubscribe = sub.add_parser("app-unsubscribe", help="Unsubscribe from an app after confirmation")
    add_common(app_unsubscribe)
    app_unsubscribe.add_argument("--app", required=True)
    add_write_guard_args(app_unsubscribe)
    app_unsubscribe.set_defaults(func=cmd_app_unsubscribe)

    sm_list = sub.add_parser("statemachine-list")
    add_common(sm_list)
    sm_list.add_argument("--app", required=True)
    add_pagination_args(sm_list)
    sm_list.set_defaults(func=cmd_statemachine_list)

    sm_get = sub.add_parser("statemachine-get")
    add_common(sm_get)
    sm_get.add_argument("--app", required=True)
    sm_get.add_argument("--id", required=True)
    sm_get.set_defaults(func=cmd_statemachine_get)

    sm_create = sub.add_parser("statemachine-create")
    add_common(sm_create)
    sm_create.add_argument("--app", required=True)
    sm_create.add_argument("--name", required=True)
    sm_create.add_argument("--file", required=True, help="Workflow definition JSON file")
    sm_create.add_argument("--type", choices=["standard", "express"], default="standard")
    sm_create.add_argument("--sa-secret", default="")
    add_write_guard_args(sm_create)
    sm_create.set_defaults(func=cmd_statemachine_create)

    sm_update = sub.add_parser(
        "statemachine-update",
        help="Update an existing statemachine definition after validation and confirmation",
    )
    add_common(sm_update)
    sm_update.add_argument("--app", required=True)
    sm_update.add_argument("--id", required=True)
    sm_update.add_argument("--file", required=True, help="Workflow definition JSON file")
    add_write_guard_args(sm_update)
    sm_update.add_argument(
        "--allow-first-revision-risk",
        action="store_true",
        help="Allow updating a statemachine with no revisions after explicit user consent",
    )
    sm_update.set_defaults(func=cmd_statemachine_update)

    sm_delete = sub.add_parser("statemachine-delete", help="Delete a statemachine after confirmation")
    add_common(sm_delete)
    sm_delete.add_argument("--app", required=True)
    sm_delete.add_argument("--id", required=True)
    add_write_guard_args(sm_delete)
    sm_delete.set_defaults(func=cmd_statemachine_delete)

    rev_list = sub.add_parser("revision-list")
    add_common(rev_list)
    rev_list.add_argument("--app", required=True)
    rev_list.add_argument("--statemachine-id", required=True)
    add_pagination_args(rev_list, page_size=10)
    rev_list.set_defaults(func=cmd_revision_list)

    rev_create = sub.add_parser("revision-create")
    add_common(rev_create)
    rev_create.add_argument("--app", required=True)
    rev_create.add_argument("--statemachine-id", required=True)
    rev_create.add_argument("--name", required=True)
    rev_create.add_argument("--description", default="")
    add_write_guard_args(rev_create)
    rev_create.add_argument(
        "--allow-first-revision-risk",
        action="store_true",
        help="Allow creating the first revision after explicit user consent",
    )
    rev_create.set_defaults(func=cmd_revision_create)

    rev_delete = sub.add_parser("revision-delete", help="Delete a revision after confirmation")
    add_common(rev_delete)
    rev_delete.add_argument("--app", required=True)
    rev_delete.add_argument("--statemachine-id", required=True)
    rev_delete.add_argument("--revision-number", required=True)
    add_write_guard_args(rev_delete)
    rev_delete.set_defaults(func=cmd_revision_delete)

    execution_get = sub.add_parser("execution-get", help="Get execution detail by URL or app/id")
    add_common(execution_get)
    add_execution_target_args(execution_get)
    execution_get.set_defaults(func=cmd_execution_get)

    execution_events = sub.add_parser("execution-events", help="List execution events by URL or app/id")
    add_common(execution_events)
    add_execution_target_args(execution_events)
    add_pagination_args(execution_events, page_size=9999)
    execution_events.set_defaults(func=cmd_execution_events)

    execution_current = sub.add_parser(
        "execution-current",
        help="Summarize execution status and currently active states",
    )
    add_common(execution_current)
    add_execution_target_args(execution_current)
    add_pagination_args(execution_current, page_size=9999)
    execution_current.add_argument("--last-events", type=int, default=12)
    execution_current.set_defaults(func=cmd_execution_current)

    execution_start = sub.add_parser("execution-start", help="Start a standard execution from a JSON payload")
    add_common(execution_start)
    execution_start.add_argument("--app", required=True)
    add_payload_file_arg(execution_start)
    add_write_guard_args(execution_start)
    execution_start.set_defaults(func=cmd_execution_start)

    execution_retry = sub.add_parser("execution-retry", help="Retry an execution after confirmation")
    add_common(execution_retry)
    add_execution_target_args(execution_retry)
    add_status_risk_arg(execution_retry)
    add_write_guard_args(execution_retry)
    execution_retry.set_defaults(func=cmd_execution_retry)

    execution_stop = sub.add_parser("execution-stop", help="Stop a running execution after confirmation")
    add_common(execution_stop)
    add_execution_target_args(execution_stop)
    add_status_risk_arg(execution_stop)
    add_write_guard_args(execution_stop)
    execution_stop.set_defaults(func=cmd_execution_stop)

    execution_delete = sub.add_parser("execution-delete", help="Delete an execution after confirmation")
    add_common(execution_delete)
    add_execution_target_args(execution_delete)
    add_status_risk_arg(execution_delete)
    add_write_guard_args(execution_delete)
    execution_delete.set_defaults(func=cmd_execution_delete)

    execution_list = sub.add_parser("execution-list", help="List executions for an app or statemachine")
    add_common(execution_list)
    execution_list.add_argument("--app", required=True)
    execution_list.add_argument("--statemachine-id", default="")
    add_pagination_args(execution_list)
    execution_list.set_defaults(func=cmd_execution_list)

    express_list = sub.add_parser("express-list", help="List express executions for an app")
    add_common(express_list)
    express_list.add_argument("--app", required=True)
    add_pagination_args(express_list)
    express_list.set_defaults(func=cmd_express_list)

    express_start = sub.add_parser("express-start", help="Start an express execution from a JSON payload")
    add_common(express_start)
    express_start.add_argument("--app", required=True)
    add_payload_file_arg(express_start)
    add_write_guard_args(express_start)
    express_start.set_defaults(func=cmd_express_start)

    express_events = sub.add_parser("express-events", help="List express execution events")
    add_common(express_events)
    express_events.add_argument("--app", required=True)
    express_events.add_argument("--id", required=True, help="Express execution ID")
    add_pagination_args(express_events, page_size=9999)
    express_events.set_defaults(func=cmd_express_events)

    activity_list = sub.add_parser("activity-list", help="List activities for an app")
    add_common(activity_list)
    activity_list.add_argument("--app", required=True)
    activity_list.add_argument("--name", default="")
    add_pagination_args(activity_list)
    activity_list.set_defaults(func=cmd_activity_list)

    activity_get = sub.add_parser("activity-get", help="Get activity detail by name")
    add_common(activity_get)
    activity_get.add_argument("--app", required=True)
    activity_get.add_argument("--name", required=True)
    activity_get.set_defaults(func=cmd_activity_get)

    activity_create = sub.add_parser("activity-create", help="Create an activity from a JSON payload")
    add_common(activity_create)
    activity_create.add_argument("--app", required=True)
    activity_create.add_argument("--name", required=True)
    add_payload_file_arg(activity_create)
    add_write_guard_args(activity_create)
    activity_create.set_defaults(func=cmd_activity_create)

    activity_update = sub.add_parser("activity-update", help="Update an activity from a JSON payload")
    add_common(activity_update)
    activity_update.add_argument("--app", required=True)
    activity_update.add_argument("--name", required=True)
    add_payload_file_arg(activity_update)
    add_write_guard_args(activity_update)
    activity_update.set_defaults(func=cmd_activity_update)

    activity_delete = sub.add_parser("activity-delete", help="Delete an activity after confirmation")
    add_common(activity_delete)
    activity_delete.add_argument("--app", required=True)
    activity_delete.add_argument("--name", required=True)
    add_write_guard_args(activity_delete)
    activity_delete.set_defaults(func=cmd_activity_delete)

    dag_list = sub.add_parser("dag-list", help="List DAG definitions for an app")
    add_common(dag_list)
    dag_list.add_argument("--app", required=True)
    dag_list.add_argument("--name", default="")
    add_pagination_args(dag_list)
    dag_list.set_defaults(func=cmd_dag_list)

    dag_get = sub.add_parser("dag-get", help="Get DAG detail by ID")
    add_common(dag_get)
    dag_get.add_argument("--app", required=True)
    dag_get.add_argument("--id", required=True, help="DAG ID")
    dag_get.set_defaults(func=cmd_dag_get)

    dag_create = sub.add_parser("dag-create", help="Create a DAG from a JSON payload")
    add_common(dag_create)
    dag_create.add_argument("--app", required=True)
    add_payload_file_arg(dag_create)
    add_write_guard_args(dag_create)
    dag_create.set_defaults(func=cmd_dag_create)

    dag_update = sub.add_parser("dag-update", help="Update a DAG from a JSON payload")
    add_common(dag_update)
    dag_update.add_argument("--app", required=True)
    dag_update.add_argument("--id", required=True, help="DAG ID")
    add_payload_file_arg(dag_update)
    add_write_guard_args(dag_update)
    dag_update.set_defaults(func=cmd_dag_update)

    dag_delete = sub.add_parser("dag-delete", help="Delete a DAG after confirmation")
    add_common(dag_delete)
    dag_delete.add_argument("--app", required=True)
    dag_delete.add_argument("--id", required=True, help="DAG ID")
    add_write_guard_args(dag_delete)
    dag_delete.set_defaults(func=cmd_dag_delete)

    dag_execution_list = sub.add_parser("dag-execution-list", help="List DAG executions for an app")
    add_common(dag_execution_list)
    dag_execution_list.add_argument("--app", required=True)
    add_pagination_args(dag_execution_list)
    dag_execution_list.set_defaults(func=cmd_dag_execution_list)

    dag_execution_get = sub.add_parser("dag-execution-get", help="Get DAG execution detail by ID")
    add_common(dag_execution_get)
    dag_execution_get.add_argument("--app", required=True)
    dag_execution_get.add_argument("--id", required=True, help="DAG execution ID")
    dag_execution_get.set_defaults(func=cmd_dag_execution_get)

    dag_execution_start = sub.add_parser(
        "dag-execution-start",
        help="Start a DAG execution from a JSON payload",
    )
    add_common(dag_execution_start)
    dag_execution_start.add_argument("--app", required=True)
    add_payload_file_arg(dag_execution_start)
    add_write_guard_args(dag_execution_start)
    dag_execution_start.set_defaults(func=cmd_dag_execution_start)

    dag_execution_stop = sub.add_parser("dag-execution-stop", help="Stop a running DAG execution")
    add_common(dag_execution_stop)
    dag_execution_stop.add_argument("--app", required=True)
    dag_execution_stop.add_argument("--id", required=True, help="DAG execution ID")
    add_status_risk_arg(dag_execution_stop)
    add_write_guard_args(dag_execution_stop)
    dag_execution_stop.set_defaults(func=cmd_dag_execution_stop)

    dag_execution_events = sub.add_parser("dag-execution-events", help="List DAG execution events")
    add_common(dag_execution_events)
    dag_execution_events.add_argument("--app", required=True)
    dag_execution_events.add_argument("--id", required=True, help="DAG execution ID")
    add_pagination_args(dag_execution_events, page_size=9999)
    dag_execution_events.set_defaults(func=cmd_dag_execution_events)

    validate = sub.add_parser("workflow-validate")
    validate.add_argument("--file", required=True)
    validate.set_defaults(func=cmd_workflow_validate)

    explain = sub.add_parser("workflow-explain")
    explain.add_argument("--file", required=True)
    explain.set_defaults(func=cmd_workflow_explain)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
