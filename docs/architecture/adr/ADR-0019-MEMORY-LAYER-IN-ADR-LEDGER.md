---
id: "ADR-0019"
title: "Memory Layer in adr-ledger — Lightweight Tracking of Architectural Transitions"
status: proposed
date: "2026-05-14"

authors:
  - name: "kernelcore"
    role: "Project Lead"
    github: "marcosfpina"
  - name: "Claude (opus-4.7)"
    role: "Drafting agent"
    github: "anthropics/claude-code"

reviewers: []

governance:
  classification: "minor"
  requires_approval_from:
    - architect
  compliance_tags: ["knowledge-management", "adr-ledger", "cerebro", "rag"]
  review_deadline: "2026-05-28"
  auto_supersede_after: "1y"

scope:
  projects:
    - PHANTOM
    - ADR-LEDGER
  layers:
    - knowledge
    - infrastructure
  environments:
    - development
    - staging
    - production

rationale:
  drivers:
    - "ADRs ficaram órfãs de continuidade: ADR-0017 (monorepo) e ADR-0018 (sprint backlog) descrevem planos que mudaram em silêncio. Sem registro intermediário, qualquer leitor reconstrói história errada."
    - "3 tentativas de consolidação (phantom-nx, phantom-soc, intel-agent standalone) morreram entre Janeiro e Abril de 2026 sem ADR de superseding. O merge intel-agent → Neoland nunca foi formalizado."
    - "Custo de ADR (deadline, reviewers, classificação major) é alto demais para registrar transições já consumadas; mas a alternativa atual (zero registro) gera 159+ referências fantasma nas docs."
    - "Cerebro RAG (FAISS + sentence-transformers) já indexa ADRs via ADRKnowledgeLoader. Extensão simétrica para memórias é incremental, não disruptiva."
  alternatives_considered:
    - "Rejeitado — Criar ADRs retroativos para cada transição: alto custo, baixo valor (decisão já vivida)."
    - "Rejeitado — Manter status quo (zero registro de transições): provou-se insuficiente; gera retrabalho cognitivo a cada onboarding de pessoa ou agente."
    - "Rejeitado — Usar git log como único registro: granularidade errada (commit message não captura motivação arquitetural)."
    - "Rejeitado — Wiki externa: fragmenta o ledger; perde signing/Merkle do adr-ledger."
  trade_offs:
    - "Custo baixo de entrada (sem aprovação formal) vs risco de virar lixeira de notas: mitigado por convenção de naming + INDEX.md obrigatório + frontmatter validado."
    - "Memórias podem conflitar com ADRs se mal disciplinadas: mitigado por regra explícita (memory = fato consumado, ADR = decisão em movimento)."

consequences:
  positive:
    - "Continuidade narrativa restaurada: leitor que cai num ADR antigo vê referência a memory mais nova que descreve o que aconteceu desde."
    - "Cerebro RAG ganha um corpus complementar: queries arquiteturais (`o que aconteceu com intel-agent?`) retornam resposta correta."
    - "Custo marginal de registrar uma transição cai drasticamente — entrada de markdown com frontmatter, 5-15 minutos de redação."
    - "Agentes (humanos e LLMs) chegando ao projeto têm fonte autoritativa de história arquitetural recente."
  negative:
    - "Mais um padrão para manter: requer disciplina inicial até virar hábito."
    - "Cerebro precisa de extensão (MemoryKnowledgeLoader): código novo, ~80-100 LOC + testes."
  risks:
    - "Memórias podem ser escritas com viés/incompletas: mitigação pelo formato curto (forced concision) e por estarem versionadas via git."
    - "Sobreposição com adr-ledger Merkle chain: decidir se memórias entram no chain (assinadas) ou ficam fora. Recomendação: ficar fora no MVP, entrar depois se valor for confirmado."

