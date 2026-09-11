#!/bin/bash

WALLPAPER="/home/decodingintuition/Pictures/wallpapers/wallpaper"

# Wait until hyprpaper's socket is ready
until [[ -S "/run/user/$(id -u)/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.hyprpaper.sock" ]]; do
  sleep 0.2
done

hyprctl hyprpaper wallpaper "DP-1,$WALLPAPER"
hyprctl hyprpaper wallpaper "DP-2,$WALLPAPER"
