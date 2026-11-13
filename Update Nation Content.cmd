@echo off
cd /d "%~dp0"

where node >nul 2>&1
if errorlevel 1 (
    echo Node.js was not found. Install Node.js, then double-click this file again.
    pause
    exit /b 1
)

echo Updating national technologies, starting history grants, and event journals...
node "tools\build_nation_content.cjs"
set "result=%errorlevel%"

if not "%result%"=="0" (
    echo.
    echo Update failed. See the error above.
) else (
    echo.
    echo Update complete.
)

pause
exit /b %result%
