# 🔮 PHANTOM CLASSIFIER v2.0

**NSA-Grade Data Classification, Sanitization & Organization Pipeline**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗              ║
║  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║              ║
║  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║              ║
║  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║              ║
║  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║              ║
║  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 🎯 Overview

PHANTOM CLASSIFIER é um pipeline DAG de nível enterprise para:

- **Classificação Inteligente**: Multi-level detection (magic bytes + extensão + análise)
- **Pseudonimização**: Mapeamento reversível criptograficamente seguro
- **Verificação de Integridade**: SHA256 + BLAKE3 + xxHash
- **Detecção de Dados Sensíveis**: 20+ padrões (PII, credenciais, chaves)
- **Sanitização**: Strip metadata, redact PII, full sanitization
- **Audit Trail**: Chain of custody completa em SQLite
- **Paralelização**: Processamento multi-thread com DAG dependencies

## 🚀 Quick Start

```bash
# Entre no ambiente Nix
nix develop

# Processar dados
phantom -i /path/to/messy/data -o /path/to/organized -v

# Dry run (simular sem mover)
phantom -i ./input -o ./output --dry-run

# Ver relatório
phantom-report ./organized
```

## 📦 Instalação

### Via Nix Flake (Recomendado)

```bash
# Clonar ou copiar o flake
cd phantom-classifier

# Entrar no dev shell
nix develop

# Ou executar diretamente
nix run .#phantom -- -i ./input -o ./output
```

### Dependências Manuais (sem Nix)

```bash
# Python 3.10+
pip install pandas numpy pyarrow python-magic chardet pynacl rich tqdm

# System tools
sudo apt install jq miller ripgrep fd-find exiftool b3sum
```

## 📖 Comandos

### `phantom` - Pipeline Principal

```bash
phantom -i <input> -o <output> [options]

Options:
  -i, --input     Diretório de entrada (obrigatório)
  -o, --output    Diretório de saída (obrigatório)
  -w, --workers   Número de workers (default: CPU count)
  -v, --verbose   Output detalhado
  --dry-run       Simular sem mover arquivos
  --resolve       Resolver pseudônimo para path original
```

### `phantom-dag` - DAG Orchestrator (Avançado)

```bash
phantom-dag -i <input> -o <output> [options]

Options:
  --sanitize      Política de sanitização:
                  none   - Cópia direta
                  strip  - Remove metadata (default)
                  pii    - Redact PII patterns
                  full   - Sanitização completa
```

### Ferramentas Auxiliares

```bash
# Gerar manifest de hashes
phantom-hash ./directory > manifest.json

# Verificar integridade
phantom-verify arquivo.pdf abc123def456...

# Scanner de dados sensíveis
phantom-scan ./directory

# Visualizar relatório
phantom-report ./output
```

## 🏗️ Arquitetura

### Pipeline DAG

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  DISCOVERY  │────▶│ FINGERPRINT  │────▶│  CLASSIFY   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                    ┌──────────────────────────┘
                    ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   VERIFY    │◀────│  SANITIZE    │◀────│ PSEUDONYM   │
└─────────────┘     └──────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   PERSIST   │────▶│   REPORT     │
└─────────────┘     └──────────────┘
```

### Estrutura de Output

```
output/
├── documents/          # PDFs, DOCx, TXT, MD...
├── images/             # PNG, JPG, GIF, SVG...
├── audio/              # MP3, FLAC, WAV...
├── video/              # MP4, MKV, AVI...
├── code/               # PY, JS, RS, GO, NIX...
├── data/               # JSON, CSV, PARQUET, DB...
├── archives/           # ZIP, TAR, 7Z...
├── configs/            # ENV, CONF, INI...
├── logs/               # LOG, OUT, ERR...
├── crypto/             # PEM, KEY, P12...
├── executables/        # ELF, EXE, DEB...
├── unknown/            # Não classificados
└── .phantom/
    ├── phantom.db          # SQLite com records
    ├── pseudonym_map.json  # Mapeamento reversível
    ├── reports/            # Relatórios JSON
    ├── logs/               # Logs de execução
    ├── audit/              # Audit trail
    ├── staging/            # Área temporária
    └── quarantine/         # Arquivos com falha
