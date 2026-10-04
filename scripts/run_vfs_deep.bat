@echo off
cd /d "%~dp0\.."
py src\main.py --vfs vfs\deep.csv --prompt "deep> " --script scripts\test_vfs_deep.txt