import os
from typing import List, Optional, Any
from ..core.config import settings

_model: Optional[Any] = None


def _get_model():
    global _model
    if _model is None:
        # Avoid importing TensorFlow parts of transformers to prevent keras dependency
        os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
        os.environ.setdefault("USE_TF", "0")
        os.environ.setdefault("USE_TORCH", "1")
        # Lazy import to ensure env vars are set before transformers loads
        from sentence_transformers import SentenceTransformer  # type: ignore
        # Use public model; no token required for all-MiniLM-L6-v2
        _model = SentenceTransformer(settings.HUGGINGFACE_MODEL)
    return _model


def generate_embedding(text: str) -> List[float]:
    try:
        model = _get_model()
        return model.encode(text).tolist()
    except Exception:
        # Fail-soft: return empty embedding if model unavailable
        return []


if __name__ == "__main__":
    sample_text = "AI for customer pain point detection"
    print(generate_embedding(sample_text))
