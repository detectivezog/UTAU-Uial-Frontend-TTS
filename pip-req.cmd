@echo off
echo - - - Running - - -
call ..\..\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
timeout /t 10