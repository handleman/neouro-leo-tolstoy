"""Cite-or-refuse chain (0010 step 2).

Same retriever as `naive`, must-cite templates, plus a score gate: when
the best hit scores below `TOLSTOY_SCORE_THRESHOLD`, answer the refusal
string with empty sources and no generator call (nothing wasted on
fabrication).
"""

from tolstoy.chains.base import StuffChain
from tolstoy.config import load_settings


class CiteOrRefuseChain(StuffChain):
    name = "cite-or-refuse"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.gate_threshold = load_settings().score_threshold
