@echo off
setlocal

pushd %~dp0

set this=%~n0

if not defined PYTHON set PYTHON=py

if not defined SPHINXBUILD (
    %PYTHON% -c "import sphinx" > nul 2> nul
    if errorlevel 1 (
        echo Installing sphinx with %PYTHON%
        %PYTHON% -m pip install sphinx
        if errorlevel 1 exit /B
    )
    set SPHINXBUILD=%PYTHON% -c "import sphinx.cmd.build, sys; sys.exit(sphinx.cmd.build.main())"
)

rem Search for HHC in likely places
set HTMLHELP=
where hhc /q && set HTMLHELP=hhc && goto :skiphhcsearch
where /R ..\externals hhc > "%TEMP%\hhc.loc" 2> nul && set /P HTMLHELP= < "%TEMP%\hhc.loc" & del "%TEMP%\hhc.loc"
if not exist "%HTMLHELP%" where /R "%ProgramFiles(x86)%" hhc > "%TEMP%\hhc.loc" 2> nul && set /P HTMLHELP= < "%TEMP%\hhc.loc" & del "%TEMP%\hhc.loc"
if not exist "%HTMLHELP%" where /R "%ProgramFiles%" hhc > "%TEMP%\hhc.loc" 2> nul && set /P HTMLHELP= < "%TEMP%\hhc.loc" & del "%TEMP%\hhc.loc"
if not exist "%HTMLHELP%" (
    echo.
    echo.The HTML Help Workshop was not found.  Set the HTMLHELP variable
    echo.to the path to hhc.exe or download and install it from
    echo.http://msdn.microsoft.com/en-us/library/ms669985
    exit /B 1
)
echo hhc.exe path: %HTMLHELP%

if "%BUILDDIR%" EQU "" set BUILDDIR=build

%SPHINXBUILD% >nul 2> nul
if errorlevel 9009 (
    echo.
    echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
    echo.installed, then set the SPHINXBUILD environment variable to point
    echo.to the full path of the 'sphinx-build' executable. Alternatively you
    echo.may add the Sphinx directory to PATH.
    popd
    exit /B 1
)

set SPHINXOPTS=-D html_theme_options.body_max_width=none %SPHINXOPTS%

cmd /S /C "%SPHINXBUILD% %SPHINXOPTS% -bhtmlhelp -dbuild\doctrees . "%BUILDDIR%\htmlhelp"

"%HTMLHELP%" "%BUILDDIR%\htmlhelp\test.hhp"
rem hhc.exe seems to always exit with code 1, reset to 0 for less than 2
if not errorlevel 2 cmd /C exit /b 0

echo.
if errorlevel 1 (
    echo.Build failed (exit code %ERRORLEVEL%^), check for error messages
    echo.above.  Any output will be found in %BUILDDIR%\%1
) else (
    echo.Build succeeded. All output should be in %BUILDDIR%\%1
)

popd
