"""
PHANTOM-NEUTRON Integration Module

Integra Phantom Intelligence com Neutron Compliance Framework.
Garante que todas as recomendações de ADRs passem por validação de compliance.
"""

from phantom.neutron.sentinel_integration import (
    PhantomSentinel,
    PhantomGuardrails,
    validate_recommendation,
)
from phantom.neutron.oracle_explainer import OracleExplainer

__all__ = [
    "PhantomSentinel",
    "PhantomGuardrails",
    "validate_recommendation",
    "OracleExplainer",
]
