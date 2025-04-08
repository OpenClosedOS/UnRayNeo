"""
Raw Partition Dump Utility for RanNeo X2 AR Glasses

This script attempts to dump raw partition images from the RanNeo X2 AR glasses.
It identifies all block devices and attempts to read their raw contents using dd.
All data is saved to the secret directory to protect potentially sensitive information.
"""
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import shutil
from typing import List, Dict, Any, Optional, Tuple

# Import project settings
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import settings

# Create timestamp for the dump directory
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
DUMP_DIR = settings.SECRET_DIR / f"raw_partition_dump_{TIMESTAMP}"


def setup_dump_directory() -> Path:
    """Create and return the dump directory path."""
    dump_dir = DUMP_DIR
    dump_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (dump_dir / "images").mkdir(exist_ok=True)
    (dump_dir / "info").mkdir(exist_ok=True)
    
    return dump_dir


def run_adb_command(command: List[str], check: bool = True) -> Tuple[int, str, str]:
    """
    Run an ADB command and return the exit code, stdout, and stderr.
    
    Args:
        command: The ADB command to run as a list of strings.
        check: Whether to raise an exception if the command fails.
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    
    Raises:
        subprocess.CalledProcessError: If check is True and the command fails.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")
        return e.returncode, e.stdout, e.stderr


def save_to_file(path: Path, content: str) -> None:
    """Save content to a file."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def identify_block_devices(dump_dir: Path) -> List[str]:
    """
    Identify all block devices on the device.
    
    Returns:
        List of block device paths
    """
    print("Identifying block devices...")
    info_dir = dump_dir / "info"
    
    # Get list of block devices
    _, block_devices, _ = run_adb_command(["adb", "shell", "ls", "-la", "/dev/block/"], check=False)
    save_to_file(info_dir / "block_devices.txt", block_devices)
    
    # Get more detailed information
    _, block_devices_by_name, _ = run_adb_command(["adb", "shell", "ls", "-la", "/dev/block/by-name/"], check=False)
    save_to_file(info_dir / "block_devices_by_name.txt", block_devices_by_name)
    
    # Get partition information
    _, partitions, _ = run_adb_command(["adb", "shell", "cat", "/proc/partitions"], check=False)
    save_to_file(info_dir / "proc_partitions.txt", partitions)
    
    # Parse block devices
    block_device_paths = []
    for line in block_devices.splitlines():
        if "brw" in line:  # Block device
            parts = line.split()
            if len(parts) >= 10:
                device_name = parts[-1]
                if not device_name.startswith("loop"):  # Skip loop devices
                    block_device_paths.append(f"/dev/block/{device_name}")
    
    # Also add named partitions
    for line in block_devices_by_name.splitlines():
        if "->" in line:  # Symlink
            parts = line.split()
            if len(parts) >= 11:
                device_name = parts[-3]
                if not device_name.startswith("loop"):  # Skip loop devices
                    target = parts[-1]
                    if target.startswith("../"):
                        target = target.replace("../", "/dev/block/")
                    block_device_paths.append(target)
    
    # Remove duplicates
    block_device_paths = list(set(block_device_paths))
    
    # Save the list of identified block devices
    save_to_file(info_dir / "identified_block_devices.txt", "\n".join(block_device_paths))
    
    return block_device_paths


