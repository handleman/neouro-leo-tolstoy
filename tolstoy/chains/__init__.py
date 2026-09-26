"""Chains package: registry grows per phase (0009 step 2, 0010 step 2, 0011 steps 2-3)."""

from tolstoy.chains.cite_or_refuse import CiteOrRefuseChain
from tolstoy.chains.multiquery import MultiQueryChain
from tolstoy.chains.naive import NaiveChain
from tolstoy.chains.persona import PersonaChain
from tolstoy.chains.rerank import RerankChain

CHAIN_REGISTRY: dict[str, type] = {
    "naive": NaiveChain,
    "persona": PersonaChain,
    "cite-or-refuse": CiteOrRefuseChain,
    "rerank": RerankChain,
    "multi-query": MultiQueryChain,
}

__all__ = [
    "CHAIN_REGISTRY",
    "CiteOrRefuseChain",
    "MultiQueryChain",
    "NaiveChain",
    "PersonaChain",
    "RerankChain",
]
