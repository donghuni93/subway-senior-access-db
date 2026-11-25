@echo off
chcp 65001 >nul
rem Windows Task Scheduler entry point. Runs the API collector hourly.
rem Uses only %~dp0 (this file's folder). Folder names are Korean, so chcp 65001 below is required.
cd /d "%~dp0"
if not exist "07_데이터\snapshots" mkdir "07_데이터\snapshots"
"C:\Users\dongh\.venvs\endb\Scripts\python.exe" -X utf8 "05_코드\collect.py" >> "07_데이터\snapshots\collect_stdout.log" 2>&1
rem After collecting, refresh lift/outage/closure tables in MySQL (subway_access_db).
rem A DB failure is logged separately and never affects the collected snapshots above.
"C:\Users\dongh\.venvs\endb\Scripts\python.exe" -X utf8 "05_코드\preprocess.py" --live >> "07_데이터\snapshots\db_refresh.log" 2>&1 && "C:\Users\dongh\.venvs\endb\Scripts\python.exe" -X utf8 "05_코드\load_db.py" --live >> "07_데이터\snapshots\db_refresh.log" 2>&1
