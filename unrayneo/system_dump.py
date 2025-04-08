"""
System Dump Utility for RanNeo X2 AR Glasses

This script performs a comprehensive dump of system information from RanNeo X2 AR glasses.
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
DUMP_DIR = settings.SECRET_DIR / f"system_dump_{TIMESTAMP}"


def setup_dump_directory() -> Path:
    """Create and return the dump directory path."""
    dump_dir = DUMP_DIR
    dump_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (dump_dir / "partitions").mkdir(exist_ok=True)
    (dump_dir / "props").mkdir(exist_ok=True)
    (dump_dir / "apks").mkdir(exist_ok=True)
    (dump_dir / "logs").mkdir(exist_ok=True)
    (dump_dir / "bootloader").mkdir(exist_ok=True)
    
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


def dump_device_info(dump_dir: Path) -> None:
    """
    Dump basic device information.
    """
    print("Dumping device information...")
    
    # Get build properties
    _, props, _ = run_adb_command(["adb", "shell", "getprop"])
    save_to_file(dump_dir / "props" / "build_props.txt", props)
    
    # Get system information
    commands = {
        "kernel_version.txt": ["adb", "shell", "uname", "-a"],
        "cpu_info.txt": ["adb", "shell", "cat", "/proc/cpuinfo"],
        "memory_info.txt": ["adb", "shell", "cat", "/proc/meminfo"],
        "disk_usage.txt": ["adb", "shell", "df", "-h"],
        "mount_points.txt": ["adb", "shell", "mount"],
        "device_features.txt": ["adb", "shell", "pm", "list", "features"]
    }
    
    for filename, command in commands.items():
        _, output, _ = run_adb_command(command)
        save_to_file(dump_dir / "props" / filename, output)
    
    # Dump specific important props
    important_props = [
        "ro.build.fingerprint",
        "ro.build.version.release",
        "ro.build.version.sdk",
        "ro.product.manufacturer",
        "ro.product.model",
        "ro.product.name",
        "ro.product.device",
        "ro.bootloader",
        "ro.serialno",
        "ro.hardware",
        "ro.secure",
        "ro.adb.secure",
        "ro.debuggable",
        "sys.oem_unlock_allowed"
    ]
    
    prop_details = {}
    for prop in important_props:
        _, output, _ = run_adb_command(["adb", "shell", "getprop", prop])
        prop_details[prop] = output.strip()
    
    prop_output = "\n".join([f"{k}: {v}" for k, v in prop_details.items()])
    save_to_file(dump_dir / "props" / "important_props.txt", prop_output)


def dump_partition_info(dump_dir: Path) -> None:
    """
    Dump partition information.
    """
    print("Dumping partition information...")
    
    # Get partition list
    _, partitions, _ = run_adb_command(["adb", "shell", "ls", "-la", "/dev/block/platform"])
    save_to_file(dump_dir / "partitions" / "block_devices.txt", partitions)
    
    # Get partition table if available
    _, partition_table, _ = run_adb_command(
        ["adb", "shell", "cat", "/proc/partitions"], 
        check=False
    )
    save_to_file(dump_dir / "partitions" / "proc_partitions.txt", partition_table)
    
    # Attempt to get more detailed partition info
    commands = {
        "mounts.txt": ["adb", "shell", "cat", "/proc/mounts"],
        "fstab.txt": ["adb", "shell", "find", "/", "-name", "fstab*", "-exec", "cat", "{}", ";", "2>/dev/null"],
    }
    
    for filename, command in commands.items():
        _, output, _ = run_adb_command(command, check=False)
        save_to_file(dump_dir / "partitions" / filename, output)


def dump_bootloader_info(dump_dir: Path) -> None:
    """
    Dump comprehensive bootloader information.
    """
    print("Dumping bootloader information...")
    
    # Create bootloader directory
    bootloader_dir = dump_dir / "bootloader"
    bootloader_dir.mkdir(exist_ok=True)
    
    # Get bootloader status
    _, bootloader_status, _ = run_adb_command(["adb", "shell", "getprop", "ro.boot.flash.locked"], check=False)
    _, oem_unlock_allowed, _ = run_adb_command(["adb", "shell", "getprop", "sys.oem_unlock_allowed"], check=False)
    
    bootloader_info = f"Bootloader locked: {bootloader_status.strip()}\nOEM unlock allowed: {oem_unlock_allowed.strip()}"
    save_to_file(bootloader_dir / "status.txt", bootloader_info)
    
    # Get boot info
    _, boot_slots, _ = run_adb_command(["adb", "shell", "getprop", "ro.boot.slot_suffix"], check=False)
    save_to_file(bootloader_dir / "boot_slot.txt", f"Current boot slot: {boot_slots.strip()}")
    
    # Get verified boot state
    _, verified_boot, _ = run_adb_command(["adb", "shell", "getprop", "ro.boot.verifiedbootstate"], check=False)
    save_to_file(bootloader_dir / "verified_boot.txt", f"Verified boot state: {verified_boot.strip()}")
    
    # Dump all boot-related properties
    _, boot_props, _ = run_adb_command(["adb", "shell", "getprop", "|", "grep", "boot"])
    save_to_file(bootloader_dir / "boot_properties.txt", boot_props)
    
    # Dump all secure boot related properties
    _, secure_boot_props, _ = run_adb_command(["adb", "shell", "getprop", "|", "grep", "secure"])
    save_to_file(bootloader_dir / "secure_boot_properties.txt", secure_boot_props)
    
    # Try to dump bootloader version
    _, bootloader_version, _ = run_adb_command(["adb", "shell", "getprop", "ro.bootloader"], check=False)
    save_to_file(bootloader_dir / "bootloader_version.txt", f"Bootloader version: {bootloader_version.strip()}")
    
    # Try to dump dtbo info
    _, dtbo_info, _ = run_adb_command(["adb", "shell", "ls", "-la", "/dev/block/by-name/dtbo"], check=False)
    save_to_file(bootloader_dir / "dtbo_info.txt", dtbo_info)
    
    # Try to dump vbmeta info
    _, vbmeta_info, _ = run_adb_command(["adb", "shell", "ls", "-la", "/dev/block/by-name/vbmeta"], check=False)
    save_to_file(bootloader_dir / "vbmeta_info.txt", vbmeta_info)


def dump_installed_packages(dump_dir: Path) -> None:
    """
    Dump information about installed packages.
    """
    print("Dumping installed package information...")
    
    # Get list of all packages
    _, packages, _ = run_adb_command(["adb", "shell", "pm", "list", "packages", "-f"])
    save_to_file(dump_dir / "apks" / "package_list.txt", packages)
    
    # Get list of system packages
    _, system_packages, _ = run_adb_command(["adb", "shell", "pm", "list", "packages", "-s"])
    save_to_file(dump_dir / "apks" / "system_packages.txt", system_packages)
    
    # Get list of third-party packages
    _, third_party_packages, _ = run_adb_command(["adb", "shell", "pm", "list", "packages", "-3"])
    save_to_file(dump_dir / "apks" / "third_party_packages.txt", third_party_packages)
    
    # Get detailed package info for selected packages
    # Parse the package list to extract package names
    package_names = []
    for line in packages.splitlines():
        if line.startswith("package:"):
            parts = line.split("=")
            if len(parts) > 1:
                package_names.append(parts[1])
    
    # Dump info for Chinese packages and system packages
    chinese_keywords = ["com.ffalcon", "com.leiniao", "com.zhiliaoapp", "rayneo"]
    for package in package_names:
        is_chinese = any(keyword in package.lower() for keyword in chinese_keywords)
        is_system = package in system_packages
        
        if is_chinese or (is_system and "android" in package):
            _, package_info, _ = run_adb_command(["adb", "shell", "dumpsys", "package", package])
            save_to_file(dump_dir / "apks" / f"{package}_info.txt", package_info)


def extract_apk_files(dump_dir: Path) -> None:
    """
    Extract actual APK files from the device.
    
    This function extracts APK files for all packages on the device.
    """
    print("\nExtracting APK files...")
    
    # Create directory for APK files
    apk_files_dir = dump_dir / "apks" / "files"
    apk_files_dir.mkdir(exist_ok=True)
    
    # Get list of all packages with their paths
    _, packages, _ = run_adb_command(["adb", "shell", "pm", "list", "packages", "-f"])
    
    # Parse package paths
    package_paths = {}
    for line in packages.splitlines():
        if line.startswith("package:"):
            path_part = line[8:].split("=")
            if len(path_part) == 2:
                package_paths[path_part[1]] = path_part[0]
    
    # Extract all APKs but prioritize Chinese packages
    chinese_keywords = ["com.ffalcon", "com.leiniao", "com.zhiliaoapp", "rayneo"]
    system_packages_of_interest = [
        "com.android.settings",
        "com.android.systemui"
    ]
    
    # First, process high-priority packages (for display purposes)
    high_priority_packages = {}
    for package, path in package_paths.items():
        is_chinese = any(keyword in package.lower() for keyword in chinese_keywords)
        is_important_system = package in system_packages_of_interest
        
        if is_chinese or is_important_system:
            high_priority_packages[package] = path
    
    # Count for progress reporting
    total_to_extract = len(package_paths)
    extracted_count = 0
    print(f"Found {total_to_extract} packages to extract.")
    
    # First extract high-priority packages
    for package, path in high_priority_packages.items():
        extracted_count += 1
        print(f"Extracting APK [{extracted_count}/{total_to_extract}]: {package} (high priority)")
        
        # Safe filename for the package
        safe_name = package.replace('.', '_')
        output_path = apk_files_dir / f"{safe_name}.apk"
        
        # Pull the APK file
        pull_cmd = ["adb", "pull", path, str(output_path)]
        returncode, stdout, stderr = run_adb_command(pull_cmd, check=False)
        
        if returncode != 0:
            print(f"  Failed to extract APK: {stderr}")
            # Try alternative method for split APKs
            _, path_output, _ = run_adb_command(["adb", "shell", "pm", "path", package])
            if "package:" in path_output:
                # Create package directory for split APKs
                package_dir = apk_files_dir / safe_name
                package_dir.mkdir(exist_ok=True)
                
                for i, path_line in enumerate(path_output.splitlines()):
                    if path_line.startswith("package:"):
                        apk_path = path_line[8:]
                        base_name = os.path.basename(apk_path)
                        output_path = package_dir / base_name
                        
                        pull_cmd = ["adb", "pull", apk_path, str(output_path)]
                        run_adb_command(pull_cmd, check=False)
        else:
            print(f"  Successfully extracted to {output_path}")
    
    # Then extract remaining packages
    for package, path in package_paths.items():
        if package not in high_priority_packages:
            extracted_count += 1
            print(f"Extracting APK [{extracted_count}/{total_to_extract}]: {package}")
            
            # Safe filename for the package
            safe_name = package.replace('.', '_')
            output_path = apk_files_dir / f"{safe_name}.apk"
            
            # Pull the APK file
            pull_cmd = ["adb", "pull", path, str(output_path)]
            returncode, stdout, stderr = run_adb_command(pull_cmd, check=False)
            
            if returncode != 0:
                print(f"  Failed to extract APK: {stderr}")
                # Try alternative method for split APKs
                _, path_output, _ = run_adb_command(["adb", "shell", "pm", "path", package])
                if "package:" in path_output:
                    # Create package directory for split APKs
                    package_dir = apk_files_dir / safe_name
                    package_dir.mkdir(exist_ok=True)
                    
                    for i, path_line in enumerate(path_output.splitlines()):
                        if path_line.startswith("package:"):
                            apk_path = path_line[8:]
                            base_name = os.path.basename(apk_path)
                            output_path = package_dir / base_name
                            
                            pull_cmd = ["adb", "pull", apk_path, str(output_path)]
                            run_adb_command(pull_cmd, check=False)
            else:
                print(f"  Successfully extracted to {output_path}")
    
    print(f"Extracted {extracted_count} APK files to {apk_files_dir}")


def dump_memory_info(dump_dir: Path) -> None:
    """
    Dump detailed memory information from the device.
    """
    print("\nDumping memory information...")
    memory_dir = dump_dir / "memory"
    memory_dir.mkdir(exist_ok=True)
    
    # Get memory stats using various commands
    memory_commands = {
        "meminfo": ["adb", "shell", "cat", "/proc/meminfo"],
        "dumpsys_meminfo": ["adb", "shell", "dumpsys", "meminfo"],
        "top_processes": ["adb", "shell", "top", "-n", "1", "-o", "RES"],
        "slabtop": ["adb", "shell", "cat", "/proc/slabinfo"],
        "vmstat": ["adb", "shell", "cat", "/proc/vmstat"],
        "zoneinfo": ["adb", "shell", "cat", "/proc/zoneinfo"],
        "buddyinfo": ["adb", "shell", "cat", "/proc/buddyinfo"],
        # System service memory
        "activity_memory": ["adb", "shell", "dumpsys", "activity", "memory"],
    }
    
    for name, command in memory_commands.items():
        print(f"Getting {name}...")
        returncode, stdout, stderr = run_adb_command(command, check=False)
        if returncode == 0:
            save_to_file(memory_dir / f"{name}.txt", stdout)
        else:
            print(f"Failed to get {name}: {stderr}")
    
    # Get memory info for specific processes (especially Chinese apps)
    _, packages, _ = run_adb_command(["adb", "shell", "pm", "list", "packages"])
    chinese_keywords = ["com.ffalcon", "com.leiniao", "com.zhiliaoapp", "rayneo"]
    process_dir = memory_dir / "processes"
    process_dir.mkdir(exist_ok=True)
    
    for line in packages.splitlines():
        if line.startswith("package:"):
            package = line[8:]
            is_chinese = any(keyword in package.lower() for keyword in chinese_keywords)
            
            if is_chinese:
                print(f"Getting memory info for {package}...")
                _, stdout, _ = run_adb_command(
                    ["adb", "shell", "dumpsys", "meminfo", package],
                    check=False
                )
                if stdout:
                    save_to_file(process_dir / f"{package.replace('.', '_')}_meminfo.txt", stdout)


def dump_system_logs(dump_dir: Path) -> None:
    """
    Dump system logs.
    """
    print("Dumping system logs...")
    
    # Dump logcat
    _, logcat, _ = run_adb_command(["adb", "logcat", "-d"])
    save_to_file(dump_dir / "logs" / "logcat.txt", logcat)
    
    # Dump dmesg
    _, dmesg, _ = run_adb_command(["adb", "shell", "dmesg"])
    save_to_file(dump_dir / "logs" / "dmesg.txt", dmesg)
    
    # Dump event logs
    _, eventlog, _ = run_adb_command(["adb", "logcat", "-b", "events", "-d"])
    save_to_file(dump_dir / "logs" / "events.txt", eventlog)


def extract_system_files(dump_dir: Path) -> None:
    """
    Extract important system files.
    
    Warning: This function requires root access on the device or may fail for some files.
    """
    print("Attempting to extract system files (some operations may fail due to permissions)...")
    
    # Create system files directory
    system_dir = dump_dir / "system_files"
    system_dir.mkdir(exist_ok=True)
    
    # List of important system files to extract
    system_files = [
        "/system/build.prop",
        "/default.prop",
        "/system/etc/permissions/platform.xml",
        "/system/etc/hosts"
    ]
    
    for file_path in system_files:
        file_name = os.path.basename(file_path)
        _, content, _ = run_adb_command(["adb", "shell", "cat", file_path], check=False)
        save_to_file(system_dir / file_name, content)


def dump_partition_contents(dump_dir: Path) -> None:
    """
    Dump partition contents (requires root or specific permissions).
    This is a potentially dangerous operation and may not work on all devices.
    """
    print("\nAttempting to dump partition contents...")
    
    # First, we need to identify where the partition block devices are
    print("Scanning for partition block devices...")
    partition_paths = {}
    
    # Try different known device paths used by various manufacturers
    path_patterns = [
        "/dev/block/platform/*/by-name/*",
        "/dev/block/bootdevice/by-name/*",
        "/dev/block/by-name/*",
        "/dev/block/platform/*/*/by-name/*",
        "/dev/block/*/by-name/*"
    ]
    
    for pattern in path_patterns:
        _, output, _ = run_adb_command(["adb", "shell", f"ls -la {pattern} 2>/dev/null"], check=False)
        if output and "No such file" not in output and "Permission denied" not in output:
            print(f"Found block devices using pattern: {pattern}")
            
            # Parse the output to get partition names and their real paths
            for line in output.splitlines():
                if "->" in line:  # It's a symlink
                    parts = line.split()
                    if len(parts) >= 9:
                        partition_name = parts[8]
                        if "/" in partition_name:
                            partition_name = os.path.basename(partition_name)
                        
                        # Get the target of the symlink
                        _, target, _ = run_adb_command(
                            ["adb", "shell", f"readlink -f {pattern.replace('*', partition_name)}"],
                            check=False
                        )
                        if target and "No such file" not in target:
                            partition_paths[partition_name] = target.strip()
    
    if not partition_paths:
        # If we couldn't find partitions using symlinks, try a more direct approach
        _, output, _ = run_adb_command(["adb", "shell", "ls -la /dev/block/"], check=False)
        save_to_file(dump_dir / "partitions" / "block_devices_direct.txt", output)
        
        # Try to look for common partition names in /proc/partitions
        _, partitions_output, _ = run_adb_command(["adb", "shell", "cat /proc/partitions"], check=False)
        save_to_file(dump_dir / "partitions" / "proc_partitions_raw.txt", partitions_output)
        
        print("Could not find partition symlinks. Looking at raw block devices...")
        
        # Parse /proc/partitions to find likely partition devices
        if partitions_output and "major minor" in partitions_output:
            for line in partitions_output.splitlines():
                parts = line.split()
                if len(parts) == 4 and parts[0] != "major":
                    partition_name = parts[3]
                    if any(name in partition_name for name in ["boot", "system", "vendor", "recovery", "userdata"]):
                        partition_paths[partition_name] = f"/dev/block/{partition_name}"
    
    # Save the identified partition paths
    partition_paths_output = "\n".join([f"{name}: {path}" for name, path in partition_paths.items()])
    save_to_file(dump_dir / "partitions" / "identified_partitions.txt", partition_paths_output)
    
    if not partition_paths:
        print("Could not identify partition paths. Dumping may not be possible without root access.")
        print("You may need to unlock the bootloader to access partitions.")
        return
    
    print(f"Identified {len(partition_paths)} partitions.")
    
    # Attempt to dump ALL partitions, not just a predefined list
    partitions_dir = dump_dir / "partitions" / "images"
    partitions_dir.mkdir(exist_ok=True)
    
    # Get partition info for all partitions
    for partition_name, source_path in partition_paths.items():
        print(f"Getting info for {partition_name} partition at {source_path}...")
        
        # Get partition size
        _, size_output, _ = run_adb_command(["adb", "shell", f"blockdev --getsize64 {source_path}"], check=False)
        if size_output and "No such file" not in size_output and "Permission denied" not in size_output:
            size_bytes = int(size_output.strip())
            size_mb = size_bytes / (1024 * 1024)
            partition_info = f"Partition: {partition_name}\nPath: {source_path}\nSize: {size_bytes} bytes ({size_mb:.2f} MB)"
            save_to_file(partitions_dir / f"{partition_name}_info.txt", partition_info)
    
    # Attempt to dump all identified partitions
    for partition_name, source_path in partition_paths.items():
        print(f"Attempting to dump {partition_name} partition from {source_path}...")
        remote_path = f"/sdcard/{partition_name}.img"
        
        # Use dd to dump the partition - this may fail without root
        dump_cmd = ["adb", "shell", f"dd if={source_path} of={remote_path} bs=4096"]
        returncode, stdout, stderr = run_adb_command(dump_cmd, check=False)
        
        if returncode == 0:
            # Pull the file
            pull_cmd = ["adb", "pull", remote_path, str(partitions_dir / f"{partition_name}.img")]
            run_adb_command(pull_cmd, check=False)
            
            # Remove remote file
            run_adb_command(["adb", "shell", f"rm {remote_path}"], check=False)
        else:
            print(f"Failed to dump {partition_name} partition: {stderr}")
            
            # Try direct read with cat (might still fail without root)
            print(f"Trying alternative method for {partition_name}...")
            cat_cmd = ["adb", "shell", f"cat {source_path} > {remote_path}"]
            returncode, stdout, stderr = run_adb_command(cat_cmd, check=False)
            
            if returncode == 0:
                # Pull the file
                pull_cmd = ["adb", "pull", remote_path, str(partitions_dir / f"{partition_name}.img")]
                run_adb_command(pull_cmd, check=False)
                
                # Remove remote file
                run_adb_command(["adb", "shell", f"rm {remote_path}"], check=False)
            else:
                print(f"Alternative method also failed: {stderr}")
    
    # Check if any partitions were dumped
    dumped_files = list(partitions_dir.glob("*.img"))
    if not dumped_files:
        print("\nFailed to dump any partitions. Root access is likely required.")
        print("Consider these options to access partitions:")
        print("1. Unlock the bootloader (since sys.oem_unlock_allowed=1)")
        print("   - Enable OEM unlocking in developer options")
        print("   - Use 'adb reboot bootloader' to enter fastboot mode")
        print("   - Use 'fastboot flashing unlock' to unlock the bootloader")
        print("2. Try using Magisk to gain root access")
        print("3. Look for Android 12 exploits that might provide temporary root")
    else:
        print(f"\nSuccessfully dumped {len(dumped_files)} partitions to {partitions_dir}")


def create_summary(dump_dir: Path) -> None:
    """
    Create a summary of the dumped information.
    """
    summary = []
    summary.append("# RanNeo X2 System Dump Summary")
    summary.append(f"Dump created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("")
    
    # Read important properties
    try:
        with open(dump_dir / "props" / "important_props.txt", 'r') as f:
            props = f.read()
            summary.append("## Device Information")
            summary.append("```")
            summary.append(props)
            summary.append("```")
    except FileNotFoundError:
        pass
    
    # Count packages
    try:
        with open(dump_dir / "apks" / "package_list.txt", 'r') as f:
            package_count = len(f.readlines())
            summary.append(f"\n## Package Information")
            summary.append(f"Total packages: {package_count}")
    except FileNotFoundError:
        pass
    
    try:
        with open(dump_dir / "apks" / "system_packages.txt", 'r') as f:
            system_package_count = len(f.readlines())
            summary.append(f"System packages: {system_package_count}")
    except FileNotFoundError:
        pass
    
    try:
        with open(dump_dir / "apks" / "third_party_packages.txt", 'r') as f:
            third_party_count = len(f.readlines())
            summary.append(f"Third-party packages: {third_party_count}")
    except FileNotFoundError:
        pass
    
    # Bootloader status
    try:
        with open(dump_dir / "bootloader" / "status.txt", 'r') as f:
            bootloader_status = f.read()
            summary.append(f"\n## Bootloader Information")
            summary.append("```")
            summary.append(bootloader_status)
            summary.append("```")
    except FileNotFoundError:
        pass
    
    # Save summary
    summary_text = "\n".join(summary)
    save_to_file(dump_dir / "summary.md", summary_text)
    print(f"Summary created at {dump_dir / 'summary.md'}")


def dump_bluetooth_info(dump_dir: Path) -> None:
    """
    Dump detailed Bluetooth information.
    """
    print("Dumping Bluetooth information...")
    
    # Create Bluetooth directory
    bluetooth_dir = dump_dir / "bluetooth"
    bluetooth_dir.mkdir(exist_ok=True)
    
    # Dump Bluetooth manager info
    _, bluetooth_manager, _ = run_adb_command(["adb", "shell", "dumpsys", "bluetooth_manager"])
    save_to_file(bluetooth_dir / "bluetooth_manager.txt", bluetooth_manager)
    
    # Dump Bluetooth processes
    _, bluetooth_processes, _ = run_adb_command(["adb", "shell", "ps", "-A", "|", "grep", "-i", "bluetooth"])
    save_to_file(bluetooth_dir / "bluetooth_processes.txt", bluetooth_processes)
    
    # Dump Bluetooth GATT services
    _, bluetooth_gatt, _ = run_adb_command(["adb", "shell", "dumpsys", "bluetooth_manager", "|", "grep", "-A", "50", "GATT"])
    save_to_file(bluetooth_dir / "bluetooth_gatt.txt", bluetooth_gatt)
    
    # Dump Bluetooth profiles
    _, bluetooth_profiles, _ = run_adb_command(["adb", "shell", "dumpsys", "bluetooth_manager", "|", "grep", "-i", "profile", "-A", "5"])
    save_to_file(bluetooth_dir / "bluetooth_profiles.txt", bluetooth_profiles)


def dump_input_devices(dump_dir: Path) -> None:
    """
    Dump information about input devices.
    """
    print("Dumping input device information...")
    
    # Create input directory
    input_dir = dump_dir / "input"
    input_dir.mkdir(exist_ok=True)
    
    # Dump input manager info
    _, input_manager, _ = run_adb_command(["adb", "shell", "dumpsys", "input"])
    save_to_file(input_dir / "input_manager.txt", input_manager)
    
    # List input devices
    _, input_devices, _ = run_adb_command(["adb", "shell", "ls", "-l", "/dev/input/"])
    save_to_file(input_dir / "input_devices.txt", input_devices)
    
    # Dump input method services
    _, input_method, _ = run_adb_command(["adb", "shell", "dumpsys", "input_method"])
    save_to_file(input_dir / "input_method.txt", input_method)
    
    # Dump accessibility services
    _, accessibility, _ = run_adb_command(["adb", "shell", "dumpsys", "accessibility"])
    save_to_file(input_dir / "accessibility.txt", accessibility)


def dump_services_info(dump_dir: Path) -> None:
    """
    Dump information about system services.
    """
    print("Dumping system services information...")
    
    # Create services directory
    services_dir = dump_dir / "services"
    services_dir.mkdir(exist_ok=True)
    
    # Get list of all services
    _, services_list, _ = run_adb_command(["adb", "shell", "service", "list"])
    save_to_file(services_dir / "services_list.txt", services_list)
    
    # Dump important services
    important_services = [
        "activity",
        "package",
        "window",
        "display",
        "power",
        "battery",
        "usb",
        "network_management",
        "wifi",
        "audio",
        "media.audio_policy",
        "sensorservice",
        "camera",
        "permission"
    ]
    
    for service in important_services:
        _, service_dump, _ = run_adb_command(["adb", "shell", "dumpsys", service], check=False)
        save_to_file(services_dir / f"{service}.txt", service_dump)
    
    # Dump Mercury-related services
    mercury_packages = [
        "com.ffalconxr.mercury.launcher",
        "com.leiniao.scanner",
        "com.tcl.xrmanager.main",
        "com.ffalcon.xr.unity.demo"
    ]
    
    for package in mercury_packages:
        _, package_info, _ = run_adb_command(["adb", "shell", "dumpsys", "package", package], check=False)
        save_to_file(services_dir / f"{package.replace('.', '_')}.txt", package_info)


def dump_firmware_info(dump_dir: Path) -> None:
    """
    Dump firmware and hardware-related information.
    """
    print("Dumping firmware information...")
    
    # Create firmware directory
    firmware_dir = dump_dir / "firmware"
    firmware_dir.mkdir(exist_ok=True)
    
    # Dump kernel information
    _, kernel_version, _ = run_adb_command(["adb", "shell", "uname", "-a"])
    save_to_file(firmware_dir / "kernel_version.txt", kernel_version)
    
    # Dump kernel modules
    _, kernel_modules, _ = run_adb_command(["adb", "shell", "lsmod"])
    save_to_file(firmware_dir / "kernel_modules.txt", kernel_modules)
    
    # Dump firmware version
    _, firmware_version, _ = run_adb_command(["adb", "shell", "getprop", "ro.build.version.incremental"])
    save_to_file(firmware_dir / "firmware_version.txt", f"Firmware version: {firmware_version.strip()}")
    
    # Dump hardware info
    _, hardware_info, _ = run_adb_command(["adb", "shell", "getprop", "ro.hardware"])
    save_to_file(firmware_dir / "hardware_info.txt", f"Hardware: {hardware_info.strip()}")
    
    # Dump SOC info
    _, soc_info, _ = run_adb_command(["adb", "shell", "getprop", "ro.board.platform"])
    save_to_file(firmware_dir / "soc_info.txt", f"SOC Platform: {soc_info.strip()}")
    
    # Try to get device tree info
    _, device_tree, _ = run_adb_command(["adb", "shell", "ls", "-la", "/proc/device-tree"], check=False)
    save_to_file(firmware_dir / "device_tree.txt", device_tree)
    
    # Dump all hardware-related properties
    _, hw_props, _ = run_adb_command(["adb", "shell", "getprop", "|", "grep", "hardware"])
    save_to_file(firmware_dir / "hardware_properties.txt", hw_props)
    
    # Dump all firmware-related properties
    _, fw_props, _ = run_adb_command(["adb", "shell", "getprop", "|", "grep", "firmware"])
    save_to_file(firmware_dir / "firmware_properties.txt", fw_props)


def dump_security_info(dump_dir: Path) -> None:
    """
    Dump security-related information.
    """
    print("Dumping security information...")
    
    # Create security directory
    security_dir = dump_dir / "security"
    security_dir.mkdir(exist_ok=True)
    
    # Dump SELinux status
    _, selinux_status, _ = run_adb_command(["adb", "shell", "getenforce"])
    save_to_file(security_dir / "selinux_status.txt", f"SELinux status: {selinux_status.strip()}")
    
    # Dump SELinux contexts
    _, selinux_contexts, _ = run_adb_command(["adb", "shell", "ls", "-Z", "/"])
    save_to_file(security_dir / "selinux_root_contexts.txt", selinux_contexts)
    
    # Dump security-related properties
    _, security_props, _ = run_adb_command(["adb", "shell", "getprop", "|", "grep", "security"])
    save_to_file(security_dir / "security_properties.txt", security_props)
    
    # Dump secure properties
    _, secure_props, _ = run_adb_command(["adb", "shell", "getprop", "|", "grep", "secure"])
    save_to_file(security_dir / "secure_properties.txt", secure_props)
    
    # Check for root
    _, su_check, _ = run_adb_command(["adb", "shell", "which", "su"], check=False)
    save_to_file(security_dir / "su_check.txt", f"su binary found: {'Yes' if su_check.strip() else 'No'}")
    
    # Check for Magisk
    _, magisk_check, _ = run_adb_command(["adb", "shell", "ls", "-la", "/sbin/.magisk"], check=False)
    save_to_file(security_dir / "magisk_check.txt", f"Magisk found: {'Yes' if "No such file" not in magisk_check else 'No'}")


def dump_hardware_info(dump_dir: Path) -> None:
    """
    Dump detailed hardware information.
    """
    print("Dumping hardware information...")
    
    # Create hardware directory
    hardware_dir = dump_dir / "hardware"
    hardware_dir.mkdir(exist_ok=True)
    
    # Dump CPU info
    _, cpu_info, _ = run_adb_command(["adb", "shell", "cat", "/proc/cpuinfo"])
    save_to_file(hardware_dir / "cpu_info.txt", cpu_info)
    
    # Dump memory info
    _, memory_info, _ = run_adb_command(["adb", "shell", "cat", "/proc/meminfo"])
    save_to_file(hardware_dir / "memory_info.txt", memory_info)
    
    # Dump GPU info
    _, gpu_info, _ = run_adb_command(["adb", "shell", "dumpsys", "SurfaceFlinger"])
    save_to_file(hardware_dir / "gpu_info.txt", gpu_info)
    
    # Dump display info
    _, display_info, _ = run_adb_command(["adb", "shell", "dumpsys", "display"])
    save_to_file(hardware_dir / "display_info.txt", display_info)
    
    # Dump sensor info
    _, sensor_info, _ = run_adb_command(["adb", "shell", "dumpsys", "sensorservice"])
    save_to_file(hardware_dir / "sensor_info.txt", sensor_info)
    
    # Dump camera info
    _, camera_info, _ = run_adb_command(["adb", "shell", "dumpsys", "media.camera"])
    save_to_file(hardware_dir / "camera_info.txt", camera_info)
    
    # Dump audio info
    _, audio_info, _ = run_adb_command(["adb", "shell", "dumpsys", "audio"])
    save_to_file(hardware_dir / "audio_info.txt", audio_info)
    
    # Dump battery info
    _, battery_info, _ = run_adb_command(["adb", "shell", "dumpsys", "battery"])
    save_to_file(hardware_dir / "battery_info.txt", battery_info)
    
    # Dump thermal info
    _, thermal_info, _ = run_adb_command(["adb", "shell", "dumpsys", "thermalservice"], check=False)
    save_to_file(hardware_dir / "thermal_info.txt", thermal_info)
    
    # Dump USB info
    _, usb_info, _ = run_adb_command(["adb", "shell", "dumpsys", "usb"])
    save_to_file(hardware_dir / "usb_info.txt", usb_info)
    
    # Dump device tree if available
    _, device_tree, _ = run_adb_command(["adb", "shell", "find", "/proc/device-tree", "-type", "f", "-exec", "echo", "{}", ";", "-exec", "cat", "{}", ";", "2>/dev/null"], check=False)
    save_to_file(hardware_dir / "device_tree_dump.txt", device_tree)


def main():
    """Main function to coordinate the system dump."""
    print(f"Starting system dump for RanNeo X2 AR Glasses...")
    print(f"All data will be saved to: {DUMP_DIR}")
    
    # Set up the dump directory
    dump_dir = setup_dump_directory()
    
    # Perform the dumps
    dump_device_info(dump_dir)
    dump_partition_info(dump_dir)
    dump_bootloader_info(dump_dir)
    dump_installed_packages(dump_dir)
    dump_system_logs(dump_dir)
    extract_system_files(dump_dir)
    
    # Extract APK files
    extract_apk_files(dump_dir)
    
    # Dump memory information
    dump_memory_info(dump_dir)
    
    # Dump Bluetooth and input device information
    dump_bluetooth_info(dump_dir)
    dump_input_devices(dump_dir)
    dump_services_info(dump_dir)
    
    # Dump firmware, hardware, and security information
    dump_firmware_info(dump_dir)
    dump_hardware_info(dump_dir)
    dump_security_info(dump_dir)
    
    # Run partition dump without asking
    dump_partition_contents(dump_dir)
    
    # Create a summary
    create_summary(dump_dir)
    
    print(f"\nSystem dump completed! All data saved to: {dump_dir}")
    print("Review the 'summary.md' file for an overview of the dump.")


if __name__ == "__main__":
    main()
