@echo off
cd /d "%~dp0\.."
py src\main.py --vfs vfs\deep.csv --prompt "test3> " --script scripts\test3.txt