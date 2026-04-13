#!/bin/bash
# On the first manual wallpaper change after a theme switch, align the current
# background with the new theme without showing the old theme in transition.
# After that, delegate to Omarchy's normal cycler.

STATE_DIR="$HOME/.cache/waybar"
LAST_THEME_FILE="$STATE_DIR/last-wallpaper-theme"
RECENT_WALLPAPERS_FILE="$STATE_DIR/recent-wallpapers"
RECENT_WALLPAPERS_LIMIT=5
OMARCHY_STATE_DIR="$HOME/.cache/omarchy"
LAST_CHANGE_FILE="$OMARCHY_STATE_DIR/last-wallpaper-change"
CURRENT_THEME_FILE="$HOME/.config/omarchy/current/theme.name"
CURRENT_THEME_DIR="$HOME/.config/omarchy/current/theme/backgrounds"
CURRENT_THEME_NAME=$(cat "$CURRENT_THEME_FILE" 2>/dev/null)
USER_THEME_DIR="$HOME/.config/omarchy/backgrounds/$CURRENT_THEME_NAME"
USER_WALLPAPERS_DIR="$HOME/Pictures/Wallpapers"
LEGACY_USER_WALLPAPERS_DIR="$HOME/Picture/Wallpapers"
CURRENT_BACKGROUND_LINK="$HOME/.config/omarchy/current/background"
LAST_THEME_NAME=""

mkdir -p "$STATE_DIR"
mkdir -p "$OMARCHY_STATE_DIR"

load_wallpapers() {
    mapfile -d '' -t WALLPAPERS < <(
        find -L "$CURRENT_THEME_DIR" "$USER_THEME_DIR" "$USER_WALLPAPERS_DIR" "$LEGACY_USER_WALLPAPERS_DIR" \
            -maxdepth 1 -type f \
            \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.webp" \) \
            -print0 2>/dev/null | sort -z
    )
}

pick_random_wallpaper() {
    printf '%s\n' "${WALLPAPERS[RANDOM % ${#WALLPAPERS[@]}]}"
}

record_wallpaper() {
    local wallpaper="$1"
    local -a recent_wallpapers=()
    local entry=""

    [[ -n "$wallpaper" ]] || return 0

    if [[ -f "$RECENT_WALLPAPERS_FILE" ]]; then
        while IFS= read -r entry; do
            [[ -n "$entry" && "$entry" != "$wallpaper" ]] && recent_wallpapers+=("$entry")
        done < "$RECENT_WALLPAPERS_FILE"
    fi

    {
        printf '%s\n' "$wallpaper"

        local count=1
        for entry in "${recent_wallpapers[@]}"; do
            (( count >= RECENT_WALLPAPERS_LIMIT )) && break
            printf '%s\n' "$entry"
            ((count++))
        done
    } > "$RECENT_WALLPAPERS_FILE"
}

touch_last_change() {
    date +%s > "$LAST_CHANGE_FILE"
}

set_next_wallpaper() {
    local current_background="" new_background="" candidate="" recent_match=""
    local -a candidates=()
    local -a recent_wallpapers=()

    if [[ -L "$CURRENT_BACKGROUND_LINK" ]]; then
        current_background=$(readlink -f "$CURRENT_BACKGROUND_LINK")
    fi

    if [[ -f "$RECENT_WALLPAPERS_FILE" ]]; then
        mapfile -t recent_wallpapers < "$RECENT_WALLPAPERS_FILE"
    fi

    if (( ${#WALLPAPERS[@]} > 1 )); then
        for candidate in "${WALLPAPERS[@]}"; do
            candidate=$(readlink -f "$candidate")
            [[ "$candidate" == "$current_background" ]] && continue

            recent_match=""
            for recent_match in "${recent_wallpapers[@]}"; do
                [[ "$candidate" == "$recent_match" ]] && break
                recent_match=""
            done

            if [[ -z "$recent_match" ]]; then
                candidates+=("$candidate")
            fi
        done
    fi

    if (( ${#candidates[@]} > 0 )); then
        new_background="${candidates[RANDOM % ${#candidates[@]}]}"
    else
        new_background="${WALLPAPERS[RANDOM % ${#WALLPAPERS[@]}]}"
    fi

    record_wallpaper "$new_background"
    touch_last_change
    exec omarchy-theme-bg-set "$new_background"
}

if [[ -f "$LAST_THEME_FILE" ]]; then
    LAST_THEME_NAME=$(cat "$LAST_THEME_FILE")
fi

if [[ -n "$CURRENT_THEME_NAME" && "$CURRENT_THEME_NAME" != "$LAST_THEME_NAME" ]]; then
    load_wallpapers

    if (( ${#WALLPAPERS[@]} > 0 )); then
        echo "$CURRENT_THEME_NAME" > "$LAST_THEME_FILE"

        if [[ -L "$CURRENT_BACKGROUND_LINK" ]]; then
            CURRENT_BACKGROUND=$(readlink -f "$CURRENT_BACKGROUND_LINK")
        else
            CURRENT_BACKGROUND=""
        fi

        INDEX=-1
        for i in "${!WALLPAPERS[@]}"; do
            if [[ $(readlink -f "${WALLPAPERS[$i]}") == "$CURRENT_BACKGROUND" ]]; then
                INDEX=$i
                break
            fi
        done

        if (( INDEX == -1 )); then
            RANDOM_WALLPAPER="$(pick_random_wallpaper)"
            record_wallpaper "$RANDOM_WALLPAPER"
            touch_last_change
            exec omarchy-theme-bg-set "$RANDOM_WALLPAPER"
        fi
    fi
fi

if [[ -n "$CURRENT_THEME_NAME" ]]; then
    echo "$CURRENT_THEME_NAME" > "$LAST_THEME_FILE"
fi

load_wallpapers

if (( ${#WALLPAPERS[@]} == 0 )); then
    notify-send "No background was found" -t 2000
    pkill -x swaybg
    setsid uwsm-app -- swaybg --color '#000000' >/dev/null 2>&1 &
    exit 0
fi

set_next_wallpaper
