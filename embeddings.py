import json
import sys
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from FlagEmbedding import BGEM3FlagModel


def _log(msg: str):
    print(msg, file=sys.stderr, flush=True)


class BGEEmbedder:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)
        
        self.model_name = self.config.get("model", "BAAI/bge-m3")
        self.use_fp16 = self.config.get("use_fp16", True)
        self.batch_size = self.config.get("batch_size", 1)
        self.device = self.config.get("device", "cuda")
        self.embedding_dim = self.config.get("embedding_dim", 1024)
        self.max_length = self.config.get("max_length", 256)
        
        self._model = None
        self._load_model()
    
    def _load_model(self):
        _log(f"Loading {self.model_name} on {self.device} (max_length={self.max_length})...")
        self._model = BGEM3FlagModel(
            self.model_name,
            use_fp16=self.use_fp16,
            device=self.device
        )
        _log("Model loaded successfully")
    
    @property
    def model(self):
        return self._model
    
    def encode(self, texts: List[str], batch_size: Optional[int] = None) -> np.ndarray:
        if not texts:
            return np.array([]).reshape(0, self.embedding_dim)
        
        if batch_size is None:
            batch_size = self.batch_size
        
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            max_length=self.max_length
        )['dense_vecs']
        
        embeddings = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = embeddings / norms
        
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        return self.encode([text])[0]
    
    def get_device_info(self) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "device": self.device,
            "use_fp16": self.use_fp16,
            "embedding_dim": self.embedding_dim,
            "max_length": self.max_length,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        }


if __name__ == "__main__":
    embedder = BGEEmbedder()
    info = embedder.get_device_info()
    print(json.dumps(info, indent=2))
    
    test_texts = [
        "місце артикуляції",
        "place of articulation",
        "उच्चारणस्थानम्",
        "sthāna"
    ]
    embeddings = embedder.encode(test_texts)
    print(f"Embeddings shape: {embeddings.shape}")
    print(f"First embedding norm: {np.linalg.norm(embeddings[0]):.6f}")