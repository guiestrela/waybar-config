#!/bin/bash
# Pomodoro Timer Script for Waybar
# Tracks pomodoro sessions using a simple file

STATE_FILE="${XDG_RUNTIME_DIR:-/tmp}/pomodoro.state"

read_state() {
    if [ -f "$STATE_FILE" ]; then
        cat "$STATE_FILE"
    else
        echo "idle 25:00"
    fi
}

write_state() {
    echo "$1 $2" > "$STATE_FILE"
}

state=$(read_state | cut -d' ' -f1)
time=$(read_state | cut -d' ' -f2)

case $state in
    "work")
        echo "🍅 $time"
        ;;
    "break")
        echo "☕ $time"
        ;;
    "long-break")
        echo "🌴 $time"
        ;;
    *)
        echo "🍅 25:00"
        ;;
esac
