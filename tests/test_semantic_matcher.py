"""Tests for SemanticGuardrailMatcher"""

from unittest.mock import MagicMock, Mock, patch

import pytest

# Try to import numpy, skip all tests if not available
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

pytestmark = pytest.mark.skipif(
    not NUMPY_AVAILABLE, reason="numpy not installed (optional dependency)"
)


class TestSemanticMatcher:
    """Test semantic matching functionality"""

    @pytest.fixture
    def mock_guardrails(self):
        """Create mock guardrails for testing"""
        guardrail1 = Mock()
        guardrail1.id = 1
        guardrail1.rule_text = "Always validate user input for SQL injection"

        guardrail2 = Mock()
        guardrail2.id = 2
        guardrail2.rule_text = "Ensure authentication before database access"

        guardrail3 = Mock()
        guardrail3.id = 3
        guardrail3.rule_text = "Use parameterized queries to prevent injection"

        return [guardrail1, guardrail2, guardrail3]

    @pytest.fixture
    def matcher(self):
        """Create matcher instance"""
        from guardloop.core.semantic_matcher import SemanticGuardrailMatcher

        return SemanticGuardrailMatcher()

    def test_init(self, matcher):
        """Test matcher initialization"""
        assert matcher.model is None
        assert matcher.guardrail_embeddings == {}
        assert matcher._model_loaded is False

    @patch("guardrail.core.semantic_matcher.SentenceTransformer")
    def test_ensure_model_loaded(self, mock_transformer, matcher):
        """Test lazy model loading"""
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model

        matcher._ensure_model_loaded()

        assert matcher._model_loaded is True
        assert matcher.model == mock_model
        mock_transformer.assert_called_once_with("all-MiniLM-L6-v2")

    @patch("guardrail.core.semantic_matcher.SentenceTransformer")
    def test_ensure_model_loaded_import_error(self, mock_transformer, matcher):
        """Test error handling when sentence-transformers not installed"""
        mock_transformer.side_effect = ImportError("No module named 'sentence_transformers'")

        with pytest.raises(ImportError):
            matcher._ensure_model_loaded()

    @pytest.mark.asyncio
    @patch("guardrail.core.semantic_matcher.SentenceTransformer")
    async def test_index_guardrails(self, mock_transformer, matcher, mock_guardrails):
        """Test guardrail indexing"""
        # Mock model encode
        mock_model = MagicMock()
        mock_embeddings = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model

        await matcher.index_guardrails(mock_guardrails)

        # Verify model was loaded
        assert matcher._model_loaded is True

        # Verify encode was called
        mock_model.encode.assert_called_once()

        # Verify embeddings were cached
        assert len(matcher.guardrail_embeddings) == 3
        assert 1 in matcher.guardrail_embeddings
        assert 2 in matcher.guardrail_embeddings
        assert 3 in matcher.guardrail_embeddings

    @pytest.mark.asyncio
    @patch("guardrail.core.semantic_matcher.SentenceTransformer")
    async def test_find_relevant(self, mock_transformer, matcher, mock_guardrails):
        """Test semantic similarity matching"""
        # Mock model
        mock_model = MagicMock()

        # Mock embeddings (normalized for cosine similarity)
        prompt_emb = np.array([1.0, 0.0])
        guardrail_embs = np.array([[0.9, 0.1], [0.5, 0.5], [0.8, 0.2]])

        def encode_side_effect(texts, **kwargs):
            if len(texts) == 1 and "SQL" in texts[0]:
                return np.array([prompt_emb])
            return guardrail_embs

        mock_model.encode.side_effect = encode_side_effect
        mock_transformer.return_value = mock_model

        # Index guardrails first
        await matcher.index_guardrails(mock_guardrails)

        # Find relevant
        results = await matcher.find_relevant(
            prompt="Check for SQL injection vulnerabilities",
            guardrails=mock_guardrails,
            top_k=2,
            threshold=0.3,
        )

        # Verify results
        assert len(results) <= 2
        assert all(isinstance(r, tuple) for r in results)
        assert all(0.0 <= score <= 1.0 for _, score in results)

        # Verify sorted by similarity (descending)
        if len(results) > 1:
            assert results[0][1] >= results[1][1]

    @pytest.mark.asyncio
    async def test_find_relevant_empty_guardrails(self, matcher):
        """Test find_relevant with empty guardrails"""
        results = await matcher.find_relevant(
            prompt="test prompt", guardrails=[], top_k=5, threshold=0.3
        )

        assert results == []

    @pytest.mark.asyncio
    @patch("guardrail.core.semantic_matcher.SentenceTransformer")
    async def test_find_relevant_threshold_filtering(
        self, mock_transformer, matcher, mock_guardrails
    ):
        """Test that threshold filters low similarity results"""
        # Mock model with low similarity scores
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.0]])  # Very different from guardrails
        mock_transformer.return_value = mock_model

        # Pre-set embeddings
        matcher.guardrail_embeddings = {
            1: np.array([1.0, 0.0]),
            2: np.array([0.9, 0.1]),
            3: np.array([0.8, 0.2]),
        }

        results = await matcher.find_relevant(
            prompt="completely unrelated topic",
            guardrails=mock_guardrails,
            top_k=5,
            threshold=0.8,  # High threshold
        )

        # Should filter out low similarity matches
        assert len(results) == 0 or all(score >= 0.8 for _, score in results)

    def test_clear_cache(self, matcher):
        """Test cache clearing"""
        # Add some embeddings
        matcher.guardrail_embeddings = {1: np.array([1, 2]), 2: np.array([3, 4])}

        matcher.clear_cache()

        assert len(matcher.guardrail_embeddings) == 0

    def test_get_cache_stats(self, matcher):
        """Test cache statistics"""
        # Initially empty
        stats = matcher.get_cache_stats()
        assert stats["cached_embeddings"] == 0
        assert stats["model_loaded"] is False
        assert stats["model_name"] is None

        # Add embeddings
        matcher.guardrail_embeddings = {1: np.array([1, 2]), 2: np.array([3, 4])}
        matcher._model_loaded = True

        stats = matcher.get_cache_stats()
        assert stats["cached_embeddings"] == 2
        assert stats["model_loaded"] is True
        assert stats["model_name"] == "all-MiniLM-L6-v2"


class TestAdaptiveGuardrailsIntegration:
    """Test semantic matching integration with AdaptiveGuardrailGenerator"""

    @pytest.mark.asyncio
    async def test_semantic_matching_flag(self):
        """Test that use_semantic_matching flag works"""
        # This is an integration test placeholder
        # Would need full database setup to test properly
        pass
