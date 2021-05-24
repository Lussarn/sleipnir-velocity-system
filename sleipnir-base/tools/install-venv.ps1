
Write-Output "Installing virtual invironment"

if (-Not (Get-Location).Path.EndsWith("sleipnir-base")) {
    Write-Output("Please cd to sleipnir-base directory and rerun..")
    exit 1
}

Write-Output "Checking for existing 'venv' directory"
if (Test-Path -Path .\venv) {
    Write-Output "WARNING: 'venv' already exists, exiting..."
    exit 0
}

Write-Output "Creating virtual environment..."
python3 -m venv .\venv
.\venv\Scripts\Activate.ps1

pip install pyside2
pip install opencv-python
pip install pywin32
pip install pyyaml
pip install pygame