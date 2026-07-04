---
id: "2026-04-intelagent-merged-into-neoland"
type: "transition"
date: "2026-04-15"
title: "IntelAgent foi mergeado no Neoland; contrato com Phantom passou de HTTP para NATS"
repos_affected:
  - "intel-agent"
  - "neoland"
  - "phantom"
  - "phantom-nx"
tags:
  - "intelagent"
  - "neoland"
  - "merge"
  - "nats"
  - "dspy"
  - "architectural-consolidation"
supersedes_adrs:
  - "ADR-0054"
related_adrs:
  - "ADR-0017"
  - "ADR-0018"
  - "ADR-0019"
related_memories: []
---

# IntelAgent foi mergeado no Neoland

## O que aconteceu

O projeto `intel-agent` (Rust workspace standalone em `github.com/marcosfpina/intel-agent`) foi **absorvido pelo Neoland** (`~/suit/neoland`) ao longo de Abril/2026.

As peças funcionais do `intel-agent/crates/core` viraram features do Neoland:

| Em intel-agent (Abr 3, 2026)        | Em Neoland (v0.1.0 Beta hoje)                          |
|--------------------------------------|--------------------------------------------------------|
| `adr_agent.rs` (206 LOC)             | ADR Ledger (Merkle chain + secp256k1 signatures)       |
| `dspy.rs` (121 LOC)                  | Multi-agent DSPy pipeline (Junior→Senior→Architect→TechLeader) |
| `orchestrator.rs` (67 LOC)           | Pipeline orchestration (mesmo padrão DSPy)             |
| `llamacpp_agent.rs` (238 LOC)        | Provider local (parte do agents subsystem)             |
| `phantom_worker.rs` (223 LOC)        | **Substituído**: HTTP REST → NATS JetStream            |
| `cli/` + (`phantom-soc-kernel/soc/`) | TUI ratatui (Tokyo Night theme, async tokio::select!)  |
| `siem.rs` (31 LOC)                   | EDR rules (3 SIGMA + 6 YARA)                           |

## Contrato com Phantom

O contrato `intel-agent → Phantom` que era HTTP REST (`phantom_worker.rs` chamando `GET /health` + `POST /api/chat`) foi **substituído** por NATS pubsub bidirecional:

```
Neoland (publisher)  ──[NATS: neoland.pipeline.output.v1]──>  Phantom NATS scanner
                                                                      │
                                                                      ▼
                                                       SPECTRE + sentiment analysis
                                                                      │
                                                                      ▼
                                                       [NATS: phantom.pipeline.scan.v1]
                                                                      │
                                                                      ▼
                                                              Neoland (subscriber)
```

Implementação em Phantom:
- `src/phantom/nats/neoland_scanner.py` (227 LOC) — subscriber + handler
- Iniciado no lifespan do FastAPI (`src/phantom/api/app.py:134`)
- Não-fatal se NATS indisponível (`logger.warning`)

## Status de cada repo após o merge

| Repo                                  | Estado em Maio/2026                                      |
|---------------------------------------|----------------------------------------------------------|
| `~/github/intel-agent` (standalone)   | **Congelado** — 1 commit em Abril 3, sem evolução desde. |
| `~/github/phantom-nx/libs/phantom-soc-kernel` | **Congelado** — snapshot Mar 29, antes do merge.  |
| `~/suit/neoland`                      | **Vivo** — v0.1.0 Beta, 96/100 production readiness.     |
| `~/suit/phantom` (este repo)          | **Vivo** — integra Neoland via NATS scanner.             |

## O que NÃO entra mais

- ❌ Não há plano de reanimar `intel-agent` standalone — Neoland herdou as features e segue como linha viva.
- ❌ `phantom-nx/libs/phantom-soc-kernel` permanece como tombstone do experimento monorepo.
- ❌ Referências a `intelagent/` como subdiretório do Phantom (CLAUDE.md, RELEASE-v0.1.0.md, README.md, etc) são **vestígios desatualizados** — Phantom nunca teve `intelagent/` interno; a integração sempre foi via boundary externo (primeiro HTTP, agora NATS).

## Implicação para Phantom

Phantom é, por design, o **motor analítico (data plane)** do Neoland. Não é um produto standalone — é a peça de ML que processa o output do pipeline multi-agent. Todo trabalho futuro em Phantom deve ser avaliado por essa lente: melhora Phantom como data-plane do Neoland?

## Referências

- Git log `~/github/intel-agent`: commit `0c13a69` (2026-04-03), único e final.
- Git log `~/github/phantom-nx`: commit `d10d243` (2026-03-29), rename ADR-0054.
- Neoland README: `~/suit/neoland/README.md` (declara as features herdadas).
- Phantom NATS scanner: `~/suit/phantom/src/phantom/nats/neoland_scanner.py`.
- Auditoria que descobriu esta transição: `~/suit/phantom/PROJECT_STATE.md` + `ROADMAP_MAP.md`.
