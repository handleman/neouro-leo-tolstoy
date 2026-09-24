"""Versioned prompt templates (0010 step 1).

One plain-text file per chain per language:
`prompts/<chain>.<lang>.txt` with `[system]` / `[user]` sections.
The `[user]` section uses `{context}` + `{question}` placeholders.
Shared `render_prompt` assembles system + stuffed context + question;
truncation budget behavior is unchanged from Phase 3.
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent

REFUSAL_RU = "Не нашёл ответа на этот вопрос в моих произведениях."
REFUSAL_EN = "I found nothing on this question in my works."


def list_templates() -> list[tuple[str, str]]:
    """Every (chain, lang) pair with a committed template file."""
    pairs = []
    for path in sorted(TEMPLATES_DIR.glob("*.txt")):
        stem = path.stem  # e.g. "cite-or-refuse.ru"
        chain, _, lang = stem.rpartition(".")
        if chain and lang in ("ru", "en"):
            pairs.append((chain, lang))
    return pairs


def load_template(chain: str, lang: str) -> dict[str, str]:
    """Return {"system", "user_template"}; unknown pair raises FileNotFoundError."""
    path = TEMPLATES_DIR / f"{chain}.{lang}.txt"
    text = path.read_text(encoding="utf-8")
    if "[system]" not in text or "[user]" not in text:
        raise ValueError(f"bad template {path}: needs [system] and [user] sections")
    system_part, _, user_part = text.partition("[user]")
    system = system_part.replace("[system]", "").strip()
    user_template = user_part.strip()
    if "{context}" not in user_template or "{question}" not in user_template:
        raise ValueError(f"bad template {path}: [user] needs {{context}} and {{question}}")
    return {"system": system, "user_template": user_template}


def _header(rank: int, hit: dict, lang: str) -> str:
    vol = f"{hit.get('volume'):02d}" if isinstance(hit.get("volume"), int) else "?"
    if lang == "en":
        return f"[{rank}] vol{vol} | {hit.get('work')} | {hit.get('chapter')}"
    return f"[{rank}] том {hit.get('volume')} | {hit.get('work')} | {hit.get('chapter')}"


def render_prompt(
    chain: str, lang: str, question: str, hits: list[dict], budget: int
) -> tuple[str, str]:
    """Return (system, user). Context chunks stuffed in order, truncated to budget."""
    template = load_template(chain, lang)
    parts: list[str] = []
    used = 0
    for rank, hit in enumerate(hits, 1):
        block = f"{_header(rank, hit, lang)}\n{hit.get('text', '')}"
        room = budget - used
        if room <= 0:
            break
        if len(block) > room:
            block = block[:room]
        parts.append(block)
        used += len(block)
    context = "\n\n".join(parts)
    return template["system"], template["user_template"].format(context=context, question=question)
