# Skill: Derive a Custom Board from an Existing Zephyr Board Twin

## Goal

Create a custom board digital twin by inheriting from an existing Zephyr-supported board and then applying project-specific overrides.

## Current example

- base board: `mimxrt1170_evk`
- derived board: `dg_evk`

## Workflow

1. Start from the base seed in `knowledge/nxp_digital_twin_seeds.json`.
2. Create a spec file describing the new board name, display name, target identifiers, and customization notes.
3. Run `tools/create_custom_board.py` to generate a derived board twin JSON.
4. Store the output in `knowledge/twins/`.
5. Update the Zephyr custom board implementation to match the twin assumptions.

## Example command

```bat
python digital_twins_nxp\tools\create_custom_board.py ^
  --seeds digital_twins_nxp\knowledge\nxp_digital_twin_seeds.json ^
  --base-board mimxrt1170_evk ^
  --new-board dg_evk ^
  --spec digital_twins_nxp\knowledge\dg_evk_spec.json ^
  --out digital_twins_nxp\knowledge\twins\dg_evk.json ^
  --index digital_twins_nxp\knowledge\custom_boards_index.json
```

## What the derivation changes

- renames the board identity from the base board to the new board
- rewrites target identifiers to the new board name
- preserves inherited hardware and lab metadata unless overridden
- records derivation metadata for traceability

## What still needs human definition

- real connector map
- changed peripherals
- changed pinctrl
- changed memory devices
- changed power rails
- changed sensors and displays
- any differences in flash and bring-up behavior

## `dg_evk` note

The initial `dg_evk` twin is intentionally compatible with the `mimxrt1170_evk` capability profile and lab workflow. Refine it as soon as the custom board electrical and software deltas are known.
