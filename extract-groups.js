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
      path: 'group_contacts.csv',
      header: [
        { id: 'group', title: 'group' },
        { id: 'phone', title: 'phone' },
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

    for (const group of groups) {
      try {
        console.log(`Extracting contacts from: ${group.name}`);
        
        // Validate group has an id
        if (!group || !group.id) {
          console.log(`Skipping group ${group?.name || 'Unknown'} - no valid ID`);
          skippedGroups++;
          continue;
        }
        
        const groupId = group.id;
        const groupMembers = await client.getGroupMembers(groupId);

        // Validate groupMembers is an array
        if (!Array.isArray(groupMembers)) {
          console.log(`Skipping group ${group.name} - invalid members data`);
          skippedGroups++;
          continue;
        }

        let groupMemberCount = 0;
        for (const member of groupMembers) {
          try {
            // Skip if member is null/undefined
            if (!member) {
              console.log(`Skipping null member in group ${group.name}`);
              continue;
            }
            
            // Try multiple ways to extract phone number
            let phone = null;
            let extractionMethod = '';
            
            // Method 1: member.id as string
            if (member.id && typeof member.id === 'string') {
              phone = member.id.replace('@c.us', '').replace('@g.us', '');
              extractionMethod = 'member.id (string)';
            }
            // Method 2: member.id._serialized
            else if (member.id && member.id._serialized) {
              phone = member.id._serialized.replace('@c.us', '').replace('@g.us', '');
              extractionMethod = 'member.id._serialized';
            }
            // Method 3: member.id.user
            else if (member.id && member.id.user) {
              phone = member.id.user;
              extractionMethod = 'member.id.user';
            }
            // Method 4: member.contact
            else if (member.contact && member.contact.id) {
              phone = member.contact.id.replace('@c.us', '').replace('@g.us', '');
              extractionMethod = 'member.contact.id';
            }
            // Method 5: member.phone
            else if (member.phone) {
              phone = member.phone;
              extractionMethod = 'member.phone';
            }
            // Method 6: member.number
            else if (member.number) {
              phone = member.number;
              extractionMethod = 'member.number';
            }
            
            // If we found a phone number, validate and add it
            if (phone && typeof phone === 'string' && phone.trim() !== '') {
              // Clean the phone number
              phone = phone.trim().replace(/[^\d]/g, ''); // Keep only digits
              
              // Basic validation - should be at least 7 digits
              if (phone.length >= 7) {
                records.push({ group: group.name, phone });
                groupMemberCount++;
              } else {
                console.log(`Skipping member with invalid phone length (${phone.length}): ${phone}`);
              }
            } else {
              console.log(`Skipping member - no valid phone found. Member data: ${JSON.stringify(member)}`);
            }
          } catch (memberError) {
            console.log(`Error processing member in group ${group.name}: ${memberError.message}`);
            continue; // Skip this member and continue with others
          }
        }
        
        console.log(`✅ Extracted ${groupMemberCount} contacts from ${group.name}`);
        processedGroups++;
        totalMembers += groupMemberCount;
        
      } catch (error) {
        console.log(`Error extracting from group ${group.name}: ${error.message}`);
        skippedGroups++;
        continue; // Skip this group and continue with others
      }
    }

    // Write to CSV
    await csvWriter.writeRecords(records);
    console.log(`\n📊 EXTRACTION SUMMARY:`);
    console.log(`✅ Processed groups: ${processedGroups}`);
    console.log(`⚠️  Skipped groups: ${skippedGroups}`);
    console.log(`📱 Total contacts extracted: ${totalMembers}`);
    console.log(`💾 Saved contacts to group_contacts.csv (${records.length} entries)`);

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
