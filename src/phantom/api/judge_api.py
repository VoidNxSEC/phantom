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
        """Inicializar Vector Store (lazy)"""
        try:
            from phantom.rag.cortex_embeddings import EmbeddingGenerator
            from phantom.rag.vectors import create_vector_store

            # Inicializar gerador de embeddings e vector store
            self.embedding_gen = EmbeddingGenerator()
            self.vector_store = create_vector_store(embedding_dim=384, backend="auto")

            # Carregar dados do Knowledge Base se disponível
            if self.knowledge_base_path and Path(self.knowledge_base_path).exists():
                with open(self.knowledge_base_path) as f:
                    kb_data = json.load(f)
                    decisions = kb_data.get("decisions", [])
                    if decisions:
                        texts = [
                            f"{d['title']} {d.get('summary', '')}" for d in decisions
                        ]
                        metadata = [
                            {"id": d["id"], "title": d["title"]} for d in decisions
                        ]

                        logger.info(f"Indexing {len(texts)} ADRs...")
                        embeddings = self.embedding_gen.encode(texts)
                        self.vector_store.add(embeddings, texts, metadata)

            logger.info("RAG Engine initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize RAG: {e}")
            self.vector_store = None

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

        # 3. Consultar knowledge base via RAG
        if getattr(self, "vector_store", None) and bundle.alerts:
            # Montar query semântica baseada nos alertas
            alert_messages = [a.message for a in bundle.alerts]
            query_text = f"System alerts: {', '.join(alert_messages)}"

            try:
                # Gerar embedding da query
                query_emb = self.embedding_gen.encode_single(query_text)

                # Buscar no Vector Store
                results = self.vector_store.search(query_emb, top_k=3)

                for result in results:
                    if result.score > 0.3:  # Threshold
                        meta = result.metadata
                        relevant_adrs.append(meta.get("id", "UNKNOWN"))
                        notes.append(
                            f"🧠 RAG Match ({result.score:.2f}): {meta.get('title', 'Untitled')}"
                        )

            except Exception as e:
                logger.error(f"RAG query failed: {e}")

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
