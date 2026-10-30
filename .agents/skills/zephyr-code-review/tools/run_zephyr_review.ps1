param(
    [ValidateSet('scan','patch','checkpatch','complexity','logic')]
    [string]$Mode = 'patch',

    [string]$Repo,
    [string]$DiffRef,
    [string]$Patch,
    [string]$ZephyrBase,
    [string]$Target,
    [switch]$Json,
    [string]$Function,
    [string]$Output,
    [int]$MaxHits = 200,
    [int]$ComplexityThreshold = 10
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillRoot = Split-Path -Parent $ScriptDir
$Rules = Join-Path $SkillRoot 'assets\zephyr_review_rules.json'
$PatchTool = Join-Path $ScriptDir 'zephyr_patch_analyzer.py'
$ScanTool = Join-Path $ScriptDir 'zephyr_code_scan.py'

function Get-CommandPath {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    return $null
}

function Get-Python {
    $candidates = @('python', 'py -3')
    foreach ($candidate in $candidates) {
        try {
            $null = Invoke-Expression "$candidate --version"
            return $candidate
        } catch {
        }
    }
    throw 'Python 3 was not found in PATH.'
}

function Get-Perl {
    $fromPath = Get-CommandPath 'perl'
    if ($fromPath) {
        return $fromPath
    }

    $known = @(
        'C:\Strawberry\perl\bin\perl.exe',
        'C:\Perl64\bin\perl.exe',
        'C:\Perl\bin\perl.exe'
    )
    foreach ($candidate in $known) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    return $null
}

$Python = Get-Python
$ComplexityTool = Join-Path $ScriptDir 'zephyr_cyclomatic_complexity.py'
$LogicTool = Join-Path $ScriptDir 'zephyr_tree_sitter_logic.py'

if ($Mode -eq 'logic') {
    if (-not $Target -and -not ($Repo -and $DiffRef)) {
        throw 'For logic mode, provide -Target, or use -Repo with -DiffRef for changed C files.'
    }

    $cmd = @($LogicTool)
    if ($Repo -and $DiffRef) {
        $cmd += @('--repo', $Repo, '--diff-ref', $DiffRef)
    }
    if ($Target) {
        $cmd += $Target
    }
    if ($Function) {
        $cmd += @('--function', $Function)
    }
    if ($Json) {
        $cmd += '--json'
    }
    if ($Output) {
        $cmd += @('--output', $Output)
    }

    Write-Host "Running Tree-sitter C logic analysis..." -ForegroundColor Cyan
    if ($Python -eq 'py -3') {
        & py -3 @cmd
    } else {
        & $Python @cmd
    }
    exit $LASTEXITCODE
}

if ($Mode -eq 'complexity') {
    if (-not $Target) {
        if ($Repo) {
            $Target = $Repo
        } else {
            throw 'For complexity mode, provide -Target or -Repo.'
        }
    }

    $cmd = @($ComplexityTool, $Target, '--threshold', "$ComplexityThreshold")
    if ($Json) {
        $cmd += '--json'
    }

    Write-Host "Running Zephyr C complexity analysis..." -ForegroundColor Cyan
    Invoke-Expression ($Python + ' ' + (($cmd | ForEach-Object {
        if ($_ -match '\s') { '"' + $_ + '"' } else { $_ }
    }) -join ' '))
    exit $LASTEXITCODE
}

if ($Mode -eq 'checkpatch') {
    if (-not $Repo -and -not $Patch) {
        throw 'For checkpatch mode, provide -Repo or -Patch.'
    }

    if (-not $ZephyrBase) {
        if ($env:ZEPHYR_BASE) {
            $ZephyrBase = $env:ZEPHYR_BASE
        } elseif ($Repo -and (Test-Path (Join-Path $Repo 'scripts\checkpatch.pl'))) {
            $ZephyrBase = $Repo
        } elseif (Test-Path 'C:\github\zephyrproject\zephyr\scripts\checkpatch.pl') {
            $ZephyrBase = 'C:\github\zephyrproject\zephyr'
        }
    }

    if (-not $ZephyrBase) {
        throw 'Unable to find Zephyr base. Provide -ZephyrBase or set ZEPHYR_BASE.'
    }

    $Checkpatch = Join-Path $ZephyrBase 'scripts\checkpatch.pl'
    if (-not (Test-Path $Checkpatch)) {
        throw "checkpatch not found at $Checkpatch"
    }

    $Perl = Get-Perl
    if (-not $Perl) {
        throw 'Perl is required for checkpatch and was not found in PATH or known install locations.'
    }

    if ($Repo -and -not $Patch) {
        $tmpPatch = Join-Path $env:TEMP 'zephyr_checkpatch.diff'
        $gitArgs = @('-C', $Repo, 'diff', '--no-ext-diff')
        if ($DiffRef) {
            $gitArgs += $DiffRef
        }
        & git @gitArgs | Out-File -FilePath $tmpPatch -Encoding ascii
        $Patch = $tmpPatch
    }

    Write-Host "Running Zephyr checkpatch..." -ForegroundColor Cyan
    & $Perl $Checkpatch --no-tree --show-types --terse $Patch
    exit $LASTEXITCODE
}

if ($Mode -eq 'patch') {
    if (-not $Repo -and -not $Patch) {
        throw 'For patch mode, provide -Repo or -Patch.'
    }
    if ($Repo -and $Patch) {
        throw 'Use either -Repo or -Patch, not both.'
    }

    $cmd = @($PatchTool, '--rules', $Rules)
    if ($Repo) {
        $cmd += @('--repo', $Repo)
        if ($DiffRef) {
            $cmd += @('--diff-ref', $DiffRef)
        }
    } else {
        $cmd += @('--patch', $Patch)
    }
    if ($Json) {
        $cmd += '--json'
    }

    Write-Host "Running Zephyr patch analysis..." -ForegroundColor Cyan
    Invoke-Expression ($Python + ' ' + (($cmd | ForEach-Object {
        if ($_ -match '\s') { '"' + $_ + '"' } else { $_ }
    }) -join ' '))
    exit $LASTEXITCODE
}

if (-not $Repo) {
    throw 'For scan mode, provide -Repo.'
}

$cmd = @($ScanTool, $Repo, '--rules', $Rules, '--max-hits', "$MaxHits")
if ($Json) {
    $cmd += '--json'
}

Write-Host "Running Zephyr code scan..." -ForegroundColor Cyan
Invoke-Expression ($Python + ' ' + (($cmd | ForEach-Object {
    if ($_ -match '\s') { '"' + $_ + '"' } else { $_ }
}) -join ' '))
exit $LASTEXITCODE
