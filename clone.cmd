@echo off
echo - - - Cloning Repositories at Exact Versions - - - 
:: 0. The Core Utility Library (libzut)
if not exist "libzut" (
    git clone https://github.com/xiaoschannel/zut_CSharp libzut
    pushd libzut & git reset --hard 22f3b37 & popd
)

:: 1. Klatt Engine (Synthesis)
:: Version: Jan 2024 - Stable for Shadow Loading
if not exist "tdklatt" (
    git clone https://github.com/guestdaniel/tdklatt
    cd tdklatt
    git reset --hard 081f984
    cd ..
)

:: 2. UIAL (UTAU API)
if not exist "UIAL" (
    git clone https://github.com/xiaoschannel/UIAL-UTAU-Interfacing-API-Library UIAL
    pushd UIAL & git reset --hard f8aa785 & popd
)

:: 3. Your Kokoro Frontend (The Brain)
:: Replace 'your_hash_here' with your most recent stable commit
if not exist "kokoro-frontend" (
    git clone https://github.com/detectivezog/kokoro-multilingual-frontend-multithread kokoro-frontend
    cd kokoro-frontend
    git reset --hard 6a368a5
    cd ..
)

echo Done. All engines are locked to validated versions.
cmd /k