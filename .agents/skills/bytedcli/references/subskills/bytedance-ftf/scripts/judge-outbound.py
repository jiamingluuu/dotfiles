#!/usr/bin/env python3
"""执行已核实的 Outbound 返回契约；只读本地 JSON，不访问网络。"""

import argparse
import json
import math
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

VERSION = "ftf-outbound/v1.3"
MISSING = object()
HTTP_PROTOCOLS = {"http", "https"}
FIELD = re.compile(r"[a-z][a-z0-9_]*\Z")


def scalar(value):
    return value is None or type(value) in (str, int, Decimal, bool)


def same_type(left, right):
    return (type(left) is type(right)
            or (type(left) in (int, Decimal) and type(right) in (int, Decimal)))


def same(left, right):
    return same_type(left, right) and left == right


def validate_rules(rules):
    if not isinstance(rules, list):
        raise ValueError("规则必须是数组")
    allowed = {"match", "adapter_version", "source", "required_signals",
               "success_values", "sentinels", "status_codes", "batch_mode",
               "top_error_policy", "inspect_error_types"}
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) - allowed:
            raise ValueError("规则包含未定义字段")
        match = rule.get("match", {})
        if (not isinstance(match, dict) or not match
                or set(match) - {"service", "component", "method", "protocol", "method_family"}
                or any(not isinstance(v, str) or not v.strip() or v != v.strip()
                       for v in match.values())):
            raise ValueError("规则匹配条件无效")
        if (match.get("protocol", "").lower() in HTTP_PROTOCOLS
                and match["protocol"] not in HTTP_PROTOCOLS):
            raise ValueError("HTTP 协议标识必须归一为小写")
        if not (set(match) == {"service", "method"}
                or set(match) == {"component", "method"}
                or set(match) == {"protocol", "method_family"}
                or set(match) == {"protocol"}):
            raise ValueError("规则必须具有明确匹配范围")
        version = rule.get("adapter_version", "")
        if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9._/-]{1,80}", version):
            raise ValueError("规则版本无效")
        if not isinstance(rule.get("source"), str) or not rule["source"].strip():
            raise ValueError("规则缺少契约来源")
        required = rule.get("required_signals")
        if (not isinstance(required, list) or not required
                or any(not isinstance(f, str) or not FIELD.fullmatch(f) for f in required)
                or len(set(required)) != len(required)):
            raise ValueError("规则必须声明所需信号")
        checks = rule.get("success_values", {})
        if not isinstance(checks, dict):
            raise ValueError("成功集合必须是对象")
        for field, check in checks.items():
            if (field not in required or field in {"error", "status_code", "stream_complete"}
                    or not isinstance(check, dict) or set(check) != {"layer", "values"}
                    or check["layer"] not in ("protocol", "business", "method")
                    or not isinstance(check["values"], list) or not check["values"]
                    or any(not scalar(v) for v in check["values"])):
                raise ValueError("成功集合无效")
        if set(required) - {"error", "status_code", "stream_complete"} - set(checks):
            raise ValueError("每个自定义信号都需要成功集合")
        sentinels = rule.get("sentinels", {})
        if (not isinstance(sentinels, dict)
                or any(not isinstance(k, str) or not k.strip() or k != k.strip()
                       or v not in ("MISS", "EMPTY", "END", "ALREADY_EXISTS")
                       for k, v in sentinels.items())
                or (sentinels and "method" not in match)):
            raise ValueError("正常哨兵必须限定具体方法")
        if sentinels and "error" not in required:
            raise ValueError("正常哨兵必须声明 error 为必需信号")
        codes = rule.get("status_codes", list(range(200, 300)))
        if (not isinstance(codes, list) or not codes
                or any(type(c) is not int or not 100 <= c <= 599 for c in codes)):
            raise ValueError("HTTP 成功状态集合无效")
        if "status_codes" in rule and "status_code" not in required:
            raise ValueError("HTTP 成功集合必须声明 status_code 为必需信号")
        mode = rule.get("batch_mode", "NONE")
        policy = rule.get("top_error_policy")
        if mode not in ("NONE", "ITEMS", "WHOLE_RESULT"):
            raise ValueError("批量模式无效")
        if mode != "NONE" and "error" not in required:
            raise ValueError("批量必须检查顶层 error")
        if ((mode == "ITEMS" and policy not in ("INVALIDATE_ITEMS", "INSPECT_ITEMS"))
                or (mode == "WHOLE_RESULT" and policy != "WHOLE_RESULT")
                or (mode == "NONE" and policy is not None)):
            raise ValueError("批量顶层策略无效")
        inspect_types = rule.get("inspect_error_types", [])
        if (not isinstance(inspect_types, list)
                or any(not isinstance(t, str) or not t.strip() or t != t.strip()
                       for t in inspect_types)
                or len(set(inspect_types)) != len(inspect_types)
                or (policy == "INSPECT_ITEMS" and not inspect_types)
                or (policy != "INSPECT_ITEMS" and inspect_types)):
            raise ValueError("逐项检查必须明确允许并存的错误类型")


