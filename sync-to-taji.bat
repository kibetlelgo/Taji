@echo off
REM Sync changes from root folders to taji/ folder
REM Run this script before committing to ensure Render gets your changes

echo.
echo ========================================
echo   TAJI DEPLOYMENT SYNC SCRIPT
echo ========================================
echo.

REM Sync CSS files
if exist "static\css" (
    echo [1/4] Syncing CSS files...
    xcopy /Y /Q static\css\*.css taji\static\css\ >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo       ✓ CSS files synced
    ) else (
        echo       ✗ CSS sync failed
    )
)

REM Sync templates
if exist "templates" (
    echo [2/4] Syncing templates...
    xcopy /Y /E /Q /I templates\* taji\templates\ >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo       ✓ Templates synced
    ) else (
        echo       ✗ Templates sync failed
    )
)

REM Sync core app
if exist "core" (
    echo [3/4] Syncing core app...
    xcopy /Y /Q core\*.py taji\core\ >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo       ✓ Core app synced
    ) else (
        echo       ✗ Core sync failed
    )
)

REM Sync loans app
if exist "loans" (
    echo [4/4] Syncing loans app...
    xcopy /Y /Q loans\*.py taji\loans\ >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo       ✓ Loans app synced
    ) else (
        echo       ✗ Loans sync failed
    )
)

echo.
echo ========================================
echo   ✅ SYNC COMPLETE!
echo ========================================
echo.
echo Next steps to deploy:
echo   1. git add taji/
echo   2. git commit -m "Your commit message"
echo   3. git push origin main
echo   4. Wait 2-3 minutes for Render to deploy
echo   5. Clear browser cache on your phone
echo.
pause
