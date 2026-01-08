#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORTEX v2.0 - Component Tests

Tests for chunking and embeddings functionality
"""

import sys
from pathlib import Path
from typing import List
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from phantom.rag.cortex_chunker import MarkdownChunker, ChunkStrategy, Chunk
from phantom.rag.cortex_embeddings import EmbeddingManager, SearchResult


# ═══════════════════════════════════════════════════════════════
# TEST DATA
# ═══════════════════════════════════════════════════════════════

TEST_DOCUMENT = """# Python Error Handling Guide

## Introduction

Error handling is crucial for robust applications. Python provides several mechanisms for handling errors gracefully.

## Try-Except Blocks

The most common way to handle errors in Python is using try-except blocks:

```python
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero")
```

## Multiple Exception Types

You can catch multiple exception types:

```python
try:
    value = int("not a number")
except (ValueError, TypeError) as e:
    print(f"Error: {e}")
```

## Finally Clause

Use finally for cleanup code that must run:

```python
try:
    file = open("data.txt")
    # process file
finally:
    file.close()
```

## Best Practices

1. Catch specific exceptions, not generic Exception
2. Use logging instead of print statements
3. Clean up resources in finally blocks
4. Don't use exceptions for flow control

## Context Managers

Modern Python prefers context managers:

```python
with open("data.txt") as file:
    content = file.read()
# File automatically closed
```

## Custom Exceptions

Define custom exceptions for domain-specific errors:

```python
class InvalidUserError(Exception):
    pass

def validate_user(user):
    if not user:
        raise InvalidUserError("User cannot be empty")
```

## Conclusion

