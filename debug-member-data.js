const wa = require('@open-wa/wa-automate');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

wa.create({
  headless: false,  // Set to false to see the browser
  useChrome: true,  // Use Chrome instead of Chromium
  qrTimeout: 0,  // so you can scan if needed
  sessionDataPath: './session',  // Use a different session folder
  puppeteerOptions: {
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu',
      '--disable-web-security',
      '--disable-features=VizDisplayCompositor'
    ],
    timeout: 60000  // Increase timeout to 60 seconds
  }
}).then(async (client) => {
  console.log("Connected successfully ✅");

  try {
    const csvWriter = createCsvWriter({
      path: 'group_contacts_debug.csv',
      header: [
        { id: 'group', title: 'group' },
        { id: 'phone', title: 'phone' },
        { id: 'member_data', title: 'member_data' },
      ],
    });

    const records = [];

    // Wait a bit for WhatsApp to fully load
    console.log("Waiting for WhatsApp to load...");
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Get all groups with retry logic
    let groups;
    let retryCount = 0;
    const maxRetries = 3;
    
    while (retryCount < maxRetries) {
      try {
        groups = await client.getAllGroups();
        break;
      } catch (error) {
        retryCount++;
        console.log(`Attempt ${retryCount} failed, retrying in 5 seconds...`);
        if (retryCount < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 5000));
        } else {
          throw error;
        }
      }
    }
    
    console.log(`Found ${groups.length} groups.`);
    
    let processedGroups = 0;
    let skippedGroups = 0;
    let totalMembers = 0;

    // Focus on the problematic group
    const targetGroup = groups.find(g => g.name && g.name.includes('UVCCM UDSM MLIMANI'));
    
    if (targetGroup) {
      console.log(`\n🔍 DEBUGGING GROUP: ${targetGroup.name}`);
      console.log(`Group ID: ${targetGroup.id}`);
      console.log(`Group Object:`, JSON.stringify(targetGroup, null, 2));
      
      try {
        const groupMembers = await client.getGroupMembers(targetGroup.id);
        console.log(`\n📱 Found ${groupMembers.length} members`);
        
        for (let i = 0; i < groupMembers.length; i++) {
          const member = groupMembers[i];
          console.log(`\n--- Member ${i + 1} ---`);
          console.log(`Member Object:`, JSON.stringify(member, null, 2));
          
          // Try different ways to extract phone number
          let phone = null;
          let extractionMethod = '';
          
          if (member && member.id) {
            if (typeof member.id === 'string') {
              phone = member.id.replace('@c.us', '').replace('@g.us', '');
              extractionMethod = 'member.id (string)';
            } else if (member.id._serialized) {
              phone = member.id._serialized.replace('@c.us', '').replace('@g.us', '');
              extractionMethod = 'member.id._serialized';
            } else if (member.id.user) {
              phone = member.id.user;
              extractionMethod = 'member.id.user';
            }
          }
          
          console.log(`Extraction method: ${extractionMethod}`);
          console.log(`Extracted phone: ${phone}`);
          
          // Log all possible phone number fields
          console.log(`All member fields:`, Object.keys(member));
          if (member.id) {
            console.log(`member.id fields:`, Object.keys(member.id));
          }
          
          // Add to records for analysis
          records.push({
            group: targetGroup.name,
            phone: phone || 'NO_PHONE_FOUND',
            member_data: JSON.stringify(member)
          });
          
          if (phone && phone.trim() !== '') {
            totalMembers++;
          }
        }
        
        console.log(`\n✅ Extracted ${totalMembers} valid contacts from ${targetGroup.name}`);
        processedGroups++;
        
      } catch (error) {
        console.log(`Error processing group ${targetGroup.name}: ${error.message}`);
        skippedGroups++;
      }
    } else {
      console.log('❌ Target group not found!');
    }

    // Write to CSV
    await csvWriter.writeRecords(records);
    console.log(`\n📊 DEBUG SUMMARY:`);
    console.log(`✅ Processed groups: ${processedGroups}`);
    console.log(`⚠️  Skipped groups: ${skippedGroups}`);
    console.log(`📱 Total contacts extracted: ${totalMembers}`);
    console.log(`💾 Saved debug data to group_contacts_debug.csv (${records.length} entries)`);

  } catch (error) {
    console.error("Error during extraction:", error);
  } finally {
    await client.close();
    process.exit();
  }
}).catch(async (error) => {
  console.error("Failed to create WhatsApp client:", error);
  console.log("Please make sure Chrome is installed and try again.");
  process.exit(1);
});