```

## 🔐 Segurança

### Hash Algorithms

| Algorithm | Purpose | Speed |
|-----------|---------|-------|
| SHA256 | Primary integrity | Medium |
| BLAKE3 | Fast verification | Fast |
| xxHash | Streaming check | Fastest |

### Pseudonymization

```
Original:   /home/user/docs/secret_report_2024.pdf
Pseudonym:  PH-a1b2c3d4-e5f6a7b8-1234abcd.pdf
            │  │        │         │
            │  │        │         └─ Timestamp (hex)
            │  │        └─ Random component
            │  └─ Path hash (deterministic)
            └─ Prefix
```

### Sensitive Pattern Detection

- **PII**: Email, Phone, SSN, CPF/CNPJ (BR), Credit Card
- **Credentials**: Passwords, API Keys, Bearer Tokens
- **Cloud**: AWS Access Keys, Connection Strings
- **Crypto**: Private Keys, Certificates, PGP Keys
- **Network**: IP Addresses, UUIDs

## 📊 Exemplo de Relatório

```json
{
  "phantom_version": "2.0.0",
  "statistics": {
    "total_files": 15420,
    "processed": 15398,
    "failed": 22,
    "success_rate": "99.86%",
    "total_size_human": "48.32 GB",
    "duration_seconds": "127.45",
    "throughput_files_per_sec": "120.81",
    "files_with_sensitive_data": 847
  },
  "classification_breakdown": {
    "documents": 3421,
    "images": 5842,
    "code": 2156,
    "data": 1893,
    "archives": 987,
    "configs": 534
  },
  "sensitivity_breakdown": {
    "PUBLIC": 12453,
    "INTERNAL": 1892,
    "CONFIDENTIAL": 734,
    "SECRET": 289,
    "TOP_SECRET": 30
  }
}
```

## 🔧 Customização

### Adicionar Novos Padrões Sensíveis

Edite `SENSITIVE_PATTERNS` em `phantom_dag.py`:

```python
SENSITIVE_PATTERNS = [
    # (regex, nome, risk_score)
    (r'seu_pattern_aqui', 'nome_pattern', 0.8),
]
```

### Adicionar Novas Classificações

Edite `EXT_MAP` em `phantom_dag.py`:

```python
EXT_MAP = {
    '.nova_ext': Classification.CATEGORIA,
}
```

## 🧪 Casos de Uso

### 1. Organizar Backup Antigo

```bash
phantom -i /mnt/backup_2020 -o /mnt/organized_backup -w 8 -v
```

### 2. Sanitizar Dados para Compartilhamento

```bash
phantom-dag -i ./dados_internos -o ./para_cliente --sanitize pii
```

### 3. Auditoria de Dados Sensíveis

```bash
phantom-scan /home/user/projects | jq '.findings | .[] | select(.risk_score > 0.7)'
```

### 4. Verificação de Integridade Pós-Transfer

```bash
# Gerar manifest antes
phantom-hash ./original > manifest_before.json

# Após transferência
phantom-hash ./transferred > manifest_after.json

# Comparar
diff <(jq -S . manifest_before.json) <(jq -S . manifest_after.json)
```

## 🛡️ Limitações

- Arquivos > 10MB não são scaneados para conteúdo sensível
- Arquivos criptografados não podem ser classificados por conteúdo
- Alguns formatos proprietários podem não ter metadata stripping

## 📜 License

MIT License - Use por sua conta e risco.

## 🤝 Contributing

Pull requests são bem-vindos. Para mudanças maiores, abra uma issue primeiro.

---

*Desenvolvido com 🧠 para profissionais de segurança e engenheiros de dados que precisam de organização cirúrgica.*
