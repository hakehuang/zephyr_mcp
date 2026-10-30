---
name: zephyr-code-review
description: Use this skill when the user wants Zephyr project code review guidance, requirement-aware review checklists, patch and scan harness workflows, Zephyr checkpatch help, cyclomatic complexity analysis, or Doris-specific Zephyr Smart Access traceability and risk checks.
---

# Zephyr Code Review

This skill is for Zephyr project code review work.

Use it to review patches, PRs, or design changes with repeatable local
analysis support. When relevant, it also carries Doris-specific Zephyr
Smart Access traceability and risk checks derived from the reviewed Doris
SRS workbook.

## When to Use This Skill

- User wants a Zephyr code review checklist.
- User wants a repo-ready review rules document for Zephyr-focused work.
- User wants a PR reviewed against Zephyr expectations.
- User wants help mapping a change to Doris SRS IDs where applicable.
- User wants gap analysis between upstream Zephyr foundations and
  Doris-specific integrations.
- User wants review comments that call out timing, memory, OTA,
  Bluetooth, Thread, 802.15.4, or security risks.
- User wants a local harness to scan code or analyze patches for review
  relevance.
- User wants Zephyr `checkpatch` help.
- User wants cyclomatic complexity analysis on C code.
- User wants structural C logic, lifecycle, state-machine, resource ownership,
  or error-unwind analysis using Tree-sitter.

## Scope Guardrails

This skill is suitable for general Zephyr review work.

When Doris-specific requirement checks are used, apply them only when the
change affects Doris configurations that explicitly include Zephyr.

Do **not** assume Doris is a Zephyr-only product.

Other Doris configurations in the reviewed SRS reference FreeRTOS, so the
first review step is always to confirm the target profile is actually in
Zephyr scope.

The Doris-specific review anchors in this skill are centered on the
reviewed Smart Access profiles:

- Matter + Aliro + NFC + BLE Channel Sounding + Thread + Zephyr
- Matter + Aliro + NFC + UWB + BLE + Thread + Zephyr

## Known Doris Review Anchors

The following reviewed SRS items are available when Doris-specific
traceability is needed.

### Smart Access configuration and memory items

- `3175745`
- `3175746`
- `3175747`
- `3175748`

### Timing and concurrency items

- `3175742`
- `3175743`
- `3175771`

### Platform, stack, and wireless items

- `3175901`
- `3176012`
- `3176013`
- `3176014`
- `3176015`
- `3176016`

### Security-related item reviewed in this summary

- `1105037`

### Lower-confidence / non-baseline item

- `1295829`

Treat `1295829` as lower-confidence for Zephyr review because the
reviewed remarks indicated rejection of the Zigbee portion.

## Review Principles

### 1. Confirm scope first

- Confirm the target scope is correct.
- If Doris-specific checks are in play, confirm the target profile
  explicitly includes Zephyr.
- Do not review mixed Doris changes as if Zephyr were the only RTOS.
- Make profile assumptions explicit.

### 2. Preserve requirement traceability

- Link comments and conclusions to requirement IDs when they are touched.
- If a requirement is affected indirectly, explain the dependency.
- If a reviewed requirement is not applicable, state why.

### 3. Separate upstream Zephyr from product-specific integration

Upstream Zephyr provides useful foundations in areas such as:

- kernel and scheduling
- Bluetooth host and controller subsystems
- OpenThread module support
- DFU foundations
- storage, settings, and flash-map infrastructure
- mbedTLS and TF-M / PSA integration points
- logging, power management, and related common subsystems

Do **not** assume upstream Zephyr alone fully solves Doris product
requirements without product-specific evidence for:

- Aliro integration
- Matter product integration as a whole
- NXP NFC Reader Library integration
- UWB middleware integration
- PQC OTA product workflow

### 4. Configuration lifecycle integrity

When a Kconfig symbol, configuration macro, or configuration option is
removed, renamed, or replaced, trace it across the full codebase before
approval. Remove or update every dependent reference so no stale behavior
remains.

Review at least these reference classes:

- C/C++/assembly preprocessor guards, conditionals, defaults, and address
  calculations that use `CONFIG_<symbol>` or related generated macros
- Kconfig defaults, `depends on`, `select`, `imply`, and board/SoC defconfig
  values
- CMake, build scripts, linker scripts, image/load-address adjustments, and
  generated-header consumers
