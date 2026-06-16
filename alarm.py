#!/usr/bin/env python3
"""
alarm.py - A minimal but complete CLI alarm clock.

Usage:
    python alarm.py 07:30
    python alarm.py 07:30 --label "Stand-up"
    python alarm.py 07:30 --snooze 5
    python alarm.py --list-timezones
"""

import argparse
import sys
import time
import threading
from datetime import datetime, timedelta


# ── Audio ─────────────────────────────────────────────────────────────────────

def _beep_cross_platform():
    """Play a terminal bell. Falls back silently if unavailable."""
    try:
        import platform
        os_name = platform.system()

        if os_name == "Windows":
            import winsound
            for _ in range(5):
                winsound.Beep(1000, 400)
                time.sleep(0.1)
        else:
            # Linux / macOS: try paplay (PulseAudio), afplay, or terminal bell
            import subprocess, shutil
            if os_name == "Darwin" and shutil.which("afplay"):
                subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"],
                               check=False)
            elif shutil.which("paplay"):
                subprocess.run(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
                    check=False
                )
            else:
                # Universal fallback: terminal bell repeated
                for _ in range(5):
                    sys.stdout.write("\a")
                    sys.stdout.flush()
                    time.sleep(0.4)
    except Exception:
        # Never crash because of audio
        sys.stdout.write("\a")
        sys.stdout.flush()


# ── Countdown display ─────────────────────────────────────────────────────────

def _countdown(target: datetime, label: str):
    """Print a live countdown on a single line until target time."""
    print()  # blank line before countdown starts
    while True:
        now = datetime.now()
        remaining = target - now
        if remaining.total_seconds() <= 0:
            # Clear the countdown line
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()
            break

        total_secs = int(remaining.total_seconds())
        hours, rem = divmod(total_secs, 3600)
        minutes, seconds = divmod(rem, 60)

        msg = f"  ⏰  [{label}]  Rings in {hours:02d}:{minutes:02d}:{seconds:02d}"
        sys.stdout.write(f"\r{msg}")
        sys.stdout.flush()
        time.sleep(1)


# ── Alarm ring & snooze ───────────────────────────────────────────────────────

def _ring(label: str, snooze_minutes: int):
    """Ring the alarm and offer snooze."""
    border = "=" * 50
    print(f"\n\n{border}")
    print(f"  🔔  ALARM: {label}")
    print(f"  {datetime.now().strftime('%I:%M %p')}")
    print(border)

    # Fire audio in a thread so we can still read input
    audio_thread = threading.Thread(target=_beep_cross_platform, daemon=True)
    audio_thread.start()

    if snooze_minutes > 0:
        print(f"\n  Press ENTER to snooze {snooze_minutes} min, or type 'stop' + ENTER to dismiss.")
        try:
            user_input = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            user_input = "stop"

        audio_thread.join(timeout=2)

        if user_input != "stop":
            snooze_target = datetime.now() + timedelta(minutes=snooze_minutes)
            print(f"\n  💤  Snoozed until {snooze_target.strftime('%I:%M:%S %p')}")
            _countdown(snooze_target, f"{label} (snoozed)")
            _ring(label, snooze_minutes)   # recurse for another snooze cycle
        else:
            print("\n  ✅  Alarm dismissed.")
    else:
        print("\n  Press ENTER to dismiss.")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass
        audio_thread.join(timeout=2)
        print("  ✅  Alarm dismissed.")


# ── Argument parsing ──────────────────────────────────────────────────────────

def _parse_args():
    parser = argparse.ArgumentParser(
        prog="alarm",
        description="A simple CLI alarm clock.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python alarm.py 07:30
  python alarm.py 14:05 --label "Lunch break"
  python alarm.py 09:00 --snooze 5
        """
    )
    parser.add_argument(
        "time",
        help='Alarm time in HH:MM (24-hour) or HH:MM AM/PM format, e.g. "07:30" or "7:30 PM"',
        nargs="?",
    )
    parser.add_argument(
        "--label", "-l",
        default="Alarm",
        help='Label shown when alarm rings (default: "Alarm")'
    )
    parser.add_argument(
        "--snooze", "-s",
        type=int,
        default=5,
        metavar="MINUTES",
        help="Snooze duration in minutes (default: 5, set 0 to disable snooze)"
    )
    return parser, parser.parse_args()


# ── Time parsing ──────────────────────────────────────────────────────────────

def _parse_time(raw: str) -> datetime:
    """
    Accept multiple formats:
      07:30        → today at 07:30 (24h)
      7:30 PM      → today at 19:30
    If the time has already passed today, schedules for tomorrow.
    """
    now = datetime.now()
    parsed = None

    # Try 24-hour first (no locale issues)
    try:
        parsed = datetime.strptime(raw.strip(), "%H:%M")
    except ValueError:
        pass

    # Try 12-hour AM/PM — uppercase the input so "am"/"pm" work,
    # but do NOT uppercase the format string (%p is locale-sensitive)
    if parsed is None:
        normalized = raw.strip().upper()
        for fmt in ["%I:%M %p", "%I:%M%p"]:
            try:
                parsed = datetime.strptime(normalized, fmt)
                break
            except ValueError:
                continue

    if parsed is None:
        raise ValueError(f"Cannot parse time: '{raw}'. Use HH:MM or HH:MM AM/PM.")

    target = now.replace(
        hour=parsed.hour,
        minute=parsed.minute,
        second=0,
        microsecond=0,
    )

    if target <= now:
        target += timedelta(days=1)
        print(f"  ℹ️   That time has passed today — scheduling for tomorrow.")

    return target


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser, args = _parse_args()

    if not args.time:
        parser.print_help()
        sys.exit(0)

    try:
        target = _parse_time(args.time)
    except ValueError as e:
        print(f"\n  ❌  {e}\n")
        sys.exit(1)

    label = args.label
    snooze = args.snooze

    print(f"\n  ✅  Alarm set for {target.strftime('%I:%M %p')}  |  label: \"{label}\"", end="")
    if snooze > 0:
        print(f"  |  snooze: {snooze} min", end="")
    print("\n  (Ctrl+C to cancel)\n")

    try:
        _countdown(target, label)
        _ring(label, snooze)
    except KeyboardInterrupt:
        print("\n\n  ❌  Alarm cancelled.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
