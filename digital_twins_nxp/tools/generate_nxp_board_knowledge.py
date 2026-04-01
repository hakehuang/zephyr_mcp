from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def clean_value(value: str) -> str:
    value = value.strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        value = value[1:-1]
    return value.strip()


def parse_int(value: str) -> int | None:
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else None


def infer_family(board_name: str) -> str:
    if board_name.startswith(("frdm_imx", "imx")):
        return "imx"
    if board_name.startswith(("frdm_mcx", "mcx")):
        return "mcx"
    if board_name.startswith(("mimxrt", "vmu_rt")):
        return "mimxrt"
    if board_name.startswith("lpcxpresso"):
        return "lpcxpresso"
    if board_name.startswith(("s32", "mr_", "ucans")):
        return "s32"
    if board_name.startswith(("frdm_rw", "rd_rw")):
        return "rw61x"
    if board_name.startswith("twr_"):
        return "tower"
    if board_name.startswith("usb_"):
        return "usb_dongle"
    if board_name.startswith("ls"):
        return "layerscape"
    if board_name.startswith("rddrone"):
        return "drone"
    return "other"


def infer_form_factor(board_name: str) -> str:
    if board_name.startswith("frdm_"):
        return "frdm"
    if board_name.endswith("_evk"):
        return "evk"
    if board_name.endswith("_mek"):
        return "mek"
    if board_name.startswith("lpcxpresso"):
        return "lpcxpresso"
    if board_name.endswith("_qsb"):
        return "qsb"
    if board_name.startswith("twr_"):
        return "tower"
    if board_name.startswith("rd_"):
        return "reference_design"
    if board_name.startswith("usb_"):
        return "usb_dongle"
    return "other"


def parse_board_yml(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "board_name": None,
        "full_name": None,
        "vendor": None,
        "socs": [],
        "revision_default": None,
        "revisions": [],
    }

    if not path.exists():
        return info

    lines = path.read_text(encoding="utf-8").splitlines()
    in_socs = False
    socs_indent = -1
    current_soc: dict[str, Any] | None = None
    in_variants = False
    variants_indent = -1
    in_revision = False
    revision_indent = -1
    in_revisions_list = False
    revisions_list_indent = -1

    for raw in lines:
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        stripped = line.strip()

        if indent == 2 and stripped.startswith("name:") and info["board_name"] is None:
            info["board_name"] = clean_value(stripped.split(":", 1)[1])
            continue
        if indent == 2 and stripped.startswith("full_name:"):
            info["full_name"] = clean_value(stripped.split(":", 1)[1])
            continue
        if indent == 2 and stripped.startswith("vendor:"):
            info["vendor"] = clean_value(stripped.split(":", 1)[1])
            continue
        if indent == 2 and stripped == "socs:":
            in_socs = True
            socs_indent = indent
            current_soc = None
            in_variants = False
            continue
        if indent == 2 and stripped == "revision:":
            in_revision = True
            revision_indent = indent
            in_revisions_list = False
            continue

        if in_socs and indent <= socs_indent:
            in_socs = False
            in_variants = False
            current_soc = None

        if in_revision and indent <= revision_indent:
            in_revision = False
            in_revisions_list = False

        if in_socs:
            if indent == socs_indent + 2 and stripped.startswith("- name:"):
                current_soc = {"name": clean_value(stripped.split(":", 1)[1]), "variants": []}
                info["socs"].append(current_soc)
                in_variants = False
                continue
            if current_soc and stripped == "variants:":
                in_variants = True
                variants_indent = indent
                continue
            if in_variants and indent <= variants_indent:
                in_variants = False
            if in_variants and current_soc and stripped.startswith("- name:"):
                current_soc["variants"].append(clean_value(stripped.split(":", 1)[1]))
                continue

        if in_revision:
            if stripped.startswith("default:"):
                info["revision_default"] = clean_value(stripped.split(":", 1)[1])
                continue
            if stripped == "revisions:":
                in_revisions_list = True
                revisions_list_indent = indent
                continue
            if in_revisions_list and indent <= revisions_list_indent:
                in_revisions_list = False
            if in_revisions_list and stripped.startswith("- name:"):
                info["revisions"].append(clean_value(stripped.split(":", 1)[1]))
                continue

    return info


def parse_target_yaml(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "file": path.name,
        "identifier": None,
        "name": None,
        "type": None,
        "arch": None,
        "vendor": None,
        "ram": None,
        "flash": None,
        "toolchain": [],
        "supported": [],
    }

    lines = path.read_text(encoding="utf-8").splitlines()
    active_list: str | None = None
    active_indent = -1

    for raw in lines:
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        stripped = line.strip()

        if active_list and indent <= active_indent and not stripped.startswith("- "):
            active_list = None

        if active_list and stripped.startswith("- "):
            info[active_list].append(clean_value(stripped[2:]))
            continue

        if stripped in {"toolchain:", "supported:"}:
            active_list = stripped[:-1]
            active_indent = indent
            continue

        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = clean_value(value)

        if key in {"identifier", "name", "type", "arch", "vendor"}:
            info[key] = value
        elif key in {"ram", "flash"}:
            info[key] = parse_int(value)

    return info


