# Linux setup

Hyprland configuration and helper scripts live in `hypr/`.
Waybar configuration and styling live in `waybar/`.

Run `./install.sh` to link `~/.config/hypr` and `~/.config/waybar` to the matching
directories in this repository.
The installer uses `$XDG_CONFIG_HOME` when set and leaves existing configurations untouched.
Move an existing configuration aside before installing on another machine.
Running the installer again preserves an existing matching link.

Edit files under `hypr/` or `waybar/` and commit changes with Git.
Keep the repository at its installed location or recreate the link after moving it.
Migration backups under `hypr/backups/` remain local and are excluded from Git.

The configuration includes machine-specific display names, workspace assignments,
application commands, Waybar device identifiers, and a wallpaper path in
`hypr/scripts/set-wallpaper.sh`.
