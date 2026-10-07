#!/usr/bin/env python3
"""Validate ByteFlow ASL-like workflow definitions with stable check IDs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "byteflow-workflow-validator/v1"
ALLOWED_STATE_TYPES = {"Task", "Choice", "Succeed", "Fail", "Pass", "Wait", "Parallel", "Map"}
TERMINAL_STATE_TYPES = {"Succeed", "Fail"}
WAIT_FIELDS = {"Seconds", "Timestamp", "SecondsPath", "TimestampPath"}
CHOICE_CONDITION_KEYS = {
    "And",
    "Or",
    "Not",
    "Variable",
    "StringEquals",
    "StringLessThan",
    "StringGreaterThan",
    "StringLessThanEquals",
    "StringGreaterThanEquals",
    "StringMatches",
    "NumericEquals",
    "NumericLessThan",
    "NumericGreaterThan",
    "NumericLessThanEquals",
    "NumericGreaterThanEquals",
    "BooleanEquals",
    "TimestampEquals",
    "TimestampLessThan",
    "TimestampGreaterThan",
    "TimestampLessThanEquals",
    "TimestampGreaterThanEquals",
    "IsNull",
    "IsPresent",
    "IsNumeric",
    "IsString",
    "IsBoolean",
    "IsTimestamp",
}
BYTEFLOW_RESOURCE_PATTERNS = (
    re.compile(
        r"^brn:byteflow:::[^/]+/stateMachine/[^/:]+(?:/[0-9]+)?:"
        r"startExecution\.(requestResponse|sync)$"
    ),
    re.compile(r"^brn:byteflow:::[^/]+/activity/[^/:]+:invoke$"),
)


def json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def load_workflow(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error_type": "READ_ERROR",
                    "file": path,
                    "message": str(exc),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        ) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error_type": "JSON_DECODE_ERROR",
                    "file": path,
                    "line": exc.lineno,
                    "column": exc.colno,
                    "message": exc.msg,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        ) from exc


def collect_targets(state: dict[str, Any]) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    if isinstance(state.get("Next"), str):
        targets.append(("Next", state["Next"]))
    if isinstance(state.get("Default"), str):
        targets.append(("Default", state["Default"]))
    choices = state.get("Choices")
    if isinstance(choices, list):
        for index, choice in enumerate(choices):
            if isinstance(choice, dict) and isinstance(choice.get("Next"), str):
                targets.append((f"Choices[{index}].Next", choice["Next"]))
    catchers = state.get("Catch")
    if isinstance(catchers, list):
        for index, catcher in enumerate(catchers):
            if isinstance(catcher, dict) and isinstance(catcher.get("Next"), str):
                targets.append((f"Catch[{index}].Next", catcher["Next"]))
    return targets


def workflow_summary(workflow: Any) -> dict[str, Any]:
    if not isinstance(workflow, dict):
        return {
            "start_at": None,
            "top_keys": [],
            "state_count": 0,
            "state_types": {},
            "transitions": [],
        }
    states = workflow.get("States")
    if not isinstance(states, dict):
        states = {}
    types = Counter()
    target_edges = []
    for name, state in states.items():
        if not isinstance(state, dict):
            continue
        state_type = state.get("Type", "<missing>")
        types[str(state_type)] += 1
        for field, target in collect_targets(state):
            target_edges.append({"from": name, "field": field, "to": target})
    return {
        "start_at": workflow.get("StartAt"),
        "top_keys": sorted(workflow.keys()),
        "state_count": len(states),
        "state_types": dict(sorted(types.items())),
        "transitions": target_edges,
    }


def explain_workflow(workflow: Any) -> dict[str, Any]:
    result = validate_workflow(workflow)
    result["states"] = []
    if not isinstance(workflow, dict):
        return result
    states = workflow.get("States") if isinstance(workflow.get("States"), dict) else {}
    for name, state in states.items():
        if not isinstance(state, dict):
            continue
        result["states"].append(
            {
                "name": name,
                "type": state.get("Type"),
                "resource": state.get("Resource"),
                "targets": collect_targets(state),
                "has_retry": bool(state.get("Retry")),
                "has_catch": bool(state.get("Catch")),
            }
        )
    return result


def _add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    path: str,
    status: str,
    severity: str,
    statement: str,
    message: str,
    **extra: Any,
) -> None:
    item = {
        "check_id": check_id,
        "message": message,
        "path": path,
        "severity": severity,
        "statement": statement,
        "status": status,
    }
    item.update(extra)
    checks.append(item)


def _path(parent: str, child: str) -> str:
    if not parent:
        return child
    if child.startswith("["):
        return f"{parent}{child}"
    if parent == "$":
        return f"$.{child}"
    return f"{parent}.{child}"


def _is_terminal_state(state: dict[str, Any]) -> bool:
    return state.get("Type") in TERMINAL_STATE_TYPES or state.get("End") is True


def _has_known_byteflow_resource_shape(resource: str) -> bool:
    return any(pattern.match(resource) for pattern in BYTEFLOW_RESOURCE_PATTERNS)


def _validate_transition_targets(
    checks: list[dict[str, Any]],
    state_name: str,
    state: dict[str, Any],
    states: dict[str, Any],
    state_path: str,
) -> None:
    missing = []
    for field, target in collect_targets(state):
        if target not in states:
            missing.append({"field": field, "target": target})
            _add_check(
                checks,
                "WF005_TRANSITION_TARGETS",
                _path(state_path, field),
                "fail",
                "error",
                "Every explicit transition target must name an existing state.",
                f"target state {target!r} does not exist",
                state=state_name,
                target=target,
            )
    if not missing:
        _add_check(
            checks,
            "WF005_TRANSITION_TARGETS",
            state_path,
            "pass",
            "info",
            "Every explicit transition target must name an existing state.",
            "all explicit transition targets exist",
            state=state_name,
        )


def _validate_termination(
    checks: list[dict[str, Any]],
    state_name: str,
    state: dict[str, Any],
    state_path: str,
) -> None:
    state_type = state.get("Type")
    has_next = "Next" in state
    has_end = state.get("End") is True
    if has_next and has_end:
        _add_check(
            checks,
            "WF006_TERMINATION",
            state_path,
            "fail",
            "error",
            "A state must choose either Next or End:true, not both.",
            "state defines both Next and End:true",
            state=state_name,
        )
        return
    if state_type in TERMINAL_STATE_TYPES:
        if has_next or "End" in state:
            _add_check(
                checks,
                "WF006_TERMINATION",
                state_path,
                "warn",
                "warning",
                "Succeed and Fail are terminal states and should not define Next or End.",
                "terminal state has an explicit transition or End field",
                state=state_name,
            )
        else:
            _add_check(
                checks,
                "WF006_TERMINATION",
                state_path,
                "pass",
                "info",
                "Succeed and Fail are terminal states and should not define Next or End.",
                "terminal state is well formed",
                state=state_name,
            )
        return
    if state_type == "Choice":
        if has_next or "End" in state:
            _add_check(
                checks,
                "WF006_TERMINATION",
                state_path,
                "fail",
                "error",
                "Choice states branch through Choices or Default rather than Next or End.",
                "Choice state should not define Next or End",
                state=state_name,
            )
        else:
            _add_check(
                checks,
                "WF006_TERMINATION",
                state_path,
                "pass",
                "info",
                "Choice states branch through Choices or Default rather than Next or End.",
                "Choice state uses branch-style termination",
                state=state_name,
            )
        return
    if has_next or has_end:
        _add_check(
            checks,
            "WF006_TERMINATION",
            state_path,
            "pass",
            "info",
            "Non-terminal states must define Next or End:true.",
            "state has a valid continuation or terminal marker",
            state=state_name,
        )
        return
    _add_check(
        checks,
        "WF006_TERMINATION",
        state_path,
        "fail",
        "error",
        "Non-terminal states must define Next or End:true.",
        "state has no Next and is not marked End:true",
        state=state_name,
    )


def _validate_choice(
    checks: list[dict[str, Any]],
    state_name: str,
    state: dict[str, Any],
    states: dict[str, Any],
    state_path: str,
) -> None:
    choices = state.get("Choices")
    default = state.get("Default")
    has_default = "Default" in state
    if has_default and (not isinstance(default, str) or not default):
        _add_check(
            checks,
            "WF007_CHOICE_SHAPE",
            _path(state_path, "Default"),
            "fail",
            "error",
            "Choice Default must be a non-empty state name when present.",
            "Default is not a non-empty string",
            state=state_name,
        )
    if not choices and not has_default:
        _add_check(
            checks,
            "WF007_CHOICE_SHAPE",
            state_path,
            "fail",
            "error",
            "Choice states must define Choices or Default.",
            "Choice state has neither Choices nor Default",
            state=state_name,
        )
        return
    if choices is not None and not isinstance(choices, list):
        _add_check(
            checks,
            "WF007_CHOICE_SHAPE",
            _path(state_path, "Choices"),
            "fail",
            "error",
            "Choices must be an array of branch objects.",
            "Choices is not an array",
            state=state_name,
        )
        return
    if choices is None:
        _add_check(
            checks,
            "WF007_CHOICE_SHAPE",
            state_path,
            "pass" if isinstance(default, str) and default else "fail",
            "info" if isinstance(default, str) and default else "error",
            "Choice states must define Choices or Default.",
            "Choice state falls back through Default"
            if isinstance(default, str) and default
            else "Choice state has no usable Choices or Default",
            state=state_name,
        )
        return
    if not choices:
        _add_check(
            checks,
            "WF007_CHOICE_SHAPE",
            _path(state_path, "Choices"),
            "fail",
            "error",
            "Choices must contain at least one branch when present.",
            "Choices is empty",
            state=state_name,
        )
        return
    for index, choice in enumerate(choices):
        choice_path = _path(state_path, f"Choices[{index}]")
        if not isinstance(choice, dict):
            _add_check(
                checks,
                "WF007_CHOICE_SHAPE",
                choice_path,
                "fail",
                "error",
                "Each Choice branch must be an object.",
                "Choice branch is not an object",
                state=state_name,
            )
            continue
        target = choice.get("Next")
        if not isinstance(target, str) or not target:
            _add_check(
                checks,
                "WF007_CHOICE_SHAPE",
                _path(choice_path, "Next"),
                "fail",
                "error",
                "Each Choice branch must define a non-empty Next target.",
                "Choice branch has no usable Next target",
                state=state_name,
            )
        elif target in states:
            _add_check(
                checks,
                "WF007_CHOICE_SHAPE",
                _path(choice_path, "Next"),
                "pass",
                "info",
                "Each Choice branch must define a non-empty Next target.",
                "Choice branch Next is usable",
                state=state_name,
                target=target,
            )
        if not any(key in choice for key in CHOICE_CONDITION_KEYS):
            _add_check(
                checks,
                "WF007_CHOICE_SHAPE",
                choice_path,
                "warn",
                "warning",
                "Each Choice branch should include an ASL condition expression.",
                "Choice branch has no recognized condition key",
                state=state_name,
            )


def _validate_task(
    checks: list[dict[str, Any]],
    state_name: str,
    state: dict[str, Any],
    state_path: str,
) -> None:
    resource = state.get("Resource")
    if not isinstance(resource, str) or not resource:
        _add_check(
            checks,
            "WF008_TASK_RESOURCE",
            _path(state_path, "Resource"),
            "fail",
            "error",
            "Task states must define a non-empty Resource string.",
            "Task Resource is missing or not a string",
            state=state_name,
        )
        return
    if _has_known_byteflow_resource_shape(resource):
        _add_check(
            checks,
            "WF008_TASK_RESOURCE",
            _path(state_path, "Resource"),
            "pass",
            "info",
            "Task Resource should use a recognized ByteFlow BRN shape when invoking ByteFlow.",
            "Task Resource matches a known ByteFlow BRN pattern",
            state=state_name,
        )
        return
    _add_check(
        checks,
        "WF008_TASK_RESOURCE",
        _path(state_path, "Resource"),
        "warn",
        "warning",
        "Task Resource should use a recognized ByteFlow BRN shape when invoking ByteFlow.",
        "Task Resource is syntactically present but not a known ByteFlow BRN pattern",
        state=state_name,
    )


def _validate_wait(
    checks: list[dict[str, Any]],
    state_name: str,
    state: dict[str, Any],
    state_path: str,
) -> None:
    present = sorted(field for field in WAIT_FIELDS if field in state)
    if len(present) != 1:
        _add_check(
            checks,
            "WF009_WAIT_SHAPE",
            state_path,
            "fail",
            "error",
            "Wait states must define exactly one wait field.",
            f"found {len(present)} wait fields: {present}",
            state=state_name,
        )
        return
    field = present[0]
    value = state[field]
    if field == "Seconds" and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
        _add_check(
            checks,
            "WF009_WAIT_SHAPE",
            _path(state_path, field),
            "fail",
            "error",
            "Seconds must be a non-negative integer.",
            "Seconds is not a non-negative integer",
            state=state_name,
        )
        return
    if field.endswith("Path") and (not isinstance(value, str) or not value):
        _add_check(
            checks,
            "WF009_WAIT_SHAPE",
            _path(state_path, field),
            "fail",
            "error",
            "Wait path fields must be non-empty strings.",
            f"{field} is not a non-empty string",
            state=state_name,
        )
        return
    _add_check(
        checks,
        "WF009_WAIT_SHAPE",
        state_path,
        "pass",
        "info",
        "Wait states must define exactly one usable wait field.",
        f"Wait state uses {field}",
        state=state_name,
    )


def _validate_retry_catch(
    checks: list[dict[str, Any]],
    state_name: str,
    state: dict[str, Any],
    state_path: str,
) -> None:
    for field in ("Retry", "Catch"):
        value = state.get(field)
        if value is None:
            continue
        field_path = _path(state_path, field)
        if not isinstance(value, list):
            _add_check(
                checks,
                "WF010_RETRY_CATCH_SHAPE",
                field_path,
                "fail",
                "error",
                "Retry and Catch must be arrays when present.",
                f"{field} is not an array",
                state=state_name,
            )
            continue
        for index, rule in enumerate(value):
            rule_path = _path(field_path, f"[{index}]")
            if not isinstance(rule, dict):
                _add_check(
                    checks,
                    "WF010_RETRY_CATCH_SHAPE",
                    rule_path,
                    "fail",
                    "error",
                    "Retry and Catch entries must be objects.",
                    f"{field} entry is not an object",
                    state=state_name,
                )
                continue
            error_equals = rule.get("ErrorEquals")
            if error_equals is not None and not isinstance(error_equals, list):
                _add_check(
                    checks,
                    "WF010_RETRY_CATCH_SHAPE",
                    _path(rule_path, "ErrorEquals"),
                    "fail",
                    "error",
                    "ErrorEquals must be an array when present.",
                    "ErrorEquals is not an array",
                    state=state_name,
                )
            if field == "Catch" and (not isinstance(rule.get("Next"), str) or not rule.get("Next")):
                _add_check(
                    checks,
                    "WF010_RETRY_CATCH_SHAPE",
                    _path(rule_path, "Next"),
                    "fail",
                    "error",
                    "Catch entries must define a non-empty Next target.",
                    "Catch entry has no usable Next target",
                    state=state_name,
                )


def _validate_parallel_or_map_nested(
    checks: list[dict[str, Any]],
    state_name: str,
    state: dict[str, Any],
    state_path: str,
) -> None:
    state_type = state.get("Type")
    if state_type == "Parallel":
        branches = state.get("Branches")
        if not isinstance(branches, list) or not branches:
            _add_check(
                checks,
                "WF011_PARALLEL_SHAPE",
                _path(state_path, "Branches"),
                "fail",
                "error",
                "Parallel states must define a non-empty Branches array.",
                "Branches is missing, empty, or not an array",
                state=state_name,
            )
            return
        _add_check(
            checks,
            "WF011_PARALLEL_SHAPE",
            _path(state_path, "Branches"),
            "pass",
            "info",
            "Parallel states must define a non-empty Branches array.",
            "Parallel state has branch definitions",
            state=state_name,
        )
        for index, branch in enumerate(branches):
            branch_path = _path(state_path, f"Branches[{index}]")
            nested = _validate_workflow(branch, branch_path)
            checks.extend(nested)
    if state_type == "Map":
        iterator = state.get("Iterator")
        item_processor = state.get("ItemProcessor")
        if not isinstance(iterator, dict) and not isinstance(item_processor, dict):
            _add_check(
                checks,
                "WF012_MAP_SHAPE",
                state_path,
                "fail",
                "error",
                "Map states must define Iterator or ItemProcessor as a nested workflow object.",
                "Map state has no usable Iterator or ItemProcessor",
                state=state_name,
            )
            return
        nested_workflow = iterator if isinstance(iterator, dict) else item_processor
        nested_name = "Iterator" if isinstance(iterator, dict) else "ItemProcessor"
        _add_check(
            checks,
            "WF012_MAP_SHAPE",
            _path(state_path, nested_name),
            "pass",
            "info",
            "Map states must define Iterator or ItemProcessor as a nested workflow object.",
            f"Map state uses {nested_name}",
            state=state_name,
        )
        nested = _validate_workflow(nested_workflow, _path(state_path, nested_name))
        checks.extend(nested)


def _validate_reachability(
    checks: list[dict[str, Any]],
    workflow: dict[str, Any],
    root_path: str,
    states: dict[str, Any],
) -> None:
    start_at = workflow.get("StartAt")
    if not isinstance(start_at, str) or start_at not in states:
        return
    graph = {name: [] for name in states}
    for name, state in states.items():
        if not isinstance(state, dict):
            continue
        for _, target in collect_targets(state):
            if target in states:
                graph[name].append(target)
    seen = set()
    queue = deque([start_at])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(target for target in graph.get(current, []) if target not in seen)
    unreachable = sorted(set(states) - seen)
    if unreachable:
        _add_check(
            checks,
            "WF013_REACHABILITY",
            _path(root_path, "States"),
            "warn",
            "warning",
            "All top-level states should be reachable from StartAt.",
            "some states are unreachable from StartAt",
            unreachable_states=unreachable,
        )
    else:
        _add_check(
            checks,
            "WF013_REACHABILITY",
            _path(root_path, "States"),
            "pass",
            "info",
            "All top-level states should be reachable from StartAt.",
            "all states are reachable from StartAt",
        )
    if not any(isinstance(states[name], dict) and _is_terminal_state(states[name]) for name in seen):
        _add_check(
            checks,
            "WF014_TERMINAL_REACHABILITY",
            _path(root_path, "States"),
            "warn",
            "warning",
            "At least one terminal state should be reachable from StartAt.",
            "no reachable Succeed, Fail, or End:true state was found",
        )
    else:
        _add_check(
            checks,
            "WF014_TERMINAL_REACHABILITY",
            _path(root_path, "States"),
            "pass",
            "info",
            "At least one terminal state should be reachable from StartAt.",
            "a terminal state is reachable from StartAt",
        )


def _validate_workflow(workflow: Any, root_path: str) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if not isinstance(workflow, dict):
        _add_check(
            checks,
            "WF001_JSON_OBJECT",
            root_path,
            "fail",
            "error",
            "Workflow root must be a JSON object.",
            "workflow root is not an object",
        )
        return checks
    _add_check(
        checks,
        "WF001_JSON_OBJECT",
        root_path,
        "pass",
        "info",
        "Workflow root must be a JSON object.",
        "workflow root is an object",
    )

    states = workflow.get("States")
    start_at = workflow.get("StartAt")
    if not isinstance(start_at, str) or not start_at:
        _add_check(
            checks,
            "WF002_REQUIRED_TOP_LEVEL",
            _path(root_path, "StartAt"),
            "fail",
            "error",
            "StartAt must be a non-empty string.",
            "StartAt is missing or not a non-empty string",
        )
    else:
        _add_check(
            checks,
            "WF002_REQUIRED_TOP_LEVEL",
            _path(root_path, "StartAt"),
            "pass",
            "info",
            "StartAt must be a non-empty string.",
            "StartAt is present",
        )
    if not isinstance(states, dict) or not states:
        _add_check(
            checks,
            "WF002_REQUIRED_TOP_LEVEL",
            _path(root_path, "States"),
            "fail",
            "error",
            "States must be a non-empty object.",
            "States is missing, empty, or not an object",
        )
        return checks
    _add_check(
        checks,
        "WF002_REQUIRED_TOP_LEVEL",
        _path(root_path, "States"),
        "pass",
        "info",
        "States must be a non-empty object.",
        "States is present",
    )
    if isinstance(start_at, str) and start_at:
        if start_at in states:
            _add_check(
                checks,
                "WF003_STARTAT_TARGET",
                _path(root_path, "StartAt"),
                "pass",
                "info",
                "StartAt must name an existing state.",
                "StartAt target exists",
                target=start_at,
            )
        else:
            _add_check(
                checks,
                "WF003_STARTAT_TARGET",
                _path(root_path, "StartAt"),
                "fail",
                "error",
                "StartAt must name an existing state.",
                f"StartAt target {start_at!r} does not exist",
                target=start_at,
            )

    for name, state in states.items():
        state_path = _path(_path(root_path, "States"), str(name))
        if not isinstance(state, dict):
            _add_check(
                checks,
                "WF004_STATE_OBJECT_AND_TYPE",
                state_path,
                "fail",
                "error",
                "Each state must be an object with a supported Type.",
                "state is not an object",
                state=name,
            )
            continue
        state_type = state.get("Type")
        if state_type not in ALLOWED_STATE_TYPES:
            _add_check(
                checks,
                "WF004_STATE_OBJECT_AND_TYPE",
                _path(state_path, "Type"),
                "fail",
                "error",
                "Each state must define a supported Type.",
                f"unsupported or missing state type: {state_type!r}",
                state=name,
            )
            continue
        _add_check(
            checks,
            "WF004_STATE_OBJECT_AND_TYPE",
            _path(state_path, "Type"),
            "pass",
            "info",
            "Each state must define a supported Type.",
            "state type is supported",
            state=name,
            state_type=state_type,
        )
        _validate_transition_targets(checks, str(name), state, states, state_path)
        _validate_termination(checks, str(name), state, state_path)
        _validate_retry_catch(checks, str(name), state, state_path)
        if state_type == "Choice":
            _validate_choice(checks, str(name), state, states, state_path)
        if state_type == "Task":
            _validate_task(checks, str(name), state, state_path)
        if state_type == "Wait":
            _validate_wait(checks, str(name), state, state_path)
        if state_type in {"Parallel", "Map"}:
            _validate_parallel_or_map_nested(checks, str(name), state, state_path)
    _validate_reachability(checks, workflow, root_path, states)
    return checks


def validate_workflow(workflow: Any, mode: str | None = None) -> dict[str, Any]:
    checks = _validate_workflow(workflow, "$")
    errors = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warn"]
    return {
        "ok": not errors,
        "schema_version": SCHEMA_VERSION,
        "mode": mode or "unspecified",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "summary": workflow_summary(workflow),
    }


def _print_summary(result: dict[str, Any]) -> None:
    print(
        "ok={ok} errors={error_count} warnings={warning_count} schema={schema_version}".format(
            **result
        )
    )
    for item in result["errors"] + result["warnings"]:
        print(f"{item['status'].upper()} {item['check_id']} {item['path']}: {item['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a ByteFlow workflow JSON definition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  python3 scripts/byteflow_workflow_validator.py --file workflow.json --output summary
  python3 scripts/byteflow_workflow_validator.py --file workflow.json --output json --explain
  python3 scripts/byteflow_workflow_validator.py --file workflow.json --strict-warnings
""",
    )
    parser.add_argument("--file", required=True, help="Workflow definition JSON file")
    parser.add_argument("--mode", choices=["standard", "express"], default=None)
    parser.add_argument("--output", choices=["json", "summary"], default="json")
    parser.add_argument("--strict-warnings", action="store_true", help="Exit non-zero on warnings")
    parser.add_argument("--explain", action="store_true", help="Include per-state explanation fields")
    args = parser.parse_args(argv)

    workflow = load_workflow(args.file)
    result = explain_workflow(workflow) if args.explain else validate_workflow(workflow, mode=args.mode)
    if args.explain:
        result["mode"] = args.mode or "unspecified"
    if args.output == "json":
        json_print(result)
    else:
        _print_summary(result)
    if result["error_count"] or (args.strict_warnings and result["warning_count"]):
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
