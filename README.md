# UnRayNeo

This repo is an attempt to install an Android with no chinese spyware on my RanNeo X2 AR glasses. I have some experience doing CTFs back in the days but since then things changed so I'll be using WindSurf to help me with this.

# Setup:

1. Setup MCP - https://github.com/minhalvp/android-mcp-server.git

# Instructions to WindSurf:

**ALWAYS** ask for permission to run adb commands since they can be dangerous.

0. Store these instructions in your MEMORY and update every time I change them.
1. Store raw dumps at the secret directory first since there may be some private data.
2. Once in a while, update the corresponding conversation's log. They are stored in the conversations/{YEAR}/{MONTH}/{DAY}/ dir and there are the following files:
    - short-summary.txt - one paragraph about the conversation
    - long-summary.txt - a few paragraphs about the conversation
    - important-findings.txt - important findings that we may refer to later. It can be things we figured out about these specific glasses, useful commands, etc.
    - fuckups.txt - things that got us into trouble, here we want to have a detailed description of what happened, why and how to fix it
    - todos.txt - things we need to work on later
3. Before updating the conversations/ dir, check the current date if it did not change.
4. After we find something interesting that you can do with these glasses, create a script (prefer Python) to automate it.
5. Whenever we create a new chat (meaning there's "Step Id: 0" in the conversation) just before my message, you should reread every single file from the conversations/ dir.
