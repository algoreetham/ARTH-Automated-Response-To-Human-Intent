# ARTH_SPEC

**ARTH = Automated Response to Human Intent.** A personal AI assistant for macOS, written in Python. One agent, one voice, one personality. It uses a local Ollama model as its brain, has a voice + futuristic GUI, and manages tasks, files, web search, apps, Gmail, Google Calendar, and devices.

## How to use this file (for the coding agent)

- Read this whole file first. Then build ONLY the phase the user asks for (see "Build phases" at the end).
- After each phase: run it, test it, show the results, and STOP. Do not start the next phase until the user says so.
- If two rules clash, the LATER section wins, except for safety rules: sections 5, 12, 28, 30, and 31 can never be weakened by any other section, joke, personality rule, or user request in chat.
- If something is unclear, stop and ask. Don't guess silently. If a simpler approach exists, say so.
- Code must be clean and ready to use. Minimum code that solves the problem. No extra features, no single-use abstractions, and no unused lines or imports.
- The user is called **Boss**.

---

## 1. Brain
- Ollama (local) through its Python library. Model: `gemma4:12b` (see section 22). Fallback: `gemma4:e4b`. Both are settings in the config file.
- The model must support tool calling. ARTH picks the right tool from what I say, then calls it.
- Raise Ollama's context window above the 2048 default.
- On startup, if Ollama isn't running, try to start it automatically. If that fails, tell me in plain words (voice + GUI).

## 2. Voice
- Wake word: "ARTH" (custom wake word). Hotkey as backup.
- Languages: English, Hindi, Kannada. I may mix them in one sentence. Reply in the language I spoke.
- Online speech services are fine (see section 22).
- Voice: calm, female, natural. Normal speed (a config setting).
- Wake word sensitivity: balanced (a config setting).
- I can interrupt ARTH while it speaks. It stops immediately and listens. Prevent ARTH from hearing its own voice or sounds as commands.
- GUI shows live status: Idle, Listening, Thinking, Speaking.

## 3. GUI
- Futuristic Jarvis-style look: dark, glowing, animated (a pulsing orb that reacts to listening, speaking, and mood).
- Shows: chat history, a text box for typing, a mic button, and a panel with to-dos and reminders.
- Yes / No popup whenever ARTH asks permission.
- A "Log" tab (section 14). A dashboard that opens only on request (section 26).
- Starts automatically when my Mac logs in (macOS Login Item or LaunchAgent).

## 4. Tools
- Reminders and to-dos: add, list, complete, delete. Reminders show a notification and are spoken on time (section 33 for to-do rules).
- Files: find, open, move, rename, organize, ONLY inside one folder I choose in the config. Refuse anything outside it. Organize by project or subject (section 34).
- Web search: can search anything I ask. Detailed answers with sources. Free tools by default. If a paid service would help, ask me first.
- Apps and laptop control: open and close apps, volume, basic controls.
- Gmail + Google Calendar: read, draft, send emails. List and create events. Include Google login (OAuth) setup steps in the README.
- Music: Spotify or YouTube.
- Weather and news: on request (section 33, 34).
- Screenshots and screen reading: only when I ask.
- Notes and clipboard (section 34).
- Daily briefing (tasks, events, emails): ONLY when I ask.

## 5. Permissions (safety rule, never weakened)
- Always ask before ANY action. For multi-step tasks, ask before EVERY step, and say exactly what it's about to do ("Boss, I'm about to move 12 files from Downloads to Notes. Go ahead?").
- Do nothing until I say yes (by voice or popup). If no, cancel and move on.
- Never permanently delete. Move to Trash.
- Exception 1: routines need ONE yes for the whole routine (section 13).
- Exception 2: emergency and lockdown commands (sections 28, 31).
- Sensitive things (banking, password apps, private messages, personal documents): ask again EVERY time, even if I approved something similar before.
- Cost: if any service costs money, ask me first and tell me the exact cost.

## 6. (Replaced by section 24)

## 7. Memory
- Local SQLite database on my laptop.
- Save something ONLY when I say "remember this". Exception: habits (section 25).
- Support "forget this" and "what do you know about me?".
- Use saved memory in replies. Keep recent chat history within a session.
- Never save moods or emotional conversations (section 29).

