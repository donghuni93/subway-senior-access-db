@echo off
rem Windows Task Scheduler entry point. Runs the API collector hourly.
rem Uses only %~dp0 (this file's folder) so the script has no non-ASCII paths.
cd /d "%~dp0"
if not exist "data\snapshots" mkdir "data\snapshots"
"C:\Users\dongh\.venvs\endb\Scripts\python.exe" -X utf8 "src\collect.py" >> "data\snapshots\collect_stdout.log" 2>&1
rem After collecting, refresh lift/outage/closure tables in MySQL (subway_access_db).
rem A DB failure is logged separately and never affects the collected snapshots above.
"C:\Users\dongh\.venvs\endb\Scripts\python.exe" -X utf8 "src\preprocess.py" --live >> "data\snapshots\db_refresh.log" 2>&1 && "C:\Users\dongh\.venvs\endb\Scripts\python.exe" -X utf8 "src\load_db.py" --live >> "data\snapshots\db_refresh.log" 2>&1
