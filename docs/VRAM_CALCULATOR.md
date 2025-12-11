# 🎮 VRAM Calculator - Guia Completo

## 📐 Fórmulas de Cálculo de VRAM

### 1. VRAM do Modelo (Estático)

A VRAM necessária para carregar um modelo GGUF depende da **quantização**:

```
VRAM_modelo = Parâmetros × Bits_por_Parâmetro / 8 / 1024³
```

#### Tabela de Quantizações Comuns

| Quantização | Bits/Param | Fator | Exemplo 30B | VRAM Aprox |
|-------------|-----------|-------|-------------|------------|
| **Q2_K**    | ~2.5      | 0.31  | 30B × 0.31  | ~9.3 GB    |
| **Q3_K_M**  | ~3.5      | 0.44  | 30B × 0.44  | ~13.2 GB   |
| **Q4_K_M**  | ~4.5      | 0.56  | 30B × 0.56  | ~16.8 GB   |
| **Q5_K_M**  | ~5.5      | 0.69  | 30B × 0.69  | ~20.7 GB   |
| **Q6_K**    | ~6.0      | 0.75  | 30B × 0.75  | ~22.5 GB   |
| **Q8_0**    | ~8.0      | 1.00  | 30B × 1.00  | ~30.0 GB   |
| **FP16**    | 16.0      | 2.00  | 30B × 2.00  | ~60.0 GB   |

**Fórmula Rápida:**
```
VRAM_modelo (GB) ≈ Parâmetros (B) × Fator_Quantização
```

---

### 2. VRAM de Contexto (KV Cache)

O **KV Cache** armazena os estados dos tokens processados:

```
VRAM_kv = 2 × Layers × Hidden_Dim × Context_Size × Precision / 8 / 1024³
```

#### Para Qwen3-Coder-30B (exemplo):
- **Layers**: ~60
- **Hidden Dim**: ~5120
- **Precision**: FP16 (2 bytes)

**Cálculo:**
```python
VRAM_kv (GB) = 2 × 60 × 5120 × Context_Size × 2 / (8 × 1024³)

# Para diferentes context sizes:
Context 2048:  ~1.5 GB
Context 4096:  ~3.0 GB
Context 8192:  ~6.0 GB
Context 16384: ~12.0 GB
```

**Fórmula Simplificada para modelos ~30B:**
```
VRAM_kv (GB) ≈ Context_Size × 0.00073
```

---

### 3. VRAM Overhead (Sistemas e Buffers)

```
VRAM_overhead = 512 MB a 1 GB  (depende do framework)
```

Para llama.cpp: **~512 MB**

---

### 4. VRAM Total Necessária

```
VRAM_total = VRAM_modelo + VRAM_kv + VRAM_overhead + VRAM_batch
```

Onde:
```
VRAM_batch = Batch_Size × Context_Size × 0.0002 GB  (estimativa)
```

---

## 🧮 Exemplos Práticos

### Exemplo 1: Qwen3-Coder-30B Q4_K_M, Context 4096

```
VRAM_modelo   = 30B × 0.56      = 16.8 GB
VRAM_kv       = 4096 × 0.00073  = 3.0 GB
VRAM_overhead = 0.5 GB
VRAM_batch    = 1 × 4096 × 0.0002 = 0.8 GB
─────────────────────────────────────────
VRAM_total    ≈ 21.1 GB
```

**GPU Compatível**: RTX 4090 (24GB), RTX 3090 (24GB), A6000 (48GB)

---

### Exemplo 2: Qwen3-Coder-30B Q3_K_M, Context 8192

```
VRAM_modelo   = 30B × 0.44      = 13.2 GB
VRAM_kv       = 8192 × 0.00073  = 6.0 GB
VRAM_overhead = 0.5 GB
VRAM_batch    = 1 × 8192 × 0.0002 = 1.6 GB
─────────────────────────────────────────
VRAM_total    ≈ 21.3 GB
```

---

### Exemplo 3: Qwen3-Coder-30B Q2_K, Context 4096

