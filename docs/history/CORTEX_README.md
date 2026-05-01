# CORTEX v1.0 - Intelligent Markdown ETL Pipeline

## 🔮 Overview

**CORTEX** é um pipeline ETL inteligente que processa arquivos Markdown usando um modelo LLM local (Qwen3-Coder-30B) via llamacpp server. Ele extrai insights estruturados como temas, padrões, aprendizados, conceitos e recomendações.

## 🎯 Features

- ✅ **Batch Processing**: Processa múltiplos arquivos em lotes configuráveis
- ✅ **Concurrency**: Threading para processamento paralelo
- ✅ **JSON Schema Validation**: Validação Pydantic de saídas estruturadas
- ✅ **Retry Logic**: Retry automático com backoff exponencial
- ✅ **VRAM Monitoring**: Monitoramento de recursos do sistema
- ✅ **Logging Detalhado**: Logs completos de execução
- ✅ **JSONL Output**: Formato otimizado para análise posterior
- ✅ **Health Checks**: Verificação do servidor antes de processar

## 📦 Dependências

Todas as dependências estão no `flake.nix`:

```nix
pydantic      # Validação de schemas
requests      # Cliente HTTP para llamacpp
rich          # Output terminal bonito
psutil        # Monitoramento de sistema
```

## 🚀 Uso

### Configuração do Servidor LlamaCPP

Primeiro, inicie seu servidor llamacpp:

```bash
# Exemplo usando llama-cpp-python
python -m llama_cpp.server \
  --model /caminho/para/unsloth_Qwen3-Coder-30B-A3B-Instruct-GGUF_Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf \
  --n_ctx 4096 \
  --host 0.0.0.0 \
  --port 8080
```

### Execução Básica

```bash
# Entre no ambiente Nix
nix develop

# Processar todos os markdowns em input_data/
./cortex.py -i input_data -o output/insights.jsonl

# Com verbose e batch personalizado
./cortex.py -i notes/ -o results.jsonl -v --batch-size 5 --workers 8

# Servidor customizado
./cortex.py -i docs/ -o insights.jsonl --url http://192.168.1.100:8080
```

### Parâmetros CLI

```
Argumentos obrigatórios:
  -i, --input DIR          Diretório com arquivos .md
  -o, --output FILE        Arquivo JSONL de saída

Configuração LlamaCPP:
  --url URL                URL do server (default: http://localhost:8080)
  --model NAME             Nome do modelo
  --context-size SIZE      Tamanho do contexto (default: 4096)

Processamento:
  --batch-size N           Tamanho do lote (default: 10)
  --workers N              Número de threads (default: 4)
  
Opções:
  -v, --verbose            Logging detalhado
  --version                Mostrar versão
```

## 📊 Schema de Saída

Cada linha do JSONL contém:

```json
{
  "file_path": "/path/to/file.md",
  "file_name": "file.md",
  "processed_at": "2025-12-10T20:00:00Z",
  "word_count": 1234,
  "themes": [
    {
      "title": "Nix Development",
      "description": "Guidelines for Python development in Nix",
      "confidence": "high",
      "keywords": ["nix", "python", "flakes"]
    }
  ],
  "patterns": [
    {
      "pattern_type": "code",
      "description": "String escaping in Nix multi-line strings",
      "examples": ["b'''", "''${var}"],
      "frequency": 3
    }
  ],
  "learnings": [
    {
      "title": "Stdlib modules should not be in pythonPackages",
      "description": "Standard library modules like hashlib, json are built-in",
      "category": "technical",
      "actionable": true
    }
  ],
  "concepts": [
    {
      "name": "Pseudonymization",
      "definition": "Reversible replacement of identifiers",
      "related_concepts": ["anonymization", "data_masking"],
      "complexity": "medium"
    }
  ],
  "recommendations": [
    {
      "title": "Use lowercase package names",
      "description": "nixpkgs uses lowercase: vadersentiment not vaderSentiment",
      "priority": "high",
      "category": "best_practice",
      "implementation_effort": "low"
    }
  ],
  "extraction_confidence": "high",
  "processing_time_seconds": 12.5,
  "model_used": "Qwen3-Coder-30B"
}
```