def select_rule(record, rules):
    candidates = []
    for rule in rules:
        match = rule["match"]
        if all(record.get(key) == value for key, value in match.items()):
            rank = (4 if "service" in match else 3 if "component" in match
                    else 2 if "method_family" in match else 1)
            candidates.append((rank, rule))
    if not candidates:
        return {}
    best = max(rank for rank, _ in candidates)
    matched = [rule for rank, rule in candidates if rank == best]
    if len(matched) != 1:
        raise ValueError("同优先级规则冲突")
    return matched[0]


def judge(record, rules, depth=0):
    fields = []
    rule = {}

    def result(outcome, reason, layer="none", **extra):
        operation = record.get("operation") if isinstance(record, dict) else None
        effect = "NOT_APPLICABLE" if operation == "READ" else "UNKNOWN"
        if operation == "WRITE" and reason in {"TIMEOUT", "CANCELED", "CALL_ERROR"}:
            effect = "POSSIBLE"
        return {"outcome": outcome, "reason_code": reason, "failure_layer": layer,
                "evidence_fields": sorted(set(fields)), "side_effect": effect,
                "adapter_version": VERSION + ("/" + rule["adapter_version"] if rule else ""),
                **extra}

    if not isinstance(record, dict) or depth > 8:
        return result("UNKNOWN", "INVALID_INPUT", "observer")
    if "observation" in record:
        fields.append("$.observation")
    if record.get("observation") != "COMPLETE":
        return result("UNKNOWN", "OBSERVATION_INCOMPLETE", "observer")
    if (record.get("call_kind") not in ("SYNC", "ASYNC", "STREAM")
            or not isinstance(record.get("protocol"), str) or not record["protocol"].strip()
            or record["protocol"] != record["protocol"].strip()
            or (record["protocol"].lower() in HTTP_PROTOCOLS
                and record["protocol"] not in HTTP_PROTOCOLS)
            or not isinstance(record.get("signals"), dict)
            or any(not isinstance(record[key], str) or not record[key].strip()
                   or record[key] != record[key].strip()
                   for key in ("component", "service", "method", "method_family") if key in record)
            or ("operation" in record and record["operation"] not in ("READ", "WRITE"))):
        return result("UNKNOWN", "INVALID_INPUT", "observer")
    try:
        rule = select_rule(record, rules)
    except ValueError:
        return result("UNKNOWN", "RULE_CONFLICT", "observer")
    signals = record["signals"]
    kind = record["call_kind"]
    mode = rule.get("batch_mode", "NONE")
    uses_http_status = (record["protocol"] in HTTP_PROTOCOLS
                        or "status_code" in rule.get("required_signals", [])
                        or "status_codes" in rule)
    error = signals.get("error", MISSING)
    if error is not MISSING:
        fields.append("$.signals.error")
    if error is not MISSING and error is not None:
        if (not isinstance(error, dict) or set(error) - {"kind", "type"}
                or error.get("kind") not in ("ERROR", "TIMEOUT", "CANCELED")
                or ("type" in error
                    and (not isinstance(error["type"], str) or not error["type"].strip()
                         or error["type"] != error["type"].strip()))):
            return result("UNKNOWN", "INVALID_ERROR", "observer")
    if kind == "ASYNC":
        if error is MISSING:
            return result("UNKNOWN", "MISSING_ERROR", "observer",
                          missing_fields=["$.signals.error"])
        if error is not None:
            reason = error["kind"] if error["kind"] != "ERROR" else "CALL_ERROR"
            return result("FAILURE", reason, "invocation")
        return result("SUCCESS", "ASYNC_RETURN_OK")
    if error is not MISSING and error is not None and error["kind"] in {"TIMEOUT", "CANCELED"}:
        return result("FAILURE", error["kind"], "invocation")
    if mode == "NONE" and ("items" in record or "request_keys" in record):
        return result("UNKNOWN", "BATCH_RULE_REQUIRED", "observer")
    disposition = None
    if error is not MISSING and error is not None:
        disposition = rule.get("sentinels", {}).get(error.get("type"))
        inspect = (mode == "ITEMS" and rule.get("top_error_policy") == "INSPECT_ITEMS"
                   and error.get("type") in rule.get("inspect_error_types", []))
        if not disposition and not inspect:
            return result("FAILURE", "CALL_ERROR", "invocation")

    required = set(rule.get("required_signals", []))
    if not rule and record["protocol"] not in HTTP_PROTOCOLS:
        required.add("error")
    if uses_http_status:
        required.add("status_code")
    if kind == "STREAM":
        required.update({"error", "stream_complete"})
    fields.extend("$.signals." + field for field in required if field in signals)
    missing = sorted(required - signals.keys())
    if missing:
        return result("UNKNOWN", "MISSING_SIGNAL", "observer",
                      missing_fields=["$.signals." + field for field in missing])
    checks = rule.get("success_values", {})
    for field, check in checks.items():
        if not any(same_type(signals[field], v) for v in check["values"]):
            return result("UNKNOWN", "SIGNAL_TYPE_MISMATCH", "observer")
    status = signals.get("status_code", MISSING) if uses_http_status else MISSING
    if status is not MISSING:
        fields.append("$.signals.status_code")
        if type(status) is not int or not 100 <= status <= 599:
            return result("UNKNOWN", "INVALID_HTTP_STATUS", "observer")
    if "stream_complete" in required and type(signals["stream_complete"]) is not bool:
        return result("UNKNOWN", "INVALID_STREAM_END", "observer")

    summary = None
    if mode == "ITEMS":
        fields.extend("$." + field for field in ("request_keys", "items")
                      if field in record)
        keys, items = record.get("request_keys"), record.get("items")
        if (not isinstance(keys, list) or not keys
                or any(not isinstance(k, str) or not k for k in keys)
                or len(set(keys)) != len(keys) or not isinstance(items, list)
                or len(items) != len(keys)
                or any(not isinstance(i, dict) or not isinstance(i.get("key"), str) for i in items)
                or len({i["key"] for i in items}) != len(keys)
                or {i["key"] for i in items} != set(keys)):
            missing = ["$." + field for field in ("request_keys", "items")
                       if field not in record]
            extra = {"missing_fields": missing} if missing else {}
            return result("UNKNOWN", "ITEM_MAPPING_INVALID", "observer", **extra)
        judged = [judge(item, rules, depth + 1) for item in items]
        summary = {name.lower(): sum(r["outcome"] == name for r in judged)
                   for name in ("SUCCESS", "FAILURE", "UNKNOWN")}
        if summary["unknown"]:
            return result("UNKNOWN", "ITEM_EVIDENCE_INCOMPLETE", "observer", item_summary=summary)

    extra = {"item_summary": summary} if summary is not None else {}
    if disposition:
        extra["disposition"] = disposition
    if status is not MISSING and status not in rule.get("status_codes", range(200, 300)):
        return result("FAILURE", "HTTP_STATUS_FAILURE", "protocol", **extra)
    for field, check in checks.items():
        if not any(same(signals[field], expected) for expected in check["values"]):
            return result("FAILURE", "RULE_CONDITION_FAILED", check["layer"], **extra)
    if "stream_complete" in required and not signals["stream_complete"]:
        return result("UNKNOWN", "STREAM_END_MISSING", "observer", **extra)
    if summary is not None:
        if summary["success"]:
            return result("SUCCESS", "BATCH_HAS_SUCCESS", **extra)
        return result("FAILURE", "BATCH_ALL_FAILED", "method", **extra)
    if error is MISSING and status is MISSING and not checks:
        return result("UNKNOWN", "NO_DECISIVE_SIGNAL", "observer")
    return result("SUCCESS", "SENTINEL_OK" if disposition else "OK", **extra)


