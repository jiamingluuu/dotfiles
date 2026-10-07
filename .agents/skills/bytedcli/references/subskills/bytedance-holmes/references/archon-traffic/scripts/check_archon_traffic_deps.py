#!/usr/bin/env python3
"""核对并改写业务仓库中 Archon 流量录制链路（TrustPress 录制 / TikDiff 回放共用）的依赖。

先探测仓库的依赖图形态（dep_graph / build_only / unsupported），再按形态给结论：

- `dep_graph`：根目录有 dep_graph.blade，走完整逻辑。默认每次运行都从远端解析各依赖当前
  分支 HEAD 作为目标值。内置的 reference_commit 只是参考水位，不是权威值：仅在拿不到远端
  HEAD（无网络 / 无权限 / ref 改名 / --offline）时用于兜底判定，且参考值本身可能因维护者
  未及时更新而过期 —— 这种结论必须原样带上输出里的醒目警告，提醒业务方自行确认是否需要
  拉到最新。`--apply` 对 dep_graph.blade 做逐行文本改写，保留原文件缩进与逗号风格。
- `build_only`：只有 BUILD、没有 dep_graph.blade。依赖没有 SHA pin，水位判定不适用，只做
  「存在性 + 分支名」体检，并禁用依赖改写。
- `unsupported`：两者都没有，输出 not_applicable 并软退出。

退出码：0 = 干净，1 = 还有待办 / 未达标，2 = 下限校验未通过（--verify），
3 = 用法或环境错误（形态不支持该操作、MR 链接非法、文件读不出来等）。
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Optional

DEP_GRAPH_FILENAME = "dep_graph.blade"
BUILD_FILENAME = "BUILD"
# 依赖图形态：dep_graph 走全量逻辑，build_only 只做体检，unsupported 直接软退出。
LAYOUT_DEP_GRAPH = "dep_graph"
LAYOUT_BUILD_ONLY = "build_only"
LAYOUT_UNSUPPORTED = "unsupported"
LEGACY_DEP = "data/trustpress_databus_lib"
ARCHON_DEP = "data/archon"
TRAFFIC_SINKER_DEP = "data-arch/traffic_sinker_lib"
MONGO_DEP = "bytedoc/mongo-cxx-driver"
BUILD_TARGET = "data-arch/traffic_sinker_lib:master@//data-arch/traffic_sinker_lib:traffic_sinker"
INJECTED_SINKER = "traffic_sinker::MultiSinker"
TRUSTPRESS_ANCHOR = "use_trustpress_external_storage"
# TrustPress handler is created during Archon / global / parent resource initialization.
# The registration call must therefore precede the first relevant qualified init call in
# the same startup source file; merely finding MultiSinker is not sufficient.
INIT_CALL_RE = re.compile(
    r"\b(?:[A-Za-z_]\w*::)*(?:ArchonContext|GlobalContext|[A-Za-z_]\w*ResourceManager)::init"
    r"\s*\([^;{}]*\)\s*;"
)
SINKER_ORDER_NOT_INJECTED = "not_injected"
SINKER_ORDER_BEFORE_INIT = "before_init"
SINKER_ORDER_AFTER_INIT = "after_init"
SINKER_ORDER_INIT_NOT_FOUND = "init_not_found"
TRUSTPRESS_FLAG = "archon_enable_trustpress"
TRUSTPRESS_ENV = "ARCHON_ENABLE_TRUSTPRESS"
TRUSTPRESS_CONF_KEYS = (
    "archon.diff.trustpress_maximum_strategy",
    "archon.diff.trustpress_maximum_queue_bytes",
    "archon.diff.trustpress_maximum_dump_in_minute",
    "archon.diff.trustpress_update_interval_in_ms",
)
MIN_ARCHON_VERSION = "1.114.18"
LS_REMOTE_TIMEOUT_SECONDS = 60
CLONE_TIMEOUT_SECONDS = 300
MR_URL_RE = re.compile(r"^https?://(?P<host>[^/]+)/(?P<repo>.+?)/merge_requests/(?P<iid>\d+)")
# Codebase 为每个 MR 维护这几个只读 ref，tmp-squash 最接近"MR 合入后的内容"。
MR_REF_CANDIDATES = ("tmp-squash", "tmp-merge", "head")

# 退出码：与「有待办」严格区分，用法 / 环境错误单独占一档，便于 CI 分流。
EXIT_OK = 0
EXIT_TODO = 1
EXIT_GATE_FAILED = 2
EXIT_USAGE = 3

# BUILD-only 仓的接线落点：启动脚本在 apps/<app>/run/real_run，录制参数在
# conf/<cluster>/server.conf 或 apps/<app>/conf/app.conf，所以 conf / 启动脚本
# 的搜索范围要同时覆盖这几类文件名。
RUN_SCRIPT_FILTERS = ["--include=*.sh", "--include=*run*", "--include=real_run"]
RUN_SCRIPT_PATTERNS = ("*.sh", "*run*", "real_run")
CONF_FILTERS = ["--include=*.conf"]
# 启动开关必须默认关闭：${ARCHON_ENABLE_TRUSTPRESS:-false}。
SWITCH_DEFAULT_OFF_RE = rf"\$\{{{TRUSTPRESS_ENV}:-(false|0)\}}"
SHELL_ASSIGNMENT_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_]\w*)=(.*)$")
SHELL_EXEC_RE = re.compile(r"(?:^|[;&|]\s*)exec\s+")
SHELL_EXEC_PROGRAM_RE = re.compile(r"(?:^|[;&|]\s*)exec\s+(?:env\s+)?([^\s;]+)")
SHELL_VAR_RE = re.compile(r"\$(?:\{([A-Za-z_]\w*)[^}]*\}|([A-Za-z_]\w*))")
TRUSTPRESS_FLAG_VALUE_RE = re.compile(
    rf"(?<![A-Za-z0-9_])-{{1,2}}{TRUSTPRESS_FLAG}(?:=|\s+)"
    r"(?P<value>\$\{[^}]+\}|\$[A-Za-z_]\w*|[^\s;]+)"
)

# dmon 老录制路线的信号。它与 archon::diff 新路线不是同一套东西，命中时只提示确认
# 迁移策略，不能当成「已接入 archon::diff 录制」。
DMON_LEGACY_SIGNALS = (
    "HOLMES_REC_USE_TPRESS_DMON",
    "tpress-dmon-bootstrap.sh",
    "HOLMES_REC_SERVER_URL",
)

# 共享框架承载：业务仓自己没有 main / handler，Archon server 初始化由共享框架仓（框架库
# 与 *_predict_common）承载，sinker 注入点只能落在框架 / common 仓。
SHARED_FRAMEWORK_TARGETS = (
    "jarvis/weiss_service",
    "jarvis/weiss_predict_common",
    "jarvis/shorttext_predict_common",
    "nlp/weiss_relevance_predict_common",
    "_predict_common",
)
# 真正调用 ArchonContext::init / create_server 的框架库，仅用于输出里指路。
SHARED_FRAMEWORK_BOOTSTRAP = "data/libtimetomb (include/timetomb/boostrap.h)"
SHARED_FRAMEWORK_INJECTION_HINT = "*_predict_common/service/main.cpp 的 before_setup_environment"

# Archon 流量录制链路必需的依赖及其分支。`ref` 是契约的一部分（fbthrift / folly 走
# archon 固定分支，不能改成 master）；`reference_commit` 只是参考水位，会随上游演进
# 过期，仅在解析不到远端 HEAD 时兜底判定 —— 正常路径的目标值一律取远端 HEAD。
# `build_*` 前缀的字段只在 BUILD-only 形态生效（BUILD 里没有 SHA pin，只能判存在性）。
REQUIRED_DEPS: dict[str, dict[str, str]] = {
    "data/archon": {
        "ref": "master",
        "reference_commit": "cb0eb3388830767afd6a8d0063d647ad93507d14",
        # BUILD-only 仓常常没有 data/archon 条目，Archon 由上游库带入（传递供给）。
        "build_transitive_providers": [
            "data/libtimetomb:libtimetomb_archon",
            "data/mage_predict:libpredict_common",
            "cppservice:cppservice_predict_simple_archon",
        ],
    },
    "data-arch/archon-gen": {
        "ref": "master",
        "reference_commit": "f115c591e079b9ff2792222bf0b8a9c5347a1660",
        # codegen 工具不参与链接，BUILD-only 仓通常由上游 idl 仓提供生成代码。
        "build_optional": True,
    },
    # folly / fbthrift 也可能由 bpt 包（cpp3rdlib/*）提供，此时无法与 git 参考 commit
    # 比较，只能标成 alt 交人工确认，绝不能自动补一个 git 条目上去。
    "data-arch/fbthrift": {
        "ref": "archon-v2018.08.20.00",
        "reference_commit": "8cf3fa70c375d29eb8ae0f6f24244602c74716ea",
        "alternatives": ["bpt/fbthrift"],
        "build_alternatives": ["bpt/fbthrift", "cpp3rdlib/fbthrift"],
        "build_pinned_branch": True,
    },
    "data-arch/folly": {
        "ref": "archon-v2022.11.14.00",
        "reference_commit": "dc0f20685273225039d7ef112c3597e6f06d3f11",
        "alternatives": ["bpt/folly"],
        "build_alternatives": ["bpt/folly", "cpp3rdlib/folly"],
        "build_pinned_branch": True,
    },
    "data-arch/traffic_sinker_lib": {
        "ref": "master",
        "reference_commit": "b6d1a98c18341ef973b0e96d4126038006fe50b3",
    },
    "bytedoc/mongo-cxx-driver": {
        "ref": "master",
        "reference_commit": "98a4e824498d70586aa9b4e5fd2d34e8e700c11d",
        # data-arch/traffic_sinker_lib 的 BUILD 自带 bytedoc/mongo-cxx-driver:v1.0.0，
        # 所以 BUILD-only 仓通常不需要额外补一条 mongo driver 依赖。
        "build_optional": True,
    },
}

STATUS_LATEST = "ok(latest)"
STATUS_STALE = "stale"
STATUS_MISSING = "missing"
# 远端 HEAD 拿不到时的兜底结论，两者都只对齐到可能已过期的参考水位。
STATUS_ALT = "alt"
STATUS_OK_REF = "ok(ref?)"
STATUS_UNKNOWN_REF = "unknown(ref?)"
REF_BASED = (STATUS_OK_REF, STATUS_UNKNOWN_REF)

# BUILD-only 形态的三态结论：BUILD 没有 SHA pin，只能判「存在性 + 分支名」，
# 不输出 stale / ok(latest)，也不做 commit 祖先比较。
STATUS_PRESENT = "present"
STATUS_TRANSITIVE = "transitive"
STATUS_ABSENT = "absent"
STATUS_ABSENT_OPTIONAL = "absent(optional)"
STATUS_BRANCH_MISMATCH = "branch_mismatch"
BUILD_ONLY_TODO = (STATUS_ABSENT, STATUS_BRANCH_MISMATCH)

# 下限校验（--verify）结论：参考 commit 必须是当前 commit 的祖先。
GATE_PASS = "pass(>=ref)"
GATE_FAIL_BEHIND = "fail(<ref)"
GATE_FAIL_MISSING = "fail(missing)"
GATE_DIVERGED = "diverged"
GATE_ALT = "unknown(alt)"
GATE_UNKNOWN = "unknown"
GATE_FAILURES = (GATE_FAIL_BEHIND, GATE_FAIL_MISSING)

REF_FALLBACK_WARNING = (
    "🔴 **依赖结论未经远端核实**：本次未能解析远端分支 HEAD，下列依赖只与技能内置的"
    "参考 commit 做了比对。参考值可能已过期（维护者未必及时更新），**请业务方自行"
    "确认这些依赖是否需要拉到各自分支最新 HEAD**，不要把本表当作「已是最新」的证据。"
)


class UsageError(Exception):
    """用法或环境错误：以 EXIT_USAGE 退出，不打 traceback，也不与「有待办」共用退出码。"""


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


@dataclass
class DepState:
    key: str
    ref: str
    reference_commit: str
    current_commit: Optional[str] = None
    remote_head: Optional[str] = None
    status: str = STATUS_MISSING
    gate: Optional[str] = None
    previous_commit: Optional[str] = None
    alternatives: list[str] = field(default_factory=list)
    alt_key: Optional[str] = None
    alt_info: Optional[str] = None
    # 以下字段只在 BUILD-only 形态使用：BUILD 里声明的分支名与实际供给方（传递供给的
    # 上游 target，或 BUILD 条目原文）。
    build_ref: Optional[str] = None
    supplied_by: Optional[str] = None
    optional: bool = False

    def info_value(self, commit: str) -> str:
        return f"{self.key}#{self.ref}#{commit}#git"


@dataclass
class Change:
    key: str
    ref: str
    old: Optional[str]
    new: Optional[str]


@dataclass
class RepoState:
    deps: list[DepState] = field(default_factory=list)
    legacy_sinker: bool = False
    legacy_wired: bool = False
    build_wired: bool = False
    sinker_injected: bool = False
    sinker_init_order: str = SINKER_ORDER_NOT_INJECTED
    switch_wired: bool = False
    switch_default_off: bool = True
    switch_candidate_scripts: list[str] = field(default_factory=list)
    switch_unwired_scripts: list[str] = field(default_factory=list)
    switch_unsafe_default_scripts: list[str] = field(default_factory=list)
    conf_wired: bool = False
    missing_conf_keys: list[str] = field(default_factory=list)
    offline: bool = False
    source: str = ""
    repo: Optional[str] = None
    legacy_previous: Optional[str] = None
    local: bool = True
    web_base: Optional[str] = None
    gate_checked: bool = False
    # 依赖图形态与 BUILD-only 专属信号。
    layout: str = LAYOUT_DEP_GRAPH
    has_own_entrypoint: bool = True
    shared_framework: bool = False
    framework_targets: list[str] = field(default_factory=list)
    dmon_signals: list[str] = field(default_factory=list)

    def dep(self, key: str) -> Optional[DepState]:
        return next((dep for dep in self.deps if dep.key == key), None)

    def has_dep(self, key: str) -> bool:
        dep = self.dep(key)
        return bool(dep and dep.current_commit)

    @property
    def build_only(self) -> bool:
        return self.layout == LAYOUT_BUILD_ONLY

    @property
    def wiring_ready(self) -> bool:
        return bool(
            self.build_wired
            and self.sinker_injected
            and self.sinker_init_order == SINKER_ORDER_BEFORE_INIT
            and self.switch_wired
            and self.switch_default_off
            and self.conf_wired
        )

    def build_supplied(self, key: str) -> bool:
        """BUILD-only 形态下该依赖是否已被供给（直接声明 / 传递供给 / 替代供给）。"""
        dep = self.dep(key)
        return bool(dep and dep.status in (STATUS_PRESENT, STATUS_TRANSITIVE, STATUS_ALT))

    @property
    def build_only_todo(self) -> list[DepState]:
        return [dep for dep in self.deps if dep.status in BUILD_ONLY_TODO]

    @property
    def onboarding_status(self) -> str:
        if self.layout == LAYOUT_UNSUPPORTED:
            return "not_applicable"
        if self.build_only:
            return self.build_only_onboarding_status
        has_archon = self.has_dep(ARCHON_DEP)
        has_traffic = self.has_dep(TRAFFIC_SINKER_DEP)
        has_mongo = self.has_dep(MONGO_DEP)
        if not has_archon and not has_traffic and not self.legacy_sinker and not self.legacy_wired:
            return "not_onboarded"
        if self.legacy_sinker or self.legacy_wired:
            return "legacy_sinker_upgrade"
        if has_traffic and not (has_mongo and (not self.local or self.wiring_ready)):
            return "partial_new_sinker"
        if any(dep.status in (STATUS_STALE, STATUS_MISSING, STATUS_OK_REF, STATUS_UNKNOWN_REF) for dep in self.deps):
            return "dependency_update"
        if self.alt_supplied:
            return "ready_with_alt_review"
        return "ready"

    @property
    def build_only_onboarding_status(self) -> str:
        """BUILD-only 体检的分流口径：旧 sinker > 共享框架承载 > 半接入 > 缺依赖 > alt > ready。"""
        if self.legacy_sinker or self.legacy_wired:
            return "legacy_sinker_upgrade"
        if self.shared_framework:
            return "shared_framework_managed"
        has_archon = self.build_supplied(ARCHON_DEP)
        has_traffic = self.build_supplied(TRAFFIC_SINKER_DEP)
        if not has_archon and not has_traffic:
            return "not_onboarded"
        if not has_traffic or not self.wiring_ready:
            return "partial_new_sinker"
        if self.build_only_todo:
            return "dependency_update"
        if self.alt_supplied:
            return "ready_with_alt_review"
        return "ready"

    @property
    def onboarding_status_text(self) -> str:
        return {
            "not_applicable": "不适用：本仓既没有 dep_graph.blade 也没有 BUILD，不是 C++ 服务仓，Archon 录制不适用",
            "not_onboarded": "从未接入：需要完整接入 Archon 流量录制",
            "legacy_sinker_upgrade": "已接旧 sinker：需要从 trustpress_databus_lib 迁到 traffic_sinker_lib",
            "partial_new_sinker": "新 sinker 半接入：补齐 mongo 依赖 / BUILD / MultiSinker（且在初始化前注册）/ 开关 / conf 参数",
            "dependency_update": "已接入但依赖不是最新或缺项：升级依赖并贴 CR diff",
            "shared_framework_managed": "共享框架承载：Archon server 初始化不在本仓，改动要拆成「业务仓」+「框架/common 仓」两栏，技能只出体检与改动清单",
            "ready_with_alt_review": "基本就绪，但 folly/fbthrift 由 bpt 等替代供给，需人工确认兼容性",
            "ready": "已接入且关键项就绪",
        }[self.onboarding_status]

    @property
    def alt_supplied(self) -> list[DepState]:
        return [dep for dep in self.deps if dep.status == STATUS_ALT]

    @property
    def gate_failures(self) -> list[DepState]:
        return [dep for dep in self.deps if dep.gate in GATE_FAILURES]

    @property
    def gate_unclear(self) -> list[DepState]:
        return [dep for dep in self.deps if dep.gate in (GATE_UNKNOWN, GATE_DIVERGED, GATE_ALT)]

    @property
    def ref_based(self) -> list[DepState]:
        """结论来自参考值而非远端 HEAD 的依赖，必须在 MR 描述里带警告。"""
        return [dep for dep in self.deps if dep.status in REF_BASED]

    @property
    def needs_action(self) -> bool:
        if self.layout == LAYOUT_UNSUPPORTED:
            return False
        if self.legacy_sinker or self.legacy_wired:
            return True
        if self.build_only:
            return bool(self.shared_framework or not self.wiring_ready or self.build_only_todo)
        if self.local and not self.wiring_ready:
            return True
        return any(dep.status != STATUS_LATEST for dep in self.deps)


def parse_info(info: str) -> Optional[str]:
    """从 `repo#ref#sha#git` 中取 commit。"""
    parts = info.split("#")
    return parts[2] if len(parts) >= 3 else None


def detect_indent(text: str) -> str:
    match = re.search(r'^(\s+)"[^"]+":\s*\{', text, re.MULTILINE)
    return match.group(1) if match else "    "


def top_level_keys(lines: list[str], indent: str) -> list[tuple[int, str]]:
    pattern = re.compile(rf'^{re.escape(indent)}"([^"]+)":\s*\{{\s*$')
    keys = []
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            keys.append((index, match.group(1)))
    return keys


def block_range(lines: list[str], start: int, indent: str) -> tuple[int, int]:
    """返回条目块的行区间 [start, end]，end 为该块闭合花括号所在行。"""
    closing = re.compile(rf"^{re.escape(indent)}\}},?\s*$")
    for index in range(start + 1, len(lines)):
        if closing.match(lines[index]):
            return start, index
    raise ValueError(f"unterminated block at line {start + 1}")


def remote_base(repo_dir: str) -> Optional[str]:
    """从业务仓库 origin 推导同平台其它仓库的地址前缀，避免硬编码 host。"""
    try:
        url = subprocess.check_output(
            ["git", "-C", repo_dir, "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        warn(f"无法读取 {repo_dir} 的 origin 地址: {err}")
        return None

    scp_like = re.match(r"^([^/]+@[^:]+:)(.+)$", url)
    if scp_like:
        return scp_like.group(1)
    if "://" in url and url.count("/") >= 4:
        return url.rsplit("/", 2)[0] + "/"
    warn(f"无法解析 origin 地址格式: {url}")
    return None


def resolve_head(base: str, repo: str, ref: str) -> Optional[str]:
    try:
        output = subprocess.check_output(
            ["git", "ls-remote", f"{base}{repo}", f"refs/heads/{ref}"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=LS_REMOTE_TIMEOUT_SECONDS,
        ).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as err:
        warn(f"解析 {repo}#{ref} 的远端 HEAD 失败: {err}")
        return None
    if not output:
        warn(f"{repo} 上找不到分支 {ref}，确认 ref 是否被上游改名")
        return None
    return output.split()[0]


def classify(dep: DepState) -> str:
    if dep.current_commit is None:
        return STATUS_ALT if dep.alt_key else STATUS_MISSING
    if dep.remote_head is None:
        # 拿不到最新值时退回参考水位给结论，但结论要打上 "?" 并配警告。
        return STATUS_OK_REF if dep.current_commit == dep.reference_commit else STATUS_UNKNOWN_REF
    return STATUS_LATEST if dep.current_commit == dep.remote_head else STATUS_STALE


def web_base_from_ssh(base: str) -> Optional[str]:
    """`gitlab@git.<host>:` -> `https://code.<host>/`，用于生成给 CR 看的链接。"""
    match = re.match(r"^[^@]+@git\.([^:]+):$", base)
    if match:
        return f"https://code.{match.group(1)}/"
    if base.startswith("http"):
        return base
    return None


def ssh_base_from_web_host(host: str) -> str:
    return f"gitlab@git.{host[len('code.'):]}:" if host.startswith("code.") else f"gitlab@{host}:"


def compare_link(web_base: Optional[str], repo: str, old: str, new: str) -> Optional[str]:
    return f"{web_base}{repo}/compare/{old}...{new}" if web_base else None


def repo_link(web_base: Optional[str], repo: str, ref: str) -> Optional[str]:
    return f"{web_base}{repo}/commits/{ref}" if web_base else None


def run_git(args: list[str], timeout: int = CLONE_TIMEOUT_SECONDS) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, timeout=timeout, check=False
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


class CommitGraphs:
    """按需拉取只含 commit 对象的浅副本（--filter=tree:0），用于祖先关系判定。"""

    def __init__(self, base: Optional[str]) -> None:
        self.base = base
        self.root = tempfile.mkdtemp(prefix="archon-traffic-graph-")
        self.cache: dict[tuple[str, str], Optional[str]] = {}

    def close(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def path_for(self, repo: str, ref: str) -> Optional[str]:
        if not self.base:
            return None
        key = (repo, ref)
        if key in self.cache:
            return self.cache[key]
        dest = os.path.join(self.root, repo.replace("/", "__") + "@" + ref.replace("/", "__"))
        code, output = run_git(
            [
                "clone", "-q", "--filter=tree:0", "--no-checkout",
                "--single-branch", "--branch", ref, f"{self.base}{repo}", dest,
            ]
        )
        if code != 0:
            warn(f"拉取 {repo}#{ref} 的 commit 图失败: {output.strip().splitlines()[-1:]}")
            dest = None
        self.cache[key] = dest
        return dest

    def ensure_commit(self, work: str, sha: str) -> bool:
        if run_git(["-C", work, "cat-file", "-e", f"{sha}^{{commit}}"])[0] == 0:
            return True
        return run_git(["-C", work, "fetch", "-q", "--filter=tree:0", "origin", sha])[0] == 0

    def gate(self, repo: str, ref: str, reference: str, current: Optional[str]) -> str:
        if current is None:
            return GATE_FAIL_MISSING
        if current == reference:
            return GATE_PASS
        work = self.path_for(repo, ref)
        if not work:
            return GATE_UNKNOWN
        if not (self.ensure_commit(work, reference) and self.ensure_commit(work, current)):
            warn(f"{repo}#{ref}: commit 对象拉不到，无法判定祖先关系")
            return GATE_UNKNOWN
        if run_git(["-C", work, "merge-base", "--is-ancestor", reference, current])[0] == 0:
            return GATE_PASS
        if run_git(["-C", work, "merge-base", "--is-ancestor", current, reference])[0] == 0:
            return GATE_FAIL_BEHIND
        return GATE_DIVERGED


def load_graph_from_mr(
    url: str, git_base: Optional[str]
) -> tuple[dict, Optional[dict], str, str]:
    """不落地业务仓库，直接从 MR 的只读 ref 上读出 dep_graph.blade。"""
    match = MR_URL_RE.match(url)
    if not match:
        raise UsageError(f"无法解析 MR 链接: {url}")
    repo, iid = match.group("repo"), match.group("iid")
    base = git_base or ssh_base_from_web_host(match.group("host"))
    work = tempfile.mkdtemp(prefix="archon-traffic-mr-")
    try:
        code, output = run_git(
            ["clone", "-q", "--filter=blob:none", "--no-checkout", f"{base}{repo}", work]
        )
        if code != 0:
            raise UsageError(f"clone {repo} 失败: {output.strip()}")
        for name in MR_REF_CANDIDATES:
            ref = f"refs/merge-requests/{iid}/{name}"
            if run_git(["-C", work, "fetch", "-q", "origin", f"{ref}:mr"])[0] == 0:
                code, content = run_git(["-C", work, "show", f"mr:{DEP_GRAPH_FILENAME}"])
                if code != 0:
                    raise UsageError(f"MR {iid} 的 {ref} 上没有 {DEP_GRAPH_FILENAME}")
                # mr^ 是 MR 的 base 侧，用来算出这次 MR 真正动了哪些依赖。
                base_code, base_content = run_git(["-C", work, "show", f"mr^:{DEP_GRAPH_FILENAME}"])
                previous = json.loads(base_content) if base_code == 0 else None
                if previous is None:
                    warn("取不到 MR base 侧的 dep_graph.blade，无法给出本次变更的 diff 链接")
                return json.loads(content), previous, repo, ref
        raise UsageError(f"MR {iid} 的只读 ref 都取不到，确认 MR 是否存在或已关闭")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def grep_repo(repo_dir: str, pattern: str, name_filters: list[str]) -> bool:
    """字面量匹配：target 里的 `//`、`:`、`.` 不能被当成正则，所以固定用 -F。"""
    command = ["grep", "-rlF", *name_filters, "--exclude-dir=.git", "--", pattern, "."]
    result = subprocess.run(command, cwd=repo_dir, capture_output=True, text=True, check=False)
    return bool(result.stdout.strip())


def grep_repo_regex(repo_dir: str, pattern: str, name_filters: list[str]) -> bool:
    """正则匹配，只用于需要校验形态（如 `:-false` 默认值）的场景。"""
    command = ["grep", "-rlE", *name_filters, "--exclude-dir=.git", "--", pattern, "."]
    result = subprocess.run(command, cwd=repo_dir, capture_output=True, text=True, check=False)
    return bool(result.stdout.strip())


def sinker_registration_state(repo_dir: str) -> tuple[bool, str]:
    """检查 MultiSinker 是否在承载它的启动文件中早于初始化入口注册。

    Archon 在 init 期间创建 TrustPress dump handler；晚注册虽然代码里能 grep 到
    MultiSinker，但 handler 已初始化失败且不会重试。找不到 init 时保守标记为需人工确认。
    """
    injected = False
    saw_init = False
    saw_late_registration = False
    source_suffixes = (".cpp", ".cc", ".cxx", ".h", ".hpp")
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [name for name in dirs if name != ".git"]
        for filename in files:
            if not filename.endswith(source_suffixes):
                continue
            path = os.path.join(root, filename)
            try:
                with open(path, encoding="utf-8", errors="ignore") as handle:
                    source = handle.read()
            except OSError:
                continue
            # 注释中的示例不能算接线；用等长空白替换以保留位置关系。
            code = re.sub(
                r"//[^\n]*|/\*.*?\*/",
                lambda match: re.sub(r"[^\n]", " ", match.group(0)),
                source,
                flags=re.DOTALL,
            )
            sinker_positions = [match.start() for match in re.finditer(INJECTED_SINKER, code)]
            if not sinker_positions:
                continue
            injected = True
            init_positions = [match.start() for match in INIT_CALL_RE.finditer(code)]
            if not init_positions:
                continue
            saw_init = True
            if min(sinker_positions) < min(init_positions):
                return True, SINKER_ORDER_BEFORE_INIT
            saw_late_registration = True
    if not injected:
        return False, SINKER_ORDER_NOT_INJECTED
    if saw_late_registration:
        return True, SINKER_ORDER_AFTER_INIT
    return True, SINKER_ORDER_INIT_NOT_FOUND if not saw_init else SINKER_ORDER_AFTER_INIT


@dataclass
class TrustpressSwitchState:
    candidate_scripts: list[str] = field(default_factory=list)
    unwired_scripts: list[str] = field(default_factory=list)
    unsafe_default_scripts: list[str] = field(default_factory=list)

    @property
    def wired(self) -> bool:
        return bool(self.candidate_scripts) and not self.unwired_scripts

    @property
    def default_off(self) -> bool:
        return bool(self.candidate_scripts) and not self.unsafe_default_scripts


def shell_logical_lines(source: str) -> list[str]:
    """合并反斜杠续行；只移除整行注释，避免把引号中的 # 误当注释。"""
    logical: list[str] = []
    pending = ""
    for raw in source.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        pending = f"{pending} {stripped}".strip()
        if pending.endswith("\\"):
            pending = pending[:-1].rstrip()
            continue
        logical.append(pending)
        pending = ""
    if pending:
        logical.append(pending)
    return logical


