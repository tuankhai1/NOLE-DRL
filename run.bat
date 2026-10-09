@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   DRL Watcher - HUST ticket-event monitor
echo   Close this window to stop. Ctrl+C to quit.
echo ============================================
python drl_watch.py run
echo.
echo Bot stopped. Press any key to close...
pause >nul
