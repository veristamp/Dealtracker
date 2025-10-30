@echo off
setlocal

echo ========================================
echo      DealTracker Fast Setup (powered by uv)
echo ========================================

:: Define the name of the virtual environment
set VENV_DIR=dealtracker-venv

:: Step 1: Check for Python
echo.
echo [*] Step 1 of 4: Checking for Python 3.8+...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 'python' command not found! Please ensure Python is installed and in your PATH.
    pause
    exit /b 1
)
echo     ...Python found.

:: Step 2: Check for uv.exe
echo.
echo [*] Step 2 of 4: Checking for uv installer...
if not exist "uv.exe" (
    echo [ERROR] uv.exe not found in this directory!
    pause
    exit /b 1
)
echo     ...uv found.

:: Step 3: Create venv and install dependencies
echo.
echo [*] Step 3 of 4: Creating environment and installing dependencies...
rem 
call .\uv.exe venv %VENV_DIR% -p python
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)

rem
call .\uv.exe pip install -r requirements.txt --python .\%VENV_DIR%\Scripts\python.exe
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies from requirements.txt!
    pause
    exit /b 1
)
echo     ...Dependencies installed successfully.

:: Step 4: Run crawl4ai setup
echo.
echo [*] Step 4 of 4: Setting up browser engine with Crawl4AI...
rem 
call %VENV_DIR%\Scripts\activate.bat
call crawl4ai-setup
if %errorlevel% neq 0 (
    echo [WARN] crawl4ai-setup failed, but continuing...
)
call crawl4ai-doctor
if %errorlevel% neq 0 (
    echo [WARN] crawl4ai-doctor failed, but continuing...
)
call deactivate
echo     ...Browser engine setup complete.

:: Create the activation flag file
echo ok > activated.txt

echo.
echo ========================================
echo [SUCCESS] Setup is complete.
echo You can now run the application using Dealtracker.exe
echo ========================================
echo.
pause
