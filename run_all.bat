@echo off
rem Regenerate test PNGs (python make_tests.py) and run this to verify PNG.bt.
rem Requires 010 Editor; runs each file in -noui mode and saves the report.
cd /d %~dp0
del testfiles\report.txt 2>nul
for %%F in (testfiles\*.png) do (
  start "" /wait "D:\Tool\010 Editor\010Editor.exe" "%%F" -noui -nowarnings -script:test_png.1sc
  move /y testfiles\report.txt "testfiles\report_%%~nF.txt" >nul 2>&1
)
echo DONE - reports in testfiles\report_*.txt
