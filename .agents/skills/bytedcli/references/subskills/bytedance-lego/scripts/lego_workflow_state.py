#!/usr/bin/env python3

import json
import math
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple


# 正在编译中的活跃态：这些架构已被排期，需要继续轮询。
COMPILE_ACTIVE = {"prepare", "building", "queue", "wait"}
COMPILE_SUCCEEDED = {"build_ok", "success"}
COMPILE_FAILED = {"build_failed"}
# not_build 表示该架构未参与本次编译（例如未开 --multi-arch 时的 arm），
# 是“未排期”而非“进行中”，不应据此继续轮询。
COMPILE_NOT_SCHEDULED = {"not_build"}
COMPILE_KNOWN = COMPILE_ACTIVE | COMPILE_SUCCEEDED | COMPILE_FAILED | COMPILE_NOT_SCHEDULED

ORDER_PENDING = {0, 2, 4, 5, 6, 8}
STEP_TYPES = {1, 2, 3, 4, 5, 6, 7, 8}
TASK_STATUSES = {0, 1, 2}
CHECK_TASK_STATUSES = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
CHECK_TASK_FAILURES = {4, 5, 9}

INTEGER_TEXT_RE = re.compile(r"^-?\d+$")
MISSING = object()


def classification(
    state: str,
    *,
    terminal: bool,
    requires_human: bool,
    next_action: str,
    reason: str,
) -> Dict[str, Any]:
    return {
        "state": state,
        "terminal": terminal,
        "requires_human": requires_human,
        "next_action": next_action,
        "reason": reason,
    }


def inspect_failure(reason: str) -> Dict[str, Any]:
    return classification(
        "unknown",
        terminal=False,
        requires_human=False,
        next_action="inspect_failure",
        reason=reason,
    )


def is_record(value: Any) -> bool:
    return isinstance(value, dict)


