# CORTEX v2.0 - Embeddings & Chunking Architecture

## 🎯 Vision

Evoluir o CORTEX para usar **semantic chunking** e **embeddings** antes da classificação, habilitando:

1. ✅ **Redução de VRAM**: Processar chunks ao invés de documentos inteiros
2. ✅ **Maior throughput**: Paralelizar chunks independentemente
3. ✅ **Melhor qualidade**: Focar contexto em partes relevantes
4. ✅ **Semantic Search**: Buscar insights por similaridade vetorial
5. ✅ **Incremental Processing**: Reutilizar embeddings já calculados
6. ✅ **RAG-Ready**: Base para Retrieval-Augmented Generation

---

## 🏗️ Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────┐
│  CORTEX v2.0 - Embeddings Pipeline                         │
└─────────────────────────────────────────────────────────────┘

Input: Markdown Files
    │
    ├─► STAGE 1: Semantic Chunking
    │   │
    │   ├─ Strategy: Recursive splitting by headers
    │   ├─ Size: 512-1024 tokens per chunk
    │   ├─ Overlap: 128 tokens (preservar contexto)
    │   └─ Metadata: source_file, chunk_id, headers
    │
    ├─► STAGE 2: Embeddings Generation
    │   │
    │   ├─ Model: sentence-transformers (local)
    │   │   • all-MiniLM-L6-v2 (384 dim, fast)
    │   │   • all-mpnet-base-v2 (768 dim, quality)
    │   ├─ Batch: 32 chunks por vez
    │   └─ Output: Vector embeddings (numpy arrays)
    │
    ├─► STAGE 3: Vector Storage
    │   │
    │   ├─ Options:
    │   │   • ChromaDB (local, simple)
    │   │   • Qdrant (production-grade)
    │   │   • FAISS (in-memory, fast)
    │   └─ Metadata: chunk_text, embedding, file_path, headers
    │
    ├─► STAGE 4: Intelligent Classification
    │   │
    │   ├─ Pre-filter: Semantic search por relevância
    │   ├─ LLM Processing: Só chunks relevantes
    │   ├─ Context Assembly: Agregar insights de chunks
    │   └─ Output: Structured JSON (como v1.0)
    │
    └─► STAGE 5: Semantic Search API
        │
        ├─ Query: "How to handle errors in Python?"
        ├─ Vector Search: Top-K chunks similares
        ├─ LLM Synthesis: Resposta baseada em chunks
        └─ Output: Answer + Source citations
```

---

## 📊 Benefícios Quantificados

### 1. Redução de VRAM

**Antes (v1.0)**:
```
Documento 10k tokens → Context 4096 → VRAM ~3 GB
```

**Depois (v2.0)**:
```
Documento 10k tokens → 10 chunks de 1k → Process 1 chunk por vez
Chunk 1k tokens → Context 1024 → VRAM ~0.75 GB (4x menor!)
```

### 2. Aumento de Throughput

**Paralelização por chunk**:
```python
# v1.0: Processar documento inteiro sequencialmente
1 documento de 10k tokens = 1 request de 20s = 1 doc/20s

# v2.0: Processar chunks em paralelo
10 chunks de 1k tokens = 10 requests de 5s cada (paralelo) = 1 doc/5s
Throughput: 4x maior!
```

### 3. Melhor Uso do Context Window

```
# v1.0: Documento grande com truncation
Documento 20k tokens → Truncado para 4k → Perda de 80% do conteúdo