implementation:
  effort: "small"
  timeline: "1 semana"
  dependencies:
    - "pyyaml (já em pyproject.toml)"
    - "sentence-transformers (já em uso por cerebro)"
    - "faiss-cpu (já em uso por cerebro)"
  blocked_by: []
  tasks:
    - "T1: Criar diretório `memory/` no adr-ledger (ou neste repo enquanto adr-ledger não absorve)"
    - "T2: Implementar `src/phantom/cerebro/memory_loader.py` com MemoryDocument + MemoryKnowledgeLoader"
    - "T3: Estender CerebroRAG para indexar dois corpora (ADR + Memory) com índices FAISS separados"
    - "T4: Adicionar parâmetro `corpus={'adr','memory','both'}` na API `/api/chat` (cerebro RAG)"
    - "T5: Documentar convenção de naming (`YYYY-MM-<slug>.md`) e schema do frontmatter"
    - "T6: Migrar conhecimento implícito desta sessão (intelagent→neoland, monorepo paused, etc) para entradas iniciais"

audit:
  created_at: "2026-05-14T22:00:00Z"
  last_modified: "2026-05-14T22:00:00Z"
  version: 1
---

# ADR-0019: Memory Layer in adr-ledger — Lightweight Tracking of Architectural Transitions

## Context

A revisão arqueológica de Maio/2026 (em `~/suit/phantom/PROJECT_STATE.md` e `ROADMAP_MAP.md`) expôs um padrão recorrente: decisões formais (ADRs) são registradas, mas **transições subsequentes** entre elas não são. Resultado: a doc do Phantom contém 159+ referências a `intelagent/` como se fosse subdiretório, quando na verdade:

1. **Janeiro 2026** — `intel-agent` foi criado como crate dentro de `phantom-nx/libs/intelagent` (commit `6a38e6d`).
2. **Março 29, 2026** — `intel-agent` foi renomeado para `phantom-soc-kernel` no monorepo (commit `d10d243`, referencia ADR-0054).
3. **Abril 3, 2026** — `intel-agent` foi extraído como repo standalone (`github.com/marcosfpina/intel-agent`), com 1.649 LOC no core (adr_agent, dspy, llamacpp_agent, orchestrator, phantom_worker, siem).
4. **Abril–Maio 2026** — `intel-agent` foi **mergeado no Neoland** (`~/suit/neoland`). Suas peças viraram: ADR Ledger (de `adr_agent.rs`), Multi-agent DSPy pipeline (de `dspy.rs` + `orchestrator.rs`), TUI ratatui (de `cli/` + `soc/`). Contrato com Phantom passou de HTTP REST (`phantom_worker.rs`) para NATS pubsub (`neoland.pipeline.output.v1`).

Nenhuma dessas 4 transições virou ADR. Não deveriam ter virado — eram fatos consumados, não decisões em deliberação. Mas a ausência de **qualquer** registro lightweight fez com que cada onboarding (humano ou LLM) tivesse que reconstruir a história por inferência sobre código + git log, com alta taxa de erro.

## Decision

Introduzir um **Memory Layer** no adr-ledger, paralelo ao diretório `adr/`, com a seguinte estrutura:

```
adr-ledger/
├── adr/                            # ADRs (já existe)
│   ├── ADR-0017-CONSOLIDACAO-MONOREPO.md
│   ├── ADR-0018-SPRINT-REMAINING-WORK.md
│   └── ADR-0019-MEMORY-LAYER-IN-ADR-LEDGER.md (este)
└── memory/                          # Memory Layer (novo)
    ├── INDEX.md                     # Um-liner por entrada, ordem cronológica reversa
    ├── transitions/                 # "X virou Y", "X foi mergeado em Y"
    │   ├── 2026-04-intelagent-merged-into-neoland.md
    │   ├── 2026-03-monorepo-attempts-paused.md
    │   └── 2026-03-cortex-api-split-from-app.md
    ├── integrations/                # Contratos vivos entre repos
    │   ├── phantom-neoland-nats.md
    │   └── phantom-aios-judge.md
    └── learnings/                   # Aprendizados generalizáveis
        └── monorepo-cost-too-high-2026.md
```

