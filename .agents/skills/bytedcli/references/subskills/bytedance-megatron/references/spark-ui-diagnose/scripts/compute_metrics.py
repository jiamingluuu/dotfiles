#!/usr/bin/env python3
"""Pure calculator for Spark-app derived metrics.

This does NOT diagnose and does NOT decide what to fetch — that is the agent's
job (see ../GUIDE.md). It only turns already-fetched `bytedcli megatron spark-ui`
JSON into the deterministic numbers a diagnosis leans on: wall-clock duration,
per-job ranking, CPU utilization, peak-memory-vs-configured, GC ratio, shuffle
volume, and executor removal-reason classification.

Feed it whatever resource JSON you have; missing inputs are skipped (mirrors the
"use alternate evidence" principle — partial data still yields partial metrics).

Usage:
  python3 compute_metrics.py --jobs jobs.json [--executors exec.json] [--env env.json] [--json]

Each input file is the `-j` output of the corresponding `spark-ui` command
(the {status,data,error,context} envelope; `data` is unwrapped automatically).
"""
import argparse
import json
import re
import sys
from datetime import datetime
from typing import Any, Optional

BYTES_UNITS = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
MEM_RE = re.compile(r"^\s*([0-9.]+)\s*([kmgtKMGT]?)[bB]?\s*$")


def load_data(path: Optional[str]) -> Any:
    """Read a spark-ui -j file and unwrap the envelope's `data`."""
    if not path:
        return None
    try:
        with open(path) as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"# skip {path}: {e}", file=sys.stderr)
        return None
    if isinstance(payload, dict) and "status" in payload:
        if payload.get("status") != "success":
            print(f"# skip {path}: status={payload.get('status')}", file=sys.stderr)
            return None
        return payload.get("data")
    return payload


def hb(n: float) -> str:
    n = float(n or 0)
    if n <= 0:
        return "0"
    i = 0
    while n >= 1024 and i < len(BYTES_UNITS) - 1:
        n /= 1024
        i += 1
    return f"{n:.1f}{BYTES_UNITS[i]}"


def hms(ms: float) -> str:
    s = (ms or 0) / 1000.0
    if s < 60:
        return f"{s:.0f}s"
    if s < 3600:
        return f"{int(s // 60)}m{int(s % 60)}s"
    return f"{int(s // 3600)}h{int((s % 3600) // 60)}m"


def parse_mem_bytes(v: Optional[str]) -> Optional[float]:
    if not v:
        return None
    m = MEM_RE.match(str(v))
    if not m:
        return None
    mult = {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}[m.group(2).lower()]
    return float(m.group(1)) * mult


def ts(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("GMT", "").rstrip("Z"))
    except ValueError:
        return None


def classify_removal(reason: str) -> str:
    r = reason.lower()
    if re.search(r"cgroup memory|memory overhead|outofmemory|exceeding .*memory|memory limit", r):
        return "OOM (out of memory)"
    if "killed by driver" in r:
        return "scaled down (driver)"
    if re.search(r"evict|preempt|exitcode=-22001|marked as failed|external signal", r):
        return "evicted / preempted"
    return "other"


