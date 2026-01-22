#!/usr/bin/env python3
"""
JUDGE API - Endpoint para julgar bundles do AI-OS-Agent
"""

import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger("judge_api")

# ═══════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════


class CPUMetrics(BaseModel):
    usage_percent: float
    cores: list[float] = Field(default_factory=list)


class MemoryMetrics(BaseModel):
    total_bytes: int
    used_bytes: int
    usage_percent: float


class ThermalMetrics(BaseModel):
    max_temp_celsius: float
    avg_temp_celsius: float


class SystemMetrics(BaseModel):
    cpu: CPUMetrics
    memory: MemoryMetrics
    thermal: ThermalMetrics


class Alert(BaseModel):
    timestamp: int
    severity: str  # "Info", "Warning", "Critical"
    category: str  # "Thermal", "Memory", "Disk", etc.
    message: str
    details: str | None = None


class LogEntry(BaseModel):
    timestamp: int
    priority: str
    unit: str | None = None
    message: str


class PhantomGateBundle(BaseModel):
    timestamp: int
    hostname: str | None = None
    metrics: SystemMetrics
    alerts: list[Alert]
    logs: list[LogEntry]


class PhantomGateResponse(BaseModel):
    severity: str  # "info", "warning", "critical"
    insights: list[str]
    relevant_adrs: list[str]
    recommendations: list[str]
    bundle_file: str
    bundle_dir: str = "/tmp/phantom-bundles"
    notes: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# STORAGE
# ═══════════════════════════════════════════════════════════════

BUNDLE_DIR = Path("/tmp/phantom-bundles")
BUNDLE_DIR.mkdir(parents=True, exist_ok=True)


def save_bundle(bundle: PhantomGateBundle) -> str:
    """Salvar bundle localmente"""
    filename = f"bundle-{bundle.timestamp}.json"
    filepath = BUNDLE_DIR / filename

    with open(filepath, "w") as f:
        json.dump(bundle.dict(), f, indent=2)

    logger.info(f"Bundle saved: {filepath}")
    return str(filepath)


# ═══════════════════════════════════════════════════════════════
# ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════


class JudgmentEngine:
    """Engine para julgar bundles baseado em métricas e knowledge base"""

    def __init__(self, knowledge_base_path: str | None = None):
        self.knowledge_base_path = knowledge_base_path
        self.cerebro_rag = None

        # Tentar inicializar Cerebro RAG
        if knowledge_base_path:
            self._init_cerebro_rag()

    def _init_cerebro_rag(self) -> None:
        """Inicializar Cerebro RAG (lazy)"""
        try:
            from phantom.cerebro import CerebroRAG

            cache_path = "/tmp/cerebro-faiss-index"
            kb_path = self.knowledge_base_path or ""
            self.cerebro_rag = CerebroRAG(  # type: ignore[assignment]
                knowledge_base_path=kb_path,
                index_cache_path=cache_path,
            )

            # Lazy initialization - será inicializado no primeiro query
            logger.info("Cerebro RAG configured (lazy initialization)")

        except Exception as e:
            logger.warning(f"Failed to initialize Cerebro RAG: {e}")
            self.cerebro_rag = None

    def judge(self, bundle: PhantomGateBundle) -> PhantomGateResponse:
        """Julgar bundle e retornar análise"""

        insights: list[str] = []
        recommendations: list[str] = []
        relevant_adrs: list[str] = []
        severity = "info"
        notes: list[str] = []

        # 1. Análise de métricas
        if bundle.metrics.thermal.max_temp_celsius > 75:
            severity = "warning"
            insights.append(
                f"Temperatura elevada detectada: {bundle.metrics.thermal.max_temp_celsius:.1f}°C"
            )
            recommendations.append("Verificar ventilação do sistema")
            recommendations.append("Considerar reduzir carga de trabalho")

        if bundle.metrics.memory.usage_percent > 85:
            severity = "warning" if severity == "info" else severity
            insights.append(
                f"Uso de memória crítico: {bundle.metrics.memory.usage_percent:.1f}%"
            )
            recommendations.append("Identificar processos com alto consumo de memória")
            recommendations.append("Considerar aumentar swap ou RAM")

        if bundle.metrics.cpu.usage_percent > 90:
            severity = "warning" if severity == "info" else severity
            insights.append(
                f"CPU em uso intenso: {bundle.metrics.cpu.usage_percent:.1f}%"
            )
            recommendations.append("Revisar processos em execução")

        # 2. Análise de alertas
        critical_alerts = [a for a in bundle.alerts if a.severity == "Critical"]
        if critical_alerts:
            severity = "critical"
            insights.append(f"{len(critical_alerts)} alertas críticos detectados")

        # 3. Consultar knowledge base via Cerebro RAG
        if self.cerebro_rag and bundle.alerts:
            # Montar query semântica baseada nos alertas
            alert_messages = [a.message for a in bundle.alerts]
            alert_categories = [a.category for a in bundle.alerts]

            query_parts = [
                f"System alerts: {', '.join(alert_messages)}",
                f"Categories: {', '.join(alert_categories)}",
                f"CPU usage: {bundle.metrics.cpu.usage_percent:.1f}%",
                f"Memory usage: {bundle.metrics.memory.usage_percent:.1f}%",
                f"Temperature: {bundle.metrics.thermal.max_temp_celsius:.1f}°C",
            ]

            query_text = " | ".join(query_parts)

            try:
                # Query RAG com Cerebro
                rag_results = self.cerebro_rag.query(
                    query_text=query_text,
                    top_k=5,
                    min_score=0.5,
                )

                for result in rag_results:
                    relevant_adrs.append(result["id"])
                    notes.append(
                        f"🧠 Cerebro ({result['score']:.2f}): "
                        f"{result['id']} - {result['title']}"
                    )

                    # Adicionar recomendações das ADRs
                    metadata = result.get("metadata", {})
                    # TODO: Extrair recommendations das ADRs

            except Exception as e:
                logger.error(f"Cerebro RAG query failed: {e}")
                # Fallback: continuar sem RAG

        # 4. Salvar bundle
        bundle_file = save_bundle(bundle)

        return PhantomGateResponse(
            severity=severity,
            insights=insights,
            relevant_adrs=list(set(relevant_adrs))[:5],  # Top 5
            recommendations=recommendations,
            bundle_file=bundle_file,
            bundle_dir=str(BUNDLE_DIR),
            notes=notes,
        )


# ═══════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════

_judgment_engine: JudgmentEngine | None = None


def get_judgment_engine() -> JudgmentEngine:
    """Get singleton judgment engine"""
    global _judgment_engine

    if _judgment_engine is None:
        # Tentar localizar knowledge base do ADR-Ledger
        kb_path = "/home/kernelcore/arch/adr-ledger/knowledge/knowledge_base.json"
        _judgment_engine = JudgmentEngine(knowledge_base_path=kb_path)

    return _judgment_engine
