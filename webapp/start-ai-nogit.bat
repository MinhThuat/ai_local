@echo off
REM ===== Khoi dong webapp KHONG can cai Git (chi can Python) =====
REM Dien ten repo GitHub cua ban:
set GH_OWNER=tenban
set GH_REPO=tenrepo
set GH_BRANCH=main
REM set GH_TOKEN=xxx        (chi mo dong nay neu repo PRIVATE)

REM (1) autosync no-git: tu tai code tu GitHub + tu restart server
start "webapp" cmd /k python autosync_nogit.py

REM cho code tai ve + server len
timeout /t 8 /nobreak >nul

REM (2) Cloudflare tunnel -> webapp 8000 (chay rieng -> link khong doi khi sync)
cloudflared tunnel --url http://localhost:8000
