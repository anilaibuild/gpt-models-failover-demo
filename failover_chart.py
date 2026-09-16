import sqlite3
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

connection = sqlite3.connect("failover_demo.db")
cursor = connection.cursor()

cursor.execute("SELECT provider_used, COUNT(*) FROM conversation_turns WHERE role='assistant' GROUP BY provider_used")
provider_counts = dict(cursor.fetchall())

cursor.execute("SELECT failover_reason, COUNT(*) FROM conversation_turns WHERE failover_reason IS NOT NULL GROUP BY failover_reason")
reason_rows = cursor.fetchall()
connection.close()

total_responses = sum(provider_counts.values())
gemini_count = provider_counts.get("gemini", 0)
claude_count = provider_counts.get("claude", 0)
failover_count = sum(count for _, count in reason_rows)

def simplify_reason(reason):
    if reason.startswith("api_error"):
        return "Live API failure"
    if reason == "budget_exceeded":
        return "Department budget exceeded"
    return reason

navy = "#1B2340"
slate = "#5B6B8C"
amber = "#C97B2E"
bg = "#F7F8FA"
panel = "#FFFFFF"
grid = "#E4E7EC"

plt.rcParams["font.family"] = "sans-serif"
fig = plt.figure(figsize=(11, 5.5), facecolor=bg)

fig.text(0.05, 0.94, "Cross-Provider Failover Summary", fontsize=18,
          fontweight="bold", color=navy)
fig.text(0.05, 0.885, "Claude \u2194 Gemini \u00b7 gpt-models-failover-demo \u00b7 cumulative across all test runs",
          fontsize=10.5, color=slate)

tile_y, tile_h = 0.58, 0.22
tile_w = 0.28
tiles = [
    (0.05, str(total_responses), "Total AI responses", navy),
    (0.05 + tile_w + 0.02, str(gemini_count) + " / " + str(claude_count), "Gemini / Claude split", slate),
    (0.05 + 2 * (tile_w + 0.02), str(failover_count), "Automatic failovers", amber),
]

for x, number, label, color in tiles:
    ax_tile = fig.add_axes([x, tile_y, tile_w, tile_h])
    ax_tile.set_xlim(0, 1)
    ax_tile.set_ylim(0, 1)
    ax_tile.axis("off")
    box = FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.04",
                          linewidth=1, edgecolor=grid, facecolor=panel)
    ax_tile.add_patch(box)
    ax_tile.text(0.08, 0.62, number, fontsize=26, fontweight="bold",
                  color=color, ha="left", va="center")
    ax_tile.text(0.08, 0.22, label, fontsize=11, color=slate, ha="left", va="center")

reason_ax = fig.add_axes([0.05, 0.06, 0.90, 0.42])
reason_ax.axis("off")
reason_ax.text(0, 0.92, "What triggered each failover", fontsize=11.5, color=slate, fontweight="bold")

y_pos = 0.68
for reason, count in reason_rows:
    label = simplify_reason(reason)
    reason_ax.add_patch(plt.Rectangle((0, y_pos - 0.06), 0.012, 0.16,
                                        color=amber, transform=reason_ax.transAxes))
    reason_ax.text(0.02, y_pos, label, fontsize=12, color=navy, va="center")
    reason_ax.text(0.55, y_pos, f"{count} occurrence" + ("s" if count != 1 else ""),
                    fontsize=11, color=slate, va="center")
    y_pos -= 0.28

reason_ax.text(0, 0.05,
                "Every failover carried the conversation's full context to the new provider \u2014 no restart, no lost history.",
                fontsize=10.5, color=slate, style="italic")

plt.savefig("failover_chart.png", dpi=200, facecolor=bg)
print("Chart saved as failover_chart.png")