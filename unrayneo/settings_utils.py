"""
Module for interacting with Android settings on RanNeo X2 AR glasses.
"""
import subprocess
from enum import Enum
from typing import Optional


class SettingsPage(Enum):
    """Enum representing different settings pages that can be opened."""
    MAIN = "com.android.settings/.Settings"
    DEVELOPER_OPTIONS = "android.settings.APPLICATION_DEVELOPMENT_SETTINGS"
    ABOUT_PHONE = "android.settings.DEVICE_INFO_SETTINGS"
    WIFI = "android.settings.WIFI_SETTINGS"
    BLUETOOTH = "android.settings.BLUETOOTH_SETTINGS"
    DISPLAY = "android.settings.DISPLAY_SETTINGS"
    APPS = "android.settings.APPLICATION_SETTINGS"
    BATTERY = "android.settings.BATTERY_SAVER_SETTINGS"
    STORAGE = "android.settings.INTERNAL_STORAGE_SETTINGS"


def open_settings(page: Optional[SettingsPage] = SettingsPage.MAIN) -> None:
    """
    Open Android settings on the RanNeo X2 AR glasses.
    
    Args:
        page: The settings page to open. Defaults to the main settings page.
    
    Raises:
        subprocess.CalledProcessError: If the ADB command fails.
    """
    try:
        if page == SettingsPage.MAIN:
            # Open main settings using explicit component name
            command = ["adb", "shell", "am", "start", "-n", page.value]
        else:
            # Open specific settings pages using action
            command = ["adb", "shell", "am", "start", "-a", page.value]
        
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        
        print(f"Opened Android settings: {page.name}")
        if "Starting" in result.stdout:
            print(f"Command output: {result.stdout.strip()}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error opening settings: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        raise
