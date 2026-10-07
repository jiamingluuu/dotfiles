#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Set, Tuple

DEFAULT_BATCH_SIZE = 10
MAX_BATCH_SIZE = 100
DEFAULT_RETRY_COUNT = 3


class CommandError(Exception):
    def __init__(self, command: List[str], returncode: int, stdout: str, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(f"command failed with exit code {returncode}: {' '.join(command)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch forge Wandb/TensorBoard queries into one consolidated output directory."
    )
    parser.add_argument("--forge", default="forge", help="forge binary to invoke")
    parser.add_argument("--source", required=True, choices=["wandb", "tensorboard"])
    parser.add_argument("--job-id", required=True, type=int)
    parser.add_argument("--data-type", required=True, choices=["scalar", "histogram", "image"])
    parser.add_argument(
        "--output",
        help="final consolidated output directory; defaults to <temp>/forge/series/<source>-<data_type>-<job_id>",
    )
    parser.add_argument(
        "--paths",
        action="append",
        default=[],
        help="one exact explicit path (repeat for multiple paths); if omitted, the script discovers paths via get-meta",
    )
    parser.add_argument(
        "--paths-file",
        help="newline-delimited file of explicit paths; blank lines and lines starting with # are ignored",
    )
    parser.add_argument(
        "--path-contains",
        action="append",
        default=[],
        help="keep only paths containing at least one of these substrings",
    )
    parser.add_argument(
        "--path-exclude",
        action="append",
        default=[],
        help="drop paths containing any of these substrings",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"paths per query batch; defaults to {DEFAULT_BATCH_SIZE} and must be between 1 and {MAX_BATCH_SIZE}",
    )
    parser.add_argument(
        "--request-interval-seconds",
        type=float,
        default=1.0,
        help="minimum delay between successful query requests; defaults to 1.0",
    )
    parser.add_argument(
        "--retry-count",
        type=int,
        default=DEFAULT_RETRY_COUNT,
        help=f"retry attempts per failed query batch; defaults to {DEFAULT_RETRY_COUNT}",
    )
    parser.add_argument(
        "--retry-base-delay-seconds",
        type=float,
        default=5.0,
        help="initial retry delay in seconds; defaults to 5.0",
    )
    parser.add_argument(
        "--retry-max-delay-seconds",
        type=float,
        default=60.0,
        help="maximum retry delay in seconds; defaults to 60.0",
    )
    parser.add_argument("--json", action="store_true", help="write per-path data files as JSONL instead of CSV")
    parser.add_argument("--step-min", type=int)
    parser.add_argument("--step-max", type=int)
    parser.add_argument("--event-time-min", type=int)
    parser.add_argument("--event-time-max", type=int)
    parser.add_argument("--network")
    parser.add_argument("--site")
    return parser


def print_error(message: str, hint: str = "", exit_code: int = 2) -> None:
    payload = {
        "ok": False,
        "error": {
            "type": "validation" if exit_code == 2 else "error",
            "message": message,
        },
    }
    if hint:
        payload["error"]["hint"] = hint
    sys.stderr.write(json.dumps(payload, indent=2) + "\n")
    raise SystemExit(exit_code)


def write_json(path: str, payload: object) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def write_jsonl(path: str, items: Iterable[object]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item))
            handle.write("\n")


