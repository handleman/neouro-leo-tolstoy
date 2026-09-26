"""Phase 5 eval report structural test (0011 step 4).

Checks coverage (5 chains x 20 questions x 2 langs + hit-rate table with a
filled winner verdict), not quality judgment.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT = REPO_ROOT / "evals" / "reports" / "phase-5-eval.md"
BANK = REPO_ROOT / "evals" / "question_bank.json"
PROBES = REPO_ROOT / "evals" / "refusal_probes.json"
CHAINS = ("naive", "persona", "cite-or-refuse", "rerank", "multi-query")


def test_phase5_bank_has_twenty_questions_and_probes() -> None:
    bank = json.loads(BANK.read_text(encoding="utf-8"))["questions"]
    assert len(bank) == 20
    for item in bank:
        assert {"id", "ru", "en", "expected", "notes"} <= set(item)
        assert {"volume", "work"} <= set(item["expected"])
    probes = json.loads(PROBES.read_text(encoding="utf-8"))["probes"]
    assert len(probes) >= 2


def test_phase5_report_covers_all_cells_and_verdict() -> None:
    bank = json.loads(BANK.read_text(encoding="utf-8"))["questions"]
    text = REPORT.read_text(encoding="utf-8")
    assert "Hit-rate@k per chain" in text
    for item in bank:
        assert f"### {item['id']}" in text
    for chain in CHAINS:
        assert f"| {chain} |" in text
        assert f"- **{chain}**" in text
    assert "Refusal precision" in text
    assert "Retrieval winner" in text
    assert "_TBD after reading._" not in text, "winner verdict must be filled in"
