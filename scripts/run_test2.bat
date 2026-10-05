@echo off
cd /d "%~dp0\.."
py src\main.py --vfs vfs\multi.csv --prompt "test2# " --script scripts\test2.txt