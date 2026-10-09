#!/usr/bin/env python3
"""按自定义时间范围只读下钻火山引擎账单：分页拉取、跨账期拼接、Decimal 对账并汇总。

时间范围是唯一口径。--start / --end 接受 YYYY-MM、YYYY-MM-DD、"YYYY-MM-DD HH:MM[:SS]"、
today、now，一律按东八区解释；月、日作为结束时间时包含整月、整天，精确到分钟的结束时间不包含该时刻。
--end 省略时为当前时间，晚于当前时间的部分截至查询时刻。整月、跨月日期段、精确到分钟的时段和
包含当天，只是不同的起止时间。

只调用 ve billing ListBillDetail、ve billing ListBillOverviewByProd 与 ve sts GetCallerIdentity，
不调用任何写操作，不读取或输出凭证。环境变量 VOLCANO_BILLING_NOW 可覆盖“当前时间”，仅用于测试和复现。

退出码：0 成功（对账差异也返回 0，见 reconciliation.ok）；1 参数错误；2 ve 调用或接口错误。
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

CST = dt.timezone(dt.timedelta(hours=8), "UTC+08:00")
NOW_ENV = "VOLCANO_BILLING_NOW"
ALLOWED_CALLS = frozenset(
    {
        ("billing", "ListBillDetail"),
        ("billing", "ListBillOverviewByProd"),
        ("sts", "GetCallerIdentity"),
    }
)
MAX_PAGE_SIZE = 300
# 同一账期内需要按天汇总的天数达到该值时，改为整账期查询后按 ExpenseDate 过滤，减少调用次数。
MONTH_FETCH_MIN_DAYS = 10
RECENT_DAYS = 2
GROUP_PERIOD_DAY = "1"
GROUP_PERIOD_DETAIL = "2"
GROUP_TERM_ITEM = "0"
GROUP_TERM_PRODUCT = "2"
CLOCK_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M")
EXPENSE_TIME_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
CSV_COLUMNS = (
    "ExpenseDate",
    "ExpenseBeginTime",
    "ExpenseEndTime",
    "Product",
    "ProductZh",
    "BillingMode",
    "BillCategory",
    "ConfigName",
    "Element",
    "InstanceNo",
    "InstanceName",
    "Project",
    "Region",
    "Count",
    "Unit",
    "PayableAmount",
    "Currency",
)

Money = Dict[str, Decimal]


class UsageError(Exception):
    """参数或时间范围不合法。"""


class VeError(Exception):
    """ve 调用失败或接口返回错误。"""


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


@dataclass(frozen=True)
class Filters:
    products: Tuple[str, ...] = ()
    owner_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class TimeRange:
    start: dt.datetime
    end: dt.datetime
    clamped: bool


@dataclass(frozen=True)
class DayPlan:
    day: dt.date
    kind: str  # full：整天；today：当天 0 点至今；partial：精确到分钟的部分时段
    window_start: dt.datetime
    window_end: dt.datetime

    @property
    def iso(self) -> str:
        return self.day.isoformat()

    @property
    def period(self) -> str:
        return self.day.strftime("%Y-%m")


@dataclass
class Collected:
    daily_products: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    daily_items: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    details: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    overview: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def current_time() -> dt.datetime:
    override = os.environ.get(NOW_ENV, "").strip()
    if not override:
        return dt.datetime.now(CST)
    try:
        value = dt.datetime.fromisoformat(override)
    except ValueError as exc:
        raise UsageError(f"{NOW_ENV} 不是 ISO 8601 时间：{override!r}") from exc
    return value.astimezone(CST) if value.tzinfo else value.replace(tzinfo=CST)


def start_of_day(day: dt.date) -> dt.datetime:
    return dt.datetime(day.year, day.month, day.day, tzinfo=CST)


def parse_bound(text: str, now: dt.datetime, is_end: bool) -> dt.datetime:
    value = text.strip()
    lowered = value.lower()
    if lowered == "now":
        return now
    if lowered == "today":
        today = start_of_day(now.date())
        return today + dt.timedelta(days=1) if is_end else today
    try:
        month = dt.datetime.strptime(value, "%Y-%m").date()
    except ValueError:
        pass
    else:
        if not is_end:
            return start_of_day(month)
        days = calendar.monthrange(month.year, month.month)[1]
        return start_of_day(month + dt.timedelta(days=days))
    try:
        day = dt.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        pass
    else:
        return start_of_day(day + dt.timedelta(days=1)) if is_end else start_of_day(day)
    for fmt in CLOCK_FORMATS:
        try:
            return dt.datetime.strptime(value, fmt).replace(tzinfo=CST)
        except ValueError:
            continue
    raise UsageError(
        f"无法解析时间 {text!r}；支持 YYYY-MM、YYYY-MM-DD、'YYYY-MM-DD HH:MM[:SS]'、today、now（东八区）"
    )


def resolve_range(start_text: str, end_text: Optional[str], now: dt.datetime) -> TimeRange:
    start = parse_bound(start_text, now, is_end=False)
    requested_end = parse_bound(end_text, now, is_end=True) if end_text else now
    end = min(requested_end, now)
    if start >= end:
        raise UsageError("开始时间必须早于结束时间，且早于当前时间（东八区）")
    return TimeRange(start=start, end=end, clamped=requested_end > now)


def plan_days(time_range: TimeRange, now: dt.datetime) -> List[DayPlan]:
    plans: List[DayPlan] = []
    day = time_range.start.date()
    last_day = (time_range.end - dt.timedelta(microseconds=1)).date()
    while day <= last_day:
        day_start = start_of_day(day)
        day_end = day_start + dt.timedelta(days=1)
        window_start = max(time_range.start, day_start)
        window_end = min(time_range.end, day_end)
        if window_start == day_start and window_end == day_end:
            kind = "full"
        elif day == now.date() and window_start == day_start and window_end == now:
            kind = "today"
        else:
            kind = "partial"
        plans.append(DayPlan(day=day, kind=kind, window_start=window_start, window_end=window_end))
        day += dt.timedelta(days=1)
    return plans


def period_fully_covered(period: str, plans: Sequence[DayPlan], now: dt.datetime) -> bool:
    """账期内 1 日至月末（当月为至今）都按整天或当天计入时，才能与产品总账做第三层核对。"""
    year, month = (int(part) for part in period.split("-"))
    first = dt.date(year, month, 1)
    last = min(dt.date(year, month, calendar.monthrange(year, month)[1]), now.date())
    kinds = {plan.day: plan.kind for plan in plans}
    day = first
    while day <= last:
        if kinds.get(day) not in ("full", "today"):
            return False
        day += dt.timedelta(days=1)
    return True


def decode_json_object(text: str) -> Optional[Dict[str, Any]]:
    """取输出中的第一个 JSON 对象，容忍其后附带的升级提示等文本。"""
    start = text.find("{")
    if start < 0:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(text, start)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


class VeClient:
    def __init__(self, profile: Optional[str], page_size: int) -> None:
        self.profile = profile
        self.page_size = page_size
        self.layers: List[Dict[str, Any]] = []
        self.show_progress = sys.stderr.isatty()

    def call(self, service: str, action: str, params: Sequence[str]) -> Dict[str, Any]:
        if (service, action) not in ALLOWED_CALLS:
            raise VeError(f"拒绝调用白名单之外的接口：{service} {action}")
        argv = ["ve", service, action, *params]
        if self.profile:
            argv += ["--profile", self.profile]
        try:
            completed = subprocess.run(argv, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            raise VeError("未找到 ve；先按 bytedance-volcano 主 SKILL 安装 ve 并完成登录") from None
        payload = decode_json_object(completed.stdout)
        if payload is None:
            lines = (completed.stderr or completed.stdout or "").strip().splitlines()
            reason = lines[-1] if lines else f"退出码 {completed.returncode}"
            raise VeError(f"ve {service} {action} 未返回 JSON：{reason[:300]}")
        metadata = payload.get("ResponseMetadata") or {}
        error = metadata.get("Error")
        if error:
            code = error.get("Code") or "Unknown"
            message = error.get("Message") or ""
            request_id = metadata.get("RequestId") or "-"
            raise VeError(f"ve {service} {action} 返回 {code}：{message}（RequestId {request_id}）")
        if completed.returncode != 0:
            raise VeError(f"ve {service} {action} 退出码 {completed.returncode}")
        return payload

    def account_id(self) -> str:
        payload = self.call("sts", "GetCallerIdentity", [])
        account = (payload.get("Result") or {}).get("AccountId")
        if not account:
            raise VeError("ve sts GetCallerIdentity 未返回 AccountId，先确认 ve 登录态")
        return str(account)

    def list_pages(self, action: str, params: Sequence[str], label: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        rows: List[Dict[str, Any]] = []
        warnings: List[str] = []
        request_ids: List[str] = []
        total: Optional[int] = None
        offset = 0
        pages = 0
        previous_first: Optional[str] = None
        while True:
            payload = self.call(
                "billing",
                action,
                [*params, "--Limit", str(self.page_size), "--NeedRecordNum", "1", "--Offset", str(offset)],
            )
            pages += 1
            request_id = (payload.get("ResponseMetadata") or {}).get("RequestId")
            if request_id:
                request_ids.append(str(request_id))
            result = payload.get("Result") or {}
            page = result.get("List") or []
            reported = result.get("Total")
            if isinstance(reported, int) and not isinstance(reported, bool) and reported >= 0:
                if total is not None and reported != total:
                    warnings.append(f"{label}：翻页期间 Total 从 {total} 变为 {reported}，账单可能仍在出账")
                total = reported
            if not page:
                if total is not None and len(rows) < total:
                    warnings.append(f"{label}：取到 {len(rows)} 条后出现空页，少于 Total={total}")
                break
            first = json.dumps(page[0], sort_keys=True, ensure_ascii=False)
            if first == previous_first:
                raise VeError(f"{label}：Offset={offset} 返回与上一页相同的数据，分页没有前进")
            previous_first = first
            rows.extend(page)
            if self.show_progress:
                expected = "?" if total is None else total
                print(f"[billing] {label} 第 {pages} 页，累计 {len(rows)}/{expected}", file=sys.stderr)
            if total is not None and len(rows) >= total:
                break
            if total is None and len(page) < self.page_size:
                break
            offset += len(page)
        if total is None:
            warnings.append(f"{label}：接口未返回有效 Total，按短页判定结束，完整性无法由 Total 证明")
        elif len(rows) > total:
            warnings.append(f"{label}：取回 {len(rows)} 条，多于 Total={total}")
        self.layers.append(
            {"label": label, "action": action, "rows": len(rows), "total": total, "pages": pages, "request_ids": request_ids}
        )
        return rows, warnings


def billing_params(period: str, extra: Sequence[str], filters: Filters) -> List[str]:
    params = ["--BillPeriod", period, *extra]
    for index, product in enumerate(filters.products, start=1):
        params += [f"--Product.{index}", product]
    for index, owner_id in enumerate(filters.owner_ids, start=1):
        params += [f"--OwnerID.{index}", owner_id]
    return params


def daily_args(group_term: str, expense_date: Optional[str] = None) -> List[str]:
    args = ["--GroupPeriod", GROUP_PERIOD_DAY, "--GroupTerm", group_term]
    return args + ["--ExpenseDate", expense_date] if expense_date else args


def collect(client: VeClient, plans: Sequence[DayPlan], now: dt.datetime, filters: Filters) -> Collected:
    data = Collected()
    by_period: Dict[str, List[DayPlan]] = defaultdict(list)
    for plan in plans:
        by_period[plan.period].append(plan)

    def fetch(action: str, params: List[str], label: str) -> List[Dict[str, Any]]:
        rows, warnings = client.list_pages(action, params, label)
        data.warnings.extend(warnings)
        return rows

    for period in sorted(by_period):
        period_plans = by_period[period]
        planned_dates = {plan.iso for plan in period_plans}
        daily_dates = {plan.iso for plan in period_plans if plan.kind != "partial"}
        product_dates = set()
        if len(daily_dates) >= MONTH_FETCH_MIN_DAYS:
            products = fetch(
                "ListBillDetail", billing_params(period, daily_args(GROUP_TERM_PRODUCT), filters), f"{period} 每日产品"
            )
            items = fetch("ListBillDetail", billing_params(period, daily_args(GROUP_TERM_ITEM), filters), f"{period} 每日计费项")
            for row in products:
                if row.get("ExpenseDate") in planned_dates:
                    data.daily_products[row["ExpenseDate"]].append(row)
            for row in items:
                if row.get("ExpenseDate") in daily_dates:
                    data.daily_items[row["ExpenseDate"]].append(row)
            product_dates = set(planned_dates)
        else:
            for iso in sorted(daily_dates):
                data.daily_products[iso].extend(
                    fetch("ListBillDetail", billing_params(period, daily_args(GROUP_TERM_PRODUCT, iso), filters), f"{iso} 每日产品")
                )
                data.daily_items[iso].extend(
                    fetch("ListBillDetail", billing_params(period, daily_args(GROUP_TERM_ITEM, iso), filters), f"{iso} 每日计费项")
                )
                product_dates.add(iso)
        for plan in period_plans:
            if plan.kind == "partial" and plan.iso not in product_dates:
                data.daily_products[plan.iso].extend(
                    fetch(
                        "ListBillDetail",
                        billing_params(period, daily_args(GROUP_TERM_PRODUCT, plan.iso), filters),
                        f"{plan.iso} 每日产品",
                    )
                )
            if plan.kind == "partial" or plan.day == now.date():
                data.details[plan.iso] = fetch(
                    "ListBillDetail",
                    billing_params(
                        period,
                        ["--GroupPeriod", GROUP_PERIOD_DETAIL, "--GroupTerm", GROUP_TERM_ITEM, "--ExpenseDate", plan.iso],
                        filters,
                    ),
                    f"{plan.iso} 明细",
                )
        if period_fully_covered(period, period_plans, now):
            data.overview[period] = fetch("ListBillOverviewByProd", billing_params(period, [], filters), f"{period} 产品总账")
    return data


def parse_amount(value: Any) -> Optional[Decimal]:
    if value is None or isinstance(value, bool) or str(value).strip() == "":
        return None
    try:
        amount = Decimal(str(value).strip())
    except InvalidOperation:
        return None
    return amount if amount.is_finite() else None


def currency_of(row: Dict[str, Any]) -> str:
    return str(row.get("Currency") or "UNKNOWN")


def field_text(row: Dict[str, Any], name: str) -> str:
    return str(row.get(name) or "")


def sum_money(rows: Iterable[Dict[str, Any]], field_name: str = "PayableAmount") -> Tuple[Money, int]:
    totals: Money = defaultdict(Decimal)
    invalid = 0
    for row in rows:
        amount = parse_amount(row.get(field_name))
        if amount is None:
            invalid += 1
            continue
        totals[currency_of(row)] += amount
    return dict(totals), invalid


def money_json(money: Money) -> Dict[str, str]:
    return {currency: str(money[currency]) for currency in sorted(money)}


def money_text(money: Money) -> str:
    return "，".join(f"{currency} {money[currency]}" for currency in sorted(money)) or "0"


def money_weight(money: Money) -> Decimal:
    return sum(money.values(), Decimal(0))


def parse_expense_time(value: Any) -> Optional[dt.datetime]:
    if not value:
        return None
    text = str(value).strip()
    for fmt in EXPENSE_TIME_FORMATS:
        try:
            return dt.datetime.strptime(text, fmt).replace(tzinfo=CST)
        except ValueError:
            continue
    return None


def classify_detail(row: Dict[str, Any], window_start: dt.datetime, window_end: dt.datetime) -> str:
    begin = parse_expense_time(row.get("ExpenseBeginTime"))
    end = parse_expense_time(row.get("ExpenseEndTime"))
    if begin is None or end is None or end < begin:
        return "boundary"
    if begin == end:
        return "inside" if window_start <= begin < window_end else "outside"
    if end <= window_start or begin >= window_end:
        return "outside"
    if begin >= window_start and end <= window_end:
        return "inside"
    return "boundary"


def compare(scope: str, name: str, left: Money, right: Money, in_progress: bool) -> Dict[str, Any]:
    currencies = sorted(set(left) | set(right))
    diff = {currency: left.get(currency, Decimal(0)) - right.get(currency, Decimal(0)) for currency in currencies}
    matched = all(value == 0 for value in diff.values())
    return {
        "scope": scope,
        "check": name,
        "left": money_json(left),
        "right": money_json(right),
        "diff": money_json({currency: value for currency, value in diff.items() if value != 0}),
        "status": "match" if matched else "mismatch",
        "in_progress": in_progress,
    }


def ranked(groups: Dict[Tuple[str, ...], Money], keys: Sequence[str], limit: Optional[int]) -> List[Dict[str, Any]]:
    entries = sorted(groups.items(), key=lambda item: (-money_weight(item[1]), item[0]))
    if limit is not None:
        entries = entries[:limit]
    return [{**dict(zip(keys, key)), "payable": money_json(money)} for key, money in entries]


def summarize(
    account_id: str,
    time_range: TimeRange,
    plans: Sequence[DayPlan],
    data: Collected,
    client: VeClient,
    filters: Filters,
    now: dt.datetime,
    top: int,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    warnings = list(data.warnings)
    included: List[Dict[str, Any]] = []
    boundary_rows: List[Dict[str, Any]] = []
    checks: List[Dict[str, Any]] = []
    by_day: List[Dict[str, Any]] = []
    invalid_amounts = 0
    today = now.date()

    for plan in plans:
        product_sum, invalid_product = sum_money(data.daily_products.get(plan.iso, []))
        invalid_amounts += invalid_product
        entry: Dict[str, Any] = {"date": plan.iso, "kind": plan.kind}
        if plan.kind == "partial":
            details = data.details.get(plan.iso, [])
            placement = [(row, classify_detail(row, plan.window_start, plan.window_end)) for row in details]
            inside = [row for row, position in placement if position == "inside"]
            crossing = [row for row, position in placement if position == "boundary"]
            detail_sum, invalid_detail = sum_money(details)
            invalid_amounts += invalid_detail
            checks.append(compare(plan.iso, "全天明细 vs 每日产品", detail_sum, product_sum, plan.day == today))
            day_rows = inside
            boundary_rows.extend(crossing)
            crossing_sum, _ = sum_money(crossing)
            entry.update(
                {
                    "window": [plan.window_start.strftime("%Y-%m-%d %H:%M:%S"), plan.window_end.strftime("%Y-%m-%d %H:%M:%S")],
                    "source": "detail",
                    "boundary_rows": len(crossing),
                    "boundary_payable": money_json(crossing_sum),
                }
            )
        else:
            day_rows = data.daily_items.get(plan.iso, [])
            item_sum, invalid_item = sum_money(day_rows)
            invalid_amounts += invalid_item
            checks.append(compare(plan.iso, "每日产品 vs 每日计费项", product_sum, item_sum, plan.kind == "today"))
            if plan.kind == "today":
                detail_sum, _ = sum_money(data.details.get(plan.iso, []))
                checks.append(compare(plan.iso, "当天明细 vs 每日产品", detail_sum, product_sum, True))
            entry["source"] = "daily"
        day_sum, _ = sum_money(day_rows)
        entry["payable"] = money_json(day_sum)
        entry["complete"] = plan.kind == "full"
        by_day.append(entry)
        included.extend(day_rows)

    for period, rows in sorted(data.overview.items()):
        overview_sum, invalid_overview = sum_money(rows)
        invalid_amounts += invalid_overview
        period_products: List[Dict[str, Any]] = []
        for plan in plans:
            if plan.period == period:
                period_products.extend(data.daily_products.get(plan.iso, []))
        product_sum, _ = sum_money(period_products)
        current = period == now.strftime("%Y-%m")
        checks.append(compare(period, "产品总账 vs 每日产品", overview_sum, product_sum, current))

    total, _ = sum_money(included)
    by_product: Dict[Tuple[str, ...], Money] = defaultdict(lambda: defaultdict(Decimal))
    by_project: Dict[Tuple[str, ...], Money] = defaultdict(lambda: defaultdict(Decimal))
    by_mode: Dict[Tuple[str, ...], Money] = defaultdict(lambda: defaultdict(Decimal))
    by_item: Dict[Tuple[str, ...], Money] = defaultdict(lambda: defaultdict(Decimal))
    item_counts: Dict[Tuple[str, ...], Decimal] = defaultdict(Decimal)
    by_instance: Dict[Tuple[str, ...], Money] = defaultdict(lambda: defaultdict(Decimal))
    settlement = Counter()
    paid, _ = sum_money(included, "PaidAmount")
    unpaid, _ = sum_money(included, "UnpaidAmount")
    for row in included:
        amount = parse_amount(row.get("PayableAmount"))
        if amount is None:
            continue
        currency = currency_of(row)
        product = field_text(row, "Product")
        by_product[(product, field_text(row, "ProductZh"))][currency] += amount
        by_project[(field_text(row, "Project") or "-",)][currency] += amount
        by_mode[(field_text(row, "BillingMode"),)][currency] += amount
        item_key = (product, field_text(row, "ConfigName"), field_text(row, "Element"), field_text(row, "Unit"))
        by_item[item_key][currency] += amount
        count = parse_amount(row.get("Count"))
        if count is not None:
            item_counts[item_key] += count
        instance_key = (
            product,
            field_text(row, "InstanceNo"),
            field_text(row, "InstanceName"),
            field_text(row, "Project"),
            field_text(row, "Region"),
        )
        by_instance[instance_key][currency] += amount
        settlement[field_text(row, "SettlementType") or "-"] += 1

    top_items = ranked(by_item, ("product", "config_name", "element", "unit"), top)
    for entry in top_items:
        key = (entry["product"], entry["config_name"], entry["element"], entry["unit"])
        entry["count"] = str(item_counts[key]) if key in item_counts else None

    as_of = None
    if any(plan.day == today for plan in plans):
        end_times = [
            str(row.get("ExpenseEndTime"))
            for row in data.details.get(today.isoformat(), [])
            if parse_expense_time(row.get("ExpenseEndTime"))
        ]
        as_of = max(end_times) if end_times else None
        if as_of:
            warnings.append(f"范围包含当天：已出账数据截至 {as_of}（查询时刻 {now:%Y-%m-%d %H:%M:%S}），当天费用仍会增加")
        else:
            warnings.append("范围包含当天，但当天暂无已出账明细")
    if time_range.clamped:
        warnings.append(f"结束时间晚于当前时间，已截至查询时刻 {now:%Y-%m-%d %H:%M:%S}")
    periods = sorted({plan.period for plan in plans})
    if now.strftime("%Y-%m") in periods:
        warnings.append(f"{now:%Y-%m} 为当前账期，只包含已出账部分")
    previous_period = (start_of_day(now.date().replace(day=1)) - dt.timedelta(days=1)).strftime("%Y-%m")
    if previous_period in periods and now < start_of_day(now.date().replace(day=2)) + dt.timedelta(hours=12):
        warnings.append(f"{previous_period} 账单在本月第 2 个自然日 12:00 前可能尚未完整出账")
    recent = [plan.iso for plan in plans if 0 < (today - plan.day).days <= RECENT_DAYS]
    if recent:
        warnings.append(f"最近 {RECENT_DAYS} 天（{', '.join(recent)}）可能仍有延迟出账，复查时以新查询为准")
    if boundary_rows:
        crossing_total, _ = sum_money(boundary_rows)
        warnings.append(
            f"部分时段按明细起止时间计入；{len(boundary_rows)} 条明细跨越时段边界、无法拆分，未计入合计（应付 {money_text(crossing_total)}）"
        )
    if invalid_amounts:
        warnings.append(f"{invalid_amounts} 条记录的 PayableAmount 无法解析，未计入合计")
    if len(total) > 1:
        warnings.append("包含多个币种，合计和排行按币种分别给出，不能直接相加")

    settled_checks = [check for check in checks if not check["in_progress"]]
    pending = [check for check in checks if check["in_progress"] and check["status"] == "mismatch"]
    for check in pending:
        diff = money_text({currency: Decimal(value) for currency, value in check["diff"].items()})
        warnings.append(f"{check['scope']} {check['check']} 暂不一致（差额 {diff}）：出账仍在进行，各层刷新不同步，稍后重跑通常会收敛")
    summary = {
        "account_id": account_id,
        "timezone": "UTC+08:00",
        "query_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "range": {
            "start": time_range.start.strftime("%Y-%m-%d %H:%M:%S"),
            "end": time_range.end.strftime("%Y-%m-%d %H:%M:%S"),
            "end_clamped_to_now": time_range.clamped,
            "bill_periods": periods,
            "days": len(plans),
        },
        "as_of": as_of,
        "complete": all(plan.kind == "full" for plan in plans) and not boundary_rows,
        "filters": {"products": list(filters.products), "owner_ids": list(filters.owner_ids)},
        "totals": {"payable": money_json(total), "paid": money_json(paid), "unpaid": money_json(unpaid)},
        "reconciliation": {
            "ok": all(check["status"] == "match" for check in settled_checks),
            "checks": checks,
        },
        "by_day": by_day,
        "by_product": ranked(by_product, ("product", "product_zh"), None),
        "by_project": ranked(by_project, ("project",), None),
        "by_billing_mode": ranked(by_mode, ("billing_mode",), None),
        "top_charge_items": top_items,
        "top_instances": ranked(by_instance, ("product", "instance_no", "instance_name", "project", "region"), top),
        "settlement_types": dict(settlement),
        "layers": client.layers,
        "warnings": warnings,
    }
    return summary, included, boundary_rows


def render_text(summary: Dict[str, Any]) -> str:
    def money(value: Dict[str, str]) -> str:
        return "，".join(f"{currency} {amount}" for currency, amount in value.items()) or "0"

    lines = [
        f"火山账号 {summary['account_id']} 账单（东八区，查询时刻 {summary['query_time']}）",
        f"范围：{summary['range']['start']} ~ {summary['range']['end']}，账期 {', '.join(summary['range']['bill_periods'])}",
    ]
    if summary["as_of"]:
        lines.append(f"已出账截至：{summary['as_of']}")
    lines.append(f"应付合计：{money(summary['totals']['payable'])}")
    checks = summary["reconciliation"]["checks"]
    settled = [check for check in checks if not check["in_progress"]]
    pending = [check for check in checks if check["in_progress"]]
    settled_mismatch = [check for check in settled if check["status"] == "mismatch"]
    pending_mismatch = [check for check in pending if check["status"] == "mismatch"]
    if settled:
        verdict = "全部一致" if not settled_mismatch else "存在未解释差异"
        lines.append(f"对账（已出账完整的天/账期）：{len(settled) - len(settled_mismatch)}/{len(settled)} 项一致，{verdict}")
    if pending:
        lines.append(f"出账进行中（当天/当前账期）：{len(pending) - len(pending_mismatch)}/{len(pending)} 项暂时一致")
    for check in settled_mismatch + pending_mismatch:
        lines.append(f"  - {check['scope']} {check['check']}：{money(check['left'])} vs {money(check['right'])}")
    lines.append("按天：")
    for day in summary["by_day"]:
        extra = f"  窗口 {day['window'][0]} ~ {day['window'][1]}" if day.get("window") else ""
        lines.append(f"  {day['date']}  {day['kind']:<7} {money(day['payable'])}{extra}")
    sections = (
        ("按产品", "by_product", ("product_zh", "product")),
        ("按项目", "by_project", ("project",)),
        ("计费项", "top_charge_items", ("product", "config_name", "element")),
        ("实例", "top_instances", ("product", "instance_name", "instance_no", "project")),
    )
    for title, key, columns in sections:
        lines.append(f"{title}：")
        for entry in summary[key]:
            label = " / ".join(str(entry.get(column) or "-") for column in columns)
            lines.append(f"  {money(entry['payable'])}  {label}")
    if summary["warnings"]:
        lines.append("提示：")
        lines.extend(f"  - {warning}" for warning in summary["warnings"])
    return "\n".join(lines)


def write_rows(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})


def write_outputs(out_dir: str, summary: Dict[str, Any], included: Sequence[Dict[str, Any]], boundary: Sequence[Dict[str, Any]]) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    write_rows(os.path.join(out_dir, "items.csv"), included)
    if boundary:
        write_rows(os.path.join(out_dir, "boundary.csv"), boundary)


def build_parser() -> Parser:
    parser = Parser(description="按自定义时间范围只读下钻火山引擎账单，分页、跨账期拼接并用 Decimal 对账（东八区）。")
    parser.add_argument("--start", required=True, help="开始时间：YYYY-MM、YYYY-MM-DD、'YYYY-MM-DD HH:MM[:SS]'、today、now")
    parser.add_argument("--end", help="结束时间，格式同上；月、日包含整月、整天；省略为当前时间")
    parser.add_argument("--product", action="append", default=[], help="只看指定产品编码（Product），可重复")
    parser.add_argument("--owner-id", action="append", default=[], help="财务托管场景只看指定 Owner 账号 ID，可重复")
    parser.add_argument("--profile", help="ve profile；仅在用户明确指定时传入")
    parser.add_argument("--top", type=int, default=10, help="计费项与实例排行长度，默认 10")
    parser.add_argument("--output", choices=("json", "text"), default="json", help="输出格式，默认 json")
    parser.add_argument("--out-dir", help="把 summary.json、items.csv（及 boundary.csv）写入该目录")
    parser.add_argument("--page-size", type=int, default=MAX_PAGE_SIZE, help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if not 1 <= args.page_size <= MAX_PAGE_SIZE:
            raise UsageError(f"--page-size 需在 1-{MAX_PAGE_SIZE} 之间")
        if args.top < 1:
            raise UsageError("--top 需为正整数")
        owner_ids = tuple(owner.strip() for owner in args.owner_id)
        if any(not owner.isdigit() for owner in owner_ids):
            raise UsageError("--owner-id 需为数字账号 ID")
        products = tuple(product.strip() for product in args.product if product.strip())
        filters = Filters(products=products, owner_ids=owner_ids)
        now = current_time()
        time_range = resolve_range(args.start, args.end, now)
        plans = plan_days(time_range, now)
        client = VeClient(args.profile, args.page_size)
        account_id = client.account_id()
        data = collect(client, plans, now, filters)
        summary, included, boundary = summarize(account_id, time_range, plans, data, client, filters, now, args.top)
        if args.out_dir:
            write_outputs(args.out_dir, summary, included, boundary)
    except UsageError as exc:
        print(f"参数错误：{exc}", file=sys.stderr)
        return 1
    except VeError as exc:
        print(f"查询失败：{exc}", file=sys.stderr)
        return 2
    if args.output == "text":
        print(render_text(summary))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
