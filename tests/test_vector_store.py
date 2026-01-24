import numpy as np
import pytest

from phantom.rag.vectors import FAISSVectorStore, NumpyVectorStore, create_vector_store


@pytest.fixture
def dummy_embeddings():
    # Dim 4 para facilitar debug
    # Doc 1: [1, 0, 0, 0]
    # Doc 2: [0, 1, 0, 0]
    e1 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    e2 = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    return np.vstack([e1, e2]), ["doc1", "doc2"]


def test_numpy_vector_store(dummy_embeddings):
    embeddings, texts = dummy_embeddings
    store = NumpyVectorStore(embedding_dim=4)
    store.add(embeddings, texts, metadata=[{"id": 1}, {"id": 2}])

    # Query proxima de doc1
    query = np.array([0.9, 0.1, 0.0, 0.0], dtype=np.float32)
    results = store.search(query, top_k=1)

    assert len(results) == 1
    assert results[0].text == "doc1"
    assert results[0].metadata["id"] == 1
    assert results[0].score > 0.8


def test_faiss_vector_store_if_available(dummy_embeddings):
    try:
        import faiss
    except ImportError:
        pytest.skip("FAISS not installed")

    embeddings, texts = dummy_embeddings
    store = FAISSVectorStore(embedding_dim=4, use_gpu=False)
    store.add(embeddings, texts)

    query = np.array([0.1, 0.9, 0.0, 0.0], dtype=np.float32)
    results = store.search(query, top_k=1)

    assert len(results) == 1
    assert results[0].text == "doc2"


def test_create_vector_store_auto():
    store = create_vector_store(384, backend="numpy")
    assert isinstance(store, NumpyVectorStore)


def test_save_load_numpy(tmp_path, dummy_embeddings):
    embeddings, texts = dummy_embeddings
    store = NumpyVectorStore(embedding_dim=4)
    store.add(embeddings, texts, metadata=[{"meta": "data"}])

    save_path = tmp_path / "index"
    store.save(save_path)

    loaded = NumpyVectorStore.load(save_path)
    assert len(loaded) == 2
    assert loaded.texts == texts
    assert loaded.metadata[0]["meta"] == "data"