Proper error handling makes your code more reliable and maintainable.
"""


# ═══════════════════════════════════════════════════════════════
# CHUNKING TESTS
# ═══════════════════════════════════════════════════════════════

def test_chunking_strategies():
    """Test all chunking strategies"""
    print("=" * 70)
    print("CHUNKING TESTS")
    print("=" * 70)
    
    strategies = [
        ("recursive", ChunkStrategy.RECURSIVE),
        ("sliding", ChunkStrategy.SLIDING),
        ("simple", ChunkStrategy.SIMPLE)
    ]
    
    results = {}
    
    for name, strategy in strategies:
        print(f"\n🧪 Testing {name.upper()} strategy...")
        
        chunker = MarkdownChunker(
            strategy=strategy,
            max_tokens=200,
            overlap=50
        )
        
        start = time.time()
        chunks = chunker.chunk_text(TEST_DOCUMENT, source_file="test.md")
        elapsed = time.time() - start
        
        stats = chunker.get_stats(chunks)
        
        print(f"   ✓ Chunks created: {len(chunks)}")
        print(f"   ✓ Total tokens: {stats['total_tokens']}")
        print(f"   ✓ Avg tokens/chunk: {stats['avg_tokens_per_chunk']:.1f}")
        print(f"   ✓ Processing time: {elapsed*1000:.1f}ms")
        
        # Validation
        assert len(chunks) > 0, f"{name} produced no chunks"
        assert all(chunk.metadata.token_count > 0 for chunk in chunks), f"{name} has chunks with no tokens"
        
        results[name] = {
            "chunks": len(chunks),
            "tokens": stats['total_tokens'],
            "time_ms": elapsed * 1000
        }
    
    print(f"\n{'─' * 70}")
    print("📊 CHUNKING SUMMARY")
    print(f"{'─' * 70}")
    print(f"{'Strategy':<15} {'Chunks':<10} {'Tokens':<10} {'Time (ms)':<10}")
    print(f"{'─' * 70}")
    for name, data in results.items():
        print(f"{name.capitalize():<15} {data['chunks']:<10} {data['tokens']:<10} {data['time_ms']:<10.1f}")
    
    return True


def test_chunk_metadata():
    """Test chunk metadata preservation"""
    print(f"\n{'=' * 70}")
    print("METADATA TESTS")
    print("=" * 70)
    
    chunker = MarkdownChunker(strategy=ChunkStrategy.RECURSIVE, max_tokens=200)
    chunks = chunker.chunk_text(TEST_DOCUMENT, source_file="test.md")
    
    print(f"\n🧪 Testing metadata preservation...")
    
    for i, chunk in enumerate(chunks[:3]):  # Test first 3 chunks
        print(f"\n   Chunk {i+1}:")
        print(f"   ✓ ID: {chunk.metadata.chunk_id}")
        print(f"   ✓ Source: {chunk.metadata.source_file}")
        print(f"   ✓ Tokens: {chunk.metadata.token_count}")
        print(f"   ✓ Words: {chunk.metadata.word_count}")
        print(f"   ✓ Headers: {chunk.metadata.headers}")
        
        # Validation
        assert chunk.metadata.chunk_id == i
        assert chunk.metadata.source_file == "test.md"
        assert chunk.metadata.token_count > 0
        assert chunk.metadata.word_count > 0
    
    print(f"\n   ✅ All metadata tests passed!")
    return True


# ═══════════════════════════════════════════════════════════════
# EMBEDDINGS TESTS
# ═══════════════════════════════════════════════════════════════

def test_embedding_generation():
    """Test embedding generation"""
    print(f"\n{'=' * 70}")
    print("EMBEDDING TESTS")
    print("=" * 70)
    
    # Create sample texts
    texts = [
        "Error handling in Python uses try-except blocks",
        "FastAPI supports async/await for better performance",
        "Use context managers for resource cleanup",
        "Python is a high-level programming language"
    ]
    
    print(f"\n🧪 Testing embedding generation...")
    print(f"   Texts to embed: {len(texts)}")
    
    manager = EmbeddingManager(model_name="all-MiniLM-L6-v2", device="cpu")
    
    start = time.time()
    manager.add_texts(texts)
    elapsed = time.time() - start
    
    print(f"   ✓ Embeddings generated: {len(manager.vector_store)}")
    print(f"   ✓ Embedding dimension: {manager.generator.embedding_dim}")
    print(f"   ✓ Processing time: {elapsed*1000:.1f}ms")
    print(f"   ✓ Speed: {len(texts)/(elapsed if elapsed > 0 else 0.001):.1f} embeddings/sec")
    
    # Validation
    assert len(manager.vector_store) == len(texts)
    assert manager.generator.embedding_dim == 384  # MiniLM dimension
    
    return manager


def test_semantic_search(manager: EmbeddingManager):
    """Test semantic search functionality"""
    print(f"\n{'=' * 70}")
    print("SEMANTIC SEARCH TESTS")
    print("=" * 70)
    
    queries = [
        "How to handle exceptions?",
        "Asynchronous programming",
        "Managing files and resources"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        
        start = time.time()
        results = manager.search(query, top_k=3)
        elapsed = time.time() - start
        
        print(f"   ⏱️  Search time: {elapsed*1000:.1f}ms")
        print(f"   📊 Top {len(results)} results:")
        
        for i, result in enumerate(results, 1):
            print(f"\n   {i}. Score: {result.score:.3f}")
            print(f"      Text: {result.text[:60]}...")
        
        # Validation
        assert len(results) > 0, "Search returned no results"
        assert all(r.score >= 0 and r.score <= 1 for r in results), "Invalid scores"
        assert results[0].score >= results[-1].score, "Results not sorted by score"
    
    print(f"\n   ✅ All search tests passed!")
    return True


def test_similarity_ranking():
    """Test that similar texts rank higher"""
    print(f"\n{'=' * 70}")
    print("SIMILARITY RANKING TESTS")
    print("=" * 70)
    
    texts = [
        "Python error handling with try-except blocks",  # Most similar
        "Exception handling is important in Python",    # Similar
        "FastAPI web framework for Python",              # Less similar
        "JavaScript async functions"                     # Least similar
    ]
    
    manager = EmbeddingManager(model_name="all-MiniLM-L6-v2")
    manager.add_texts(texts)
    
    query = "How to handle errors in Python?"
    results = manager.search(query, top_k=4)
    
    print(f"\n🧪 Query: '{query}'")
    print(f"\n   Expected order: Error handling topics first\n")
    
    for i, result in enumerate(results, 1):
        relevance = "🟢" if i <= 2 else "🟡" if i == 3 else "🔴"
        print(f"   {relevance} Rank {i} (score: {result.score:.3f}): {result.text[:50]}...")
    
    # Validation: Top result should be most relevant
    assert "error" in results[0].text.lower() or "exception" in results[0].text.lower()
    print(f"\n   ✅ Ranking test passed!")
    
    return True


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════

def test_chunking_plus_embeddings():
    """Test full pipeline: chunk → embed → search"""
    print(f"\n{'=' * 70}")
    print("INTEGRATION TEST: Chunking + Embeddings")
    print("=" * 70)
    
    print(f"\n🧪 Testing full pipeline...")
    
    # Step 1: Chunk document
    print(f"\n   Step 1: Chunking document...")
    chunker = MarkdownChunker(strategy=ChunkStrategy.RECURSIVE, max_tokens=150)
    chunks = chunker.chunk_text(TEST_DOCUMENT, source_file="test.md")
    print(f"   ✓ Created {len(chunks)} chunks")
    
    # Step 2: Generate embeddings
    print(f"\n   Step 2: Generating embeddings...")
    manager = EmbeddingManager(model_name="all-MiniLM-L6-v2")
    
    chunk_texts = [chunk.text for chunk in chunks]
    chunk_metadata = [
        {
            "chunk_id": chunk.metadata.chunk_id,
            "source_file": chunk.metadata.source_file,
            "headers": chunk.metadata.headers
        }
        for chunk in chunks
    ]
    
    manager.add_texts(chunk_texts, metadata=chunk_metadata)
    print(f"   ✓ Embedded {len(manager.vector_store)} chunks")
    
    # Step 3: Semantic search
    print(f"\n   Step 3: Testing semantic search...")
    queries = [
        "try-except syntax",
        "resource cleanup",
        "custom exceptions"
    ]
    
    for query in queries:
        results = manager.search(query, top_k=2)
        print(f"\n   Query: '{query}'")
        print(f"   → Top result: {results[0].text[:50]}... (score: {results[0].score:.3f})")
        
        assert len(results) > 0
    
    print(f"\n   ✅ Integration test passed!")
    return True


# ═══════════════════════════════════════════════════════════════
# MAIN TEST RUNNER
# ═══════════════════════════════════════════════════════════════

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print(" " * 15 + "🧪 CORTEX v2.0 COMPONENT TESTS")
    print("=" * 70 + "\n")
    
    tests_passed = 0
    tests_failed = 0
    
    tests = [
        ("Chunking Strategies", test_chunking_strategies),
        ("Chunk Metadata", test_chunk_metadata),
        ("Embedding Generation", test_embedding_generation),
        ("Similarity Ranking", test_similarity_ranking),
        ("Integration Pipeline", test_chunking_plus_embeddings)
    ]
    
    for name, test_func in tests:
        try:
            if name == "Embedding Generation":
                # This test returns the manager for next test
                manager = test_func()
                # Run semantic search with the manager
                test_semantic_search(manager)
                tests_passed += 2
            else:
                test_func()
                tests_passed += 1
        except Exception as e:
            print(f"\n   ❌ Test failed: {e}")
            tests_failed += 1
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print(" " * 20 + "📊 TEST SUMMARY")
    print("=" * 70)
    print(f"\n   ✅ Tests passed: {tests_passed}")
    print(f"   ❌ Tests failed: {tests_failed}")
    print(f"   📈 Success rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")
    print("\n" + "=" * 70 + "\n")
    
    return tests_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
