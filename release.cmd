@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Usage:
rem   release.cmd
rem   release.cmd patch
rem   release.cmd minor
rem   release.cmd major

set "BUMP=%~1"
if "%BUMP%"=="" set "BUMP=patch"

if /I not "%BUMP%"=="patch" if /I not "%BUMP%"=="minor" if /I not "%BUMP%"=="major" (
    echo Invalid bump type: %BUMP%
    echo Use: patch ^| minor ^| major
    exit /b 1
)

rem Check git
git --version >nul 2>&1
if errorlevel 1 (
    echo Git is not installed or not in PATH.
    exit /b 1
)

rem Check we are in a git repo
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo Current folder is not a git repository.
    exit /b 1
)

rem Optional: ensure working tree is clean
for /f %%A in ('git status --porcelain') do (
    echo Working tree is not clean. Commit or stash changes first.
    exit /b 1
)

rem Get latest semver tag like v1.2.3
set "LATEST="
for /f "delims=" %%A in ('git tag --list "v*" --sort=-v:refname') do (
    if not defined LATEST set "LATEST=%%A"
)

if not defined LATEST (
    set "LATEST=v0.0.0"
)

echo Latest tag: %LATEST%

rem Strip leading v
set "VER=%LATEST:~1%"

rem Parse version
for /f "tokens=1,2,3 delims=." %%A in ("%VER%") do (
    set /a MAJOR=%%A
    set /a MINOR=%%B
    set /a PATCH=%%C
)

if /I "%BUMP%"=="patch" (
    set /a PATCH+=1
)

if /I "%BUMP%"=="minor" (
    set /a MINOR+=1
    set /a PATCH=0
)

if /I "%BUMP%"=="major" (
    set /a MAJOR+=1
    set /a MINOR=0
    set /a PATCH=0
)

set "NEW_TAG=v!MAJOR!.!MINOR!.!PATCH!"
echo New tag: !NEW_TAG!

rem Check if tag already exists
git rev-parse "!NEW_TAG!" >nul 2>&1
if not errorlevel 1 (
    echo Tag !NEW_TAG! already exists.
    exit /b 1
)

rem Create annotated tag
git tag -a "!NEW_TAG!" -m "Release !NEW_TAG!"
if errorlevel 1 (
    echo Failed to create tag !NEW_TAG!.
    exit /b 1
)

rem Push tag
git push origin "!NEW_TAG!"
if errorlevel 1 (
    echo Failed to push tag !NEW_TAG!.
    exit /b 1
)

echo Done. Pushed !NEW_TAG!
exit /b 0