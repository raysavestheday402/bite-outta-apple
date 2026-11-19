@echo off
cd /d "%~dp0"
echo Taking the private notes out of the published site...
echo.
set "GIT="
where git >nul 2>nul && set "GIT=git"
if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set "GIT=%%D\resources\app\git\cmd\git.exe"
if not defined GIT (
  echo Git wasn't found. Open GitHub Desktop once, then run this again.
  pause
  exit /b 1
)
"%GIT%" -C .. rm --cached -q CLAUDE.md PROJECT-BRIEF.md
if errorlevel 1 (
  echo They were already private - nothing to change.
) else (
  echo Done. CLAUDE.md and PROJECT-BRIEF.md stay on this PC but will be
  echo removed from GitHub on your next commit.
)
echo.
echo The files are NOT deleted from your folder - you keep them.
echo.
pause
