"""Handler for compound requests per Section 16 of ARTH_SPEC:
'If I ask for two or more things at once, repeat them back and ask which to do first.
Then do them one at a time, in the order I choose.'
"""

from __future__ import annotations

import re
from typing import Callable, List, Optional, Tuple


class MultiRequestHandler:
    """Detects and coordinates multiple requests asked in a single utterance."""

    SPLIT_PATTERNS = [
        r"\band\s+then\b",
        r"\b,\s*and\b",
        r"\band\s+also\b",
        r"\balso\b",
        r"\bafter\s+that\b",
        r"\band\b",
    ]

    def __init__(self, prompt_callback: Optional[Callable[[str], str]] = None):
        self.prompt_callback = prompt_callback or self._default_terminal_prompt

    @staticmethod
    def _default_terminal_prompt(prompt_message: str) -> str:
        try:
            return input(f"\n{prompt_message}\nYour choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "1"

    def split_requests(self, user_input: str) -> List[str]:
        """Split a user utterance into distinct requests if compound conjunctions exist."""
        text = user_input.strip()
        # Avoid splitting common phrases like "rock and roll", "bread and butter"
        # We look for action verbs in splits
        combined_pattern = "|".join(self.SPLIT_PATTERNS)
        parts = [p.strip() for p in re.split(combined_pattern, text, flags=re.IGNORECASE) if p.strip()]

        # Only treat as multi-request if each part has sufficient substance (at least 2 words)
        valid_requests = [p for p in parts if len(p.split()) >= 2]
        if len(valid_requests) > 1:
            return valid_requests
        return [text]

    def order_requests(self, requests: List[str]) -> List[str]:
        """Ask Boss which request to perform first and order accordingly."""
        if len(requests) <= 1:
            return requests

        prompt_lines = ["Boss, you asked for several things at once:"]
        for idx, req in enumerate(requests, 1):
            prompt_lines.append(f"  {idx}) {req}")
        prompt_lines.append("Which one would you like me to do first? (Enter number)")

        choice_str = self.prompt_callback("\n".join(prompt_lines))

        # Parse user choice
        match = re.search(r"\b(\d+)\b", choice_str)
        if match:
            choice_idx = int(match.group(1)) - 1
            if 0 <= choice_idx < len(requests):
                first = requests[choice_idx]
                remaining = [r for i, r in enumerate(requests) if i != choice_idx]
                return [first] + remaining

        # Default to natural order if input not parsed
        return requests
