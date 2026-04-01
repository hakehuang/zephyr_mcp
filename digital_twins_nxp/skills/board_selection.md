# Skill: Select an NXP Board for a Digital Twin

## Goal

Choose an NXP Zephyr board and target variant that is a good fit for a digital twin use case.

## Inputs

- `knowledge/nxp_board_inventory.json`
- `knowledge/nxp_board_inventory.md`
- the intended system behavior to model
- optional real hardware access constraints

## Workflow

1. Identify the board family needed:
   - `mimxrt` for MCU and crossover MCU work
   - `imx` for heterogeneous application and control systems
   - `mcx` for modern MCU platforms and peripheral-rich control nodes
   - `lpcxpresso` for LPC-based development boards
   - `s32` for automotive and real-time control targets
2. Filter by target capabilities:
   - networking (`netif:eth`)
   - usb (`usb_device`, `usbd`)
   - storage (`sdhc`, `flash`, `nvs`)
   - control (`pwm`, `counter`, `watchdog`)
   - analog (`adc`, `dac`)
3. Check target architecture and cpu cluster variants.
4. Prefer boards with richer metadata and support files when modeling bring-up behavior.
5. If hardware-in-the-loop validation matters, prioritize boards with known lab access.

## Selection heuristics

- Use target identifiers, not only board names, when the board has multiple runtime variants.
- Treat `_ns`, `_qspi`, `_smp`, `_ddr`, `cm4`, `cm7`, `cpu0`, and `cpu1` as distinct twin deployment modes.
- Boards with `board.c`, overlays, or support scripts often need more explicit initialization in the twin.

## Example

For Ethernet-enabled real hardware validation, `mimxrt1170_evk` is a strong starter because:

- it has multiple CPU targets
- it advertises `netif:eth`
- it has known lab connectivity in the current workspace
