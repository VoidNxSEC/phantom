#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORTEX v2.0 - Semantic Chunking Module

Intelligent text chunking strategies for markdown documents to enable:
- Reduced VRAM usage (smaller chunks vs full documents)
- Better semantic coherence
- Parallel processing optimization
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
import tiktoken

# Try langchain import (optional for advanced splitting)
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  langchain not available, using basic chunking")


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DEFAULT_CHUNK_SIZE = 1024  # tokens
DEFAULT_OVERLAP = 128      # tokens
DEFAULT_ENCODING = "cl100k_base"  # GPT-4 tokenizer


class ChunkStrategy(str, Enum):
    """Chunking strategy options"""
    RECURSIVE = "recursive"      # Split by headers, respecting structure
    SLIDING = "sliding"          # Fixed-size sliding window
    SEMANTIC = "semantic"        # Semantic boundary detection
    SIMPLE = "simple"            # Simple token limit splitting


# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ChunkMetadata:
    """Metadata for a text chunk"""
    source_file: str
    chunk_id: int
    start_offset: int
    end_offset: int
    headers: List[str] = field(default_factory=list)  # H1, H2, H3 hierarchy
    word_count: int = 0
    token_count: int = 0
    has_code: bool = False
    has_lists: bool = False


@dataclass
class Chunk:
    """Text chunk with metadata"""
    text: str
    metadata: ChunkMetadata
    
    def __len__(self) -> int:
        return self.metadata.token_count
    
    def __str__(self) -> str:
        return f"Chunk[{self.metadata.chunk_id}]: {len(self)} tokens"


# ═══════════════════════════════════════════════════════════════
# TOKEN COUNTING
# ═══════════════════════════════════════════════════════════════

class TokenCounter:
    """Token counting utility using tiktoken"""
    
    def __init__(self, encoding_name: str = DEFAULT_ENCODING):
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            print(f"⚠️  Error loading tiktoken: {e}, using approximate counting")
            self.encoding = None
    
    def count(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Approximate: 1 token ≈ 4 characters
            return len(text) // 4
    
    def encode(self, text: str) -> List[int]:
        """Encode text to tokens"""
        if self.encoding:
            return self.encoding.encode(text)
        else:
            return []
    
    def decode(self, tokens: List[int]) -> str:
        """Decode tokens to text"""
        if self.encoding:
            return self.encoding.decode(tokens)
        else:
            return ""


# ═══════════════════════════════════════════════════════════════
# CHUNKING STRATEGIES
# ═══════════════════════════════════════════════════════════════

class RecursiveMarkdownChunker:
    """
    Split markdown by headers while respecting semantic structure
    
    Strategy:
    1. Parse header hierarchy (H1 -> H2 -> H3)
    2. Split at headers if section exceeds max_tokens
    3. Preserve header context in chunks
    4. Add overlap between chunks
    """
    
    def __init__(self, max_tokens: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.token_counter = TokenCounter()
    
    def extract_headers(self, text: str) -> List[Tuple[int, str, str]]:
        """
        Extract headers with their level and position
        Returns: [(position, level, text), ...]
        """
        headers = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE):
            level = len(match.group(1))
            header_text = match.group(2).strip()
            position = match.start()
            headers.append((position, level, header_text))
        return headers
    
    def split_by_headers(self, text: str, source_file: str) -> List[Chunk]:
        """Split text by markdown headers"""
        headers = self.extract_headers(text)
        
        if not headers:
            # No headers, fall back to sliding window
            return SlidingWindowChunker(self.max_tokens, self.overlap).chunk(text, source_file)
        
        chunks = []
        header_stack = []  # Track current header hierarchy
        
        for i, (pos, level, header_text) in enumerate(headers):
            # Update header stack
            header_stack = [h for h in header_stack if h[0] < level] + [(level, header_text)]
            
            # Determine section boundaries
            start_pos = pos
            end_pos = headers[i + 1][0] if i + 1 < len(headers) else len(text)
            
            section_text = text[start_pos:end_pos]
            section_tokens = self.token_counter.count(section_text)
            
            # If section fits, create single chunk
            if section_tokens <= self.max_tokens:
                metadata = ChunkMetadata(
                    source_file=source_file,
                    chunk_id=len(chunks),
                    start_offset=start_pos,
                    end_offset=end_pos,
                    headers=[h[1] for h in header_stack],
                    token_count=section_tokens,
                    word_count=len(section_text.split())
                )
                chunks.append(Chunk(text=section_text, metadata=metadata))
            else:
                # Section too large, split with sliding window
                sub_chunks = self._split_large_section(
                    section_text, 
                    source_file, 
                    start_pos,
                    [h[1] for h in header_stack],
                    len(chunks)
                )
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _split_large_section(
        self, 
        text: str, 
        source_file: str, 
        base_offset: int,
        headers: List[str],
        start_chunk_id: int
    ) -> List[Chunk]:
        """Split large section using sliding window"""
        chunks = []
        tokens = self.token_counter.encode(text)
        
        for i in range(0, len(tokens), self.max_tokens - self.overlap):
            chunk_tokens = tokens[i:i + self.max_tokens]
            chunk_text = self.token_counter.decode(chunk_tokens)
            
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_id=start_chunk_id + len(chunks),
                start_offset=base_offset + i,
                end_offset=base_offset + i + len(chunk_tokens),
                headers=headers,
                token_count=len(chunk_tokens),
                word_count=len(chunk_text.split())
            )
            chunks.append(Chunk(text=chunk_text, metadata=metadata))
        
        return chunks
    
    def chunk(self, text: str, source_file: str) -> List[Chunk]:
        """Main chunking method"""
        return self.split_by_headers(text, source_file)