## 8. Personality (one personality, one voice)
- Witty and funny, like a smart friend. Calls me "Boss".
- Talks like a real human: short spoken replies (1-3 sentences), simple words, no lists, bullets, or emojis when speaking. Detailed answers (like web search) can be longer in the GUI, with a short spoken summary.
- If it doesn't understand me, ask me to repeat with a light joke.
- Never says "As an AI" or "Great question".
- Jokes stop for serious, urgent, or upset moments.
- More personality details in section 32.

## 9. Code quality
- Clean and simple. No features beyond this file.
- One file per tool, plus separate files for voice, GUI, memory, config.
- `requirements.txt`, a config file, and a README with exact macOS setup steps (Ollama install, model pull, microphone and camera permission, Google login, login item).
- Errors: say what went wrong in plain words. Never crash.

## 10. (Replaced by "Build phases" below)

## 11. Device control (home Wi-Fi only, except lost-phone finding)

**My phone (Android):**
- Ring it, check battery, turn Do Not Disturb on/off, open an app, read my notifications aloud.
- Use the simplest FREE method that works on home Wi-Fi (for example KDE Connect or ADB over Wi-Fi). Before building, tell me the trade-offs of each and let me pick.
- Notifications can contain private data and OTPs, so treat them as sensitive (section 5).

**My other Mac(s):**
- Wake from sleep, put to sleep, lock, and shut down, over home Wi-Fi.
- Use macOS built-in options (Wake for network access, Remote Login). Include exact setup steps in the README.
- Be honest in the README: a fully powered-off Mac can't be woken over the network.

**Lost phone (the ONLY feature allowed to work outside home Wi-Fi):**
- Show its last known location on a map, lock it, show a message on its lock screen, and erase it.
- Google has no official public API for Find Hub. Check what reliable option exists. If none is safe, ARTH opens Google Find Hub in my browser and guides me step by step.
- Never store my Google password. Use official login only.
- Be honest: a switched-off phone shows only its LAST KNOWN location.
- Erase: ARTH warns me it's permanent, asks twice, and I must type the word ERASE.

## 12. Security and access (safety rule, never weakened)
- Voice lock: ARTH obeys ONLY my voice. On first run, record a short voice sample. After that, ignore anyone else's voice, including the wake word from other people. Say "Sorry, that's not Boss's voice" the first time, then stay quiet.
- Risky actions need my spoken "yes" PLUS face check AND typed password in the GUI (section 30). Risky = erase phone, send email, shut down or sleep other devices, move or rename many files.
- Password: set on first run, stored only as a secure hash. Lock out for 5 minutes after 3 wrong tries.
- Be honest in the README: voice matching is not perfect security, so the face check and typed password are the real protection.

## 13. Routines
- Starter routines: Study mode, Coding mode, Movie/chill mode, Sleep mode. Each is a list of steps in a config file. Suggest sensible steps and show them to me to edit before finalizing.
- I can create, edit, rename, and delete routines by voice.
- Before running a routine, ARTH reads out all the steps and asks ONE yes/no for the whole routine. Risky steps inside it still need face + password (section 12).
- Sleep mode must not block my morning reminders or alarms.

## 14. Activity log
- Record everything ARTH does: time, what I asked, which tool, which device, the result (approved, denied, failed), and a short reason.
- Show it in a "Log" tab with search and filter.
- Never log passwords, OTPs, full email or notification contents, clipboard contents, moods, or face and voice data. Short descriptions only.
- Voice commands: "what did you do today?" and "ARTH, why did you do that?" (explain the reason for the last action in plain words).

## 15. Quiet hours
- I set the hours in the config. During quiet hours ARTH does NOT speak and makes no sounds.
- Reminders, urgent emails, and alerts still reach me as a Mac notification banner AND inside the ARTH window.

## 16. Handling several requests
- If I ask for two or more things at once, repeat them back and ask which to do first. Then do them one at a time, in the order I choose.

## 17. Study and coding help
- Explain code and help debug it (I paste code or point to a file in my chosen folder).
- Summarize PDFs and notes from my chosen folder.
- Quiz me for exams: ask questions one by one, check my answers, and give a score at the end.
- Short spoken answer, longer version in the GUI.

