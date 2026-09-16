# Cross-Provider Failover Demo

A working demonstration that a multi-turn conversation can automatically fail over from one AI provider to another mid-conversation, without losing context — because Claude's and Gemini's APIs are both stateless, the conversation was never stored on their servers to begin with. It only ever lived in one place: this project's own database.

Full writeup: *[link to be added once published]*

## The problem this solves

An organization gives employees access to both Claude and Gemini, with some departments given limited token budgets. Employees worry: if a provider has an outage, or a department runs out of budget, does their in-progress work just stop? This project tests that directly.

## What this does

1. **Canonical, provider-agnostic storage** (`conversation_store.py`) — every turn of a conversation is saved to SQLite in one neutral format, independent of either provider's API shape.
2. **Payload translators** (`providers.py`) — convert the canonical format into Claude's exact request shape (`role: assistant`, top-level `system`) and Gemini's exact shape (`role: model`, `system_instruction` config) — verified directly against both providers' official docs.
3. **Real API clients** (`api_clients.py`) — make genuine calls to Claude and Gemini, logging real token usage back to the database.
4. **Automatic failover** (`failover.py`) — two independent triggers feed the same fallback path: a live API failure (caught via exception handling) or a department's token budget being exhausted (tracked and enforced by this project, not the providers).
5. **Interactive live demo** (`live_demo.py`) — have a real conversation in the terminal, and type `/fail` at any point to force a live failover and watch the conversation continue coherently on the other provider.
6. **Dashboard** (`failover_chart.py`) — visual summary of failover activity, queried live from the database.

## Real findings

- A conversation started on Gemini continues coherently on Claude (and vice versa), correctly referencing context Claude never directly saw — proven, not assumed.
- Translation overhead (fetching stored history + reshaping it for the target provider) measured at ~0.08ms — effectively negligible next to real end-to-end API latency, measured at ~1.1–1.2 seconds for both providers.
- The two failover triggers (live failure vs. budget exhaustion) are independent and were tested separately, each correctly logging its own reason to the database.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with:


## Usage

Run the full test suite (storage, translators, real API calls, both failover triggers):
```bash
python failover.py
```

Try the interactive live demo:
```bash
python live_demo.py
```

Generate the dashboard:
```bash
python failover_chart.py
```

Measure real latency yourself:
```bash
python measure_latency.py
```

## Notes on scope

This is a personal proof-of-concept, not production infrastructure.
- Department token budgets are illustrative demo values, not measured or industry-standard figures.
- Tool/function-calling conversations are out of scope — Claude's and Gemini's tool-call formats are not directly compatible, and this project only handles plain text turns.
- Failure detection is currently either a real exception or a manually-forced simulation — this does not include automatic health-check polling of either provider's public status page.

## License

MIT