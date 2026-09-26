"""Phase 4 comparison report structural test (0010 step 4).

Checks coverage (3 chains x 10 questions x 2 langs), not quality judgment.
Phase 4 reports are frozen at the 10-question bank (q01-q10); the bank grows
to ~20 in Phase 5 (0011), so these tests pin the q01-q10 subset.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT = REPO_ROOT / "evals" / "reports" / "phase-4-comparison.md"
BANK = REPO_ROOT / "evals" / "question_bank.json"


def _phase4_bank() -> list[dict]:
    bank = json.loads(BANK.read_text(encoding="utf-8"))["questions"]
    frozen = [item for item in bank if item["id"] in {f"q{i:02d}" for i in range(1, 11)}]
    assert len(frozen) == 10
    return frozen


def test_comparison_report_covers_all_cells() -> None:
    bank = _phase4_bank()
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


def test_fixes_report_covers_all_cells_plus_delta() -> None:
    bank = _phase4_bank()
    report = REPO_ROOT / "evals" / "reports" / "phase-4b-fixes-comparison.md"
    text = report.read_text(encoding="utf-8")
    for item in bank:
        assert f"## {item['id']}" in text
    for chain in ("naive", "persona", "cite-or-refuse"):
        assert text.count(f"### {chain}") == len(bank)
    assert "## Delta vs phase-4-comparison.md" in text
