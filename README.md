# Presentation Feedback Project

WPF presentation feedback app connected to a Python video/audio analysis pipeline.

## Windows Quick Start

1. Clone or download this repository.
2. Double-click `setup_windows.cmd`.
3. Double-click `run_windows.cmd`.

The setup script creates `.venv`, installs Python packages from `requirements.txt`, checks `ffmpeg`, and checks the .NET SDK.

## Required Runtime

- Windows
- Python 3.11 or 3.12
- .NET 8 SDK
- ffmpeg

## Manual Commands

```cmd
cd PresentationFeedbackProject
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
dotnet run --project PresentationFeedbackProject\PresentationFeedbackProject.csproj
```

The WPF app automatically uses `.venv\Scripts\python.exe` when it exists.
