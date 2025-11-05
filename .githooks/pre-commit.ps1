$ErrorActionPreference = "Stop"
Write-Host "[pre-commit] Refreshing context…"

# Prefer 'py' launcher; fallback to 'python'
function Run-Python($args) {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    & py $args
  } elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $args
  } else {
    Write-Host "[pre-commit] Python not found on PATH. Skipping refresh."
    return $false
  }
  return $true
}

# Run cx_refresh.py if present (non-blocking on failure)
if (Test-Path "scripts\cx_refresh.py") {
  try { Run-Python "scripts\cx_refresh.py" | Out-Null }
  catch { Write-Host "[pre-commit] cx_refresh.py error (continuing): $($_.Exception.Message)" }
} else {
  Write-Host "[pre-commit] scripts\cx_refresh.py not found, skipping."
}

# Auto-stage context updates (ignore errors if paths missing)
git add context\00_MASTER_CONTEXT.md 2>$null
git add context\02_MODULE_SUMMARIES 2>$null
git add context\07_SESSIONS 2>$null

Write-Host "[pre-commit] Done."
exit 0
