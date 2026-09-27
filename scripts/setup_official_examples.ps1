<# Download the official pyadi-iio main branch and copy its CN0565 examples. #>

$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
$downloadDirectory = Join-Path $workspace 'work\upstream-download'
$archivePath = Join-Path $downloadDirectory 'pyadi-iio-main.zip'
$extractDirectory = Join-Path $downloadDirectory 'extracted'
$sourceDirectory = Join-Path $extractDirectory 'pyadi-iio-main\examples\cn0565'
$destinationDirectory = Join-Path $workspace 'examples\cn0565'
$archiveUrl = 'https://github.com/analogdevicesinc/pyadi-iio/archive/refs/heads/main.zip'

New-Item -ItemType Directory -Force -Path $downloadDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $extractDirectory | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $destinationDirectory) | Out-Null

Write-Host 'Downloading official pyadi-iio examples...'
Invoke-WebRequest -Uri $archiveUrl -OutFile $archivePath
Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDirectory -Force

if (-not (Test-Path $sourceDirectory)) {
    throw "CN0565 example directory was not found in the downloaded archive: $sourceDirectory"
}

Copy-Item -Path $sourceDirectory -Destination (Split-Path $destinationDirectory) -Recurse -Force
Write-Host "CN0565 examples ready: $destinationDirectory"
Get-ChildItem $destinationDirectory -File | Select-Object Name
