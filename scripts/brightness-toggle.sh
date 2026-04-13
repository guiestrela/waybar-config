#!/bin/bash

# Alterna entre brilho mínimo e máximo
MAX_BRIGHTNESS=$(brightnessctl max)
CURRENT=$(brightnessctl get)

if [ "$CURRENT" -gt $((MAX_BRIGHTNESS / 2)) ]; then
    # Brilho alto, diminui para 20%
    brightnessctl set "20%"
else
    # Brilho baixo, aumenta para 100%
    brightnessctl set "100%"
fi
