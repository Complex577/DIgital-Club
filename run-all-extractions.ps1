# WhatsApp Group Members Extraction Suite
# PowerShell version

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WhatsApp Group Members Extraction Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will run all extraction methods sequentially" -ForegroundColor Yellow
Write-Host "Each method will require QR code scanning" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue"

try {
    Write-Host ""
    Write-Host "[1/4] Running whatsapp-web.js extraction..." -ForegroundColor Green
    node extract-groups-wwjs.js
    if ($LASTEXITCODE -ne 0) {
        throw "Error in whatsapp-web.js extraction"
    }

    Write-Host ""
    Write-Host "[2/4] Running Baileys extraction..." -ForegroundColor Green
    node extract-groups-baileys.js
    if ($LASTEXITCODE -ne 0) {
        throw "Error in Baileys extraction"
    }

    Write-Host ""
    Write-Host "[3/4] Running venom-bot extraction..." -ForegroundColor Green
    node extract-groups-venom.js
    if ($LASTEXITCODE -ne 0) {
        throw "Error in venom-bot extraction"
    }

    Write-Host ""
    Write-Host "[4/4] Running original @open-wa/wa-automate extraction..." -ForegroundColor Green
    node extract-groups.js
    if ($LASTEXITCODE -ne 0) {
        throw "Error in @open-wa/wa-automate extraction"
    }

    Write-Host ""
    Write-Host "[5/5] Merging and comparing results..." -ForegroundColor Green
    node merge-contacts.js
    if ($LASTEXITCODE -ne 0) {
        throw "Error in merge process"
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "All extractions completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Check the following files:" -ForegroundColor Yellow
    Write-Host "- group_contacts_merged.csv (complete contact list)" -ForegroundColor White
    Write-Host "- extraction_comparison_report.txt (analysis report)" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"

} catch {
    Write-Host ""
    Write-Host "Error occurred: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
