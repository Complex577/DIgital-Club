import base64
import json
import os

import dotenv
import requests
from flask import current_app

dotenv.load_dotenv()
# If you are in need of this credentials contact the project managers for assistance
# print(api_key, secret_key)
# Official Beem SMS API endpoint
URL = 'https://apisms.beem.africa/v1/send'

# Replace these with your actual Beem API credentials
content_type = 'application/json'

def send_sms(phone_number, message):
    """
    Sends an SMS using the Beem SMS gateway API v1 with certificate verification enabled.
    """
    api_key = os.getenv('BEEM_API_KEY')
    secret_key = os.getenv('BEEM_SECRET_KEY')
    if not api_key or not secret_key:
        current_app.logger.error(
            "BEEM credentials are missing. Set BEEM_API_KEY and BEEM_SECRET_KEY in .env."
        )
        return False

    response = None  # ensure defined for logging in finally
    payload = {
        "source_addr": "KIUTCLUBS",
        "encoding": 0,
        "schedule_time": "",
        "message": message,
        "recipients": [
            {"recipient_id": "1", "dest_addr": phone_number}
        ]
    }
    # Beem requires HTTP Basic Authentication with api_key:secret_key as the credentials
    auth_value = base64.b64encode(f"{api_key}:{secret_key}".encode("utf-8")).decode("utf-8")
    headers = {
        "Content-Type": content_type,
        "Authorization": f"Basic {auth_value}",
    }
    try:
        response = requests.post(
            url=URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=10  # Reasonable timeout to avoid hanging
        )
        response.raise_for_status()  # Will raise for 4xx/5xx responses
        return response.ok
    except requests.exceptions.SSLError as ssl_err:
        current_app.logger.error(f"SSL Error: {ssl_err}. Please ensure your system has up-to-date CA certificates.")
        return False
    except requests.exceptions.RequestException as e:
        current_app.logger.error("Error sending SMS: %s", e)
        return False
    except Exception as e:
        current_app.logger.error("Unexpected SMS error: %s", e)
        return False
    finally:
        # Only log status if a response was obtained
        if response is not None:
            current_app.logger.info("SMS API response status: %s", response.status_code)

if __name__ == "__main__":
    print(send_sms("+255749300606", "Message We received a request to reset your password. Use the link below to set a new one: http://digitalclub.kiut.ac.tz/auth/reset-password/eyJ1c2VyX2lkIjo4LCJlbWFpbCI6InNuYXZpZHV4Lm9mZmljaWFsQGdtYWlsLmNvbSJ9.aW6Fkg.9q4VOSCKSitj2AvKaiUduVWwpEE"))