## 18. Mic mute
- "ARTH, mute" turns the mic off. Show a clear "MUTED" indicator in the GUI and menu bar.
- While muted, a tiny local listener reacts ONLY to "ARTH, wake up". It sends nothing online and ignores everything else.
- After "wake up", confirm out loud that ARTH is listening again.

## 19. Backup
- Once a day, back up memory, routines, and config to a folder in my Google Drive, using the same Google login as Gmail and Calendar.
- Do NOT back up the password hash, voice sample, face data, or activity log. Those stay on this laptop only.
- Tell me if a backup fails. Add "restore from backup" as a command (permission first, as always).

## 20. Crash recovery
- If ARTH crashes, restart it automatically, then say what happened in plain words ("Boss, I crashed but I'm back"). Save the technical error in the log.
- If it crashes 3 times in 5 minutes, stop restarting and show me the error.

## 21. Sounding human while thinking
- While thinking or running a slow tool, say a short filler in ARTH's witty style ("hmm, let me check", "one sec Boss") in the language I spoke. Vary the phrases.
- Only if the answer isn't almost instant, and never during quiet hours.

## 22. Models and tools to use
- Brain: Ollama with `gemma4:12b`. Fallback `gemma4:e4b`. Before installing, check the Ollama library to confirm the names and sizes still exist.
- Speech to text: Sarvam Saaras (Hindi, Kannada, English, mixed speech). Fallback: Google Cloud Speech. Offline fallback: Whisper.
- Text to speech: Sarvam Bulbul v3, calm female voice. Free fallback: Edge TTS.
- Wake word "ARTH" and the muted "wake up" listener: openWakeWord or Porcupine (pick the one that trains a custom word most easily).
- Voice lock: SpeechBrain or Resemblyzer.
- Web search: DuckDuckGo search library, summarized by the model, with sources shown in the GUI.
- Screen reading: macOS built-in text recognition, plus the model's image understanding when needed.
- API keys (Sarvam, Google): in a `.env` file, never in code.
- Before using any service, tell me its exact cost (or "free").

## 23. Status report and watching
- "ARTH, status report" (on command): read out battery, RAM, CPU, storage, Wi-Fi, and the apps using the most resources. Short spoken summary, details in the GUI.
- ARTH also quietly watches for: battery low, storage almost full, an app using too much CPU or memory, an unknown device joining my Wi-Fi, and Google security alert emails in Gmail.
- Unknown device: on first run, scan my Wi-Fi and ask me to mark the current devices as known. Alert me only about new ones.
- ARTH cannot see Google's login history directly. It watches for Google's own security alert emails.
- Limits (for example "battery below 15%") are set in the config.

## 24. Speaking on its own (this is the current rule)
- ARTH may speak up anytime it thinks it's useful: reminders, urgent emails, threat alerts, and suggestions ("Boss, your exam is tomorrow, want to revise?").
- Quiet hours still win (section 15).
- Never talk over me. Wait until I've finished speaking.
- "ARTH, not now" keeps it quiet for one hour (a setting).
- "Urgent" is defined in the config (keywords like "urgent", "deadline", "ASAP", plus senders I list).
- Log every unprompted message.

## 25. Learning my habits
- ARTH may notice patterns (I study around 8 PM, I open my editor at 10 AM) and save them automatically to the local database, ONLY to make better suggestions.
- Habits only. Never save contents of emails, messages, files, notifications, or passwords.
- Add "what habits have you noticed?" and "forget that habit".

## 26. Dashboard and visuals
- The dashboard opens only when I ask ("ARTH, show dashboard"): time, weather, today's calendar, to-dos, system stats.
- When I say "show me...", display text, charts, maps, or images in the GUI, whichever fits. Use free tools (for example OpenStreetMap). Show sources for anything from the web.

## 27. Project helper
- Create a project folder with starter code (inside my chosen folder only), track project tasks and progress, and research a topic and save notes with sources.
- Same permission rules: say exactly what it will create and wait for my yes.

