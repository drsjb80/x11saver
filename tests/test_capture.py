"""tools/capture: argument handling and GIF output."""
import shutil
import sys

import pytest

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def run_main(monkeypatch, capture_tool, *argv):
    monkeypatch.setattr(sys, "argv", ["capture", *argv])
    capture_tool.main()


@pytest.mark.parametrize("argv", [[], ["rain", "--demos"]])
def test_needs_exactly_one_of_plugin_or_demos(monkeypatch, capture_tool, argv):
    monkeypatch.setattr(capture_tool.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    with pytest.raises(SystemExit) as exc:
        run_main(monkeypatch, capture_tool, *argv)
    assert exc.value.code == 2


def test_reports_missing_ffmpeg(monkeypatch, capture_tool):
    monkeypatch.setattr(capture_tool.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit) as exc:
        run_main(monkeypatch, capture_tool, "rain")
    assert "ffmpeg is required" in str(exc.value.code)


def test_reports_ffmpeg_failure(monkeypatch, capture_tool, tmp_path):
    class FailingFfmpeg:
        def __init__(self, *args, **kwargs):
            self.stdin = open(tmp_path / "frames.raw", "wb")

        def wait(self):
            return 1

    monkeypatch.setattr(capture_tool.subprocess, "Popen", FailingFfmpeg)
    with pytest.raises(SystemExit) as exc:
        capture_tool.capture("rain", str(tmp_path / "x.gif"), size="32x24",
                             seconds=0.1, fps=10, warmup=0)
    assert "ffmpeg failed for rain" in str(exc.value.code)


@needs_ffmpeg
def test_capture_writes_a_gif(monkeypatch, capture_tool, tmp_path):
    out = tmp_path / "rain.gif"
    run_main(monkeypatch, capture_tool, "rain", "--size", "64x48", "--seconds", "0.5",
             "--fps", "10", "--warmup", "0.1", "-o", str(out))
    assert out.read_bytes()[:4] == b"GIF8"


@needs_ffmpeg
def test_demos_writes_every_configured_demo(monkeypatch, capture_tool, tmp_path):
    small = dict(size="64x48", seconds=0.3, fps=10, warmup=0.1)
    monkeypatch.setattr(capture_tool, "DEMOS", {"rain": small, "starfield": small})
    run_main(monkeypatch, capture_tool, "--demos", str(tmp_path))
    assert sorted(p.name for p in tmp_path.iterdir()) == ["rain.gif", "starfield.gif"]


def test_every_plugin_has_a_demo_entry(capture_tool):
    from conftest import PLUGINS
    assert set(capture_tool.DEMOS) == set(PLUGINS), \
        "add new plugins to DEMOS in tools/capture so --demos includes them"
