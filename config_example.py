# Email Configuration
# For Gmail, use these settings:
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'your-email@gmail.com'
SMTP_PASSWORD = 'your-app-password'  # Use App Password for Gmail
FROM_EMAIL = 'your-email@gmail.com'

# For other email providers, adjust accordingly:
# Outlook: smtp-mail.outlook.com
# Yahoo: smtp.mail.yahoo.com

# SMS Configuration (Twilio)
# Sign up at https://www.twilio.com/ and get these credentials:
TWILIO_ACCOUNT_SID = 'your-twilio-account-sid'
TWILIO_AUTH_TOKEN = 'your-twilio-auth-token'
TWILIO_PHONE_NUMBER = '+1234567890'  # Your Twilio phone number

# Alternative SMS providers:
# - AWS SNS
# - MessageBird
# - Vonage (formerly Nexmo)

# Instructions:
# 1. Copy this file to config.py in your project root
# 2. Replace the placeholder values with your actual credentials
# 3. Make sure config.py is in your .gitignore file to keep credentials secure
# 4. For Gmail, enable 2-factor authentication and generate an App Password
# 5. For Twilio, verify your phone number and get a Twilio phone number
