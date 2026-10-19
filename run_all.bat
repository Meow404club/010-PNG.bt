@echo off
cd /d D:\workspace\010-PNG.bt
for %%F in (testfiles\*.png) do (
  "D:\Tool\010 Editor\010Editor.exe" "%%F" -noui -nowarnings -script:test_png.1sc
  echo %%F LEVEL=!ERRORLEVEL!
  move /y testfiles\report.txt "testfiles\report_%%~nF.txt" >nul 2>&1
)
