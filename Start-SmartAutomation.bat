@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-smartautomation.ps1"
if errorlevel 1 (
  echo.
  echo SmartAutomation could not start. Read the message above.
  pause
)
