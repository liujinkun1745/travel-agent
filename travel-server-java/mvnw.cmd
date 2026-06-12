@echo off
REM Maven Wrapper for Windows
REM Downloads Maven 3.9.9 automatically if not cached, then runs mvn

setlocal enabledelayedexpansion

cd /d "%~dp0"

set "MAVEN_VERSION=3.9.9"
set "MAVEN_ZIP=apache-maven-%MAVEN_VERSION%-bin.zip"
set "MAVEN_DIR=apache-maven-%MAVEN_VERSION%"
set "MAVEN_CACHE=%USERPROFILE%\.m2\wrapper\dists\%MAVEN_DIR%"

REM Check if Maven already cached
if exist "%MAVEN_CACHE%\bin\mvn.cmd" (
    set "MVN_CMD=%MAVEN_CACHE%\bin\mvn.cmd"
    goto :run
)

REM Download Maven
echo Downloading Maven %MAVEN_VERSION%...
if not exist "%MAVEN_CACHE%" mkdir "%MAVEN_CACHE%\.."

REM Try multiple mirrors
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://dlcdn.apache.org/maven/maven-3/%MAVEN_VERSION%/binaries/%MAVEN_ZIP%' -OutFile '%TEMP%\%MAVEN_ZIP%'}" 2>nul
if not exist "%TEMP%\%MAVEN_ZIP%" (
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://archive.apache.org/dist/maven/maven-3/%MAVEN_VERSION%/binaries/%MAVEN_ZIP%' -OutFile '%TEMP%\%MAVEN_ZIP%'}"
)

if not exist "%TEMP%\%MAVEN_ZIP%" (
    echo ERROR: Failed to download Maven.
    echo Please download manually: https://maven.apache.org/download.cgi
    echo Extract to: %MAVEN_CACHE%
    exit /b 1
)

echo Extracting Maven...
powershell -Command "Expand-Archive -Path '%TEMP%\%MAVEN_ZIP%' -DestinationPath '%MAVEN_CACHE%\..' -Force"
del "%TEMP%\%MAVEN_ZIP%" 2>nul

if exist "%MAVEN_CACHE%\bin\mvn.cmd" (
    set "MVN_CMD=%MAVEN_CACHE%\bin\mvn.cmd"
    echo Maven %MAVEN_VERSION% ready.
) else (
    echo ERROR: Maven extraction failed.
    exit /b 1
)

:run
%MVN_CMD% %*
goto :end

:end
endlocal
