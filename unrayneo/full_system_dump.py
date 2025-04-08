"""
Full System Dump Utility for RanNeo X2 AR Glasses

This script performs a comprehensive dump of ALL system information from RanNeo X2 AR glasses.
It uses alternative methods to extract as much data as possible without requiring root access.
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
DUMP_DIR = settings.SECRET_DIR / f"full_system_dump_{TIMESTAMP}"


def setup_dump_directory() -> Path:
    """Create and return the dump directory path."""
    dump_dir = DUMP_DIR
    dump_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    subdirs = [
        "partitions", "props", "apks", "logs", "bootloader", "bluetooth",
        "input", "services", "firmware", "hardware", "security", "system_files",
        "memory", "network", "display", "sensors", "audio", "camera", "databases",
        "settings", "packages", "permissions", "accounts", "media"
    ]
    
    for subdir in subdirs:
        (dump_dir / subdir).mkdir(exist_ok=True)
    
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


def dump_all_properties(dump_dir: Path) -> None:
    """
    Dump ALL system properties.
    """
    print("Dumping ALL system properties...")
    props_dir = dump_dir / "props"
    
    # Get all properties
    _, all_props, _ = run_adb_command(["adb", "shell", "getprop"])
    save_to_file(props_dir / "all_properties.txt", all_props)
    
    # Get properties by category
    categories = [
        "build", "ro", "sys", "persist", "debug", "service", "init", 
        "dev", "gsm", "net", "wifi", "bluetooth", "dalvik", "pm", 
        "camera", "audio", "media", "display", "hw", "security"
    ]
    
    for category in categories:
        _, category_props, _ = run_adb_command(["adb", "shell", "getprop", "|", "grep", category])
        save_to_file(props_dir / f"{category}_properties.txt", category_props)


def dump_all_services(dump_dir: Path) -> None:
    """
    Dump ALL system services.
    """
    print("Dumping ALL system services...")
    services_dir = dump_dir / "services"
    
    # Get list of all services
    _, services_list, _ = run_adb_command(["adb", "shell", "service", "list"])
    save_to_file(services_dir / "services_list.txt", services_list)
    
    # Dump all services using dumpsys
    _, all_services, _ = run_adb_command(["adb", "shell", "dumpsys", "-l"])
    service_names = []
    
    for line in all_services.splitlines():
        line = line.strip()
        if line and not line.startswith("Currently running services:"):
            service_names.append(line)
    
    for service in service_names:
        print(f"  Dumping service: {service}")
        _, service_dump, _ = run_adb_command(["adb", "shell", "dumpsys", service], check=False)
        safe_name = service.replace(".", "_").replace("/", "_").replace(":", "_")
        save_to_file(services_dir / f"{safe_name}.txt", service_dump)


def dump_all_packages(dump_dir: Path) -> None:
    """
    Dump ALL package information.
    """
    print("Dumping ALL package information...")
    packages_dir = dump_dir / "packages"
    
    # Get list of all packages
    _, packages, _ = run_adb_command(["adb", "shell", "pm", "list", "packages", "-f"])
    save_to_file(packages_dir / "all_packages.txt", packages)
    
    # Get detailed package info for all packages
    package_names = []
    for line in packages.splitlines():
        if line.startswith("package:"):
            parts = line.split("=")
            if len(parts) > 1:
                package_names.append(parts[1])
    
    for package in package_names:
        print(f"  Dumping package info: {package}")
        _, package_info, _ = run_adb_command(["adb", "shell", "dumpsys", "package", package], check=False)
        safe_name = package.replace(".", "_")
        save_to_file(packages_dir / f"{safe_name}_info.txt", package_info)
        
        # Get permissions for the package
        _, permissions, _ = run_adb_command(["adb", "shell", "dumpsys", "package", package, "|", "grep", "permission"], check=False)
        save_to_file(packages_dir / f"{safe_name}_permissions.txt", permissions)


def dump_all_settings(dump_dir: Path) -> None:
    """
    Dump ALL system settings.
    """
    print("Dumping ALL system settings...")
    settings_dir = dump_dir / "settings"
    
    # Get all settings
    settings_types = ["system", "secure", "global"]
    
    for setting_type in settings_types:
        _, settings_values, _ = run_adb_command(["adb", "shell", "settings", "list", setting_type])
        save_to_file(settings_dir / f"{setting_type}_settings.txt", settings_values)


def dump_all_databases(dump_dir: Path) -> None:
    """
    Dump information about system databases.
    """
    print("Dumping database information...")
    db_dir = dump_dir / "databases"
    
    # Find all SQLite databases
    _, databases, _ = run_adb_command(["adb", "shell", "find", "/data/data", "-name", "*.db", "2>/dev/null"], check=False)
    save_to_file(db_dir / "database_paths.txt", databases)
    
    # Try to get database schemas where possible
    for line in databases.splitlines():
        if not line or "Permission denied" in line:
            continue
        
        db_path = line.strip()
        db_name = os.path.basename(db_path)
        print(f"  Attempting to get schema for: {db_name}")
        
        _, schema, _ = run_adb_command(["adb", "shell", f"sqlite3 {db_path} '.schema' 2>/dev/null"], check=False)
        if schema and "Error" not in schema and "Permission denied" not in schema:
            safe_name = db_name.replace(".", "_")
            save_to_file(db_dir / f"{safe_name}_schema.txt", schema)


def dump_all_hardware_info(dump_dir: Path) -> None:
    """
    Dump ALL hardware information.
    """
    print("Dumping ALL hardware information...")
    hw_dir = dump_dir / "hardware"
    
    # CPU info
    _, cpu_info, _ = run_adb_command(["adb", "shell", "cat", "/proc/cpuinfo"])
    save_to_file(hw_dir / "cpu_info.txt", cpu_info)
    
    # Memory info
    _, memory_info, _ = run_adb_command(["adb", "shell", "cat", "/proc/meminfo"])
    save_to_file(hw_dir / "memory_info.txt", memory_info)
    
    # Device tree
    _, device_tree, _ = run_adb_command(["adb", "shell", "find", "/proc/device-tree", "-type", "f", "-exec", "echo", "{}", ";", "-exec", "cat", "{}", ";", "2>/dev/null"], check=False)
    save_to_file(hw_dir / "device_tree.txt", device_tree)
    
    # Hardware components
    components = {
        "gpu": ["adb", "shell", "dumpsys", "SurfaceFlinger"],
        "display": ["adb", "shell", "dumpsys", "display"],
        "sensors": ["adb", "shell", "dumpsys", "sensorservice"],
        "camera": ["adb", "shell", "dumpsys", "media.camera"],
        "audio": ["adb", "shell", "dumpsys", "audio"],
        "battery": ["adb", "shell", "dumpsys", "battery"],
        "thermal": ["adb", "shell", "dumpsys", "thermalservice"],
        "usb": ["adb", "shell", "dumpsys", "usb"],
        "wifi": ["adb", "shell", "dumpsys", "wifi"],
        "bluetooth": ["adb", "shell", "dumpsys", "bluetooth_manager"]
    }
    
    for component, command in components.items():
        _, output, _ = run_adb_command(command, check=False)
        save_to_file(hw_dir / f"{component}_info.txt", output)


def dump_all_system_files(dump_dir: Path) -> None:
    """
    Attempt to dump all accessible system files.
    """
    print("Dumping all accessible system files...")
    files_dir = dump_dir / "system_files"
    
    # List of important system directories to dump
    system_dirs = [
        "/system/etc",
        "/system/usr",
        "/system/bin",
        "/system/xbin",
        "/vendor/etc",
        "/vendor/bin",
        "/vendor/firmware",
        "/vendor/overlay",
        "/system/app",
        "/system/priv-app",
        "/vendor/app",
        "/vendor/overlay",
        "/system/framework"
    ]
    
    for directory in system_dirs:
        dir_name = directory.replace("/", "_").strip("_")
        target_dir = files_dir / dir_name
        target_dir.mkdir(exist_ok=True)
        
        print(f"  Listing files in {directory}...")
        _, file_list, _ = run_adb_command(["adb", "shell", f"find {directory} -type f -name '*.xml' -o -name '*.conf' -o -name '*.json' -o -name '*.prop' -o -name '*.rc' 2>/dev/null"], check=False)
        save_to_file(target_dir / "file_list.txt", file_list)
        
        # Try to pull some important config files
        for line in file_list.splitlines():
            if not line or "Permission denied" in line:
                continue
            
            file_path = line.strip()
            file_name = os.path.basename(file_path)
            
            if any(ext in file_name for ext in [".xml", ".conf", ".json", ".prop", ".rc"]):
                print(f"    Attempting to extract: {file_name}")
                _, file_content, _ = run_adb_command(["adb", "shell", f"cat {file_path} 2>/dev/null"], check=False)
                
                if file_content and "Permission denied" not in file_content:
                    safe_name = file_name.replace("/", "_")
                    save_to_file(target_dir / safe_name, file_content)


def main():
    """Main function to coordinate the full system dump."""
    print(f"Starting FULL system dump for RanNeo X2 AR Glasses...")
    print(f"All data will be saved to: {DUMP_DIR}")
    
    # Set up the dump directory
    dump_dir = setup_dump_directory()
    
    # Perform comprehensive dumps
    dump_all_properties(dump_dir)
    dump_all_services(dump_dir)
    dump_all_packages(dump_dir)
    dump_all_settings(dump_dir)
    dump_all_databases(dump_dir)
    dump_all_hardware_info(dump_dir)
    dump_all_system_files(dump_dir)
    
    print(f"\nFull system dump completed! All data saved to: {dump_dir}")
    print("This dump includes all accessible system information without requiring root access.")


if __name__ == "__main__":
    main()
