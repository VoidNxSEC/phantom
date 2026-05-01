# 🔮 CORTEX ETL Pipeline - Summary

## ✅ O que foi criado

### 1. **cortex.py** - Pipeline ETL Inteligente
- **Localização**: `/home/kernelcore/dev/Projects/phantom/cortex.py`
- **Linhas de código**: ~830 linhas
- **Funcionalidades**:
  - ✅ Processamento batch de arquivos markdown
  - ✅ Integração com llamacpp server local
  - ✅ Extração de: Themes, Patterns, Learnings, Concepts, Recommendations
  - ✅ Validação Pydantic V2 com schemas robustos
  - ✅ Retry logic com exponential backoff
  - ✅ Monitoramento de VRAM/RAM
  - ✅ Threading para processamento paralelo
  - ✅ Logging detalhado
  - ✅ Output em JSONL
  - ✅ CLI completa com argparse

### 2. **CORTEX_README.md** - Documentação Completa
- Guia de uso completo
- Exemplos práticos
- Troubleshooting
- Schema de saída documentado
- Performance benchmarks
- Exemplos de análise posterior

### 3. **test_cortex.py** - Test Suite
- **Status**: ✅ 5/5 testes passando
- Valida:
  - Imports
  - Pydantic models (V2)
  - Prompt building
  - JSON parsing
  - System monitoring

### 4. **cortex_demo.sh** - Script de Demonstração
- Cria arquivos markdown de exemplo
- Verifica servidor llamacpp
- Executa CORTEX automaticamente
- Mostra resultados

### 5. **flake.nix** - Dependências Atualizadas
- ✅ Adicionado `requests` (HTTP client)
- ✅ Adicionado `psutil` (System monitoring)
- ✅ Todas as dependências já estavam presentes:
  - `pydantic` (v2)
  - `rich` (Terminal UI)

## 🎯 Como Usar

### Passo 1: Iniciar o LlamaCPP Server

```bash
# Com llama-cpp-python
python -m llama_cpp.server \
  --model /path/to/unsloth_Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080
```

### Passo 2: Executar CORTEX

```bash
# Entre no ambiente Nix
nix develop

# Opção 1: Usar o demo
./cortex_demo.sh

# Opção 2: Processar seus próprios arquivos
./cortex.py -i /path/to/markdown/files -o output/insights.jsonl -v

# Opção 3: Com configurações customizadas
./cortex.py \
  -i notes/ \
  -o insights.jsonl \
  --url http://192.168.1.100:8080 \
  --batch-size 5 \
  --workers 8 \
  --context-size 8192 \
  -v
```

### Passo 3: Analisar Resultados

```python
import json

# Ler insights
insights = []
with open('output/insights.jsonl') as f:
    for line in f:
        insights.append(json.loads(line))

# Exemplo: Extrair todos os temas
all_themes = []
for doc in insights:
    all_themes.extend(doc['themes'])

# Análise de keywords
from collections import Counter
keywords = [kw for theme in all_themes for kw in theme['keywords']]
print("Top 10 keywords:", Counter(keywords).most_common(10))
```

## 📊 Schema de Saída (JSONL)

Cada linha representa um arquivo processado:

```json
{
  "file_path": "/absolute/path/to/file.md",
  "file_name": "file.md",
  "processed_at": "2025-12-10T22:00:00Z",
  "word_count": 1234,
  "themes": [
    {
      "title": "Development Best Practices",
      "description": "Guidelines for code quality and testing",
      "confidence": "high",
      "keywords": ["testing", "code-review", "tdd"]
    }
  ],
  "patterns": [
    {
      "pattern_type": "workflow",
      "description": "Test-driven development approach",
      "examples": ["Write tests first", "Red-Green-Refactor"],
      "frequency": 2
    }
  ],
  "learnings": [
    {
      "title": "Early testing saves time",
      "description": "Implementing TDD reduces debugging time",
      "category": "technical",
      "actionable": true
    }
  ],
  "concepts": [
    {
      "name": "Microservices",
      "definition": "Architectural pattern using independent services",
      "related_concepts": ["API Gateway", "Event-driven"],
      "complexity": "medium"
    }
  ],
  "recommendations": [
    {
      "title": "Never commit secrets",
      "description": "Use environment variables for sensitive data",
      "priority": "high",
      "category": "security",
      "implementation_effort": "low"
    }
  ],
  "extraction_confidence": "high",
  "processing_time_seconds": 12.5,
  "model_used": "Qwen3-Coder-30B"
}
```

