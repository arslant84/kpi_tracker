@echo off
title KPI Tracker
cd /d "%~dp0kpi_tracker"
call venv\Scripts\activate
echo.
echo  Starting KPI Tracker...
echo  Open http://127.0.0.1:8000 in your browser
echo.
start "" "http://127.0.0.1:8000"
python manage.py runserver
pause
