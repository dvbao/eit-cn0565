<#
Creates a project-local Python 3.11 environment and installs pyadi-iio from
its current main branch, then the CN0565 example dependencies. Git is not
required.

Run from this directory:
  .\bootstrap-cn0565-env.ps1
#>

$ErrorActionPreference = 'Stop'
$workspace = $PSScriptRoot
$environmentPath = Join-Path $workspace 'cn0565-env'
$requirementsPath = Join-Path $workspace 'requirements.txt'
$pyadiArchive = 'https://github.com/analogdevicesinc/pyadi-iio/archive/refs/heads/main.zip'
$python = Join-Path $environmentPath 'Scripts\python.exe'

if (-not (Test-Path $python)) {
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pythonLauncher) {
        throw 'Python Launcher (py.exe) was not found. Install Python 3.11 from python.org, select "Add python.exe to PATH", then rerun this script.'
    }

    & py -3.11 --version | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw 'Python 3.11 was not found. Install a Python 3.11 x64 release, then rerun this script.'
    }

    & py -3.11 -m venv $environmentPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $python)) {
        throw "Could not create the virtual environment: $environmentPath"
    }
}

& $python -m pip install --upgrade pip

if (-not (Test-Path $requirementsPath)) {
    throw "Requirements file was not found: $requirementsPath"
}

# The local requirements file combines the upstream root requirements with
# examples/cn0565/requirements.txt. Install pyadi-iio directly from its main
# branch archive so a system Git installation is unnecessary.
& $python -m pip install -r $requirementsPath
& $python -m pip install --upgrade $pyadiArchive

& $python --version
& $python -c "import adi, iio, numpy, pyeit; print('OK: CN0565 Python dependencies imported')"
Write-Host "Environment ready: $environmentPath"
