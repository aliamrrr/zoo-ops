# Creates .venv and installs the dependencies. Run from the project root:
#   powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$candidates = @(@("py", "-3"), @("python"), @("python3"))
$python = $null
foreach ($candidate in $candidates) {
    $exe = $candidate[0]
    $prefix = @($candidate | Select-Object -Skip 1)
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
        continue
    }
    $version = & $exe @prefix -c "import sys; print('%d.%d' % sys.version_info[:2])"
    if ($LASTEXITCODE -eq 0 -and [version]$version -ge [version]"3.11") {
        $python = $candidate
        break
    }
}
if ($null -eq $python) {
    Write-Host "Python 3.11 or newer is required: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".venv")) {
    $prefix = @($python | Select-Object -Skip 1)
    & $python[0] @prefix -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet

Write-Host ""
Write-Host "Zoo Ops is ready." -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python -m zoo test"
Write-Host "  python -m zoo play"
