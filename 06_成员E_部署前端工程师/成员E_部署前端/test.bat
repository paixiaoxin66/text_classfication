@echo off
chcp 65001 >nul
title Heimao Scraper - TEST (200 items)
cd /d "%~dp0"
uv sync || (echo FAILED: uv sync & pause & exit /b 1)
echo Small test run: 500 items, then check data\hemao_complaints.csv
uv run python scraper.py --max-items 500 %*
pause
