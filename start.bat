@echo off
title Juki Akira - Discord Bot
color 0A

echo.
echo  ================================================
echo   Juki Akira Hub - Discord Bot Launcher
echo  ================================================
echo.

:: Discord bot token
if "%DISCORD_BOT_TOKEN%"=="" (
    set /p DISCORD_BOT_TOKEN="  Enter your Discord Bot Token: "
    echo.
)

:: GitHub token (needed for instant Gist updates on the website)
if "%GITHUB_TOKEN%"=="" (
    set /p GITHUB_TOKEN="  Enter your GitHub Token (for live website updates): "
    echo.
)

:: Auto git push after each queue change
if "%AUTO_GIT_PUSH%"=="" (
    set AUTO_GIT_PUSH=true
)

echo  Discord Token : SET
echo  GitHub Token  : SET
echo  Git Push      : %AUTO_GIT_PUSH%
echo.
echo  Starting bot... (Ctrl+C to stop)
echo  ================================================
echo.

py discord-bot/bot.py

echo.
echo  Bot stopped.
pause
