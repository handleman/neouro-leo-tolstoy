"""Naive stuff-everything chain (0009 step 2, templates in 0010 step 1).

Retrieve top-k (default 4, no filter, no threshold gate) -> render the
`naive` template -> generate -> attach sources in retrieval order.
"""

from tolstoy.chains.base import StuffChain


class NaiveChain(StuffChain):
    name = "naive"
    gate_threshold = 0.0
