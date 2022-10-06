@echo off
cd src
cls

set /a i=0
set /a max=10
:start
@REM if %i% GTR %max% goto end

@REM arg1: color mode; arg2: logging level
python main.py %~1 %~2
echo "%i% error occured: %DATE% %TIME%"

set /a i+=1
goto start
:end

pause