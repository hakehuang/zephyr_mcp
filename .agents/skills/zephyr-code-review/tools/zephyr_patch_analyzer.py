#!/usr/bin/env python3
"""Analyze a git diff or patch for Zephyr review hints."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


TEXT_EXTS = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx",
    ".py", ".rst", ".md", ".txt", ".yml", ".yaml", ".conf",
    ".overlay", ".dts", ".dtsi", ".kconfig", ".cmake",
}


def load_rules(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_git_diff(repo: Path, diff_ref: str | None) -> str:
    cmd = ["git", "-C", str(repo), "diff", "--no-ext-diff"]
    if diff_ref:
        cmd.append(diff_ref)
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "git diff failed")
    return res.stdout


def read_patch(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_changed_files(diff_text: str) -> dict[str, dict[str, int]]:
    files: dict[str, dict[str, int]] = {}
    current: str | None = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+?) b/(.+)$", line)
            if m:
                current = m.group(2)
                files.setdefault(current, {"added": 0, "removed": 0})
            else:
                current = None
            continue
        if current is None:
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            files[current]["added"] += 1
        elif line.startswith("-"):
            files[current]["removed"] += 1
    return files


def lower_blob(diff_text: str) -> str:
    return diff_text.lower()


def collect_path_tags(changed_files: dict[str, dict[str, int]],
                      rules: dict[str, Any]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = defaultdict(list)
    for path in changed_files:
        norm = path.replace("\\", "/")
        for rule in rules.get("path_rules", []):
            for pattern in rule.get("patterns", []):
                if pattern in norm:
                    hits[path].extend(rule.get("tags", []))
                    break
    return {k: sorted(set(v)) for k, v in hits.items()}


def collect_srs_hits(diff_text: str, rules: dict[str, Any]) -> list[dict[str, Any]]:
    blob = lower_blob(diff_text)
    hits: list[dict[str, Any]] = []
    for item in rules.get("srs_items", []):
        matched = []
        for kw in item.get("keywords", []):
            if kw.lower() in blob:
                matched.append(kw)
        if matched:
            hits.append({
                "id": item["id"],
                "title": item.get("title", ""),
                "matched_keywords": matched,
                "review_focus": item.get("review_focus", []),
                "status": item.get("status", "baseline"),
            })
    return hits


def classify_risks(changed_files: dict[str, dict[str, int]],
                   path_tags: dict[str, list[str]],
                   srs_hits: list[dict[str, Any]],
                   diff_text: str) -> list[str]:
    risks: list[str] = []
    all_tags = sorted({tag for tags in path_tags.values() for tag in tags})
    blob = lower_blob(diff_text)

    if any(tag in all_tags for tag in ["ota", "storage", "flash"]):
        risks.append("Patch touches OTA or storage paths; check external "
                     "flash constraint and partition impact.")
    if any(tag in all_tags for tag in ["timing", "concurrency", "can"]):
        risks.append("Patch touches timing-sensitive or concurrency-related "
                     "paths; review full-load responsiveness and CAN Keep "
                     "Alive behavior.")
    if any(tag in all_tags for tag in ["ble", "channel_sounding", "gatt"]):
        risks.append("Patch touches Bluetooth paths; review Zephyr BLE stack "
                     "support, MW30 GATT parity expectations, and channel "
                     "sounding behavior.")
    if any(tag in all_tags for tag in ["thread", "802154"]):
        risks.append("Patch touches Thread or 802.15.4 paths; review "
                     "OpenThread support and proprietary 802.15.4 behavior.")
    if any(tag in all_tags for tag in ["security", "credentials", "keys"]):
        risks.append("Patch touches security-related paths; review credential "
                     "protection, secure storage, and protected update flow.")

    trigger_words = {
        "k_thread": "Threading changes may affect scheduling and latency.",
        "irq": "Interrupt-related changes may affect real-time behavior.",
        "flash_area": "Flash map changes may affect OTA storage assumptions.",
        "settings": "Settings or storage changes may affect persistent "
                    "configuration and secure data handling.",
        "mbedtls": "Crypto or TLS changes may affect Matter or protected "
                    "credential handling.",
        "openthread": "Thread stack changes may affect Thread 1.4 support.",
        "bluetooth": "Bluetooth changes require BLE support and profile "
                     "regression review.",
    }
    for word, text in trigger_words.items():
        if word in blob and text not in risks:
            risks.append(text)

    if any(item.get("status") == "lower-confidence" for item in srs_hits):
        risks.append("Patch may overlap a lower-confidence Zephyr item; do "
                     "not treat non-baseline hosted gateway scope as required "
                     "without confirmation.")

    if not risks:
        risks.append("No high-risk review area was auto-detected; manual "
                     "scope confirmation is still required.")
    return risks


def summarize(changed_files: dict[str, dict[str, int]],
              path_tags: dict[str, list[str]],
              srs_hits: list[dict[str, Any]],
              risks: list[str]) -> dict[str, Any]:
    files = []
    for path, counts in sorted(changed_files.items()):
        ext = Path(path).suffix.lower()
        kind = "text" if ext in TEXT_EXTS or ext == "" else ext.lstrip(".")
        files.append({
            "path": path,
            "kind": kind,
            "added": counts["added"],
            "removed": counts["removed"],
            "tags": path_tags.get(path, []),
        })
    return {
        "files": files,
        "srs_hits": srs_hits,
        "risks": risks,
    }


def print_markdown(summary: dict[str, Any]) -> None:
    print("## Zephyr Patch Analysis")
    print()
    print("### Changed files")
    for item in summary["files"]:
        tags = ", ".join(item["tags"]) if item["tags"] else "none"
        print(f"- `{item['path']}` (+{item['added']} / -{item['removed']}) "
              f"tags: {tags}")
    print()
    print("### Candidate SRS links")
    if summary["srs_hits"]:
        for item in summary["srs_hits"]:
            kws = ", ".join(item["matched_keywords"])
            focus = ", ".join(item["review_focus"])
            print(f"- `{item['id']}` {item['title']} "
                  f"(keywords: {kws}; focus: {focus})")
    else:
        print("- No direct Doris SRS keyword hit detected from patch text.")
    print()
    print("### Review risks")
    for risk in summary["risks"]:
        print(f"- {risk}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a git diff or patch using Zephyr review rules."
    )
    parser.add_argument("--repo", type=Path,
                        help="Git repo to analyze with git diff")
    parser.add_argument("--diff-ref", default=None,
                        help="Optional git diff ref, such as HEAD~1")
    parser.add_argument("--patch", type=Path,
                        help="Path to an exported patch or diff file")
    parser.add_argument("--rules", type=Path,
                        default=Path(__file__).resolve().parents[1] /
                        "assets" / "zephyr_review_rules.json",
                        help="Path to Zephyr review rules JSON")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON instead of markdown")
    args = parser.parse_args()

    if not args.repo and not args.patch:
        parser.error("one of --repo or --patch is required")
    if args.repo and args.patch:
        parser.error("use only one of --repo or --patch")

    rules = load_rules(args.rules)

    try:
        diff_text = run_git_diff(args.repo, args.diff_ref) if args.repo \
            else read_patch(args.patch)
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        return 1

    changed_files = parse_changed_files(diff_text)
    path_tags = collect_path_tags(changed_files, rules)
    srs_hits = collect_srs_hits(diff_text, rules)
    risks = classify_risks(changed_files, path_tags, srs_hits, diff_text)
    summary = summarize(changed_files, path_tags, srs_hits, risks)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_markdown(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
