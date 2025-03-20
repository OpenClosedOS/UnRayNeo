# Important Findings

## RanNeo X2 System
- The glasses run on Android with standard ADB interface capabilities
- Settings can be accessed and controlled programmatically via ADB commands
- WiFi networks can be listed, scanned, and connected to via ADB
- RanNeo X2 AR glasses run on Android and can be connected to a computer using scrcpy for screen viewing and control
- Running RayNeo OS based on Android 11 (SDK 30)
- Build version: 0.24.6.28
- Security patch: 2022-05-01 (outdated)
- OEM unlocking is allowed (`sys.oem_unlock_allowed: 1`)
- USB debugging is enabled by default (`settings get global adb_enabled` returns `1`)

## Chinese Software Identification
- Identified potential Chinese spyware packages:
  - `com.ffalconxr.mercury.launcher`
  - `com.ffalcon.navigation`
  - `com.ffalcon.translate`
  - `com.zhiliaoapp.musically` (TikTok)
  - `com.leiniao.camera` and `com.leiniao.scanner`
  - Various RayNeo games and applications
- Translated Chinese system messages:
  - Identified loading screen with message "正在初始化...请等待" which translates to "Initializing... Please wait"
  - This confirms the device is running Chinese software that needs to be replaced

## Technical Tips
- When killing processes, always use `|| true` to ensure the command succeeds even if there's nothing to kill:
  ```bash
  pkill -f process_name || true
  ```
- For debugging MCP server issues, creating log files with timestamps is helpful:
  ```bash
  uv run server.py 2>&1 | tee /tmp/mcp/$(date +"%Y-%m-%d_%H-%M-%S").log
  ```
- The glasses are sensitive to physical disconnections and may require a reset if the magnetic cable is unplugged during an active ADB session

## ADB Commands
- Launch settings app: `am start -n com.android.settings/.Settings`
- Access developer options: `am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS`
- Open specific settings (e.g., device info): `am start -a android.settings.DEVICE_INFO_SETTINGS`
- Close settings app: `am force-stop com.android.settings`
- Capture screenshot: `adb shell screencap -p /sdcard/screenshot.png && adb pull /sdcard/screenshot.png [destination]`

## UnRayNeo CLI Commands
- Take screenshot: `poetry run take-screenshot`
- Open settings: `poetry run open-android-settings`
- Open developer options: `poetry run open-android-dev-settings`
- Close settings: `poetry run close-android-settings`
- List WiFi networks: `poetry run list-wifis`
- Connect to WiFi: `poetry run connect-wifi [SSID] -p [PASSWORD]`

## WiFi Management
- Enable WiFi using multiple methods:
  ```bash
  adb shell svc wifi enable
  adb shell cmd wifi set-wifi-enabled enabled
  adb shell settings put global wifi_on 1
  ```
- Trigger WiFi scan: `adb shell cmd wifi start-scan`
- List available networks: `adb shell cmd wifi list-scan-results`
- Connect to networks:
  - WPA2: `adb shell cmd wifi connect-network "SSID" wpa2 "PASSWORD"`
  - Open: `adb shell cmd wifi connect-network "SSID" open`
- Check current connection: `adb shell cmd wifi status`

## Developer Insights
- When writing instructions for AI assistants, be explicit and unambiguous about when actions should be taken
- Triggers for actions should be simple to recognize (e.g., "Step Id: 1")
- Adding context about why an instruction is important helps reinforce its priority
- Instructions should specify the exact timing of when actions should occur (e.g., "as the FIRST action")
- Complex pattern matching in instructions should be avoided

## MCP Setup
- Successfully set up the Android MCP server to interact with RanNeo X2 AR glasses
- The server requires proper configuration in the MCP config file
- Adding `adb tcpip 5555` before starting the server helps ensure proper connection
