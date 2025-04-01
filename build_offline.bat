@echo off
echo Building ASSHM...

:: Clean up previous build artifacts
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

:: Create build directory structure
mkdir build 2>nul
mkdir build\installers 2>nul
mkdir build\asshm 2>nul

:: Copy installer files to build directory
copy installers\* build\installers\

:: Build Python application
pyinstaller asshm.spec

:: Move PyInstaller output to build directory
copy /Y dist\asshm.exe build\asshm\

:: Build installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

:: Clean up dist directory after installer is built
rmdir /s /q dist

echo Done!
pause