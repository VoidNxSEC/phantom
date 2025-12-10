# 🔮 SPECTRE v1.0

**Sentiment & Pattern Extraction for Contextual Text Research Engine**

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║  ███████╗██████╗ ███████╗ ██████╗████████╗██████╗ ███████╗                       ║
║  ██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝                       ║
║  ███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝█████╗                         ║
║  ╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══╝                         ║
║  ███████║██║     ███████╗╚██████╗   ██║   ██║  ██║███████╗                       ║
║  ╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝                       ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

## 🎯 Overview

SPECTRE é um pipeline de análise de sentimento **multi-dimensional** projetado para documentação técnica, especialmente no domínio **blockchain/Web3**. 

Diferente de análise de sentimento tradicional (positivo/negativo), SPECTRE avalia **5 dimensões** simultâneas:

| Dimensão | O que mede |
|----------|------------|
| **Technical** | Confiança técnica, segurança, robustez |
| **Market** | Sentimento bullish/bearish, tendências |
| **Community** | Saúde da comunidade, engajamento |
| **Innovation** | Progresso, novidade, estagnação |
| **Risk** | Perfil de risco, vulnerabilidades |

## 🚀 Quick Start

```bash
# 1. Entrar no ambiente
cd spectre-pipeline
nix develop

# 2. Analisar corpus de markdown
spectre -i ./docs -o ./analysis -t taxonomy.txt -v

# 3. Ver relatório
glow ./analysis/reports/summary_report_*.md

# 4. Heatmap de sentimento
spectre-heatmap ./analysis/reports/sentiment_data_*.csv
```

## 📦 Ferramentas Incluídas

### `spectre` - Pipeline Principal

```bash
spectre -i <input_dir> -o <output_dir> [options]

Options:
  -i, --input      Diretório com arquivos .md
  -o, --output     Diretório para resultados
  -t, --taxonomy   Arquivo de taxonomia (um termo por linha)
  -w, --workers    Threads paralelas (default: CPU count)
  -v, --verbose    Output detalhado
```

### `spectre-quick` - Análise Rápida

```bash
# Análise de arquivo único
spectre-quick documento.md

# Via stdin
cat doc.md | spectre-quick -

# Output:
# 📊 Quick Sentiment Analysis
#    Words: 1547
#    Matched: 23
#    Score: 0.2341
#    Label: POSITIVE
```

### `spectre-scan` - Scanner de Tópicos

```bash
# Scan com taxonomia
spectre-scan ./docs taxonomy.txt

# Output:
# 🔍 SPECTRE Topic Scanner
#   smart contracts              47 mentions
#   defi                         35 mentions
#   tokenization                 28 mentions
```

### `spectre-stats` - Estatísticas do Corpus

```bash
spectre-stats ./docs

# Output:
# 📊 SPECTRE Corpus Statistics
#   📄 MD Files:     1247
#   📖 Total Words:  892341
#   📊 Avg Words/Doc: 715
```

### `spectre-heatmap` - Visualização ASCII

```bash
spectre-heatmap sentiment_data.csv

# Output visual colorido mostrando sentimento por documento/dimensão
```

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SPECTRE PIPELINE                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐      │
│  │  INGEST  │──▶│  PARSE   │──▶│ ANALYZE  │──▶│  ENRICH  │──▶│  OUTPUT  │      │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘      │
│       │              │              │              │              │              │
│  File         Markdown      Multi-Dim       Knowledge      Reports              │
│  Discovery    AST           Sentiment       Graph          Insights             │
│  Metadata     Sections      Topics          Entities       Trends               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📊 Outputs Gerados

```
output/
├── documents/                    # Análise individual de cada doc
│   ├── doc1_analysis.json
│   └── doc2_analysis.json
└── reports/
    ├── corpus_insights_*.json    # Insights agregados (JSON)
    ├── summary_report_*.md       # Relatório legível (Markdown)
    └── sentiment_data_*.csv      # Dados para visualização
```

### Exemplo de Insight JSON

```json
{
  "sentiment_distribution": {
    "technical": {
      "positive": 342,
      "neutral": 567,
      "negative": 91
    }
  },
  "avg_sentiment_by_dimension": {
    "technical": 0.2341,
    "market": 0.1892,
    "community": 0.3012,
    "innovation": 0.2567,
    "risk": -0.1234
  },
  "key_findings": [
    "📈 Overall corpus sentiment is POSITIVE (avg: 0.23)",
    "🔧 High TECHNICAL CONFIDENCE detected (avg: 0.23)",
    "🏷️ Most discussed topics: smart contracts (47x), defi (35x)"
  ]
}
```

## 🧠 Lexicons de Sentimento

SPECTRE usa lexicons customizados para o domínio blockchain:

### Technical Confidence
```
positive: audited (+0.85), secure (+0.7), battle-tested (+0.85)
negative: vulnerable (-0.8), unaudited (-0.8), exploit (-0.9)
```

