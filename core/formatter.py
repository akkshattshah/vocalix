import re
import os
from openai import OpenAI
from PyQt5.QtCore import QObject, pyqtSignal

WAKE_WORDS = [
    "hey vocalix",
    "hey vocal x",
    "hey vocal ix",
    "hey vocalics",
    "hey vocalize",
    "a vocalix",
    "a vocal x",
]


def detect_command(raw_text: str) -> tuple[bool, str]:
    """Check if the transcript starts with a wake phrase.

    Returns (True, instruction) for commands, (False, original_text) otherwise.
    """
    lower = raw_text.lower().strip()
    for wake in WAKE_WORDS:
        if lower.startswith(wake):
            instruction = raw_text[len(wake):].strip(" ,.")
            if instruction:
                return True, instruction
            return False, raw_text
    return False, raw_text

SYSTEM_PROMPT = """\
You are a plain-text formatter. You receive raw speech-to-text transcriptions \
and return a cleanly formatted plain-text version.

Rules:
1. Fix punctuation, capitalisation, and obvious grammar slips.
2. When the speaker lists items (e.g. "number one … number two … number three", \
"first … second … third", "next … also …"), output them as a numbered list \
where EACH item is on its OWN line, like:
1. First item
2. Second item
3. Third item
   Keep the introductory sentence as a normal paragraph BEFORE the list, \
separated by a blank line.
3. Only use numbered-list formatting when the speaker clearly enumerated \
points. Normal speech stays as regular paragraphs.
4. Do NOT change the speaker's wording or meaning — only restructure layout \
and fix punctuation.
5. Return ONLY the formatted plain text. No markdown code fences, no \
commentary, no extra explanation. Plain text only.
6. If the input is COMPLETELY empty or is clearly random nonsense syllables \
(e.g. "uh ah hmm"), return EXACTLY an empty string — nothing at all. \
However, short but coherent phrases (even just a few words like \
"skin hair laser aesthetics" or "meeting tomorrow at 3") are VALID — \
format and return them normally. NEVER apologise, ask for more context, \
or generate placeholder text.\
"""


class Formatter(QObject):
    """Sends raw transcript through GPT for smart formatting."""

    formatted_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def format(self, raw_text: str):
        try:
            resp = self._client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": raw_text},
                ],
            )
            formatted = resp.choices[0].message.content.strip()
            self.formatted_ready.emit(formatted)
        except Exception as exc:
            self.error.emit(str(exc))

    def format_sync(self, raw_text: str) -> str:
        """Synchronous variant -- returns formatted text, raises on error."""
        resp = self._client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_text},
            ],
        )
        return resp.choices[0].message.content.strip()