## 🔧 Configurações

### Defaults
- **Context Size**: 4096 tokens
- **Batch Size**: 10 arquivos
- **Workers**: 4 threads
- **Temperature**: 0.3 (baixa para consistência)
- **Max Tokens**: 2048
- **Retry Attempts**: 3
- **Retry Delay**: 2s (exponential backoff)

### VRAM Thresholds
- **Warning**: < 512MB livre
- **Critical**: < 256MB livre (pausa processamento)

## 🎓 Notas Técnicas

### Design Decisions

1. **Pydantic V2**: 
   - Migrado `@validator` → `@field_validator`
   - Adicionado `@classmethod` decorator
   - Removido parâmetro `field` dos validators

2. **Threading vs Multiprocessing**:
   - ThreadPoolExecutor escolhido para I/O-bound (HTTP calls)
   - Melhor para latência de rede do que CPU

3. **JSONL Format**:
   - Permite processamento incremental
   - Cada linha é JSON independente
   - Fácil de processar em streaming

4. **Prompt Engineering**:
   - System prompt claro com schema JSON
   - Truncamento inteligente de contexto
   - Parsing robusto (remove markdown code blocks)

### Limitações

- **Tamanho de arquivo**: Limitado pelo context window (4k-8k tokens)
- **Formato**: Somente markdown (.md)
- **Modelo**: Requer modelo instruído para JSON output
- **Servidor**: Depende de llamacpp server rodando

## 🚀 Próximas Melhorias Sugeridas

1. **Multi-formato**:
   - Suporte para .txt, .pdf, .docx
   - Auto-detecção de formato

2. **Embeddings**:
   - Gerar embeddings com sentence-transformers
   - Habilitar semantic search

3. **Graph Database**:
   - Export para Neo4j
   - Visualizar relacionamentos entre conceitos

4. **Web UI**:
   - Dashboard interativo
   - Visualização de insights
   - Busca e filtros

5. **Incremental Processing**:
   - Detectar arquivos já processados
   - Only process new/modified files

6. **Quality Metrics**:
   - Score de qualidade das extrações
   - Validação cruzada entre múltiplas runs

## 📈 Performance Esperada

Com modelo Q4_K_M Qwen3-Coder-30B:

- **Throughput**: 5-10 arquivos/minuto
- **VRAM Usage**: 6-8GB (modelo carregado)
- **RAM Usage**: 2-4GB (processamento)
- **Latência média**: 10-20s por arquivo

## ✅ Checklist de Validação

- [x] Código criado e funcional (`cortex.py`)
- [x] Dependências adicionadas ao `flake.nix`
- [x] Pydantic V2 compatibilidade
- [x] Test suite passando (5/5)
- [x] Documentação completa (`CORTEX_README.md`)
- [x] Script de demo (`cortex_demo.sh`)
- [x] CLI funcional com `--help`
- [x] Executable permissions configuradas

## 🎉 Status Final

**CORTEX v1.0 está pronto para uso!**

Todos os componentes foram implementados, testados e documentados. O pipeline está operacional e aguardando apenas que você:

1. Inicie seu servidor llamacpp
2. Execute `./cortex_demo.sh` ou `./cortex.py -i <input> -o <output>`
3. Analise os insights extraídos

Enjoy! 🚀
