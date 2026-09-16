"""
api_clients.py

Calls Claude and Gemini using the canonical conversation history stored
in SQLite, translated into each provider's real request format via
providers.py. Every call's result is saved back into conversation_turns,
so the store always reflects the true state of the conversation --
regardless of which provider actually generated each turn.
"""

import os
from dotenv import load_dotenv

from anthropic import Anthropic
from google import genai

from providers import to_claude_payload, to_gemini_payload
from conversation_store import get_turns, save_turn

load_dotenv()

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def ask_claude(session_id: str, department: str) -> str:
    """
    Reads the current stored conversation, sends it to Claude, saves
    Claude's reply back into the store, and returns the reply text.
    """
    turns = get_turns(session_id)
    system_prompt, messages = to_claude_payload(turns)

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system_prompt if system_prompt else None,
        messages=messages,
    )

    reply_text = response.content[0].text
    tokens_used = response.usage.input_tokens + response.usage.output_tokens

    save_turn(session_id, department, "assistant", reply_text,
              provider_used="claude", tokens_consumed=tokens_used)

    return reply_text


def ask_gemini(session_id: str, department: str) -> str:
    """
    Reads the current stored conversation, sends it to Gemini, saves
    Gemini's reply back into the store, and returns the reply text.
    """
    turns = get_turns(session_id)
    system_instruction, contents = to_gemini_payload(turns)

    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=contents,
        config={"system_instruction": system_instruction} if system_instruction else None,
    )

    reply_text = response.text
    tokens_used = response.usage_metadata.total_token_count

    save_turn(session_id, department, "assistant", reply_text,
              provider_used="gemini", tokens_consumed=tokens_used)

    return reply_text


if __name__ == "__main__":
    import uuid
    test_session = f"live-test-{uuid.uuid4().hex[:8]}"
    department = "IT"

    print(f"Session: {test_session}")
    save_turn(test_session, department, "system", "You are a concise compliance policy assistant.")
    save_turn(test_session, department, "user", "Rule 1: storage buckets must deny public read by default. Acknowledge Rule 1 only.")

    print("Asking Gemini...")
    reply = ask_gemini(test_session, department)
    print("Gemini replied:", reply)

