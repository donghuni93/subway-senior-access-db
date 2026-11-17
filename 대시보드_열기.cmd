@echo off
rem 더블클릭: 대시보드(8501)와 읽기 가이드(8502)를 켜고, 서버가 응답하면 브라우저로 연다.
rem 대시보드는 MySQL이 켜져 있어야 데이터가 보인다. 서버 로그: %TEMP%\streamlit-8501.log, streamlit-8502.log
chcp 65001 >nul
cd /d "%~dp0"
where uv >nul 2>&1
if errorlevel 1 (
  echo uv를 찾을 수 없습니다. 설치: https://docs.astral.sh/uv/
  pause
  exit /b 1
)
call :serve 8501 04_본프로젝트/src/app.py
call :serve 8502 04_본프로젝트/src/guide_app.py
call :open 8501
call :open 8502
echo 끝났습니다. 서버를 끄려면 작업 표시줄의 streamlit 창을 닫으세요.
timeout /t 3 >nul 2>&1
exit /b

:listening
rem 포트가 열려 있으면 0. Windows 표시 언어와 상관없이 동작하도록 PowerShell로 확인한다.
powershell -NoProfile -Command "if (Get-NetTCPConnection -State Listen -LocalPort %1 -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
exit /b

:serve
call :listening %1
if not errorlevel 1 (
  echo %1 이미 실행 중 ^(다른 프로그램이 쓰는 중일 수도 있습니다^)
  exit /b
)
echo %1 시작: %2
start "streamlit-%1" /min cmd /c uv run streamlit run %2 --server.port %1 --server.headless true ^> "%TEMP%\streamlit-%1.log" 2^>^&1
exit /b

:open
rem 최대 120초 동안 1초마다 확인하고, 열리면 브라우저를 연다.
for /l %%i in (1,1,120) do (
  call :listening %1
  if not errorlevel 1 (
    start "" http://localhost:%1
    exit /b
  )
  ping -n 2 127.0.0.1 >nul
)
echo %1 서버가 120초 안에 열리지 않았습니다. 로그: %TEMP%\streamlit-%1.log
exit /b
