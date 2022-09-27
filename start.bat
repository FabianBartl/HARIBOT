@echo off
cd src
cls
:start
main.py
echo "error at %DATE% %TIME%"
goto start
pause