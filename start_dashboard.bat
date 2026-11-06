@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please create the virtual environment using README.md first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run dashboard/app.py --server.address 127.0.0.1