def metrics(jobs, execs, env) -> dict:
    out: dict[str, Any] = {}

    if jobs is not None:
        subs = [ts(j.get("submissionTime")) for j in jobs if ts(j.get("submissionTime"))]
        comps = [ts(j.get("completionTime")) for j in jobs if ts(j.get("completionTime"))]
        wall_s = (max(comps) - min(subs)).total_seconds() if subs and comps else None
        job_durs = []
        for j in jobs:
            s, c = ts(j.get("submissionTime")), ts(j.get("completionTime"))
            job_durs.append({
                "jobId": j.get("jobId"), "status": j.get("status"),
                "durationS": round((c - s).total_seconds()) if s and c else None,
                "numTasks": j.get("numTasks", 0), "numFailedTasks": j.get("numFailedTasks", 0),
                "stageIds": j.get("stageIds"), "name": (j.get("name") or "")[:70],
            })
        job_durs.sort(key=lambda r: (r["durationS"] or -1), reverse=True)
        out["jobs"] = {
            "total": len(jobs),
            "failed": sum(1 for j in jobs if (j.get("status") or "").upper() == "FAILED"),
            "wallClockS": round(wall_s) if wall_s else None,
            "byDurationDesc": job_durs,
        }

    if execs is not None:
        real = [e for e in execs if e.get("id") != "driver"]
        cores = sum(e.get("totalCores", 0) or 0 for e in real)
        task_ms = sum(e.get("totalDuration", 0) or 0 for e in real)
        gc_ms = sum(e.get("totalGCTime", 0) or 0 for e in real)
        peak = max((max((e.get("peakMemoryMetrics") or {}).get("JVMHeapMemory", 0) or 0,
                         e.get("memoryUsed", 0) or 0) for e in real), default=0)
        removal: dict[str, int] = {}
        for e in real:
            rr = e.get("removeReason")
            if rr:
                removal[classify_removal(rr)] = removal.get(classify_removal(rr), 0) + 1
        out["executors"] = {
            "total": len(real),
            "dead": sum(1 for e in real if e.get("isActive") is False),
            "cores": cores,
            "failedTasks": sum(e.get("failedTasks", 0) or 0 for e in real),
            "taskComputeS": round(task_ms / 1000),
            "gcRatio": round(gc_ms / task_ms, 4) if task_ms else None,
            "peakMemBytes": peak,
            "removalBreakdown": removal,
        }
        out["shuffle"] = {
            "inputBytes": sum(e.get("totalInputBytes", 0) or 0 for e in real),
            "readBytes": sum(e.get("totalShuffleRead", 0) or 0 for e in real),
            "writeBytes": sum(e.get("totalShuffleWrite", 0) or 0 for e in real),
        }

    if env is not None and isinstance(env, dict):
        props = {p[0]: p[1] for p in (env.get("sparkProperties") or [])
                 if isinstance(p, list) and len(p) >= 2}
        out["config"] = {k: props.get(k) for k in [
            "spark.executor.memory", "spark.executor.cores", "spark.executor.instances",
            "spark.dynamicAllocation.maxExecutors", "spark.sql.shuffle.partitions",
        ]}
        cfg_mem = parse_mem_bytes(props.get("spark.executor.memory"))
        out.setdefault("config", {})["executorMemoryBytes"] = cfg_mem

    # cross-resource derived: mem ratio + cpu util (only when inputs allow)
    ex = out.get("executors")
    if ex and out.get("config", {}).get("executorMemoryBytes"):
        cfg_mem = out["config"]["executorMemoryBytes"]
        out["derived"] = out.get("derived", {})
        out["derived"]["peakMemRatio"] = round(ex["peakMemBytes"] / cfg_mem, 3) if cfg_mem else None
    if ex and out.get("jobs", {}).get("wallClockS") and ex["cores"]:
        wall_ms = out["jobs"]["wallClockS"] * 1000
        out.setdefault("derived", {})["cpuUtilLowerBound"] = round(
            ex["taskComputeS"] * 1000 / (wall_ms * ex["cores"]), 4)
    return out


def to_text(d: dict) -> str:
    lines = ["# Derived metrics (numbers only — diagnosis is the agent's job)"]
    j = d.get("jobs")
    if j:
        lines.append(f"jobs: total={j['total']} failed={j['failed']} wall={hms((j['wallClockS'] or 0)*1000)}")
        for r in j["byDurationDesc"][:6]:
            lines.append(f"  job {r['jobId']}: {r['status']} dur={hms((r['durationS'] or 0)*1000)} "
                         f"tasks={r['numTasks']} failed={r['numFailedTasks']} stages={r['stageIds']} {r['name']}")
    ex = d.get("executors")
    if ex:
        gc = f"{ex['gcRatio'] * 100:.1f}%" if ex["gcRatio"] is not None else "n/a"
        lines.append(f"executors: total={ex['total']} dead={ex['dead']} cores={ex['cores']} "
                     f"failedTasks={ex['failedTasks']} taskCompute={hms(ex['taskComputeS'] * 1000)} "
                     f"gcRatio={gc} peakMem={hb(ex['peakMemBytes'])}")
        if ex["removalBreakdown"]:
            lines.append("  removals: " + ", ".join(f"{k}={v}" for k, v in
                         sorted(ex["removalBreakdown"].items(), key=lambda kv: -kv[1])))
    sh = d.get("shuffle")
    if sh:
        lines.append(f"shuffle: read={hb(sh['readBytes'])} write={hb(sh['writeBytes'])} input={hb(sh['inputBytes'])}")
    cfg = d.get("config")
    if cfg:
        lines.append("config: " + json.dumps({k: v for k, v in cfg.items() if k != "executorMemoryBytes"}, ensure_ascii=False))
    dv = d.get("derived", {})
    if "peakMemRatio" in dv:
        lines.append(f"peak mem / configured = {dv['peakMemRatio']*100:.0f}%")
    if "cpuUtilLowerBound" in dv:
        lines.append(f"CPU util (lower bound, dynamic-alloc caveat) = {dv['cpuUtilLowerBound']*100:.1f}%")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute derived Spark metrics from spark-ui JSON.")
    ap.add_argument("--jobs")
    ap.add_argument("--executors")
    ap.add_argument("--env")
    ap.add_argument("--json", action="store_true", help="Emit structured JSON instead of text.")
    args = ap.parse_args()
    if not any([args.jobs, args.executors, args.env]):
        ap.error("provide at least one of --jobs / --executors / --env")
    d = metrics(load_data(args.jobs), load_data(args.executors), load_data(args.env))
    print(json.dumps(d, ensure_ascii=False, indent=2) if args.json else to_text(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