## 🔧 Configuração Avançada

### Ajuste de Context Window

Para arquivos muito grandes, ajuste o context size:

```bash
./cortex.py -i large_docs/ -o output.jsonl --context-size 8192
```

### Monitoramento de VRAM

O CORTEX monitora automaticamente VRAM (NVIDIA) e pausa se:
- **Warning**: < 512MB livre
- **Critical**: < 256MB livre (pausa de 5s)

### Retry Logic

Configuração padrão:
- **Tentativas**: 3
- **Backoff**: Exponencial (2s, 4s, 8s)
- **Timeout**: 120s por requisição

## 📈 Performance

Benchmarks típicos (modelo Q4_K_M):
- **Throughput**: ~5-10 arquivos/minuto
- **VRAM**: ~6-8GB (modelo carregado)
- **RAM**: ~2-4GB (processamento)
- **Tempo médio**: 10-20s por arquivo (dependendo do tamanho)

## 🛠️ Troubleshooting

### Error: "chiamacpp server health check failed"

1. Verifique se o servidor está rodando:
   ```bash
   curl http://localhost:8080/health
   ```

2. Confirme a porta correta no comando

### Error: "JSON parse error"

O modelo pode estar retornando texto não-JSON. Soluções:
- Reduza o `temperature` no código (já está em 0.3)
- Use um modelo melhor treinado para structured output
- Verifique os logs com `-v`

### VRAM Insuficiente

Se o modelo não cabe na VRAM:
- Use um modelo menor (Q3, Q2)
- Reduza `context-size`
- Use CPU offloading

## 📝 Exemplos de Análise Posterior

### Extrair todos os temas

```python
import json

themes = []
with open('insights.jsonl') as f:
    for line in f:
        data = json.loads(line)
        themes.extend(data['themes'])

# Análise de frequência
from collections import Counter
keywords = [kw for t in themes for kw in t['keywords']]
print(Counter(keywords).most_common(10))
```

### Filtrar por confidence

```python
high_confidence = []
with open('insights.jsonl') as f:
    for line in f:
        data = json.loads(line)
        if data['extraction_confidence'] == 'high':
            high_confidence.append(data)
```

## 🔐 Segurança

- ✅ Processa apenas arquivos `.md`
- ✅ Ignora arquivos ocultos (começando com `.`)
- ✅ Timeout em requisições HTTP
- ✅ Validação de schema Pydantic
- ✅ Logs de erro detalhados

## 📚 Estrutura do Código

```
cortex.py
├── Pydantic Models (Schemas)
│   ├── Theme, Pattern, Learning
│   ├── Concept, Recommendation
│   └── MarkdownInsights
│
├── System Monitoring
│   └── SystemMonitor (VRAM/RAM)
│
├── LlamaCPP Client
│   ├── Health check
│   ├── Generation with retry
│   └── Error handling
│
├── Prompt Engineering
│   ├── PromptBuilder
│   └── JSON parsing
│
├── ETL Processor
│   ├── File discovery
│   ├── Batch processing
│   ├── Threading
│   └── JSONL output
│
└── CLI Interface
    └── argparse configuration
```

## 🎓 Notas de Design

1. **4K Context**: Escolhido para balancear velocidade e qualidade
2. **Temperature 0.3**: Baixa para extração consistente
3. **Threading**: Melhor para I/O-bound (chamadas HTTP)
4. **JSONL**: Permite processamento incremental e análise stream
5. **Pydantic**: Garante qualidade de dados extraídos

## 🚀 Próximos Passos

- [ ] Suporte para outros formatos (txt, pdf, docx)
- [ ] Embeddings para semantic search
- [ ] Dashboard web para visualização
- [ ] Export para Neo4j (conhecimento em grafo)
- [ ] Integração com Obsidian/Logseq

## 📄 Licença

Parte do projeto Phantom. Veja `LICENSE`.

---

**Version**: 1.0.0  
**Codename**: CORTEX  
**Last Updated**: 2025-12-10
