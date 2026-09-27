@echo off
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 goto usepy

where python >nul 2>nul
if %errorlevel%==0 goto usepython

where python3 >nul 2>nul
if %errorlevel%==0 goto usepython3

echo Python not found.
echo Please install from https://www.python.org/downloads/
goto end

:usepy
py python\convert.py
goto end

:usepython
python python\convert.py
goto end

:usepython3
python3 python\convert.py
goto end

:end
echo.
echo Done. Press any key to close.
pause >nul