### Schema do frontmatter de memory

```yaml
---
id: "2026-04-intelagent-merged-into-neoland"      # filename-derived
type: "transition"                                 # transition | integration | learning
date: "2026-04-15"                                 # ISO 8601
title: "IntelAgent mergeado no Neoland"
repos_affected:
  - "intel-agent"
  - "neoland"
  - "phantom"
tags: ["intelagent", "neoland", "merge", "nats"]
supersedes_adrs: ["ADR-0054"]                      # opcional
related_adrs: ["ADR-0017", "ADR-0018"]             # opcional
related_memories: []                                # opcional
---

# Título humano

Corpo curto e factual (10-50 linhas). O que aconteceu, onde o código foi parar,
quais contratos mudaram. SEM justificar — justificativa fica nos ADRs originais.
```

### Regra de uso

| Situação                                                           | Usar    |
|---------------------------------------------------------------------|---------|
| Decisão sendo tomada agora, com alternativas em deliberação        | **ADR** |
| Decisão pendente, com prazo de revisão e classificação             | **ADR** |
| Fato consumado, transição completada, integração ativa             | **Memory** |
| Aprendizado generalizável depois de um experimento                 | **Memory** |
| Conflito de contrato detectado entre repos                         | **Memory** + ADR de resolução se aplicável |

### Diferença prática ADR vs Memory

| Aspecto             | ADR                                  | Memory                            |
|---------------------|--------------------------------------|-----------------------------------|
| Workflow            | proposed → accepted → superseded     | Inerte (registro)                 |
| Aprovação           | Sim (architect+)                     | Não                               |
| Classification      | major/moderate/minor                 | type: transition/integration/learning |
| Merkle/secp256k1    | Sim (do adr-ledger)                  | Fora do chain (MVP); revisitar depois |
| Custo de redação    | 1-3 horas                            | 5-15 minutos                      |
| Tamanho típico      | 200-800 linhas                       | 10-50 linhas                      |

### Extensão do Cerebro RAG

O `CerebroRAG` será estendido para indexar dois corpora separadamente:

```python
adr_results = cerebro.search(query, corpus="adr", top_k=3)
mem_results = cerebro.search(query, corpus="memory", top_k=5)
combined = cerebro.search(query, corpus="both", top_k=8, recency_weight={"adr": 0.1, "memory": 0.4})
```

Decisões técnicas para a extensão:
- **Índices FAISS separados**: simplifica filtros de metadata e permite recency weighting diferente por corpus.
- **Mesmo embedder** (`all-MiniLM-L6-v2`): texto curto é onde o MiniLM brilha; sem motivo para divergir no MVP.
- **Chunking**: memórias são whole-doc (não chunked); ADRs continuam como hoje.

## Implementation tasks

Ver bloco `implementation.tasks` no frontmatter. Resumo:

- **T1** — Estrutura de diretórios em adr-ledger (ou neste repo provisoriamente)
- **T2** — `memory_loader.py` no cerebro
- **T3** — Extensão `CerebroRAG` para dual-corpus
- **T4** — Parâmetro `corpus` em `/api/chat`
- **T5** — Docs de convenção (naming + schema)
- **T6** — Migração inicial: pelo menos as 4 transições mapeadas neste ADR viram memory entries

## References

- `PROJECT_STATE.md` — Auditoria de Maio/2026 que originou esta ADR
- `ROADMAP_MAP.md` — Mapa completo do roadmap reconciliado com realidade
- `src/phantom/cerebro/knowledge_loader.py` — Padrão a espelhar
- `src/phantom/cerebro/rag_engine.py` — Onde a extensão dual-corpus entra
- ADR-0017 — Tentativa de consolidação monorepo (pausada, sem superseding formal)
- ADR-0018 — Sprint backlog que assumia IntelAgent como subdir do Phantom (obsoleto após o merge no Neoland)
