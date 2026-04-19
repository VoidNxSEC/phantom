#!/usr/bin/env python3
"""
ORACLE Explainer - Explainability para recomendações de ADRs

Gera explicações humanas claras sobre porque um ADR foi recomendado.
Atende LGPD Art. 18 (direito à explicação) e AI Act transparency requirements.

Workflow:
1. Recebe bundle de métricas + ADRs recomendados
2. Gera explicação estruturada de cada recomendação
3. Rastreia evidências que levaram à recomendação
4. Formata explicação em linguagem natural
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("phantom.neotron.oracle")


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class Evidence:
    """Evidência que levou a uma recomendação"""
    metric_name: str
    value: float
    threshold: float
    severity: str  # "info", "warning", "critical"


@dataclass
class ADRExplanation:
    """Explicação estruturada de uma recomendação de ADR"""
    adr_id: str
    adr_title: str
    match_score: float
    evidences: list[Evidence]
    explanation: str  # Explicação em linguagem natural
    confidence: float  # 0-1


# =============================================================================
# Oracle Explainer Engine
# =============================================================================

class OracleExplainer:
    """
    ORACLE engine para gerar explicações de ADRs

    Transforma dados técnicos (métricas, scores) em explicações
    humanas compreensíveis.
    """

    def __init__(self):
        logger.info("OracleExplainer initialized")

    def explain_recommendation(
        self,
        adr_id: str,
        adr_title: str,
        match_score: float,
        metrics: dict[str, Any],
        alerts: list[dict[str, Any]] | None = None,
    ) -> ADRExplanation:
        """
        Gera explicação para uma recomendação de ADR

        Args:
            adr_id: ID do ADR (ex: "ADR-0023")
            adr_title: Título do ADR
            match_score: Score de similaridade (0-1)
            metrics: Métricas do sistema que levaram à recomendação
            alerts: Alertas ativos

        Returns:
            ADRExplanation com explicação estruturada
        """

        # Coletar evidências
        evidences = self._extract_evidences(metrics, alerts or [])

        # Gerar explicação em linguagem natural
        explanation = self._generate_natural_explanation(
            adr_id, adr_title, match_score, evidences
        )

        # Calcular confidence baseado em evidências
        confidence = self._calculate_confidence(match_score, evidences)

        return ADRExplanation(
            adr_id=adr_id,
            adr_title=adr_title,
            match_score=match_score,
            evidences=evidences,
            explanation=explanation,
            confidence=confidence,
        )

    def _extract_evidences(
        self,
        metrics: dict[str, Any],
        alerts: list[dict[str, Any]]
    ) -> list[Evidence]:
        """Extrai evidências das métricas e alertas"""
        evidences: list[Evidence] = []

        # Evidências de thermal
        if "thermal" in metrics:
            thermal = metrics["thermal"]
            max_temp = thermal.get("max_temp_celsius", 0)

            if max_temp > 85:
                evidences.append(Evidence(
                    metric_name="temperature",
                    value=max_temp,
                    threshold=85.0,
                    severity="critical"
                ))
            elif max_temp > 75:
                evidences.append(Evidence(
                    metric_name="temperature",
                    value=max_temp,
                    threshold=75.0,
                    severity="warning"
                ))

        # Evidências de memória
        if "memory" in metrics:
            memory = metrics["memory"]
            usage_percent = memory.get("usage_percent", 0)

            if usage_percent > 90:
                evidences.append(Evidence(
                    metric_name="memory_usage",
                    value=usage_percent,
                    threshold=90.0,
                    severity="critical"
                ))
            elif usage_percent > 85:
                evidences.append(Evidence(
                    metric_name="memory_usage",
                    value=usage_percent,
                    threshold=85.0,
                    severity="warning"
                ))

        # Evidências de CPU
        if "cpu" in metrics:
            cpu = metrics["cpu"]
            cpu_usage = cpu.get("usage_percent", 0)

            if cpu_usage > 95:
                evidences.append(Evidence(
                    metric_name="cpu_usage",
                    value=cpu_usage,
                    threshold=95.0,
                    severity="critical"
                ))
            elif cpu_usage > 90:
                evidences.append(Evidence(
                    metric_name="cpu_usage",
                    value=cpu_usage,
                    threshold=90.0,
                    severity="warning"
                ))

        # Evidências de alertas
        for alert in alerts:
            if alert.get("severity") == "Critical":
                evidences.append(Evidence(
                    metric_name=f"alert_{alert.get('category', 'unknown')}",
                    value=1.0,
                    threshold=0.0,
                    severity="critical"
                ))

        return evidences

    def _generate_natural_explanation(
        self,
        adr_id: str,
        adr_title: str,
        match_score: float,
        evidences: list[Evidence],
    ) -> str:
        """
        Gera explicação em linguagem natural

        Formato:
        "O {ADR_ID} '{ADR_TITLE}' foi recomendado (score: X.XX) porque:
        - Evidência 1
        - Evidência 2
        Este ADR é relevante para resolver esses problemas."
        """

        lines = [
            f"O {adr_id} '{adr_title}' foi recomendado com score de similaridade {match_score:.2f} porque:"
        ]

        # Adicionar evidências
        if evidences:
            for evidence in evidences:
                lines.append(
                    f"  - {self._format_evidence(evidence)}"
                )
        else:
            lines.append("  - Similaridade semântica com o contexto atual")

        # Conclusão
        lines.append(
            f"\nEste ADR contém decisões arquiteturais relevantes para resolver "
            f"{'esse problema' if len(evidences) == 1 else 'esses problemas'}."
        )

        return "\n".join(lines)

    def _format_evidence(self, evidence: Evidence) -> str:
        """Formata uma evidência em texto legível"""

        formats = {
            "temperature": f"Temperatura em {evidence.value:.1f}°C (threshold: {evidence.threshold:.1f}°C)",
            "memory_usage": f"Uso de memória em {evidence.value:.1f}% (threshold: {evidence.threshold:.1f}%)",
            "cpu_usage": f"Uso de CPU em {evidence.value:.1f}% (threshold: {evidence.threshold:.1f}%)",
        }

        if evidence.metric_name in formats:
            return formats[evidence.metric_name]

        # Alertas
        if evidence.metric_name.startswith("alert_"):
            category = evidence.metric_name.replace("alert_", "")
            return f"Alerta crítico: {category}"

        # Fallback genérico
        return f"{evidence.metric_name}: {evidence.value} (threshold: {evidence.threshold})"

    def _calculate_confidence(
        self,
        match_score: float,
        evidences: list[Evidence]
    ) -> float:
        """
        Calcula confidence score da explicação

        Fatores:
        - Match score do RAG
        - Número de evidências
        - Severidade das evidências
        """

        # Base: match score
        confidence = match_score

        # Bonus por evidências
        if evidences:
            evidence_bonus = min(0.2, len(evidences) * 0.05)
            confidence += evidence_bonus

            # Bonus por evidências críticas
            critical_count = sum(1 for e in evidences if e.severity == "critical")
            if critical_count > 0:
                confidence += min(0.1, critical_count * 0.05)

        # Normalizar para [0, 1]
        return min(1.0, confidence)

    def explain_multiple(
        self,
        recommendations: list[dict[str, Any]],
        metrics: dict[str, Any],
        alerts: list[dict[str, Any]] | None = None,
    ) -> list[ADRExplanation]:
        """
        Gera explicações para múltiplas recomendações

        Args:
            recommendations: Lista de dicts com {id, title, score}
            metrics: Métricas do sistema
            alerts: Alertas ativos

        Returns:
            Lista de ADRExplanation
        """
        explanations = []

        for rec in recommendations:
            explanation = self.explain_recommendation(
                adr_id=rec.get("id", "UNKNOWN"),
                adr_title=rec.get("title", "Untitled"),
                match_score=rec.get("score", 0.0),
                metrics=metrics,
                alerts=alerts,
            )
            explanations.append(explanation)

        return explanations


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("ORACLE EXPLAINER - ADR Explainability")
    print("=" * 60)

    oracle = OracleExplainer()

    # Mock data
    metrics = {
        "cpu": {"usage_percent": 92.5},
        "memory": {"usage_percent": 87.3},
        "thermal": {"max_temp_celsius": 82.0, "avg_temp_celsius": 76.5}
    }

    alerts = [
        {"severity": "Critical", "category": "Thermal", "message": "High temperature"}
    ]

    # Test single explanation
    print("\n[TEST] Explicação de ADR único:")
    explanation = oracle.explain_recommendation(
        adr_id="ADR-0023",
        adr_title="Thermal Management and Monitoring Strategy",
        match_score=0.89,
        metrics=metrics,
        alerts=alerts
    )

    print(f"\n{explanation.explanation}")
    print(f"\nConfidence: {explanation.confidence:.2f}")
    print(f"Evidências: {len(explanation.evidences)}")

    # Test multiple
    print("\n" + "=" * 60)
    print("[TEST] Múltiplas recomendações:")

    recommendations = [
        {"id": "ADR-0023", "title": "Thermal Management", "score": 0.89},
        {"id": "ADR-0011", "title": "Memory Optimization", "score": 0.76},
    ]

    explanations = oracle.explain_multiple(recommendations, metrics, alerts)

    for exp in explanations:
        print(f"\n{exp.adr_id} (confidence: {exp.confidence:.2f}):")
        print(f"  {exp.explanation[:100]}...")

    print("\n" + "=" * 60)
