# PHANTOM — Project State (verified)

> Snapshot ponta-a-ponta do repositório em **2026-05-14**.
> Auditado direto do código (não a partir de docs). Os docs mais antigos (`CLAUDE.md`, `IMPLEMENTATION_STATUS.md`, `ADR-0018`) **divergem da realidade** em pontos importantes — esses descompassos estão explicitados na seção [Descompassos](#descompassos-doc--código).

---

## 1. Resumo executivo (5 linhas)

- **Backend Python** está feature-complete: 17 endpoints REST + 11 comandos CLI funcionando, todos com Pydantic e logging estruturado.
- **Frontend** já foi decomposto em componentes por tab (CLAUDE.md/ADR-0018 ainda afirmam que é monolítico — está desatualizado).
- **Diretório `intelagent/` (Rust agent) NÃO EXISTE no working tree** — toda a referência a ele em docs é fictícia. O único Rust real é a shim do Tauri (~23 LOC).
- **`main` está atrás de `origin/dev`** por 6 commits, incluindo providers cloud (Anthropic + DeepSeek) e separação cortex-api / main-api.
- **CI não roda testes Python** — todos os 8 workflows são Nix (build/check/fmt/release/security/maintenance). `pytest` só roda local.

---

## 2. Topologia do repositório

```
phantom/
├── src/phantom/              # 13.470 LOC Python, 37 arquivos
│   ├── api/                  # 3 FastAPI apps separados (não compostos)
│   │   ├── app.py            # 1.063 LOC — API principal (17 endpoints)
│   │   ├── cortex_api.py     #   527 LOC — FastAPI standalone p/ Cortex Desktop
│   │   └── judge_api.py      #   360 LOC — bibliotecário Neotron (sem FastAPI próprio)
│   ├── core/                 # cortex.py (783), embeddings.py (130), metrics_schema.py (450)
│   ├── rag/                  # vectors.py (483), cortex_chunker.py (432), cortex_embeddings.py (464)
│   ├── analysis/             # spectre.py (2.265), viability_scorer.py (864), ai_analyzer.py (794),
│   │                         #   latency_optimizer.py (216), sentiment_analysis.py (152)
│   ├── pipeline/             # phantom_dag.py (1.666) — DAG orchestrator
│   ├── providers/            # base.py + llamacpp.py SOMENTE (cloud providers só no branch dev)
│   ├── nats/                 # publisher (101), consumer (127), neoland_scanner (227)
│   ├── cerebro/              # rag_engine (274), knowledge_loader (183)
│   ├── neotron/              # sentinel_integration (427), oracle_explainer (356)
│   └── cli/main.py           # 484 LOC — Typer (11 comandos funcionais)
├── cortex-desktop/           # Tauri 2 + SvelteKit + Svelte 5
│   ├── src/                  # 1.537 LOC TS/Svelte
│   └── src-tauri/            # 23 LOC Rust (shim só)
├── tests/                    # 26 arquivos, 5.677 LOC
│   ├── unit/                 # 21 arquivos
│   ├── integration/          # 3 arquivos (test_api, test_api_endpoints, test_cli)
│   └── e2e/                  # 1 arquivo (test_full_pipeline)
├── docs/                     # 29 docs em architecture/, development/, guides/, history/, reference/
├── .github/workflows/        # 8 workflows (todos Nix-centric — ver §8)
├── nix/                      # módulos NixOS
└── flake.nix, justfile, pyproject.toml
```

---

## 3. Backend — Endpoints REST (api/app.py)

Todos respondem em `phantom api serve` (default `:8008`). Padrão: handlers definidos dentro de `create_app()`.

| Método | Path                    | Linha    | O que faz                                                                  |
|--------|-------------------------|----------|----------------------------------------------------------------------------|
| GET    | `/health`               | 188      | Liveness                                                                   |
| GET    | `/ready`                | 193      | Readiness + checagem do SecureLLM bridge em `SECURELLM_BRIDGE_URL`         |
| GET    | `/metrics`              | 226      | Prometheus                                                                 |
| GET    | `/api/system/metrics`   | 231      | CPU/RAM/disk/VRAM em tempo real via psutil + helper de cortex              |
| POST   | `/extract`              | 311      | Extrai insights de markdown via CORTEX                                     |
| POST   | `/process`              | 363      | Pipeline completo de processamento + chunking                              |
| POST   | `/upload`               | 418      | Upload single-file                                                         |
| POST   | `/api/upload`           | 431      | Upload batch                                                               |
| POST   | `/vectors/search`       | 471      | FAISS dense/sparse/hybrid                                                  |
| POST   | `/vectors/index`        | 538      | Indexa documento individual                                                |
| POST   | `/vectors/batch-index`  | 594      | Indexação em lote                                                          |
| POST   | `/api/chat`             | 640      | RAG chat (não-streaming)                                                   |
| GET    | `/api/models`           | 715      | Lista modelos disponíveis                                                  |
| POST   | `/api/prompt/test`      | 745      | Renderiza template + conta tokens                                          |
| POST   | `/api/chat/stream`      | 783      | Streaming via SSE (LlamaCpp streaming real)                                |
| POST   | `/api/pipeline`         | 872      | Executa DAG de classificação                                               |
| POST   | `/api/pipeline/scan`    | 954      | Scan de diretório sem mover arquivos                                       |
| GET    | `/rag/query`            | 1008     | Legacy redirect → `/api/chat`                                              |
| POST   | `/judge`                | 1024     | Julgamento de bundles AI-OS-Agent via Neotron (Sentinel + Oracle)          |

### APIs paralelas (não compostas em `app.py`)

`api/__init__.py` exporta apenas `create_app`/`app` de `app.py`. **`cortex_api.py` e `judge_api.py` não são `APIRouter`** — são FastAPI apps standalone que precisariam ser iniciados separadamente, OU integrados com `app.include_router(...)`. Hoje vivem isolados:

- **`cortex_api.py`** (527 LOC): FastAPI completo (próprio CORS, próprios endpoints) expondo CortexProcessor + SpectreAnalyzer. Provavelmente uma versão alternativa do `app.py` para o desktop — possível dead-code ou duplicação não consolidada.
- **`judge_api.py`** (360 LOC): apesar do nome "API", é um módulo de Pydantic models + lógica auxiliar para o endpoint `/judge` (importado em `app.py`). Não tem FastAPI próprio.

> **Ação sugerida**: decidir entre (a) deletar `cortex_api.py` se for dead-code, ou (b) converter para `APIRouter` e fazer `include_router`. Hoje está num limbo.

---

## 4. Backend — CLI (cli/main.py, Typer)

```
phantom extract -i <dir> -o <output>     # extrai insights de markdown
phantom analyze <file>                    # análise full c/ sentimento
phantom classify <dir>                    # classifica arquivos
phantom scan <dir>                        # scan sensitive data
phantom rag query <pergunta>              # RAG query
phantom rag ingest <dir>                  # ingest p/ RAG
phantom tools vram                        # monitor CPU/RAM/VRAM
phantom tools prompt                      # workbench interativo
phantom tools audit <dir>                 # auditoria com classificações
phantom api serve                         # sobe servidor REST
phantom version                           # versão
```

Todos os 11 comandos têm implementação real (não são stubs). Verificado em `cli/main.py:30-484`.

---

## 5. Frontend (cortex-desktop)

**Stack**: Tauri 2.0 + SvelteKit + Svelte 5 (runes `$state`/`$effect`) + Tailwind.

**Estrutura atual**:
```
src/
├── routes/+page.svelte           #  38 LOC — só monta tabs (decomposto!)
├── routes/+layout.svelte         #  77 LOC
├── routes/process/+page.svelte   # 219 LOC (rota dedicada)
├── lib/api.ts                    #  89 LOC — cliente fetch
├── lib/state.svelte.ts           # 320 LOC — stores reativos
├── lib/components/Sidebar.svelte
└── lib/components/tabs/
    ├── ChatTab.svelte            # 108 LOC
    ├── ProcessTab.svelte         # 126 LOC
    ├── SearchTab.svelte          #  84 LOC
    ├── WorkbenchTab.svelte       # 149 LOC
    ├── LibraryTab.svelte         #  86 LOC
    └── SettingsTab.svelte        # 171 LOC
```

**O monolito de 1.193 LOC descrito no ADR-0018 P1 não existe mais** — a decomposição foi feita. Mas:
- ❌ Não há `SystemMonitor.svelte` (CPU/RAM/VRAM em tempo real)
- ❌ Não há `ErrorToast.svelte`
- ❌ Não há `MessageBubble.svelte` / `FileUploader.svelte` (lógica ainda inline nos tabs)
- ❌ **Zero testes frontend** (sem Vitest, sem Playwright, sem `@testing-library/svelte`)

**Tauri Rust** (`src-tauri/src/`): `main.rs` 6 LOC, `lib.rs` 14 LOC, `build.rs` 3 LOC. É só a shim oficial — nenhuma lógica de IPC custom.

---

## 6. Tests

| Nível       | Arquivos | LOC   | Cobertura alvo |
|-------------|----------|-------|----------------|
| Unit        | 21       | 4.605 | 70%+ enforced  |
| Integration | 3        | 808   | —              |
| E2E         | 1        | 64    | mínimo         |
| Imports     | 1        | 181   | smoke          |
| **Total**   | **26**   | **5.677** | —          |

Tudo bate com `pytest.ini` (70% mínimo). `tests/validate_just.py` valida o justfile. **Não rodei `just test` neste sessão** — pode haver regressões silenciosas dado que nada em CI roda.

---

## 7. Providers (LLM)

**Branch `main`** (atual):
- ✅ `base.py` (122 LOC) — interface abstrata
- ✅ `llamacpp.py` (156 LOC) — provider local
- ❌ Sem `openai.py`, `anthropic.py`, `deepseek.py`

**Branch `origin/dev`** (não-mergeado):
- ✅ `feat(phantom): add anthropic and deepseek providers` (commit `45d74fb`)
- Pode haver outros providers/refatorações.

> **Ação sugerida**: revisar e mergear `dev` em `main` (6 commits ahead). Ver §9.

---

## 8. CI/CD

8 workflows, **todos Nix-centric**, **nenhum roda `pytest`**:

| Workflow                  | Trigger     | O que faz                              |
|---------------------------|-------------|----------------------------------------|
| `nix-build.yml`           | push/PR     | `nix build .#default && nix develop`   |
| `nix-check.yml`           | push/PR     | `nix flake check`                      |
| `nix-fmt.yml`             | push/PR     | `nix fmt --check`                      |
| `release.yml`             | tag         | Release automation                     |
| `secret-scan.yml`         | push/PR     | Secret scanning                        |
| `update-flake-lock.yml`   | cron        | Bump flake.lock                        |
| `update-images.yml`       | cron        | Bump container images                  |
| `update-nix-version.yml`  | cron        | Bump Nix version                       |

**Gap claro**: criar um workflow `tests.yml` que rode `just test` + `just lint` (Ruff + mypy) em PRs. Hoje, o único portão é a sanidade do Nix.

---

## 9. Branches e divergência

```
main  (HEAD)
  └─ origin/dev  (6 commits ahead of main):
       eb0c7d3 p                                            ← WIP / checkpoint
       a962fed Merge main into dev
       2077b2d feat(api): add cortex-api and main-api separation
       a42303e Merge dev into dev
       3f88864 feat(cli): add playground and cheat sheet
       45d74fb feat(phantom): add anthropic and deepseek providers

  └─ origin/staging  (estado não inspecionado)
```

A separação `cortex-api / main-api` em `dev` provavelmente **resolve o limbo do `cortex_api.py`** (§3). Vale revisar o diff antes de seguir construindo em `main`.

---

## 10. Documentação

**Raiz** (10 arquivos):
```
README.md                  CONTRIBUTING.md
CLAUDE.md ⚠️ (stale)        SECURITY.md
AGENTS.md                  CODE_OF_CONDUCT.md
IMPLEMENTATION_STATUS.md ⚠️ (parcial)
SESSION_SUMMARY.md         FILES_MODIFIED.md
RELEASE-v0.1.0.md
```

**docs/** (29 arquivos organizados):
- `architecture/`: `ARCHITECTURAL_SYNTHESIS.md`, `CORTEX_V2_ARCHITECTURE.md` + 2 ADRs (`ADR-0017` consolidação monorepo, `ADR-0018` sprint backlog v2)
- `development/`: setup do desktop Svelte, guideline Nix+Python, mensagens de commit
- `guides/`: ROADMAP, VRAM calculator, quickstarts
- `history/`: PHASE1, TEST_RESULTS, reorganizações (snapshots históricos)
- `reference/`: docs específicos (Sentiment, vulnix report)
- `CHANGELOG.md`, `DEPLOYMENT.md`, `VALIDATION_REPORT.md`, `Phantom-GUI.md`

---

## 11. Descompassos doc ↔ código

| Doc                              | Afirma                                                | Realidade                                                    |
|----------------------------------|-------------------------------------------------------|--------------------------------------------------------------|
| `CLAUDE.md` §Tech Stack          | "Agent: Rust (Crane, multi-crate workspace)"          | `intelagent/` **não existe**. Único Rust é shim Tauri (23 LOC). |
| `CLAUDE.md` Diretório            | Lista `intelagent/crates/{security,governance,…}`     | Fictício.                                                    |
| `CLAUDE.md` LOC                  | "11.290 LOC, 33 files, 18 test files"                 | **13.470 LOC**, **37 files**, **26 test files**.             |
| `CLAUDE.md` API status           | 7 endpoints "TODO"                                    | 17 endpoints implementados.                                  |
| `CLAUDE.md` CLI status           | "Stubs only — phantom extract/analyze/classify/scan"  | Todos os 11 comandos funcionam.                              |
| `IMPLEMENTATION_STATUS.md`       | "Deployment docs (0%)"                                | `docs/DEPLOYMENT.md` existe (não verifiquei conteúdo).        |
| `IMPLEMENTATION_STATUS.md`       | Cloud providers "stubs only"                          | Em `main` não existem nem stubs. Em `dev` foram adicionados. |
| `ADR-0018` P1                    | "+page.svelte é monolítico, 1.193 LOC"                | Hoje tem 38 LOC, decomposto em 6 tabs em `lib/components/tabs/`. |
| `CLAUDE.md` `/process` status    | "TODO"                                                | Implementado, linha 363.                                     |
| `CLAUDE.md`                      | Mostra `app.py` com 190 LOC                           | 1.063 LOC.                                                   |

---

## 12. Trabalho realmente em aberto

Ordenado por impacto sobre o usuário final + esforço.

### P0 — Higiene técnica imediata
1. **Atualizar/podar `CLAUDE.md` e `IMPLEMENTATION_STATUS.md`** — qualquer agente novo (humano ou LLM) é induzido ao erro hoje.
2. **Resolver limbo `cortex_api.py`**: ou virar `APIRouter` e `include_router`, ou deletar. Olhar `dev` (`2077b2d feat(api): add cortex-api and main-api separation`) antes de decidir.
3. **CI roda testes Python**: workflow novo executando `just test` + `just lint` em PR.
4. **Mergear `origin/dev` em `main`** (ou rebase) — 6 commits, inclui Anthropic/DeepSeek e separação API.

### P1 — Features ainda não realmente entregues
5. **Cloud providers**: trazer Anthropic/DeepSeek de `dev`; OpenAI ainda 100% faltando.
6. **Frontend tests**: Vitest + Playwright + `@testing-library/svelte`. ADR-0018 P2 segue válido.
7. **SystemMonitor.svelte**: consome `/api/system/metrics` em loop curto e renderiza gráficos. Componentização da UI no resto do caminho (MessageBubble, FileUploader, ErrorToast).

### P2 — Otimizações
8. **Cache layer** (`src/phantom/core/cache.py`): LRU em memória para embeddings + queries (ADR-0018 P4). Redis depois.
9. **Streaming de fato no desktop**: ChatTab.svelte → `/api/chat/stream` via `fetch` + ReadableStream (ADR-0018 P5).
10. **Docstrings faltantes**: `core/cortex.py` e `rag/vectors.py` (Google style).

### P3 — Roadmap distante (não bloqueia GA)
11. **`intelagent/` real**: scaffold do crate Rust se for de fato no roadmap, ou tirar todas as menções dos docs.
12. **Auto-gen API docs** (Sphinx ou MkDocs).
13. **K8s/Helm**, **WebSocket chat**, **GraphQL** — todos low-priority.

---

## 13. Sinais de saúde

- ✅ Working tree limpa (só `.mcp.json` modificado da nossa sessão).
- ✅ Zero TODO/FIXME no Python (1 ocorrência inofensiva em comentário).
- ✅ Pydantic em todas as fronteiras; logging estruturado (`logging.py`).
- ✅ `nix develop` é a fonte única de toolchain — reprodutível.
- ⚠️ Nenhum gate automatizado pra qualidade Python (testes/lint só local).
- ⚠️ `dev` divergindo de `main` há ~1 semana com features prontas.
- ⚠️ Duas docs de status (`CLAUDE.md` + `IMPLEMENTATION_STATUS.md`) em desacordo entre si e com o código.

---

**Compilado por**: Claude (opus-4.7) em 2026-05-14
**Fonte**: leitura direta do filesystem em `/home/nx/suit/phantom` + `git log` / `git diff main..origin/dev`
**Não testado nesta sessão**: `just test`, `just lint`, `just build`, `nix flake check`
