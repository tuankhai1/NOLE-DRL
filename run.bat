@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   DRL Watcher - theo doi su kien dat ve HUST
echo   Dong cua so nay = dung bot. Ctrl+C de thoat.
echo ============================================
python drl_watch.py run
echo.
echo Bot da dung. Nhan phim bat ky de dong...
pause >nul
