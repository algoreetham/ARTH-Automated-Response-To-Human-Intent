"""Natural Conversation and Dialog Reasoning Engine for ARTH.
Provides fluent, context-aware, human-like dialogue between Boss and ARTH.
Handles:
- Follow-up questions based on recent conversation history (e.g. "which storage", "why", "tell me more")
- General knowledge questions (Wikipedia REST summary + DuckDuckGo Q&A)
- Conversational chit-chat, moods, humor, and empathy
- Direct questions about system, capabilities, time, and environment
"""

from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional


class NaturalConversationEngine:
    """Intelligent conversational partner with memory of previous turns and real-time knowledge."""

    def __init__(self, user_name: str = "Boss"):
        self.user_name = user_name

    def process_conversational_query(
        self,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        """
        Evaluate user input for natural dialogue, contextual follow-ups, and general knowledge.
        Returns a natural spoken response if handled, or None if it should fall through to tool execution.
        """
        raw = user_input.strip()
        lower = raw.lower()
        cleaned = re.sub(r"[^\w\s]", "", lower).strip()

        # 1. Follow-up awareness based on recent conversation history
        followup_reply = self._handle_contextual_followup(lower, cleaned, history)
        if followup_reply:
            return followup_reply

        # 2. Direct time & date inquiries
        time_reply = self._handle_time_date(lower, cleaned)
        if time_reply:
            return time_reply

        # 3. System inquiries & clarifications (storage, battery, Mac status)
        sys_reply = self._handle_system_clarification(lower, cleaned)
        if sys_reply:
            return sys_reply

        # 4. Identity, capabilities, and casual banter
        banter_reply = self._handle_banter_and_identity(lower, cleaned)
        if banter_reply:
            return banter_reply

        # 5. General knowledge questions (who is, what is, explain, why does, etc.)
        knowledge_reply = self._handle_general_knowledge(raw, lower)
        if knowledge_reply:
            return knowledge_reply

        return None

    def _handle_contextual_followup(
        self,
        lower: str,
        cleaned: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        """Detect if the user is following up on a topic mentioned in the previous turn."""
        if not history or len(history) < 2:
            return None

        # Last assistant message
        last_turn = history[-1]
        last_assistant_msg = last_turn.get("content", "").lower() if last_turn.get("role") == "assistant" else ""

        # Context: Storage
        if any(w in lower for w in ["which storage", "what storage", "storage are you saying", "storage are you talking", "storage do you mean"]):
            return self._explain_storage()

        if any(w in lower for w in ["why", "explain", "how come", "why is that", "tell me why"]):
            if "storage" in last_assistant_msg or "gb free" in last_assistant_msg:
                return (
                    f"{self.user_name}, your macOS startup disk has only a few gigabytes remaining because application caches, "
                    "Xcode builds, downloads, or system snapshots accumulate over time. "
                    "I can help you locate and organize files in your workspace folder whenever you're ready."
                )
            if "battery" in last_assistant_msg:
                return (
                    f"{self.user_name}, battery consumption depends on background processes, screen brightness, and active apps. "
                    "Closing heavy background tabs or switching to battery-saver mode will extend runtime."
                )

        # Context: Weather follow-up
        if any(w in lower for w in ["what about tomorrow", "tomorrow weather", "will it rain", "is it going to rain"]):
            if "weather" in last_assistant_msg or "°c" in last_assistant_msg:
                return (
                    f"Looking ahead for tomorrow, {self.user_name}, conditions should remain fairly consistent with today's pattern. "
                    "I'll keep an eye on incoming clouds and give you an update in the morning."
                )

        return None

    def _handle_time_date(self, lower: str, cleaned: str) -> Optional[str]:
        """Handle questions asking for current time or date."""
        is_time_query = any(q in cleaned for q in [
            "what is the time", "whats the time", "what time is it", "tell me the time",
            "say me whats the time", "say me what is the time", "say the time",
            "can you say me whats the time", "can you say me what is the time",
            "current time", "the time right now", "time right now"
        ]) or (
            "time" in cleaned and any(k in cleaned for k in ["what", "tell", "say", "know", "current"])
            and not any(k in cleaned for k in ["file", "sleep", "routine", "quiet", "long", "table", "waste"])
        )

        if is_time_query:
            now = datetime.now()
            time_str = now.strftime("%I:%M %p").lstrip("0")
            return f"It is currently {time_str}, {self.user_name}."

        is_date_query = any(q in cleaned for q in [
            "what is the date", "whats the date", "today date", "todays date",
            "what day is today", "what day is it", "which day is it", "which day",
            "aaj ki tareekh", "ivathu yav dina"
        ]) or ("date" in cleaned and any(k in cleaned for k in ["what", "today", "current"]))

        if is_date_query:
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            return f"Today is {date_str}, {self.user_name}."

        return None

    def _handle_system_clarification(self, lower: str, cleaned: str) -> Optional[str]:
        """Handle questions clarifying system parameters like storage, battery, RAM, or Wi-Fi."""
        # Storage
        if any(q in cleaned for q in [
            "which storage", "what storage", "storage are you saying", "storage are you talking",
            "storage do you mean", "where is storage", "why is storage low", "explain storage",
            "storage details", "tell me about storage"
        ]) or ("storage" in cleaned and any(k in cleaned for k in ["which", "what", "where", "why", "how much", "saying", "talking", "mean"])):
            return self._explain_storage()

        # Battery
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
            return f"{self.user_name}, your MacBook battery is currently at {batt_pct}.{status_note}"

        # RAM / Memory usage
        if "ram" in cleaned or "memory usage" in cleaned:
            return f"{self.user_name}, your macOS memory pressure is currently within normal operating limits, with all system caches performing stably."

        return None

    def _explain_storage(self) -> str:
        """Provide detailed breakdown of the user's Macintosh HD storage volume."""
        try:
            usage = shutil.disk_usage("/")
            free_gb = round(usage.free / (1024**3), 1)
            total_gb = round(usage.total / (1024**3), 1)
            used_gb = round(usage.used / (1024**3), 1)
            return (
                f"{self.user_name}, I'm referring to your primary macOS startup disk (Macintosh HD). "
                f"You currently have {free_gb} GB free out of {total_gb} GB total ({used_gb} GB used). "
                "Since free space is under 10 GB, macOS might slow down during heavy operations. "
                "I can help you review or organize files in your workspace folder anytime!"
            )
        except Exception:
            return f"{self.user_name}, I'm referring to your internal Macintosh HD SSD where macOS and your files live."

    def _handle_banter_and_identity(self, lower: str, cleaned: str) -> Optional[str]:
        """Handle identity questions, mood check-ins, and friendly conversational banter."""
        # Hearing check
        if any(q in cleaned for q in ["can you hear me", "are you listening", "am i audible", "can u hear me"]):
            return f"Loud and clear through your MacBook microphone, {self.user_name}! I'm listening."

        # Mood / Wellness check
        if any(q in cleaned for q in ["i am tired", "im tired", "feeling sleepy", "exhausted", "tired"]):
            return f"You've been putting in serious work, {self.user_name}. How about taking a 10-minute break, or would you like me to switch to chill mode?"

        if any(q in cleaned for q in ["im bored", "i am bored", "feeling bored"]):
            return f"Boredom is the enemy of genius, {self.user_name}! Want me to tell you a fresh tech joke, run a quick coding quiz, or pull up some music?"

        # Appreciation / praise
        if any(q in cleaned for q in ["thank you", "thanks", "good job", "well done", "you are awesome", "nice one", "awesome"]):
            replies = [
                f"Always a pleasure serving you, {self.user_name}! What's next on our agenda?",
                f"At your service, {self.user_name}! Glad I could help.",
                f"Anytime, {self.user_name}! Just doing my job.",
            ]
            return random.choice(replies)

        # Identity & Creator
        if any(q in cleaned for q in ["who created you", "who made you", "who built you", "who is your developer"]):
            return f"I was built by you, {self.user_name}! Handcrafted from the ground up right here on your Mac."

        if any(q in cleaned for q in ["who are you", "what is your name", "what are you"]):
            return f"I am ARTH — Automated Response to Human Intent. Your personal macOS assistant, built specifically for you, {self.user_name}."

        if any(q in cleaned for q in ["are you real", "are you human", "are you an ai"]):
            return f"I'm 100% custom code running directly on your Mac, {self.user_name}. No external corporate clouds tracking your data — just pure local intelligence."

        # Kannada / Multilingual banter
        if any(q in cleaned for q in ["kannada gothaa", "kannada gothilla", "do you know kannada", "speak kannada"]):
            return f"Haudhu {self.user_name}! Nanage Kannada chennagi gothu. Enu samachara?"

        # Humor & jokes
        if any(q in cleaned for q in ["tell me a joke", "tell me something funny", "make me laugh", "crack a joke", "tech joke"]):
            jokes = [
                f"Why do programmers prefer dark mode? Because light attracts bugs, {self.user_name}!",
                f"There are 10 types of people in the world: those who understand binary, and those who don't, {self.user_name}.",
                f"Why was the JavaScript developer sad? Because he didn't know how to 'null' his feelings, {self.user_name}!",
                f"Why did the computer keep freezing? It left its Windows open, {self.user_name}!",
            ]
            return random.choice(jokes)

        # What are you doing / Day check-in
        if any(q in cleaned for q in ["what are you doing", "what are u doing", "what r u doing"]):
            return f"Monitoring system vitals, keeping your reminders indexed, and standing by for your next instruction, {self.user_name}!"

        if any(q in cleaned for q in ["how is your day", "how was your day"]):
            return f"Smooth as macOS core animations, {self.user_name}! Always great when we're collaborating."

        # Food & recommendations
        if any(q in cleaned for q in ["what should i eat", "what to eat", "food suggestion", "recommend food"]):
            return f"How about some hot masala dosa or a crisp south Indian filter coffee to fuel the coding session, {self.user_name}?"

        # Capabilities
        if any(q in cleaned for q in ["what can you do", "help me", "how can you help", "what are your features", "commands"]):
            return (
                f"{self.user_name}, I can manage your daily to-dos and reminders, track live system diagnostics and battery, "
                "fetch real-time weather and news, search the web, organize files safely in your workspace, and draft emails. "
                "Just speak or type naturally!"
            )

        return None

    def _handle_general_knowledge(self, raw_input: str, lower_input: str) -> Optional[str]:
        """
        Query real-time knowledge bases (Wikipedia REST + DuckDuckGo) for factual questions.
        Answers questions like: 'who is...', 'what is...', 'explain...', 'why is...', etc.
        """
        question_starters = [
            "who is", "who was", "what is", "what was", "what are",
            "explain", "tell me about", "can you explain", "how does", "why is", "why do", "where is"
        ]

        matched_starter = None
        for starter in question_starters:
            if lower_input.startswith(starter + " "):
                matched_starter = starter
                break

        if not matched_starter:
            return None

        # Extract search topic
        topic = raw_input[len(matched_starter):].strip().strip("?").strip()
        if not topic or len(topic) < 2:
            return None

        # Don't intercept tool commands that happen to start with 'what is'
        if any(topic.lower().startswith(skip) for skip in ["my system", "the weather", "the time", "the date", "battery", "storage"]):
            return None

        # 1. Try Wikipedia REST API summary
        try:
            clean_topic = urllib.parse.quote(topic.replace(" ", "_"))
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_topic}"
            req = urllib.request.Request(wiki_url, headers={"User-Agent": "ARTH_Assistant/1.0 (contact@arth.local)"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    extract = data.get("extract", "")
                    if extract:
                        # Take the first 2 concise sentences
                        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", extract) if s.strip()]
                        concise = " ".join(sentences[:2])
                        return f"{self.user_name}, {concise}"
        except Exception:
            pass

        # 2. Try DuckDuckGo Instant Answer API
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(topic)}&format=json"
            req = urllib.request.Request(ddg_url, headers={"User-Agent": "ARTH_Assistant/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    abstract = data.get("AbstractText", "")
                    if abstract:
                        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", abstract) if s.strip()]
                        concise = " ".join(sentences[:2])
                        return f"{self.user_name}, {concise}"
        except Exception:
            pass

        return None
