# ruun_bot.ps1
# Usage: .\ruun_bot.ps1 <module> [args]
# Example: .\ruun_bot.ps1 cli.py run_reminders

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Module,
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "[ruun_bot] Script directory: $scriptDir"

# Path to the venv python
$venvDir = Join-Path $scriptDir '.\.venv\Scripts\'
Write-Host "[ruun_bot] venv dir: $venvDir"

# Activate the virtual environment
if (-Not (Test-Path $venvDir)) {
    Write-Error "Virtual environment not found at $venvDir. Please set up the virtual environment."
    exit 1
}
$venvScript = Join-Path $venvDir 'Activate.ps1'
Write-Host "[ruun_bot] venv activation script: $venvScript"

if (-Not (Test-Path $venvScript)) {
    Write-Error "Activation script not found at $venvScript. Please set up the virtual environment."
    exit 1
}
Write-Host "[ruun_bot] Activating venv..."
. $venvScript

$venvPython = Join-Path $venvDir 'scripts\python.exe'
Write-Host "[ruun_bot] venv python: $venvPython"

if (-Not (Test-Path $venvPython)) {
    Write-Error "Python venv not found at $venvPython. Please set up the virtual environment."
    exit 1
}

# Build the command
$modulePath = Join-Path $scriptDir $Module
Write-Host "[ruun_bot] Module: $Module"
Write-Host "[ruun_bot] Args: $Args"

$allArgs = @($modulePath) + $Args

# Activate .env if present (python-dotenv will handle this if imported in code)

# Run the module
Write-Host "[ruun_bot] Running: $venvPython $allArgs"
& $venvPython @allArgs
