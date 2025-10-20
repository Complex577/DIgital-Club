const fs = require('fs');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

// Function to read CSV file
function readCSV(filename) {
  try {
    if (!fs.existsSync(filename)) {
      console.log(`⚠️  File ${filename} not found, skipping...`);
      return [];
    }
    
    const content = fs.readFileSync(filename, 'utf8');
    const lines = content.split('\n').filter(line => line.trim() !== '');
    const contacts = [];
    
    // Skip header line
    for (let i = 1; i < lines.length; i++) {
      const [group, phone] = lines[i].split(',');
      if (group && phone) {
        contacts.push({
          group: group.trim(),
          phone: phone.trim()
        });
      }
    }
    
    return contacts;
  } catch (error) {
    console.error(`❌ Error reading ${filename}:`, error.message);
    return [];
  }
}

// Function to create unique contact key
function createContactKey(contact) {
  return `${contact.group}|${contact.phone}`;
}

// Function to merge and compare contacts
async function mergeAndCompareContacts() {
  console.log('🔄 Starting contact comparison and merge process...\n');
  
  // Read all CSV files
  const openwaContacts = readCSV('group_contacts.csv');
  const wwjsContacts = readCSV('group_contacts_wwjs.csv');
  const baileysContacts = readCSV('group_contacts_baileys.csv');
  const venomContacts = readCSV('group_contacts_venom.csv');
  
  console.log(`📊 Contact counts:`);
  console.log(`   @open-wa/wa-automate: ${openwaContacts.length}`);
  console.log(`   whatsapp-web.js: ${wwjsContacts.length}`);
  console.log(`   Baileys: ${baileysContacts.length}`);
  console.log(`   venom-bot: ${venomContacts.length}\n`);
  
  // Create sets for each method
  const openwaSet = new Set(openwaContacts.map(createContactKey));
  const wwjsSet = new Set(wwjsContacts.map(createContactKey));
  const baileysSet = new Set(baileysContacts.map(createContactKey));
  const venomSet = new Set(venomContacts.map(createContactKey));
  
  // Find unique contacts from each method
  const openwaUnique = openwaContacts.filter(contact => 
    !wwjsSet.has(createContactKey(contact)) && 
    !baileysSet.has(createContactKey(contact)) && 
    !venomSet.has(createContactKey(contact))
  );
  
  const wwjsUnique = wwjsContacts.filter(contact => 
    !openwaSet.has(createContactKey(contact)) && 
    !baileysSet.has(createContactKey(contact)) && 
    !venomSet.has(createContactKey(contact))
  );
  
  const baileysUnique = baileysContacts.filter(contact => 
    !openwaSet.has(createContactKey(contact)) && 
    !wwjsSet.has(createContactKey(contact)) && 
    !venomSet.has(createContactKey(contact))
  );
  
  const venomUnique = venomContacts.filter(contact => 
    !openwaSet.has(createContactKey(contact)) && 
    !wwjsSet.has(createContactKey(contact)) && 
    !baileysSet.has(createContactKey(contact))
  );
  
  // Create merged set of all unique contacts
  const allContacts = new Set();
  [...openwaContacts, ...wwjsContacts, ...baileysContacts, ...venomContacts].forEach(contact => {
    allContacts.add(createContactKey(contact));
  });
  
  // Convert back to contact objects
  const mergedContacts = Array.from(allContacts).map(key => {
    const [group, phone] = key.split('|');
    return { group, phone };
  });
  
  // Write merged CSV
  const csvWriter = createCsvWriter({
    path: 'group_contacts_merged.csv',
    header: [
      { id: 'group', title: 'group' },
      { id: 'phone', title: 'phone' },
    ],
  });
  
  await csvWriter.writeRecords(mergedContacts);
  
  // Generate comparison report
  const report = `
📊 WHATSAPP GROUP EXTRACTION COMPARISON REPORT
===============================================

📈 SUMMARY STATISTICS:
- Total unique contacts found: ${mergedContacts.length}
- @open-wa/wa-automate contacts: ${openwaContacts.length}
- whatsapp-web.js contacts: ${wwjsContacts.length}
- Baileys contacts: ${baileysContacts.length}
- venom-bot contacts: ${venomContacts.length}

🔍 UNIQUE CONTACTS BY METHOD:
- @open-wa/wa-automate unique: ${openwaUnique.length}
- whatsapp-web.js unique: ${wwjsUnique.length}
- Baileys unique: ${baileysUnique.length}
- venom-bot unique: ${venomUnique.length}

📊 COVERAGE ANALYSIS:
- @open-wa/wa-automate coverage: ${((openwaContacts.length / mergedContacts.length) * 100).toFixed(1)}%
- whatsapp-web.js coverage: ${((wwjsContacts.length / mergedContacts.length) * 100).toFixed(1)}%
- Baileys coverage: ${((baileysContacts.length / mergedContacts.length) * 100).toFixed(1)}%
- venom-bot coverage: ${((venomContacts.length / mergedContacts.length) * 100).toFixed(1)}%

🏆 BEST PERFORMING METHOD:
${getBestMethod(openwaContacts.length, wwjsContacts.length, baileysContacts.length, venomContacts.length)}

📁 OUTPUT FILES:
- group_contacts_merged.csv: Complete merged contact list
- This report: extraction_comparison_report.txt

✅ RECOMMENDATION:
Use the merged CSV file (group_contacts_merged.csv) as it contains all unique contacts from all methods.
`;

  // Write report to file
  fs.writeFileSync('extraction_comparison_report.txt', report);
  
  console.log(report);
  console.log('💾 Files created:');
  console.log('   - group_contacts_merged.csv (complete contact list)');
  console.log('   - extraction_comparison_report.txt (detailed analysis)');
}

// Helper function to determine best method
function getBestMethod(openwa, wwjs, baileys, venom) {
  const methods = [
    { name: '@open-wa/wa-automate', count: openwa },
    { name: 'whatsapp-web.js', count: wwjs },
    { name: 'Baileys', count: baileys },
    { name: 'venom-bot', count: venom }
  ];
  
  const best = methods.reduce((max, current) => 
    current.count > max.count ? current : max
  );
  
  return `${best.name} with ${best.count} contacts`;
}

// Run the comparison
mergeAndCompareContacts().catch(error => {
  console.error('❌ Error during comparison:', error);
  process.exit(1);
});
