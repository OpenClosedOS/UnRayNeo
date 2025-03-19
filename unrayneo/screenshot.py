"""
Module for capturing screenshots from RanNeo X2 AR glasses.
"""
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

import settings


def ensure_directory_exists(directory: Path) -> None:
    """Ensure that the specified directory exists."""
    directory.mkdir(parents=True, exist_ok=True)


def get_date_time_paths() -> tuple[str, str]:
    """Get the current date and time formatted for directory and file names."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")
    return date_str, time_str


def copy_to_tmp_dir(screenshot_path: Path) -> Path:
    """
    Copy the screenshot to the temporary directory for easy access.
    
    Args:
        screenshot_path: Path to the original screenshot.
        
    Returns:
        Path to the copied screenshot in the temporary directory.
    """
    # Ensure the temporary directory exists
    ensure_directory_exists(settings.TMP_SCREENSHOTS_DIR)
    
    # Create a path in the temporary directory with the same filename
    tmp_path = settings.TMP_SCREENSHOTS_DIR / screenshot_path.name
    
    # Copy the file
    shutil.copy2(screenshot_path, tmp_path)
    print(f"Screenshot copied to: {tmp_path}")
    
    return tmp_path


def capture_screenshot(output_path: Path = None) -> Path:
    """
    Capture a screenshot from the RanNeo X2 AR glasses and save it to the specified path.
    
    Args:
        output_path: Optional path where the screenshot should be saved.
                    If not provided, it will be saved to the default location.
    
    Returns:
        Path to the saved screenshot.
    """
    date_str, time_str = get_date_time_paths()
    
    # If no output path is provided, use the default location
    if output_path is None:
        screenshot_dir = settings.SCREENSHOTS_DIR / date_str
        ensure_directory_exists(screenshot_dir)
        output_path = screenshot_dir / f"{time_str}.png"
    
    # Ensure the parent directory exists
    ensure_directory_exists(output_path.parent)
    
    # Capture the screenshot
    try:
        # Take screenshot on the device
        subprocess.run(
            ["adb", "shell", "screencap", "-p", settings.SCREENSHOT_REMOTE_PATH],
            check=True,
            capture_output=True,
        )
        
        # Pull the screenshot to the local machine
        subprocess.run(
            ["adb", "pull", settings.SCREENSHOT_REMOTE_PATH, str(output_path)],
            check=True,
            capture_output=True,
        )
        
        print(f"Screenshot saved to: {output_path}")
        
        # Copy the screenshot to the temporary directory
        tmp_path = copy_to_tmp_dir(output_path)
        
        return output_path
    
    except subprocess.CalledProcessError as e:
        print(f"Error capturing screenshot: {e}")
        print(f"Command output: {e.stdout.decode()}")
        print(f"Command error: {e.stderr.decode()}")
        raise
