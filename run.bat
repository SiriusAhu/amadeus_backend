@echo off
setlocal enabledelayedexpansion

if not exist .env (
    echo [ERROR] .env file not found!
    exit /b
)

for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    set "key=%%a"
    set "value=%%b"
    set "!key!=!value!"
)

echo Starting Uvicorn server at %SERVER_HOST%:%SERVER_PORT% ...
uv run -m uvicorn main:app --host %SERVER_HOST% --port %SERVER_PORT% --reload