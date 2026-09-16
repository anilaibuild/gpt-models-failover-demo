"""
measure_latency.py

Measures two genuinely different things, separately:
  1. Translation overhead -- how long OUR code takes to fetch stored
     turns and reshape them into a provider's payload (no network call).
  2. End-to-end latency -- the full round trip including the real API
     call, for context (this is dominated by the provider's own
     network/model time, not by anything we control).

Real measurements only. No numbers are assumed or estimated.
"""

import time
import statistics
import uuid

from conversation_store import save_turn, get_turns
from providers import to_claude_payload, to_gemini_payload
from api_clients import ask_gemini, ask_claude


def measure_translation_overhead(n_runs: int = 20):
    session = f"latency-test-{uuid.uuid4().hex[:8]}"
    save_turn(session, "IT", "system", "You are a concise assistant.")
    save_turn(session, "IT", "user", "Rule 1: storage buckets must deny public read by default.")
    save_turn(session, "IT", "assistant", "Acknowledged.", provider_used="gemini", tokens_consumed=50)

    gemini_times = []
    claude_times = []

    for _ in range(n_runs):
        start = time.perf_counter()
        turns = get_turns(session)
        to_gemini_payload(turns)
        gemini_times.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        turns = get_turns(session)
        to_claude_payload(turns)
        claude_times.append((time.perf_counter() - start) * 1000)

    print(f"Translation overhead over {n_runs} runs (store fetch + payload reshape, no network):")
    print(f"  Gemini path: mean={statistics.mean(gemini_times):.3f}ms  max={max(gemini_times):.3f}ms")
    print(f"  Claude path: mean={statistics.mean(claude_times):.3f}ms  max={max(claude_times):.3f}ms")


def measure_end_to_end(n_runs: int = 5):
    print(f"\nEnd-to-end latency over {n_runs} REAL API calls each (includes real network + model time):")

    gemini_times = []
    for _ in range(n_runs):
        session = f"latency-e2e-gemini-{uuid.uuid4().hex[:8]}"
        save_turn(session, "IT", "system", "You are a concise assistant.")
        save_turn(session, "IT", "user", "Say OK.")
        start = time.perf_counter()
        ask_gemini(session, "IT")
        gemini_times.append((time.perf_counter() - start) * 1000)

    claude_times = []
    for _ in range(n_runs):
        session = f"latency-e2e-claude-{uuid.uuid4().hex[:8]}"
        save_turn(session, "IT", "system", "You are a concise assistant.")
        save_turn(session, "IT", "user", "Say OK.")
        start = time.perf_counter()
        ask_claude(session, "IT")
        claude_times.append((time.perf_counter() - start) * 1000)

    print(f"  Gemini: mean={statistics.mean(gemini_times):.1f}ms  min={min(gemini_times):.1f}ms  max={max(gemini_times):.1f}ms")
    print(f"  Claude: mean={statistics.mean(claude_times):.1f}ms  min={min(claude_times):.1f}ms  max={max(claude_times):.1f}ms")


if __name__ == "__main__":
    measure_translation_overhead(n_runs=20)
    measure_end_to_end(n_runs=5)