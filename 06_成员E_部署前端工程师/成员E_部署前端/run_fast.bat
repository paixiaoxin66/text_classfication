@echo off
chcp 65001 >nul
title Heimao Scraper - FAST (delay 0.4)
cd /d "%~dp0"
uv sync || (echo FAILED: uv sync & pause & exit /b 1)
uv run python scraper.py --delay 0.4 %*
pause
