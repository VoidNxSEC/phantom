"""
Phantom NATS scanner — neoland pipeline outputs.

Assina ``neoland.pipeline.output.v1`` e roda análise de sentimento + extração
de padrões SPECTRE sobre os textos do pipeline multi-agent (hypothesis, rationale,
risk_assessment, etc.). Publica ``phantom.pipeline.scan.v1`` com os resultados.

Integração: Ciclo 1 — Fase D
"""

import asyncio
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("phantom.nats.neoland_scanner")

_subscription = None
_nc = None


async def start_scanner() -> None:
    """
    Conecta ao NATS e assina ``neoland.pipeline.output.v1``.

    Roda como background task no lifespan do FastAPI.
    Non-fatal se NATS não estiver disponível.
    """
    global _subscription, _nc
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nkey_seed = os.environ.get("NATS_NKEY_SEED", "").strip()
    nkey_seed_file = os.environ.get("NATS_NKEY_SEED_FILE", "").strip()
    ca_file = os.environ.get("NATS_CA_FILE", "").strip()
    cert_file = os.environ.get("NATS_CLIENT_CERT_FILE", "").strip()
    key_file = os.environ.get("NATS_CLIENT_KEY_FILE", "").strip()

    try:
        import nats

        kwargs: dict[str, Any] = {}
        if not nkey_seed and nkey_seed_file and os.path.exists(nkey_seed_file):
            with open(nkey_seed_file, encoding="utf-8") as fh:
                for line in fh:
                    candidate = line.strip()
                    if candidate and not candidate.startswith("#"):
                        nkey_seed = candidate
                        break
        if nkey_seed:
            kwargs["nkeys_seed_str"] = nkey_seed
        if nats_url.startswith("tls://") or ca_file or cert_file or key_file:
            import ssl
            tls_context = ssl.create_default_context(cafile=ca_file or None)
            if cert_file and key_file:
                tls_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
            kwargs["tls"] = tls_context

        _nc = await nats.connect(nats_url, **kwargs)
        _subscription = await _nc.subscribe(
            "neoland.pipeline.output.v1",
            cb=_handle_pipeline_output,
        )
        logger.info(
            "Phantom scanner subscribed to neoland.pipeline.output.v1 @ %s", nats_url
        )
        while True:
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.warning("Phantom neoland scanner failed (non-fatal): %s", exc)


async def stop_scanner() -> None:
    """Desassocia e drena a conexão."""
    global _subscription, _nc
    if _subscription is not None:
        try:
            await _subscription.unsubscribe()
        except Exception:
            pass
        _subscription = None
    if _nc is not None and not _nc.is_closed:
        try:
            await _nc.drain()
        except Exception:
            pass
        _nc = None


async def _handle_pipeline_output(msg) -> None:
    """Recebe neoland.pipeline.output.v1, analisa e publica phantom.pipeline.scan.v1."""
    try:
        raw = json.loads(msg.data.decode())

        # O envelope spectre-events envolve o payload em {"payload": {...}}
        payload = raw.get("payload", raw)

        session_id = payload.get("session_id", "unknown")
        task_id = payload.get("task_id", "unknown")
        decision = payload.get("decision", "unknown")

        logger.info(
            "Phantom scanner recebeu pipeline output: session=%s decision=%s",
            session_id,
            decision,
        )

        # Concatena todos os campos de texto para análise
        text_corpus = _build_corpus(payload)
        if not text_corpus.strip():
            logger.warning("Corpus vazio para session=%s — descartando", session_id)
            return

        scan_result = await asyncio.get_event_loop().run_in_executor(
            None, _run_analysis, text_corpus, payload
        )

        # Publica resultado do scan
        await _publish_scan(session_id, task_id, decision, scan_result)

    except Exception as exc:
        logger.error("Erro no handler neoland_scanner: %s", exc, exc_info=True)


def _build_corpus(payload: dict) -> str:
    """Concatena campos de texto do pipeline output."""
    parts = []
    for field in (
        "hypothesis",
        "refined_hypothesis",
        "risk_assessment",
        "rationale",
        "adr_title",
    ):
        val = payload.get(field, "")
        if val:
            parts.append(val)

    for list_field in ("junior_unknowns", "innovation_vectors", "action_items"):
        items = payload.get(list_field, [])
        if items:
            parts.extend(items)

    return "\n".join(parts)


def _run_analysis(text: str, payload: dict) -> dict:
    """
    Roda análise síncrona (executa em thread pool via run_in_executor).

    Usa SentimentEngine (NLTK VADER) — sem dependência de GPU ou LLM.
    Extrai métricas leves: sentimento, contagem de unknowns, score de risco.
    """
    result: dict[str, Any] = {
        "analyzed_at": datetime.now(UTC).isoformat(),
        "corpus_length": len(text),
    }

    # Sentimento via NLTK VADER (leve, sem deps externas além de nltk)
    try:
        from phantom.analysis.sentiment_analysis import SentimentEngine

        engine = SentimentEngine(use_spacy=False)
        sentiment = engine.analyze(text)
        result["sentiment"] = {
            "label": sentiment.label,
            "score": sentiment.score,
            "details": sentiment.details,
        }
    except Exception as exc:
        logger.warning("SentimentEngine falhou (non-fatal): %s", exc)
        result["sentiment"] = None

    # Métricas estruturais do pipeline
    unknowns = payload.get("junior_unknowns", [])
    action_items = payload.get("action_items", [])
    result["structural"] = {
        "unknowns_count": len(unknowns),
        "action_items_count": len(action_items),
        "has_innovation_vectors": bool(payload.get("innovation_vectors")),
        "risk_keywords": _extract_risk_keywords(text),
    }

    return result


def _extract_risk_keywords(text: str) -> list[str]:
    """Extrai palavras-chave de risco de forma leve (sem ML)."""
    risk_terms = [
        "breaking change", "migration", "deprecated", "security", "vulnerability",
        "performance", "latency", "memory", "leak", "race condition", "deadlock",
        "coupling", "dependency", "compatibility", "regression", "rollback",
    ]
    found = [term for term in risk_terms if term.lower() in text.lower()]
    return found


async def _publish_scan(
    session_id: str,
    task_id: str,
    decision: str,
    scan: dict,
) -> None:
    """Publica phantom.pipeline.scan.v1 via publisher singleton do Phantom."""
    try:
        from phantom.nats.publisher import publish_async

        await publish_async(
            "phantom.pipeline.scan.v1",
            {
                "session_id": session_id,
                "task_id": task_id,
                "decision": decision,
                "scan": scan,
                "source": "phantom-neoland-scanner",
            },
        )
        logger.info(
            "phantom.pipeline.scan.v1 publicado: session=%s sentiment=%s unknowns=%d",
            session_id,
            scan.get("sentiment", {}).get("label") if scan.get("sentiment") else "n/a",
            scan.get("structural", {}).get("unknowns_count", 0),
        )
    except Exception as exc:
        logger.warning("Falha ao publicar phantom.pipeline.scan.v1 (non-fatal): %s", exc)
