"""
Command-line interface for UnRayNeo tools.
"""
import argparse
import sys
from pathlib import Path

from unrayneo.screenshot import capture_screenshot
from unrayneo.settings_utils import SettingsPage, open_settings
from unrayneo.wifi import (
    list_wifi_networks, 
    get_current_wifi_connection, 
    update_mcp_config,
    enable_wifi,
    trigger_wifi_scan,
    connect_to_wifi
)


def take_screenshot_command():
    """Command to take a screenshot from the RanNeo X2 AR glasses."""
    parser = argparse.ArgumentParser(description="Capture a screenshot from RanNeo X2 AR glasses")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Custom output path for the screenshot",
    )
    
    args = parser.parse_args(sys.argv[1:])
    
    try:
        screenshot_path = capture_screenshot(args.output)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def open_android_settings_command():
    """Command to open Android settings on the RanNeo X2 AR glasses."""
    parser = argparse.ArgumentParser(description="Open Android settings on RanNeo X2 AR glasses")
    parser.add_argument(
        "-p", "--page",
        type=str,
        choices=[page.name.lower() for page in SettingsPage],
        default="main",
        help="Settings page to open (default: main)",
    )
    
    args = parser.parse_args(sys.argv[1:])
    
    # Convert the page name to the enum value
    page_name = args.page.upper()
    page = SettingsPage[page_name]
    
    try:
        open_settings(page)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def open_android_dev_settings_command():
    """Command to open Android Developer Options on the RanNeo X2 AR glasses."""
    parser = argparse.ArgumentParser(description="Open Android Developer Options on RanNeo X2 AR glasses")
    
    # Parse args but don't use them - this is just for help text
    parser.parse_args(sys.argv[1:])
    
    try:
        open_settings(SettingsPage.DEVELOPER_OPTIONS)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def list_wifis_command():
    """Command to list available WiFi networks on the RanNeo X2 AR glasses."""
    parser = argparse.ArgumentParser(description="List available WiFi networks on RanNeo X2 AR glasses")
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Update the MCP config with the current IP address",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable WiFi before listing networks",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Trigger a WiFi scan before listing networks",
    )
    
    args = parser.parse_args(sys.argv[1:])
    
    try:
        # Enable WiFi if requested
        if args.enable:
            enable_wifi()
        
        # Trigger a WiFi scan if requested
        if args.scan:
            trigger_wifi_scan()
        
        # Get current connection first
        current = get_current_wifi_connection()
        if current:
            print("\nCurrent WiFi Connection:")
            print(f"  SSID: {current['ssid']}")
            print(f"  BSSID: {current['bssid']}")
            print(f"  IP: {current['ip']}")
            
            # Update MCP config if requested
            if args.update_config:
                update_mcp_config(current['ip'])
        else:
            print("\nNot currently connected to any WiFi network")
        
        # List available networks
        networks = list_wifi_networks()
        
        if networks:
            print("\nAvailable WiFi Networks:")
            for i, network in enumerate(networks, 1):
                # Only show networks with non-empty SSIDs
                if network['ssid']:
                    print(f"\n{i}. {network['ssid']}")
                    print(f"   BSSID: {network['bssid']}")
                    print(f"   Frequency: {network['frequency']} MHz")
                    print(f"   Signal Strength: {network['rssi']}")
                    print(f"   Security: {network['flags']}")
        else:
            print("\nNo WiFi networks found")
            
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def connect_wifi_command():
    """Command to connect to a WiFi network on the RanNeo X2 AR glasses."""
    parser = argparse.ArgumentParser(description="Connect to a WiFi network on RanNeo X2 AR glasses")
    parser.add_argument(
        "ssid",
        type=str,
        help="SSID of the WiFi network to connect to",
    )
    parser.add_argument(
        "-p", "--password",
        type=str,
        help="Password for the WiFi network (not required for open networks)",
    )
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Update the MCP config with the IP address after connecting",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable WiFi before connecting",
    )
    
    args = parser.parse_args(sys.argv[1:])
    
    try:
        # Enable WiFi if requested
        if args.enable:
            enable_wifi()
        
        print(f"Connecting to WiFi network: {args.ssid}")
        success = connect_to_wifi(args.ssid, args.password)
        
        if success:
            print(f"Successfully connected to {args.ssid}")
            
            # Wait a moment for the connection to stabilize
            import time
            time.sleep(2)
            
            # Get the current connection details
            current = get_current_wifi_connection()
            if current:
                print(f"IP address: {current['ip']}")
                
                # Update MCP config if requested
                if args.update_config:
                    update_mcp_config(current['ip'])
            else:
                print("Warning: Connected but couldn't get IP address")
        else:
            print(f"Failed to connect to {args.ssid}")
            return 1
            
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
