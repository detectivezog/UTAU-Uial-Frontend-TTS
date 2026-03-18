@echo off
echo - - - Checking for .NET SDK 10 - - -

:: Try to find the SDK
dotnet --list-sdks | findstr "10." >nul 2>&1

if %errorlevel% neq 0 (
    echo .NET SDK 10 not found. Installing via winget...
    :: Microsoft.DotNet.SDK.10 is the package ID
    winget install Microsoft.DotNet.SDK.10 --silent --accept-package-agreements --accept-source-agreements
    
    if %errorlevel% neq 0 (
        echo Failed to install via winget. Please download manually:
        echo https://dotnet.microsoft.com/en-us/download/dotnet/10.0
    ) else (
        echo Installation started. Please restart your terminal after it finishes.
    )
) else (
    echo .NET SDK 10 is already installed.
)

pause