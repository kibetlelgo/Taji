@echo off
REM Sync changes from root folders to taji/ folder
REM Run this script before committing to ensure Render gets your changes

echo 🔄 Syncing files to taji/ folder...

REM Sync CSS files
if exist "static\css" (
    echo 📝 Syncing CSS files...
    xcopy /Y /E /I static\css\* taji\static\css\
)

REM Sync templates
if exist "templates" (
    echo 📝 Syncing templates...
    xcopy /Y /E /I templates\* taji\templates\
)

REM Sync core app
if exist "core" (
    echo 📝 Syncing core app...
    xcopy /Y /E /I core\* taji\core\
)

REM Sync loans app
if exist "loans" (
    echo 📝 Syncing loans app...
    xcopy /Y /E /I loans\* taji\loans\
)

echo.
echo ✅ Sync complete! Now you can commit and push.
echo.
echo Next steps:
echo   git add taji/
echo   git commit -m "Your commit message"
echo   git push origin main
echo.
pause
