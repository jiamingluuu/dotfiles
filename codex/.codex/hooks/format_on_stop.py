#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def respond(obj: dict) -> None:
    print(json.dumps(obj))
    sys.exit(0)


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout, proc.stderr


def git_root() -> Path | None:
    code, out, _ = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    if code != 0:
        return None
    return Path(out.strip())


def changed_files(root: Path) -> list[Path]:
    # Includes unstaged and staged changes.
    cmds = [
        ["git", "diff", "--name-only", "--diff-filter=ACMR"],
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
    ]

    seen: set[str] = set()
    result: list[Path] = []

    for cmd in cmds:
        code, out, _ = run(cmd, root)
        if code != 0:
            continue

        for line in out.splitlines():
            rel = line.strip()
            if not rel or rel in seen:
                continue
            seen.add(rel)

            path = root / rel
            if path.exists() and path.is_file():
                result.append(path)

    return result


def group_by_formatter(files: list[Path]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {
        "clang-format": [],
        "ruff": [],
        "black": [],
        "rustfmt": [],
        "prettier": [],
    }

    for path in files:
        suffix = path.suffix.lower()

        if suffix in {".cc", ".cpp", ".cxx", ".c", ".h", ".hh", ".hpp", ".hxx"}:
            groups["clang-format"].append(str(path))
        elif suffix == ".py":
            # Prefer ruff format over black if available.
            if shutil.which("ruff"):
                groups["ruff"].append(str(path))
            else:
                groups["black"].append(str(path))
        elif suffix == ".rs":
            groups["rustfmt"].append(str(path))
        elif suffix in {
            ".js", ".jsx", ".ts", ".tsx",
            ".json", ".jsonc",
            ".css", ".scss",
            ".html",
            ".md", ".mdx",
            ".yaml", ".yml",
        }:
            groups["prettier"].append(str(path))

    return groups


def main() -> None:
    payload = json.load(sys.stdin)

    # Avoid infinite continuation loops.
    if payload.get("stop_hook_active"):
        respond({"continue": True})

    root = git_root()
    if root is None:
        respond({"continue": True})

    files = changed_files(root)
    if not files:
        respond({"continue": True})

    groups = group_by_formatter(files)
    ran: list[str] = []
    failures: list[str] = []

    if groups["clang-format"] and shutil.which("clang-format"):
        cmd = ["clang-format", "-i", *groups["clang-format"]]
        code, _, err = run(cmd, root)
        if code == 0:
            ran.append(f"clang-format on {len(groups['clang-format'])} file(s)")
        else:
            failures.append(f"clang-format failed:\n{err}")

    if groups["ruff"] and shutil.which("ruff"):
        cmd = ["ruff", "format", *groups["ruff"]]
        code, _, err = run(cmd, root)
        if code == 0:
            ran.append(f"ruff format on {len(groups['ruff'])} file(s)")
        else:
            failures.append(f"ruff format failed:\n{err}")

    if groups["black"] and shutil.which("black"):
        cmd = ["black", *groups["black"]]
        code, _, err = run(cmd, root)
        if code == 0:
            ran.append(f"black on {len(groups['black'])} file(s)")
        else:
            failures.append(f"black failed:\n{err}")

    if groups["rustfmt"] and shutil.which("rustfmt"):
        for file in groups["rustfmt"]:
            code, _, err = run(["rustfmt", file], root)
            if code == 0:
                ran.append(f"rustfmt on {file}")
            else:
                failures.append(f"rustfmt failed on {file}:\n{err}")

    if groups["prettier"] and shutil.which("prettier"):
        cmd = ["prettier", "--write", *groups["prettier"]]
        code, _, err = run(cmd, root)
        if code == 0:
            ran.append(f"prettier on {len(groups['prettier'])} file(s)")
        else:
            failures.append(f"prettier failed:\n{err}")

    if failures:
        reason = (
            "The format-on-stop hook attempted to format modified files, but "
            "some formatter commands failed. Inspect the formatter errors, fix "
            "the issue if appropriate, and then summarize the result.\n\n"
            + "\n\n".join(failures[:3])
        )
        respond({
            "decision": "block",
            "reason": reason,
        })

    if ran:
        reason = (
            "The format-on-stop hook ran these formatter commands:\n"
            + "\n".join(f"- {x}" for x in ran)
            + "\n\nInspect the resulting git diff, make sure formatting did not "
              "introduce unintended changes, and then provide the final summary."
        )
        respond({
            "decision": "block",
            "reason": reason,
        })

    respond({"continue": True})


if __name__ == "__main__":
    main()