```
VRAM_modelo   = 30B × 0.31      = 9.3 GB
VRAM_kv       = 4096 × 0.00073  = 3.0 GB
VRAM_overhead = 0.5 GB
VRAM_batch    = 1 × 4096 × 0.0002 = 0.8 GB
─────────────────────────────────────────
VRAM_total    ≈ 13.6 GB
```

**GPU Compatível**: RTX 3060 (12GB), RTX 4060 Ti (16GB), RTX 3080 (10GB com swap)

---

## 🔧 Dimensionamento do Pipeline CORTEX

### VRAM Pipeline vs VRAM Livre

O **CORTEX** usa **threading** para processar arquivos em paralelo, mas cada thread **compartilha** o mesmo servidor LLM. Portanto:

```
VRAM_cortex = VRAM_servidor_llm  (mesma instância)
```

**Não há multiplicação de VRAM por worker!** ✅

---

### Cálculo de Workers Ideais

Os workers do CORTEX são **I/O-bound** (esperam resposta HTTP), não **GPU-bound**:

```python
# Workers não afetam VRAM, apenas throughput
Workers_ideal = min(CPU_cores, 8)  # Default: 4

# A limitação é tempo de resposta do servidor, não VRAM
```

---

### Batch Size vs VRAM

No CORTEX, o `batch_size` define **quantos arquivos são processados juntos**, mas:
- ✅ Um arquivo por vez vai para o LLM
- ✅ Multiple workers = multiple HTTP requests em paralelo
- ❌ Não aumenta VRAM, apenas concorrência

**IMPORTANTE**: Se o servidor LLM usar batch inference (não é o caso padrão do llama.cpp), então:

```
VRAM_extra = Batch_Size × Context_Size × 0.0002 GB
```

Mas para **llama.cpp server padrão**, batch=1 sempre (sequential processing).

---

## 📊 Tabela de Dimensionamento

### GPU 12GB (RTX 3060, RTX 4060 Ti)

| Modelo      | Quant  | Context | VRAM Total | Workers | Batch | Throughput |
|-------------|--------|---------|------------|---------|-------|------------|
| Qwen3-30B   | Q2_K   | 4096    | ~13.6 GB   | ❌      | -     | N/A        |
| Qwen3-30B   | Q3_K_M | 2048    | ~14.2 GB   | ❌      | -     | N/A        |
| Qwen2-7B    | Q4_K_M | 4096    | ~5.2 GB    | ✅ 4    | 10    | ~15/min    |
| Llama3-8B   | Q4_K_M | 4096    | ~5.8 GB    | ✅ 4    | 10    | ~12/min    |

**Recomendação**: Use modelos **7B-8B com Q4_K_M** ou **Q2_K** para 30B.

---

### GPU 24GB (RTX 4090, RTX 3090, A6000)

| Modelo      | Quant  | Context | VRAM Total | Workers | Batch | Throughput |
|-------------|--------|---------|------------|---------|-------|------------|
| Qwen3-30B   | Q4_K_M | 4096    | ~21.1 GB   | ✅ 4    | 10    | ~5-8/min   |
| Qwen3-30B   | Q3_K_M | 8192    | ~21.3 GB   | ✅ 4    | 10    | ~4-6/min   |
| Qwen3-30B   | Q5_K_M | 4096    | ~24.6 GB   | ✅ 2    | 5     | ~3-5/min   |
| Llama3-70B  | Q2_K   | 4096    | ~24.7 GB   | ✅ 2    | 5     | ~2-4/min   |

**Recomendação**: **Q4_K_M com 4096 context** é o sweet spot.

---

### GPU 48GB (A6000, RTX 6000 Ada)

| Modelo      | Quant  | Context | VRAM Total | Workers | Batch | Throughput |
|-------------|--------|---------|------------|---------|-------|------------|
| Qwen3-30B   | Q6_K   | 8192    | ~28.5 GB   | ✅ 8    | 20    | ~10-15/min |
| Qwen3-30B   | Q8_0   | 4096    | ~34.3 GB   | ✅ 8    | 20    | ~8-12/min  |
| Llama3-70B  | Q4_K_M | 4096    | ~45.2 GB   | ✅ 4    | 10    | ~4-6/min   |

**Recomendação**: Use **Q6_K ou Q8_0** para máxima qualidade.

---

## 🎯 Estratégias de Otimização

