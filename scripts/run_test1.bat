@echo off
cd /d "%~dp0\.."
py src\main.py --vfs C:\vfs\minimal --prompt "test1> " --script scripts\test1.txt