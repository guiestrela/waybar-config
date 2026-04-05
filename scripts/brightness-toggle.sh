#!/bin/bash
# Brightness Toggle Script for Waybar
# Toggles between max brightness and 50%

current=$(brightnessctl get)
max=$(brightnessctl max)

if [ "$current" -eq "$max" ]; then
    # Set to 50%
    target=$((max / 2))
    brightnessctl set "$target"
else
    # Set to max
    brightnessctl set "$max"
fi
