"""
Unit tests for ChunkEmbedder
"""
import pytest
import json
from unittest.mock import MagicMock, patch, call


@pytest.fixture
def embedder():
    with patch("src.chunking.embedder.storage.Client"), \
            patch("src.chunking.embedder.aiplatform.init"), \
            patch("src.chunking.embedder.TextEmbeddingModel"):
        from src.chunking.embedder import ChunkEmbedder
        e = ChunkEmbedder(
            project_id="test-project",
            bucket_processed="test-bucket",
            location="us-east1"
        )
        e.storage_client = MagicMock()
        return e


# ==================== Initialization ====================

def test_embedder_default_location():
    with patch("src.chunking.embedder.storage.Client"), \
            patch("src.chunking.embedder.aiplatform.init"), \
            patch("src.chunking.embedder.TextEmbeddingModel"):
        from src.chunking.embedder import ChunkEmbedder
        e = ChunkEmbedder(project_id="proj", bucket_processed="bucket")
    assert e.location == "us-east1"


def test_embedder_batch_size(embedder):
    assert embedder.batch_size == 250


def test_embedder_max_text_length(embedder):
    assert embedder.max_text_length == 3072


def test_embedder_not_initialized_at_start(embedder):
    assert embedder.initialized is False


# ==================== initialize_model ====================

def test_initialize_model_success(embedder):
    mock_model = MagicMock()
    with patch(
        "src.chunking.embedder.TextEmbeddingModel.from_pretrained",
        return_value=mock_model
    ):
        result = embedder.initialize_model()
    assert result is True
    assert embedder.initialized is True


def test_initialize_model_failure(embedder):
    with patch(
        "src.chunking.embedder.TextEmbeddingModel.from_pretrained",
        side_effect=Exception("fail")
    ):
        result = embedder.initialize_model()
    assert result is False
    assert embedder.initialized is False


def test_initialize_model_idempotent(embedder):
    embedder.initialized = True
    with patch("src.chunking.embedder.TextEmbeddingModel.from_pretrained") as mock:
        result = embedder.initialize_model()
    assert result is True
    mock.assert_not_called()


# ==================== _load_chunks ====================

def test_load_chunks(embedder):
    chunks = [
        {"content": "def foo(): pass", "language": "python"},
        {"content": "def bar(): pass", "language": "python"},
    ]
    jsonl = "\n".join(json.dumps(c) for c in chunks)

    mock_blob = MagicMock()
    mock_blob.download_as_text.return_value = jsonl
    embedder.storage_client.bucket.return_value.blob.return_value = mock_blob

    result = embedder._load_chunks("repos/owner/repo")
    assert len(result) == 2
    assert result[0]["content"] == "def foo(): pass"


def test_load_chunks_skips_empty_lines(embedder):
    jsonl = '{"content": "foo"}\n\n{"content": "bar"}\n'
    mock_blob = MagicMock()
    mock_blob.download_as_text.return_value = jsonl
    embedder.storage_client.bucket.return_value.blob.return_value = mock_blob

    result = embedder._load_chunks("repos/owner/repo")
    assert len(result) == 2


# ==================== _save_chunks ====================

def test_save_chunks(embedder):
    chunks = [{"content": "def foo(): pass", "embedding": [0.1, 0.2]}]
    mock_blob = MagicMock()
    embedder.storage_client.bucket.return_value.blob.return_value = mock_blob

    embedder._save_chunks("repos/owner/repo", chunks)
    mock_blob.upload_from_string.assert_called_once()
    saved = mock_blob.upload_from_string.call_args[0][0]
    assert "def foo(): pass" in saved


# ==================== embed_repository ====================

def test_embed_repository_skips_already_embedded(embedder):
    chunks = [
        {"content": "def foo(): pass", "embedding": [0.1, 0.2]},
        {"content": "def bar(): pass", "embedding": [0.3, 0.4]},
    ]
    jsonl = "\n".join(json.dumps(c) for c in chunks)
    mock_blob = MagicMock()
    mock_blob.download_as_text.return_value = jsonl
    embedder.storage_client.bucket.return_value.blob.return_value = mock_blob

    result = embedder.embed_repository("repos/owner/repo", force_reembed=False)
    assert result["already_embedded"] == 2
    assert result["newly_embedded"] == 0


def test_embed_repository_force_reembed_clears_embeddings(embedder):
    chunks = [
        {"content": "def foo(): pass", "embedding": [
            0.1, 0.2], "embedding_model": "old"},
    ]
    jsonl = "\n".join(json.dumps(c) for c in chunks)
    mock_blob = MagicMock()
    mock_blob.download_as_text.return_value = jsonl
    embedder.storage_client.bucket.return_value.blob.return_value = mock_blob

    embedder.initialized = True
    embedder.model = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.values = [0.5] * 768
    embedder.model.get_embeddings.return_value = [mock_embedding]

    result = embedder.embed_repository("repos/owner/repo", force_reembed=True)
    assert result["newly_embedded"] == 1


def test_embed_repository_no_model_returns_failed(embedder):
    chunks = [{"content": "def foo(): pass"}]
    jsonl = json.dumps(chunks[0])
    mock_blob = MagicMock()
    mock_blob.download_as_text.return_value = jsonl
    embedder.storage_client.bucket.return_value.blob.return_value = mock_blob

    with patch.object(embedder, "initialize_model", return_value=False):
        result = embedder.embed_repository("repos/owner/repo")
    assert result["failed"] == 1
    assert result["newly_embedded"] == 0


# ==================== _generate_embeddings_batch ====================

def test_generate_embeddings_batch_truncates_long_text(embedder):
    embedder.initialized = True
    embedder.model = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1] * 768
    embedder.model.get_embeddings.return_value = [mock_embedding]

    long_text = "x" * 5000
    chunks = [{"content": long_text}]

    embedder._generate_embeddings_batch(chunks)

    called_texts = embedder.model.get_embeddings.call_args[0][0]
    assert len(called_texts[0]) <= embedder.max_text_length


def test_generate_embeddings_batch_uses_enriched_content(embedder):
    embedder.initialized = True
    embedder.model = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1] * 768
    embedder.model.get_embeddings.return_value = [mock_embedding]

    chunks = [{"content": "raw", "enriched_content": "enriched context"}]
    embedder._generate_embeddings_batch(chunks)

    called_texts = embedder.model.get_embeddings.call_args[0][0]
    assert called_texts[0] == "enriched context"


def test_generate_embeddings_batch_assigns_metadata(embedder):
    embedder.initialized = True
    embedder.model = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1] * 768
    embedder.model.get_embeddings.return_value = [mock_embedding]

    chunks = [{"content": "def foo(): pass"}]
    embedder._generate_embeddings_batch(chunks)

    assert chunks[0]["embedding"] == [0.1] * 768
    assert chunks[0]["embedding_model"] == "text-embedding-004-vertex"
    assert chunks[0]["embedding_dim"] == 768


def test_generate_embeddings_batch_handles_failure(embedder):
    embedder.initialized = True
    embedder.model = MagicMock()
    embedder.model.get_embeddings.side_effect = Exception("API error")

    chunks = [{"content": "def foo(): pass"}]
    result = embedder._generate_embeddings_batch(chunks)
    assert result["failed"] >= 0  # Should not crash
