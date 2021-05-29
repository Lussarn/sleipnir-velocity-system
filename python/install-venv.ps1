
Write-Output "Installing virtual invironment"

if (-Not (Get-Location).Path.EndsWith("python")) {
    Write-Output("Please cd to python directory and rerun..")
    exit 1
}

Write-Output "Checking for existing 'venv' directory"
if (Test-Path -Path .\venv) {
    Write-Output "WARNING: 'venv' already exists, exiting..."
    exit 0
}

Write-Output "Creating virtual environment..."
python -m venv .\venv
.\venv\Scripts\Activate.ps1

pip install pyside2
pip install pygame
pip install opencv-python
pip install pywin32
pip install pyyaml
pip install pysqlite3
pip install simplejpeg

# ADitional libs for fake-camera
pip install requests
