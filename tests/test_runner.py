"""Tests for the x11saver runner: names, input handling, locking, daemon, CLI."""
import subprocess
import sys
import types

import pygame
import pytest


# --- plugin names -----------------------------------------------------------

@pytest.mark.parametrize("given", ["snow", "plugins/snow", "plugins/snow.py",
                                   "/abs/path/plugins/snow.py"])
def test_normalize_plugin_name(runner, given):
    assert runner.normalize_plugin_name(given) == "snow"


# --- exit decision ----------------------------------------------------------

@pytest.mark.parametrize("event_type", [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN])
def test_key_or_click_exits(runner, event_type):
    assert runner.should_exit(event_type, (0, 0), (0, 0), 0.0)


def test_any_motion_exits_with_zero_threshold(runner):
    assert runner.should_exit(pygame.MOUSEMOTION, (1, 0), (0, 0), 0.0)


def test_motion_event_without_movement_does_not_exit(runner):
    assert not runner.should_exit(pygame.MOUSEMOTION, (5, 5), (5, 5), 0.0)


def test_motion_within_threshold_does_not_exit(runner):
    assert not runner.should_exit(pygame.MOUSEMOTION, (3, 4), (0, 0), 10.0)   # 5px


def test_motion_beyond_threshold_exits(runner):
    assert runner.should_exit(pygame.MOUSEMOTION, (30, 40), (0, 0), 10.0)    # 50px


def test_threshold_is_measured_from_baseline_not_last_event(runner):
    # Many small moves that drift far from the start must still exit.
    assert runner.should_exit(pygame.MOUSEMOTION, (12, 0), (0, 0), 10.0)


@pytest.mark.parametrize("event_type", [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN,
                                        pygame.MOUSEMOTION])
def test_input_ignored_during_grace_period(runner, event_type):
    # baseline is None until the grace period ends. This used to crash for
    # MOUSEMOTION when the grace period ended mid-frame.
    assert not runner.should_exit(event_type, (500, 500), None, 0.0)


def test_other_events_never_exit(runner):
    assert not runner.should_exit(pygame.ACTIVEEVENT, (0, 0), (0, 0), 0.0)


# --- locking ----------------------------------------------------------------

@pytest.fixture
def fake_run(monkeypatch, runner):
    """Replace subprocess.run; results maps command name -> returncode or exception."""
    calls = []
    results = {}

    def run(cmd, *args, **kwargs):
        calls.append(cmd)
        outcome = results.get(cmd[0], 0)
        if isinstance(outcome, Exception):
            raise outcome
        return subprocess.CompletedProcess(cmd, outcome)

    monkeypatch.setattr(runner.subprocess, "run", run)
    return types.SimpleNamespace(calls=calls, results=results)


def test_lock_uses_desktop_command(monkeypatch, runner, fake_run):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "X-Cinnamon")
    assert runner.lock_session()
    assert fake_run.calls == [["cinnamon-screensaver-command", "--lock"]]


@pytest.mark.parametrize("desktop,expected", [
    ("MATE", ["mate-screensaver-command", "--lock"]),
    ("XFCE", ["xflock4"]),
    ("GNOME", ["loginctl", "lock-session"]),
    ("KDE", ["loginctl", "lock-session"]),
])
def test_lock_command_per_desktop(monkeypatch, runner, fake_run, desktop, expected):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", desktop)
    assert runner.lock_session()
    assert fake_run.calls[0] == expected


def test_lock_handles_colon_separated_desktops(monkeypatch, runner, fake_run):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")
    assert runner.lock_session()
    assert fake_run.calls == [["loginctl", "lock-session"]]


def test_lock_falls_back_when_desktop_command_fails(monkeypatch, runner, fake_run):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "X-Cinnamon")
    fake_run.results["cinnamon-screensaver-command"] = 1
    assert runner.lock_session()
    assert fake_run.calls[-1] == ["loginctl", "lock-session"]


def test_lock_skips_missing_command(monkeypatch, runner, fake_run):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "XFCE")
    fake_run.results["xflock4"] = FileNotFoundError("xflock4")
    assert runner.lock_session()
    assert fake_run.calls == [["xflock4"], ["loginctl", "lock-session"]]


@pytest.mark.parametrize("env", [None, "", "SomeUnknownDesktop"])
def test_lock_unknown_desktop_uses_fallback(monkeypatch, runner, fake_run, env):
    if env is None:
        monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)
    else:
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", env)
    assert runner.lock_session()
    assert fake_run.calls == [["loginctl", "lock-session"]]