def build_lab_profile(board_name: str) -> dict[str, Any]:
    if board_name != "mimxrt1170_evk":
        return {}

    return {
        "ssh_host": "ubuntu@10.17.12.234",
        "ssh_password": "ubuntu",
        "remote_zephyr_path": "/home/shared/disk/zephyr_project/zephyr_test/zephyr",
        "serial_by_id": "/dev/serial/by-id/usb-NXP_Semiconductors_MCU-LINK_on-board__r0E2__CMSIS-DAP_V2.250_CMYBV2XFSPLRA-if02",
        "flash_command": 'west flash --runner linkserver --probe "CMYBV2XFSPLRA"',
        "notes": [
            "Target board context supplied by the local workspace notes.",
            "Useful when validating the digital twin against real hardware.",
        ],
    }


def summarize_board(board_dir: Path) -> dict[str, Any]:
    board_name = board_dir.name
    board_yml = parse_board_yml(board_dir / "board.yml")
    target_yamls = sorted(
        [p for p in board_dir.glob("*.yaml") if p.name != "board.yml"],
        key=lambda item: item.name,
    )
    targets = [parse_target_yaml(path) for path in target_yamls]

    capabilities = sorted({cap for target in targets for cap in target["supported"]})
    toolchains = sorted({tool for target in targets for tool in target["toolchain"]})
    architectures = sorted({target["arch"] for target in targets if target["arch"]})
    target_types = sorted({target["type"] for target in targets if target["type"]})
    target_identifiers = [target["identifier"] for target in targets if target["identifier"]]
    target_names = [target["name"] for target in targets if target["name"]]
    max_ram = max((target["ram"] or 0 for target in targets), default=0) or None
    max_flash = max((target["flash"] or 0 for target in targets), default=0) or None

    socs = [soc["name"] for soc in board_yml["socs"] if soc.get("name")]
    variants = sorted({variant for soc in board_yml["socs"] for variant in soc.get("variants", [])})

    special_dirs = [
        child.name
        for child in sorted(board_dir.iterdir(), key=lambda item: item.name)
        if child.is_dir() and child.name not in {"doc", "dts", "support"}
    ]

    summary = {
        "board": board_name,
        "full_name": board_yml["full_name"] or board_name,
        "vendor": board_yml["vendor"] or "nxp",
        "family": infer_family(board_name),
        "form_factor": infer_form_factor(board_name),
        "path": str(board_dir),
        "board_yml": (board_dir / "board.yml").name if (board_dir / "board.yml").exists() else None,
        "socs": socs,
        "variants": variants,
        "revision_default": board_yml["revision_default"],
        "revisions": board_yml["revisions"],
        "targets": targets,
        "target_identifiers": target_identifiers,
        "target_names": target_names,
        "architectures": architectures,
        "target_types": target_types,
        "capabilities": capabilities,
        "toolchains": toolchains,
        "max_ram_kib": max_ram,
        "max_flash_kib": max_flash,
        "has_doc": (board_dir / "doc").exists(),
        "has_support": (board_dir / "support").exists(),
        "has_dts_dir": (board_dir / "dts").exists(),
        "has_board_c": (board_dir / "board.c").exists(),
        "has_board_cmake": (board_dir / "board.cmake").exists(),
        "top_level_dts_files": sorted([path.name for path in board_dir.glob("*.dts")]),
        "top_level_overlays": sorted([path.name for path in board_dir.glob("*.overlay")]),
        "special_dirs": special_dirs,
        "lab_profile": build_lab_profile(board_name),
    }

    summary["digital_twin_seed"] = {
        "twin_id": f"nxp.{board_name}",
        "board": board_name,
        "display_name": summary["full_name"],
        "classification": {
            "vendor": summary["vendor"],
            "family": summary["family"],
            "form_factor": summary["form_factor"],
            "architectures": architectures,
            "target_types": target_types,
        },
        "hardware": {
            "socs": socs,
            "variants": variants,
            "revisions": summary["revisions"],
            "revision_default": summary["revision_default"],
            "targets": target_identifiers,
            "max_ram_kib": max_ram,
            "max_flash_kib": max_flash,
        },
        "capabilities": capabilities,
        "development": {
            "toolchains": toolchains,
            "has_doc": summary["has_doc"],
            "has_support": summary["has_support"],
            "board_cmake": summary["has_board_cmake"],
            "board_source_path": str(board_dir),
        },
        "lab_profile": summary["lab_profile"],
        "notes": [
            "Generated from Zephyr board metadata.",
            "Enrich this seed with connectors, sensor topology, timing, and physical constraints for higher-fidelity twins.",
        ],
    }

    return summary


