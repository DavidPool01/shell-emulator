@echo off
cd /d "%~dp0\.."
py src\main.py --vfs vfs\not_exists.csv --prompt "err> "