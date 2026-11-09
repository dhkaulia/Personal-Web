@echo off
title Juki Akira - Discord Bot
color 0A

echo.
echo  ================================================
echo   Juki Akira Hub - Discord Bot Launcher
echo  ================================================
echo.

:: Check if token is already set in environment
if "%DISCORD_BOT_TOKEN%"=="" (
    set /p DISCORD_BOT_TOKEN="  Enter your Discord Bot Token: "
    echo.
)

:: Optional: auto git push after each queue change
if "%AUTO_GIT_PUSH%"=="" (
    set AUTO_GIT_PUSH=true
)

echo  Token  : SET
echo  Git Push: %AUTO_GIT_PUSH%
echo.
echo  Starting bot... (Ctrl+C to stop)
echo  ================================================
echo.

py discord-bot/bot.py

echo.
echo  Bot stopped.
pause