def dump_partition(dump_dir: Path, device_path: str) -> bool:
    """
    Attempt to dump a partition using dd.
    
    Args:
        dump_dir: Directory to save the dump
        device_path: Path to the block device
    
    Returns:
        True if successful, False otherwise
    """
    images_dir = dump_dir / "images"
    device_name = device_path.split("/")[-1]
    output_file = images_dir / f"{device_name}.img"
    
    print(f"Attempting to dump {device_path} to {output_file}...")
    
    # First, get the size of the partition
    _, size_output, _ = run_adb_command(["adb", "shell", f"blockdev --getsize64 {device_path}"], check=False)
    
    if not size_output or "Permission denied" in size_output or "No such file or directory" in size_output:
        print(f"  Failed to get size of {device_path}: {size_output}")
        return False
    
    try:
        size = int(size_output.strip())
        print(f"  Partition size: {size} bytes ({size / (1024*1024):.2f} MB)")
        
        # Use dd to dump the partition
        dd_command = f"dd if={device_path} of=/data/local/tmp/{device_name}.img bs=4096"
        _, dd_output, _ = run_adb_command(["adb", "shell", dd_command], check=False)
        
        if "Permission denied" in dd_output or "Operation not permitted" in dd_output:
            print(f"  Failed to dump {device_path}: Permission denied")
            return False
        
        # Pull the file from the device
        pull_command = ["adb", "pull", f"/data/local/tmp/{device_name}.img", str(output_file)]
        _, pull_output, _ = run_adb_command(pull_command, check=False)
        
        if "No such file or directory" in pull_output or "failed to copy" in pull_output:
            print(f"  Failed to pull {device_name}.img from device")
            return False
        
        # Clean up the temporary file
        _, _, _ = run_adb_command(["adb", "shell", f"rm /data/local/tmp/{device_name}.img"], check=False)
        
        print(f"  Successfully dumped {device_path} to {output_file}")
        return True
        
    except ValueError:
        print(f"  Failed to parse size of {device_path}: {size_output}")
        return False


def dump_bootloader(dump_dir: Path) -> None:
    """
    Attempt to dump bootloader-related partitions.
    """
    print("Attempting to dump bootloader-related partitions...")
    bootloader_partitions = [
        "boot", "recovery", "dtbo", "vbmeta", "aboot", "sbl1", "tz", "rpm", 
        "modem", "bluetooth", "dsp", "devcfg", "keymaster", "cmnlib", "cmnlib64",
        "apdp", "msadp", "hyp", "pmic", "xbl", "xbl_config", "abl", "logfs",
        "vendor_boot", "init_boot"
    ]
    
    # Get list of block devices by name
    _, block_devices_by_name, _ = run_adb_command(["adb", "shell", "ls", "-la", "/dev/block/by-name/"], check=False)
    
    for partition in bootloader_partitions:
        for line in block_devices_by_name.splitlines():
            if f"{partition} ->" in line or f"{partition}_" in line:
                parts = line.split()
                if len(parts) >= 11:
                    target = parts[-1]
                    if target.startswith("../"):
                        target = target.replace("../", "/dev/block/")
                        dump_partition(dump_dir, target)


def dump_all_partitions(dump_dir: Path) -> None:
    """
    Attempt to dump all identified partitions.
    """
    print("Attempting to dump all partitions...")
    block_devices = identify_block_devices(dump_dir)
    
    successful_dumps = 0
    failed_dumps = 0
    
    for device in block_devices:
        if dump_partition(dump_dir, device):
            successful_dumps += 1
        else:
            failed_dumps += 1
    
    print(f"\nPartition dump summary:")
    print(f"  Successfully dumped: {successful_dumps} partitions")
    print(f"  Failed to dump: {failed_dumps} partitions")
    
    if failed_dumps > 0:
        print("\nNote: Some partitions could not be dumped due to permission restrictions.")
        print("To dump all partitions, you may need to:")
        print("1. Root the device")
        print("2. Unlock the bootloader")
        print("3. Boot into recovery mode")


def main():
    """Main function to coordinate the raw partition dump."""
    print(f"Starting RAW partition dump for RanNeo X2 AR Glasses...")
    print(f"All data will be saved to: {DUMP_DIR}")
    print(f"WARNING: This operation may require root access or an unlocked bootloader.")
    print(f"         Some partitions may fail to dump due to permission restrictions.")
    
    # Set up the dump directory
    dump_dir = setup_dump_directory()
    
    # Try to dump bootloader partitions specifically
    dump_bootloader(dump_dir)
    
    # Try to dump all partitions
    dump_all_partitions(dump_dir)
    
    print(f"\nRaw partition dump completed! All data saved to: {dump_dir}")


if __name__ == "__main__":
    main()
