#!/bin/bash
# Pomodoro Control Script for Waybar
# Usage: pomodoro-control.sh [start|pause|reset]

STATE_FILE="${XDG_RUNTIME_DIR:-/tmp}/pomodoro.state"

case $1 in
    start)
        # Start work session (25 min)
        echo "work 25:00" > "$STATE_FILE"
        ;;
    pause)
        # Pause current session
        if [ -f "$STATE_FILE" ]; then
            state=$(cut -d' ' -f1 "$STATE_FILE")
            time=$(cut -d' ' -f2 "$STATE_FILE")
            if [ "$state" = "paused" ]; then
                # Resume
                prev_time=$(cut -d' ' -f3 "$STATE_FILE")
                echo "$prev_state $prev_time" > "$STATE_FILE"
            else
                # Pause
                echo "paused $time $state" > "$STATE_FILE"
            fi
        fi
        ;;
    reset)
        rm -f "$STATE_FILE"
        ;;
    *)
        echo "Usage: pomodoro-control.sh [start|pause|reset]"
        ;;
esac

# Restart waybar to update display
pkill -RTMIN+<SIGNAL> waybar 2>/dev/null || true
