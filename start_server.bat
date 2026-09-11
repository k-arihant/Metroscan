@echo off
TITLE MetroScan SIH 2026 Unified Server Launcher
COLOR 0B

echo ================================================================
echo       METROSCAN SIH 2026 -- OFFICIAL UNIFIED SERVER LAUNCHER
echo       Version 3.2 (MetroScan Golden Master Release)
echo       Updated: 10-Sep-2026 02:21 AM IST
echo ================================================================
echo.

:: 1. Define Canonical Workspace Paths
set WORKSPACE_ROOT=%~dp0
if "%WORKSPACE_ROOT:~-1%"=="\" set WORKSPACE_ROOT=%WORKSPACE_ROOT:~0,-1%
set FRONTEND_DIR=%WORKSPACE_ROOT%\frontend
set BACKEND_DIR=%WORKSPACE_ROOT%\backend
set PYTHON_EXE=C:\Users\yashr\miniconda3\envs\metroscan-gpu\python.exe

if not exist "%PYTHON_EXE%" (
    echo [INFO] Conda env python not found at default path, using system python.
    set PYTHON_EXE=python
)

:: 2. Terminate any stale zombie processes on port 8000 and 5173
echo [1/5] Clearing stale processes on ports 8000 and 5173...
powershell -NoProfile -Command "(Get-NetTCPConnection -LocalPort 8000, 5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess) | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1
timeout /t 2 /nobreak >nul

:: 3. Launch Authoritative FastAPI Backend
echo [2/5] Starting FastAPI Backend on 0.0.0.0:8000 (Supports Web + Mobile Wireless & USB) ...
start "MetroScan-Backend" /D "%WORKSPACE_ROOT%" cmd /k ""%PYTHON_EXE%" -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload"
adb reverse tcp:8000 tcp:8000 >nul 2>&1

:: Allow backend 3 seconds to initialize worker pool
timeout /t 3 /nobreak >nul

:: 4. Launch Authoritative Vite Frontend
echo [3/5] Starting Vite Web Portal on http://localhost:5173 ...
start "MetroScan-Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev -- --host 0.0.0.0 --port 5173 --strictPort"

:: 5. Health Check Verification Loop
echo [4/5] Waiting for backend and frontend services to become ready...
powershell -NoProfile -Command "$ready = $false; for ($i=0; $i -lt 50; $i++) { try { $res = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2; if ($res.StatusCode -eq 200) { $ready = $true; break } } catch {}; Start-Sleep -Milliseconds 500 }; if ($ready) { Write-Host '[OK] FastAPI Backend is ONLINE at http://127.0.0.1:8000' -ForegroundColor Green } else { Write-Host '[WARN] Backend did not respond on /health. Check MetroScan-Backend window.' -ForegroundColor Red }"

powershell -NoProfile -Command "$ready = $false; for ($i=0; $i -lt 60; $i++) { try { $res = Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 2; if ($res.StatusCode -eq 200) { $ready = $true; break } } catch {}; Start-Sleep -Milliseconds 500 }; if ($ready) { Write-Host '[OK] Vite Frontend Portal is ONLINE at http://localhost:5173' -ForegroundColor Green } else { Write-Host '[WARN] Frontend did not respond. Check MetroScan-Frontend window.' -ForegroundColor Red }"

:: 6. Launch Web Browser
echo.
echo [5/5] Launching MetroScan Web Portal in browser...
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo ================================================================
echo   METROSCAN SIH 2026 -- ALL SERVICES SUCCESSFULLY LAUNCHED!
echo.
echo   WEB PORTAL (Open in Browser): http://localhost:5173
echo   Backend REST API:             http://127.0.0.1:8000
echo   Interactive API Docs:         http://127.0.0.1:8000/docs
echo.
echo   LOGIN OPTIONS:
echo   1. Google OAuth Verified Accounts (with persistent audit history):
echo      - okay131005@gmail.com
echo      - rockstarboi1310@gmail.com
echo      - yashrajnikam2005@gmail.com
echo      - ynikam2005@gmail.com
echo.
echo   2. One-Click Demo Logins:
echo      - Demo Inspector: inspector@legalmetrology.gov.in / Inspector@123
echo      - Demo Citizen:   citizen@example.in / Citizen@123
echo.
echo   GOLDEN MASTER HIGHLIGHTS:
echo   - App Header: Clean 'MetroScan' branding across all portals
echo   - Inspector Poki: Interactive mascot popup with all 10 Metrology Laws
echo   - Persistent History: Scans auto-saved to account history
echo   - MPE Auditor: Ratio-based (9%%) tolerance calculation for small sachets
echo   - Sector Analytics: Live compliance breakdown for 9 FMCG sectors
echo.
echo   To stop MetroScan, close the two opened command windows.
echo ================================================================
pause
