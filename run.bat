@echo off
REM Service Status Monitor - Windows Startup Script
REM This script sets up the environment and starts the Flask application

echo Service Status Monitor - Startup Script
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if configuration file exists
if not exist "config\services.json" (
    echo Error: Configuration file config\services.json not found
    echo Please create the configuration file before starting the application.
    pause
    exit /b 1
)

REM Set environment variables if not already set
if not defined FLASK_APP set FLASK_APP=app.py
if not defined FLASK_ENV set FLASK_ENV=production
if not defined FLASK_HOST set FLASK_HOST=127.0.0.1
if not defined FLASK_PORT set FLASK_PORT=5000
if not defined FLASK_DEBUG set FLASK_DEBUG=False

echo Starting Service Status Monitor...
echo Host: %FLASK_HOST%
echo Port: %FLASK_PORT%
echo Debug: %FLASK_DEBUG%
echo.
echo Press Ctrl+C to stop the application
echo.

REM Start the application
python app.py

pause