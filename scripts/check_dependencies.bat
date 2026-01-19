@echo off
REM Check system dependencies for The Mixer (Windows)

echo Checking system dependencies for The Mixer...
echo.

set ALL_OK=1

REM Check ffmpeg
echo Checking ffmpeg...
where ffmpeg >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Found ffmpeg
    ffmpeg -version | findstr /R "ffmpeg version"
) else (
    echo   [ERROR] ffmpeg NOT FOUND
    echo   Install from: https://ffmpeg.org/download.html
    echo   Or use: choco install ffmpeg  (if you have Chocolatey)
    set ALL_OK=0
)

REM Check Python
echo.
echo Checking Python...
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Found Python
    python --version
) else (
    echo   [ERROR] Python NOT FOUND
    echo   Install from: https://www.python.org/downloads/
    set ALL_OK=0
)

REM Check pip
echo.
echo Checking pip...
where pip >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Found pip
    pip --version
) else (
    echo   [ERROR] pip NOT FOUND
    echo   Install: python -m ensurepip
    set ALL_OK=0
)

REM Note about libsndfile
echo.
echo Note: libsndfile will be installed automatically with soundfile package

REM Optional: Check for CUDA
echo.
echo Optional dependencies:
echo Checking CUDA...
where nvcc >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Found CUDA (GPU acceleration available)
    nvcc --version | findstr "release"
) else (
    echo   [WARN] CUDA not found (will use CPU - slower but functional)
)

echo.
if %ALL_OK% EQU 1 (
    echo [OK] All required dependencies are installed!
    echo.
    echo Next steps:
    echo   1. Create virtual environment: python -m venv venv
    echo   2. Activate it: venv\Scripts\activate
    echo   3. Install Python packages: pip install -r requirements.txt
) else (
    echo [ERROR] Some dependencies are missing. Please install them first.
    exit /b 1
)
