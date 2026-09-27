@echo off
chcp 65001 > nul
echo ============================================================
echo   SOCRATES NHI 💡 - DONG GOI UNG DUNG WINDOWS DESKTOP
echo   Cuoc thi Sang tao tre Quoc gia AI 2026 - Bang A (THCS)
echo ============================================================
echo.

python build_desktop.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo [THANH CONG] Ung dung da duoc dong goi tai thu muc: dist\Socrates_Nhi
    echo Tep chay: dist\Socrates_Nhi\Socrates_Nhi.exe
    echo ============================================================
) else (
    echo.
    echo [THAT BAI] Co loi xay ra trong qua trinh dong goi!
)

pause
