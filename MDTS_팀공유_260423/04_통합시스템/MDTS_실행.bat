@echo off
chcp 65001 >nul
setlocal

REM ─────────────────────────────────────────────────────────────
REM  MDTS (M-MEDIC v2) 통합 진단 시스템 더블클릭 런처
REM ─────────────────────────────────────────────────────────────

cd /d "%~dp0"

echo ============================================================
echo   MDTS 통합 진단 시스템 시작
echo ============================================================
echo.

set "PYTHON=python"
where %PYTHON% >nul 2>nul
if errorlevel 1 (
  set "PYTHON=py -3"
  where py >nul 2>nul
  if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo        https://www.python.org/downloads/ 에서 Python 3.10 이상을 설치하세요.
    pause
    exit /b 1
  )
)

echo [1/2] 필요 패키지 확인 중 (torch, torchvision, scikit-learn, Pillow, numpy)...
%PYTHON% -c "import torch, torchvision, sklearn, PIL, numpy" 2>nul
if errorlevel 1 (
  echo.
  echo [경고] 필수 패키지 일부가 누락되어 자동 설치를 시도합니다.
  echo        설치를 건너뛰려면 Ctrl+C로 종료하세요.
  echo.
  %PYTHON% -m pip install --upgrade pip
  %PYTHON% -m pip install torch torchvision scikit-learn Pillow numpy
  if errorlevel 1 (
    echo [오류] 패키지 설치 실패. 인터넷 연결과 권한을 확인하세요.
    pause
    exit /b 1
  )
)

echo [2/2] 통합 진단 앱 기동...
echo.
%PYTHON% "MDTS_통합진단앱.py" %*

echo.
echo ============================================================
echo   서버가 종료되었습니다.
echo ============================================================
pause
endlocal
