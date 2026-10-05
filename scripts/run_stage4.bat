@echo off
cd /d "%~dp0\.."
py src\main.py --vfs vfs\deep.csv --prompt "stage4> " --script scripts\test_stage4.txt