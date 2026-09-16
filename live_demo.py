"""
live_demo.py

Interactive terminal demo: have a real, ongoing conversation, and at any
point type /fail to force the next response to fail over to the other
provider mid-conversation -- watch it continue seamlessly.

Run:  python live_demo.py
Commands inside the demo:
  /fail    -- force the NEXT response to simulate a provider failure
  /status  -- show current department token usage vs budget
  /quit    -- exit
"""

import uuid

from conversation_store import save_turn
from failover import ask_with_failover, DEPARTMENT_BUDGETS, get_department_usage

BOLD = "\033[1m"
GREEN = "\033[92m"
AMBER = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

BANNER = f"""
{BOLD}Cross-Provider Failover -- Live Demo{RESET}
Claude \u2194 Gemini \u00b7 one conversation, automatic handoff on failure

Type a message to continue the conversation.
Type {AMBER}/fail{RESET} to force the NEXT response to fail over.
Type {AMBER}/status{RESET} to see token usage vs. budget.
Type {AMBER}/quit{RESET} to exit.
"""


def main():
    print(BANNER)

    session_id = f"live-demo-{uuid.uuid4().hex[:8]}"
    department = "IT"
    preferred = "gemini"
    force_next_failure = False

    print(f"Session: {session_id}  |  Department: {department}  |  Starting on: {preferred}\n")

    save_turn(session_id, department, "system", "You are a concise, helpful assistant.")

    while True:
        try:
            user_input = input(f"{BOLD}You> {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            continue

        if user_input.lower() == "/quit":
            print("Exiting.")
            break

        if user_input.lower() == "/status":
            usage = get_department_usage(department)
            budget = DEPARTMENT_BUDGETS.get(department, "unlimited")
            print(f"{department} usage: {usage} / {budget} tokens\n")
            continue

        if user_input.lower() == "/fail":
            force_next_failure = True
            print(f"{AMBER}Next response will simulate a {preferred} failure and fail over.{RESET}\n")
            continue

        save_turn(session_id, department, "user", user_input)

        result = ask_with_failover(
            session_id, department,
            preferred=preferred,
            force_failure=preferred if force_next_failure else None,
        )
        force_next_failure = False

        provider_tag = f"{GREEN}[{result['provider_used']}]{RESET}"
        if result["failover_reason"]:
            provider_tag = f"{AMBER}[{result['provider_used']} \u2014 FAILED OVER]{RESET}"

        print(f"{provider_tag} {result['reply']}\n")

        preferred = result["provider_used"]


if __name__ == "__main__":
    main()