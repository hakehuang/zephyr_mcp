#!/usr/bin/env python3
"""Extract review-oriented C control-flow facts with Tree-sitter.

The report is intentionally structural rather than a complete control-flow proof. It
lists functions, switch cases, calls, state-changing assignments, and returns in
source order so a reviewer can check lifecycle and rollback paths efficiently.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    from tree_sitter import Language, Parser
    import tree_sitter_c
except ImportError as exc:
    print(
        "Missing Tree-sitter dependencies. Install them with: "
        "python -m pip install -r tools/requirements-tree-sitter.txt",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc

C_EXTENSIONS = {".c", ".h"}
ASSIGNMENT_TYPES = {
    "assignment_expression",
    "update_expression",
}
RESOURCE_CALLS = {
    "clock_control_on": ("clock", "acquire"),
    "clock_control_off": ("clock", "release"),
    "pm_policy_device_power_lock_get": ("policy_lock", "acquire"),
    "pm_policy_device_power_lock_put": ("policy_lock", "release"),
    "pinctrl_apply_state": ("pinctrl", "transition"),
    "reset_line_assert": ("reset", "transition"),
    "reset_line_deassert": ("reset", "transition"),
    "pm_device_runtime_get": ("runtime_pm", "acquire"),
    "pm_device_runtime_put": ("runtime_pm", "release"),
}


def node_text(source: bytes, node: Any | None) -> str:
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def walk(node: Any) -> Iterable[Any]:
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def function_name(source: bytes, declarator: Any) -> str:
    current = declarator
    while current is not None:
        if current.type == "identifier":
            return node_text(source, current)
        child = current.child_by_field_name("declarator")
        if child is not None:
            current = child
            continue
        identifiers = [n for n in walk(current) if n.type == "identifier"]
        return node_text(source, identifiers[0]) if identifiers else "<anonymous>"
    return "<anonymous>"


def call_name(source: bytes, call: Any) -> str:
    return node_text(source, call.child_by_field_name("function"))


def assignment_operator(node: Any) -> str:
    for child in node.children:
        if child.type in {"=", "|=", "&=", "^=", "+=", "-=", "++", "--"}:
            return child.type
    return ""


def event_for_assignment(lhs: str, operator: str, expression: str) -> dict[str, str] | None:
    upper = expression.upper()
    enable_like = any(token in upper for token in ("_EN_MASK", "ENABLE_MASK", "OPA_EN"))
    if not enable_like:
        return None
    if operator == "|=":
        return {"resource": lhs, "operation": "enable"}
    if operator == "&=" and "~" in expression:
        return {"resource": lhs, "operation": "disable"}
    return None


def error_locations(root: Any, limit: int = 20) -> list[dict[str, Any]]:
    errors = []
    for node in walk(root):
        if node.type in {"ERROR", "MISSING"} or node.is_missing:
            errors.append(
                {
                    "type": node.type,
                    "line": node.start_point.row + 1,
                    "column": node.start_point.column + 1,
                }
            )
            if len(errors) >= limit:
                break
    return errors


def analyze_region(source: bytes, region: Any) -> dict[str, Any]:
    calls: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    returns: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    for node in walk(region):
        line = node.start_point.row + 1
        if node.type == "call_expression":
            name = call_name(source, node)
            item = {"name": name, "line": line}
            calls.append(item)
            if name in RESOURCE_CALLS:
                resource, operation = RESOURCE_CALLS[name]
                events.append(
                    {
                        "kind": "call",
                        "name": name,
                        "resource": resource,
                        "operation": operation,
                        "line": line,
                    }
                )
        elif node.type in ASSIGNMENT_TYPES:
            lhs_node = node.child_by_field_name("left") or node.child_by_field_name("argument")
            lhs = node_text(source, lhs_node)
            operator = assignment_operator(node)
            expression = node_text(source, node).replace("\n", " ").strip()
            assignments.append(
                {"lhs": lhs, "operator": operator, "expression": expression, "line": line}
            )
            resource_event = event_for_assignment(lhs, operator, expression)
            if resource_event:
                events.append(
                    {
                        "kind": "assignment",
                        "name": expression,
                        "line": line,
                        **resource_event,
                    }
                )
        elif node.type == "return_statement":
            expression = node_text(source, node)[len("return") :].strip().rstrip(";")
            returns.append({"expression": expression, "line": line})
            events.append(
                {
                    "kind": "return",
                    "name": expression or "void",
                    "resource": "control_flow",
                    "operation": "return",
                    "line": line,
                }
            )

    calls.sort(key=lambda item: item["line"])
    assignments.sort(key=lambda item: item["line"])
    returns.sort(key=lambda item: item["line"])
    # Calls or mutations on a return-expression line happen before control exits.
    events.sort(key=lambda item: (item["line"], item["kind"] == "return"))
    return {
        "calls": calls,
        "assignments": assignments,
        "returns": returns,
        "resource_events": events,
    }


def direct_switch_cases(source: bytes, body: Any) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for node in walk(body):
        if node.type != "switch_statement":
            continue
        switch_body = node.child_by_field_name("body")
        if switch_body is None:
            continue
        for case in switch_body.named_children:
            if case.type != "case_statement":
                continue
            label_node = case.named_children[0] if case.named_children else None
            label = node_text(source, label_node) if label_node else "default"
            if case.children and case.children[0].type == "default":
                label = "default"
            cases.append(
                {
                    "label": label,
                    "line_start": case.start_point.row + 1,
                    "line_end": case.end_point.row + 1,
                    **analyze_region(source, case),
                }
            )
        # Nested switches are analyzed by the walk loop too.
    return cases


def analyze_file(path: Path, parser: Parser, function_filter: re.Pattern[str] | None) -> dict[str, Any]:
    source = path.read_bytes()
    tree = parser.parse(source)
    root = tree.root_node
    functions: list[dict[str, Any]] = []

    for node in walk(root):
        if node.type != "function_definition":
            continue
        declarator = node.child_by_field_name("declarator")
        body = node.child_by_field_name("body")
        if declarator is None or body is None:
            continue
        name = function_name(source, declarator)
        if function_filter and not function_filter.search(name):
            continue
        functions.append(
            {
                "name": name,
                "line_start": node.start_point.row + 1,
                "line_end": node.end_point.row + 1,
                **analyze_region(source, body),
                "switch_cases": direct_switch_cases(source, body),
            }
        )

    return {
        "file": str(path),
        "parse_has_errors": root.has_error,
        "parse_diagnostics": error_locations(root),
        "functions": functions,
    }


def collect_paths(raw_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in raw_paths:
        path = Path(raw)
        if path.is_file() and path.suffix.lower() in C_EXTENSIONS:
            files.append(path)
        elif path.is_dir():
            files.extend(
                p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in C_EXTENSIONS
            )
        else:
            print(f"warning: skipping missing or unsupported path: {path}", file=sys.stderr)
    return sorted(set(files))


def changed_paths(repo: Path, diff_ref: str) -> list[Path]:
    command = ["git", "-C", str(repo), "diff", "--name-only", "--diff-filter=ACMR", diff_ref]
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    paths = []
    for relative in result.stdout.splitlines():
        candidate = repo / relative
        if candidate.is_file() and candidate.suffix.lower() in C_EXTENSIONS:
            paths.append(candidate)
    return sorted(set(paths))


def format_events(events: list[dict[str, Any]]) -> str:
    if not events:
        return "none"
    return " -> ".join(
        f"L{event['line']} {event['name']} [{event['operation']}:{event['resource']}]"
        for event in events
    )


def print_text(report: dict[str, Any]) -> None:
    print("Tree-sitter C logic report")
    print("Note: structural event order is review guidance, not a path-sensitive CFG proof.\n")
    for file_report in report["files"]:
        status = "with parse diagnostics" if file_report["parse_has_errors"] else "clean parse"
        print(f"FILE {file_report['file']} ({status})")
        if file_report["parse_diagnostics"]:
            locations = ", ".join(
                f"{item['type']}@{item['line']}:{item['column']}"
                for item in file_report["parse_diagnostics"]
            )
            print(f"  diagnostics: {locations}")
        for function in file_report["functions"]:
            print(
                f"  FUNCTION {function['name']} "
                f"L{function['line_start']}-L{function['line_end']}"
            )
            print(f"    events: {format_events(function['resource_events'])}")
            for case in function["switch_cases"]:
                print(
                    f"    CASE {case['label']} L{case['line_start']}-L{case['line_end']}: "
                    f"{format_events(case['resource_events'])}"
                )
        print()
    print(
        f"Summary: {report['summary']['files']} file(s), "
        f"{report['summary']['functions']} function(s), "
        f"{report['summary']['files_with_parse_errors']} file(s) with parse diagnostics."
    )


def main() -> int:
    parser_arg = argparse.ArgumentParser(
        description="Extract review-oriented C logic and resource-event sequences with Tree-sitter."
    )
    parser_arg.add_argument("paths", nargs="*", help="C files or directories to analyze")
    parser_arg.add_argument("--repo", type=Path, help="Git repository for changed-file mode")
    parser_arg.add_argument(
        "--diff-ref",
        help="Git diff range/ref used with --repo, for example origin/main...HEAD",
    )
    parser_arg.add_argument("--function", help="Regular expression selecting function names")
    parser_arg.add_argument("--json", action="store_true", help="Emit JSON")
    parser_arg.add_argument("--output", type=Path, help="Write the report to this file")
    args = parser_arg.parse_args()

    if args.repo or args.diff_ref:
        if not (args.repo and args.diff_ref):
            parser_arg.error("--repo and --diff-ref must be used together")
        paths = changed_paths(args.repo.resolve(), args.diff_ref)
        paths.extend(collect_paths(args.paths))
        paths = sorted(set(paths))
    else:
        paths = collect_paths(args.paths)

    if not paths:
        parser_arg.error("no C source/header files selected")

    function_filter = re.compile(args.function) if args.function else None
    language = Language(tree_sitter_c.language())
    ts_parser = Parser(language)
    file_reports = [analyze_file(path, ts_parser, function_filter) for path in paths]
    report = {
        "schema_version": 1,
        "analysis_kind": "tree-sitter-c-structural-logic",
        "files": file_reports,
        "summary": {
            "files": len(file_reports),
            "functions": sum(len(item["functions"]) for item in file_reports),
            "files_with_parse_errors": sum(item["parse_has_errors"] for item in file_reports),
        },
    }

    if args.json:
        rendered = json.dumps(report, indent=2)
    else:
        from io import StringIO
        original = sys.stdout
        buffer = StringIO()
        try:
            sys.stdout = buffer
            print_text(report)
        finally:
            sys.stdout = original
        rendered = buffer.getvalue().rstrip()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