### Market Sentiment
```
bullish: moon (+0.8), ath (+0.8), adoption (+0.6)
bearish: crash (-0.85), dump (-0.7), rug pull (-0.95)
```

### Risk Assessment
```
low risk: insured (+0.55), collateralized (+0.45)
high risk: liquidation (-0.6), flashloan attack (-0.8)
```

## 🏷️ Taxonomia

O arquivo `taxonomy.txt` contém ~200 termos do ecossistema blockchain/Web3, organizados em categorias:

- **blockchain_core**: consensus, sharding, state channels
- **smart_contracts**: TEAL, PyTeal, formal verification
- **defi**: AMM, liquidity pools, yield farming
- **governance**: DAO, voting mechanisms, treasury
- **security**: audit, vulnerability, bug bounty
- **scalability**: layer-2, rollups, zk-proofs

## 📈 Métricas Calculadas

### Por Documento

| Métrica | Descrição |
|---------|-----------|
| `compound` | Score normalizado [-1, 1] |
| `pos/neg/neu` | Proporções de cada polaridade |
| `confidence` | Certeza da classificação |
| `dominant_dimension` | Dimensão mais expressiva |
| `sentiment_divergence` | Desvio entre dimensões |

### Por Corpus

| Métrica | Descrição |
|---------|-----------|
| `topic_frequency` | Frequência de cada termo da taxonomia |
| `topic_sentiment` | Sentimento médio associado a cada tópico |
| `sentiment_trend` | Evolução do sentimento ao longo dos docs |
| `entity_network` | Co-ocorrências de entidades |

## 🔬 Algoritmo VADER Adaptado

SPECTRE usa uma implementação customizada do VADER (Valence Aware Dictionary and sEntiment Reasoner) com:

1. **Boosters**: "very", "extremely" amplificam sentimento
2. **Dampeners**: "slightly", "somewhat" reduzem intensidade
3. **Negation**: "not", "never" invertem polaridade
4. **ALL CAPS**: Amplificação automática
5. **Punctuation**: `!!!` aumenta intensidade

## 🛠️ Extensão

### Adicionar Termos ao Lexicon

```python
# Em spectre.py, classe SentimentLexicons
TECHNICAL_CONFIDENCE = {
    # Adicione novos termos
    'novo_termo': 0.6,  # Score entre -1 e 1
}
```

### Adicionar Categoria de Taxonomia

```python
# Em TaxonomyManager.CATEGORY_PATTERNS
CATEGORY_PATTERNS = {
    'nova_categoria': [
        'termo1', 'termo2', 'termo3'
    ],
}
```

## 📋 Casos de Uso

### 1. Auditoria de Documentação de Projeto

```bash
spectre -i ./project-docs -o ./audit -t blockchain_taxonomy.txt -v
# → Identifica gaps de documentação, áreas com linguagem negativa
```

### 2. Análise de Whitepapers

```bash
spectre -i ./whitepapers -o ./wp-analysis -v
# → Compara tom técnico vs marketing entre projetos
```

### 3. Monitoramento de Comunidade

```bash
# Exportar posts do Discord/Forum para .md
spectre -i ./community-posts -o ./sentiment-tracking -v
# → Detecta mudanças de sentimento ao longo do tempo
```

### 4. Due Diligence

```bash
spectre -i ./project-materials -o ./dd-report -t taxonomy.txt -v
# → Identifica red flags em documentação de projetos
```

## 🔒 Integração com PHANTOM

SPECTRE foi projetado para trabalhar junto com o PHANTOM CLASSIFIER:

```bash
# 1. Classificar e organizar dados brutos
phantom -i ./raw_data -o ./classified

# 2. Analisar apenas documentos
spectre -i ./classified/documents -o ./sentiment_analysis -t taxonomy.txt
```

## 📊 Exemplo de Relatório Gerado

```markdown
# 🔮 SPECTRE Analysis Report

**Generated:** 2024-12-10T15:30:00Z
**Documents Analyzed:** 1247
**Total Words Processed:** 892,341

## 📊 Sentiment Overview

| Dimension | Average Score | Interpretation |
|-----------|--------------|----------------|
| Technical | 0.2341 | Positive |
| Market | 0.1892 | Positive |
| Community | 0.3012 | Positive |
| Innovation | 0.2567 | Positive |
| Risk | -0.1234 | Negative |

## 🎯 Key Findings

- 📈 Overall corpus sentiment is POSITIVE (avg: 0.23)
- 🔧 High TECHNICAL CONFIDENCE detected (avg: 0.23)
- ⚠️ RISK dimension shows concerns (avg: -0.12)

## 💡 Recommendations

- 💡 Address concerns around: liquidation, impermanent loss
- 💡 Risk-related content is negative - add mitigation strategies
```

---

*SPECTRE v1.0 - Built for blockchain documentation analysis*
