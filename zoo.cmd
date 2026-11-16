@echo off
rem Zoo Ops for Windows. Double-click it, or run it from a terminal:
rem   zoo.cmd               choose a mode, then play
rem   zoo.cmd play hard     play a mode directly: classic, hard or hardpp
rem   zoo.cmd test 3        run the tests of level 3
rem   zoo.cmd --help        every command
setlocal
set "ZOO_ARGS=%*"
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "VENV_PY=.venv\Scripts\python.exe"

if exist "%VENV_PY%" goto install
call :find_python
if errorlevel 1 goto no_python
echo Setting up Zoo Ops (first run only)...
%PYTHON% -m venv .venv
if errorlevel 1 goto failed

:install
rem Install on the first run, and again whenever pyproject.toml changes (after a git pull).
"%VENV_PY%" -c "import os, sys; s = '.venv/.zoo-installed'; sys.exit(0 if os.path.exists(s) and os.path.getmtime(s) >= os.path.getmtime('pyproject.toml') else 1)"
if not errorlevel 1 goto run
echo Installing the game's dependencies (about a minute)...
"%VENV_PY%" -m pip install --upgrade pip > ".venv\install.log" 2>&1
"%VENV_PY%" -m pip install --editable . >> ".venv\install.log" 2>&1
if errorlevel 1 (
  type ".venv\install.log"
  goto failed
)
type nul > ".venv\.zoo-installed"

:run
"%VENV_PY%" -m zoo %*
set "CODE=%ERRORLEVEL%"
if not "%CODE%"=="0" call :keep_open
exit /b %CODE%

:find_python
for %%P in ("py -3.13" "py -3.12" "py -3.11" "python") do (
  %%~P -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1 && (
    set "PYTHON=%%~P"
    exit /b 0
  )
)
exit /b 1

:no_python
echo Zoo Ops needs Python 3.11 or newer: https://www.python.org/downloads/
echo Tick "Add python.exe to PATH" during the install, then run zoo.cmd again.
echo Or play without Python: docker compose up
call :keep_open
exit /b 1

:failed
echo The setup failed (log above, also in .venv\install.log).
echo Delete the .venv folder and run zoo.cmd again.
call :keep_open
exit /b 1

:keep_open
rem Started with a double-click (no arguments): keep the window open to read the message.
if not defined ZOO_ARGS pause
exit /b 0