def shell_vars(value: str) -> set[str]:
    return {left or right for left, right in SHELL_VAR_RE.findall(value)}


def flag_value(line: str) -> Optional[str]:
    match = TRUSTPRESS_FLAG_VALUE_RE.search(line)
    return match.group("value") if match else None


def inspect_trustpress_script(source: str) -> tuple[Optional[str], bool, bool, bool]:
    """返回 (最终 exec 程序, 是否有 TrustPress 信号, 是否透传, 是否默认关闭)。

    候选入口需同时有 exec 和 Archon 信号。每个入口必须在本文件中形成
    `ARCHON_ENABLE_TRUSTPRESS -> shell 变量 -> exec flag` 闭环；flag 经 common_flags
    等变量间接展开也支持，不能再把不同文件里的两个字符串做集合并集。
    """
    lines = shell_logical_lines(source)
    exec_lines = [line for line in lines if SHELL_EXEC_RE.search(line)]
    has_trustpress_signal = TRUSTPRESS_ENV in source or TRUSTPRESS_FLAG in source
    if not exec_lines:
        return None, has_trustpress_signal, False, False
    program_match = SHELL_EXEC_PROGRAM_RE.search(exec_lines[-1])
    program = os.path.basename(program_match.group(1)) if program_match else None

    assignments: dict[str, str] = {}
    for line in lines:
        match = SHELL_ASSIGNMENT_RE.match(line)
        if match:
            assignments[match.group(1)] = match.group(2).strip()

    env_vars: set[str] = set()
    safe_env_vars: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, value in assignments.items():
            refs = shell_vars(value)
            if (TRUSTPRESS_ENV in refs or refs & env_vars) and name not in env_vars:
                env_vars.add(name)
                changed = True
            if (re.search(SWITCH_DEFAULT_OFF_RE, value) or refs & safe_env_vars) and name not in safe_env_vars:
                safe_env_vars.add(name)
                changed = True

    carrier_vars: set[str] = set()
    safe_carrier_vars: set[str] = set()
    for name, value in assignments.items():
        flag = flag_value(value)
        if not flag:
            continue
        refs = shell_vars(flag)
        if TRUSTPRESS_ENV in refs or refs & env_vars:
            carrier_vars.add(name)
        if re.search(SWITCH_DEFAULT_OFF_RE, flag) or refs & safe_env_vars:
            safe_carrier_vars.add(name)

    wired = False
    default_off = False
    for line in exec_lines:
        flag = flag_value(line)
        if flag:
            refs = shell_vars(flag)
            wired |= TRUSTPRESS_ENV in refs or bool(refs & env_vars)
            default_off |= bool(re.search(SWITCH_DEFAULT_OFF_RE, flag)) or bool(
                refs & safe_env_vars
            )
        refs = shell_vars(line)
        wired |= bool(refs & carrier_vars)
        default_off |= bool(refs & safe_carrier_vars)
    return program, has_trustpress_signal, wired, default_off