def load_json(path):
    def pairs(entries):
        obj = {}
        for key, value in entries:
            if key in obj:
                raise ValueError("JSON 存在重复字段")
            obj[key] = value
        return obj

    def invalid_constant(_):
        raise ValueError("JSON 数字无效")

    def finite_decimal(value):
        try:
            number = Decimal(value)
        except InvalidOperation as error:
            raise ValueError("JSON 数字无效") from error
        if not number.is_finite() or not math.isfinite(float(number)):
            raise ValueError("JSON 数字必须是有限值")
        return number

    content = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(content, object_pairs_hook=pairs, parse_constant=invalid_constant,
                      parse_float=finite_decimal)


def main():
    parser = argparse.ArgumentParser(description="根据已核实契约判定 FTF Outbound 结果")
    parser.add_argument("--input", required=True, help="输入 JSON 文件；- 表示标准输入")
    parser.add_argument("--rules", help="已核实的方法规则 JSON 数组文件")
    args = parser.parse_args()
    reason = "INVALID_RULES"
    try:
        rules = load_json(args.rules) if args.rules else []
        validate_rules(rules)
        reason = "INVALID_INPUT"
        data = load_json(args.input)
        output = [judge(record, rules) for record in data] if isinstance(data, list) else judge(data, rules)
        print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, UnicodeError, ValueError, RecursionError):
        # 不回显原始输入、解析器异常或文件内容，避免泄露敏感数据。
        print(json.dumps({"outcome": "UNKNOWN", "reason_code": reason,
                          "failure_layer": "observer", "evidence_fields": [],
                          "side_effect": "UNKNOWN",
                          "adapter_version": VERSION}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
