"""
generate.py - OTP Generation Module
Generates random OTPs and manages OTP verification with expiry.
"""

import random
import time

# Store OTPs with their creation time: {phone_number: (otp, timestamp)}
_otp_store = {}

# OTP validity duration in seconds (5 minutes)
OTP_EXPIRY_SECONDS = 300


def generate_otp(length=6):
    """
    Generate a random numeric OTP of the given length.
    
    
    Args:
        length (int): Number of digits in the OTP (default: 6)
    
    Returns:
        str: A string of random digits
    """
    if length < 4 or length > 8:
        raise ValueError("OTP length must be between 4 and 8 digits.")
    
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp


def store_otp(phone_number, otp):
    """
    Store an OTP for a given phone number with the current timestamp.
    
    Args:
        phone_number (str): The student's phone number
        otp (str): The generated OTP
    """
    _otp_store[phone_number] = (otp, time.time())


def verify_otp(phone_number, entered_otp):
    """
    Verify the entered OTP against the stored OTP for a phone number.
    
    Args:
        phone_number (str): The student's phone number
        entered_otp (str): The OTP entered by the student
    
    Returns:
        tuple: (bool, str) - (success, message)
    """
    if phone_number not in _otp_store:
        return False, "No OTP was generated for this phone number."
    
    stored_otp, timestamp = _otp_store[phone_number]
    
    # Check if OTP has expired
    elapsed = time.time() - timestamp
    if elapsed > OTP_EXPIRY_SECONDS:
        del _otp_store[phone_number]
        return False, f"OTP has expired (valid for {OTP_EXPIRY_SECONDS // 60} minutes). Please request a new one."
    
    # Check if OTP matches
    if entered_otp == stored_otp:
        del _otp_store[phone_number]  # OTP is single-use
        return True, "OTP verified successfully!"
    else:
        return False, "Incorrect OTP. Please try again."


def clear_expired_otps():
    """Remove all expired OTPs from the store."""
    current_time = time.time()
    expired = [
        phone for phone, (_, timestamp) in _otp_store.items()
        if current_time - timestamp > OTP_EXPIRY_SECONDS
    ]
    for phone in expired:
        del _otp_store[phone]


if __name__ == "__main__":
    # Quick test
    test_otp = generate_otp()
    print(f"Generated OTP: {test_otp}")
    store_otp("9876543210", test_otp)
    
    success, msg = verify_otp("9876543210", test_otp)
    print(f"Verification: {success} - {msg}")
    
    success, msg = verify_otp("9876543210", test_otp)
    print(f"Re-verify (should fail): {success} - {msg}")