#!/bin/bash
# cortex_demo.sh - Demonstração do CORTEX ETL Pipeline

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  CORTEX v1.0 - Demo Script                                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar se está no ambiente Nix
if ! command -v python &> /dev/null || ! python -c "import pydantic" 2>/dev/null; then
    echo "⚠️  Ambiente Nix não detectado. Executando 'nix develop'..."
    exec nix develop --command bash "$0" "$@"
fi

# Criar diretório de exemplo
DEMO_DIR="demo_cortex"
mkdir -p "$DEMO_DIR/input"
mkdir -p "$DEMO_DIR/output"

echo "📁 Criando arquivos markdown de exemplo em $DEMO_DIR/input/"
echo ""

# Criar exemplo 1: Guia de desenvolvimento
cat > "$DEMO_DIR/input/dev_guide.md" << 'EOF'
# Development Best Practices Guide

## Introduction

This guide covers essential development practices for our team.

## Code Quality

### Testing
Always write tests before implementing features (TDD approach). Tests should cover:
- Happy path scenarios
- Edge cases
- Error handling

### Code Review
All code must go through peer review. Key points:
1. Check for security vulnerabilities
2. Verify coding standards compliance
3. Ensure adequate documentation

## Architecture Patterns

### Microservices
We use a microservices architecture with the following patterns:
- Event-driven communication
- API Gateway pattern
- Circuit breaker for resilience

### Database
Prefer PostgreSQL for relational data. Use Redis for caching.

## Security Recommendations

1. **Never commit secrets** - Use environment variables
2. **Input validation** - Sanitize all user inputs
3. **HTTPS only** - All communication must be encrypted
4. **Regular updates** - Keep dependencies up to date

## Key Learnings

Through our development process, we've learned that:
- Early testing saves time later
- Documentation is as important as code
- Security should be considered from day one
EOF

# Criar exemplo 2: Troubleshooting
cat > "$DEMO_DIR/input/troubleshooting.md" << 'EOF'
# System Troubleshooting Guide

## Common Issues

### Database Connection Errors

**Problem**: Application cannot connect to database

**Pattern**: This occurs frequently after system restarts

**Solution Steps**:
1. Check if database service is running
2. Verify connection string configuration
3. Test network connectivity
4. Review firewall rules

**Implementation Effort**: Low
**Category**: Infrastructure

### Memory Leaks

**Concept**: Memory leak occurs when application doesn't properly release memory

**Related Concepts**:
- Garbage collection
- Resource management
- Performance monitoring

**Recommendation**: Use profiling tools like valgrind or memory-profiler to identify leaks early.

### API Rate Limiting

**Pattern Type**: Workflow
**Description**: Implement exponential backoff when hitting rate limits

**Example**:
```python
import time

def retry_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except RateLimitError:
            time.sleep(2 ** i)
```

## Best Practices

1. **Monitor system resources** - Set up alerts for CPU, memory, disk usage
2. **Log aggregation** - Centralize logs for easier debugging
3. **Automated backups** - Schedule daily backups with verification

## Key Takeaways

- Prevention is better than cure - invest in monitoring
- Document all incidents and solutions
- Automation reduces human error
EOF

echo "✅ Arquivos de exemplo criados:"
echo "   - $DEMO_DIR/input/dev_guide.md"
echo "   - $DEMO_DIR/input/troubleshooting.md"
echo ""

# Verificar se o servidor llamacpp está rodando
echo "🔍 Verificando servidor llamacpp em http://localhost:8080..."
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Servidor detectado!"
    echo ""
    
    # Executar CORTEX
    echo "🚀 Executando CORTEX..."
    echo ""
    ./cortex.py -i "$DEMO_DIR/input" -o "$DEMO_DIR/output/insights.jsonl" -v
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📊 RESULTADOS"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    
    if [ -f "$DEMO_DIR/output/insights.jsonl" ]; then
        LINE_COUNT=$(wc -l < "$DEMO_DIR/output/insights.jsonl")
        echo "✅ Arquivo de saída criado: $DEMO_DIR/output/insights.jsonl"
        echo "   Total de linhas processadas: $LINE_COUNT"
        echo ""
        
        echo "📝 Exemplo da primeira extração:"
        echo ""
        head -n 1 "$DEMO_DIR/output/insights.jsonl" | python -m json.tool 2>/dev/null || cat "$DEMO_DIR/output/insights.jsonl" | head -n 1
    else
        echo "⚠️  Arquivo de saída não foi criado"
    fi
    
else
    echo "❌ Servidor llamacpp não encontrado!"
    echo ""
    echo "Para executar este demo, você precisa:"
    echo ""
    echo "1. Iniciar o servidor llamacpp:"
    echo "   python -m llama_cpp.server \\"
    echo "     --model /caminho/para/modelo.gguf \\"
    echo "     --n_ctx 4096 \\"
    echo "     --host 0.0.0.0 \\"
    echo "     --port 8080"
    echo ""
    echo "2. Depois executar novamente este script"
    echo ""
    echo "Ou você pode executar o CORTEX manualmente depois:"
    echo "   ./cortex.py -i $DEMO_DIR/input -o $DEMO_DIR/output/insights.jsonl -v"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "📚 PRÓXIMOS PASSOS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "1. Analise os resultados em: $DEMO_DIR/output/insights.jsonl"
echo "2. Cada linha é um arquivo processado com insights estruturados"
echo "3. Use as extrações para:"
echo "   - Construir knowledge graphs"
echo "   - Gerar embeddings para busca semântica"
echo "   - Criar dashboards de insights"
echo "   - Alimentar sistemas de recomendação"
echo ""
