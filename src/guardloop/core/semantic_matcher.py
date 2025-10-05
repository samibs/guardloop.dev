"""Semantic similarity for guardrail matching using embeddings."""

from typing import List, Tuple

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class SemanticGuardrailMatcher:
    """Use embeddings to match guardrails to prompts with semantic similarity."""

    def __init__(self):
        """Initialize semantic matcher with lightweight embedding model."""
        self.model = None
        self.guardrail_embeddings = {}
        self._model_loaded = False

    def _ensure_model_loaded(self):
        """Lazy load the sentence transformer model."""
        if not self._model_loaded:
            try:
                from sentence_transformers import SentenceTransformer

                # Load lightweight model (all-MiniLM-L6-v2: 80MB, fast inference)
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self._model_loaded = True
                logger.info("Semantic matcher model loaded", model="all-MiniLM-L6-v2")
            except ImportError:
                logger.error(
                    "sentence-transformers not installed. Run: pip install sentence-transformers"
                )
                raise

    async def index_guardrails(self, guardrails: List[any]) -> None:
        """Pre-compute embeddings for all guardrails.

        Args:
            guardrails: List of DynamicGuardrailModel instances
        """
        self._ensure_model_loaded()

        if not guardrails:
            logger.warning("No guardrails to index")
            return

        # Extract rule texts for encoding
        texts = [g.rule_text for g in guardrails]

        # Batch encode all guardrails
        embeddings = self.model.encode(texts, show_progress_bar=False)

        # Store embeddings with guardrail IDs
        for guardrail, embedding in zip(guardrails, embeddings):
            self.guardrail_embeddings[guardrail.id] = embedding

        logger.info(
            "Guardrails indexed with embeddings",
            count=len(guardrails),
            dimension=embeddings.shape[1],
        )

    async def find_relevant(
        self,
        prompt: str,
        guardrails: List[any],
        top_k: int = 5,
        threshold: float = 0.3,
    ) -> List[Tuple[any, float]]:
        """Find most relevant guardrails using semantic similarity.

        Args:
            prompt: User prompt to match against
            guardrails: List of DynamicGuardrailModel instances
            top_k: Maximum number of results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of (guardrail, similarity_score) tuples sorted by relevance
        """
        self._ensure_model_loaded()

        if not guardrails:
            logger.warning("No guardrails provided for matching")
            return []

        # Encode prompt
        prompt_embedding = self.model.encode([prompt], show_progress_bar=False)[0]

        # Calculate similarity scores
        scores = []

        for guardrail in guardrails:
            # Get or compute guardrail embedding
            if guardrail.id not in self.guardrail_embeddings:
                # Compute on-demand if not cached
                g_embedding = self.model.encode(
                    [guardrail.rule_text], show_progress_bar=False
                )[0]
                self.guardrail_embeddings[guardrail.id] = g_embedding
            else:
                g_embedding = self.guardrail_embeddings[guardrail.id]

            # Cosine similarity
            similarity = np.dot(prompt_embedding, g_embedding) / (
                np.linalg.norm(prompt_embedding) * np.linalg.norm(g_embedding)
            )

            # Filter by threshold
            if similarity >= threshold:
                scores.append((guardrail, float(similarity)))

        # Sort by similarity (descending) and return top K
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]

        logger.info(
            "Semantic matching complete",
            candidates=len(guardrails),
            matches=len(top_results),
            top_score=top_results[0][1] if top_results else 0.0,
        )

        return top_results

    def clear_cache(self) -> None:
        """Clear cached embeddings."""
        count = len(self.guardrail_embeddings)
        self.guardrail_embeddings.clear()
        logger.info("Embedding cache cleared", cleared_count=count)

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            "cached_embeddings": len(self.guardrail_embeddings),
            "model_loaded": self._model_loaded,
            "model_name": "all-MiniLM-L6-v2" if self._model_loaded else None,
        }
