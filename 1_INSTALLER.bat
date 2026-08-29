@echo off
chcp 65001 >nul
title Installation - Choix des options
echo.
echo ================================================
echo   Installation du bot Choix des 15 options
echo ================================================
echo.
py -m pip install -r requirements.txt
echo.
if %errorlevel% neq 0 (
  echo Une erreur est survenue pendant l'installation.
) else (
  echo Installation terminee.
)
echo.
pause
