@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

set "PROJECT_DIR=%CD%"
set "LOG_FILE=%PROJECT_DIR%\setup.log"
set "ENV_FILE=%PROJECT_DIR%\.env"
set "ENV_TEMPLATE=%PROJECT_DIR%\.env.example"
set "MAIN_FILE=%PROJECT_DIR%\main.py"
set "REQUIREMENTS_FILE=%PROJECT_DIR%\requirements.txt"
set "VENV_PYTHON=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "RESTART_DELAY=5"
set "PYTHON_CMD="

break > "%LOG_FILE%"

echo ========================================
echo Finance Telegram Bot Setup and Run
echo Project: %PROJECT_DIR%
echo Log file: %LOG_FILE%
echo ========================================
>> "%LOG_FILE%" echo ========================================
>> "%LOG_FILE%" echo Finance Telegram Bot Setup and Run
>> "%LOG_FILE%" echo Project: %PROJECT_DIR%
>> "%LOG_FILE%" echo Log file: %LOG_FILE%
>> "%LOG_FILE%" echo ========================================

if not exist "%MAIN_FILE%" (
    echo [ERROR] main.py not found.
    >> "%LOG_FILE%" echo [ERROR] main.py not found.
    pause
    exit /b 1
)

if not exist "%REQUIREMENTS_FILE%" (
    echo [ERROR] requirements.txt not found.
    >> "%LOG_FILE%" echo [ERROR] requirements.txt not found.
    pause
    exit /b 1
)

if not exist "%ENV_FILE%" (
    if exist "%ENV_TEMPLATE%" (
        echo [INFO] Creating .env from .env.example...
        >> "%LOG_FILE%" echo [INFO] Creating .env from .env.example...
        copy /Y "%ENV_TEMPLATE%" "%ENV_FILE%" >nul
    ) else (
        echo [WARN] .env.example not found. Creating default .env...
        >> "%LOG_FILE%" echo [WARN] .env.example not found. Creating default .env...
        (
            echo BOT_TOKEN=paste_your_bot_token_here
            echo DATABASE_PATH=bot.db
            echo ALERT_CHECK_INTERVAL=60
        ) > "%ENV_FILE%"
    )
)

where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    if exist "%LocalAppData%\Programs\Python\Launcher\py.exe" (
        set "PYTHON_CMD=%LocalAppData%\Programs\Python\Launcher\py.exe"
    )
)

if not defined PYTHON_CMD (
    echo [WARN] Python not found. Trying to install Python automatically...
    >> "%LOG_FILE%" echo [WARN] Python not found. Trying to install Python automatically...

    where winget >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python not found and winget is unavailable.
        echo Install Python 3.11+ manually, then rerun this file.
        >> "%LOG_FILE%" echo [ERROR] Python not found and winget is unavailable.
        >> "%LOG_FILE%" echo Install Python 3.11+ manually, then rerun this file.
        pause
        exit /b 1
    )

    echo [INFO] Running winget install for Python 3.12...
    >> "%LOG_FILE%" echo [INFO] Running winget install for Python 3.12...
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] Automatic Python installation failed.
        >> "%LOG_FILE%" echo [ERROR] Automatic Python installation failed.
        pause
        exit /b 1
    )

    where py >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py"

    if not defined PYTHON_CMD (
        where python >nul 2>nul
        if not errorlevel 1 set "PYTHON_CMD=python"
    )

    if not defined PYTHON_CMD (
        if exist "%LocalAppData%\Programs\Python\Launcher\py.exe" (
            set "PYTHON_CMD=%LocalAppData%\Programs\Python\Launcher\py.exe"
        )
    )

    if not defined PYTHON_CMD (
        echo [ERROR] Python still not found after installation attempt.
        >> "%LOG_FILE%" echo [ERROR] Python still not found after installation attempt.
        pause
        exit /b 1
    )
)

echo [INFO] Using Python command: %PYTHON_CMD%
>> "%LOG_FILE%" echo [INFO] Using Python command: %PYTHON_CMD%

