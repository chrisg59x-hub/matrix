@echo off
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0pre-commit.ps1"
exit /b %ERRORLEVEL%
