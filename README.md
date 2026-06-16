# ⏰ alarm-clock-cli

A minimal, zero-dependency CLI alarm clock built in Python.

## Quick Start

```bash
# Set an alarm for 7:30 AM
python alarm.py 07:30

# With a label
python alarm.py 14:00 --label "Stand-up meeting"

# Custom snooze duration (minutes)
python alarm.py 09:00 --snooze 10

# Disable snooze
python alarm.py 09:00 --snooze 0
```

## Requirements

- Python 3.8+
- No external packages — stdlib only

## Features

| Feature | Notes |
|---|---|
| Set alarm by HH:MM (24h or AM/PM) | `07:30` or `7:30 AM` |
| Live countdown display | Updates every second in-place |
| Cross-platform audio alert | Windows: `winsound`, macOS: `afplay`, Linux: `paplay` → terminal bell |
| Custom label | `--label "Dentist"` |
| Snooze | Default 5 min, configurable, dismissible |
| Auto-next-day | Schedules for tomorrow if time already passed |
| Ctrl+C to cancel | Clean exit at any stage |

---

## Engineering Decisions

### Scope

Given a 30-minute build window and no spec, I scoped deliberately:

**Included:**
- Core alarm (time → alert) — non-negotiable
- Live countdown — minimal effort, large UX win
- Snooze — one real product feature that shows thinking about how people actually use alarms
- Cross-platform audio — without sound, it's just a timer

**Cut deliberately:**
- Multiple simultaneous alarms — needs a background scheduler/daemon, out of scope
- Persistence (config file / DB) — explicitly excluded in spec; single-session is fine
- Recurring alarms — complexity without gain in 30 minutes
- Timezone support — over-engineering for a local alarm clock
- GUI / TUI (curses) — CLI only was the requirement

### Why stdlib only?

`playsound`, `pygame`, `rich` etc. are one-pip installs but introduce a setup step and potential cross-platform issues. The requirement was a CLI that works — not a package management exercise. `winsound` / `afplay` / `paplay` cover the three major OSes with zero installs.

### Why polling over `schedule` or `APScheduler`?

A 1-second `sleep` loop is readable, debuggable, and has zero dependencies. The latency (±1s) is perfectly acceptable for an alarm clock. A proper scheduler would be justified only if this ran as a background daemon across multiple alarms.

### Why recurse for snooze?

Each snooze cycle is a fresh countdown → ring. Recursion keeps the logic flat and readable — no state machine needed for a single alarm. Stack depth is bounded by how many times a person actually snoozes (realistically < 10).

### What I'd add with more time

- Persistent alarm list (JSON file) + `--list` / `--delete` commands
- Background daemon mode (`alarm.py set 07:30 &`)
- Desktop notification via `notify-send` (Linux) / `osascript` (macOS)
- `--repeat daily` flag

---

## Project Structure

```
alarm_clock/
├── alarm.py          # Single-file implementation (~180 lines)
├── requirements.txt  # stdlib only — nothing to install
└── README.md
```

---

## Testing It

```bash
# Test immediately — set alarm 1 minute from now
python alarm.py $(date -d "+1 minute" +%H:%M)    # Linux
python alarm.py $(date -v+1M +%H:%M)             # macOS

# Test snooze
python alarm.py HH:MM --snooze 1

# Test cancel
python alarm.py 23:59   # then Ctrl+C
```