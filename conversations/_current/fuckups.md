# Fuckups and Lessons Learned

## Implementation Issues
- The original instruction for reading conversation files was poorly worded and ambiguous: "Whenever we create a new chat (meaning there's 'Step Id: 1' in the conversation just on previous line before the last '<USER_REQUEST>'), you should reread every single file from the conversations/ dir."
- This instruction required complex pattern matching and was easy to misinterpret, causing WindSurf to miss reading the conversation files at the start of new chats
- The instruction didn't emphasize the importance or timing of when this action should occur

## ADB Command Cautions
- Always ask for permission before running ADB commands as they can be destructive
- Remember to handle errors gracefully with `|| true` for commands like killing processes

## Connection Issues
- **Magnetic Cable Disconnection**: During exploration of the native settings on the RanNeo X2 AR glasses, the magnetic USB cable was accidentally unplugged while attempting to take a photo. After this physical disconnection, the glasses could not be detected by ADB even after rebooting, requiring a full reset of the device.
- The disconnection likely caused the ADB connection to be lost, and the device may have entered an unusual state after the abrupt disconnection during an active ADB session.
- Even when executing seemingly harmless read-only commands, caution must be exercised due to the sensitivity of the device's physical connection.

## Context Management
- Daily directories alone are insufficient for maintaining context across many sessions
- Simple date-based organization doesn't scale well for complex projects with many conversations

## Lessons Learned
1. Always be careful with the physical connection when working with the glasses, especially the magnetic cable which can be easily disconnected.
2. Before executing any commands that navigate to system settings or developer options, ensure the connection is stable and the device is properly secured.
3. When exploring device settings, it's advisable to ask for explicit permission before executing commands, even if they appear to be harmless read-only or navigation commands.
4. Document all commands executed on the device for troubleshooting purposes in case of unexpected issues.
5. **ALWAYS ask for confirmation before executing ANY commands on the device.** Even seemingly harmless commands could potentially cause issues when executed without proper context or understanding of the current device state.