def format_value(value: Any) -> str:
    if value is MISSING:
        return "<missing>"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def as_json_integer(value: Any) -> Optional[int]:
    """Return JSON integer-valued numbers; reject bool and non-integral floats."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    return None


def parse_integer_text(value: str) -> Optional[int]:
    text = value.strip()
    if not INTEGER_TEXT_RE.fullmatch(text):
        return None
    return int(text)


def unwrap_payload(payload: Any, kind: str) -> Optional[Dict[str, Any]]:
    if not is_record(payload):
        return None

    is_envelope = "data" in payload or "error" in payload or "context" in payload
    data = payload.get("data") if is_envelope else payload
    if is_envelope and (payload.get("status") != "success" or not is_record(data)):
        return None
    if not is_record(data):
        return None

    nested_key = {"compile": "detail", "order": "order", "step": "step"}[kind]
    nested = data.get(nested_key, data)
    return nested if is_record(nested) else None


def read_nested_status(value: Any) -> Any:
    if not is_record(value) or "status" not in value:
        return MISSING

    status = value["status"]
    if isinstance(status, str):
        parsed = parse_integer_text(status)
        return parsed if parsed is not None else status
    return status


def validate_enum(field: str, value: Any, allowed: Set[int]) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    if value is MISSING:
        return None, None

    normalized = as_json_integer(value)
    if normalized is None or normalized not in allowed:
        return None, inspect_failure(f"unknown {field}: {format_value(value)}")
    return normalized, None


def classify_compile(data: Dict[str, Any]) -> Dict[str, Any]:
    observed: List[str] = []
    for field in ("status", "status_arm"):
        if field not in data:
            continue
        value = data[field]
        if not isinstance(value, str) or value == "":
            return inspect_failure(f"invalid compile {field}: {format_value(value)}")
        observed.append(value)

    if not observed:
        return inspect_failure("compile detail has no status or status_arm")

    unknown = [value for value in observed if value not in COMPILE_KNOWN]
    if unknown:
        return inspect_failure(f"unknown compile status: {', '.join(unknown)}")

    if any(value in COMPILE_FAILED for value in observed):
        return classification(
            "failed",
            terminal=True,
            requires_human=False,
            next_action="inspect_failure",
            reason=f"compile reached build_failed: {', '.join(observed)}",
        )

    # 只统计被排期的架构；not_build 表示该架构未参与本次编译，直接忽略。
    scheduled = [value for value in observed if value not in COMPILE_NOT_SCHEDULED]

    if not scheduled:
        return inspect_failure(
            f"compile has no scheduled architecture (all not_build): {', '.join(observed)}"
        )

    if all(value in COMPILE_SUCCEEDED for value in scheduled):
        return classification(
            "succeeded",
            terminal=True,
            requires_human=False,
            next_action="stop",
            reason=f"compile succeeded: {', '.join(observed)}",
        )

    return classification(
        "pending",
        terminal=False,
        requires_human=False,
        next_action="poll",
        reason=f"compile is still running: {', '.join(observed)}",
    )


def classify_order(data: Dict[str, Any]) -> Dict[str, Any]:
    status = as_json_integer(data.get("status"))
    if status is None:
        return inspect_failure(f"unknown order status: {format_value(data.get('status'))}")

    if status == 1:
        return classification(
            "succeeded",
            terminal=True,
            requires_human=False,
            next_action="stop",
            reason="order reached PublishFinish(1)",
        )
    if status == 3:
        return classification(
            "canceled",
            terminal=True,
            requires_human=False,
            next_action="stop",
            reason="order reached PublishCancel(3)",
        )
    if status == 7:
        return classification(
            "canceling",
            terminal=False,
            requires_human=False,
            next_action="stop",
            reason="order is PublishCanceling(7); stop automatic progression",
        )
    if status in ORDER_PENDING:
        return classification(
            "pending",
            terminal=False,
            requires_human=False,
            next_action="poll",
            reason=f"order status {status} is not terminal",
        )
    return inspect_failure(f"unknown order status: {status}")


def classify_step(data: Dict[str, Any]) -> Dict[str, Any]:
    raw_type = data["type"] if "type" in data else MISSING
    raw_task_status = (
        data["task_status"] if "task_status" in data else read_nested_status(data.get("task_info"))
    )
    raw_check_status = (
        data["check_task_status"]
        if "check_task_status" in data
        else read_nested_status(data.get("check_task_info"))
    )

    if raw_type is MISSING and raw_task_status is MISSING and raw_check_status is MISSING:
        return inspect_failure("step detail has no type, task_status, or check_task_status")

    task_status, error = validate_enum("task_status", raw_task_status, TASK_STATUSES)
    if error is not None:
        return error
    check_status, error = validate_enum("check_task_status", raw_check_status, CHECK_TASK_STATUSES)
    if error is not None:
        return error
    step_type, error = validate_enum("type", raw_type, STEP_TYPES)
    if error is not None:
        return error

    if task_status == 2:
        return classification(
            "failed",
            terminal=False,
            requires_human=False,
            next_action="inspect_failure",
            reason="step task_status is TaskFailed(2)",
        )
    if check_status in CHECK_TASK_FAILURES:
        return classification(
            "failed",
            terminal=False,
            requires_human=False,
            next_action="inspect_failure",
            reason=f"step check_task_status indicates failure: {check_status}",
        )
    if step_type in {5, 8}:
        return classification(
            "needs_human",
            terminal=False,
            requires_human=True,
            next_action="confirm",
            reason=f"step type {step_type} requires human action",
        )

    return classification(
        "pending",
        terminal=False,
        requires_human=False,
        next_action="poll",
        reason="step has no failure or human-confirmation condition; recheck the order state",
    )


def classify(kind: str, payload: Any) -> Dict[str, Any]:
    data = unwrap_payload(payload, kind)
    if data is None:
        return inspect_failure("input must be a successful JSON envelope or data object")
    if kind == "compile":
        return classify_compile(data)
    if kind == "order":
        return classify_order(data)
    return classify_step(data)


def selection(selected: Optional[Dict[str, Any]], reason: str) -> Dict[str, Any]:
    return {"selected": selected, "reason": reason}


def unwrap_selection_payload(payload: Any) -> Optional[Dict[str, Any]]:
    if not is_record(payload):
        return None
    is_envelope = "data" in payload or "error" in payload or "context" in payload
    data = payload.get("data") if is_envelope else payload
    if is_envelope and (payload.get("status") != "success" or not is_record(data)):
        return None
    return data if is_record(data) else None


def parse_create_time(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or value.strip() == "":
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def select_latest(records: Any, label: str) -> Dict[str, Any]:
    if not isinstance(records, list):
        return selection(None, f"{label} list is missing or invalid")
    if not records:
        return selection(None, f"{label} list is empty")
    if any(not is_record(record) for record in records):
        return selection(None, f"{label} list contains a non-object record")

    parsed: List[Tuple[datetime, Dict[str, Any]]] = []
    timezone_modes: Set[bool] = set()
    for record in records:
        created_at = parse_create_time(record.get("create_time"))
        if created_at is None:
            return selection(None, f"{label} record has missing or invalid create_time")
        timezone_modes.add(created_at.tzinfo is not None)
        parsed.append((created_at, record))

    if len(timezone_modes) > 1:
        return selection(None, f"{label} records mix timezone-aware and timezone-naive create_time values")

    latest_time = max(created_at for created_at, _ in parsed)
    latest = [record for created_at, record in parsed if created_at == latest_time]
    if len(latest) != 1:
        return selection(None, f"{label} has multiple records tied for latest create_time")
    return selection(latest[0], f"selected unique latest {label} by create_time")


def is_successful_version(record: Dict[str, Any]) -> bool:
    observed = [
        record[field]
        for field in ("status", "status_arm")
        if field in record and isinstance(record[field], str)
    ]
    # 忽略未参与编译的架构（not_build），只要求被排期架构全部成功。
    scheduled = [status for status in observed if status not in COMPILE_NOT_SCHEDULED]
    return bool(scheduled) and all(status in COMPILE_SUCCEEDED for status in scheduled)


def select(kind: str, payload: Any) -> Dict[str, Any]:
    data = unwrap_selection_payload(payload)
    if data is None:
        return selection(None, "input must be a successful JSON envelope or data object")
    if kind == "latest-order":
        return select_latest(data.get("items"), "order")

    versions = data.get("versions")
    if not isinstance(versions, list):
        return selection(None, "version list is missing or invalid")
    successful = [record for record in versions if is_record(record) and is_successful_version(record)]
    if not successful:
        return selection(None, "version list has no successful version")
    return select_latest(successful, "successful version")


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {format_value(expected)}, got {format_value(actual)}")


def run_self_test() -> None:
    cases = [
        ("compile", {"status": "build_ok"}, "succeeded", "stop"),
        ("compile", {"detail": {"status": "build_failed"}}, "failed", "inspect_failure"),
        ("compile", {"detail": {"status": "building", "status_arm": "queue"}}, "pending", "poll"),
        # 单架构编译：x86 成功、arm 未参与，应判为成功而非继续轮询。
        ("compile", {"detail": {"status": "build_ok", "status_arm": "not_build"}}, "succeeded", "stop"),
        # arm 仍在编译时不受影响，继续轮询。
        ("compile", {"detail": {"status": "build_ok", "status_arm": "building"}}, "pending", "poll"),
        # 单架构失败仍优先判失败。
        ("compile", {"detail": {"status": "build_failed", "status_arm": "not_build"}}, "failed", "inspect_failure"),
        # 两个架构都未参与编译，属于异常，需人工检查。
        ("compile", {"detail": {"status": "not_build", "status_arm": "not_build"}}, "unknown", "inspect_failure"),
        ("compile", {"status": "new_state"}, "unknown", "inspect_failure"),
        ("compile", {"status": 123, "status_arm": "build_ok"}, "unknown", "inspect_failure"),
        ("compile", {"status": {"value": "build_ok"}}, "unknown", "inspect_failure"),
        ("order", {"order": {"status": 1}}, "succeeded", "stop"),
        ("order", {"order": {"status": 1.0}}, "succeeded", "stop"),
        ("order", {"order": {"status": 3}}, "canceled", "stop"),
        ("order", {"order": {"status": 7}}, "canceling", "stop"),
        ("order", {"order": {"status": 4}}, "pending", "poll"),
        ("order", {"status": 2}, "pending", "poll"),
        ("order", {"status": 99}, "unknown", "inspect_failure"),
        ("order", {"status": True}, "unknown", "inspect_failure"),
        ("step", {"step": {"type": 5}}, "needs_human", "confirm"),
        ("step", {"step": {"type": 8.0}}, "needs_human", "confirm"),
        ("step", {"step": {"type": 6, "task_status": 2}}, "failed", "inspect_failure"),
        ("step", {"step": {"type": 6, "task_status": 2.0}}, "failed", "inspect_failure"),
        ("step", {"step": {"type": 6, "task_info": {"status": 2}}}, "failed", "inspect_failure"),
        ("step", {"step": {"type": 6, "task_info": {"status": "2"}}}, "failed", "inspect_failure"),
        ("step", {"step": {"type": 6, "task_info": {"status": "--2"}}}, "unknown", "inspect_failure"),
        ("step", {"step": {"type": 6, "check_task_info": {"status": 4}}}, "failed", "inspect_failure"),
        ("step", {"step": {"type": 6, "check_task_info": {"status": "4"}}}, "failed", "inspect_failure"),
        ("step", {"step": {"type": 6, "check_task_status": 9}}, "failed", "inspect_failure"),
        ("step", {"step": {"type": 6, "check_task_info": {"status": "9"}}}, "failed", "inspect_failure"),
        ("step", {"type": 6, "task_status": []}, "unknown", "inspect_failure"),
        ("step", {"type": 6, "task_info": {"status": []}}, "unknown", "inspect_failure"),
        ("step", {"type": 6, "task_info": {"status": "failed"}}, "unknown", "inspect_failure"),
        ("step", {"type": None}, "unknown", "inspect_failure"),
    ]

    for index, (kind, payload, expected_state, expected_action) in enumerate(cases):
        actual = classify(kind, payload)
        assert_equal(actual["state"], expected_state, f"{index + 1}: state")
        assert_equal(actual["next_action"], expected_action, f"{index + 1}: next_action")

    for status in COMPILE_ACTIVE:
        assert_equal(classify("compile", {"status": status})["next_action"], "poll", f"compile {status}")
    # 仅 not_build（无任何被排期架构）不是进行中，应转人工检查而非轮询。
    assert_equal(
        classify("compile", {"status": "not_build"})["next_action"],
        "inspect_failure",
        "compile not_build alone",
    )
    for status in ORDER_PENDING:
        assert_equal(classify("order", {"status": status})["next_action"], "poll", f"order {status}")

    assert_equal(classify("step", {"type": 8})["requires_human"], True, "type 8 requires human")
    assert_equal(classify("step", {"type": 6, "check_task_status": 4})["next_action"], "inspect_failure", "check 4")
    assert_equal(classify("step", {"type": 6, "check_task_status": 5})["next_action"], "inspect_failure", "check 5")
    assert_equal(classify("step", {"type": 6, "check_task_status": 9})["next_action"], "inspect_failure", "check 9")
    assert_equal(classify("step", {"type": 6, "check_task_status": 7})["next_action"], "poll", "check warning")
    assert_equal(classify("step", {"type": 6, "task_status": 0})["next_action"], "poll", "task running")
    assert_equal(classify("step", {"type": True})["next_action"], "inspect_failure", "boolean type")
    assert_equal(
        classify(
            "compile",
            {
                "status": "success",
                "data": {"detail": {"status": "success", "status_arm": "success"}},
            },
        )["state"],
        "succeeded",
        "compile envelope",
    )
    assert_equal(
        classify("order", {"status": "partial", "data": {"order": {"status": 1}}})["next_action"],
        "inspect_failure",
        "non-success envelope",
    )
    print(f"{len(cases)} table cases passed")

    selection_cases = [
        ("latest-order", {"items": []}, None),
        ("latest-order", {"items": [{"id": 1, "create_time": "2026-01-01T00:00:00Z"}]}, 1),
        (
            "latest-order",
            {"items": [{"id": 1, "create_time": "2026-01-01T00:00:00Z"}, {"id": 2, "create_time": "2026-01-01T00:00:00Z"}]},
            None,
        ),
        ("latest-order", {"items": [{"id": 1}]}, None),
        (
            "latest-successful-version",
            {"versions": [{"version": "1.0.0.1", "status": "build_failed", "create_time": "2026-01-02T00:00:00Z"}]},
            None,
        ),
        (
            "latest-successful-version",
            {"versions": [{"version": "1.0.0.1", "status": "build_ok", "status_arm": "success", "create_time": "2026-01-02T00:00:00Z"}]},
            "1.0.0.1",
        ),
        (
            # 单架构版本：arm 未参与编译也算成功版本。
            "latest-successful-version",
            {"versions": [{"version": "1.0.0.14", "status": "build_ok", "status_arm": "not_build", "create_time": "2026-01-03T00:00:00Z"}]},
            "1.0.0.14",
        ),
        (
            "latest-successful-version",
            {"versions": [{"version": "1.0.0.1", "status": "new_state", "create_time": "2026-01-02T00:00:00Z"}]},
            None,
        ),
        (
            "latest-successful-version",
            {"versions": [{"version": "1.0.0.1", "status": "success", "create_time": "bad-time"}]},
            None,
        ),
        (
            "latest-successful-version",
            {"versions": [{"version": "1.0.0.1", "status": "success", "create_time": "2026-01-02T00:00:00Z"}, {"version": "1.0.0.2", "status": "build_ok", "create_time": "2026-01-02T00:00:00Z"}]},
            None,
        ),
    ]
    for index, (kind, payload, expected_identity) in enumerate(selection_cases):
        actual = select(kind, payload)["selected"]
        identity = None if actual is None else actual.get("id", actual.get("version"))
        assert_equal(identity, expected_identity, f"selection {index + 1}")
    print(f"{len(selection_cases)} selection cases passed")


def parse_args(argv: List[str]) -> Dict[str, Any]:
    if "--self-test" in argv:
        return {"self_test": True}
    if len(argv) == 0 or argv[0] not in {"classify", "select"}:
        usage()
    command = argv[0]
    try:
        kind_index = argv.index("--kind")
        kind = argv[kind_index + 1]
    except (ValueError, IndexError):
        usage()
    allowed_kinds = {"compile", "order", "step"} if command == "classify" else {"latest-order", "latest-successful-version"}
    if kind not in allowed_kinds:
        usage()
    return {"self_test": False, "command": command, "kind": kind}


def usage() -> None:
    print(
        "use classify --kind <compile|order|step>, select --kind <latest-order|latest-successful-version>, or --self-test",
        file=sys.stderr,
    )
    raise SystemExit(2)


def main() -> None:
    args = parse_args(sys.argv[1:])
    if args["self_test"]:
        run_self_test()
        return

    try:
        payload = json.loads(sys.stdin.read())
    except Exception as error:
        invalid = (
            inspect_failure(f"invalid JSON input: {error}")
            if args["command"] == "classify"
            else selection(None, f"invalid JSON input: {error}")
        )
        print(json.dumps(invalid, separators=(",", ":")))
        return

    result = classify(args["kind"], payload) if args["command"] == "classify" else select(args["kind"], payload)
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