def trustpress_switch_state(repo_dir: str) -> TrustpressSwitchState:
    state = TrustpressSwitchState()
    scripts: list[tuple[str, Optional[str], bool, bool, bool]] = []
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [name for name in dirs if name != ".git"]
        for filename in files:
            if not any(fnmatch.fnmatch(filename, pattern) for pattern in RUN_SCRIPT_PATTERNS):
                continue
            path = os.path.join(root, filename)
            try:
                with open(path, encoding="utf-8", errors="ignore") as handle:
                    program, signal, wired, default_off = inspect_trustpress_script(handle.read())
            except OSError:
                continue
            relative = os.path.relpath(path, repo_dir)
            scripts.append((relative, program, signal, wired, default_off))
    trustpress_programs = {program for _, program, signal, _, _ in scripts if program and signal}
    for relative, program, signal, wired, default_off in scripts:
        # 已出现 TrustPress 信号的脚本都要自证闭环；另外强制审计同一二进制的 TCE 入口，
        # 防止普通 real_run 已接而 real_run_tce 漏接。区域专用的非 TCE 启动脚本可能由
        # 不同发布系统管理，不能仅凭二进制相同就一概要求接入。
        is_tce_entry = "tce" in os.path.basename(relative).lower()
        if not signal and not (is_tce_entry and program in trustpress_programs):
            continue
        state.candidate_scripts.append(relative)
        if not wired:
            state.unwired_scripts.append(relative)
        if not default_off:
            state.unsafe_default_scripts.append(relative)
    state.candidate_scripts.sort()
    state.unwired_scripts.sort()
    state.unsafe_default_scripts.sort()
    return state


