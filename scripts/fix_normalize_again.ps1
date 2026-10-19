# fix_normalize_again.ps1 — Replace aggressive prefix-removal with a precise blocklist
$ErrorActionPreference = "Stop"

$file = "scripts\build_products.py"
if (-not (Test-Path $file)) { Write-Host "ERROR: file not found" -ForegroundColor Red; exit 1 }

Copy-Item $file "$file.bak3" -Force
Write-Host "Backup: $file.bak3" -ForegroundColor Gray

$content = [System.IO.File]::ReadAllText((Resolve-Path $file))
$contentN = $content -replace "`r`n", "`n"

$old = @"
def normalize_commands(commands: list[str]) -> list[str]:
    `"`"`"Remove commands that are strict prefixes of longer commands (e.g. AT+CN vs AT+CNUM).`"`"`"
    result: list[str] = []
    sorted_cmds = sorted(commands, key=len, reverse=True)
    for cmd in sorted_cmds:
        if any(cmd != other and other.startswith(cmd) for other in sorted_cmds):
            continue
        result.append(cmd)
    return sorted(result)
"@ -replace "`r`n", "`n"

$new = @"
KNOWN_FAKE_COMMANDS = {"AT+CN", "AT+FTPMOD", "AT+CMMSSENDCF"}


def normalize_commands(commands: list[str]) -> list[str]:
    `"`"`"Remove known artifact commands (regex captures of sub-strings inside the manual).`"`"`"
    return sorted(cmd for cmd in commands if cmd not in KNOWN_FAKE_COMMANDS)
"@ -replace "`r`n", "`n"

if (-not $contentN.Contains($old)) {
    Write-Host "ERROR: old normalize_commands block not found verbatim." -ForegroundColor Red
    Write-Host "Check $file and replace the function manually if needed." -ForegroundColor Yellow
    exit 1
}

$contentN = $contentN.Replace($old, $new)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText((Resolve-Path $file), $contentN, $utf8NoBom)

Write-Host "`n=== Verification ===" -ForegroundColor Cyan
$v = [System.IO.File]::ReadAllText((Resolve-Path $file))
$checks = [ordered]@{
    "KNOWN_FAKE_COMMANDS defined"       = $v.Contains("KNOWN_FAKE_COMMANDS")
    "normalize uses blocklist (not prefix scan)" = $v.Contains("if cmd not in KNOWN_FAKE_COMMANDS")
    "No more prefix scan loop"          = -not $v.Contains("for cmd in sorted_cmds:")
    "pdf_text UTF-8 (unchanged)"        = $v.Contains('encoding="utf-8"')
    "merge loop (unchanged)"            = $v.Contains("merged_rows")
}
foreach ($k in $checks.Keys) {
    if ($checks[$k]) { Write-Host "  [OK]   $k" -ForegroundColor Green }
    else { Write-Host "  [FAIL] $k" -ForegroundColor Red }
}