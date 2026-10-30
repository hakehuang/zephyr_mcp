#!/usr/bin/env python3
"""Lightweight cyclomatic complexity estimator for C/C++ source files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


C_EXTS = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
SKIP_DIRS = {".git", "build", "out", "dist", ".west", ".venv", "venv",
             "node_modules", "__pycache__"}
DECISION_TOKENS = [
    r"\bif\b",
    r"\bfor\b",
    r"\bwhile\b",
    r"\bcase\b",
    r"\bcatch\b",
    r"\?",
    r"&&",
    r"\|\|",
]
FUNC_START_RE = re.compile(
    r"^\s*[A-Za-z_][\w\s\*]*\b([A-Za-z_]\w*)\s*\([^;]*\)\s*\{\s*$"
)
COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.S | re.M)
STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')


def strip_comments_and_strings(text: str) -> str:
    text = COMMENT_RE.sub("", text)
    text = STRING_RE.sub("''", text)
    return text


def iter_sources(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in C_EXTS:
            yield path


def compute_function_complexities(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = strip_comments_and_strings(raw)
    lines = text.splitlines()

    results = []
    current = None
    brace_depth = 0

    for lineno, line in enumerate(lines, start=1):
        if current is None:
            m = FUNC_START_RE.match(line)
            if m:
                current = {
                    "name": m.group(1),
                    "line": lineno,
                    "complexity": 1,
                    "body": [line],
                }
                brace_depth = line.count("{") - line.count("}")
            continue

        current["body"].append(line)
        for token in DECISION_TOKENS:
            current["complexity"] += len(re.findall(token, line))
        brace_depth += line.count("{") - line.count("}")
        if brace_depth <= 0:
            body = "\n".join(current.pop("body"))
            current["decision_points"] = max(current["complexity"] - 1, 0)
            current["body_lines"] = len(body.splitlines())
            results.append(current)
            current = None
            brace_depth = 0

    return results


def analyze(target: Path, threshold: int) -> dict:
    files = []
    flagged = []
    total_funcs = 0

    for path in iter_sources(target):
        funcs = compute_function_complexities(path)
        if not funcs:
            continue
        rel = path.as_posix() if path == target else path.relative_to(target if target.is_dir() else path.parent).as_posix()
        files.append({"path": rel, "functions": funcs})
        total_funcs += len(funcs)
        for func in funcs:
            if func["complexity"] >= threshold:
                flagged.append({
                    "path": rel,
                    "name": func["name"],
                    "line": func["line"],
                    "complexity": func["complexity"],
                })

    flagged.sort(key=lambda x: (-x["complexity"], x["path"], x["line"]))
    return {
        "target": str(target),
        "threshold": threshold,
        "file_count": len(files),
        "function_count": total_funcs,
        "flagged": flagged,
        "files": files,
    }


def print_markdown(report: dict) -> None:
    print("## Doris C Cyclomatic Complexity")
    print()
    print(f"- Target: `{report['target']}`")
    print(f"- Files with parsed functions: {report['file_count']}")
    print(f"- Parsed functions: {report['function_count']}")
    print(f"- Threshold: {report['threshold']}")
    print()
    print("### Flagged functions")
    if report["flagged"]:
        for item in report["flagged"][:100]:
            print(f"- `{item['path']}`:`{item['name']}` line {item['line']} -> "
                  f"complexity {item['complexity']}")
        if len(report["flagged"]) > 100:
            print(f"- ... {len(report['flagged']) - 100} more flagged functions")
    else:
        print("- No functions exceeded the threshold.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estimate cyclomatic complexity for C/C++ code."
    )
    parser.add_argument("target", type=Path,
                        help="File or directory to analyze")
    parser.add_argument("--threshold", type=int, default=10,
                        help="Flag functions at or above this complexity")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON instead of markdown")
    args = parser.parse_args()

    report = analyze(args.target, args.threshold)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
