"""
Settings for the UnRayNeo project.
"""
import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Directory for storing secret files
SECRET_DIR = BASE_DIR / "secret"

# Directory for storing screenshots
SCREENSHOTS_DIR = SECRET_DIR / "screenshots"

# Temporary directory for easy access to screenshots
TMP_SCREENSHOTS_DIR = Path("/tmp/unrayneo-secret-screenshots")

# ADB settings
ADB_DEVICE_IP = "192.168.2.59"  # Update this with the current device IP
ADB_PORT = 5555

# Screenshot settings
SCREENSHOT_REMOTE_PATH = "/sdcard/screenshot.png"