def render_markdown(records: list[dict[str, Any]], source_root: Path) -> str:
    family_counts = Counter(record["family"] for record in records)
    form_counts = Counter(record["form_factor"] for record in records)
    capability_counts = Counter(cap for record in records for cap in record["capabilities"])
    total_targets = sum(len(record["targets"]) for record in records)

    lines: list[str] = []
    lines.append("# NXP Zephyr Board Inventory for Digital Twins")
    lines.append("")
    lines.append(f"Generated from: `{source_root}`")
    lines.append(f"Generated at: `{datetime.now(timezone.utc).isoformat()}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Boards discovered: **{len(records)}**")
    lines.append(f"- Target YAML definitions discovered: **{total_targets}**")
    lines.append(f"- Unique families: **{len(family_counts)}**")
    lines.append("")
    lines.append("### Boards by family")
    lines.append("")
    lines.append("| Family | Count |")
    lines.append("|---|---:|")
    for family, count in sorted(family_counts.items()):
        lines.append(f"| {family} | {count} |")
    lines.append("")
    lines.append("### Boards by form factor")
    lines.append("")
    lines.append("| Form factor | Count |")
    lines.append("|---|---:|")
    for form_factor, count in sorted(form_counts.items()):
        lines.append(f"| {form_factor} | {count} |")
    lines.append("")
    lines.append("### Most common capabilities")
    lines.append("")
    lines.append("| Capability | Boards |")
    lines.append("|---|---:|")
    for capability, count in capability_counts.most_common(20):
        lines.append(f"| {capability} | {count} |")
    lines.append("")
    lines.append("## Board catalog")
    lines.append("")
    lines.append("| Board | Full name | Family | Targets | SoCs | Max RAM KiB | Max Flash KiB |")
    lines.append("|---|---|---|---:|---|---:|---:|")
    for record in records:
        socs = ", ".join(record["socs"]) if record["socs"] else "-"
        lines.append(
            f"| `{record['board']}` | {record['full_name']} | {record['family']} | {len(record['targets'])} | {socs} | {record['max_ram_kib'] or '-'} | {record['max_flash_kib'] or '-'} |"
        )
    lines.append("")
    lines.append("## Twin modeling notes")
    lines.append("")
    lines.append("- Use `targets` as deployable runtime variants in the twin model.")
    lines.append("- Use `socs`, `architectures`, and `toolchains` to derive execution envelopes.")
    lines.append("- Use `capabilities` as the first-pass digital twin feature list.")
    lines.append("- Boards with `support/`, `dts/`, or `board.c` often need extra bring-up logic represented in the twin.")
    lines.append("")
    lines.append("## Highlighted lab-backed board")
    lines.append("")
    lines.append("The workspace context includes live-lab notes for `mimxrt1170_evk`, including probe id, remote Zephyr path, and a verified `west flash` pattern. Those notes are injected into the generated digital twin seed for that board.")
    lines.append("")
    return "\n".join(lines) + "\n"


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate NXP Zephyr board knowledge for digital twin projects.")
    parser.add_argument(
        "--source",
        default=os.path.join(os.environ.get("ZEPHYR_BASE", ""), "boards", "nxp") if os.environ.get("ZEPHYR_BASE") else None,
        help="Path to Zephyr boards/nxp directory. Defaults to $ZEPHYR_BASE/boards/nxp when available.",
    )
    parser.add_argument(
        "--outdir",
        default=str(Path(__file__).resolve().parents[1] / "knowledge"),
        help="Output directory for generated knowledge artifacts.",
    )
    args = parser.parse_args()

    if not args.source:
        raise SystemExit("A source path is required. Pass --source or set ZEPHYR_BASE.")

    source_root = Path(args.source).resolve()
    if not source_root.exists():
        raise SystemExit(f"Source path does not exist: {source_root}")

    records = [
        summarize_board(path)
        for path in sorted(source_root.iterdir(), key=lambda item: item.name)
        if path.is_dir() and path.name != "common"
    ]

    outdir = Path(args.outdir).resolve()
    ensure_directory(outdir)
    ensure_directory(outdir / "twins")

    inventory_path = outdir / "nxp_board_inventory.json"
    seeds_path = outdir / "nxp_digital_twin_seeds.json"
    markdown_path = outdir / "nxp_board_inventory.md"

    inventory_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source_root),
        "board_count": len(records),
        "records": records,
    }
    seeds_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source_root),
        "board_count": len(records),
        "seeds": {record["board"]: record["digital_twin_seed"] for record in records},
    }

    inventory_path.write_text(json.dumps(inventory_payload, indent=2), encoding="utf-8")
    seeds_path.write_text(json.dumps(seeds_payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(records, source_root), encoding="utf-8")

    print(f"Generated {inventory_path}")
    print(f"Generated {seeds_path}")
    print(f"Generated {markdown_path}")


if __name__ == "__main__":
    main()
