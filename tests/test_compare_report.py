"""Phase 4 comparison report structural test (0010 step 4).

Checks coverage (3 chains x 10 questions x 2 langs), not quality judgment.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT = REPO_ROOT / "evals" / "reports" / "phase-4-comparison.md"
BANK = REPO_ROOT / "evals" / "question_bank.json"


def test_comparison_report_covers_all_cells() -> None:
    bank = json.loads(BANK.read_text(encoding="utf-8"))["questions"]
    assert len(bank) == 10
    text = REPORT.read_text(encoding="utf-8")
    for item in bank:
        assert f"## {item['id']}" in text
        assert item["ru"] in text
    for chain in ("naive", "persona", "cite-or-refuse"):
        assert text.count(f"### {chain}") == len(bank)
    assert text.count("**ru**") == 3 * len(bank)
    assert text.count("**en**") == 3 * len(bank)
    assert "Author notes" in text
    assert "_TBD" not in text, "author notes must be filled in, not placeholders"
