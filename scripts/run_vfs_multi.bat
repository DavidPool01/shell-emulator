@echo off
cd /d "%~dp0\.."
py src\main.py --vfs vfs\multi.csv --prompt "multi> " --script scripts\test_vfs_minimal.txt