@echo off
rem Double-click to update the library: finds Apple TV links, gets new covers, rebuilds data.js and checks it.
cd /d "%~dp0"
python update_library.py %*
if errorlevel 9009 (
  echo Python was not found. Install it from python.org and tick "Add python.exe to PATH".
  pause
)
