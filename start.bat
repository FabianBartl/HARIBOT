@echo off

@REM setup nodejs environment
call apps/nodejs/nodevars.bat

@REM open src/ as working directory
cd src

set /a i=0
set /a max=100
:start
if %i% GTR %max% goto check

@REM arg1: color mode; arg2: logging level
call python main.py %~1 %~2 >> ../log/log_start.dat
echo "%i%. error occured with error level %errorlevel% at %DATE% %TIME%"

set /a i+=1
goto start

:check
@REM calling the error handler after occurrence of %max% errors
@REM call python [ERROR_SCRIPT.PY] %i%

@REM increase error counter
set /a max+=i
goto start

:end

pause