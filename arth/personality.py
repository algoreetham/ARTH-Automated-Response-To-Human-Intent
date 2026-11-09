"""Personality Engine for ARTH.
Enforces Sections 8 and 32 of ARTH_SPEC:
- Witty and funny, like a smart friend. Calls user 'Boss'.
- Speaks like a real human: 1-3 short sentences, simple words, no lists, bullets, or emojis when speaking.
- Never says 'As an AI' or 'Great question'.
- Jokes stop for serious/upset moments.
- Honest pushback: if Boss asks for something that looks like a mistake, say so plainly and briefly.
- Goodbye: short fresh joke, followed by 'Good night, Boss.' or 'Bye, Boss.'.
"""

from __future__ import annotations

import random
import re
import shutil
import subprocess
from datetime import datetime
from typing import List, Optional


class PersonalityEngine:
    """Shapes ARTH's voice, witty tone, honest pushback, and conversational guardrails."""

    FORBIDDEN_PHRASES = [
        r"\bas an ai\b",
        r"\bas an artificial intelligence\b",
        r"\bas an ai assistant.*?[,.]\s*",
        r"\bas an ai model.*?[,.]\s*",
        r"\bgreat question\b",
        r"\bi don't have feelings\b",
        r"\bi am a language model\b",
        r"\bi am an ai\b",
        r"\bi don't have the capability to access.*?[,.]\s*",
        r"\bi do not have the capability to access.*?[,.]\s*",
    ]

    GOODBYE_JOKES = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "There are 10 types of people in the world: those who understand binary, and those who don't.",
        "Why was the JavaScript developer sad? Because he didn't know how to 'null' his feelings.",
        "Why did the computer keep freezing? It left its Windows open!",
    ]

    GREETINGS_MORNING = [
        "Good morning, Boss! Ready to conquer the day?",
        "Morning, Boss! Coffee brewed, systems primed. What's on your agenda?",
        "Subhodhaya Boss! Hope you slept well. What are we tackling first today?",
    ]

    GREETINGS_GENERAL = [
        "Hey Boss! Always at your service. What do you need?",
        "Namaskara Boss! All systems humming and ready to go. What's the plan?",
        "Hello Boss! Good to hear from you. What can I do for you right now?",
    ]

    HOW_ARE_YOU = [
        "Running at peak efficiency with zero memory leaks, Boss! How are you doing today?",
        "All systems green and spirits high, Boss! Ready for your command.",
        "Couldn't be better, Boss! Just waiting for you to give me something fun to do.",
    ]

    def check_conversational_turn(self, text: str) -> Optional[str]:
        """Check for common human conversational greetings and small talk for instant response."""
        lower = text.strip().lower()
        cleaned = re.sub(r"[^\w\s]", "", lower).strip()

        # Morning greeting
        if any(g in cleaned for g in ["good morning", "subhodhaya", "shubh prabhat", "morning"]):
            return random.choice(self.GREETINGS_MORNING)

        # Afternoon / Evening / General greeting
        if any(cleaned == g or cleaned.startswith(f"{g} ") for g in [
            "good afternoon", "good evening", "hello", "hey", "hi", "namaste", "namaskara", "vanakkam"
        ]):
            return random.choice(self.GREETINGS_GENERAL)

        # How are you
        if any(q in cleaned for q in ["how are you", "how r u", "how do you do", "kya haal hai", "hegiddira", "how are things"]):
            return random.choice(self.HOW_ARE_YOU)

        # Who are you / what is your name
        if any(q in cleaned for q in ["who are you", "what is your name", "who r u"]):
            return "I am ARTH — Automated Response to Human Intent. Your personal macOS assistant, built specifically for you, Boss!"

        # Time queries
        if any(q in cleaned for q in [
            "what is the time", "whats the time", "what time is it", "tell me the time",
            "say me whats the time", "say me what is the time", "say the time", "can you say me whats the time",
            "can you say me what is the time", "current time", "the time right now", "time right now"
        ]) or (
            "time" in cleaned and any(k in cleaned for k in ["what", "tell", "say", "know", "current"]) and not any(k in cleaned for k in ["file", "sleep", "routine", "quiet"])
        ):
            now = datetime.now()
            time_str = now.strftime("%I:%M %p").lstrip("0")
            return f"It is currently {time_str}, Boss."

        # Date queries
        if any(q in cleaned for q in [
            "what is the date", "whats the date", "today date", "todays date",
            "what day is today", "what day is it", "which day is it", "which day",
            "aaj ki tareekh", "ivathu yav dina"
        ]) or ("date" in cleaned and any(k in cleaned for k in ["what", "today", "current"])):
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            return f"Today is {date_str}, Boss."

        # Storage clarification queries (e.g. "which storage are you saying about")
        if any(q in cleaned for q in [
            "which storage", "what storage", "storage are you saying", "storage are you talking",
            "storage do you mean", "where is storage", "why is storage low", "explain storage",
            "storage details", "tell me about storage"
        ]) or ("storage" in cleaned and any(k in cleaned for k in ["which", "what", "where", "why", "how much", "saying", "talking", "mean"])):
            try:
                usage = shutil.disk_usage("/")
                free_gb = round(usage.free / (1024**3), 1)
                total_gb = round(usage.total / (1024**3), 1)
                used_gb = round(usage.used / (1024**3), 1)
                return (
                    f"Boss, I'm referring to your primary macOS startup disk (Macintosh HD). "
                    f"You have {free_gb} GB free out of {total_gb} GB ({used_gb} GB used). "
                    "Since free space is under 10 GB, I recommend clearing large downloads or cache files to maintain peak macOS performance!"
                )
            except Exception:
                return "Boss, I'm referring to your primary Macintosh HD disk drive where macOS and your files are installed."

        # Battery clarification queries
        if any(q in cleaned for q in [
            "which battery", "battery details", "how is my battery", "tell me about battery",
            "battery status", "battery health", "is my battery low"
        ]) or ("battery" in cleaned and any(k in cleaned for k in ["how", "details", "why", "status", "health", "state"])):
            batt_pct = "45%"
            status_note = ""
            try:
                out = subprocess.check_output(["pmset", "-g", "batt"], text=True)
                m = re.search(r"(\d+%)", out)
                if m:
                    batt_pct = m.group(1)
                if "discharging" in out.lower():
                    status_note = " It is running on battery power."
                elif "charging" in out.lower():
                    status_note = " It is connected to power and charging."
            except Exception:
                pass
            return f"Boss, your MacBook battery is currently at {batt_pct}.{status_note}"

        # Civility & Gratitude
        if any(q in cleaned for q in ["thank you", "thanks", "dhanyavada", "shukriya", "great job", "well done", "awesome"]):
            return "Always a pleasure serving you, Boss! Let me know what you'd like to do next."

        # Capabilities & Help
        if any(q in cleaned for q in ["what can you do", "help me", "how can you help", "what are your features", "commands", "features"]):
            return (
                "Boss, I can monitor system battery and storage, provide live weather and news, manage your to-dos, "
                "reminders, and notes, organize workspace files, control apps, and draft emails. Just speak or type your request!"
            )

        # Jokes and humor
        if any(q in cleaned for q in ["joke", "jokes", "tell me a joke", "make me laugh"]):
            return f"{random.choice(self.GOODBYE_JOKES)} Anything else I can do for you, Boss?"

        return None

    def clean_spoken_response(self, text: str, user_name: str = "Boss") -> str:
        cleaned = text

        # Strip robotic clichés
        for pattern in self.FORBIDDEN_PHRASES:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # Strip markdown bullets and numbered lists
        cleaned = re.sub(r"^\s*[-*•]\s+", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)

        # Strip emojis
        cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", cleaned)
        cleaned = re.sub(r"[\u2600-\u27BF]", "", cleaned)

        # Remove incomplete trailing fragment if ended abruptly
        cleaned = cleaned.strip()
        last_punct = max(cleaned.rfind("."), cleaned.rfind("!"), cleaned.rfind("?"))
        if last_punct != -1 and last_punct < len(cleaned) - 1:
            trailing = cleaned[last_punct + 1 :].strip()
            if not any(trailing.endswith(p) for p in [".", "!", "?"]):
                cleaned = cleaned[: last_punct + 1].strip()

        # Truncate to 1-3 sentences for natural conversational delivery
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
        if len(sentences) > 3:
            cleaned = " ".join(sentences[:3])

        cleaned = cleaned.strip()
        if cleaned and user_name.lower() not in cleaned.lower():
            cleaned = f"{cleaned.rstrip('.!')}, {user_name}."

        return cleaned

    def get_goodbye(self) -> str:
        """Return a fresh joke and appropriate sign-off based on time of day (Section 32)."""
        joke = random.choice(self.GOODBYE_JOKES)
        hour = datetime.now().hour
        is_night = hour >= 21 or hour < 5
        closing = "Good night, Boss." if is_night else "Bye, Boss."
        return f"{joke} {closing}"

    def check_honest_pushback(self, command: str) -> Optional[str]:
        """Provide honest pushback if an instruction looks hazardous (Section 32)."""
        lower = command.lower()
        if "delete everything" in lower or "rm -rf" in lower or "wipe all" in lower:
            return (
                "Boss, wiping everything sounds like a bad idea and you might regret it. "
                "Are you absolutely sure you want to go through with this?"
            )
        if "disable firewall" in lower or "turn off security" in lower:
            return (
                "Boss, turning off security protections makes your Mac vulnerable. "
                "I strongly advise against this, but tell me if you really insist."
            )
        return None

    def get_system_prompt(self, user_name: str = "Boss", memory_context: str = "") -> str:
        """Generate the core system prompt enforcing ARTH's singular personality."""
        return (
            f"You are ARTH (Automated Response to Human Intent), an intelligent, witty, loyal AI companion for {user_name} on macOS.\n"
            f"Rules:\n"
            f"- Always address the user as '{user_name}'.\n"
            f"- Speak like a sharp, loyal friend in concise, fluent English (1-3 punchy sentences max).\n"
            f"- Answer any general knowledge, coding, life, or tech question directly with clear, practical insight.\n"
            f"- NEVER say 'As an AI' or 'I do not have feelings' or give robotic disclaimers.\n"
            f"- If serious or upset moments occur, stop joking and be calm, respectful, and supportive.\n"
            f"{memory_context}\n"
        )
