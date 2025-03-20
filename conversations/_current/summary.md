# UnRayNeo Project Summary

This project aims to install a clean Android system without unwanted Chinese software on RanNeo X2 AR glasses. Key areas of focus:

1. **Core Functionality**: Creating Python utilities for basic operations like taking screenshots, opening/closing settings, and managing WiFi connections.
2. **System Exploration**: Investigating the Android system on the glasses to better understand its capabilities and limitations.
3. **Context Management**: Implementing a robust conversation logging system to maintain context across multiple chat sessions.

## System Information
- Running RayNeo OS based on Android 11 (SDK 30)
- Build version: 0.24.6.28
- Security patch: 2022-05-01 (outdated)
- OEM unlocking is allowed (`sys.oem_unlock_allowed: 1`)

## Current Capabilities
- Screenshot capture and organization in structured directories
- Settings page navigation and control
- WiFi scanning, listing, and connection management
- UI layout analysis through ADB

## Chinese Software Identification
- Identified Chinese interface elements with text "正在初始化...请等待" ("Initializing... Please wait")
- Numerous Chinese packages have been identified that will need to be replaced

Current stage: Early exploration and utility development with several basic functions implemented.
