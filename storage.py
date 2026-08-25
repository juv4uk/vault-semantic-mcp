import json
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ChunkMetadata:
    source_path: str
    relative_path: str
    mtime: float
    content_hash: str
    chunk_id: int
    heading: str
    chunk_text: str
    char_start: int
    char_end: int


class IndexStorage:
    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.embeddings_file = self.index_path / "embeddings.npy"
        self.metadata_file = self.index_path / "metadata.json"
        self.manifest_file = self.index_path / "manifest.json"
    
    def _compute_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    
    def save(self, embeddings: np.ndarray, metadata: List[ChunkMetadata], manifest: Dict[str, Any]):
        np.save(self.embeddings_file, embeddings)
        
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump([asdict(m) for m in metadata], f, ensure_ascii=False, indent=2)
        
        manifest["index_timestamp"] = datetime.now().isoformat()
        manifest["indexed_chunks"] = len(metadata)
        manifest["embedding_dim"] = embeddings.shape[1] if len(embeddings) > 0 else 0
        
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    def load(self) -> tuple[Optional[np.ndarray], List[ChunkMetadata], Dict[str, Any]]:
        if not self.embeddings_file.exists() or not self.metadata_file.exists():
            return None, [], {}
        
        embeddings = np.load(self.embeddings_file)
        
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            metadata_raw = json.load(f)
            metadata = [ChunkMetadata(**m) for m in metadata_raw]
        
        manifest = {}
        if self.manifest_file.exists():
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        
        return embeddings, metadata, manifest
    
    def exists(self) -> bool:
        return self.embeddings_file.exists() and self.metadata_file.exists()
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.exists():
            return {"exists": False}
        
        _, metadata, manifest = self.load()
        return {
            "exists": True,
            "indexed_chunks": len(metadata),
            "embedding_dim": manifest.get("embedding_dim", 0),
            "index_timestamp": manifest.get("index_timestamp"),
            "vault_path": manifest.get("vault_path"),
            "model": manifest.get("model"),
            "device": manifest.get("device")
        }


if __name__ == "__main__":
    storage = IndexStorage("/home/agents/GitHub/vault-semantic-mcp/data/index")
    print(storage.get_stats())