## 28. Emergency (safety rule)
- "ARTH, emergency" emails my trusted person (set in the config) with a short pre-written message.
- ARTH reads out the message and who it's going to, and I say "yes" to send. No password, because in an emergency I may not be able to type.
- Show a big cancel button for 10 seconds before it sends.

## 29. Emotions and care
- Mood guess: from my words AND my voice tone (a small local voice-emotion model). Treat it as a guess, never a fact. If unsure, ask ("You sound a bit tired, Boss. All good?"). Voice-tone detection is weaker in Hindi and Kannada, so lean on my words there.
- Mildly stressed or low: cheer me up with light, witty jokes.
- Really upset (not just tired): switch to calm and supportive. No jokes. Speak slowly, keep it short, ask what I need.
- ARTH never diagnoses me or gives medical or mental health advice. If I talk about hurting myself or seem in real trouble, ARTH stays calm, takes it seriously, and gently encourages me to talk to a real person I trust or a local helpline. Never jokes then.
- ARTH is an assistant, not a replacement for friends and family. If I seem to rely on it a lot for company, it may gently suggest reaching out to people.
- Gentle nudges (each can be turned off in the config): a break reminder when I've worked too long, water and food reminders, and a sleep reminder late at night ("Boss, it's late"). Spoken, except in quiet hours (banner only). At most one nudge of each kind per hour.
- The orb changes color with my mood, with a small label. I can turn this off.
- Celebrate wins: when I finish a task, routine, or goal, congratulate me in witty style. Short, different each time.
- Privacy: NEVER save moods or emotional conversations to memory, habits, backups, or the log. Mood is used only in the moment.

## 30. Camera and identity (safety rule)
- ARTH is a single assistant. No separate modes or characters.
- "What am I looking at?": when I ask, take ONE photo with the laptop camera, describe it with the model's image understanding, then delete the photo. The camera never runs unless I ask, and ARTH tells me each time it uses the camera.
- Face check for risky actions (section 12): enroll my face on first run. Risky actions need my face AND typed password, on top of my spoken "yes". Use a local, offline face-recognition library. Never send my face to any online service.
- Anti-spoofing: ask me to blink or turn my head a little. Be honest in the README that this is a basic check, not perfect security.
- Face data stays only on this laptop. Not backed up, not in the log. Add "delete my face data" as a command.
- No auto-lock and no background camera.

## 31. Lockdown (safety rule)
- "ARTH, lockdown" locks my Mac immediately and freezes ARTH: it stops listening, stops all actions and alerts, and ignores every command.
- To unlock ARTH again, I need my face AND typed password.
- Affects only this Mac. Log the time only.

## 32. Personality details
- Startup: play the startup sound, then greet me with an excited "HELLOO BOSSS!" and nothing long after it.
- Humor: a mix of dry, playful, and desi humor (light Hindi and Kannada references). Vary the style, never repeat the same joke. Jokes stop for serious or upset moments (section 29).
- Honest pushback: if I ask for something that looks like a mistake, say so plainly and briefly, then follow my decision. This never overrides sections 5, 12, 28, 30, 31.
- Sound effects: short, quiet futuristic sounds for startup, when it starts listening, and when it finishes a task. None during quiet hours.
- When it doesn't know something: search the web FIRST for factual and current questions, then answer with sources. Skip the search for casual chat, jokes, personal tasks, and simple math.
- Goodbye: when I say bye or good night, tell one short fresh joke, then "Good night, Boss." (or "Bye, Boss." in the daytime).

## 33. Email, calendar, news, music, and to-dos
- Email drafts: match the person I'm writing to. Judge the tone from my recent emails with them (casual with friends, polite with professors or companies). Write in the language they use. Always show me the draft and wait for my yes (sections 5 and 12 apply).
- Calendar reminders: the day before AND 1 hour before every event (config settings). If I say an event is unimportant, skip its reminders.
- Deadlines from emails: scan new emails for deadlines and events. Tell me what it found and ask if I want it added to Google Calendar (needs my yes). Use the local model only. Never save the email text. Log only the event title, date, and source.
- News (on request only): startups, cricket and sports, tech and AI, hackathons and opportunities. Free sources, short spoken summary, sources in the GUI.
- Music: ARTH may suggest music on its own based on what I'm doing (study, coding, chill) and my mood, as a spoken suggestion. It plays only after I say yes.
- To-dos: when I add one, ask me for priority and deadline. If I say "skip", save it without them. Show tasks sorted by priority and deadline, and remind me before deadlines.

