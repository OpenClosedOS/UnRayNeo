"""
Module for interacting with WiFi settings on RanNeo X2 AR glasses.
"""
import subprocess
import re
import yaml
from pathlib import Path

import settings


def enable_wifi():
    """
    Enable WiFi on the RanNeo X2 AR glasses.
    
    Returns:
        True if WiFi was enabled successfully, False otherwise.
        
    Raises:
        subprocess.CalledProcessError: If the ADB command fails.
    """
    try:
        # Try multiple methods to enable WiFi
        methods = [
            ["adb", "shell", "svc", "wifi", "enable"],
            ["adb", "shell", "cmd", "wifi", "set-wifi-enabled", "enabled"],
            ["adb", "shell", "settings", "put", "global", "wifi_on", "1"]
        ]
        
        for method in methods:
            try:
                subprocess.run(method, check=True, capture_output=True, text=True)
                print(f"Attempted to enable WiFi using: {' '.join(method)}")
            except subprocess.CalledProcessError:
                continue
        
        # Check if WiFi is enabled
        result = subprocess.run(
            ["adb", "shell", "dumpsys", "wifi", "|", "grep", "mWifiState"],
            check=True,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if "ENABLED_STATE" in result.stdout:
            print("WiFi is now enabled")
            return True
        else:
            print("Failed to enable WiFi")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error enabling WiFi: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        raise


def trigger_wifi_scan():
    """
    Trigger a WiFi scan on the RanNeo X2 AR glasses.
    
    Returns:
        True if the scan was triggered successfully, False otherwise.
        
    Raises:
        subprocess.CalledProcessError: If the ADB command fails.
    """
    try:
        subprocess.run(
            ["adb", "shell", "cmd", "wifi", "start-scan"],
            check=True,
            capture_output=True,
            text=True
        )
        
        print("WiFi scan triggered")
        return True
            
    except subprocess.CalledProcessError as e:
        print(f"Error triggering WiFi scan: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        raise


def list_wifi_networks():
    """
    List available WiFi networks using ADB.
    
    Returns:
        A list of dictionaries containing WiFi network information.
    
    Raises:
        subprocess.CalledProcessError: If the ADB command fails.
    """
    try:
        # Run the command to get WiFi scan results
        result = subprocess.run(
            ["adb", "shell", "cmd", "wifi", "list-scan-results"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Parse the output
        networks = []
        lines = result.stdout.strip().split('\n')
        
        # Skip the header line if it exists
        start_idx = 0
        for i, line in enumerate(lines):
            if "BSSID" in line and "SSID" in line:
                start_idx = i + 1
                break
        
        # Process each network
        for line in lines[start_idx:]:
            if not line.strip():
                continue
                
            # Extract network details using regex
            bssid_match = re.search(r'^\s*([0-9a-f:]+)', line)
            freq_match = re.search(r'\s+(\d+)\s+', line)
            rssi_match = re.search(r'-\d+\(', line)
            ssid_match = re.search(r'\s+([^\s].*?)\s+\[', line)
            flags_match = re.search(r'\[(.*)\]$', line)
            
            if bssid_match:
                # Extract RSSI value
                rssi = "Unknown"
                if rssi_match:
                    rssi_start = line.find(rssi_match.group(0))
                    rssi_end = line.find(")", rssi_start)
                    if rssi_end > rssi_start:
                        rssi = line[rssi_start:rssi_end+1]
                
                # Extract SSID (some networks might have empty SSIDs)
                ssid = ""
                if ssid_match:
                    ssid = ssid_match.group(1).strip()
                
                network = {
                    'bssid': bssid_match.group(1).strip(),
                    'frequency': freq_match.group(1).strip() if freq_match else 'Unknown',
                    'rssi': rssi,
                    'ssid': ssid,
                    'flags': flags_match.group(1).strip() if flags_match else 'Unknown'
                }
                networks.append(network)
        
        return networks
        
    except subprocess.CalledProcessError as e:
        print(f"Error listing WiFi networks: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        raise


def connect_to_wifi(ssid, password=None):
    """
    Connect to a WiFi network using ADB.
    
    Args:
        ssid: The SSID of the WiFi network to connect to.
        password: The password for the WiFi network. If None, assumes an open network.
        
    Returns:
        True if connection was successful, False otherwise.
        
    Raises:
        subprocess.CalledProcessError: If the ADB command fails.
    """
    try:
        if password:
            # Connect to a secured network
            result = subprocess.run(
                ["adb", "shell", "cmd", "wifi", "connect-network", ssid, "wpa2", password],
                check=True,
                capture_output=True,
                text=True
            )
        else:
            # Connect to an open network
            result = subprocess.run(
                ["adb", "shell", "cmd", "wifi", "connect-network", ssid, "open"],
                check=True,
                capture_output=True,
                text=True
            )
        
        print(f"Attempting to connect to WiFi network: {ssid}")
        print(f"Command output: {result.stdout.strip()}")
        
        # Check if connection was successful
        if "successfully" in result.stdout.lower():
            return True
        else:
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error connecting to WiFi network: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        raise


def get_current_wifi_connection():
    """
    Get information about the current WiFi connection.
    
    Returns:
        A dictionary containing information about the current WiFi connection,
        or None if not connected.
        
    Raises:
        subprocess.CalledProcessError: If the ADB command fails.
    """
    try:
        # Run the command to get current WiFi connection
        result = subprocess.run(
            ["adb", "shell", "cmd", "wifi", "status"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Parse the output
        output = result.stdout.strip()
        
        # Check if connected
        if "Wifi is disabled" in output or "Not connected" in output:
            return None
            
        # Extract connection details
        ssid_match = re.search(r'SSID: (.*?)($|\n)', output)
        bssid_match = re.search(r'BSSID: (.*?)($|\n)', output)
        ip_match = re.search(r'IP: (.*?)($|\n)', output)
        
        if ssid_match:
            connection = {
                'ssid': ssid_match.group(1).strip(),
                'bssid': bssid_match.group(1).strip() if bssid_match else 'Unknown',
                'ip': ip_match.group(1).strip() if ip_match else 'Unknown'
            }
            return connection
        
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"Error getting current WiFi connection: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        raise


def update_mcp_config(ip_address=None):
    """
    Update the MCP server configuration with the device IP address.
    
    Args:
        ip_address: The IP address to set in the config. If None, will attempt
                    to get the current IP address from the WiFi connection.
                    
    Returns:
        True if the config was updated successfully, False otherwise.
    """
    try:
        # If no IP address provided, get it from the current WiFi connection
        if not ip_address:
            connection = get_current_wifi_connection()
            if not connection or 'ip' not in connection:
                print("Error: Could not determine device IP address")
                return False
                
            ip_address = connection['ip']
        
        # Path to MCP config file
        config_path = Path("/home/user/projects/UnRayNeo/android-mcp-server/config.yaml")
        
        # Read the current config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update the device name (IP address)
        if 'device' not in config:
            config['device'] = {}
            
        config['device']['name'] = ip_address
        
        # Write the updated config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        print(f"Updated MCP config with device IP: {ip_address}")
        return True
        
    except Exception as e:
        print(f"Error updating MCP config: {e}")
        return False
