# fix_build_products.ps1 — Apply remaining fixes to scripts\build_products.py
$ErrorActionPreference = "Stop"

$file = "scripts\build_products.py"
if (-not (Test-Path $file)) {
    Write-Host "ERROR: $file not found. Run from project root." -ForegroundColor Red
    exit 1
}

# Backup
$backup = "$file.bak2"
Copy-Item $file $backup -Force
Write-Host "Backup saved: $backup" -ForegroundColor Gray

$content = [System.IO.File]::ReadAllText((Resolve-Path $file))
$contentN = $content -replace "`r`n", "`n"

if ($contentN.Contains("def normalize_commands")) {
    Write-Host "Already contains normalize_commands. Aborting." -ForegroundColor Yellow
    exit 0
}

# --- Fix 1: pdf_text -> UTF-8 + safe return ---
$oldPdf = "    result = subprocess.run([`"pdftotext`", `"-layout`", str(path), `"-`"], check=True, capture_output=True, text=True)`n    return result.stdout"
$newPdf = @"
    result = subprocess.run(
        [`"pdftotext`", `"-layout`", str(path), `"-`"],
        check=True,
        capture_output=True,
        text=True,
        encoding=`"utf-8`",
        errors=`"replace`",
    )
    return result.stdout or `"`"
"@ -replace "`r`n", "`n"

if ($contentN.Contains($oldPdf)) {
    $contentN = $contentN.Replace($oldPdf, $newPdf)
    Write-Host "Fix 1 applied: pdf_text now uses UTF-8" -ForegroundColor Green
} else {
    Write-Host "Fix 1: pattern not found (already fixed?)" -ForegroundColor Yellow
}

# --- Fix 2a: insert normalize_commands before commands_for ---
$oldDef = "def commands_for(version: str) -> list[str]:"
$newDef = @"
def normalize_commands(commands: list[str]) -> list[str]:
    `"`"`"Remove commands that are strict prefixes of longer commands (e.g. AT+CN vs AT+CNUM).`"`"`"
    result: list[str] = []
    sorted_cmds = sorted(commands, key=len, reverse=True)
    for cmd in sorted_cmds:
        if any(cmd != other and other.startswith(cmd) for other in sorted_cmds):
            continue
        result.append(cmd)
    return sorted(result)


def commands_for(version: str) -> list[str]:
"@ -replace "`r`n", "`n"

if ($contentN.Contains($oldDef)) {
    $contentN = $contentN.Replace($oldDef, $newDef)
    Write-Host "Fix 2a applied: normalize_commands inserted" -ForegroundColor Green
} else {
    Write-Host "Fix 2a: def commands_for not found" -ForegroundColor Red
}

# --- Fix 2b: wire it into commands_for return ---
$oldRet = "return sorted(set(COMMAND_RE.findall(text)))"
$newRet = "return normalize_commands(sorted(set(COMMAND_RE.findall(text))))"
if ($contentN.Contains($oldRet)) {
    $contentN = $contentN.Replace($oldRet, $newRet)
    Write-Host "Fix 2b applied: commands_for uses normalize_commands" -ForegroundColor Green
} else {
    Write-Host "Fix 2b: return pattern not found" -ForegroundColor Red
}

# Write back as UTF-8 without BOM, LF endings
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText((Resolve-Path $file), $contentN, $utf8NoBom)

Write-Host ""
Write-Host "=== Verification ===" -ForegroundColor Cyan
$v = [System.IO.File]::ReadAllText((Resolve-Path $file))
$checks = [ordered]@{
    "normalize_commands function exists"       = $v.Contains("def normalize_commands")
    "commands_for uses normalize_commands"     = $v.Contains("normalize_commands(sorted(set(COMMAND_RE.findall(text))))")
    "pdf_text uses encoding=`"utf-8`""         = $v.Contains('encoding="utf-8"')
    "pdf_text returns safe empty string"       = $v.Contains('return result.stdout or ""')
    "merge loop (from your previous edit)"     = $v.Contains("merged_rows")
}
$allOk = $true
foreach ($k in $checks.Keys) {
    if ($checks[$k]) { Write-Host "  [OK]   $k" -ForegroundColor Green }
    else { Write-Host "  [FAIL] $k" -ForegroundColor Red; $allOk = $false }
}

if ($allOk) {
    Write-Host "`nAll checks passed." -ForegroundColor Green
    Write-Host "`nNow run:" -ForegroundColor Cyan
    Write-Host '  .\.venv\Scripts\Activate.ps1' -ForegroundColor White
    Write-Host '  $env:Path += ";C:\poppler\Library\bin"' -ForegroundColor White
    Write-Host '  $env:PYTHONUTF8 = "1"' -ForegroundColor White
    Write-Host '  $env:DATASHEET_DIR = "C:\Users\Workshop\Downloads\New folder (3)\Finish\data\raw"' -ForegroundColor White
    Write-Host '  python scripts\build_products.py' -ForegroundColor White
} else {
    Write-Host "`nSome fixes did not apply. Check $backup and compare." -ForegroundColor Red
}