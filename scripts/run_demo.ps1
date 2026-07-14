# Run the data-quality observability demo
param(
    [string]$HistoryDb = "sqlite:///.dqo/history.db"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot ..

Write-Host "Running valid orders check..."
python -m src.dqo.cli run `
    --contract contracts/orders.yml `
    --data data/samples/orders.csv `
    --references data/samples `
    --history-db $HistoryDb

Write-Host ""
Write-Host "Running invalid orders check (expect failures)..."
python -m src.dqo.cli run `
    --contract contracts/orders.yml `
    --data data/samples/orders_invalid.csv `
    --references data/samples `
    --history-db $HistoryDb
if ($LASTEXITCODE -ne 0) {
    Write-Host "Invalid dataset failed checks as expected."
}

Write-Host ""
Write-Host "Recent history:"
python -m src.dqo.cli history --contract orders --history-db $HistoryDb

Write-Host ""
Write-Host "Running tests..."
python -m pytest -q

Write-Host "Demo complete. See docs/operations.md for triage procedures."
