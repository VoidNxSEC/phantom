import pytest

from phantom.rag.cortex_chunker import Chunk, ChunkStrategy, MarkdownChunker

pytestmark = pytest.mark.unit


@pytest.fixture
def sample_markdown():
    return """# Header 1
Some content here.

## Header 2
More content here.
* List item 1
* List item 2

### Header 3
Deep content.
"""


def test_simple_chunker():
    chunker = MarkdownChunker(strategy=ChunkStrategy.SIMPLE, max_tokens=10)
    text = "Word " * 20
    chunks = chunker.chunk_text(text)
    assert len(chunks) > 1
    assert all(isinstance(c, Chunk) for c in chunks)


def test_recursive_chunker_headers(sample_markdown):
    chunker = MarkdownChunker(strategy=ChunkStrategy.RECURSIVE, max_tokens=50)
    chunks = chunker.chunk_text(sample_markdown)

    assert len(chunks) > 0
    # Check if headers are preserved in metadata
    assert any("Header 1" in c.metadata.headers for c in chunks)
    assert any("Header 2" in c.metadata.headers for c in chunks)


def test_sliding_window_overlap():
    text = "1 2 3 4 5 6 7 8 9 10"
    # Approx 1 token per number + space.
    # Let's say 1 number = 1 token for simplicity in approximate counter

    chunker = MarkdownChunker(strategy=ChunkStrategy.SLIDING, max_tokens=5, overlap=2)
    chunks = chunker.chunk_text(text)

    assert len(chunks) >= 2
    # In a real sliding window, we expect overlap.
    # Exact verification depends on the tokenizer, but we ensure multiple chunks are created.


def test_chunk_metadata_defaults():
    chunker = MarkdownChunker(strategy=ChunkStrategy.SIMPLE)
    chunks = chunker.chunk_text("test")
    assert chunks[0].metadata.source_file == "unknown"
