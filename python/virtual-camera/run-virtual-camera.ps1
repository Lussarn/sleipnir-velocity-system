Write-Output "Running virtual camera"
Write-Output "Checking for virtual environment..."
if (-Not (Test-Path -Path ..\venv)) {
    Write-Output "ERROR: no 'venv' exists, please run install-venv.ps1 from parent firectory"
    exit 0
}

..\venv\Scripts\activate.ps1
python .\src\virtual-camera.py $args[0]  $args[1]