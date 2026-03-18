@echo off
echo - - - Setting up UTAU-UIEL Environment - - -

:: Create venv if it doesn't exist
if not exist "../../.venv" (
    python -m venv ../../.venv
)

:: Activate and Install
call ../../.venv/Scripts/activate
python -m pip install --upgrade pip
pip install numpy scipy sounddevice phonemizer gruut

echo.
echo - - - Setup Complete - - -
echo Environment is ready for the Klatt Prototype.
cmd /k