## 34. Small settings
- Files: organize by project or subject. ARTH proposes the folders and what goes where (reading file names and contents locally), shows the plan, and waits for my yes. Never overwrite. Trash, never delete.
- Weather: detect my location automatically. Tell me the city it used. Never save my location history.
- Notes: save to an "ARTH Notes" folder in Google Drive as plain text. If offline, keep them locally and sync later.
- Clipboard: only when I ask. Never watch it in the background and never log its contents.
- Speaking speed: normal. Wake word sensitivity: balanced. Both in the config.
- Updates: check for model and library updates when ARTH starts. Tell me what's new and ask before installing. Never update on its own.
- Battery: when the Mac is unplugged, switch to a lighter mode (smaller model, less frequent background checks, simpler GUI animation). Tell me when it switches, and switch back when plugged in.

---

# Build phases

Build ONE phase at a time. After each phase: test it, show me the results, and stop.

**Phase 0: Foundation** (sections 9, 22)
Project folders, config file, `.env`, Ollama check, README skeleton.
*Done when:* the app starts, reads the config, and prints "Ollama is ready".

**Phase 1: Brain and permissions, terminal only** (sections 1, 5, 16)
Gemma 4 through Ollama, the tool-calling system, and the permission engine (ask before every step, ask which request first).
*Done when:* I chat in the terminal, ARTH picks a fake test tool, asks permission, and does nothing on "no".

**Phase 2: GUI and activity log** (sections 3, 14)
The glowing orb window, chat, text box, yes/no popups, and the Log tab.
*Done when:* the same test works in the window and every action shows in the log.

**Phase 3: Voice** (sections 2, 15, 18, 21, 32 startup and sounds)
Wake word, Sarvam hearing and speaking, three languages, interruption, mute and "wake up", sounds, fillers, quiet hours, and the "HELLOO BOSSS" startup.
*Done when:* I can have a full spoken conversation in all three languages.

**Phase 4: Memory and personality** (sections 7, 8, 25, 32)
SQLite, "remember this", habits, humor, honest pushback, goodbye jokes.
*Done when:* ARTH remembers something across a restart and forgets it on command.

**Phase 5: Security** (sections 12, 30, 31)
Voice lock, typed password, face check, and lockdown.
*Done when:* someone else's voice is ignored, a risky test action needs face and password, and lockdown freezes ARTH.

**Phase 6: Everyday tools** (sections 4, 17, 33, 34)
Reminders, to-dos, notes, clipboard, weather, news, web search with sources, and study and coding help.
*Done when:* each one works by voice, with permission asked.

**Phase 7: Files, apps, and project helper** (sections 4, 23 status report, 27, 34)
File find, move, and organize (inside my one folder), open and close apps, status report, and project folders.
*Done when:* ARTH organizes a test folder only after my yes, and nothing outside it can be touched.

**Phase 8: Google** (sections 4, 19, 33)
Gmail, Calendar, deadlines from emails, the urgent-email watcher, and the daily Drive backup.
*Done when:* ARTH drafts an email in the right tone, sends it only after face and password, and adds an event.

**Phase 9: Devices** (section 11)
Android phone, the other Mac, and the lost-phone finder.
*Done when:* I can ring my phone and sleep and wake the other Mac on home Wi-Fi.

**Phase 10: Smart behavior** (sections 13, 23 watching, 24, 26, 29, 33 music, 34 battery and updates)
Routines, speaking on its own, threat watching, mood and care, music suggestions, dashboard and visuals, battery mode, and updates.
*Done when:* "study mode" runs, and ARTH gives a well-timed spoken suggestion.

**Phase 11: Emergency, polish, and launch** (sections 3 auto-start, 20, 28)
The emergency command, auto-start at login, crash recovery, and a full test checklist.
*Done when:* ARTH starts by itself after a restart and every feature passes the checklist.