def missing_trustpress_conf_keys(repo_dir: str) -> list[str]:
    return [key for key in TRUSTPRESS_CONF_KEYS if not grep_repo(repo_dir, key, CONF_FILTERS)]


def dmon_legacy_signals(repo_dir: str) -> list[str]:
    """dmon 老录制路线的信号，命中不代表接了 archon::diff 新路线。"""
    return [signal for signal in DMON_LEGACY_SIGNALS if grep_repo(repo_dir, signal, [])]


def commit_of(graph: dict, key: str) -> Optional[str]:
    entry = graph.get(key)
    return parse_info(str(entry.get("info", ""))) if entry else None


def find_alternative(graph: dict, alternatives: list[str]) -> tuple[Optional[str], Optional[str]]:
    """主 key 缺失时看是否由别的条目（常见是 bpt 包）供给同一个库。"""
    for key in alternatives:
        entry = graph.get(key)
        if entry:
            return key, str(entry.get("info", ""))
    return None, None


def build_state(
    graph: dict,
    previous: Optional[dict],
    required: dict[str, dict[str, str]],
    base: Optional[str],
    verify: bool,
) -> list[DepState]:
    graphs = CommitGraphs(base) if verify else None
    deps = []
    try:
        for key, spec in required.items():
            dep = DepState(
                key=key,
                ref=spec["ref"],
                reference_commit=spec["reference_commit"],
                alternatives=list(spec.get("alternatives", [])),
            )
            dep.current_commit = commit_of(graph, key)
            if dep.current_commit is None and dep.alternatives:
                dep.alt_key, dep.alt_info = find_alternative(graph, dep.alternatives)
            if previous is not None:
                dep.previous_commit = commit_of(previous, key)
            if base:
                dep.remote_head = resolve_head(base, key, dep.ref)
            dep.status = classify(dep)
            if graphs:
                dep.gate = (
                    GATE_ALT
                    if dep.status == STATUS_ALT
                    else graphs.gate(key, dep.ref, dep.reference_commit, dep.current_commit)
                )
            deps.append(dep)
    finally:
        if graphs:
            graphs.close()
    return deps


def detect_dep_layout(repo_dir: str) -> str:
    """探测依赖图形态。

    `dep_graph.blade` 在位就走原有全量逻辑；只有 BUILD 时进 BUILD-only 体检模式；
    两者都没有说明不是 C++ 服务仓（例如纯 CONFIG 仓），直接判 unsupported。
    `blade_root/BLADE_ROOT.local` 之类的 *.blade 只带编译 flag，不参与依赖解析。
    """
    if not os.path.isdir(repo_dir):
        raise UsageError(f"{repo_dir} 不是一个目录，确认 --repo 指向业务仓库根目录")
    if os.path.isfile(os.path.join(repo_dir, DEP_GRAPH_FILENAME)):
        return LAYOUT_DEP_GRAPH
    if os.path.isfile(os.path.join(repo_dir, BUILD_FILENAME)):
        return LAYOUT_BUILD_ONLY
    return LAYOUT_UNSUPPORTED


def read_build_text(repo_dir: str) -> str:
    """读根 BUILD 与子目录 BUILD（依赖声明可能拆在子目录），拼成一份文本用于解析。"""
    chunks = []
    for current, dirs, files in os.walk(repo_dir):
        dirs[:] = [name for name in dirs if name != ".git"]
        if BUILD_FILENAME in files:
            path = os.path.join(current, BUILD_FILENAME)
            try:
                with open(path, encoding="utf-8", errors="replace") as handle:
                    chunks.append(handle.read())
            except OSError as err:
                warn(f"读取 {path} 失败: {err}")
    return "\n".join(chunks)


@dataclass
class BuildEntry:
    repo: str
    ref: str
    target: Optional[str]
    raw: str


def parse_build_entries(text: str) -> list[BuildEntry]:
    """从 BUILD 文本里抽出依赖条目。

    两种形态都要认：`global_settler(prefer_deps=[...])` 里的简写 `<repo>:<ref>`，
    以及完整 target `<repo>:<ref>@//<path>:<target>`。BUILD 里没有 SHA pin，所以
    这里只拿到 repo 与分支名，拿不到 commit。
    """
    entries: list[BuildEntry] = []
    for raw in re.findall(r'"([^"\n]+)"', text):
        left, _, target = raw.partition("@//")
        repo, sep, ref = left.partition(":")
        if not sep or "/" not in repo or not ref:
            continue
        entries.append(BuildEntry(repo=repo.strip(), ref=ref.strip(), target=target or None, raw=raw))
    return entries


def find_build_entry(entries: list[BuildEntry], repo: str) -> Optional[BuildEntry]:
    return next((entry for entry in entries if entry.repo == repo), None)


def find_transitive_provider(entries: list[BuildEntry], providers: list[str]) -> Optional[str]:
    """Archon 可能由上游库带入（如 libtimetomb / mage_predict / cppservice 的 archon target）。"""
    for provider in providers:
        for entry in entries:
            if provider in entry.raw:
                return entry.raw
    return None


def build_only_dep_state(
    entries: list[BuildEntry], required: dict[str, dict[str, str]]
) -> list[DepState]:
    """BUILD-only 形态的依赖判定：只判「存在性 + 分支名」，不判水位、不比 commit。"""
    deps: list[DepState] = []
    for key, spec in required.items():
        dep = DepState(
            key=key,
            ref=spec["ref"],
            reference_commit=spec["reference_commit"],
            alternatives=list(spec.get("build_alternatives", spec.get("alternatives", []))),
            optional=bool(spec.get("build_optional")),
        )
        entry = find_build_entry(entries, key)
        if entry:
            dep.build_ref = entry.ref
            dep.supplied_by = entry.raw
            pinned = bool(spec.get("build_pinned_branch"))
            # 固定分支约束在 prefer_deps 简写里也要生效。
            dep.status = (
                STATUS_BRANCH_MISMATCH if pinned and entry.ref != dep.ref else STATUS_PRESENT
            )
            deps.append(dep)
            continue
        provider = find_transitive_provider(
            entries, list(spec.get("build_transitive_providers", []))
        )
        if provider:
            dep.status = STATUS_TRANSITIVE
            dep.supplied_by = provider
            deps.append(dep)
            continue
        alt = next((entry for entry in entries if entry.repo in dep.alternatives), None)
        if alt:
            dep.status = STATUS_ALT
            dep.alt_key = alt.repo
            dep.alt_info = alt.raw
            dep.build_ref = alt.ref
            deps.append(dep)
            continue
        dep.status = STATUS_ABSENT_OPTIONAL if dep.optional else STATUS_ABSENT
        deps.append(dep)
    return deps


def detect_shared_framework(
    repo_dir: str, entries: list[BuildEntry]
) -> tuple[bool, list[str], bool]:
    """业务仓没有自己的 main / handler，且依赖了共享框架 target ⇒ 共享框架承载。

    返回 (是否共享框架承载, 命中的框架 target, 本仓是否有自己的入口)。
    """
    targets = sorted(
        {
            entry.repo
            for entry in entries
            if any(marker in entry.raw for marker in SHARED_FRAMEWORK_TARGETS)
        }
    )
    has_main = grep_repo(repo_dir, "int main", ["--include=*.cpp", "--include=*.cc"])
    has_handler = grep_repo(
        repo_dir, TRUSTPRESS_ANCHOR, ["--include=*.cpp", "--include=*.h", "--include=*.cc"]
    )
    has_own_entrypoint = has_main or has_handler
    return bool(targets and not has_own_entrypoint), targets, has_own_entrypoint


