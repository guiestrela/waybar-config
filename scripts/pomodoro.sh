#!/bin/bash

WORK=1500
BREAK=300
LONG_BREAK=900
CYCLES=3

STATE_FILE="/tmp/pomodoro_state"
CONTROL_FILE="/tmp/pomodoro_control"
PID_FILE="/tmp/pomodoro_pid"
ICON_FOCUS="󱎫"
ICON_BREAK="󰐎"
ICON_FINISHED="󰓎"
DEFAULT_STATE="${ICON_FOCUS} 25:00"

notify() {
    notify-send "Pomodoro" "$1"
}

format_time() {
    printf "%02d:%02d" "$(($1 / 60))" "$(($1 % 60))"
}

run_timer() {
    local duration=$1
    local icon=$2
    local remaining=$duration

    while [ $remaining -ge 0 ]; do
        if [ -r "$CONTROL_FILE" ] && [ "$(<"$CONTROL_FILE")" = "pause" ]; then
            printf "%s %s\n" "$ICON_BREAK" "$(format_time "$remaining")" > "$STATE_FILE"
            sleep 1
            continue
        fi

        printf "%s %s\n" "$icon" "$(format_time "$remaining")" > "$STATE_FILE"
        sleep 1
        ((remaining--))
    done

    printf "%s 00:00\n" "$ICON_FINISHED" > "$STATE_FILE"
    sleep 1
}

read_pid() {
    [ -r "$PID_FILE" ] || return 1
    read -r pid < "$PID_FILE"
    [ -n "$pid" ] || return 1
    printf "%s\n" "$pid"
}

is_running() {
    local pid
    pid=$(read_pid) || return 1
    kill -0 "$pid" 2>/dev/null
}

stop_timer() {
    local pid
    pid=$(read_pid) || return 0
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
    fi
    rm -f "$PID_FILE"
}

print_status() {
    if [ -r "$STATE_FILE" ]; then
        printf "%s\n" "$(<"$STATE_FILE")"
    else
        printf "%s\n" "$DEFAULT_STATE"
    fi
}

start_timer() {
    if ! is_running; then
        rm -f "$CONTROL_FILE"
        "$0" run >/dev/null 2>&1 &
        printf "%s\n" "$!" > "$PID_FILE"
    fi
}

toggle_pause() {
    if [ -r "$CONTROL_FILE" ] && [ "$(<"$CONTROL_FILE")" = "pause" ]; then
        rm -f "$CONTROL_FILE"
    else
        printf "pause\n" > "$CONTROL_FILE"
    fi
}

reset_timer() {
    stop_timer
    rm -f "$CONTROL_FILE"
    printf "%s\n" "$DEFAULT_STATE" > "$STATE_FILE"
}

run_daemon() {
    while true; do
        for ((i = 1; i <= CYCLES; i++)); do
            notify "${ICON_FOCUS} Focus"
            run_timer "$WORK" "$ICON_FOCUS"

            if [ $i -eq $CYCLES ]; then
                notify "${ICON_BREAK} Long break"
                run_timer "$LONG_BREAK" "$ICON_BREAK"
            else
                notify "${ICON_BREAK} Short break"
                run_timer "$BREAK" "$ICON_BREAK"
            fi
        done
    done
}

case "${1:-status}" in
    status)
        print_status
        ;;
    start)
        start_timer
        ;;
    pause)
        toggle_pause
        ;;
    reset)
        reset_timer
        ;;
    run)
        run_daemon
        ;;
    *)
        printf "Usage: %s [status|start|pause|reset|run]\n" "$0" >&2
        exit 1
        ;;
esac
