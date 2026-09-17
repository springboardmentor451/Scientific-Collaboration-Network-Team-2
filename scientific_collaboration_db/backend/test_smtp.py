"""
Standalone SMTP connectivity test — run this directly to check whether
Gmail's SMTP server is reachable from this machine/network, completely
separate from the FastAPI app. Helps confirm whether login hangs because
of a blocked outbound connection to smtp.gmail.com:587.

Usage:
    python test_smtp.py
"""
import smtplib
import sys

HOST = "smtp.gmail.com"
PORT = 587
USERNAME = "art.ishi.03@gmail.com"   # change if needed
PASSWORD = "fdfrluwmclmrmevv"  # do NOT commit/share this

print(f"Connecting to {HOST}:{PORT} ...")
try:
    with smtplib.SMTP(HOST, PORT, timeout=10) as server:
        print("Connected. Starting TLS...")
        server.starttls()
        print("TLS started. Logging in...")
        server.login(USERNAME, PASSWORD)
        print("SUCCESS: SMTP login worked. Your network can reach Gmail's SMTP server.")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    sys.exit(1)