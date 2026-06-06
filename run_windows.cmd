@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo First run detected. Running setup_windows.cmd...
    call setup_windows.cmd
    if errorlevel 1 (
        echo Setup failed.
        pause
        exit /b 1
    )
)

set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"

dotnet run --project PresentationFeedbackProject\PresentationFeedbackProject.csproj
if errorlevel 1 (
    echo.
    echo App failed to start. Run setup_windows.cmd and try again.
    pause
    exit /b 1
)