# v2.0: Chunks completos processados
Documento 20k tokens → 20 chunks de 1k → 100% processado
```

---

## 🔧 Implementação Técnica

### Componentes Necessários

```nix
# Adicionar ao flake.nix
pythonEnv = pkgs.python3.withPackages (ps: with ps; [
  # Existing...
  
  # Embeddings & NLP
  sentence-transformers  # Embeddings model
  transformers          # HuggingFace
  torch                 # PyTorch backend
  
  # Chunking
  langchain             # Semantic text splitters
  tiktoken              # Token counting (OpenAI)
  
  # Vector Databases
  chromadb              # Local vector DB
  faiss                 # Facebook AI similarity search
  
  # Optional: Production
  # qdrant-client       # Qdrant vector DB
]);
```

### Estimativas de VRAM

| Componente | VRAM | Observações |
|------------|------|-------------|
| **Embedding Model** (MiniLM) | ~500 MB | Roda em GPU ou CPU |
| **LLM per chunk** (1k tokens) | ~0.75 GB | vs 3 GB para doc inteiro |
| **Total headroom** | ~1.5-2 GB | Embedding + chunk processing |

**Exemplo GPU 24GB**:
```
Modelo Qwen3-30B Q4_K_M:  16.8 GB
Embedding Model:           0.5 GB
Chunk (1k context):        0.8 GB
Overhead:                  0.5 GB
─────────────────────────────────
Total:                    18.6 GB  (vs 21.1 GB em v1.0)
Free:                      5.4 GB  ✅ (~2x mais livre!)
```

---

## 🎯 Chunking Strategies

### 1. **Recursive by Headers** (Recomendado para Markdown)

```python
# Preserva estrutura semântica
Document
├─ # Header 1
│  ├─ ## Subheader 1.1  → Chunk 1
│  └─ ## Subheader 1.2  → Chunk 2
└─ # Header 2
   └─ ## Subheader 2.1  → Chunk 3
```

**Vantagens**:
- ✅ Respeita estrutura do documento
- ✅ Chunks semanticamente coesos
- ✅ Preserva hierarquia em metadata

### 2. **Sliding Window** (Para documentos sem estrutura)

```python
# Overlap para preservar contexto
[────────────────]
      [────────────────]
            [────────────────]
```

### 3. **Semantic Similarity** (Avançado)

```python
# Agrupa sentenças por similaridade
Embeddings → Cluster → Chunks naturais
```

---

## 🚀 Pipeline de Processamento Otimizado

### Workflow Proposto

```python
def process_document_v2(doc_path):
    # 1. Chunk
    chunks = semantic_chunk(doc_path, max_tokens=1024, overlap=128)
    
    # 2. Generate embeddings (batch)
    embeddings = embed_model.encode(chunks, batch_size=32)
    
    # 3. Store in vector DB
    vector_db.add(chunks, embeddings, metadata={...})
    
    # 4. Classify (com pre-filtering opcional)
    insights = []
    for chunk in chunks:
        # Opção A: LLM em todos os chunks
        insight = llm_classify(chunk)
        
        # Opção B: Pre-filter por relevância
        if is_relevant(chunk, query="extract insights"):
            insight = llm_classify(chunk)
        
        insights.append(insight)
    
    # 5. Aggregate insights
    final_insights = aggregate_chunk_insights(insights)
    
    return final_insights
```

### Paralelização Inteligente

```python
# Worker pool por chunk (não por documento!)
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = []
    
    for doc in documents:
        chunks = chunk_document(doc)
        
        for chunk in chunks:
            # Processar cada chunk independentemente
            future = executor.submit(process_chunk, chunk)
            futures.append(future)
    
    # Collect e aggregate
    results = [f.result() for f in as_completed(futures)]
```

**Ganho de throughput**:
```
100 documentos × 10 chunks cada = 1000 chunks
1000 chunks ÷ 8 workers = 125 chunks por worker
@5s por chunk = ~625s total

vs v1.0:
100 documentos × 20s cada = 2000s total

Speedup: 3.2x! 🚀
```

---

## 📈 Casos de Uso Habilitados

### 1. **Semantic Search**

```python
# Query de busca
query = "How to implement error handling in Python?"

# Vector search
similar_chunks = vector_db.search(query, top_k=10)

# LLM synthesis
answer = llm.synthesize(similar_chunks, query)
```

### 2. **RAG (Retrieval-Augmented Generation)**

```python
# User question
question = "What are the best practices for NixOS flakes?"

# Retrieve relevant chunks
context_chunks = vector_db.search(question, top_k=5)

# Generate answer with context
answer = llm.generate(
    prompt=f"Context: {context_chunks}\n\nQuestion: {question}",
    max_tokens=512
)
```

### 3. **Incremental Updates**

```python
# Novo documento adicionado
new_doc = "new_guide.md"