def inspect_build_only(repo_dir: str, required: dict[str, dict[str, str]]) -> RepoState:
    """BUILD-only 体检：依赖三态 + 接线检查 + dmon 老路线识别 + 共享框架承载识别。"""
    entries = parse_build_entries(read_build_text(repo_dir))
    missing_conf = missing_trustpress_conf_keys(repo_dir)
    shared_framework, framework_targets, has_own_entrypoint = detect_shared_framework(
        repo_dir, entries
    )
    sinker_injected, sinker_init_order = sinker_registration_state(repo_dir)
    switch = trustpress_switch_state(repo_dir)
    return RepoState(
        deps=build_only_dep_state(entries, required),
        layout=LAYOUT_BUILD_ONLY,
        legacy_sinker=bool(find_build_entry(entries, LEGACY_DEP)),
        legacy_wired=grep_repo(
            repo_dir, "trustpress_databus", ["--include=BUILD", "--include=*.cpp", "--include=*.h"]
        ),
        build_wired=grep_repo(repo_dir, "traffic_sinker", ["--include=BUILD"]),
        sinker_injected=sinker_injected,
        sinker_init_order=sinker_init_order,
        switch_wired=switch.wired,
        switch_default_off=switch.default_off,
        switch_candidate_scripts=switch.candidate_scripts,
        switch_unwired_scripts=switch.unwired_scripts,
        switch_unsafe_default_scripts=switch.unsafe_default_scripts,
        missing_conf_keys=missing_conf,
        conf_wired=not missing_conf,
        source=repo_dir,
        has_own_entrypoint=has_own_entrypoint,
        shared_framework=shared_framework,
        framework_targets=framework_targets,
        dmon_signals=dmon_legacy_signals(repo_dir),
    )


def inspect_unsupported(repo_dir: str) -> RepoState:
    return RepoState(layout=LAYOUT_UNSUPPORTED, source=repo_dir)


def inspect_local(
    repo_dir: str, required: dict[str, dict[str, str]], offline: bool, verify: bool
) -> RepoState:
    graph_path = os.path.join(repo_dir, DEP_GRAPH_FILENAME)
    try:
        with open(graph_path, encoding="utf-8") as handle:
            graph = json.load(handle)
    except (OSError, json.JSONDecodeError) as err:
        raise UsageError(f"读取 {graph_path} 失败: {err}") from err

    base = None if offline else remote_base(repo_dir)
    if not offline and base is None:
        warn("远端地址推导失败，本次判定退回参考水位；确认后可加 --offline 显式离线运行")
    missing_conf = missing_trustpress_conf_keys(repo_dir)

    sinker_injected, sinker_init_order = sinker_registration_state(repo_dir)
    switch = trustpress_switch_state(repo_dir)
    return RepoState(
        deps=build_state(graph, None, required, base, verify),
        legacy_sinker=LEGACY_DEP in graph,
        legacy_wired=grep_repo(repo_dir, "trustpress_databus", ["--include=BUILD", "--include=*.cpp", "--include=*.h"]),
        build_wired=grep_repo(repo_dir, "traffic_sinker", ["--include=BUILD"]),
        sinker_injected=sinker_injected,
        sinker_init_order=sinker_init_order,
        switch_wired=switch.wired,
        switch_default_off=switch.default_off,
        switch_candidate_scripts=switch.candidate_scripts,
        switch_unwired_scripts=switch.unwired_scripts,
        switch_unsafe_default_scripts=switch.unsafe_default_scripts,
        missing_conf_keys=missing_conf,
        conf_wired=not missing_conf,
        offline=offline,
        source=repo_dir,
        web_base=web_base_from_ssh(base) if base else None,
        gate_checked=verify,
    )


def inspect_mr(
    url: str,
    required: dict[str, dict[str, str]],
    offline: bool,
    verify: bool,
    git_base: Optional[str],
) -> RepoState:
    graph, previous, repo, ref = load_graph_from_mr(url, git_base)
    host = MR_URL_RE.match(url).group("host")
    base = None if offline else (git_base or ssh_base_from_web_host(host))
    return RepoState(
        deps=build_state(graph, previous, required, base, verify),
        legacy_sinker=LEGACY_DEP in graph,
        legacy_previous=commit_of(previous, LEGACY_DEP) if previous else None,
        offline=offline,
        source=f"{url} ({ref})",
        repo=repo,
        local=False,
        web_base=f"https://{host}/",
        gate_checked=verify,
    )


def plan_edits(state: RepoState) -> tuple[list[tuple[str, DepState, str]], list[DepState]]:
    """目标值只取远端 HEAD。解析不到 HEAD 时按参考水位给结论但不改写已存在条目：
    缺失项用参考值补齐，其余一律交人工，避免把比参考值更新的依赖降级回去。"""
    edits: list[tuple[str, DepState, str]] = []
    manual: list[DepState] = []
    for dep in state.deps:
        if dep.status == STATUS_LATEST:
            continue
        if dep.status == STATUS_STALE and dep.remote_head:
            edits.append(("upgrade", dep, dep.remote_head))
        elif dep.status == STATUS_MISSING:
            edits.append(("insert", dep, dep.remote_head or dep.reference_commit))
        else:
            manual.append(dep)
    return edits, manual


def upgrade_entry(lines: list[str], key: str, info: str, indent: str) -> list[str]:
    entries = {name: index for index, name in top_level_keys(lines, indent)}
    if key not in entries:
        raise ValueError(f"entry not found: {key}")
    start, end = block_range(lines, entries[key], indent)
    updated = list(lines)
    for index in range(start, end):
        if '"info"' in updated[index]:
            updated[index] = re.sub(r'("info":\s*")[^"]*(")', rf"\g<1>{info}\g<2>", updated[index])
            return updated
    raise ValueError(f"info field not found for {key}")


def insert_entry(lines: list[str], key: str, info: str, indent: str) -> list[str]:
    block = [
        f'{indent}"{key}": {{',
        f'{indent}{indent}"info": "{info}",',
        f'{indent}{indent}"repo": "{key}"',
        f"{indent}}},",
    ]
    for index, name in top_level_keys(lines, indent):
        if name > key:
            return lines[:index] + block + lines[index:]

    entries = top_level_keys(lines, indent)
    if not entries:
        raise ValueError(f"{DEP_GRAPH_FILENAME} 中没有可定位的条目")
    _, end = block_range(lines, entries[-1][0], indent)
    updated = list(lines)
    if not updated[end].rstrip().endswith(","):
        updated[end] = updated[end].rstrip() + ","
    block[-1] = block[-1].rstrip(",")
    return updated[: end + 1] + block + updated[end + 1 :]


def remove_entry(lines: list[str], key: str, indent: str) -> list[str]:
    entries = top_level_keys(lines, indent)
    index_of = {name: index for index, name in entries}
    if key not in index_of:
        return lines
    was_last = entries[-1][1] == key
    start, end = block_range(lines, index_of[key], indent)
    updated = lines[:start] + lines[end + 1 :]
    remaining = top_level_keys(updated, indent)
    if was_last and remaining:
        # 删掉的是最后一个条目，新的末尾条目不能再带尾逗号。
        _, last_end = block_range(updated, remaining[-1][0], indent)
        updated[last_end] = updated[last_end].rstrip().rstrip(",")
    return updated


def rewrite_dep_graph(
    repo_dir: str, edits: list[tuple[str, DepState, str]], drop_legacy: bool
) -> str:
    graph_path = os.path.join(repo_dir, DEP_GRAPH_FILENAME)
    with open(graph_path, encoding="utf-8") as handle:
        text = handle.read()

    indent = detect_indent(text)
    lines = text.splitlines()
    for kind, dep, commit in edits:
        info = dep.info_value(commit)
        lines = (
            insert_entry(lines, dep.key, info, indent)
            if kind == "insert"
            else upgrade_entry(lines, dep.key, info, indent)
        )
    if drop_legacy:
        lines = remove_entry(lines, LEGACY_DEP, indent)

    rewritten = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    json.loads(rewritten)
    return rewritten


def collect_changes(state: RepoState, edits: list[tuple[str, DepState, str]]) -> list[Change]:
    """本次动了哪些依赖：MR 模式取 base -> MR，本地模式取当前值 -> 计划写入值。"""
    if not state.local:
        changes = [
            Change(dep.key, dep.ref, dep.previous_commit, dep.current_commit)
            for dep in state.deps
            if dep.current_commit and dep.current_commit != dep.previous_commit
        ]
        if state.legacy_previous and not state.legacy_sinker:
            changes.append(Change(LEGACY_DEP, "master", state.legacy_previous, None))
        return changes
    changes = [
        Change(dep.key, dep.ref, dep.current_commit if kind == "upgrade" else None, commit)
        for kind, dep, commit in edits
    ]
    if state.legacy_sinker:
        changes.append(Change(LEGACY_DEP, "master", None, None))
    return changes


def render_change_links(state: RepoState, changes: list[Change]) -> list[str]:
    """给 CR 用的依赖变更清单：升级给 compare 链接，首次引入 / 删除给仓库地址。"""
    if not changes:
        return []
    rows = ["", "## 本次依赖变更（供 CR）", "", "| 依赖 | 变更 | Code Diff |", "| --- | --- | --- |"]
    for change in changes:
        repo_url = repo_link(state.web_base, change.key, change.ref)
        fallback = f"[{change.key}]({repo_url})" if repo_url else f"`{change.key}`"
        if change.new is None:
            summary = "移除" + (f"（原 `{change.old[:10]}`）" if change.old else "")
            cell = fallback
        elif change.old:
            link = compare_link(state.web_base, change.key, change.old, change.new)
            summary = f"`{change.old[:10]}` → `{change.new[:10]}`"
            cell = f"[{change.old[:10]}...{change.new[:10]}]({link})" if link else "（无法推导链接）"
        else:
            summary = f"首次引入 → `{change.new[:10]}`"
            cell = fallback
        rows.append(f"| `{change.key}` | {summary} | {cell} |")
    return rows


