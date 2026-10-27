@echo off
rem Double-click to download certain covers again (for example when a title has the wrong cover).
rem Type the ids, like: 010a 010b 010c 010d   (an id is the number in data.js / cover_rows.json)
rem Press Enter with nothing typed to redo the four Halloweentown covers.
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "IDS="
set /p IDS=Which ids? (Enter = 010a 010b 010c 010d): 
if not defined IDS set "IDS=010a 010b 010c 010d"
echo.
python update_library.py --redo !IDS!
if errorlevel 9009 (
  echo Python was not found. Install it from python.org and tick "Add python.exe to PATH".
  pause
)
