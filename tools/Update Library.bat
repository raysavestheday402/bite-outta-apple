@echo off
rem Double-click to update the library. It first gets the latest version of the site and these tools
rem from GitHub, then finds Apple TV links, gets new covers, rebuilds data.js and checks it.
rem Everything is inside one ( ) block, so this file can safely update itself while it runs.
setlocal EnableDelayedExpansion
cd /d "%~dp0"
(
  set "GIT="
  where git >nul 2>nul && set "GIT=git"
  if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set "GIT=%%D\resources\app\git\cmd\git.exe"
  if defined GIT (
    echo Getting the latest version from GitHub...
    "!GIT!" -C .. pull --ff-only
    if errorlevel 1 (
      echo.
      echo Couldn't get the latest version. In GitHub Desktop click "Fetch origin", then "Pull origin", and run this again.
      pause
      exit /b 1
    )
  ) else (
    echo Git wasn't found, so this can't get the latest version itself. Pull in GitHub Desktop first.
  )
  echo.
  python update_library.py %*
  if errorlevel 9009 (
    echo Python was not found. Install it from python.org and tick "Add python.exe to PATH".
    pause
  )
  exit /b
)