def write_text_lines(path: str, items: Iterable[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for item in items:
            handle.write(item)
            handle.write("\n")


def canonicalize_output_dir(path: str) -> str:
    return os.path.realpath(os.path.abspath(path))


def default_output_dir(source: str, data_type: str, job_id: int) -> str:
    # Mirror the CLI default: os.TempDir()/forge/series/<source>-<data_type>-<job_id>.
    # tempfile.gettempdir() is the Python equivalent of Go's os.TempDir() (both
    # honor $TMPDIR), so the helper and the CLI agree on the output location.
    return canonicalize_output_dir(
        os.path.join(tempfile.gettempdir(), "forge", "series", f"{source}-{data_type}-{job_id}")
    )


def normalize_explicit_paths(values: Iterable[str]) -> List[str]:
    return [value.strip() for value in values if value.strip()]


def dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def load_paths_file(path: str) -> List[str]:
    result: List[str] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            result.append(line)
    return result


def apply_path_filters(paths: List[str], includes: List[str], excludes: List[str]) -> List[str]:
    filtered = paths
    if includes:
        filtered = [path for path in filtered if any(token in path for token in includes)]
    if excludes:
        filtered = [path for path in filtered if not any(token in path for token in excludes)]
    return filtered


def chunked(values: List[str], size: int) -> Iterable[List[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def build_base_command(args: argparse.Namespace) -> List[str]:
    command = [args.forge]
    if args.network:
        command.extend(["--network", args.network])
    if args.site:
        command.extend(["--site", args.site])
    return command


def command_text(command: List[str]) -> str:
    return " ".join(command)


def run_json_command(command: List[str]) -> dict:
    sys.stderr.write(f"$ {' '.join(command)}\n")
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        if completed.stdout:
            sys.stderr.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        raise CommandError(command, completed.returncode, completed.stdout, completed.stderr)
    if not completed.stdout.strip():
        print_error(f"expected JSON stdout from command: {' '.join(command)}", exit_code=1)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        print_error(f"failed to parse JSON stdout from command: {exc}", exit_code=1)


def command_error_payload(error: CommandError) -> dict:
    return {
        "command": error.command,
        "returncode": error.returncode,
        "stdout_tail": error.stdout[-4000:] if error.stdout else "",
        "stderr_tail": error.stderr[-4000:] if error.stderr else "",
    }


def is_transient_command_error(error: CommandError) -> bool:
    text = f"{error.stdout}\n{error.stderr}".lower()
    if "rate limit" in text or "rate-limited" in text or "too many requests" in text:
        return True
    if re.search(r"\bhttp\s*429\b|\bstatus(?: code)?\s*[:=]?\s*429\b", text):
        return True
    if re.search(r"\bhttp\s*5\d\d\b|\bstatus(?: code)?\s*[:=]?\s*5\d\d\b", text):
        return True
    return False


def retry_delay_seconds(args: argparse.Namespace, attempt: int) -> float:
    delay = args.retry_base_delay_seconds * (2 ** max(0, attempt - 1))
    return min(delay, args.retry_max_delay_seconds)


def run_query_with_retries(args: argparse.Namespace, command: List[str]) -> dict:
    attempt = 0
    while True:
        try:
            return run_json_command(command)
        except CommandError as exc:
            attempt += 1
            if attempt > args.retry_count or not is_transient_command_error(exc):
                raise
            delay = retry_delay_seconds(args, attempt)
            sys.stderr.write(
                f"query failed with a transient error; retry {attempt}/{args.retry_count} "
                f"after {delay:.1f}s: {command_text(command)}\n"
            )
            time.sleep(delay)


def discover_paths(args: argparse.Namespace) -> List[str]:
    explicit_paths = normalize_explicit_paths(args.paths)
    if args.paths_file:
        explicit_paths.extend(load_paths_file(args.paths_file))
    explicit_paths = dedupe_preserve_order(explicit_paths)
    if explicit_paths:
        return explicit_paths

    command = build_base_command(args) + [
        "job",
        args.source,
        "get-meta",
        "--job-id",
        str(args.job_id),
        "--data-type",
        args.data_type,
    ]
    try:
        response = run_json_command(command)
    except CommandError as exc:
        raise SystemExit(exc.returncode)
    paths = response.get("paths") or []
    return dedupe_preserve_order(str(path).strip() for path in paths if str(path).strip())


def remove_path(path: str) -> None:
    if not os.path.lexists(path):
        return
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
        return
    os.remove(path)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: str) -> List[dict]:
    items: List[dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def data_file_ext(as_json: bool) -> str:
    return "jsonl" if as_json else "csv"


def request_fingerprint(args: argparse.Namespace, requested_paths: List[str]) -> dict:
    return {
        "job_id": args.job_id,
        "source": args.source,
        "data_type": args.data_type,
        "data_format": "jsonl" if args.json else "csv",
        "batch_size": args.batch_size,
        "requested_paths": requested_paths,
        "range": {
            "step_min": args.step_min,
            "step_max": args.step_max,
            "event_time_min": args.event_time_min,
            "event_time_max": args.event_time_max,
        },
        "network": args.network,
        "site": args.site,
    }


def validate_resume_compatibility(args: argparse.Namespace, output_dir: str, requested_paths: List[str]) -> None:
    query_meta_path = os.path.join(output_dir, "files", "query-meta.json")
    if not os.path.exists(query_meta_path):
        return
    query_meta = load_json(query_meta_path)
    previous = query_meta.get("request_fingerprint")
    legacy_series_paths = os.path.exists(os.path.join(output_dir, "files", "series-paths.jsonl"))
    legacy_batch_manifest = os.path.exists(os.path.join(output_dir, "files", "batch-manifest.json"))
    if not previous and (legacy_series_paths or legacy_batch_manifest):
        print_error(
            "existing output directory was created before resumable checkpoints were supported",
            hint="choose a new --output directory, or archive/remove the old output before rerunning",
        )
    current = request_fingerprint(args, requested_paths)
    if previous and previous != current:
        print_error(
            "existing output directory was created with different request parameters",
            hint="reuse the exact same command to resume, or choose a new --output directory",
        )


def path_set(values: Iterable[str]) -> Set[str]:
    return {str(value) for value in values}


def batch_is_complete(manifest_entry: dict, requested_paths: List[str]) -> bool:
    if manifest_entry.get("status") != "complete":
        return False
    return path_set(manifest_entry.get("requested_paths") or []) == path_set(requested_paths)


def load_existing_batch_manifest(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    payload = load_json(path)
    if not isinstance(payload, list):
        print_error(f"existing batch manifest is not a JSON list: {path}", exit_code=1)
    return payload


def find_manifest_entry(batch_manifest: List[dict], batch_index: int) -> Optional[dict]:
    for entry in batch_manifest:
        if entry.get("batch_index") == batch_index:
            return entry
    return None


def remove_manifest_entry(batch_manifest: List[dict], batch_index: int) -> List[dict]:
    return [entry for entry in batch_manifest if entry.get("batch_index") != batch_index]


def prune_merged_paths(merged_paths: List[dict], batch_index: int) -> List[dict]:
    return [entry for entry in merged_paths if entry.get("batch_index") != batch_index]


def renumber_merged_paths(args: argparse.Namespace, output_dir: str, merged_paths: List[dict]) -> Tuple[List[dict], Set[int]]:
    extension = data_file_ext(args.json)
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    invalid_batch_indexes: Set[int] = set()
    for entry in merged_paths:
        current_data_file = entry.get("data_file")
        if current_data_file and os.path.exists(current_data_file):
            continue
        batch_index = entry.get("batch_index")
        if isinstance(batch_index, int):
            invalid_batch_indexes.add(batch_index)
            continue
        print_error(f"missing data file while resuming batch merge: {current_data_file}", exit_code=1)
    if invalid_batch_indexes:
        for batch_index in sorted(invalid_batch_indexes):
            sys.stderr.write(
                f"resume checkpoint for batch {batch_index} references missing data; "
                "the batch will be re-run\n"
            )
        merged_paths = [
            entry for entry in merged_paths if entry.get("batch_index") not in invalid_batch_indexes
        ]

    result: List[dict] = []
    for next_path_id, entry in enumerate(merged_paths, start=1):
        current_data_file = entry.get("data_file")
        target_data_file = os.path.join(data_dir, f"{args.data_type}.{next_path_id:06d}.{extension}")
        if current_data_file != target_data_file:
            if os.path.exists(target_data_file):
                remove_path(target_data_file)
            os.replace(current_data_file, target_data_file)
        next_entry = dict(entry)
        next_entry["path_id"] = next_path_id
        next_entry["data_file"] = target_data_file
        next_entry["data_format"] = "jsonl" if args.json else "csv"
        result.append(next_entry)
    return result, invalid_batch_indexes


def query_meta_payload(
    args: argparse.Namespace,
    output_dir: str,
    requested_paths: List[str],
    merged_paths: List[dict],
    batch_manifest: List[dict],
    auth_source: Optional[str],
    token_refreshed: bool,
    network: Optional[str],
    site: Optional[str],
    message: str,
) -> dict:
    files_dir = os.path.join(output_dir, "files")
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": output_dir,
        "summary_path": os.path.join(output_dir, "summary.json"),
        "job_id": args.job_id,
        "source": args.source,
        "data_type": args.data_type,
        "data_format": "jsonl" if args.json else "csv",
        "network": network or None,
        "site": site or None,
        "requested_path_count": len(requested_paths),
        "requested_paths_file": os.path.join(files_dir, "requested-paths.txt"),
        "returned_path_count": len(merged_paths),
        "batch_count": len(batch_manifest),
        "batch_size": args.batch_size,
        "batch_manifest_file": os.path.join(files_dir, "batch-manifest.json"),
        "request_interval_seconds": args.request_interval_seconds,
        "retry_count": args.retry_count,
        "retry_base_delay_seconds": args.retry_base_delay_seconds,
        "retry_max_delay_seconds": args.retry_max_delay_seconds,
        "request_fingerprint": request_fingerprint(args, requested_paths),
        "range": {
            "step_min": args.step_min,
            "step_max": args.step_max,
            "event_time_min": args.event_time_min,
            "event_time_max": args.event_time_max,
        },
        "auth_source": auth_source or None,
        "token_refreshed": token_refreshed,
        "message": message,
        "series_paths_file": os.path.join(files_dir, "series-paths.jsonl"),
        "can_requery_for_fresher_or_finer_data": True,
    }


def checkpoint_ok(batch_manifest: List[dict]) -> bool:
    return not any(entry.get("status") == "failed" for entry in batch_manifest)


def summary_payload(
    args: argparse.Namespace,
    output_dir: str,
    merged_paths: List[dict],
    batch_manifest: List[dict],
    auth_source: Optional[str],
    token_refreshed: bool,
    message: str,
) -> dict:
    files_dir = os.path.join(output_dir, "files")
    return {
        "ok": checkpoint_ok(batch_manifest),
        "job_id": args.job_id,
        "source": args.source,
        "data_type": args.data_type,
        "path_count": len(merged_paths),
        "batch_count": len(batch_manifest),
        "auth_source": auth_source or None,
        "token_refreshed": token_refreshed,
        "message": message,
        "artifacts": {
            "output_dir": output_dir,
            "summary_path": os.path.join(output_dir, "summary.json"),
            "files_dir": files_dir,
            "data_dir": os.path.join(output_dir, "data"),
            "data_format": "jsonl" if args.json else "csv",
            "query_meta_path": os.path.join(files_dir, "query-meta.json"),
            "series_paths_path": os.path.join(files_dir, "series-paths.jsonl"),
        },
    }


def write_checkpoint(
    args: argparse.Namespace,
    output_dir: str,
    requested_paths: List[str],
    merged_paths: List[dict],
    batch_manifest: List[dict],
    auth_source: Optional[str],
    token_refreshed: bool,
    network: Optional[str],
    site: Optional[str],
    message: str,
) -> dict:
    files_dir = os.path.join(output_dir, "files")
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(files_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    write_jsonl(os.path.join(files_dir, "series-paths.jsonl"), merged_paths)
    write_text_lines(os.path.join(files_dir, "requested-paths.txt"), requested_paths)
    write_json(os.path.join(files_dir, "batch-manifest.json"), batch_manifest)
    write_json(
        os.path.join(files_dir, "query-meta.json"),
        query_meta_payload(
            args,
            output_dir,
            requested_paths,
            merged_paths,
            batch_manifest,
            auth_source,
            token_refreshed,
            network,
            site,
            message,
        ),
    )
    payload = summary_payload(
        args,
        output_dir,
        merged_paths,
        batch_manifest,
        auth_source,
        token_refreshed,
        message,
    )
    write_json(os.path.join(output_dir, "summary.json"), payload)
    return payload


def build_query_command(args: argparse.Namespace, batch_paths: List[str], batch_output: str) -> List[str]:
    command = build_base_command(args) + [
        "job",
        args.source,
        "query",
        "--job-id",
        str(args.job_id),
        "--data-type",
        args.data_type,
        "--output",
        batch_output,
    ]
    for path in batch_paths:
        command.extend(["--paths", path])
    if args.json:
        command.append("--json")
    if args.step_min is not None:
        command.extend(["--step-min", str(args.step_min)])
    if args.step_max is not None:
        command.extend(["--step-max", str(args.step_max)])
    if args.event_time_min is not None:
        command.extend(["--event-time-min", str(args.event_time_min)])
    if args.event_time_max is not None:
        command.extend(["--event-time-max", str(args.event_time_max)])
    return command


def merge_batches(args: argparse.Namespace, output_dir: str, requested_paths: List[str]) -> dict:
    files_dir = os.path.join(output_dir, "files")
    data_dir = os.path.join(output_dir, "data")
    batches_dir = os.path.join(files_dir, "batches")
    os.makedirs(files_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(batches_dir, exist_ok=True)

    final_batch_manifest_path = os.path.join(files_dir, "batch-manifest.json")
    final_series_paths_path = os.path.join(files_dir, "series-paths.jsonl")
    validate_resume_compatibility(args, output_dir, requested_paths)
    previous_query_meta = load_json(os.path.join(files_dir, "query-meta.json")) if os.path.exists(os.path.join(files_dir, "query-meta.json")) else {}
    batch_manifest = load_existing_batch_manifest(final_batch_manifest_path)
    merged_paths = load_jsonl(final_series_paths_path) if os.path.exists(final_series_paths_path) else []
    if merged_paths:
        merged_paths, invalid_batch_indexes = renumber_merged_paths(args, output_dir, merged_paths)
        if invalid_batch_indexes:
            batch_manifest = [
                entry for entry in batch_manifest if entry.get("batch_index") not in invalid_batch_indexes
            ]
            write_checkpoint(
                args,
                output_dir,
                requested_paths,
                merged_paths,
                batch_manifest,
                previous_query_meta.get("auth_source"),
                bool(previous_query_meta.get("token_refreshed")),
                previous_query_meta.get("network") or args.network,
                previous_query_meta.get("site") or args.site,
                "pruned incomplete resume checkpoint batches before continuing",
            )

    auth_source: Optional[str] = previous_query_meta.get("auth_source")
    token_refreshed = bool(previous_query_meta.get("token_refreshed"))
    network: Optional[str] = previous_query_meta.get("network") or args.network
    site: Optional[str] = previous_query_meta.get("site") or args.site
    extension = data_file_ext(args.json)
    total_batches = (len(requested_paths) + args.batch_size - 1) // args.batch_size
    completed_before = sum(1 for entry in batch_manifest if entry.get("status") == "complete")
    if completed_before:
        sys.stderr.write(f"resuming from {completed_before} completed batch checkpoint(s)\n")

    for batch_index, batch_paths in enumerate(chunked(requested_paths, args.batch_size), start=1):
        existing_entry = find_manifest_entry(batch_manifest, batch_index)
        if existing_entry and batch_is_complete(existing_entry, batch_paths):
            sys.stderr.write(f"skip completed batch {batch_index}/{total_batches}\n")
            continue

        temp_root = tempfile.mkdtemp(prefix=f"batch-{batch_index:03d}-", dir=batches_dir)
        batch_output = os.path.join(temp_root, "output")
        try:
            summary = run_query_with_retries(args, build_query_command(args, batch_paths, batch_output))
            artifacts = summary.get("artifacts") or {}
            query_meta_path = artifacts.get("query_meta_path")
            series_paths_path = artifacts.get("series_paths_path")
            if not artifacts.get("summary_path") or not query_meta_path or not series_paths_path:
                print_error("batch query summary is missing required artifact paths", exit_code=1)

            query_meta = load_json(query_meta_path)
            if not auth_source and summary.get("auth_source"):
                auth_source = summary["auth_source"]
            token_refreshed = token_refreshed or bool(summary.get("token_refreshed"))
            if not network and query_meta.get("network"):
                network = query_meta["network"]
            if not site and query_meta.get("site"):
                site = query_meta["site"]

            batch_manifest = remove_manifest_entry(batch_manifest, batch_index)
            merged_paths = prune_merged_paths(merged_paths, batch_index)
            merged_paths, invalid_batch_indexes = renumber_merged_paths(args, output_dir, merged_paths)
            if invalid_batch_indexes:
                batch_manifest = [
                    entry for entry in batch_manifest if entry.get("batch_index") not in invalid_batch_indexes
                ]

            batch_entries = load_jsonl(series_paths_path)
            remapped_entries: List[dict] = []
            for entry in batch_entries:
                next_path_id = len(merged_paths) + 1
                target_name = f"{args.data_type}.{next_path_id:06d}.{extension}"
                final_data_file = os.path.join(data_dir, target_name)
                shutil.copy2(entry["data_file"], final_data_file)
                remapped_entry = dict(entry)
                remapped_entry["path_id"] = next_path_id
                remapped_entry["batch_index"] = batch_index
                remapped_entry["data_file"] = final_data_file
                remapped_entry["data_format"] = "jsonl" if args.json else "csv"
                remapped_entries.append(remapped_entry)
                merged_paths.append(remapped_entry)

            batch_manifest.append(
                {
                    "batch_index": batch_index,
                    "status": "complete",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "requested_path_count": len(batch_paths),
                    "returned_path_count": len(remapped_entries),
                    "requested_paths": batch_paths,
                    "source": args.source,
                    "job_id": args.job_id,
                    "data_type": args.data_type,
                }
            )
            batch_manifest.sort(key=lambda entry: int(entry.get("batch_index") or 0))
            message = f"checkpointed {len(batch_manifest)}/{total_batches} batched queries into the output directory"
            write_checkpoint(
                args,
                output_dir,
                requested_paths,
                merged_paths,
                batch_manifest,
                auth_source,
                token_refreshed,
                network,
                site,
                message,
            )
            sys.stderr.write(f"{message}\n")
        except CommandError as exc:
            batch_manifest = remove_manifest_entry(batch_manifest, batch_index)
            batch_manifest.append(
                {
                    "batch_index": batch_index,
                    "status": "failed",
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                    "requested_path_count": len(batch_paths),
                    "requested_paths": batch_paths,
                    "source": args.source,
                    "job_id": args.job_id,
                    "data_type": args.data_type,
                    "error": command_error_payload(exc),
                    "resume_hint": "rerun the same command; completed batches will be skipped",
                }
            )
            batch_manifest.sort(key=lambda entry: int(entry.get("batch_index") or 0))
            write_checkpoint(
                args,
                output_dir,
                requested_paths,
                merged_paths,
                batch_manifest,
                auth_source,
                token_refreshed,
                network,
                site,
                f"batch {batch_index}/{total_batches} failed; rerun the same command to resume",
            )
            raise SystemExit(exc.returncode)
        finally:
            remove_path(temp_root)

        if batch_index < total_batches and args.request_interval_seconds > 0:
            time.sleep(args.request_interval_seconds)

    batch_manifest = [entry for entry in batch_manifest if entry.get("status") == "complete"]
    message = f"merged {len(batch_manifest)} batched queries into one output directory"
    return write_checkpoint(
        args,
        output_dir,
        requested_paths,
        merged_paths,
        batch_manifest,
        auth_source,
        token_refreshed,
        network,
        site,
        message,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.job_id <= 0:
        print_error("--job-id must be positive")
    if args.batch_size <= 0 or args.batch_size > MAX_BATCH_SIZE:
        print_error(
            f"--batch-size must be between 1 and {MAX_BATCH_SIZE}",
            hint=f"use {MAX_BATCH_SIZE} or any smaller positive value",
        )
    if args.request_interval_seconds < 0:
        print_error("--request-interval-seconds must be non-negative")
    if args.retry_count < 0:
        print_error("--retry-count must be non-negative")
    if args.retry_base_delay_seconds < 0:
        print_error("--retry-base-delay-seconds must be non-negative")
    if args.retry_max_delay_seconds < 0:
        print_error("--retry-max-delay-seconds must be non-negative")

    output_dir = default_output_dir(args.source, args.data_type, args.job_id)
    if args.output:
        output_dir = canonicalize_output_dir(args.output)

    requested_paths = discover_paths(args)
    requested_paths = apply_path_filters(requested_paths, args.path_contains, args.path_exclude)
    requested_paths = dedupe_preserve_order(requested_paths)
    if not requested_paths:
        print_error(
            "no paths remain after discovery and filtering",
            hint="run get-meta first, or relax the path filters",
        )

    summary = merge_batches(args, output_dir, requested_paths)
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
