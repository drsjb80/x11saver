# x11saver

A small, plugin-based screensaver for X11 desktops. It runs a fullscreen
pygame window with an effect, and on the first key press or mouse click it
locks the session and exits.

## Usage

```
./x11saver thematrix
./x11saver starfield
```

The plugin name can also be given as a path, e.g. `plugins/thematrix`.

Requires Python 3 and pygame (`pip install -r requirements.txt`).

## Plugins

A plugin is a module in `plugins/` that defines:

- `init(screen, size)`: called once after the display is set up
- `render(screen, dt)`: called every frame; `dt` is seconds since the last frame
- `shutdown()`: called once before exit

Optionally, a plugin can set a module-level `FPS` (default 30).

To add an effect, drop a new file in `plugins/` following that interface.

## Locking

On exit the runner locks the session before closing its window, so the
desktop never shows through. It picks a lock command from
`XDG_CURRENT_DESKTOP`:

| Desktop | Command |
|---|---|
| Cinnamon | `cinnamon-screensaver-command --lock` |
| MATE | `mate-screensaver-command --lock` |
| Xfce | `xflock4` |
| GNOME, KDE | `loginctl lock-session` |

If no command works, it falls back to `loginctl lock-session`. If that also
fails, it prints a warning and exits without locking.

Only Cinnamon has been tested so far.

## Input handling

Input is ignored for the first second so startup events don't close the
screensaver immediately. After that, a key press or mouse click exits.

Mouse motion exits too, by default on any movement. To tolerate small jitter,
pass a threshold in pixels; motion only exits once the pointer has moved more
than that far from where it was when the grace period ended:

```
./x11saver thematrix --mouse-threshold 10
```

## Daemon mode

`-d` runs x11saver in the background. It checks the X server's idle time once
a minute, and when you've been idle for 10 minutes it starts the saver. When
the saver exits (on input, after locking), the daemon keeps watching.

```
./x11saver -d thematrix
./x11saver -d starfield --timeout 5 --interval 30
```

- `--timeout MINUTES` sets the idle time before the saver starts (default 10).
- `--interval SECONDS` sets how often idle time is checked (default 60).

Stop the daemon with Ctrl-C, or `pkill -f "x11saver -d"`.

Requires `python-xlib` (`pip install -r requirements.txt` installs it).

Set the built-in screensaver's idle timeout to "never". Otherwise both will
try to start, and the built-in one may lock the screen first.

To start it at login, add the command to `~/.profile` and put `&` at the end so
it runs in the background. If your profile runs before the X session starts,
the daemon will print a warning each check until the display is available.

## License

MIT. See [LICENSE](LICENSE).
