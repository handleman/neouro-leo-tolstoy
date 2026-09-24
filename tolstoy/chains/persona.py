"""Persona chain (0010 step 2): same retriever as `naive`, Tolstoy-voice templates."""

from tolstoy.chains.base import StuffChain


class PersonaChain(StuffChain):
    name = "persona"
    gate_threshold = 0.0
