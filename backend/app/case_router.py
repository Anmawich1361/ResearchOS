import re
from typing import Literal


DemoCase = Literal["canadian_banks", "oil_airlines", "ai_capex_semis"]

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def route_question(question: str) -> DemoCase:
    """Route a user question to one of the deterministic golden-path demos."""
    tokens = set(_TOKEN_RE.findall(question.lower()))

    if _matches_ai_capex_case(tokens):
        return "ai_capex_semis"

    if _matches_oil_airlines_case(tokens):
        return "oil_airlines"

    if _matches_canadian_banks_case(tokens):
        return "canadian_banks"

    return "canadian_banks"


def _matches_oil_airlines_case(tokens: set[str]) -> bool:
    oil_terms = {"oil", "crude", "fuel", "jet", "energy"}
    airline_terms = {"airline", "airlines", "carrier", "carriers", "travel"}
    demand_terms = {"consumer", "demand", "leisure", "fare", "fares"}

    return bool(tokens & oil_terms) and bool(tokens & (airline_terms | demand_terms))


def _matches_ai_capex_case(tokens: set[str]) -> bool:
    ai_terms = {"ai", "artificial", "intelligence", "accelerator", "gpu", "gpus"}
    capex_terms = {
        "capex",
        "capital",
        "spending",
        "spend",
        "infrastructure",
        "datacenter",
        "datacenters",
        "data",
        "center",
        "centers",
    }
    sector_terms = {
        "semiconductor",
        "semiconductors",
        "semi",
        "semis",
        "chip",
        "chips",
        "hyperscaler",
        "hyperscalers",
        "cloud",
    }

    return bool(tokens & ai_terms) and bool(tokens & (capex_terms | sector_terms))


def _matches_canadian_banks_case(tokens: set[str]) -> bool:
    rate_terms = {"rate", "rates", "cut", "cuts", "easing", "boc"}
    bank_terms = {"bank", "banks", "banking", "canada", "canadian", "mortgage"}

    return bool(tokens & rate_terms) or bool(tokens & bank_terms)