### 1. **Reduzir VRAM do Modelo**

```bash
# Opção 1: Quantização mais agressiva
Q4_K_M → Q3_K_M  (economiza ~3.6 GB)
Q3_K_M → Q2_K    (economiza ~3.9 GB)

# Opção 2: Modelo menor
30B → 14B        (economiza ~8-10 GB)
14B → 7B         (economiza ~3-4 GB)
```

### 2. **Reduzir Context Size**

```bash
# Cada redução pela metade economiza ~50% do KV cache
8192 → 4096  (economiza ~3 GB)
4096 → 2048  (economiza ~1.5 GB)
```

### 3. **CPU Offloading** (llama.cpp)

```bash
# Descarregar camadas para RAM
llama-server \
  --model modelo.gguf \
  --n-gpu-layers 40  # Só 40 layers na GPU (de 60)
  
# Economiza ~30-40% VRAM, mas reduz velocidade
```

### 4. **Flash Attention** (se disponível)

```bash
# Reduz VRAM do KV cache em ~30-40%
llama-server \
  --model modelo.gguf \
  --flash-attn
```

---

## 🔍 Monitoramento em Tempo Real

### Verificar VRAM Disponível

```bash
# NVIDIA
nvidia-smi --query-gpu=memory.free,memory.total --format=csv

# Durante execução do CORTEX (com -v)
nix develop --command ./cortex.py -i input/ -o output.jsonl -v
# Mostrará warnings de VRAM automaticamente
```

### Scripts de Monitoramento

```bash
# Continuous monitoring
watch -n 1 nvidia-smi

# Com alertas
while true; do
  FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n1)
  if [ $FREE -lt 1024 ]; then
    echo "⚠️  VRAM LOW: ${FREE}MB"
  fi
  sleep 2
done
```

---

## 📝 Checklist de Pré-Execução

Antes de executar o CORTEX, verifique:

```bash
# 1. Verificar VRAM total da GPU
nvidia-smi --query-gpu=memory.total --format=csv

# 2. Calcular VRAM necessária (use fórmulas acima)

# 3. Verificar VRAM livre ANTES de carregar modelo
nvidia-smi --query-gpu=memory.free --format=csv

# 4. Iniciar servidor com configurações apropriadas
python -m llama_cpp.server \
  --model modelo.gguf \
  --n_ctx 4096 \          # Ajuste baseado em cálculo
  --n-gpu-layers -1       # -1 = todas na GPU

# 5. Verificar VRAM APÓS carregar modelo
nvidia-smi

# 6. Calcular VRAM livre para processing headroom
# Deve ter pelo menos 1-2GB livre
```

---

## 🧮 Calculadora Rápida (Python)

Veja o script `vram_calculator.py` que criei para você!

```bash
# Usar a calculadora
python vram_calculator.py \
  --model-size 30 \
  --quantization Q4_K_M \
  --context-size 4096 \
  --gpu-vram 24

# Output:
# VRAM Breakdown:
#   Model:    16.8 GB
#   KV Cache:  3.0 GB
#   Overhead:  0.5 GB
#   Batch:     0.8 GB
#   ─────────────────
#   TOTAL:    21.1 GB
#
# GPU VRAM: 24.0 GB
# Free:      2.9 GB ✅
# Status:    OK - Safe to run
```

---

## 🎓 Regras de Ouro

1. **Reserve 10-15% VRAM livre** para evitar OOM
2. **Context size** é o maior consumidor depois do modelo
3. **Workers no CORTEX não multiplicam VRAM** (compartilham servidor)
4. **Q4_K_M é o melhor custo-benefício** (qualidade vs VRAM)
5. **Monitor em tempo real** durante processamento
6. **Se OOM, reduza context ou quantização**, não workers

---

## 📚 Referências

- [llama.cpp Memory Requirements](https://github.com/ggerganov/llama.cpp#memory-requirements)
- [GGUF Quantization Guide](https://github.com/ggerganov/llama.cpp/blob/master/examples/quantize/README.md)
- [KV Cache Explained](https://kipp.ly/transformer-inference-arithmetic/)

---

**Última Atualização**: 2025-12-10  
**Versão**: 1.0
