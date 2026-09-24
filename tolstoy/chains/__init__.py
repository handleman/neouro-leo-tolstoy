"""Chains package: registry grows per phase (0009 step 2, 0010 step 2)."""

from tolstoy.chains.cite_or_refuse import CiteOrRefuseChain
from tolstoy.chains.naive import NaiveChain
from tolstoy.chains.persona import PersonaChain

CHAIN_REGISTRY: dict[str, type] = {
    "naive": NaiveChain,
    "persona": PersonaChain,
    "cite-or-refuse": CiteOrRefuseChain,
}

__all__ = ["CHAIN_REGISTRY", "CiteOrRefuseChain", "NaiveChain", "PersonaChain"]
