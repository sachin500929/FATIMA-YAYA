@echo off
echo ================================================
echo  FATIMA YOUTH FEDERATION OF YAYAMULLA
echo  Starting the app...
echo ================================================

cd /d "%~dp0"

:: Use venv pip/python directly (most reliable on Windows)
if exist ".venv\Scripts\pip.exe" (
    echo Using existing virtual environment...
    echo Installing/updating dependencies...
    .venv\Scripts\pip.exe install -r requirements.txt
    echo.
    echo ================================================
    echo  Server starting at: http://127.0.0.1:5000
    echo  Press Ctrl+C to stop.
    echo ================================================
    echo.
    .venv\Scripts\python.exe app.py
) else (
    echo No .venv found. Using system Python...
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
    echo ================================================
    echo  Server starting at: http://127.0.0.1:5000
    echo  Press Ctrl+C to stop.
    echo ================================================
    echo.
    python app.py
)
pause
