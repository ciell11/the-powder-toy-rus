@echo off
echo ============================================================
echo   The Powder Toy - Optional Binary Patcher (Early Alpha)
echo ============================================================
echo.
py "%~dp0patch_powder.py"
if %errorlevel% neq 0 (
    python "%~dp0patch_powder.py"
)
echo.
pause
