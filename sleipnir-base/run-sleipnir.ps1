Write-Output "Running sleipnir"
Write-Output "Checking for virtual environment..."
if (-Not (Test-Path -Path .\venv)) {
    Write-Output "ERROR: no 'venv' exists, please run tools\install-venv.ps1"
    exit 0
}

python .\src\sleipnir.py