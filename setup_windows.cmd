@echo off
setlocal

cd /d "%~dp0"

echo [1/5] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
    echo Python is not installed or not added to PATH.
    echo Install Python 3.11 or 3.12 from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/5] Creating virtual environment...
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [3/5] Installing Python packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install Python packages.
    pause
    exit /b 1
)

echo [4/5] Checking ffmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo ffmpeg is not installed. Trying winget install...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo winget is not available. Install ffmpeg manually and run setup again.
        echo Recommended: https://www.gyan.dev/ffmpeg/builds/
        pause
        exit /b 1
    )

    winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo ffmpeg installation failed. Install ffmpeg manually and run setup again.
        pause
        exit /b 1
    )
)

echo [5/5] Checking .NET SDK...
where dotnet >nul 2>nul
if errorlevel 1 (
    echo .NET SDK is not installed.
    echo Install .NET 8 SDK from https://dotnet.microsoft.com/download/dotnet/8.0
    pause
    exit /b 1
)

echo.
echo Setup complete.
echo Run run_windows.cmd to start the WPF app.
pause
