# zephyr-code-review

A Goose skill for reviewing Zephyr project changes, including Doris-
related Smart Access requirements identified from the reviewed Doris SRS
workbook where applicable.

## What this skill is for

Use this skill when you want help with:

- reviewing Zephyr patches or pull requests
- checking Zephyr-based Doris Smart Access scope when relevant
- tracing review comments to Doris SRS IDs where Doris requirements apply
- identifying gaps between upstream Zephyr foundations and Doris-specific
  integration needs
- checking timing, memory, OTA, wireless, and security review risks
- generating structured review summaries for Zephyr changes

## What this skill covers

This skill is suitable for general Zephyr review workflows and is
especially useful when a change may affect Doris configurations that
explicitly include Zephyr, including the reviewed Smart Access profiles:

- Matter + Aliro + NFC + BLE Channel Sounding + Thread + Zephyr
- Matter + Aliro + NFC + UWB + BLE + Thread + Zephyr

It includes guidance for reviewing:

- Zephyr BLE stack support
- OpenThread support
- Channel Sounding and phase coherency concerns
- proprietary IEEE 802.15.4 protocol support
- Smart Access stack composition
- memory and OTA via external flash constraints
- timing and concurrency risks
- credential protection and security-backed flows
- Zephyr patch hygiene with `checkpatch`
- cyclomatic complexity hotspots in C/C++ code

## Important scope note

Doris is not a Zephyr-only product.

Some Doris configurations in the reviewed SRS reference FreeRTOS. Use the
Doris-specific requirement checks only after confirming the change is in
scope for a Zephyr-based Doris profile.

## SRS anchors used by this skill

These Doris anchors are retained for Zephyr reviews when Doris-specific
traceability is needed.

### Smart Access configuration and memory

- `3175745`
- `3175746`
- `3175747`
- `3175748`

### Timing and concurrency

- `3175742`
- `3175743`
- `3175771`

### Platform, stack, and wireless

- `3175901`
- `3176012`
- `3176013`
- `3176014`
- `3176015`
- `3176016`

### Security

- `1105037`

### Lower-confidence / non-baseline

- `1295829`

## Harness and scripts

This skill includes a local review harness:

- `assets/zephyr_review_rules.json`
  - Zephyr review rules, Doris SRS anchors, path tags, and keyword mapping
- `tools/zephyr_patch_analyzer.py`
  - analyze a git diff or exported patch and suggest SRS links and risks
- `tools/zephyr_code_scan.py`
  - scan a source tree for Zephyr and Doris review-relevant files and
    keywords
- `tools/run_zephyr_review.ps1`
  - PowerShell wrapper for patch analysis, code scan, optional
    Zephyr `checkpatch`, and C cyclomatic complexity workflows
- `tools/zephyr_cyclomatic_complexity.py`
  - estimate cyclomatic complexity for C/C++ functions and flag high
    complexity candidates
- `tools/zephyr_tree_sitter_logic.py`
  - structurally extract C functions, switch cases, calls, assignments,
    returns, and ordered resource events for lifecycle/error-path review
- `tools/requirements-tree-sitter.txt`
  - pinned optional dependencies for Tree-sitter C analysis

### Example commands

Patch analysis from a git repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_zephyr_review.ps1 \
  -Mode patch \
  -Repo C:\github\zephyrproject\zephyr \
  -DiffRef HEAD~1
```

Patch analysis from an exported patch:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_zephyr_review.ps1 \
  -Mode patch \
  -Patch C:\temp\change.patch
```

Code scan of a tree:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_zephyr_review.ps1 \
  -Mode scan \
  -Repo C:\github\zephyrproject\zephyr \
  -MaxHits 100
```

Optional Zephyr checkpatch run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_zephyr_review.ps1 \
  -Mode checkpatch \
  -Repo C:\github\vero_skill_for_zephyr \
  -ZephyrBase C:\github\zephyrproject\zephyr
```

C cyclomatic complexity analysis:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_zephyr_review.ps1 `
  -Mode complexity `
  -Target C:\github\zephyrproject\zephyr\subsys\bluetooth `
  -ComplexityThreshold 10
```

Tree-sitter analysis of changed C files:

```powershell
python -m pip install -r .\tools\requirements-tree-sitter.txt
powershell -ExecutionPolicy Bypass -File .\tools\run_zephyr_review.ps1 `
  -Mode logic `
  -Repo C:\github\zephyrproject\zephyr `
  -DiffRef origin/main...HEAD `
  -Function "pm|init|resume|suspend|enable|disable"
```

Tree-sitter analysis of an explicit driver file:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_zephyr_review.ps1 `
  -Mode logic `
  -Target C:\github\zephyrproject\zephyr\drivers\example.c `
  -Json `
  -Output C:\temp\example-logic.json
```

Treat this output as structural review evidence, not a path-sensitive CFG proof.
Inspect reported parse diagnostics and relevant preprocessor branches manually.

The wrapper will also look for Perl in common installed locations such
as `C:\Strawberry\perl\bin\perl.exe`.

## Example prompts

- "Review this Zephyr PR with the code review skill."
- "Give me a Zephyr code review checklist for this patch."
- "Map this Zephyr change to the Doris SRS IDs if relevant."
- "What Doris-specific gaps are still not covered by upstream Zephyr?"
- "Draft review comments for timing and OTA risks in this Zephyr change."
- "Run the Zephyr patch analyzer on this repo diff."
- "Scan this tree for Zephyr review-relevant files and Doris SRS hits."
- "Run Zephyr checkpatch for this patch."
- "Analyze C cyclomatic complexity in this Zephyr folder."
- "Use Tree-sitter to review lifecycle and rollback logic in these drivers."

## Typical output

This skill is designed to produce concise, structured reviews with:

- scope conclusion
- relevant SRS IDs when applicable
- main risks found
- required fixes or evidence requests
- final review outcome

## Files

- `SKILL.md` - main skill instructions and checklist
- `README.md` - quick usage guide and examples