# Check existing embeddings
if not vector_db.exists(new_doc):
    chunks = chunk_document(new_doc)
    embeddings = embed_model.encode(chunks)
    vector_db.add(chunks, embeddings)
else:
    print("Already processed, skipping")
```

### 4. **Topic Clustering**

```python
# Agrupar documentos por similaridade
clusters = cluster_by_embedding(
    embeddings=vector_db.get_all_embeddings(),
    n_clusters=10,
    method='kmeans'
)

# Visualizar
visualize_clusters(clusters, method='tsne')
```

---

## 🎓 Design Decisions

### Embedding Model Selection

| Model | Dim | Size | Speed | Quality | Uso |
|-------|-----|------|-------|---------|-----|
| **MiniLM-L6-v2** | 384 | 80MB | ⚡⚡⚡ | ⭐⭐⭐ | General purpose |
| **mpnet-base-v2** | 768 | 420MB | ⚡⚡ | ⭐⭐⭐⭐ | High quality |
| **instructor-xl** | 768 | 1.3GB | ⚡ | ⭐⭐⭐⭐⭐ | Task-specific |

**Recomendação**: Começar com **MiniLM-L6-v2** (rápido, leve, bom trade-off).

### Vector DB Selection

| DB | Deployment | Performance | Features | Complexidade |
|----|------------|-------------|----------|--------------|
| **FAISS** | In-memory | ⚡⚡⚡ | Basic search | Simples |
| **ChromaDB** | Local/Server | ⚡⚡ | Metadata filter | Médio |
| **Qdrant** | Server | ⚡⚡⚡ | Production features | Alto |

**Recomendação**: 
- Desenvolvimento: **FAISS** (in-memory, sem setup)
- Produção: **ChromaDB** (persistência, fácil deploy)

---

## 📊 Roadmap de Implementação

### Phase 1: Core Chunking & Embeddings
- [x] Design architecture
- [ ] Implement semantic chunker
- [ ] Integrate sentence-transformers
- [ ] Add FAISS vector storage
- [ ] Update flake.nix dependencies

### Phase 2: Optimized Classification
- [ ] Chunk-based LLM processing
- [ ] Parallel chunk workers
- [ ] Insight aggregation
- [ ] Performance benchmarks

### Phase 3: Semantic Search
- [ ] Query interface
- [ ] Vector similarity search
- [ ] Result ranking
- [ ] Citation tracking

### Phase 4: Advanced Features
- [ ] ChromaDB integration
- [ ] Incremental processing
- [ ] Topic clustering
- [ ] RAG capabilities

---

## 🎯 Expected Performance

### VRAM Savings

| Scenario | v1.0 VRAM | v2.0 VRAM | Savings |
|----------|-----------|-----------|---------|
| Small doc (2k tokens) | 18 GB | 17.5 GB | 3% |
| Medium doc (5k tokens) | 19 GB | 17.8 GB | 6% |
| Large doc (10k tokens) | 21 GB | 18.1 GB | 14% |
| **Huge doc (20k tokens)** | **Won't fit** | **18.6 GB** | **∞%** |

### Throughput Gains

| Metric | v1.0 | v2.0 | Improvement |
|--------|------|------|-------------|
| Docs/min (small) | 8 | 12 | +50% |
| Docs/min (medium) | 5 | 10 | +100% |
| Docs/min (large) | 3 | 8 | +167% |
| **Max doc size** | **10k tokens** | **Unlimited** | **∞** |

---

## 💡 Next Steps

1. **Review architecture** → Iterar design com você
2. **Implement chunker** → `cortex_chunker.py`
3. **Add embeddings** → `cortex_embeddings.py`
4. **Integrate vector DB** → ChromaDB ou FAISS
5. **Benchmark** → Comparar v1.0 vs v2.0
6. **Documentation** → Guias de uso

---

**Ready to implement?** Posso começar com qualquer componente! 🚀

Sugestões:
- A. Começar pelo chunker semântico
- B. Setup de embeddings primeiro
- C. Protótipo end-to-end mínimo
- D. Outro enfoque?
