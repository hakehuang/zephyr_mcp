# Skill: Build a Board-Level Digital Twin Model

## Goal

Turn Zephyr board metadata into a useful board-level digital twin seed and then refine it into a higher-fidelity model.

## Phase 1: Extract

Use the generator script to pull from `boards/nxp`:

- board names and full names
- SoCs and variants from `board.yml`
- target definitions from `*.yaml`
- supported features
- toolchains
- memory sizes
- special directories such as `dts/`, `support/`, and board-specific source files

## Phase 2: Seed

For each board, create a seed object with:

- stable twin id
- board classification
- target variants
- SoC inventory
- capability list
- development and lab metadata

The generated file `knowledge/nxp_digital_twin_seeds.json` provides this initial seed set.

## Phase 3: Refine

Add higher-fidelity attributes not present in the Zephyr board metadata:

- clock tree and frequencies
- interrupt relationships
- communication buses
- pin ownership
- physical connectors
- external memories
- sensor topology
- boot and flash constraints
- performance envelopes
- safety constraints

## Phase 4: Validate

Validation can be done in one or more modes:

- static consistency checks against Zephyr metadata
- build validation with Twister or west
- hardware-in-the-loop validation against a real board
- remote lab validation through SSH-accessible hosts

## Phase 5: Operationalize

Create board-specific adapters under future twin runtime code, for example:

- telemetry acquisition
- flash or reset orchestration
- synthetic sensor injection
- fault simulation
- environment profiles

## Practical note for `mimxrt1170_evk`

The current workspace has known lab details for `mimxrt1170_evk`, so it is a good first candidate for a closed-loop twin:

- remote host: `ubuntu@10.17.12.234`
- remote Zephyr tree: `/home/shared/disk/zephyr_project/zephyr_test/zephyr`
- flash command: `west flash --runner linkserver --probe "CMYBV2XFSPLRA"`
