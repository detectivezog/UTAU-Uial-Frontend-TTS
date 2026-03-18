@echo off
echo - - - Building UIAL Bridge - - -

:: Build the main project
cd UIAL\UIAL-Main
dotnet build --configuration Debug

echo.
:: The compiler named it UIAL.dll, not UIAL-Main.dll
if exist "bin\Debug\netstandard2.0\UIAL.dll" (
    echo [SUCCESS] UIAL.dll is ready!
) else (
    echo [ERROR] DLL not found.
)
pause