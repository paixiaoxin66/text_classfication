@echo off
chcp 65001 >nul
title Heimao Scraper
cd /d "%~dp0"
echo [1/2] uv sync ...
uv sync || (echo FAILED: uv sync & pause & exit /b 1)
echo [2/2] start scraper ...
uv run python scraper.py %*
echo.
echo Done. Output: data\hemao_complaints.csv  (resume with --resume)
pause
