# Linux setup

Hyprland configuration and helper scripts live in `hypr/`.

Run `./install.sh` to link `~/.config/hypr` to this repository's `hypr/` directory.
The installer uses `$XDG_CONFIG_HOME` when set and leaves existing configurations untouched.
Move an existing configuration aside before installing on another machine.
Running the installer again preserves an existing matching link.

Edit files under `hypr/` and commit changes with Git.
Keep the repository at its installed location or recreate the link after moving it.
Migration backups under `hypr/backups/` remain local and are excluded from Git.

The configuration includes machine-specific display names, workspace assignments,
application commands, and a wallpaper path in `hypr/scripts/set-wallpaper.sh`.
