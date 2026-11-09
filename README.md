# ARTH (Automated Response to Human Intent)

ARTH is a personal AI assistant for macOS built in Python. One agent, one voice, one personality. Powered by a local Ollama brain (`gemma4:12b`), ARTH includes voice interaction, a futuristic Jarvis-style GUI, local SQLite memory, file management, task tracking, Google Workspace integration, and device controls.

---

## Architecture Overview

```
ARTH System
├── Brain: Local Ollama (gemma4:12b / gemma4:e4b) with custom tools & >2048 context window
├── Voice: Wake word ("ARTH"), Sarvam STT (Saaras) & TTS (Bulbul v3), three languages (EN, HI, KN)
├── GUI: Futuristic glowing orb, interactive chat, Yes/No approval popups, activity log
├── Memory: SQLite database on laptop (explicit memory & habit tracking)
├── Security: Spoken approval + Face check + Password for sensitive tasks; Voice Lock; Lockdown mode
└── Tools: Files (restricted folder), Tasks/To-dos, Web search, Apps, Gmail, Calendar
```

---

## macOS Setup Guide

### 1. Install Ollama
ARTH requires Ollama for local LLM inference.
- **Option A (Homebrew):**
  ```bash
  brew install ollama
  ```
- **Option B (Direct Download):**
  Download the macOS application from [ollama.com/download](https://ollama.com/download) and drag it to your `/Applications` folder.

Start the Ollama service:
```bash
ollama serve
```

### 2. Pull the Models
ARTH uses `gemma4:12b` as its primary brain and `gemma4:e4b` as its battery/lightweight fallback:
```bash
ollama pull gemma4:12b
ollama pull gemma4:e4b
```

### 3. Environment & Dependencies Setup
Ensure Python 3.10+ is installed:
```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in any external API keys:
```bash
cp .env.example .env
```
*Note: Phase 0 and local inference require no paid API keys.*

### 4. macOS Permissions
To enable full voice, vision, and system control features in future phases, grant the following permissions in **System Settings > Privacy & Security**:
- **Microphone**: Allow Terminal / IDE / Python to record audio for voice commands and wake-word detection.
- **Camera**: Allow access for face check authentication and vision tools.
- **Accessibility**: Allow control of system volume, app window manipulation, and global hotkeys.
- **Full Disk Access**: If accessing files in custom user directories outside the app sandbox.

### 5. Google OAuth Login Setup (Gmail, Calendar, Drive)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project named `ARTH-Assistant`.
3. Enable the **Gmail API**, **Google Calendar API**, and **Google Drive API**.
4. Configure the OAuth Consent Screen (User Type: External, Testing mode).
5. Create OAuth 2.0 Client IDs (Application type: Desktop App).
6. Download the client secret JSON or copy the Client ID and Secret into your `.env` file:
   ```env
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```

### 6. Auto-Start on macOS Login
To launch ARTH automatically when logging in to your Mac:
- **Option A (Login Items):**
  Open **System Settings > General > Login Items**, click the `+` button under "Open at Login", and add the ARTH launcher script or application.
- **Option B (LaunchAgent):**
  Create a launch plist at `~/Library/LaunchAgents/com.arth.assistant.plist` pointing to `python3 /path/to/ARTH/main.py`.

---

## Security & Limitations (Full Disclosure)

1. **Remote Mac Wake Limitations:**
   A Mac that is completely powered off cannot be woken over the network. Wake-on-LAN / Wake for network access only works when the remote Mac is sleeping.
2. **Voice Matching Limitations:**
   Voice recognition / speaker identification is not foolproof. Background noise, recordings, or similar voices can cause false matches. For this reason, all sensitive and destructive actions strictly require a **face check AND typed password** in addition to spoken approval.
3. **Face Check & Anti-Spoofing:**
   The face check utilizes local offline detection and asks the user to blink or move slightly. While effective against static photos, it remains a secondary verification layer alongside your password.
4. **Safety Invariants:**
   Safety rules (Sections 5, 12, 28, 30, and 31) can never be overridden. ARTH will never permanently delete files (items are moved to macOS Trash), always asks before every step, and immediately locks down upon command.

---

## Running Phase 0

To verify that the project structure, configuration, and Ollama connection are properly set up:

```bash
python3 main.py
```

When Ollama is running and accessible, the output will confirm:
```
Loaded configuration for Boss.
Configured brain: gemma4:12b (fallback: gemma4:e4b, context window: 8192)
Ollama is ready
```
