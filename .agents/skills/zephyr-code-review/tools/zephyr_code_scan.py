#!/usr/bin/env python3
"""Scan a source tree for Zephyr review-relevant keywords and paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TEXT_EXTS = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx",
    ".py", ".rst", ".md", ".txt", ".yml", ".yaml", ".conf",
    ".overlay", ".dts", ".dtsi", ".kconfig", ".cmake",
}

SKIP_DIRS = {
    ".git", "build", "out", "dist", ".west", ".venv", "venv",
    "node_modules", "__pycache__",
}


def load_rules(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTS and path.suffix != "":
            continue
        yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def path_tags(rel_path: str, rules: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for rule in rules.get("path_rules", []):
        for pattern in rule.get("patterns", []):
            if pattern in rel_path:
                tags.extend(rule.get("tags", []))
                break
    return sorted(set(tags))


def scan_tree(root: Path, rules: dict[str, Any], max_hits: int) -> dict[str, Any]:
    keyword_hits = []
    srs_counts: dict[str, int] = {}
    tagged_files = []

    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        tags = path_tags(rel, rules)
        if tags:
            tagged_files.append({"path": rel, "tags": tags})

        text = read_text(path).lower()
        for item in rules.get("srs_items", []):
            matched = [kw for kw in item.get("keywords", []) if kw.lower() in text]
            if not matched:
                continue
            srs_counts[item["id"]] = srs_counts.get(item["id"], 0) + 1
            keyword_hits.append({
                "path": rel,
                "srs_id": item["id"],
                "title": item.get("title", ""),
                "matched_keywords": matched[:8],
                "review_focus": item.get("review_focus", []),
            })
            if len(keyword_hits) >= max_hits:
                return {
                    "tagged_files": tagged_files,
                    "keyword_hits": keyword_hits,
                    "srs_counts": srs_counts,
                    "truncated": True,
                }

    return {
        "tagged_files": tagged_files,
        "keyword_hits": keyword_hits,
        "srs_counts": srs_counts,
        "truncated": False,
    }


def print_markdown(report: dict[str, Any]) -> None:
    print("## Zephyr Code Scan")
    print()
    print("### Tagged files")
    if report["tagged_files"]:
        for item in report["tagged_files"][:80]:
            print(f"- `{item['path']}` tags: {', '.join(item['tags'])}")
        if len(report["tagged_files"]) > 80:
            print(f"- ... {len(report['tagged_files']) - 80} more tagged files")
    else:
        print("- No path-based Zephyr review tags detected.")
    print()
    print("### SRS-oriented keyword hits")
    if report["keyword_hits"]:
        for item in report["keyword_hits"][:80]:
            kws = ", ".join(item["matched_keywords"])
            print(f"- `{item['path']}` -> `{item['srs_id']}` {item['title']} "
                  f"(keywords: {kws})")
        if len(report["keyword_hits"]) > 80:
            print(f"- ... {len(report['keyword_hits']) - 80} more hits")
    else:
        print("- No SRS keyword hits detected.")
    print()
    print("### SRS hit counts")
    if report["srs_counts"]:
        for srs_id, count in sorted(report["srs_counts"].items()):
            print(f"- `{srs_id}`: {count}")
    else:
        print("- No SRS counts available.")
    if report.get("truncated"):
        print()
        print("### Note")
        print("- Output was truncated after reaching the requested hit limit.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan a source tree using Zephyr review rules."
    )
    parser.add_argument("root", type=Path, help="Root folder to scan")
    parser.add_argument("--rules", type=Path,
                        default=Path(__file__).resolve().parents[1] /
                        "assets" / "zephyr_review_rules.json",
                        help="Path to Zephyr review rules JSON")
    parser.add_argument("--max-hits", type=int, default=200,
                        help="Maximum keyword hits to collect")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON instead of markdown")
    args = parser.parse_args()

    rules = load_rules(args.rules)
    report = scan_tree(args.root, rules, args.max_hits)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
