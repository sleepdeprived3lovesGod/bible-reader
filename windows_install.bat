@echo off
setlocal enabledelayedexpansion

:: Store the current directory
set "INSTALL_DIR=%~dp0"
echo Installing in: %INSTALL_DIR%

:: Define the path to Python 3.11.9
set "PYTHON311_PATH=C:\Program Files\Python311\python.exe"

:: Check if Python 3.11.9 is installed
if exist "%PYTHON311_PATH%" (
    set "PYTHON_EXEC=%PYTHON311_PATH%"
    echo Using Python 3.11.9 from %PYTHON311_PATH%
) else (
    echo Python 3.11.9 not found at %PYTHON311_PATH%. Trying to use the default Python installation...
    :: Check for python.exe or py.exe in the system PATH
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXEC=python"
        echo Using default Python from PATH
    ) else (
        where py >nul 2>&1
        if %errorlevel% equ 0 (
            set "PYTHON_EXEC=py"
            echo Using default Python from PATH
        ) else (
            echo ERROR: No Python installation found. Please install Python from https://www.python.org/
            pause
            exit /b 1
        )
    )
)

:: Create virtual environment with the detected Python
echo Creating virtual environment in: %INSTALL_DIR%venv
"%PYTHON_EXEC%" -m venv "%INSTALL_DIR%venv"
if not exist "%INSTALL_DIR%venv\Scripts" (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

:: Check for python.exe or py.exe in the virtual environment scripts directory
if exist "%INSTALL_DIR%venv\Scripts\python.exe" (
    set "PYTHON_EXEC=python"
) else if exist "%INSTALL_DIR%venv\Scripts\py.exe" (
    set "PYTHON_EXEC=py"
) else (
    echo ERROR: Neither python.exe nor py.exe found in the virtual environment scripts directory.
    pause
    exit /b 1
)

:: Activate virtual environment and install dependencies
echo Activating virtual environment...
call "%INSTALL_DIR%venv\Scripts\activate"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Upgrading pip...
%PYTHON_EXEC% -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip.
    pause
    exit /b 1
)

:: Install build tools and dependencies
echo Installing build tools and dependencies...
pip install wheel setuptools
if errorlevel 1 (
    echo ERROR: Failed to install build tools.
    pause
    exit /b 1
)

:: Install PortAudio
echo Installing PortAudio...
:: Download PortAudio binaries
powershell -Command "Invoke-WebRequest -Uri 'http://files.portaudio.com/archives/pa_stable_v190700_20210406.tgz' -OutFile 'pa_stable_v190700_20210406.tgz'"
if errorlevel 1 (
    echo ERROR: Failed to download PortAudio.
    pause
    exit /b 1
)

:: Extract PortAudio
echo Extracting PortAudio...
tar -xzf pa_stable_v190700_20210406.tgz
if errorlevel 1 (
    echo ERROR: Failed to extract PortAudio.
    pause
    exit /b 1
)

:: Set environment variables for PortAudio
set "PORTAUDIO_DIR=%INSTALL_DIR%portaudio"
set "PATH=%PATH%;%PORTAUDIO_DIR%\bin"

:: Install pyaudio using pip
echo Installing pyaudio using pip...
pip install pyaudio
if errorlevel 1 (
    echo ERROR: Failed to install pyaudio.
    pause
    exit /b 1
)

:: Install other dependencies
echo Installing other dependencies...
pip install pandas edge-tts pydub pyperclip
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

:: Create start.bat with relative paths
echo Creating start.bat...
(
echo @echo off
echo call "venv\Scripts\activate"
echo %PYTHON_EXEC% "Bible.py"
echo pause
) > "%INSTALL_DIR%start.bat"

echo.
echo Installation Summary:
echo -------------------
echo Virtual Environment: %INSTALL_DIR%venv
echo Start Script: %INSTALL_DIR%start.bat
echo.
echo Setup complete! You can now run the Bible Reader using the start.bat file.
echo.
pause
