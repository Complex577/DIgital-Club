const { Client, LocalAuth } = require('whatsapp-web.js');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const qrcode = require('qrcode-terminal');

const client = new Client({
  authStrategy: new LocalAuth({
    clientId: "wwjs-session"
  }),
  puppeteer: {
    headless: false,
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
    timeout: 60000
  }
});

client.on('qr', (qr) => {
  console.log('📱 Scan this QR code with your WhatsApp mobile app:');
  qrcode.generate(qr, { small: true });
});

client.on('ready', async () => {
  console.log('✅ WhatsApp Web is ready!');
  
  try {
    const csvWriter = createCsvWriter({
      path: 'group_contacts_wwjs.csv',
      header: [
        { id: 'group', title: 'group' },
        { id: 'phone', title: 'phone' },
      ],
    });

    const records = [];
    
    // Wait for WhatsApp to fully load
    console.log('⏳ Waiting for WhatsApp to load completely...');
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Get all chats (groups)
    const chats = await client.getChats();
    const groups = chats.filter(chat => chat.isGroup);
    
    console.log(`📊 Found ${groups.length} groups.`);
    
    let processedGroups = 0;
    let skippedGroups = 0;
    let totalMembers = 0;

    for (const group of groups) {
      try {
        console.log(`\n🔍 Processing: ${group.name}`);
        
        // Validate group
        if (!group || !group.id) {
          console.log(`⚠️  Skipping group ${group?.name || 'Unknown'} - no valid ID`);
          skippedGroups++;
          continue;
        }

        // Get group participants with retry logic
        let participants = [];
        let retryCount = 0;
        const maxRetries = 3;
        
        while (retryCount < maxRetries) {
          try {
            participants = await group.participants;
            break;
          } catch (error) {
            retryCount++;
            console.log(`   ⚠️  Attempt ${retryCount} failed, retrying in 3 seconds...`);
            if (retryCount < maxRetries) {
              await new Promise(resolve => setTimeout(resolve, 3000));
            } else {
              throw error;
            }
          }
        }

        // Validate participants array
        if (!Array.isArray(participants)) {
          console.log(`   ⚠️  Skipping group ${group.name} - invalid participants data`);
          skippedGroups++;
          continue;
        }

        let groupMemberCount = 0;
        console.log(`   📱 Found ${participants.length} participants`);

        for (const participant of participants) {
          try {
            // Skip if participant is null/undefined
            if (!participant) {
              console.log(`   ⚠️  Skipping null participant in group ${group.name}`);
              continue;
            }
            
            // Try multiple ways to extract phone number
            let phone = null;
            let extractionMethod = '';
            
            // Method 1: participant.id._serialized
            if (participant.id && participant.id._serialized) {
              phone = participant.id._serialized.replace('@c.us', '').replace('@g.us', '');
              extractionMethod = 'participant.id._serialized';
            }
            // Method 2: participant.id as string
            else if (participant.id && typeof participant.id === 'string') {
              phone = participant.id.replace('@c.us', '').replace('@g.us', '');
              extractionMethod = 'participant.id (string)';
            }
            // Method 3: participant.id.user
            else if (participant.id && participant.id.user) {
              phone = participant.id.user;
              extractionMethod = 'participant.id.user';
            }
            // Method 4: participant.contact
            else if (participant.contact && participant.contact.id) {
              phone = participant.contact.id.replace('@c.us', '').replace('@g.us', '');
              extractionMethod = 'participant.contact.id';
            }
            // Method 5: participant.phone
            else if (participant.phone) {
              phone = participant.phone;
              extractionMethod = 'participant.phone';
            }
            // Method 6: participant.number
            else if (participant.number) {
              phone = participant.number;
              extractionMethod = 'participant.number';
            }
            
            // If we found a phone number, validate and add it
            if (phone && typeof phone === 'string' && phone.trim() !== '') {
              // Clean the phone number
              phone = phone.trim().replace(/[^\d]/g, ''); // Keep only digits
              
              // Basic validation - should be at least 7 digits
              if (phone.length >= 7) {
                records.push({ 
                  group: group.name, 
                  phone: phone.trim() 
                });
                groupMemberCount++;
              } else {
                console.log(`   ⚠️  Skipping participant with invalid phone length (${phone.length}): ${phone}`);
              }
            } else {
              console.log(`   ⚠️  Skipping participant - no valid phone found. Participant data: ${JSON.stringify(participant)}`);
            }
          } catch (memberError) {
            console.log(`   ⚠️  Error processing participant in group ${group.name}: ${memberError.message}`);
            continue;
          }
        }

        console.log(`   ✅ Extracted ${groupMemberCount} valid contacts from ${group.name}`);
        processedGroups++;
        totalMembers += groupMemberCount;

        // Rate limiting - wait between groups
        await new Promise(resolve => setTimeout(resolve, 2000));

      } catch (error) {
        console.log(`   ❌ Error processing group ${group.name}: ${error.message}`);
        skippedGroups++;
        continue;
      }
    }

    // Write to CSV
    await csvWriter.writeRecords(records);
    
    console.log(`\n📊 EXTRACTION SUMMARY:`);
    console.log(`✅ Processed groups: ${processedGroups}`);
    console.log(`⚠️  Skipped groups: ${skippedGroups}`);
    console.log(`📱 Total contacts extracted: ${totalMembers}`);
    console.log(`💾 Saved contacts to group_contacts_wwjs.csv (${records.length} entries)`);

  } catch (error) {
    console.error('❌ Error during extraction:', error);
  } finally {
    await client.destroy();
    process.exit();
  }
});

client.on('auth_failure', msg => {
  console.error('❌ Authentication failed:', msg);
  process.exit(1);
});

client.on('disconnected', (reason) => {
  console.log('⚠️  Client was logged out:', reason);
  process.exit(1);
});

// Start the client
client.initialize().catch(error => {
  console.error('❌ Failed to initialize WhatsApp client:', error);
  process.exit(1);
});
