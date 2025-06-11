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

# Path to the venv python
$venvPython = Join-Path $scriptDir 'activate\Scripts\python.exe'

if (-Not (Test-Path $venvPython)) {
    Write-Error "Python venv not found at $venvPython. Please set up the virtual environment."
    exit 1
}

# Build the command
$modulePath = Join-Path $scriptDir $Module
$allArgs = @($modulePath) + $Args

# Activate .env if present (python-dotenv will handle this if imported in code)

# Run the module
& $venvPython @allArgs
