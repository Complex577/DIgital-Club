const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const { Boom } = require('@hapi/boom');
const fs = require('fs');
const P = require('pino');

async function startBaileysExtraction() {
  const { state, saveCreds } = await useMultiFileAuthState('./baileys-session');
  
  const csvWriter = createCsvWriter({
    path: 'group_contacts_baileys.csv',
    header: [
      { id: 'group', title: 'group' },
      { id: 'phone', title: 'phone' },
    ],
  });

  const records = [];
  
  const sock = makeWASocket({
    auth: state,
    printQRInTerminal: true,
    logger: P({ level: 'silent' }),
    browser: ['WhatsApp Group Extractor', 'Chrome', '1.0.0'],
    connectTimeoutMs: 60000,
    keepAliveIntervalMs: 30000,
    retryRequestDelayMs: 250,
    markOnlineOnConnect: false,
    generateHighQualityLinkPreview: false,
    getMessage: async (key) => {
      return {
        conversation: 'Hello!'
      };
    }
  });

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;
    
    if (qr) {
      console.log('📱 Scan this QR code with your WhatsApp mobile app:');
    }
    
    if (connection === 'close') {
      const shouldReconnect = (lastDisconnect?.error instanceof Boom)?.output?.statusCode !== DisconnectReason.loggedOut;
      console.log('⚠️  Connection closed due to ', lastDisconnect?.error, ', reconnecting ', shouldReconnect);
      
      if (shouldReconnect) {
        startBaileysExtraction();
      } else {
        console.log('❌ Connection closed permanently');
        process.exit(1);
      }
    } else if (connection === 'open') {
      console.log('✅ WhatsApp Web is ready!');
      
      try {
        // Wait for WhatsApp to fully load
        console.log('⏳ Waiting for WhatsApp to load completely...');
        await new Promise(resolve => setTimeout(resolve, 5000));

        // Get all chats
        const chats = await sock.groupFetchAllParticipating();
        const groups = Object.values(chats);
        
        console.log(`📊 Found ${groups.length} groups.`);
        
        let processedGroups = 0;
        let skippedGroups = 0;
        let totalMembers = 0;

        for (const group of groups) {
          try {
            console.log(`\n🔍 Processing: ${group.subject}`);
            
            // Validate group
            if (!group || !group.id) {
              console.log(`⚠️  Skipping group ${group?.subject || 'Unknown'} - no valid ID`);
              skippedGroups++;
              continue;
            }

            // Get group participants
            let participants = [];
            let retryCount = 0;
            const maxRetries = 3;
            
            while (retryCount < maxRetries) {
              try {
                const groupInfo = await sock.groupMetadata(group.id);
                participants = groupInfo.participants || [];
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
              console.log(`   ⚠️  Skipping group ${group.subject} - invalid participants data`);
              skippedGroups++;
              continue;
            }

            let groupMemberCount = 0;
            console.log(`   📱 Found ${participants.length} participants`);

            for (const participant of participants) {
              try {
                // Skip if participant is null/undefined
                if (!participant) {
                  console.log(`   ⚠️  Skipping null participant in group ${group.subject}`);
                  continue;
                }
                
                // Try multiple ways to extract phone number
                let phone = null;
                let extractionMethod = '';
                
                // Method 1: participant.id as string
                if (participant.id && typeof participant.id === 'string') {
                  phone = participant.id.replace('@c.us', '').replace('@g.us', '');
                  extractionMethod = 'participant.id (string)';
                }
                // Method 2: participant.id.user
                else if (participant.id && participant.id.user) {
                  phone = participant.id.user;
                  extractionMethod = 'participant.id.user';
                }
                // Method 3: participant.contact
                else if (participant.contact && participant.contact.id) {
                  phone = participant.contact.id.replace('@c.us', '').replace('@g.us', '');
                  extractionMethod = 'participant.contact.id';
                }
                // Method 4: participant.phone
                else if (participant.phone) {
                  phone = participant.phone;
                  extractionMethod = 'participant.phone';
                }
                // Method 5: participant.number
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
                      group: group.subject, 
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
                console.log(`   ⚠️  Error processing participant in group ${group.subject}: ${memberError.message}`);
                continue;
              }
            }

            console.log(`   ✅ Extracted ${groupMemberCount} valid contacts from ${group.subject}`);
            processedGroups++;
            totalMembers += groupMemberCount;

            // Rate limiting - wait between groups
            await new Promise(resolve => setTimeout(resolve, 2000));

          } catch (error) {
            console.log(`   ❌ Error processing group ${group.subject}: ${error.message}`);
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
        console.log(`💾 Saved contacts to group_contacts_baileys.csv (${records.length} entries)`);

      } catch (error) {
        console.error('❌ Error during extraction:', error);
      } finally {
        await sock.logout();
        process.exit();
      }
    }
  });

  sock.ev.on('creds.update', saveCreds);
}

// Start the extraction
startBaileysExtraction().catch(error => {
  console.error('❌ Failed to start Baileys extraction:', error);
  process.exit(1);
});
