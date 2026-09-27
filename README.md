# Linux setup

Hyprland configuration and helper scripts live in `hypr/`.
Waybar configuration and styling live in `waybar/`.
keyd keyboard configuration and its system setup helper live in `keyd/`.
SwayNotificationCenter configuration and Noita styling live in `swaync/`.

Run `./install.sh` to link `~/.config/hypr`, `~/.config/waybar`, `~/.config/keyd`, and
`~/.config/swaync` to the matching directories in this repository.
The installer uses `$XDG_CONFIG_HOME` when set and leaves existing configurations untouched.
Move an existing configuration aside before installing on another machine.
Running the installer again preserves an existing matching link.

Edit files under `hypr/`, `waybar/`, `keyd/`, or `swaync/` and commit changes with Git.
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

The mouse side button `275` holds F3 while a Minecraft game window is focused.
Other applications retain the button's normal behavior.
Press the button without modifiers, hold it for F3 combinations, and release it to release F3.
The release targets the original game window even after focus or modifier changes.
Run its behavior checks with `lua tests/minecraft_mouse.lua`.

Install `swaync` and `libnotify` on Arch Linux for desktop notifications.
Hyprland starts the packaged `swaync.service` user service at login.
Right Super + N or the Waybar bell opens notification history.
Right-click the bell to toggle Do Not Disturb.
The panel's **Show notifications on** buttons choose **Primary** for the left display
`DP-1` or **Second** for the right display `DP-2`, which is the default.
The selection persists in `swaync/config.json` across reloads and restarts.
Only popup placement changes, and the notification panel still opens on the focused display.
SwayNC falls back to the focused display when the selected monitor is disconnected.
Normal popups expire after eight seconds and remain in history until dismissed.
Critical notifications remain visible until dismissed.
The SwayNC theme extends the packaged GTK 4 stylesheet with the Noita palette.
Reload edits with `swaync-client -R` and `swaync-client -rs`.
Send a test popup with `notify-send "Notifications ready"`.

Codex completion alerts use `swaync/scripts/codex-notify.py` through the global
`notify` setting in `~/.codex/config.toml`:

```toml
notify = ["python3", "/absolute/path/to/.config/swaync/scripts/codex-notify.py"]
```

Place this setting above the first TOML section and use the installed absolute path.
Restart or resume existing Codex sessions after changing their notification configuration.
Each `agent-turn-complete` event sends a popup with the project, session identifier,
and a shortened response, including when the terminal is focused.
A completed turn can include a question and does not guarantee task success.
SwayNC's Do Not Disturb setting still controls popup visibility.
The hook uses the [documented Codex notification payload](https://learn.chatgpt.com/docs/config-file/config-advanced#notifications).

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

Waybar battery modules refresh every second using Python 3, PyGObject, BlueZ, and UPower.
On Arch Linux the packages are `python`, `python-gobject`, `bluez`, and `upower`.
Model filters live in `waybar/config.jsonc`.

| Device | Battery source | Charging state |
| --- | --- | --- |
| Keychron M6 | USB status query once per second, Bluetooth fallback | USB reports charging |
| NuPhy Air75 V3 | BlueZ battery service | Bluetooth reports percentage only |
| AirPods Max | Persistent Apple battery notifications over Bluetooth | Reports charging when connected |

The USB mouse query requires read/write access to its vendor `/dev/hidraw*` interface.
The current system already grants this access.
The AirPods connection subscribes to status without changing audio or listening settings.
Bluetooth levels are device-reported updates, so a one-second display refresh does not force
a new hardware measurement every second.
Keyboard USB charging telemetry remains unverified and has no custom USB reader.
UPower provides a fallback for wired devices with standard battery reporting.

Missing readings display `N/A`, and reported charging states show a lightning indicator.
Each device shares one reader across all bars through a runtime lock and cache.
Readers rediscover devices after reconnects and clear disconnected Bluetooth readings.
For a live diagnostic, run `waybar/scripts/battery.py mouse --model "Keychron M6" --watch`.
Without `--watch`, the script prints the UPower snapshot only.

The M6 query follows [Keychron Launcher](https://launcher.keychron.com/), using report
`0xB3`, command `0x06`, and the packed percentage/charging byte in response `0xB4`.
The AirPods handshake and subscription follow the
[AAP protocol implementation](https://github.com/superninjv/airpods-helper/tree/main/daemon/src/aap),
with the Max component identifier verified against the connected headset.
Run battery checks with `python -m unittest discover -s tests -p 'test_battery.py'`.
