"""Chains package: registry grows in Phases 4-5 (0009 step 2)."""

from tolstoy.chains.naive import NaiveChain

CHAIN_REGISTRY: dict[str, type] = {"naive": NaiveChain}

__all__ = ["CHAIN_REGISTRY", "NaiveChain"]
