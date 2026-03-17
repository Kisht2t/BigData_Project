"""Tests for the embedder — verifies vector shape and normalization."""

import sys
sys.path.insert(0, "/Users/kisht2t/Downloads/BigData_Project/backend/worker")

import math
from embedder import embed, embed_one, VECTOR_SIZE


def test_embed_returns_correct_shape():
    texts = ["Hello world", "Another sentence"]
    vectors = embed(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == VECTOR_SIZE


def test_embed_one_returns_single_vector():
    vec = embed_one("test sentence")
    assert len(vec) == VECTOR_SIZE
    assert isinstance(vec[0], float)


def test_vectors_are_normalized():
    vec = embed_one("test normalization")
    magnitude = math.sqrt(sum(v ** 2 for v in vec))
    assert abs(magnitude - 1.0) < 1e-5, f"Vector magnitude {magnitude} is not ~1.0"


def test_similar_texts_have_higher_similarity():
    v1 = embed_one("large language models and transformers")
    v2 = embed_one("LLMs and transformer architectures")
    v3 = embed_one("cooking recipes and food preparation")

    sim_12 = sum(a * b for a, b in zip(v1, v2))
    sim_13 = sum(a * b for a, b in zip(v1, v3))

    assert sim_12 > sim_13, "Similar texts should have higher cosine similarity"
