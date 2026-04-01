from __future__ import annotations

import argparse
import shutil
from pathlib import Path

TEXT_SUFFIXES = {
    ".c",
    ".cmake",
    ".conf",
    ".defconfig",
    ".dts",
    ".dtsi",
    ".h",
    ".ld",
    ".md",
    ".overlay",
    ".rst",
    ".txt",
    ".yaml",
    ".yml",
    "",
}


def is_text_file(path: Path) -> bool:
    name = path.name
    if name == "Kconfig" or name.startswith("Kconfig."):
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def rename_path_parts(path: Path, base_board: str, new_board: str) -> Path:
    parts = [part.replace(base_board, new_board) for part in path.parts]
    return Path(*parts)


def replace_text(content: str, base_board: str, new_board: str, new_display_name: str) -> str:
    base_symbol = base_board.upper()
    new_symbol = new_board.upper()
    base_board_config = f"BOARD_{base_symbol}"
    new_board_config = f"BOARD_{new_symbol}"
    base_display_name = "MIMXRT1170-EVK"
    base_display_name_b = "MIMXRT1170-EVKB"
    new_display_name_b = f"{new_display_name}-B"

    replacements = [
        (base_board_config, new_board_config),
        (base_symbol, new_symbol),
        (base_board, new_board),
        (base_display_name_b, new_display_name_b),
        (base_display_name, new_display_name),
        ('model = "NXP MIMXRT1170-EVK board";', f'model = "NXP {new_display_name} board";'),
        (".. zephyr:board:: mimxrt1170_evk", f".. zephyr:board:: {new_board}"),
        ("Hello World! mimxrt1170_evk", f"Hello World! {new_board}"),
    ]

    updated = content
    for old, new in replacements:
        updated = updated.replace(old, new)
    return updated


def copy_and_transform(source_dir: Path, dest_dir: Path, base_board: str, new_board: str, new_display_name: str) -> None:
    for source_path in source_dir.rglob("*"):
        relative = source_path.relative_to(source_dir)
        target_relative = rename_path_parts(relative, base_board, new_board)
        target_path = dest_dir / target_relative

        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if is_text_file(source_path):
            content = source_path.read_text(encoding="utf-8")
            transformed = replace_text(content, base_board, new_board, new_display_name)
            target_path.write_text(transformed, encoding="utf-8")
        else:
            shutil.copy2(source_path, target_path)


def patch_board_files(dest_dir: Path, new_board: str, new_display_name: str) -> None:
    board_yml = dest_dir / "board.yml"
    if board_yml.exists():
        text = board_yml.read_text(encoding="utf-8")
        text = text.replace(f"name: {new_board}", f"name: {new_board}")
        text = text.replace("full_name: DG-EVK-B", f"full_name: {new_display_name}")
        text = text.replace("full_name: DG-EVK", f"full_name: {new_display_name}")
        board_yml.write_text(text, encoding="utf-8")

    doc_index = dest_dir / "doc" / "index.rst"
    if doc_index.exists():
        text = doc_index.read_text(encoding="utf-8")
        if f".. zephyr:board:: {new_board}" in text and f"derived from the upstream ``mimxrt1170_evk`` board" not in text:
            text = text.replace(
                f".. zephyr:board:: {new_board}\n",
                f".. zephyr:board:: {new_board}\n\nThis board definition was derived from the upstream ``mimxrt1170_evk`` board and should be refined for DG-EVK-specific hardware differences.\n",
                1,
            )
        doc_index.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Zephyr custom board by copying and renaming an existing board directory.")
    parser.add_argument("--source-dir", required=True, help="Source board directory")
    parser.add_argument("--dest-dir", required=True, help="Destination board directory")
    parser.add_argument("--base-board", required=True, help="Source board name, for example mimxrt1170_evk")
    parser.add_argument("--new-board", required=True, help="New board name, for example dg_evk")
    parser.add_argument("--new-display-name", default="DG-EVK", help="Display name to use in metadata")
    parser.add_argument("--force", action="store_true", help="Overwrite destination if it already exists")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    dest_dir = Path(args.dest_dir).resolve()

    if not source_dir.exists():
        raise SystemExit(f"Source board directory does not exist: {source_dir}")
    if dest_dir.exists():
        if not args.force:
            raise SystemExit(f"Destination already exists: {dest_dir}. Use --force to overwrite.")
        shutil.rmtree(dest_dir)

    dest_dir.mkdir(parents=True, exist_ok=True)
    copy_and_transform(source_dir, dest_dir, args.base_board, args.new_board, args.new_display_name)
    patch_board_files(dest_dir, args.new_board, args.new_display_name)

    print(f"Created custom Zephyr board at: {dest_dir}")
    print(f"Base board: {args.base_board}")
    print(f"New board: {args.new_board}")


if __name__ == "__main__":
    main()
