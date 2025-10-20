@echo off
echo ========================================
echo WhatsApp Group Members Extraction Suite
echo ========================================
echo.
echo This will run all extraction methods sequentially
echo Each method will require QR code scanning
echo.
pause

echo.
echo [1/4] Running whatsapp-web.js extraction...
node extract-groups-wwjs.js
if %errorlevel% neq 0 (
    echo Error in whatsapp-web.js extraction
    pause
    exit /b 1
)

echo.
echo [2/4] Running Baileys extraction...
node extract-groups-baileys.js
if %errorlevel% neq 0 (
    echo Error in Baileys extraction
    pause
    exit /b 1
)

echo.
echo [3/4] Running venom-bot extraction...
node extract-groups-venom.js
if %errorlevel% neq 0 (
    echo Error in venom-bot extraction
    pause
    exit /b 1
)

echo.
echo [4/4] Running original @open-wa/wa-automate extraction...
node extract-groups.js
if %errorlevel% neq 0 (
    echo Error in @open-wa/wa-automate extraction
    pause
    exit /b 1
)

echo.
echo [5/5] Merging and comparing results...
node merge-contacts.js
if %errorlevel% neq 0 (
    echo Error in merge process
    pause
    exit /b 1
)

echo.
echo ========================================
echo All extractions completed successfully!
echo ========================================
echo.
echo Check the following files:
echo - group_contacts_merged.csv (complete contact list)
echo - extraction_comparison_report.txt (analysis report)
echo.
pause
