#!/bin/bash
# Wallpaper Next Script for Waybar
# Cycles to next wallpaper in a directory

# CONFIG: Set your wallpaper directory
WALLPAPER_DIR="${HOME}/Pictures/wallpapers"

# CONFIG: Set wallpaper command (uncomment your WM)
# Hyprland
# WALLPAPER_CMD="hyprpaper"

# Sway
# WALLPAPER_CMD="swaybg -i"

# Other (feh for openbox/i3)
WALLPAPER_CMD="swaybg -i"

# Get current wallpaper from hyprland
current=$(hyprctl hyprpaper | grep "loaded" | head -1 | cut -d'"' -f2)

# Find next wallpaper
if [ -d "$WALLPAPER_DIR" ]; then
    # Get list of images
    images=$(find "$WALLPAPER_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \) | sort)
    
    # Find current and get next
    found=0
    for img in $images; do
        if [ "$found" -eq 1 ]; then
            next=$img
            break
        fi
        if [ "$img" = "$current" ]; then
            found=1
        fi
    done
    
    # Loop back to first if at end
    if [ -z "$next" ]; then
        next=$(echo "$images" | head -1)
    fi
    
    # Set wallpaper
    $WALLPAPER_CMD "$next" 2>/dev/null &
    
    # Notify (optional)
    # notify-send "Wallpaper" "$(basename "$next")"
fi
