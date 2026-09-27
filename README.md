# Linux setup

Hyprland configuration and helper scripts live in `hypr/`.
Waybar configuration and styling live in `waybar/`.
keyd keyboard configuration and its system setup helper live in `keyd/`.

Run `./install.sh` to link `~/.config/hypr`, `~/.config/waybar`, and
`~/.config/keyd` to the matching directories in this repository.
The installer uses `$XDG_CONFIG_HOME` when set and leaves existing configurations untouched.
Move an existing configuration aside before installing on another machine.
Running the installer again preserves an existing matching link.

Edit files under `hypr/`, `waybar/`, or `keyd/` and commit changes with Git.
Keep the repository at its installed location or recreate the link after moving it.
Migration backups under `hypr/backups/` remain local and are excluded from Git.

`hypr/hyprland.lua` loads these modules from `hypr/config/`:

| File | Contents |
| --- | --- |
| `keybindings.lua` | Keyboard and mouse shortcuts, application commands, desktop modifier |
| `monitors.lua` | Displays and workspace placement |
| `startup.lua` | Environment variables and startup applications |
| `appearance.lua` | Default layout, borders, effects, and animations |
| `layout.lua` | Current layout, floating toggle, and tiled-layout memory |
| `input.lua` | Keyboard, pointer, gestures, and device settings |
| `rules.lua` | Window rules and the shared floating-layout handle |

Edits to these modules trigger Hyprland's automatic configuration reload.

New sessions start in monocle, and layout selection survives configuration reloads.
Right Super + Space switches between monocle and main across all workspaces.
Right Super + Shift + Space toggles global floating mode and returns to the last tiled layout.
Right Super + Space while floating exits floating mode and selects the next tiled layout.
Windows already floating before the global toggle remain floating afterward.

On Arch Linux, run `./keyd/setup.sh` to install keyd, link its configuration at
`/etc/keyd/default.conf`, and enable the service.
This helper requires administrator authentication and preserves any different
configuration already at that system path.
After editing `keyd/default.conf`, apply it with `sudo keyd reload`.

The keyboard mappings follow the current keyboard's physical labels:

- Left Super + HJKL sends arrow keys.
- Left Alt supplies application shortcuts.
- Right Control supplies Control + Alt for Emacs Control + Meta shortcuts.
- Right Super supplies Mod3 for Hyprland keyboard and mouse shortcuts.

The keyboard reports different modifier names from its physical labels.
Review `keyd/default.conf` and `hypr/keymap-mod3.xkb` before using another layout.

The configuration includes machine-specific display names, workspace assignments,
application commands, Waybar battery model filters, and a wallpaper path in
`hypr/scripts/set-wallpaper.sh`.

Waybar battery modules use Python 3 and UPower to find the configured mouse and keyboard models.
Missing battery readings display `N/A`, including wired connections without battery reporting.
Reported charging states show a lightning indicator.
Run battery checks with `python -m unittest discover -s tests -p 'test_battery.py'`.
