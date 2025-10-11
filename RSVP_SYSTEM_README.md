# RSVP System Documentation

## Overview
The RSVP system allows members to register for events and enables administrators to manage approvals with bulk operations and automated notifications.

## Features

### For Members
- **RSVP Form**: Complete form with personal details, emergency contacts, and dietary requirements
- **Status Tracking**: View RSVP status (pending, approved, rejected)
- **Acceptance Codes**: Unique codes for approved RSVPs
- **Email/SMS Notifications**: Automatic notifications for status changes

### For Administrators
- **Bulk Approval**: Approve/reject multiple RSVPs at once (10, 20, 30+)
- **Filtering**: Filter RSVPs by event and status
- **Detailed View**: Complete RSVP information in modal popups
- **Acceptance Code Generation**: Automatic unique code generation
- **Notification Management**: Email and SMS notifications sent automatically

## Setup Instructions

### 1. Database Migration
Run the migration script to add the RSVP table:
```bash
python migrate_rsvp.py
```

### 2. Email Configuration
Create a `config.py` file in your project root:
```python
# Email Configuration (Gmail example)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'your-email@gmail.com'
SMTP_PASSWORD = 'your-app-password'  # Use App Password for Gmail
FROM_EMAIL = 'your-email@gmail.com'
```

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password in your config

### 3. SMS Configuration (Twilio)
Add to your `config.py`:
```python
# SMS Configuration
TWILIO_ACCOUNT_SID = 'your-twilio-account-sid'
TWILIO_AUTH_TOKEN = 'your-twilio-auth-token'
TWILIO_PHONE_NUMBER = '+1234567890'
```

**Twilio Setup:**
1. Sign up at https://www.twilio.com/
2. Get your Account SID and Auth Token
3. Purchase a phone number
4. Verify your phone number for testing

### 4. Update Flask App Configuration
Add to your Flask app configuration:
```python
# Load configuration from config.py
try:
    from config import *
    app.config.update({
        'SMTP_SERVER': SMTP_SERVER,
        'SMTP_PORT': SMTP_PORT,
        'SMTP_USERNAME': SMTP_USERNAME,
        'SMTP_PASSWORD': SMTP_PASSWORD,
        'FROM_EMAIL': FROM_EMAIL,
        'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
        'TWILIO_AUTH_TOKEN': TWILIO_AUTH_TOKEN,
        'TWILIO_PHONE_NUMBER': TWILIO_PHONE_NUMBER,
    })
except ImportError:
    print("Warning: config.py not found. Email/SMS notifications will not work.")
```

## Usage Guide

### For Members

#### 1. RSVP to an Event
1. Go to the Events page
2. Click "RSVP" on any upcoming event
3. Fill out the RSVP form with:
   - Personal information (name, email, phone)
   - Course and year of study
   - Emergency contact details
   - Dietary requirements
   - Additional notes
4. Submit the form

#### 2. Check RSVP Status
1. After submitting, you'll be redirected to your RSVP status page
2. You can also access it via: `/events/{event_id}/rsvp/status?email={your_email}`
3. Status will show as:
   - **Pending**: Under review
   - **Approved**: You'll receive an acceptance code
   - **Rejected**: Unable to accommodate

#### 3. For Approved RSVPs
- Save your acceptance code
- Bring the code to the event for verification
- You'll receive email/SMS confirmation

### For Administrators

#### 1. Access RSVP Management
1. Log in as admin
2. Go to Admin Panel → RSVP Management
3. View all RSVPs with filtering options

#### 2. Individual Approval/Rejection
1. Click the green checkmark to approve
2. Click the red X to reject
3. Confirm the action
4. Notification will be sent automatically

#### 3. Bulk Operations
1. Select multiple RSVPs using checkboxes
2. Click "Approve Selected" or "Reject Selected"
3. Confirm the bulk action
4. All selected RSVPs will be processed
5. Notifications sent to all affected members

#### 4. Filtering Options
- **By Event**: Filter RSVPs for specific events
- **By Status**: Show only pending, approved, or rejected RSVPs
- **Combined**: Use both filters together

## Database Schema

