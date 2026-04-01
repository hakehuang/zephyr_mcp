# NXP Zephyr Digital Twins Project

A starter project for building digital twins from the boards under `C:\github\zephyrproject\zephyr\boards\nxp`.

## Purpose

This project creates a reusable foundation for:

- discovering NXP Zephyr boards and targets
- extracting board metadata into machine-readable knowledge
- seeding digital twin definitions per board
- documenting repeatable skills for board selection and twin modeling

## Project structure

- `tools/` — scripts that generate or refresh board knowledge
- `skills/` — workflow guides for using and extending the twin project
- `knowledge/` — generated inventory, seeds, and reference notes

## Current source

- Zephyr board source: `C:\github\zephyrproject\zephyr\boards\nxp`
- Local `ZEPHYR_BASE`: `C:\github\zephyrproject\zephyr`

## Included outputs

- `knowledge/nxp_board_inventory.json`
- `knowledge/nxp_board_inventory.md`
- `knowledge/nxp_digital_twin_seeds.json`
- `knowledge/twins/dg_evk.json` after custom-board derivation
- `knowledge/custom_boards_index.json` after custom-board derivation

## Custom board derivation

This project also supports deriving a custom board twin from an existing Zephyr base board.

Current example:

- base board: `mimxrt1170_evk`
- custom board: `dg_evk`

Use:

```bat
python digital_twins_nxp\tools\create_custom_board.py --seeds digital_twins_nxp\knowledge\nxp_digital_twin_seeds.json --base-board mimxrt1170_evk --new-board dg_evk --spec digital_twins_nxp\knowledge\dg_evk_spec.json --out digital_twins_nxp\knowledge\twins\dg_evk.json --index digital_twins_nxp\knowledge\custom_boards_index.json
```

## Refresh the knowledge

From `C:\github\zephyr_mcp` run:

```bat
python digital_twins_nxp\tools\generate_nxp_board_knowledge.py --source "C:\github\zephyrproject\zephyr\boards\nxp" --outdir "C:\github\zephyr_mcp\digital_twins_nxp\knowledge"
```

## Suggested next steps

1. Pick one board family such as `mimxrt`, `imx`, or `mcx`.
2. Add higher-fidelity twin attributes:
   - clocks
   - buses
   - memory map
   - power domains
   - sensors and peripherals
3. Add board-specific simulation adapters or validation hooks.
4. Connect a twin to real hardware validation when available.

## Lab-backed board note

Workspace notes include a real-lab profile for `mimxrt1170_evk`, including:

- SSH host: `ubuntu@10.17.12.234`
- Remote Zephyr path: `/home/shared/disk/zephyr_project/zephyr_test/zephyr`
- Serial id: `/dev/serial/by-id/usb-NXP_Semiconductors_MCU-LINK_on-board__r0E2__CMSIS-DAP_V2.250_CMYBV2XFSPLRA-if02`
- Flash pattern: `west flash --runner linkserver --probe "CMYBV2XFSPLRA"`

That profile is embedded in the generated twin seed for `mimxrt1170_evk`.
