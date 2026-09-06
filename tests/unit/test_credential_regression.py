from pathlib import Path
import json

import pytest

from scripts.check_no_embedded_operational_credentials import (
    scan_repository,
    scan_text,
)


def test_scanner_detects_the_missed_database_credential_shape() -> None:
    source = "\n".join(
        [
            "DB_" + "PASS" + 'WORD = "OperationalValue-42!"',
            "Pass" + "word: `OperationalValue-42!`",
        ]
    )

    findings = scan_text(source, "training.py")

    assert [finding.rule for finding in findings] == [
        "literal-password-assignment",
        "documented-literal-password",
    ]


def test_scanner_accepts_environment_injection_and_documented_placeholders() -> None:
    source = "\n".join(
        [
            'DB_PASSWORD = os.getenv("DATABASE_PASSWORD")',
            "postgresql://taxiuser:${DATABASE_PASSWORD}@db.example.invalid/taxi",
            "taxi-duration-db.xxxxx.us-east-1.rds.amazonaws.com",
        ]
    )

    assert scan_text(source, "example.py") == []


def test_current_tracked_tree_has_no_operational_database_credentials() -> None:
    root = Path(__file__).resolve().parents[2]

    assert scan_repository(root) == []


@pytest.mark.parametrize(
    "value",
    [
        "Fictional[42]!",
        "Fictional{42}!",
        "Fictional<42>!",
        "Fictional-example-42!",
        "Notyour_secret42",
    ],
)
def test_punctuation_and_placeholder_substrings_do_not_exempt_literals(value):
    assert scan_text("DB_PASS" + "WORD = " + repr(value), "probe.py")


def test_repository_scans_markdown_and_notebook_outputs(tmp_path, monkeypatch):
    from scripts import check_no_embedded_operational_credentials as scanner

    documentation = tmp_path / "guide.md"
    notebook = tmp_path / "demo.ipynb"
    documentation.write_text("Pass" + "word: `Fictional[42]!`", encoding="utf-8")
    notebook.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "source": [],
                        "outputs": [
                            {
                                "output_type": "stream",
                                "text": ["DB_PASS" + "WORD = ", "'Fictional[42]!'\n"],
                            },
                            {
                                "output_type": "display_data",
                                "data": {"text/plain": ["Pass" + "word: `Fictional[42]!`"]},
                            },
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(scanner, "_tracked_paths", lambda root: [documentation, notebook])
    findings = scan_repository(tmp_path)
    assert {item.path for item in findings} == {"guide.md", "demo.ipynb"}
    assert len(findings) == 3
