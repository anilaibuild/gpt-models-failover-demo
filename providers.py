"""
providers.py

Translates a canonical, provider-agnostic list of conversation turns
into the exact request shape each provider's API actually expects.

Verified against official docs:
- Claude Messages API: stateless, {"role": "user"|"assistant", "content": ...},
  system prompt as a separate top-level "system" string.
- Gemini generateContent API: stateless, {"role": "user"|"model", "parts": [{"text": ...}]},
  system prompt as a separate "system_instruction" config value.
"""

from typing import List, Dict, Tuple, Any


def to_gemini_payload(turns: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, Any]]]:
    """Translates canonical turns into Gemini's contents + system_instruction shape."""
    system_instruction = ""
    contents = []

    for turn in turns:
        if turn["role"] == "system":
            system_instruction = turn["content"]
        else:
            # Gemini calls the AI's own turns "model", not "assistant"
            role = "user" if turn["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": turn["content"]}]
            })

    return system_instruction, contents


def to_claude_payload(turns: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, Any]]]:
    """Translates canonical turns into Claude's messages + system shape."""
    system_prompt = ""
    messages = []

    for turn in turns:
        if turn["role"] == "system":
            system_prompt = turn["content"]
        else:
            # Claude's canonical roles (user/assistant) match our own storage directly
            messages.append({
                "role": turn["role"],
                "content": turn["content"]
            })

    return system_prompt, messages


if __name__ == "__main__":
    sample_turns = [
        {"role": "system", "content": "You are a compliance policy assistant."},
        {"role": "user", "content": "Rule 1 is that all storage buckets must deny public read by default."},
        {"role": "assistant", "content": "Acknowledged. Rule 1: storage buckets deny public read by default."},
    ]

    gemini_system, gemini_contents = to_gemini_payload(sample_turns)
    print("--- Gemini payload ---")
    print("system_instruction:", gemini_system)
    print("contents:", gemini_contents)

    claude_system, claude_messages = to_claude_payload(sample_turns)
    print("\n--- Claude payload ---")
    print("system:", claude_system)
    print("messages:", claude_messages)