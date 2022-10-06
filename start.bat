
@REM copied from "C:\Program Files\nodejs\nodevars.bat"

@REM Ensure this Node.js and npm are first in the PATH
set "PATH=%APPDATA%\npm;%~dp0;%PATH%"

setlocal enabledelayedexpansion
pushd "%~dp0"

@REM Figure out the Node.js version.
set print_version=.\node.exe -p -e "process.versions.node + ' (' + process.arch + ')'"
for /F "usebackq delims=" %%v in (`%print_version%`) do set version=%%v

rem Print message.
if exist npm.cmd (
  echo Your environment has been set up for using Node.js !version! and npm.
) else (
  echo Your environment has been set up for using Node.js !version!.
)

popd
endlocal

@REM If we're in the Node.js directory, change to the user's home dir.
if "%CD%\"=="%~dp0" cd /d "%HOMEDRIVE%%HOMEPATH%"

@REM -------------------------------------------------------------------------

cd C:\Users\fabia\OneDrive\Dokumente\GitHub\HARIBOT\src

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
