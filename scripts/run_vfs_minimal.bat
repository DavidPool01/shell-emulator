@echo off
cd /d "%~dp0\.."
py src\main.py --vfs vfs\minimal.csv --prompt "min> " --script scripts\test_vfs_minimal.txt