"""
PHANTOM-NEOTRON Integration Module

Integra Phantom Intelligence com Neotron Compliance Framework.
Garante que todas as recomendações de ADRs passem por validação de compliance.
"""

from phantom.neotron.sentinel_integration import (
    PhantomSentinel,
    PhantomGuardrails,
    validate_recommendation,
)
from phantom.neotron.oracle_explainer import OracleExplainer

__all__ = [
    "PhantomSentinel",
    "PhantomGuardrails",
    "validate_recommendation",
    "OracleExplainer",
]
