# 🎯 Resumo Rápido: VRAM e CORTEX Pipeline

## 📐 Fórmula Essencial

```
VRAM_total = VRAM_modelo + VRAM_kv_cache + 0.5GB

Onde:
  VRAM_modelo    = Parâmetros_B × Fator_Quantização
  VRAM_kv_cache  = Context_Size × 0.00073  (para modelos ~30B)
```

## 🎮 Seu Modelo: Qwen3-Coder-30B

### Cenários Comuns

| Quantização | Context | VRAM Total | GPU Mínima | Workers | Status |
|-------------|---------|------------|------------|---------|--------|
| **Q2_K**    | 4096    | ~10.4 GB   | 12GB       | 4       | 🟡 Tight |
| **Q3_K_M**  | 4096    | ~13.8 GB   | 16GB       | 4       | 🟢 OK    |
| **Q4_K_M**  | 4096    | ~17.9 GB   | 24GB       | 4       | 🟢 OK    |
| **Q4_K_M**  | 8192    | ~21.1 GB   | 24GB       | 4       | 🟡 Tight |
| **Q5_K_M**  | 4096    | ~21.2 GB   | 24GB       | 2       | 🟡 Tight |

## ⚡ Resposta Direta: Workers e VRAM

**❗ IMPORTANTE**: No CORTEX, os **workers NÃO multiplicam VRAM**!

```
✅ 1 worker  = 17.9 GB VRAM
✅ 4 workers = 17.9 GB VRAM  (mesma!)
✅ 8 workers = 17.9 GB VRAM  (mesma!)
```

**Por quê?**
- Todos os workers **compartilham** o mesmo servidor LLM
- Workers são I/O-bound (esperam resposta HTTP)
- O servidor processa 1 request por vez (batch=1)

## 🔧 Configurar Workers

**Base o número de workers em CPU, não VRAM:**

```bash
# CPU cores: 8
# VRAM: 24GB com Q4_K_M = OK

./cortex.py -i input/ -o output.jsonl \
  --workers 8        # ✅ OK - não afeta VRAM
  --batch-size 20    # ✅ OK - só agrupa arquivos localmente
```

**Regra de ouro:**
```
Workers_ideal = min(CPU_cores, 8)
```

## 📊 Usar a Calculadora

```bash
# Seu setup
python vram_calculator.py \
  --model-size 30 \
  --quantization Q4_K_M \
  --context-size 4096 \
  --gpu-vram 24

# Output:
# VRAM Usage:
#   Model:     16.80 GB
#   KV Cache:   0.59 GB
#   Overhead:   0.50 GB
#   ──────────────────
#   TOTAL:     17.89 GB
#
# GPU VRAM:   24.00 GB
# Free:        6.11 GB ✅
# Status:      OK - Safe to run
```

## 🎯 Recomendações para Você

### Se você tem GPU 24GB (RTX 4090/3090):

```bash
# Configuração ideal
Model:      Qwen3-Coder-30B
Quant:      Q4_K_M
Context:    4096
Workers:    4-8 (baseado em CPU cores)
Batch:      10-20
Throughput: ~5-8 arquivos/min
```

### Se você tem GPU 12GB (RTX 3060/4060Ti):

```bash
# Opção 1: Modelo menor
Model:      Qwen2-7B ou Llama3-8B
Quant:      Q4_K_M
Context:    4096
Workers:    4
Throughput: ~12-15 arquivos/min

# Opção 2: Quantização agressiva
Model:      Qwen3-Coder-30B
Quant:      Q2_K
Context:    2048-4096
Workers:    2-4
Throughput: ~3-5 arquivos/min
```

## 🔍 Como Monitorar

```bash
# Durante execução do CORTEX
nix develop --command ./cortex.py -i input/ -o output.jsonl -v

# Em outro terminal, monitore VRAM
watch -n 1 nvidia-smi
```

O CORTEX já tem monitoramento built-in que avisa se:
- 🟡 VRAM livre < 512MB: Warning
- 🔴 VRAM livre < 256MB: Pausa automática

## ⚙️ Ajustar se Necessário

### Reduzir VRAM do modelo:
```bash
# Q4_K_M → Q3_K_M: economiza ~3.6 GB
# Q3_K_M → Q2_K:   economiza ~3.9 GB
```

### Reduzir Context Size:
```bash
# 8192 → 4096: economiza ~3 GB
# 4096 → 2048: economiza ~1.5 GB
```

### CPU Offloading:
```bash
# Mover algumas layers para RAM
python -m llama_cpp.server \
  --model modelo.gguf \
  --n-gpu-layers 40  # Só 40 de 60 layers na GPU
  
# Economiza ~30% VRAM, mas perde ~40% velocidade
```

## 🎓 TL;DR - Perguntas Frequentes

**Q: Posso usar 8 workers se tenho 24GB?**
✅ SIM! Workers não afetam VRAM. Se o modelo cabe, pode usar quantos workers quiser (limitado apenas por CPU).

**Q: Batch size afeta VRAM?**
❌ NÃO no CORTEX! O batch_size só agrupa arquivos localmente. O servidor LLM processa 1 por vez.

**Q: Como saber se cabe?**
✅ Use: `python vram_calculator.py -m 30 -q Q4_K_M -c 4096 --auto-detect`

**Q: O que fazer se não caber?**
1. Reduza quantização (Q4→Q3→Q2)
2. Reduza context (8192→4096→2048)
3. Use modelo menor (30B→13B→7B)
4. CPU offloading (parcial na GPU)

**Q: Quanto VRAM livre devo reservar?**
✅ Ideal: 2-4 GB livre para sistema e overhead

---

📚 **Documentação Completa**: `VRAM_CALCULATOR.md`  
🧮 **Calculadora**: `python vram_calculator.py --interactive`  
📊 **Quick Ref**: `CORTEX_QUICKREF.txt`
