"""
conversation_store.py

Reads and writes conversation turns to the canonical, provider-agnostic
SQLite store. This is the single source of truth for conversation history
-- neither Claude nor Gemini ever holds state themselves (both APIs are
stateless), so this table IS the memory of the conversation.
"""

import sqlite3
from datetime import datetime

DB_PATH = "failover_demo.db"


def save_turn(session_id: str, department: str, role: str, content: str,
              provider_used: str = None, tokens_consumed: int = 0,
              failover_reason: str = None):
    """Appends one turn to the conversation_turns table."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO conversation_turns
            (session_id, department, role, content, provider_used, tokens_consumed, failover_reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id, department, role, content, provider_used, tokens_consumed, failover_reason,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    connection.commit()
    connection.close()


def get_turns(session_id: str) -> list[dict]:
    """
    Returns all turns for a session, in chronological order, as plain
    dicts with just {"role", "content"} -- the canonical shape the
    to_gemini_payload()/to_claude_payload() translators expect.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT role, content FROM conversation_turns
        WHERE session_id = ?
        ORDER BY turn_id ASC
    """, (session_id,))

    rows = cursor.fetchall()
    connection.close()

    return [{"role": role, "content": content} for role, content in rows]


def get_full_session(session_id: str) -> list[dict]:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT turn_id, role, content, provider_used, tokens_consumed, failover_reason, created_at
        FROM conversation_turns
        WHERE session_id = ?
        ORDER BY turn_id ASC
    """, (session_id,))

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "turn_id": r[0], "role": r[1], "content": r[2],
            "provider_used": r[3], "tokens_consumed": r[4],
            "failover_reason": r[5], "created_at": r[6],
        }
        for r in rows
    ]


if __name__ == "__main__":
    test_session = "test-session-001"

    save_turn(test_session, "IT", "system", "You are a compliance policy assistant.")
    save_turn(test_session, "IT", "user", "Rule 1 is that storage buckets must deny public read.")
    save_turn(test_session, "IT", "assistant", "Acknowledged. Rule 1 recorded.", provider_used="gemini", tokens_consumed=42)

    print("--- get_turns (canonical, for API payload) ---")
    print(get_turns(test_session))

    print("\n--- get_full_session (with provider/token detail) ---")
    for turn in get_full_session(test_session):
        print(turn)