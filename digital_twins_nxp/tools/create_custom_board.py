from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def merge_dict(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def replace_board_name(value: Any, base_board: str, new_board: str) -> Any:
    if isinstance(value, str):
        return value.replace(base_board, new_board)
    if isinstance(value, list):
        return [replace_board_name(item, base_board, new_board) for item in value]
    if isinstance(value, dict):
        return {key: replace_board_name(item, base_board, new_board) for key, item in value.items()}
    return value


def derive_board(seed: dict[str, Any], new_board: str, spec: dict[str, Any]) -> dict[str, Any]:
    base_board = seed["board"]
    derived = replace_board_name(deepcopy(seed), base_board, new_board)

    derived["twin_id"] = spec.get("twin_id", f"nxp.{new_board}")
    derived["board"] = new_board
    derived["display_name"] = spec.get("display_name", new_board.upper())

    derived.setdefault("classification", {})
    derived.setdefault("hardware", {})
    derived.setdefault("development", {})
    derived.setdefault("notes", [])

    derived["derivation"] = {
        "base_board": base_board,
        "base_twin_id": seed.get("twin_id"),
        "derived_at": datetime.now(timezone.utc).isoformat(),
        "mode": "customized_board",
    }

    derived["development"]["board_source_path"] = spec.get(
        "board_source_path",
        str(Path(seed["development"]["board_source_path"]).parent / new_board),
    )

    if "board_name" in spec:
        derived["board"] = spec["board_name"]
    if "notes_append" in spec:
        derived["notes"] = list(derived.get("notes", [])) + list(spec["notes_append"])

    if "overrides" in spec:
        derived = merge_dict(derived, spec["overrides"])

    derived.setdefault("customization", {})
    derived["customization"] = merge_dict(
        derived["customization"],
        {
            "inherits_from": base_board,
            "intended_zephyr_board_name": new_board,
        },
    )
    if "customization" in spec:
        derived["customization"] = merge_dict(derived["customization"], spec["customization"])

    return derived


def update_index(index_path: Path, board_name: str, output_path: Path, base_board: str) -> None:
    if index_path.exists():
        index = load_json(index_path)
    else:
        index = {
            "generated_at": None,
            "custom_boards": {},
        }

    index["generated_at"] = datetime.now(timezone.utc).isoformat()
    index.setdefault("custom_boards", {})
    index["custom_boards"][board_name] = {
        "base_board": base_board,
        "path": str(output_path),
    }
    write_json(index_path, index)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a customized digital twin board derived from an existing base board seed.")
    parser.add_argument("--seeds", required=True, help="Path to nxp_digital_twin_seeds.json")
    parser.add_argument("--base-board", required=True, help="Base board name, for example mimxrt1170_evk")
    parser.add_argument("--new-board", required=True, help="New customized board name, for example dg_evk")
    parser.add_argument("--spec", help="Optional JSON spec file with overrides")
    parser.add_argument("--out", required=True, help="Output path for the derived board JSON")
    parser.add_argument("--index", help="Optional custom boards index JSON to update")
    args = parser.parse_args()

    seeds_payload = load_json(Path(args.seeds))
    seeds = seeds_payload.get("seeds", {})
    if args.base_board not in seeds:
        raise SystemExit(f"Base board not found in seeds: {args.base_board}")

    spec: dict[str, Any] = {}
    if args.spec:
        spec = load_json(Path(args.spec))

    seed = seeds[args.base_board]
    derived = derive_board(seed, args.new_board, spec)

    output_path = Path(args.out)
    write_json(output_path, derived)

    if args.index:
        update_index(Path(args.index), derived["board"], output_path, args.base_board)

    print(f"Created customized board: {derived['board']}")
    print(f"Base board: {args.base_board}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
