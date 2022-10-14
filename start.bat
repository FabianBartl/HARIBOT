@echo off

@REM setup nodejs environment
call apps/nodejs/nodevars.bat

@REM setup src/ as working directory
cd src

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