def build_only_wiring_rows(state: RepoState) -> list[str]:
    """BUILD-only / 共享框架承载共用的接线体检行。"""
    rows = [
        f"legacy_sinker({LEGACY_DEP}): {state.legacy_sinker}",
        f"legacy_wired(BUILD/代码仍引用旧 sinker): {state.legacy_wired}",
        f"build_wired(BUILD 含 traffic_sinker 目标): {state.build_wired}",
        f"sinker_injected(代码注入 MultiSinker): {state.sinker_injected}",
        f"sinker_init_order(必须早于 Archon/全局/父类 init): {state.sinker_init_order}",
        f"switch_wired({TRUSTPRESS_ENV} 默认关闭并透传 flag): {state.switch_wired}",
        f"switch_default_off(存在 ${{{TRUSTPRESS_ENV}:-false}} 形态): {state.switch_default_off}",
        f"switch_candidate_scripts: {','.join(state.switch_candidate_scripts) if state.switch_candidate_scripts else '-'}",
        f"switch_unwired_scripts: {','.join(state.switch_unwired_scripts) if state.switch_unwired_scripts else '-'}",
        f"switch_unsafe_default_scripts: {','.join(state.switch_unsafe_default_scripts) if state.switch_unsafe_default_scripts else '-'}",
        f"conf_wired(录制参数齐全): {state.conf_wired}",
        f"missing_conf_keys: {','.join(state.missing_conf_keys) if state.missing_conf_keys else '-'}",
        f"archon 最低版本要求: {MIN_ARCHON_VERSION}",
    ]
    return rows


def switch_default_warning(state: RepoState) -> Optional[str]:
    if state.switch_unsafe_default_scripts:
        return (
            f"⚠️ 以下启动入口没有形成 ${{{TRUSTPRESS_ENV}:-false}} -> "
            f"-{TRUSTPRESS_FLAG} 的默认关闭数据流："
            + "、".join(state.switch_unsafe_default_scripts)
        )
    return None


def switch_wiring_warning(state: RepoState) -> Optional[str]:
    if not state.switch_unwired_scripts:
        return None
    return (
        f"❌ 以下启动入口没有在同一脚本内把 {TRUSTPRESS_ENV} 透传给 "
        f"-{TRUSTPRESS_FLAG}：" + "、".join(state.switch_unwired_scripts)
    )


def sinker_order_warning(state: RepoState) -> Optional[str]:
    if state.sinker_init_order == SINKER_ORDER_AFTER_INIT:
        return (
            "❌ MultiSinker 注册晚于同文件的初始化入口：TrustPress handler 会在 init 期间"
            "读取 sinker，晚注册不会触发重试；请把 use_trustpress_external_storage 移到"
            " ArchonContext::init / GlobalContext::init / 父类资源 init 之前"
        )
    if state.sinker_init_order == SINKER_ORDER_INIT_NOT_FOUND:
        return (
            "⚠️ 已找到 MultiSinker，但同文件未识别到初始化入口，无法自动证明注册顺序；"
            "需人工确认调用发生在 Archon 或父类资源初始化之前"
        )
    return None


def dmon_warning(state: RepoState) -> Optional[str]:
    if not state.dmon_signals:
        return None
    return (
        "⚠️ 命中 dmon 老录制路线信号（" + "、".join(state.dmon_signals) + "）："
        "这是老 dmon 录制路线，与 archon::diff 新路线不是同一套东西，"
        "需要先和业务方确认迁移策略（并行保留 / 直接替换），不要当成已接入新路线"
    )


def build_only_manual_steps(state: RepoState) -> list[str]:
    """BUILD-only 仓的人工步骤清单：脚本不改 BUILD，只给可执行清单。"""
    steps = [
        "1. BUILD：在公共依赖列表（含所有独立链接的子目标）加 "
        f'"{BUILD_TARGET}"；缺的依赖按体检表补，'
        "固定分支不要改成 master",
        f"2. 注入点：在 {TRUSTPRESS_ANCHOR} 调用处注入 "
        f"{INJECTED_SINKER}（`use_trustpress_external_storage(std::make_shared<traffic_sinker::MultiSinker>())`），"
        "并确保它早于 ArchonContext::init / GlobalContext::init / 父类资源 init",
        "3. 启动脚本（`apps/<app>/run/real_run`）：加 "
        f"`{TRUSTPRESS_FLAG}=${{{TRUSTPRESS_ENV}:-false}}` 并透传 `-{TRUSTPRESS_FLAG}=${{{TRUSTPRESS_FLAG}}}`，默认关闭",
        "4. 录制参数（`conf/<cluster>/server.conf` 或 `apps/<app>/conf/app.conf`）：补 "
        + "、".join(TRUSTPRESS_CONF_KEYS),
        "5. 编译 + 本地起服务验证（符号里有 MultiSinker、没有 trustpress_databus::）",
    ]
    if state.shared_framework:
        steps = [
            "【可落业务仓】",
            "1. BUILD：加 " f'"{BUILD_TARGET}"（sinker 参与链接的目标都要加）',
            "2. 录制参数：`conf/<cluster>/server.conf` 或 `conf/app.conf` 补 "
            + "、".join(TRUSTPRESS_CONF_KEYS),
            "3. 启动脚本（本仓自带 `conf/real_run` / `run/*` 之类）：加 "
            f"`{TRUSTPRESS_FLAG}=${{{TRUSTPRESS_ENV}:-false}}` 默认关闭开关并透传 flag",
            "",
            "【必须落框架/common 仓，业务仓改不到】",
            f"4. sinker 注入：`{INJECTED_SINKER}` 注入到 {TRUSTPRESS_ANCHOR}，"
            f"建议落点 {SHARED_FRAMEWORK_INJECTION_HINT}，且必须早于父类/Archon 初始化；"
            f"Archon server 初始化实际在 {SHARED_FRAMEWORK_BOOTSTRAP}",
            "5. 该改动需框架 owner 确认：一处改动会影响所有下游服务，要先评估推全策略"
            "（默认关闭开关 + 灰度仓库列表），本路线暂无先例 MR，首个仓库需人工评审",
        ]
    return steps


