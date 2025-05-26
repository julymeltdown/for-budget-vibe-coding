@echo off
echo ========================================
echo PyAutoGUI Dependencies Quick Fix
echo ========================================
echo.

echo Step 1: Sending error notification...
python send_error_notification.py

echo.
echo Step 2: Fixing PyAutoGUI dependencies...
python fix_pyautogui_dependencies.py

echo.
echo Step 3: Testing the fix...
python -c "import pyautogui; import pyscreeze; print('SUCCESS: All dependencies working!')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ SUCCESS: Dependencies fixed!
    echo You can now restart the automation:
    echo python task_orchestrator_enhanced.py
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ❌ FAILED: Please check the logs
    echo ========================================
)

pause
