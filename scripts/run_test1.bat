@echo off
cd /d "%~dp0\.."
py src\main.py --vfs vfs\deep.csv --prompt "test1> " --script scripts\test1.txt