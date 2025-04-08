"""
Partition Information Utility for RanNeo X2 AR Glasses

This script gathers detailed information about all partitions on the device
without requiring root access. It maps partition names to block devices and
collects metadata about each partition.
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
DUMP_DIR = settings.SECRET_DIR / f"partition_info_{TIMESTAMP}"


def setup_dump_directory() -> Path:
    """Create and return the dump directory path."""
    dump_dir = DUMP_DIR
    dump_dir.mkdir(parents=True, exist_ok=True)
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


def get_partition_mapping(dump_dir: Path) -> Dict[str, str]:
    """
    Get a mapping of partition names to block devices.
    
    Returns:
        Dictionary mapping partition names to block device paths
    """
    print("Getting partition mapping...")
    
    # Get list of block devices by name
    _, block_devices_by_name, _ = run_adb_command(["adb", "shell", "ls", "-la", "/dev/block/by-name/"], check=False)
    save_to_file(dump_dir / "block_devices_by_name.txt", block_devices_by_name)
    
    # Parse the output to create a mapping
    partition_map = {}
    for line in block_devices_by_name.splitlines():
        if "->" in line:  # Symlink
            parts = line.split("->")
            if len(parts) == 2:
                # Extract partition name from the left part
                left_part = parts[0].strip().split()
                if left_part:
                    partition_name = left_part[-1]
                    
                    # Extract target from the right part
                    target = parts[1].strip()
                    partition_map[partition_name] = target
    
    # Save the mapping
    mapping_content = "\n".join([f"{name}: {device}" for name, device in partition_map.items()])
    save_to_file(dump_dir / "partition_mapping.txt", mapping_content)
    
    return partition_map


def get_partition_sizes(dump_dir: Path, partition_map: Dict[str, str]) -> Dict[str, int]:
    """
    Get the size of each partition.
    
    Args:
        dump_dir: Directory to save the output
        partition_map: Mapping of partition names to block device paths
    
    Returns:
        Dictionary mapping partition names to sizes in bytes
    """
    print("Getting partition sizes...")
    
    partition_sizes = {}
    size_content = []
    
    for name, device in partition_map.items():
        print(f"  Getting size of {name} ({device})...")
        _, size_output, _ = run_adb_command(["adb", "shell", f"blockdev --getsize64 {device} 2>/dev/null || echo 'Permission denied'"], check=False)
        
        if size_output and not "Permission denied" in size_output and not "No such file or directory" in size_output:
            try:
                size = int(size_output.strip())
                partition_sizes[name] = size
                size_mb = size / (1024 * 1024)
                size_content.append(f"{name}: {size} bytes ({size_mb:.2f} MB)")
            except ValueError:
                size_content.append(f"{name}: Error parsing size: {size_output}")
        else:
            size_content.append(f"{name}: Error getting size: {size_output}")
    
    # Save the sizes
    save_to_file(dump_dir / "partition_sizes.txt", "\n".join(size_content))
    
    return partition_sizes


def get_partition_types(dump_dir: Path, partition_map: Dict[str, str]) -> Dict[str, str]:
    """
    Attempt to determine the type of each partition.
    
    Args:
        dump_dir: Directory to save the output
        partition_map: Mapping of partition names to block device paths
    
    Returns:
        Dictionary mapping partition names to partition types
    """
    print("Determining partition types...")
    
    # Create headers directory
    headers_dir = dump_dir / "headers"
    headers_dir.mkdir(exist_ok=True)
    
    partition_types = {}
    type_content = []
    
    for name, device in partition_map.items():
        print(f"  Determining type of {name} ({device})...")
        
        # Try to read the first 512 bytes to determine type
        _, header_output, _ = run_adb_command(["adb", "shell", f"dd if={device} bs=512 count=1 2>/dev/null | hexdump -C | head -n 10"], check=False)
        
        if "Permission denied" in header_output or "Operation not permitted" in header_output:
            partition_types[name] = "Unknown (permission denied)"
            type_content.append(f"{name}: Unknown (permission denied)")
        elif not header_output:
            partition_types[name] = "Unknown (no data)"
            type_content.append(f"{name}: Unknown (no data)")
        else:
            # Try to determine type based on header
            partition_type = "Unknown"
            
            # Check for common partition types
            if "Android" in header_output:
                partition_type = "Android filesystem"
            elif "ANDROID!" in header_output:
                partition_type = "Android boot image"
            elif "ELF" in header_output:
                partition_type = "ELF binary"
            elif "ustar" in header_output:
                partition_type = "tar archive"
            elif "hsqs" in header_output:
                partition_type = "SquashFS"
            elif "ext2" in header_output or "ext3" in header_output or "ext4" in header_output:
                partition_type = "ext filesystem"
            
            # Special cases based on partition name
            if name in ["boot_a", "boot_b"]:
                partition_type = "Android boot image"
            elif name in ["recovery_a", "recovery_b"]:
                partition_type = "Android recovery image"
            elif name in ["system_a", "system_b", "vendor_a", "vendor_b"]:
                partition_type = "Android filesystem"
            elif name in ["userdata"]:
                partition_type = "User data (ext4)"
            elif name in ["metadata"]:
                partition_type = "Metadata (ext4)"
            elif name in ["super"]:
                partition_type = "Super (dynamic partitions)"
            elif name in ["vbmeta_a", "vbmeta_b", "vbmeta_system_a", "vbmeta_system_b"]:
                partition_type = "Verified Boot Metadata"
            elif name in ["dtbo_a", "dtbo_b"]:
                partition_type = "Device Tree Blob Overlay"
            elif name in ["tz_a", "tz_b"]:
                partition_type = "TrustZone"
            elif name in ["modem_a", "modem_b"]:
                partition_type = "Modem firmware"
            elif name in ["bluetooth_a", "bluetooth_b"]:
                partition_type = "Bluetooth firmware"
            elif name in ["dsp_a", "dsp_b"]:
                partition_type = "DSP firmware"
            
            partition_types[name] = partition_type
            type_content.append(f"{name}: {partition_type}")
            
            # Save the header for reference
            save_to_file(headers_dir / f"{name}_header.txt", header_output)
    
    # Save the types
    save_to_file(dump_dir / "partition_types.txt", "\n".join(type_content))
    
    return partition_types


def get_bootloader_info(dump_dir: Path) -> None:
    """
    Get detailed information about the bootloader.
    """
    print("Getting bootloader information...")
    
    # Create bootloader directory
    bootloader_dir = dump_dir / "bootloader"
    bootloader_dir.mkdir(exist_ok=True)
    
    # Get bootloader status
    _, bootloader_status, _ = run_adb_command(["adb", "shell", "getprop ro.boot.verifiedbootstate"], check=False)
    save_to_file(bootloader_dir / "bootloader_state.txt", bootloader_status.strip())
    
    # Get bootloader version
    _, bootloader_version, _ = run_adb_command(["adb", "shell", "getprop ro.bootloader"], check=False)
    save_to_file(bootloader_dir / "bootloader_version.txt", bootloader_version.strip())
    
    # Get secure boot status
    _, secure_boot, _ = run_adb_command(["adb", "shell", "getprop ro.boot.secureboot"], check=False)
    save_to_file(bootloader_dir / "secure_boot.txt", secure_boot.strip())
    
    # Get verified boot status
    _, verified_boot, _ = run_adb_command(["adb", "shell", "getprop ro.boot.verifiedboot"], check=False)
    save_to_file(bootloader_dir / "verified_boot.txt", verified_boot.strip())
    
    # Get boot slot information
    _, boot_slot, _ = run_adb_command(["adb", "shell", "getprop ro.boot.slot_suffix"], check=False)
    save_to_file(bootloader_dir / "boot_slot.txt", boot_slot.strip())
    
    # Get all bootloader-related properties
    _, boot_props, _ = run_adb_command(["adb", "shell", "getprop | grep boot"], check=False)
    save_to_file(bootloader_dir / "boot_properties.txt", boot_props)


def get_partition_contents(dump_dir: Path, partition_map: Dict[str, str]) -> None:
    """
    Attempt to get contents of important partitions using alternative methods.
    
    Args:
        dump_dir: Directory to save the output
        partition_map: Mapping of partition names to block device paths
    """
    print("Attempting to get partition contents using alternative methods...")
    
    # Create contents directory
    contents_dir = dump_dir / "contents"
    contents_dir.mkdir(exist_ok=True)
    
    # Try to get boot image information
    if "boot_a" in partition_map:
        print("  Analyzing boot image...")
        _, boot_info, _ = run_adb_command(["adb", "shell", "cat /proc/cmdline"], check=False)
        save_to_file(contents_dir / "boot_cmdline.txt", boot_info)
    
    # Try to get dtbo information
    if "dtbo_a" in partition_map:
        print("  Analyzing dtbo image...")
        _, dtbo_info, _ = run_adb_command(["adb", "shell", "ls -la /proc/device-tree/"], check=False)
        save_to_file(contents_dir / "device_tree_listing.txt", dtbo_info)
    
    # Try to get vbmeta information
    if "vbmeta_a" in partition_map:
        print("  Analyzing vbmeta image...")
        _, vbmeta_info, _ = run_adb_command(["adb", "shell", "getprop | grep avb"], check=False)
        save_to_file(contents_dir / "vbmeta_properties.txt", vbmeta_info)
    
    # Try to get fstab information
    print("  Getting fstab information...")
    _, fstab, _ = run_adb_command(["adb", "shell", "cat /etc/fstab*"], check=False)
    save_to_file(contents_dir / "fstab.txt", fstab)
    
    # Try to get mount information
    print("  Getting mount information...")
    _, mounts, _ = run_adb_command(["adb", "shell", "cat /proc/mounts"], check=False)
    save_to_file(contents_dir / "mounts.txt", mounts)
    
    # Try to get partition table information
    print("  Getting partition table information...")
    _, partition_table, _ = run_adb_command(["adb", "shell", "cat /proc/partitions"], check=False)
    save_to_file(contents_dir / "partitions.txt", partition_table)


def main():
    """Main function to coordinate the partition information gathering."""
    print(f"Starting partition information gathering for RanNeo X2 AR Glasses...")
    print(f"All data will be saved to: {DUMP_DIR}")
    
    # Set up the dump directory
    dump_dir = setup_dump_directory()
    
    # Create subdirectories
    (dump_dir / "headers").mkdir(exist_ok=True)
    
    # Get partition mapping
    partition_map = get_partition_mapping(dump_dir)
    
    # Get partition sizes
    partition_sizes = get_partition_sizes(dump_dir, partition_map)
    
    # Get partition types
    partition_types = get_partition_types(dump_dir, partition_map)
    
    # Get bootloader information
    get_bootloader_info(dump_dir)
    
    # Get partition contents where possible
    get_partition_contents(dump_dir, partition_map)
    
    # Generate summary
    summary = []
    summary.append(f"Partition Information Summary for RanNeo X2 AR Glasses")
    summary.append(f"=======================================================")
    summary.append(f"Total partitions identified: {len(partition_map)}")
    summary.append("")
    summary.append("Key Bootloader Partitions:")
    
    bootloader_partitions = ["xbl_a", "xbl_b", "abl_a", "abl_b", "tz_a", "tz_b", 
                            "boot_a", "boot_b", "recovery_a", "recovery_b", 
                            "dtbo_a", "dtbo_b", "vbmeta_a", "vbmeta_b"]
    
    for name in bootloader_partitions:
        if name in partition_map:
            size_str = f"{partition_sizes.get(name, 0) / (1024 * 1024):.2f} MB" if name in partition_sizes else "Unknown"
            type_str = partition_types.get(name, "Unknown")
            summary.append(f"  {name}: {partition_map[name]} ({size_str}) - {type_str}")
    
    summary.append("")
    summary.append("Key System Partitions:")
    
    system_partitions = ["super", "userdata", "metadata", "persist"]
    
    for name in system_partitions:
        if name in partition_map:
            size_str = f"{partition_sizes.get(name, 0) / (1024 * 1024):.2f} MB" if name in partition_sizes else "Unknown"
            type_str = partition_types.get(name, "Unknown")
            summary.append(f"  {name}: {partition_map[name]} ({size_str}) - {type_str}")
    
    summary.append("")
    summary.append("Note: Direct partition dumps were not possible due to permission restrictions.")
    summary.append("To dump raw partition images, you would need:")
    summary.append("1. Root access")
    summary.append("2. An unlocked bootloader")
    summary.append("3. Custom recovery (like TWRP)")
    
    save_to_file(dump_dir / "summary.txt", "\n".join(summary))
    
    print(f"\nPartition information gathering completed! All data saved to: {dump_dir}")
    print(f"See {dump_dir}/summary.txt for a summary of the findings.")


if __name__ == "__main__":
    main()
