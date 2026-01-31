#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Activates the virtual environment and starts the FastAPI development server.

.DESCRIPTION
    This script activates the Python virtual environment located in the env folder
    and runs the FastAPI server using uvicorn with hot-reload enabled.

.EXAMPLE
    .\run_server.ps1
#>

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Navigate to the backend directory
Push-Location $ScriptDir

try {
    # Activate the virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & ".\env\Scripts\Activate.ps1"
    
    # Run the server
    Write-Host "Starting FastAPI server..." -ForegroundColor Green
    python run_server.py
}
finally {
    # Return to the original directory
    Pop-Location
}
