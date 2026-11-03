@echo off
REM Starts the ttspiper service on port 9150 (syncs .venv with uv on each run). The first start downloads 63 MB.
REM LABEL: TTSPiper Service
REM DESCRIPTION: Shared HTTP service that runs Piper text to speech on the CPU for every project.

cd /d "%~dp0"

python -m uv sync
if errorlevel 1 (
    echo uv sync failed. Install uv: python -m pip install uv
    pause
    exit /b 1
)
call .venv\Scripts\activate

python src/app.py
pause
