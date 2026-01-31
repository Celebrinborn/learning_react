#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launches both the backend and frontend development servers in VSCode terminals.

.DESCRIPTION
    This script triggers the VSCode compound task that starts both the FastAPI backend
    and the React frontend development servers in separate terminals.

.EXAMPLE
    .\run_all.ps1
#>

Write-Host "Launching Backend and Frontend Development Servers..." -ForegroundColor Cyan
Write-Host ""
Write-Host "This will open two terminals:" -ForegroundColor Yellow
Write-Host "  1. Backend  - FastAPI server (http://127.0.0.1:8000)" -ForegroundColor Green
Write-Host "  2. Frontend - Vite dev server (http://localhost:5173)" -ForegroundColor Green
Write-Host ""
Write-Host "To run manually in VSCode:" -ForegroundColor Yellow
Write-Host "  Press Ctrl+Shift+P -> 'Tasks: Run Task' -> 'Run All (Backend + Frontend)'" -ForegroundColor Gray
Write-Host ""

# Try to use VSCode CLI to run the task
if (Get-Command code -ErrorAction SilentlyContinue) {
    Write-Host "Starting via VSCode CLI..." -ForegroundColor Cyan
    code --command "workbench.action.tasks.runTask" "Run All (Backend + Frontend)"
} else {
    Write-Host "VSCode CLI not found. Opening terminals manually..." -ForegroundColor Yellow
    Write-Host ""
    
    # Get the workspace directory
    $WorkspaceDir = $PSScriptRoot
    
    # Start backend in a new PowerShell window
    Write-Host "Starting Backend..." -ForegroundColor Green
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceDir\src\backend'; .\env\Scripts\Activate.ps1; python run_server.py"
    
    # Wait a moment before starting frontend
    Start-Sleep -Seconds 2
    
    # Start frontend in a new PowerShell window
    Write-Host "Starting Frontend..." -ForegroundColor Green
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceDir\src\frontend'; npm run dev"
    
    Write-Host ""
    Write-Host "Servers started in separate windows!" -ForegroundColor Cyan
}