### RSVP Table
```sql
CREATE TABLE rsvp (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL,
    member_id INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    acceptance_code VARCHAR(10) UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    course VARCHAR(100),
    year VARCHAR(20),
    dietary_requirements TEXT,
    emergency_contact VARCHAR(100),
    emergency_phone VARCHAR(20),
    additional_notes TEXT,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_at DATETIME,
    approved_by INTEGER,
    FOREIGN KEY (event_id) REFERENCES event (id),
    FOREIGN KEY (member_id) REFERENCES member (id),
    FOREIGN KEY (approved_by) REFERENCES user (id)
);
```

## API Endpoints

### Public Endpoints
- `GET /events/{event_id}/rsvp` - RSVP form
- `POST /events/{event_id}/rsvp` - Submit RSVP
- `GET /events/{event_id}/rsvp/status` - Check RSVP status

### Admin Endpoints
- `GET /admin/rsvps` - RSVP management page
- `GET /admin/rsvps/approve/{rsvp_id}` - Approve individual RSVP
- `GET /admin/rsvps/reject/{rsvp_id}` - Reject individual RSVP
- `POST /admin/rsvps/bulk-approve` - Bulk approve RSVPs
- `POST /admin/rsvps/bulk-reject` - Bulk reject RSVPs

## Notification Templates

### Email Templates

#### Approved RSVP
```
Subject: RSVP Approved - {Event Title}

Dear {Full Name},

Your RSVP for "{Event Title}" has been approved!

Event Details:
- Date: {Event Date}
- Location: {Event Location}

Your Acceptance Code: {Acceptance Code}

Please bring this code with you to the event for verification.

Best regards,
Digital Club Team
```

#### Rejected RSVP
```
Subject: RSVP Update - {Event Title}

Dear {Full Name},

Thank you for your interest in "{Event Title}".

Unfortunately, we are unable to accommodate your RSVP at this time due to capacity limitations.

We appreciate your understanding and hope to see you at future events.

Best regards,
Digital Club Team
```

### SMS Templates

#### Approved RSVP
```
RSVP Approved! Event: {Event Title} on {Event Date}. Your code: {Acceptance Code}. Bring this code to the event.
```

#### Rejected RSVP
```
RSVP Update: Unfortunately, we cannot accommodate your RSVP for {Event Title} due to capacity limitations. We hope to see you at future events!
```

## Troubleshooting

### Common Issues

#### 1. Email Not Sending
- Check SMTP credentials in config.py
- Verify Gmail App Password is correct
- Check firewall/network restrictions
- Review application logs for error messages

#### 2. SMS Not Sending
- Verify Twilio credentials
- Check phone number format (should include country code)
- Ensure Twilio account has sufficient credits
- Verify phone number is verified in Twilio

#### 3. Database Issues
- Run migration script: `python migrate_rsvp.py`
- Check database permissions
- Verify SQLite file exists and is writable

#### 4. RSVP Form Issues
- Check JavaScript console for errors
- Verify form validation is working
- Check server logs for submission errors

### Logging
The system logs all notification attempts. Check your application logs for:
- Email sending success/failure
- SMS sending success/failure
- Database operation errors
- Form submission issues

## Security Considerations

1. **Email Credentials**: Store in environment variables or secure config file
2. **SMS Credentials**: Never commit Twilio credentials to version control
3. **Input Validation**: All form inputs are validated server-side
4. **SQL Injection**: Using SQLAlchemy ORM prevents SQL injection
5. **XSS Protection**: Templates use Jinja2 auto-escaping

## Future Enhancements

1. **QR Code Generation**: Generate QR codes for acceptance codes
2. **Event Capacity**: Add capacity limits to events
3. **Waitlist**: Automatic waitlist for over-capacity events
4. **Reminder Notifications**: Send reminders before events
5. **Analytics**: Track RSVP statistics and trends
6. **Mobile App**: Native mobile app for RSVP management
7. **Calendar Integration**: Sync with Google Calendar/Outlook
8. **Multi-language Support**: Support for multiple languages

## Support

For technical support or questions about the RSVP system:
1. Check this documentation first
2. Review application logs
3. Test with sample data
4. Contact the development team

---

**Note**: This RSVP system is designed to be flexible and can be customized for different event types and requirements. The notification system supports multiple providers and can be extended as needed.
