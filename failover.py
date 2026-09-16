"""
failover.py

Two triggers feed the same fallback path:
  1. Department token budget exhausted (a policy limit WE track and enforce)
  2. A live API failure from the preferred provider (real exception, or a
     clearly-labeled simulated one for testing)

Either way, ask_with_failover() catches it and automatically continues
the conversation on the other provider.
"""

import sqlite3

from api_clients import ask_claude, ask_gemini
from conversation_store import DB_PATH

DEPARTMENT_BUDGETS = {
    "HR": 2000,
    "Facility": 2000,
    "Finance": 10000,
    "IT": 50000,
}


class SimulatedProviderFailure(Exception):
    """Raised only when explicitly forced, to test failover without waiting for a real outage."""
    pass


def get_department_usage(department: str) -> int:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(tokens_consumed), 0) FROM conversation_turns
        WHERE department = ?
    """, (department,))
    total = cursor.fetchone()[0]
    connection.close()
    return total


def is_over_budget(department: str) -> bool:
    budget = DEPARTMENT_BUDGETS.get(department)
    if budget is None:
        return False
    return get_department_usage(department) >= budget


def ask_with_failover(session_id: str, department: str, preferred: str = "gemini",
                       force_failure: str = None) -> dict:
    """
    Tries the preferred provider first. Falls back to the other provider if:
      - the department is already over its token budget, or
      - the preferred provider's real API call fails, or
      - force_failure matches the preferred provider (simulated failure, for testing)

    Returns {"reply": ..., "provider_used": ..., "failover_reason": ... or None}
    """
    other = "claude" if preferred == "gemini" else "gemini"
    ask_fn = {"gemini": ask_gemini, "claude": ask_claude}

    if is_over_budget(department):
        print(f"[failover] {department} is over its token budget ({DEPARTMENT_BUDGETS.get(department)}). Skipping {preferred}, going straight to {other}.")
        reply = ask_fn[other](session_id, department, failover_reason="budget_exceeded")
        return {"reply": reply, "provider_used": other, "failover_reason": "budget_exceeded"}

    try:
        if force_failure == preferred:
            raise SimulatedProviderFailure(f"Simulated outage: {preferred} unavailable (forced for testing)")

        reply = ask_fn[preferred](session_id, department)
        return {"reply": reply, "provider_used": preferred, "failover_reason": None}

    except Exception as e:
        print(f"[failover] {preferred} failed ({e}). Falling back to {other}.")
        reply = ask_fn[other](session_id, department, failover_reason=f"api_error: {e}")
        return {"reply": reply, "provider_used": other, "failover_reason": f"api_error: {e}"}


if __name__ == "__main__":
    import uuid
    from conversation_store import save_turn, get_full_session

    session = f"failover-test-{uuid.uuid4().hex[:8]}"
    dept = "IT"

    print(f"Session: {session}\n")

    save_turn(session, dept, "system", "You are a concise compliance policy assistant.")
    save_turn(session, dept, "user", "Rule 1: storage buckets must deny public read by default. Acknowledge Rule 1 only.")

    print("--- Turn 1: normal call, preferred provider (Gemini) ---")
    result1 = ask_with_failover(session, dept, preferred="gemini")
    print(result1, "\n")

    save_turn(session, dept, "user", "Now add Rule 2: all ingress must require TLS 1.3. Summarize both rules.")

    print("--- Turn 2: FORCED simulated Gemini outage, should fail over to Claude ---")
    result2 = ask_with_failover(session, dept, preferred="gemini", force_failure="gemini")
    print(result2, "\n")

    print("--- Full stored session ---")
    for turn in get_full_session(session):
        print(turn)

    print("\n\n=== Testing the budget-exhaustion trigger (separate department: HR) ===")
    hr_session = f"failover-test-hr-{uuid.uuid4().hex[:8]}"

    save_turn(hr_session, "HR", "system", "You are an HR policy assistant.")
    save_turn(hr_session, "HR", "assistant", "[Simulated prior usage this month]",
              provider_used="gemini", tokens_consumed=2100)

    print(f"HR usage so far: {get_department_usage('HR')} / {DEPARTMENT_BUDGETS['HR']} budget")

    save_turn(hr_session, "HR", "user", "Can you summarize our PTO policy in one sentence?")
    result3 = ask_with_failover(hr_session, "HR", preferred="gemini")
    print(result3)