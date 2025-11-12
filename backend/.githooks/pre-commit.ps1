$ErrorActionPreference = "Stop"
Write-Host "[pre-commit] Refreshing context…"

# Prefer 'py' then 'python'
function Run-Python($args) {
  if (Get-Command py -ErrorAction SilentlyContinue)     { & py $args;     return $LASTEXITCODE }
  if (Get-Command python -ErrorAction SilentlyContinue) { & python $args; return $LASTEXITCODE }
  Write-Host "[pre-commit] Python not found on PATH. Skipping refresh."
  return 0
}

# Optional refresh step (non-blocking)
if (Test-Path "scripts\cx_refresh.py") {
  try {
    $code = Run-Python "scripts\cx_refresh.py"
    if ($code -ne 0) { Write-Host "[pre-commit] cx_refresh.py returned $code (continuing)" }
  } catch {
    Write-Host "[pre-commit] cx_refresh.py error (continuing): $($_.Exception.Message)"
  }
} else {
  Write-Host "[pre-commit] scripts\cx_refresh.py not found, skipping."
}

# Safe git add (only if the path exists)
function Safe-Add($p) {
  if (Test-Path $p) {
    & git add $p 2>$null | Out-Null
  }
}

Safe-Add "context\00_MASTER_CONTEXT.md"
Safe-Add "context\02_MODULE_SUMMARIES"
Safe-Add "context\07_SESSIONS"

Write-Host "[pre-commit] Done."
exit 0

