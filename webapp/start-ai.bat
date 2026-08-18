@echo off
REM ============================================================
REM  Khoi dong webapp tren may AI (Windows).
REM  cloudflared chay RIENG -> khi autosync restart server.py,
REM  link Cloudflare KHONG doi.
REM ============================================================

REM (1) ComfyUI: gia su da chay san bang run_nvidia_gpu.bat.
REM     Neu muon bat nay mo luon thi bo REM dong duoi:
REM start "ComfyUI" cmd /k run_nvidia_gpu.bat

REM (2) Webapp: tu sync code tu GitHub + tu restart. Chay o cua so rieng.
start "webapp" cmd /k python autosync.py

REM Cho server len truoc vai giay roi mo tunnel
timeout /t 5 /nobreak >nul

REM (3) Cloudflare tunnel -> webapp cong 8000 (KHONG phai 8188).
REM     Chay o cua so nay; URL trycloudflare hien ra o day.
REM     Giu cua so nay mo -> link song. Restart code KHONG dung toi no.
cloudflared tunnel --url http://localhost:8000
