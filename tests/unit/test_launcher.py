"""The compatibility launcher never fabricates a successful lifecycle."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def launcher():
    spec = importlib.util.spec_from_file_location(
        "taxi_launcher_test", Path(__file__).parents[2] / "main.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("status", [0, 1, 27])
def test_bootstrap_propagates_status(launcher, monkeypatch, status):
    calls = []
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda *a, **kw: (calls.append((a, kw)) or SimpleNamespace(returncode=status)),
    )
    assert launcher.main(["bootstrap"]) == status
    assert calls == [
        (
            (
                [
                    launcher.sys.executable,
                    "-m",
                    "taxi_duration_predictor.pipeline.train",
                    "--bootstrap",
                ],
            ),
            {"check": False},
        )
    ]


def test_api_does_not_train_and_defaults_to_loopback(launcher, monkeypatch):
    calls = []
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda command, **kw: (calls.append(command) or SimpleNamespace(returncode=4)),
    )
    assert launcher.main(["api"]) == 4
    assert calls == [
        [
            launcher.sys.executable,
            "-m",
            "uvicorn",
            "taxi_duration_predictor.api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ]
    ]


def test_requires_explicit_operation(launcher, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Explicit command required before starting a process")

    monkeypatch.setattr(launcher.subprocess, "run", forbidden)
    with pytest.raises(SystemExit) as error:
        launcher.main([])
    assert error.value.code == 2
    with pytest.raises(SystemExit) as help_exit:
        launcher.main(["--help"])
    assert help_exit.value.code == 0


def test_process_launch_error_is_not_success(launcher, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OSError("process unavailable")

    monkeypatch.setattr(launcher.subprocess, "run", unavailable)
    with pytest.raises(OSError, match="process unavailable"):
        launcher.main(["bootstrap"])
