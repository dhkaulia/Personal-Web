@echo off
title Juki Akira - Discord Bot
color 0A

echo.
echo  ================================================
echo   Juki Akira Hub - Discord Bot Launcher
echo  ================================================
echo.

:: Load saved tokens from .env if it exists
if exist "%~dp0.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%~dp0.env") do (
        if not "%%A"=="" if not "%%B"=="" set "%%A=%%B"
    )
)

:: Discord bot token — ask once and save
if "%DISCORD_BOT_TOKEN%"=="" (
    set /p DISCORD_BOT_TOKEN="  Enter Discord Bot Token: "
    echo DISCORD_BOT_TOKEN=%DISCORD_BOT_TOKEN%>> "%~dp0.env"
    echo.
)

:: GitHub token — ask once and save
if "%GITHUB_TOKEN%"=="" (
    set /p GITHUB_TOKEN="  Enter GitHub Token: "
    echo GITHUB_TOKEN=%GITHUB_TOKEN%>> "%~dp0.env"
    echo.
)

if "%AUTO_GIT_PUSH%"=="" set AUTO_GIT_PUSH=true

echo  Discord Token : SET
echo  GitHub Token  : SET
echo  Git Push      : %AUTO_GIT_PUSH%
echo.
echo  Starting bot... (Ctrl+C to stop)
echo  ================================================
echo.

py "%~dp0discord-bot/bot.py"

echo.
echo  Bot stopped.
pause
