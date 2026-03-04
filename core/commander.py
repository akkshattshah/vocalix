import os
from openai import OpenAI
from PyQt5.QtCore import QObject, pyqtSignal

SYSTEM_PROMPT = """\
You are a writing assistant. The user gave you a spoken instruction describing \
what they need you to write (an email, a message, a reply, a summary, etc.).

Rules:
1. Generate ONLY the requested content. No preamble like "Sure, here you go" \
or "Here is your email". Just output the content itself.
2. Output plain text only. No markdown code fences, no commentary.
3. Match the tone and length the user asked for. If they said "keep it short \
and formal", do exactly that.
4. For emails, include a Subject line on the first line formatted as \
"Subject: ..." followed by a blank line, then the body.
5. If the instruction is empty or makes no sense, return an empty string. \
NEVER apologise or ask for clarification.\
"""


class Commander(QObject):
    """Takes a spoken instruction and generates the requested content via LLM."""

    command_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def execute(self, instruction: str):
        try:
            resp = self._client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.4,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction},
                ],
            )
            result = resp.choices[0].message.content.strip()
            self.command_ready.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))

    def execute_sync(self, instruction: str) -> str:
        """Synchronous variant -- returns generated text, raises on error."""
        resp = self._client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": instruction},
            ],
        )
        return resp.choices[0].message.content.strip()
