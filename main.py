"""Compatibility launcher with separate explicit training and serving operations.

No model is created on API startup. Delegated commands retain their exit status;
the launcher does not claim model readiness or fabricate fallback artifacts.
"""

import argparse
import subprocess
import sys


def __getattr__(name):
    # Preserve uvicorn main:app without importing MLflow for CLI help.
    if name == "app":
        from taxi_duration_predictor.api.main import app

        return app
    raise AttributeError(name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    api = commands.add_parser("api", help="Serve the API; does not train a model")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8000)
    commands.add_parser("bootstrap", help="Train and evaluate the owned synthetic fixture")
    args = parser.parse_args(argv)
    if args.command == "api":
        command = [
            sys.executable,
            "-m",
            "uvicorn",
            "taxi_duration_predictor.api.main:app",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ]
    else:
        command = [sys.executable, "-m", "taxi_duration_predictor.pipeline.train", "--bootstrap"]
    # Inherit operator tracking URI and selection settings unchanged.
    # No global MLflow mutation, fallback artifact, or extra service.
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
