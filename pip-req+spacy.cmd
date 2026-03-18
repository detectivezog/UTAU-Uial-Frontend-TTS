@echo off
echo - - - Running - - -
call ..\..\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
timeout /t 10