def render_not_applicable(state: RepoState, fmt: str) -> str:
    reason = (
        f"本仓根目录既没有 {DEP_GRAPH_FILENAME} 也没有 {BUILD_FILENAME}，"
        "不是 C++ 服务仓（例如纯 CONFIG / 数据仓），Archon 流量录制不适用；"
        f"`blade_root/BLADE_ROOT.local` 之类的 *.blade 只带编译 flag，不是依赖图"
    )
    if fmt == "json":
        return json.dumps(
            {
                "source": state.source,
                "dep_layout": state.layout,
                "onboarding_status": state.onboarding_status,
                "onboarding_status_text": state.onboarding_status_text,
                "reason": reason,
                "needs_action": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    if fmt == "md":
        return "\n".join(
            [
                f"- 依赖图形态: **{state.layout}**",
                f"- 接入状态: **{state.onboarding_status}** — {state.onboarding_status_text}",
                f"- 结论: {reason}",
            ]
        )
    return "\n".join(
        [
            f"输入: {state.source}",
            f"依赖图形态: {state.layout}",
            f"接入状态: {state.onboarding_status} - {state.onboarding_status_text}",
            f"结论: {reason}",
        ]
    )


def render_text_build_only(state: RepoState) -> str:
    rows = [
        f"输入: {state.source}",
        f"依赖图形态: {state.layout}（无 {DEP_GRAPH_FILENAME}，只有 {BUILD_FILENAME}）",
        f"接入状态: {state.onboarding_status} - {state.onboarding_status_text}",
        "",
        "BUILD 没有 SHA pin，只判「存在性 + 分支名」；不输出 stale/latest，也不做 commit 祖先比较。",
        "",
        f"{'依赖':<32}{'结论':<20}{'BUILD 分支':<28}供给方",
    ]
    for dep in state.deps:
        rows.append(
            f"{dep.key:<32}{dep.status:<20}"
            f"{(dep.build_ref or '-')[:26]:<28}"
            f"{(dep.supplied_by or dep.alt_info or '-')}"
        )
    rows.append("")
    rows.extend(build_only_wiring_rows(state))
    if state.shared_framework:
        rows.extend(
            [
                "",
                "共享框架承载: 本仓没有自己的 int main / handler，Archon server 初始化由共享框架仓承载",
                "框架/common 依赖: " + "、".join(state.framework_targets),
                f"实际初始化位置: {SHARED_FRAMEWORK_BOOTSTRAP}",
            ]
        )
    for dep in state.deps:
        if dep.status == STATUS_BRANCH_MISMATCH:
            rows.append(
                f"!! {dep.key} 固定分支约束不满足: BUILD 声明 {dep.build_ref}，要求 {dep.ref}"
            )
        elif dep.status == STATUS_TRANSITIVE:
            rows.append(f"note: {dep.key} 由上游 target 传递供给（{dep.supplied_by}）")
        elif dep.status == STATUS_ABSENT_OPTIONAL:
            rows.append(f"note: {dep.key} 未在 BUILD 中声明，BUILD-only 仓通常不需要单独补")
        elif dep.status == STATUS_ALT:
            rows.append(f"note: {dep.key} 由 {dep.alt_key} 替代供给（{dep.alt_info}），需人工确认兼容性")
    for message in (
        dmon_warning(state),
        sinker_order_warning(state),
        switch_wiring_warning(state),
        switch_default_warning(state),
    ):
        if message:
            rows.extend(["", message])
    rows.extend(["", "依赖改写在 BUILD-only 形态下禁用（会误改 BUILD 语义），人工步骤清单："])
    rows.extend(f"  {step}" if step else "" for step in build_only_manual_steps(state))
    return "\n".join(rows)


def render_markdown_build_only(state: RepoState) -> str:
    rows = [
        f"- 依赖图形态: **{state.layout}**（无 `{DEP_GRAPH_FILENAME}`，只有 `{BUILD_FILENAME}`；"
        "依赖没有 SHA pin，只判存在性 + 分支名，不给 stale/latest 水位）",
        f"- 接入状态: **{state.onboarding_status}** — {state.onboarding_status_text}",
        "",
        "| 依赖 | 要求分支 | BUILD 声明分支 | 结论 | 供给方 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for dep in state.deps:
        supplier = dep.supplied_by or dep.alt_info or "-"
        rows.append(
            f"| `{dep.key}` | `{dep.ref}` | `{dep.build_ref or '-'}` | {dep.status} | `{supplier}` |"
        )
    rows.extend(
        [
            "",
            f"- 旧 sinker `{LEGACY_DEP}`: {'仍存在，需删除' if state.legacy_sinker else '未引入'}",
            f"- BUILD 接线: {'已接' if state.build_wired else '未接'}",
            f"- sinker 注入: {'已注入' if state.sinker_injected else '未注入'}",
            f"- sinker 注册顺序: `{state.sinker_init_order}`（必须早于初始化入口）",
            "- 录制开关: "
            + (
                "已接"
                + ("（默认关闭）" if state.switch_default_off else "（**默认值不是 false**）")
                if state.switch_wired
                else "未接"
            ),
            f"- 录制参数: {'已配齐' if state.conf_wired else '缺 ' + ', '.join(state.missing_conf_keys)}",
        ]
    )
    if state.shared_framework:
        rows.extend(
            [
                "",
                "- ⚠️ **共享框架承载**：本仓没有自己的 `int main` / handler，"
                f"Archon server 初始化由共享框架仓承载（依赖 {'、'.join(f'`{t}`' for t in state.framework_targets)}，"
                f"实际初始化在 {SHARED_FRAMEWORK_BOOTSTRAP}）。"
                "sinker 注入改不到业务仓，必须由框架 owner 在框架/common 仓落地；"
                "该路线**暂无先例 MR**，首个仓库需人工评审 + 框架 owner 确认后再推全。",
            ]
        )
    for message in (
        dmon_warning(state),
        sinker_order_warning(state),
        switch_wiring_warning(state),
        switch_default_warning(state),
    ):
        if message:
            rows.extend(["", f"- {message}"])
    rows.extend(
        [
            "",
            "## 改动清单（BUILD-only：脚本不自动改写依赖）",
            "",
        ]
    )
    # 清单本身已带编号 / 分栏标题，直接原样输出，不再叠一层 `- ` 列表标记。
    rows.extend(f"**{step}**" if step.startswith("【") else step for step in build_only_manual_steps(state))
    return "\n".join(rows)


def render_json_build_only(state: RepoState) -> str:
    payload = {
        "source": state.source,
        "dep_layout": state.layout,
        "onboarding_status": state.onboarding_status,
        "onboarding_status_text": state.onboarding_status_text,
        "deps": [
            {
                "key": dep.key,
                "required_ref": dep.ref,
                "build_ref": dep.build_ref,
                "status": dep.status,
                "supplied_by": dep.supplied_by or dep.alt_info,
                "optional": dep.optional,
            }
            for dep in state.deps
        ],
        "legacy_sinker": state.legacy_sinker,
        "legacy_wired": state.legacy_wired,
        "build_wired": state.build_wired,
        "sinker_injected": state.sinker_injected,
        "sinker_init_order": state.sinker_init_order,
        "switch_wired": state.switch_wired,
        "switch_default_off": state.switch_default_off,
        "switch_candidate_scripts": state.switch_candidate_scripts,
        "switch_unwired_scripts": state.switch_unwired_scripts,
        "switch_unsafe_default_scripts": state.switch_unsafe_default_scripts,
        "conf_wired": state.conf_wired,
        "missing_conf_keys": state.missing_conf_keys,
        "min_archon_version": MIN_ARCHON_VERSION,
        "apply_supported": False,
        "gate_checked": False,
        "gate_not_applicable_reason": f"{BUILD_FILENAME} 里的依赖没有 SHA pin，无法做 commit 祖先比较",
        "shared_framework": state.shared_framework,
        "framework_targets": state.framework_targets,
        "has_own_entrypoint": state.has_own_entrypoint,
        "dmon_legacy_signals": state.dmon_signals,
        "build_only_todo": [dep.key for dep in state.build_only_todo],
        "alt_supplied": [
            {"key": dep.key, "supplied_by": dep.alt_key, "info": dep.alt_info}
            for dep in state.alt_supplied
        ],
        "manual_steps": [step for step in build_only_manual_steps(state) if step],
        "needs_action": state.needs_action,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_text(
    state: RepoState, edits: list[tuple[str, DepState, str]], manual: list[DepState]
) -> str:
    header = f"{'依赖':<32}{'状态':<14}{'当前':<12}{'远端 HEAD':<12}{'参考值':<12}"
    rows = [
        f"输入: {state.source}",
        f"接入状态: {state.onboarding_status} - {state.onboarding_status_text}",
        "",
        header + ("下限校验" if state.gate_checked else ""),
    ]
    for dep in state.deps:
        rows.append(
            f"{dep.key:<32}{dep.status:<14}"
            f"{(dep.current_commit or ('->' + dep.alt_key if dep.alt_key else '-'))[:10]:<12}"
            f"{(dep.remote_head or '未解析')[:10]:<12}{dep.reference_commit[:10]:<12}"
            f"{dep.gate or ''}"
        )
    rows.extend(
        [
            "",
            f"onboarding_status: {state.onboarding_status} ({state.onboarding_status_text})",
            f"legacy_sinker({LEGACY_DEP}): {state.legacy_sinker}",
            f"legacy_wired(BUILD/代码仍引用旧 sinker): "
            f"{state.legacy_wired if state.local else '未检查(MR 模式)'}",
            f"build_wired(BUILD 含 traffic_sinker 目标): "
            f"{state.build_wired if state.local else '未检查(MR 模式)'}",
            f"sinker_injected(代码注入 MultiSinker): "
            f"{state.sinker_injected if state.local else '未检查(MR 模式)'}",
            f"sinker_init_order(必须早于 Archon/全局/父类 init): "
            f"{state.sinker_init_order if state.local else '未检查(MR 模式)'}",
            f"switch_wired({TRUSTPRESS_ENV} 默认关闭并透传 flag): "
            f"{state.switch_wired if state.local else '未检查(MR 模式)'}",
            f"switch_default_off(存在 ${{{TRUSTPRESS_ENV}:-false}} 形态): "
            f"{state.switch_default_off if state.local else '未检查(MR 模式)'}",
            f"switch_candidate_scripts: {','.join(state.switch_candidate_scripts) if state.switch_candidate_scripts else '-'}",
            f"switch_unwired_scripts: {','.join(state.switch_unwired_scripts) if state.switch_unwired_scripts else '-'}",
            f"switch_unsafe_default_scripts: {','.join(state.switch_unsafe_default_scripts) if state.switch_unsafe_default_scripts else '-'}",
            f"conf_wired(录制参数齐全): "
            f"{state.conf_wired if state.local else '未检查(MR 模式)'}",
            f"missing_conf_keys: {','.join(state.missing_conf_keys) if state.missing_conf_keys else '-'}",
            f"archon 最低版本要求: {MIN_ARCHON_VERSION}",
        ]
    )
    if state.gate_checked:
        failures = state.gate_failures
        rows.append(
            "下限校验: 全部 >= 技能参考 commit"
            if not failures
            else "下限校验未通过: " + "、".join(f"{dep.key}({dep.gate})" for dep in failures)
        )
        if state.gate_unclear:
            rows.append(
                "下限校验无法判定: "
                + "、".join(f"{dep.key}({dep.gate})" for dep in state.gate_unclear)
            )
    rows.extend(render_change_links(state, collect_changes(state, edits)))
    if edits:
        rows.append("")
        rows.append("待改写条目(目标值来自远端 HEAD):")
        rows.extend(f"  {kind:<8}{dep.key} -> {commit}" for kind, dep, commit in edits)
    if state.ref_based:
        rows.append("")
        rows.append("!! 未能解析远端 HEAD，以下结论基于可能已过期的参考值，请业务方自行确认 !!")
    if manual:
        rows.append("")
        rows.append("需人工判定(结论来自参考值，不代表已是最新):")
        rows.extend(
            f"  {dep.key}#{dep.ref}: "
            f"当前 {dep.current_commit or ('由 ' + dep.alt_key + ' 供给' if dep.alt_key else '缺失')}"
            f" / 参考 {dep.reference_commit}"
            for dep in manual
        )
    return "\n".join(rows)


def render_markdown(state: RepoState, edits: list[tuple[str, DepState, str]]) -> str:
    gate_col = " 下限校验 |" if state.gate_checked else ""
    gate_sep = " --- |" if state.gate_checked else ""
    rows = [
        f"- 接入状态: **{state.onboarding_status}** — {state.onboarding_status_text}",
        "",
        "| 依赖 | 分支 | 当前 commit | 远端 HEAD | 状态 |" + gate_col,
        "| --- | --- | --- | --- | --- |" + gate_sep,
    ]
    for dep in state.deps:
        rows.append(
            f"| `{dep.key}` | `{dep.ref}` "
            f"| `{dep.current_commit[:10] if dep.current_commit else ('由 ' + dep.alt_key if dep.alt_key else '缺失')}` "
            f"| `{(dep.remote_head or '未解析')[:10]}` | {dep.status} |"
            + (f" {dep.gate} |" if state.gate_checked else "")
        )
    rows.extend(
        [
            "",
            f"- 旧 sinker `{LEGACY_DEP}`: "
            f"{'仍存在，需删除' if state.legacy_sinker else '已移除'}",
            f"- 旧 sinker 引用: {('仍存在，需替换' if state.legacy_wired else '已清理') if state.local else '未检查（MR 模式）'}",
            f"- BUILD 接线: {('已接' if state.build_wired else '未接') if state.local else '未检查（MR 模式）'}",
            f"- sinker 注入: {('已注入' if state.sinker_injected else '未注入') if state.local else '未检查（MR 模式）'}",
            f"- sinker 注册顺序: {('`' + state.sinker_init_order + '`（必须早于初始化入口）') if state.local else '未检查（MR 模式）'}",
            f"- 录制开关: {('已接' + ('（默认关闭）' if state.switch_default_off else '（**默认值不是 false**）') if state.switch_wired else '未接') if state.local else '未检查（MR 模式）'}",
            f"- 录制参数: {('已配齐' if state.conf_wired else '缺 ' + ', '.join(state.missing_conf_keys)) if state.local else '未检查（MR 模式）'}",
            "- 本次未取到远端 HEAD，下表结论基于内置参考 commit"
            if state.ref_based
            else "- 目标值为执行时从各依赖分支解析的远端 HEAD",
        ]
    )
    for dep in state.alt_supplied:
        rows.append(
            f"- ⚠️ `{dep.key}` 未在 `{DEP_GRAPH_FILENAME}` 中，改由 `{dep.alt_key}` 供给"
            f"（`{dep.alt_info}`）：这是另一条供给路径（通常是 bpt 包），"
            f"无法与 git 参考 commit 比较，**需人工确认它满足 archon 的兼容版本要求**，"
            f"不要直接补一个 `{dep.key}` 条目上去（两份 folly/fbthrift 同时存在会冲突）"
        )
    if state.gate_checked:
        failures = state.gate_failures
        rows.append(
            "- 下限校验（必须 >= 技能内置参考 commit）: "
            + (
                "✅ 全部通过"
                if not failures
                else "❌ " + "、".join(f"`{dep.key}`({dep.gate})" for dep in failures)
            )
        )
        if state.gate_unclear:
            rows.append(
                "- 下限校验无法判定: "
                + "、".join(f"`{dep.key}`({dep.gate})" for dep in state.gate_unclear)
            )
    if state.ref_based:
        # 直接产出可粘贴进 MR 描述的醒目警告，状态带 "?" 的项列出来。
        rows.extend(
            [
                "",
                f"> {REF_FALLBACK_WARNING}",
                ">",
                "> 待确认依赖："
                + "、".join(f"`{dep.key}#{dep.ref}`" for dep in state.ref_based),
            ]
        )
    if state.local and sinker_order_warning(state):
        rows.extend(["", f"> {sinker_order_warning(state)}"])
    rows.extend(render_change_links(state, collect_changes(state, edits)))
    return "\n".join(rows)


def render_json(
    state: RepoState, edits: list[tuple[str, DepState, str]], manual: list[DepState]
) -> str:
    payload = {
        "deps": [
            {
                "key": dep.key,
                "ref": dep.ref,
                "current_commit": dep.current_commit,
                "previous_commit": dep.previous_commit,
                "remote_head": dep.remote_head,
                "reference_commit": dep.reference_commit,
                "status": dep.status,
                "gate": dep.gate,
            }
            for dep in state.deps
        ],
        "source": state.source,
        "onboarding_status": state.onboarding_status,
        "onboarding_status_text": state.onboarding_status_text,
        "legacy_sinker": state.legacy_sinker,
        "legacy_wired": state.legacy_wired if state.local else None,
        "build_wired": state.build_wired if state.local else None,
        "sinker_injected": state.sinker_injected if state.local else None,
        "sinker_init_order": state.sinker_init_order if state.local else None,
        "switch_wired": state.switch_wired if state.local else None,
        "switch_default_off": state.switch_default_off if state.local else None,
        "switch_candidate_scripts": state.switch_candidate_scripts if state.local else None,
        "switch_unwired_scripts": state.switch_unwired_scripts if state.local else None,
        "switch_unsafe_default_scripts": (
            state.switch_unsafe_default_scripts if state.local else None
        ),
        "conf_wired": state.conf_wired if state.local else None,
        "missing_conf_keys": state.missing_conf_keys if state.local else None,
        "min_archon_version": MIN_ARCHON_VERSION,
        "offline": state.offline,
        "planned_edits": [
            {"kind": kind, "key": dep.key, "commit": commit} for kind, dep, commit in edits
        ],
        "changes": [
            {
                "key": change.key,
                "from": change.old,
                "to": change.new,
                "link": compare_link(state.web_base, change.key, change.old, change.new)
                if change.old and change.new
                else repo_link(state.web_base, change.key, change.ref),
            }
            for change in collect_changes(state, edits)
        ],
        "alt_supplied": [
            {"key": dep.key, "supplied_by": dep.alt_key, "info": dep.alt_info}
            for dep in state.alt_supplied
        ],
        "gate_checked": state.gate_checked,
        "gate_failures": [dep.key for dep in state.gate_failures],
        "gate_unclear": [dep.key for dep in state.gate_unclear],
        "needs_manual_review": [dep.key for dep in manual],
        "ref_based_conclusion": [dep.key for dep in state.ref_based],
        "ref_fallback_warning": REF_FALLBACK_WARNING if state.ref_based else None,
        "needs_action": state.needs_action,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def load_required_deps(path: Optional[str]) -> dict[str, dict[str, str]]:
    if not path:
        return REQUIRED_DEPS
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="核对/改写 Archon 流量录制链路依赖")
    parser.add_argument("--repo", default=".", help="业务仓库根目录，默认当前目录")
    parser.add_argument(
        "--mr",
        help="直接校验一个 MR（Codebase merge_requests 链接），无需本地 clone 业务仓库",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="下限校验：每个依赖必须 >= 技能内置参考 commit（按祖先关系判定）",
    )
    parser.add_argument("--git-base", help="依赖仓库 git 地址前缀，默认从 origin / MR host 推导")
    parser.add_argument("--web-base", help="生成 CR 链接用的 web 前缀，默认从 git 地址推导")
    parser.add_argument("--deps", help="自定义依赖清单 JSON，覆盖内置 REQUIRED_DEPS")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="跳过远端解析；结论退回参考水位并附警告，只有缺失项会用参考值补齐",
    )
    parser.add_argument("--apply", action="store_true", help="写回 dep_graph.blade")
    parser.add_argument("--dry-run", action="store_true", help="打印将要改写的内容，不落盘")
    parser.add_argument("--format", choices=["text", "md", "json"], default="text")
    return parser


def run_non_dep_graph(args, required: dict[str, dict[str, str]], repo_dir: str, layout: str) -> int:
    """dep_graph.blade 之外的两种形态：unsupported 软退出，build_only 只体检不改写。"""
    if layout == LAYOUT_UNSUPPORTED:
        state = inspect_unsupported(repo_dir)
        print(render_not_applicable(state, args.format))
        return EXIT_OK

    state = inspect_build_only(repo_dir, required)
    if args.web_base:
        state.web_base = args.web_base if args.web_base.endswith("/") else args.web_base + "/"
    if args.format == "json":
        print(render_json_build_only(state))
    elif args.format == "md":
        print(render_markdown_build_only(state))
    else:
        print(render_text_build_only(state))

    if args.verify:
        warn(
            f"{BUILD_FILENAME} 里的依赖没有 SHA pin，--verify 的下限校验（commit 祖先比较）不适用；"
            "本次只给出「存在性 + 分支名」体检结论"
        )
    if state.dmon_signals:
        warn("命中 dmon 老录制路线信号: " + "、".join(state.dmon_signals) + "，需确认迁移策略")
    for message in (switch_wiring_warning(state), switch_default_warning(state)):
        if message:
            warn(message)
    order_warning = sinker_order_warning(state)
    if order_warning:
        warn(order_warning)
    if args.apply or args.dry_run:
        raise UsageError(
            f"BUILD-only 仓（无 {DEP_GRAPH_FILENAME}）不支持 --apply / --dry-run："
            f"BUILD 是构建脚本，自动改写会误改语义。请按上面的人工步骤清单手工改动"
        )
    return EXIT_TODO if state.needs_action else EXIT_OK


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    required = load_required_deps(args.deps)

    repo_dir = os.path.abspath(args.repo)
    if args.mr:
        if args.apply or args.dry_run:
            raise UsageError("--mr 是只读校验入口，改写请用 --repo 指向本地仓库")
        state = inspect_mr(args.mr, required, args.offline, args.verify, args.git_base)
    else:
        layout = detect_dep_layout(repo_dir)
        if layout != LAYOUT_DEP_GRAPH:
            return run_non_dep_graph(args, required, repo_dir, layout)
        state = inspect_local(repo_dir, required, args.offline, args.verify)
        if args.git_base:
            state.web_base = state.web_base or web_base_from_ssh(args.git_base)
    if args.web_base:
        state.web_base = args.web_base if args.web_base.endswith("/") else args.web_base + "/"

    edits, manual = plan_edits(state)

    if args.format == "json":
        print(render_json(state, edits, manual))
    elif args.format == "md":
        print(render_markdown(state, edits))
    else:
        print(render_text(state, edits, manual))

    if state.ref_based:
        warn(
            f"{len(state.ref_based)} 个依赖未能解析远端 HEAD，结论退回参考水位且不做自动改写；"
            "参考值可能已过期，务必把输出里的警告一并贴进 MR 描述，或联网重跑取最新值"
        )

    if state.gate_checked and state.gate_failures:
        warn(
            f"{len(state.gate_failures)} 个依赖低于技能内置参考 commit: "
            + "、".join(dep.key for dep in state.gate_failures)
        )

    for message in (switch_wiring_warning(state), switch_default_warning(state)):
        if message:
            warn(message)
    order_warning = sinker_order_warning(state)
    if order_warning:
        warn(order_warning)

    if not (args.apply or args.dry_run):
        if state.gate_checked and state.gate_failures:
            return EXIT_GATE_FAILED
        return EXIT_TODO if state.needs_action else EXIT_OK

    if not edits and not state.legacy_sinker:
        print(f"\n{DEP_GRAPH_FILENAME} 无需改动")
        return EXIT_TODO if manual else EXIT_OK

    rewritten = rewrite_dep_graph(repo_dir, edits, state.legacy_sinker)
    graph_path = os.path.join(repo_dir, DEP_GRAPH_FILENAME)
    if args.dry_run:
        print(f"\n--dry-run: {graph_path} 将被改写，共 {len(edits)} 处版本变更")
        return EXIT_OK

    with open(graph_path, "w", encoding="utf-8") as handle:
        handle.write(rewritten)
    print(f"\n已改写 {graph_path}")
    if state.legacy_wired:
        print("提醒: BUILD/代码里仍引用 trustpress_databus_lib，需要替换成 traffic_sinker_lib/MultiSinker")
    if not state.build_wired:
        print(f"提醒: BUILD 里还需加目标 {BUILD_TARGET}")
    if not state.sinker_injected:
        print(f"提醒: 还需在 {TRUSTPRESS_ANCHOR} 调用处注入 {INJECTED_SINKER}")
    elif state.sinker_init_order != SINKER_ORDER_BEFORE_INIT:
        print("提醒: 需把 sinker 注册移动到 Archon/全局/父类资源初始化之前")
    if not state.switch_wired:
        print(f"提醒: 启动脚本还需用 {TRUSTPRESS_ENV} 默认 false 并透传 -{TRUSTPRESS_FLAG}")
    if not state.conf_wired:
        print("提醒: server.conf 还需补录制参数 " + ",".join(state.missing_conf_keys))
    return EXIT_OK


def cli(argv: Optional[list[str]] = None) -> int:
    """把用法 / 环境错误收敛成 EXIT_USAGE + 可读消息，不给用户抛 traceback。"""
    try:
        return main(argv)
    except UsageError as err:
        print(f"error: {err}", file=sys.stderr)
        return EXIT_USAGE
    except KeyboardInterrupt:
        print("error: 已中断", file=sys.stderr)
        return EXIT_USAGE
    except Exception as err:  # noqa: BLE001 - 顶层兜底：只输出可读错误，不打 traceback
        print(f"error: {type(err).__name__}: {err}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(cli())