def test_lock_warns_when_nothing_works(monkeypatch, runner, fake_run, capsys):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "X-Cinnamon")
    fake_run.results["cinnamon-screensaver-command"] = FileNotFoundError()
    fake_run.results["loginctl"] = 1
    assert not runner.lock_session()
    assert "could not lock" in capsys.readouterr().err


# --- daemon -----------------------------------------------------------------

def test_check_once_launches_when_idle_long_enough(runner):
    launched = []
    assert runner.check_once(lambda: 600_000, 600_000, lambda: launched.append(1))
    assert launched == [1]


def test_check_once_waits_when_not_idle(runner):
    launched = []
    assert not runner.check_once(lambda: 599_999, 600_000, lambda: launched.append(1))
    assert launched == []


def test_check_once_survives_idle_errors(runner, capsys):
    def broken():
        raise RuntimeError("no display")
    assert not runner.check_once(broken, 0, lambda: pytest.fail("should not launch"))
    assert "idle check failed (no display)" in capsys.readouterr().err


def test_daemon_launches_saver_with_args_and_stops_on_ctrl_c(monkeypatch, runner):
    sleeps, launched = [], []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        if len(sleeps) > 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(runner.time, "sleep", fake_sleep)
    monkeypatch.setattr(runner, "x_idle_ms", lambda: 10 * 60 * 1000)
    monkeypatch.setattr(runner.subprocess, "run", lambda cmd: launched.append(cmd))

    with pytest.raises(SystemExit) as exc:
        runner.daemon("snow", timeout_min=10, interval_s=60, mouse_threshold=5.0)
    assert exc.value.code == 0
    assert sleeps == [60, 60, 60]
    assert len(launched) == 2
    cmd = launched[0]
    assert cmd[0] == sys.executable
    assert cmd[1].endswith("x11saver")
    assert cmd[2:] == ["snow", "--mouse-threshold", "5.0"]


def test_x_idle_ms_reads_and_closes_display(monkeypatch, runner):
    """x_idle_ms queries the XScreenSaver extension and always closes the display."""
    from Xlib import display as xdisplay
    from Xlib.ext import screensaver

    closed = []

    class FakeDisplay:
        def screen(self):
            return types.SimpleNamespace(root="ROOT")

        def close(self):
            closed.append(True)

    monkeypatch.setattr(xdisplay, "Display", FakeDisplay)
    monkeypatch.setattr(screensaver, "query_info",
                        lambda root: types.SimpleNamespace(idle=1234))
    assert runner.x_idle_ms() == 1234
    assert closed == [True]


# --- command line -----------------------------------------------------------

def test_parse_args_defaults(runner):
    args = runner.parse_args(["snow"])
    assert (args.plugin, args.daemon, args.timeout, args.interval, args.mouse_threshold) \
        == ("snow", False, 10.0, 60.0, 0.0)


def test_parse_args_daemon_options(runner):
    args = runner.parse_args(["-d", "rain", "--timeout", "5", "--interval", "30",
                              "--mouse-threshold", "10"])
    assert (args.plugin, args.daemon, args.timeout, args.interval, args.mouse_threshold) \
        == ("rain", True, 5.0, 30.0, 10.0)


def test_parse_args_requires_plugin(runner):
    with pytest.raises(SystemExit):
        runner.parse_args([])


# --- main loop (headless) ---------------------------------------------------

def test_main_runs_plugin_then_locks_and_exits_on_key(monkeypatch, runner):
    """Drive main() with a fake plugin: frames render, a key press locks and exits."""
    log = []
    fake = types.ModuleType("plugins.fake")
    fake.FPS = 1000
    fake.init = lambda screen, size: log.append("init")
    fake.render = lambda screen, dt: log.append("render")
    fake.shutdown = lambda: log.append("shutdown")
    monkeypatch.setitem(sys.modules, "plugins.fake", fake)

    frames = []

    def fake_events():
        frames.append(1)
        if len(frames) == 1:
            return []
        if len(frames) == 2:                # an event that should not exit
            return [pygame.event.Event(pygame.ACTIVEEVENT, gain=1, state=1)]
        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)]

    monkeypatch.setattr(runner, "GRACE_MS", 0)
    monkeypatch.setattr(runner.pygame.event, "get", fake_events)
    monkeypatch.setattr(runner, "lock_session", lambda: log.append("lock"))
    monkeypatch.setattr(runner.pygame, "quit", lambda: log.append("quit"))

    with pytest.raises(SystemExit):
        runner.main("plugins/fake.py")

    assert log[0] == "init"
    assert log.count("render") == 2
    # Lock happens before the window closes, so the desktop never shows.
    assert log[-3:] == ["shutdown", "lock", "quit"]
