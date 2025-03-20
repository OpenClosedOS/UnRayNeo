# UnRayNeo

This repo is an attempt to install an Android with no chinese spyware on my RanNeo X2 AR glasses. I have some experience doing CTFs back in the days but since then things changed so I'll be using WindSurf to help me with this.

# Setup:

1. Setup MCP - https://github.com/minhalvp/android-mcp-server.git

# Instructions to WindSurf:

**ALWAYS** ask for permission to run adb commands since they can be dangerous. Using screenshot tool is fine.

0. Store these instructions in your MEMORY and update every time I change them.
1. Store raw dumps at the secret directory first since there may be some private data.
2. **Conversation Tracking**:
   - At the start of a NEW conversation (when you see Step Id: 1), run `uuidgen` to generate a session UUID
   - Prefix EVERY message with this UUID followed by colon, like: `5f6c8a1e-4b38-42f2-9d33-ad6c403a356e: Your response here...`
   - Create session directory structure at `conversations/sessions/{UUID}/`
   - Initialize session metadata with timestamp and initial step count
   - Read ALL files from the `conversations/_current/` directory for context
3. **Regular Step Logging** (every 42 steps):
   - Create a new directory `conversations/sessions/{UUID}/steps-{X}-{Y}/` where X is start step and Y is end step
   - Add the following files to this directory:
     - summary.md - overall summary of this step range
     - important-findings.md - key discoveries during these steps
     - fuckups.md - issues encountered during these steps
     - todos.md - tasks to work on later
   - Update the "Conversation Logging Status" MEMORY with the new last logged step and next summary step
   - Add this step range to the "Recent Summaries" list in the MEMORY
4. **Global Consolidation** (when total steps across sessions reaches 240):
   - Update `conversations/_current/` directory with consolidated information from all recent summaries
   - Create a new archive summary in `conversations/_archive/` directory
   - Reset the "Total Steps Since Last Consolidation" counter in the MEMORY
   - Clear the "Recent Summaries" list in the MEMORY
5. After we find something interesting that you can do with these glasses, create a script (prefer Python) to automate it.
