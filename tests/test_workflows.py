from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_test_workflow_records_and_uploads_health_snapshot() -> None:
    workflow = ROOT / ".github" / "workflows" / "tests.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "name: Record health snapshot" in text
    assert "agent-metrics health --append" in text
    assert "--input-file /tmp/agent-metrics-ci-health.json" in text
    assert "--bundle agent-metrics-ci" in text
    assert (
        '"contract_files": len(list(Path(".agent-metrics/contracts").glob("*.md")))'
        in text
    )
    assert '"pytest_passed": 1' in text

    assert "name: Upload health snapshot" in text
    assert "uses: actions/upload-artifact@v4" in text
    assert "name: agent-metrics-health" in text
    assert "path: .agent-metrics/health.jsonl" in text
    assert "if-no-files-found: error" in text

    assert text.index("name: Test") < text.index("name: Record health snapshot")
    assert text.index("name: Record health snapshot") < text.index(
        "name: Upload health snapshot"
    )
