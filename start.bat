@echo off
chcp 65001 >nul
echo ================================
echo   ????????
echo ================================
echo.

REM Try to find python
where python >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=python
) else (
    where py >nul 2>&1
    if %errorlevel%==0 (
        set PYTHON=py
    ) else (
        echo Python not found in PATH!
        echo Trying default install locations...
        if exist "C:\Python312\python.exe" (
            set PYTHON=C:\Python312\python.exe
        ) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
            set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
        ) else (
            echo Cannot find Python. Please install Python 3.10+
            pause
            exit /b 1
        )
    )
)

echo Using Python: %PYTHON%
echo.

REM Check if database exists
if not exist "db.sqlite3" (
    echo Initializing database...
    %PYTHON% manage.py makemigrations accounts library
    %PYTHON% manage.py migrate
    %PYTHON% manage.py init_data
    echo Database initialized!
    echo.
)

echo Starting server at http://127.0.0.1:8002/
echo Press Ctrl+C to stop.
echo.
%PYTHON% manage.py runserver 127.0.0.1:8002

pause
