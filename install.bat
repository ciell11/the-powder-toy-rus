@echo off
chcp 65001 >nul
echo ========================================================
echo   The Powder Toy - Установщик русификатора (Late Alpha)
echo ========================================================
echo.
py "%~dp0patch_powder.py"
if %errorlevel% neq 0 (
    python "%~dp0patch_powder.py"
)
echo.
pause
