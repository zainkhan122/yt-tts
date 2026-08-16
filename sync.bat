@echo off
title GitHub Sync Script
cls

echo ===================================
echo   GITHUB SYNC TOOL
echo ===================================
echo [1] UPLOAD local changes to GitHub (Push)
echo [2] DOWNLOAD GitHub changes to PC (Pull)
echo [3] Exit
echo ===================================
set /p choice="Select an option (1-3): "

if "%choice%"=="1" goto PUSH
if "%choice%"=="2" goto PULL
if "%choice%"=="3" goto END

:PUSH
cls
echo Starting Upload Process...
set /p msg="Enter commit message (Press Enter for 'Auto update'): "
if "%msg%"=="" set msg=Auto update

git add .
git commit -m "%msg%"
git push origin main
echo.
echo Operation finished.
pause
goto END

:PULL
cls
echo Starting Download Process...
git pull origin main
echo.
echo Operation finished.
pause
goto END

:END
exit