if not exist "%VENV_PYTHON%" (
    echo [INFO] Creating virtual environment...
    >> "%LOG_FILE%" echo [INFO] Creating virtual environment...
    call "%PYTHON_CMD%" -m venv ".venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        >> "%LOG_FILE%" echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment Python was not created.
    >> "%LOG_FILE%" echo [ERROR] Virtual environment Python was not created.
    pause
    exit /b 1
)

echo [INFO] Upgrading pip...
>> "%LOG_FILE%" echo [INFO] Upgrading pip...
call "%VENV_PYTHON%" -m ensurepip --upgrade
if errorlevel 1 (
    echo [ERROR] Failed to initialize pip.
    >> "%LOG_FILE%" echo [ERROR] Failed to initialize pip.
    pause
    exit /b 1
)

call "%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip/setuptools/wheel.
    >> "%LOG_FILE%" echo [ERROR] Failed to upgrade pip/setuptools/wheel.
    pause
    exit /b 1
)

echo [INFO] Installing dependencies...
>> "%LOG_FILE%" echo [INFO] Installing dependencies...
call "%VENV_PYTHON%" -m pip install -r "%REQUIREMENTS_FILE%"
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    >> "%LOG_FILE%" echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [INFO] Checking BOT_TOKEN in .env...
>> "%LOG_FILE%" echo [INFO] Checking BOT_TOKEN in .env...

findstr /b /c:"BOT_TOKEN=" "%ENV_FILE%" >nul
if errorlevel 1 (
    echo [ERROR] BOT_TOKEN is missing in .env.
    >> "%LOG_FILE%" echo [ERROR] BOT_TOKEN is missing in .env.
    start "" notepad "%ENV_FILE%"
    pause
    exit /b 1
)

findstr /b /c:"BOT_TOKEN=paste_your_bot_token_here" "%ENV_FILE%" >nul
if not errorlevel 1 (
    echo [ERROR] Replace BOT_TOKEN in .env before launch.
    >> "%LOG_FILE%" echo [ERROR] Replace BOT_TOKEN in .env before launch.
    start "" notepad "%ENV_FILE%"
    pause
    exit /b 1
)

findstr /r /b /c:"BOT_TOKEN=$" "%ENV_FILE%" >nul
if not errorlevel 1 (
    echo [ERROR] BOT_TOKEN is empty in .env.
    >> "%LOG_FILE%" echo [ERROR] BOT_TOKEN is empty in .env.
    start "" notepad "%ENV_FILE%"
    pause
    exit /b 1
)

echo [INFO] Starting bot...
echo [INFO] Press Ctrl+C to stop.
>> "%LOG_FILE%" echo [INFO] Starting bot...
>> "%LOG_FILE%" echo [INFO] Press Ctrl+C to stop.

:run_bot
call "%VENV_PYTHON%" "%PROJECT_DIR%\main.py"
set "BOT_EXIT_CODE=%errorlevel%"

if "%BOT_EXIT_CODE%"=="0" (
    echo [INFO] Bot process finished normally.
    >> "%LOG_FILE%" echo [INFO] Bot process finished normally.
    pause
    exit /b 0
)

echo [WARN] Bot stopped with exit code %BOT_EXIT_CODE%.
>> "%LOG_FILE%" echo [WARN] Bot stopped with exit code %BOT_EXIT_CODE%.
choice /C YN /N /M "Restart bot automatically? [Y/N]: "
if errorlevel 2 (
    echo [INFO] Restart canceled by user.
    >> "%LOG_FILE%" echo [INFO] Restart canceled by user.
    pause
    exit /b %BOT_EXIT_CODE%
)

echo [INFO] Restarting in %RESTART_DELAY% seconds...
>> "%LOG_FILE%" echo [INFO] Restarting in %RESTART_DELAY% seconds...
timeout /t %RESTART_DELAY% /nobreak >nul
goto run_bot