class SlidingWindowChunker:
    """
    Fixed-size sliding window chunking with overlap
    
    Simple but effective for documents without clear structure
    """
    
    def __init__(self, max_tokens: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.token_counter = TokenCounter()
    
    def chunk(self, text: str, source_file: str) -> List[Chunk]:
        """Split text into overlapping chunks"""
        chunks = []
        tokens = self.token_counter.encode(text)
        
        for i in range(0, len(tokens), self.max_tokens - self.overlap):
            chunk_tokens = tokens[i:i + self.max_tokens]
            chunk_text = self.token_counter.decode(chunk_tokens)
            
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_id=len(chunks),
                start_offset=i,
                end_offset=i + len(chunk_tokens),
                token_count=len(chunk_tokens),
                word_count=len(chunk_text.split())
            )
            chunks.append(Chunk(text=chunk_text, metadata=metadata))
        
        return chunks


class SimpleChunker:
    """
    Simple chunking by token limit without overlap
    Fastest but lowest quality
    """
    
    def __init__(self, max_tokens: int = DEFAULT_CHUNK_SIZE):
        self.max_tokens = max_tokens
        self.token_counter = TokenCounter()
    
    def chunk(self, text: str, source_file: str) -> List[Chunk]:
        """Split text into non-overlapping chunks"""
        chunks = []
        tokens = self.token_counter.encode(text)
        
        for i in range(0, len(tokens), self.max_tokens):
            chunk_tokens = tokens[i:i + self.max_tokens]
            chunk_text = self.token_counter.decode(chunk_tokens)
            
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_id=len(chunks),
                start_offset=i,
                end_offset=i + len(chunk_tokens),
                token_count=len(chunk_tokens),
                word_count=len(chunk_text.split())
            )
            chunks.append(Chunk(text=chunk_text, metadata=metadata))
        
        return chunks


# ═══════════════════════════════════════════════════════════════
# MAIN CHUNKER INTERFACE
# ═══════════════════════════════════════════════════════════════

class MarkdownChunker:
    """
    Main chunker interface with strategy selection
    """
    
    def __init__(
        self,
        strategy: ChunkStrategy = ChunkStrategy.RECURSIVE,
        max_tokens: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP
    ):
        self.strategy = strategy
        self.max_tokens = max_tokens
        self.overlap = overlap
        
        # Initialize appropriate chunker
        if strategy == ChunkStrategy.RECURSIVE:
            self.chunker = RecursiveMarkdownChunker(max_tokens, overlap)
        elif strategy == ChunkStrategy.SLIDING:
            self.chunker = SlidingWindowChunker(max_tokens, overlap)
        elif strategy == ChunkStrategy.SIMPLE:
            self.chunker = SimpleChunker(max_tokens)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def chunk_text(self, text: str, source_file: str = "unknown") -> List[Chunk]:
        """Chunk text using selected strategy"""
        return self.chunker.chunk(text, source_file)
    
    def chunk_file(self, filepath: Path) -> List[Chunk]:
        """Chunk markdown file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return self.chunk_text(text, str(filepath))
    
    def get_stats(self, chunks: List[Chunk]) -> Dict:
        """Get chunking statistics"""
        if not chunks:
            return {}
        
        total_tokens = sum(c.metadata.token_count for c in chunks)
        avg_tokens = total_tokens / len(chunks)
        
        return {
            'num_chunks': len(chunks),
            'total_tokens': total_tokens,
            'avg_tokens_per_chunk': avg_tokens,
            'min_tokens': min(c.metadata.token_count for c in chunks),
            'max_tokens': max(c.metadata.token_count for c in chunks),
            'strategy': self.strategy.value,
        }


# ═══════════════════════════════════════════════════════════════
# CLI FOR TESTING
# ═══════════════════════════════════════════════════════════════

def main():
    """Test chunking on a file"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test markdown chunking")
    parser.add_argument('file', help='Markdown file to chunk')
    parser.add_argument('-s', '--strategy', choices=['recursive', 'sliding', 'simple'],
                       default='recursive', help='Chunking strategy')
    parser.add_argument('-t', '--max-tokens', type=int, default=1024,
                       help='Max tokens per chunk')
    parser.add_argument('-o', '--overlap', type=int, default=128,
                       help='Overlap tokens')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create chunker
    chunker = MarkdownChunker(
        strategy=ChunkStrategy(args.strategy),
        max_tokens=args.max_tokens,
        overlap=args.overlap
    )
    
    # Chunk file
    filepath = Path(args.file)
    print(f"📄 Chunking: {filepath}")
    print(f"   Strategy: {args.strategy}")
    print(f"   Max tokens: {args.max_tokens}, Overlap: {args.overlap}")
    print()
    
    chunks = chunker.chunk_file(filepath)
    
    # Stats
    stats = chunker.get_stats(chunks)
    print(f"📊 Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()
    
    # Show chunks
    if args.verbose:
        for i, chunk in enumerate(chunks[:5]):  # First 5 chunks
            print(f"─── Chunk {i} ───")
            print(f"Headers: {' > '.join(chunk.metadata.headers)}")
            print(f"Tokens: {chunk.metadata.token_count}")
            print(f"Preview: {chunk.text[:200]}...")
            print()
        
        if len(chunks) > 5:
            print(f"... and {len(chunks) - 5} more chunks")


if __name__ == "__main__":
    main()