- devicetree overlays or bindings, board support files, documentation,
  samples, tests, CI configurations, and helper scripts

Do not accept removal of the configuration definition alone. The patch must
also remove obsolete dependent code, or update each reference to the new
configuration or address model. Require a repository-wide reference search
and relevant build/test evidence when the option affects boot flow, memory
maps, image placement, or multicore startup.

### 5. Focus on regression risk

Prioritize review attention on:

- timing closure
- memory headroom
- OTA storage constraints
- concurrency under load
- wireless stack composition
- key protection and security-backed flows
- code hygiene and complexity hotspots

## Review Workflow

### Step 1: Identify the change boundary

Collect:

- target Zephyr area or product scope
- whether Doris-specific checks apply
- touched subsystems or modules
- expected runtime behaviors that could regress

### Step 2: Map the change to review anchors

Check whether the patch affects one or more of these areas:

- Zephyr platform support
- Zephyr BLE stack support
- OpenThread support
- Channel Sounding and phase coherency
- proprietary 802.15.4 protocol support
- Smart Access stack composition
- timing and concurrency
- memory and OTA via external flash
- security-backed key handling and credential storage
- patch style and complexity hotspots

### Step 3: Review platform and subsystem fit

Where relevant, validate the change against the correct Zephyr areas,
for example:

- `kernel/`
- `subsys/bluetooth/host`
- `subsys/bluetooth/controller`
- `modules/openthread`
- `subsys/dfu`
- storage / settings / flash map areas
- PSA / TF-M / mbedTLS integration points

### Step 4: Analyze changed C logic with Tree-sitter

When the patch changes C source or headers with non-trivial control flow, run
`tools/zephyr_tree_sitter_logic.py` before writing conclusions. This is required
for changes involving:

- PM or device lifecycle callbacks
- state machines, switch-driven dispatch, or mode transitions
- clocks, resets, regulators, locks, runtime references, or other paired resources
- hardware enable/disable register writes
- error exits after partial initialization or state mutation
- rollback, unwind, cleanup, suspend/resume, or power-domain behavior

Prefer changed-file analysis when a usable Git range is available:

```powershell
python tools/zephyr_tree_sitter_logic.py `
  --repo C:\path\to\zephyr `
  --diff-ref origin/main...HEAD `
  --function "pm|init|resume|suspend|enable|disable"
```

Analyze explicit files or a directory when a diff range is unavailable:

```powershell
python tools/zephyr_tree_sitter_logic.py `
  C:\path\to\driver.c `
  --function "pm|init|resume|suspend"
