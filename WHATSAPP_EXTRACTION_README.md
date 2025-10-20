# WhatsApp Group Members Extraction - Maximum Reliability

This project provides multiple WhatsApp automation libraries to extract all group members' phone numbers with maximum reliability. Each library has different strengths and may capture different members, so we provide a comparison tool to merge results.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Run Individual Extraction Methods

#### Option A: whatsapp-web.js (Recommended)
```bash
node extract-groups-wwjs.js
```

#### Option B: Baileys (Lightweight)
```bash
node extract-groups-baileys.js
```

#### Option C: venom-bot (Enhanced)
```bash
node extract-groups-venom.js
```

#### Option D: Original @open-wa/wa-automate
```bash
node extract-groups.js
```

### 3. Compare and Merge Results
```bash
node merge-contacts.js
```

## 📊 Output Files

Each extraction method creates its own CSV file:
- `group_contacts_wwjs.csv` - whatsapp-web.js results
- `group_contacts_baileys.csv` - Baileys results  
- `group_contacts_venom.csv` - venom-bot results
- `group_contacts.csv` - Original @open-wa/wa-automate results

The merge tool creates:
- `group_contacts_merged.csv` - Complete merged contact list
- `extraction_comparison_report.txt` - Detailed analysis report

## 🔧 Features

### All Scripts Include:
- ✅ QR code authentication
- ✅ Session persistence (no re-scanning)
- ✅ Robust error handling
- ✅ Null safety checks
- ✅ Rate limiting to avoid blocks
- ✅ Progress tracking
- ✅ Detailed logging
- ✅ CSV export in consistent format

### Individual Strengths:

#### whatsapp-web.js
- Most popular and stable
- Active maintenance
- Good error handling
- Reliable group member extraction

#### Baileys
- Lightweight (no Chromium overhead)
- Direct WhatsApp Web API connection
- Multi-device support
- Fast performance

#### venom-bot
- Built on whatsapp-web.js
- Enhanced features
- Better session management
- Built-in retry mechanisms

#### @open-wa/wa-automate
- Original implementation
- Mature library
- Good for basic extraction

## 📱 Usage Instructions

1. **Run any extraction script**
2. **Scan QR code** with your WhatsApp mobile app
3. **Wait for completion** - scripts will show progress
4. **Run merge tool** to get complete results
5. **Check report** for coverage analysis

## ⚠️ Important Notes

- Each script creates its own session folder
- Session folders are excluded from git (.gitignore)
- CSV files are excluded from git (.gitignore)
- Run scripts one at a time to avoid conflicts
- Each method may capture different members
- Use the merged CSV for complete coverage

## 🛠️ Troubleshooting

### Common Issues:

1. **QR Code Not Showing**
   - Ensure headless: false in script
   - Check browser permissions

2. **Session Errors**
   - Delete session folders and restart
   - Clear browser cache

3. **Rate Limiting**
   - Scripts include delays between groups
   - Wait if you get blocked

4. **Missing Members**
   - Run multiple methods
   - Use merge tool for complete coverage

### Session Folders:
- `wwjs-session/` - whatsapp-web.js
- `baileys-session/` - Baileys
- `venom-session/` - venom-bot
- `session/` - @open-wa/wa-automate

## 📈 Expected Results

The merge tool will show:
- Total unique contacts found
- Coverage percentage for each method
- Which method performed best
- Complete merged contact list

## 🔒 Privacy & Security

- All session data is stored locally
- No data is sent to external servers
- CSV files contain only group names and phone numbers
- Session folders are excluded from version control

## 📝 License

This project is for educational and personal use only. Please respect WhatsApp's Terms of Service and use responsibly.
