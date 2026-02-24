@echo off
title Gastro SaaS - Cargar Datos de Ejemplo
echo.
echo  Cargando datos de ejemplo...
echo.
"%~dp0venv\Scripts\python.exe" "%~dp0manage.py" load_demo_data
echo.
pause