```

If imports fail, install the pinned optional dependencies from
`tools/requirements-tree-sitter.txt`. Do not silently replace structural
analysis with regex-only conclusions.

Interpret the output as a review aid, not a complete path-sensitive control-flow
proof. For every lifecycle case or function:

1. Read the ordered resource events and returns.
2. Identify the intended entry and successful-exit invariants.
3. Inspect every error return after an acquire or hardware mutation.
4. Verify reverse-order cleanup or explicit rollback.
5. Cross-check findings against the PM/framework caller because the framework may
   preserve, advance, or restore software state differently on callback failure.
6. Inspect parser diagnostics and manually read affected preprocessor branches;
   Zephyr C macros and conditional compilation may produce recoverable parse
   diagnostics.

Record the important call sequence, state/resource invariant, failing path, and
framework consequence in the review. Do not report every extracted event as a
defect.

### Step 5: Apply the review checklist

Use the checklist below before approval.

## Zephyr Review Checklist

### A. Platform and profile applicability

- [ ] The change is in the intended Zephyr scope.
- [ ] If Doris-specific checks are used, the target Doris configuration
      explicitly includes Zephyr.
- [ ] The review does not assume Zephyr is the only RTOS in mixed Doris
      scope.
- [ ] Configuration or product assumptions are documented clearly enough
      for later reviewers.

### B. Bluetooth, Thread, and 802.15.4 behavior

- [ ] The change preserves support for the Zephyr BLE stack.
- [ ] The change does not create obvious regression risk against the
      required Bluetooth LE GATT profile support expected from MW30 when
      Doris scope applies.
- [ ] Channel Sounding related changes do not break required phase
      coherency support for CS sniffing when Doris scope applies.
- [ ] OpenThread support remains intact where required.
- [ ] 802.15.4 changes do not block required proprietary protocol
      behavior over compliant PHY/MAC when Doris scope applies.

### C. Product composition and dependency checks

- [ ] Product or application integration assumptions remain valid.
- [ ] OTA via external flash is preserved where required.
- [ ] External UWB IC assumptions are preserved where required.
- [ ] External secure element assumptions are preserved where required.

### D. Memory, flash, and OTA constraints

- [ ] Memory impact has been evaluated where the target profile has
      explicit memory budgets.
- [ ] Partition, image, storage, and DFU changes remain compatible with
      the update flow.
- [ ] Ask for image-size or partition evidence when code inspection is
      not enough.

### E. Timing, scheduling, and real-time behavior

- [ ] Scheduler, thread priority, interrupt, work queue, and blocking
      behavior do not create obvious responsiveness risks.
- [ ] Full-load and concurrency risks are reviewed when relevant.
- [ ] Timing-sensitive product flows are reviewed when Doris-specific
      latency requirements apply.

### F. Security, credentials, and protected services

- [ ] Secure storage expectations remain intact.
- [ ] No change weakens protected credential handling.
- [ ] Firmware update changes do not remove, weaken, or bypass the
      required protected update path.

### G. Patch hygiene and evidence

- [ ] `checkpatch` findings were considered when appropriate.
- [ ] High cyclomatic complexity hotspots were considered when
      appropriate.
- [ ] Tree-sitter structural logic analysis was run for non-trivial changed C
      lifecycle, state-machine, resource ownership, and error-unwind code.
- [ ] Resource acquisitions, hardware state mutations, error returns, and
      reverse-order rollback were cross-checked against framework caller behavior.
- [ ] Tree-sitter parser diagnostics caused by preprocessor-heavy Zephyr C were
      reviewed manually rather than treated as either clean proof or automatic
      defects.
- [ ] Kconfig, devicetree, build, memory-map, or storage assumptions are
      documented if the change depends on them.
- [ ] When a configuration symbol or macro is removed, renamed, or
      replaced, a repository-wide reference search confirms that dependent
      source, Kconfig, CMake/build, linker/image, devicetree, documentation,
      sample, test, CI, and script references were removed or updated.
- [ ] Boot-flow, memory-map, image-placement, or multicore configuration
      changes include focused build/test evidence for the affected targets.
- [ ] Ask for benchmark, log, memory, or test evidence when timing or
      sizing impact cannot be trusted from code inspection alone.

## Local Harness

This skill includes a lightweight local harness for repeatable review
pre-checks.

Files:

- `assets/zephyr_review_rules.json`
  - Zephyr review path rules, Doris SRS anchors, and keyword mappings
- `tools/zephyr_patch_analyzer.py`
  - analyze a git diff or patch file and suggest SRS links and risks
- `tools/zephyr_code_scan.py`
  - scan a source tree for Zephyr and Doris review-relevant files and
    keywords
- `tools/run_zephyr_review.ps1`
  - PowerShell wrapper for patch, scan, optional Zephyr `checkpatch`,
    and C cyclomatic complexity workflows
- `tools/zephyr_cyclomatic_complexity.py`
  - estimate cyclomatic complexity for C/C++ functions and flag review
    candidates above a threshold
- `tools/zephyr_tree_sitter_logic.py`
  - parse C source with Tree-sitter and report functions, switch cases, calls,
    state-changing assignments, returns, and ordered resource events
- `tools/requirements-tree-sitter.txt`
  - pinned optional Python dependencies for the Tree-sitter C analyzer

Use the harness to gather candidate links and review risks before
writing the final review summary. Treat harness output as guidance, not
as automatic approval evidence.

## Output Format

ALWAYS use this structure for the final response:

```text
## Result

[Short review summary]

**Scope check:**
- scope conclusion
- affected subsystem or product scope

**Requirements touched:**
- requirement ID and short reason
- requirement ID and short reason

**Main risks found:**
- risk 1
- risk 2

**Required fixes or follow-ups:**
- fix or evidence request 1
- fix or evidence request 2

**Review outcome:**
- approve / comment / request changes
```

## Notes / Caveats

- This skill supports both general Zephyr code review and Doris-specific
  Zephyr Smart Access review.
- Detailed Doris security requirements were noted as living in Security
  RS.
- Detailed Doris software requirements were noted as living in Software
  RS.
- Do not use Doris-specific anchors to invent new requirements beyond
  the reviewed summary.
