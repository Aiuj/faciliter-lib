"""Models for embeddings responses."""
from typing import List, Union, Optional
from .embeddings_config import embeddings_settings


class EmbeddingResponse:
    def __init__(self, embedding: Union[List[float], List[List[float]]], model: str):
        self.embedding = embedding
        self.model = model

    @classmethod
    def from_dict(cls, data: dict, default_model: Optional[str] = None):
        if default_model is None:
            default_model = embeddings_settings.model

        if 'embeddings' in data:
            embedding = data['embeddings']
        elif 'embedding' in data:
            embedding = data['embedding']
        else:
            raise KeyError('embedding or embeddings')
        model = data.get('model', default_model)
        return cls(embedding=embedding, model=model)
