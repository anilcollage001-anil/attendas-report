"""
text.py - SMS / OTP Delivery Module
Handles sending OTP messages to students' phone numbers.

By default, uses CONSOLE MODE (prints OTP to terminal for testing).
To use real SMS via Twilio, set USE_TWILIO = True and fill in your credentials.
"""

# ============================================================
#  CONFIGURATION - Switch between Console and Twilio
# ============================================================

USE_TWILIO = False  # Set to True to send real SMS via Twilio

# Twilio credentials (fill these in if USE_TWILIO = True)
TWILIO_ACCOUNT_SID = "your_account_sid_here"
TWILIO_AUTH_TOKEN = "your_auth_token_here"
TWILIO_PHONE_NUMBER = "+1234567890"  # Your Twilio phone number


def send_otp_message(phone_number, otp):
    """
    Send an OTP message to the given phone number.
    
    Args:
        phone_number (str): Recipient's phone number (e.g., "9876543210")
        otp (str): The OTP to send
    
    Returns:
        tuple: (bool, str) - (success, message)
    """
    message_body = f"Your OTP for attendance verification is: {otp}. Valid for 5 minutes. Do not share with anyone."
    
    if USE_TWILIO:
        return _send_via_twilio(phone_number, message_body)
    else:
        return _send_via_console(phone_number, message_body, otp)


def _send_via_console(phone_number, message_body, otp):
    """
    Console mode: Print OTP to terminal (for testing/development).
    
    Args:
        phone_number (str): Recipient's phone number
        message_body (str): Full message text
        otp (str): The OTP code
    
    Returns:
        tuple: (bool, str)
    """
    print("\n" + "=" * 50)
    print("  📱 SMS SIMULATION (Console Mode)")
    print("=" * 50)
    print(f"  To:      +91-{phone_number}")
    print(f"  Message: {message_body}")
    print(f"  OTP:     {otp}")
    print("=" * 50 + "\n")
    
    return True, f"OTP sent to +91-{phone_number} (console mode)"


def _send_via_twilio(phone_number, message_body):
    """
    Send SMS via Twilio API.
    
    Args:
        phone_number (str): Recipient's phone number
        message_body (str): Full message text
    
    Returns:
        tuple: (bool, str)
    """
    try:
        from twilio.rest import Client
    except ImportError:
        return False, "Twilio package not installed. Run: pip install twilio"
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Ensure phone number has country code
        if not phone_number.startswith("+"):
            phone_number = "+91" + phone_number  # Default to India (+91)
        
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        return True, f"SMS sent successfully! SID: {message.sid}"
    
    except Exception as e:
        return False, f"Failed to send SMS: {str(e)}"


if __name__ == "__main__":
    # Test console mode
    success, msg = send_otp_message("9876543210", "123456")
    print(f"Result: {success} - {msg}")