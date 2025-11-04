@echo off
REM Windows Batch Script to Start Django Server
REM Double-click this file to start the news website

echo ==========================================================
echo    DJANGO NEWS APPLICATION - STARTING SERVER
echo ==========================================================
echo.

REM Check if database exists
if not exist "db.sqlite3" (
    echo WARNING: Database not found!
    echo Please run setup-windows.bat first
    echo.
    pause
    exit /b 1
)

echo Starting Django development server...
echo.
echo The website will be available at:
echo   http://127.0.0.1:8000/
echo.
echo Press Ctrl+C to stop the server
echo ==========================================================
echo.

REM Start the server
python manage.py runserver

echo.
echo Server stopped.
pause