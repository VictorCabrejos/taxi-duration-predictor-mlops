from pathlib import Path

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
