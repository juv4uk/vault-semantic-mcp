#!/usr/bin/env python3
"""Embed full Sanskrit corpus using BGE-M3 on GPU"""

import json
import sys
import hashlib
from pathlib import Path
from embeddings import BGEEmbedder

SRC_DIR = "/home/agents/GitHub/shiva-sutras/ksetra/sanskritworld_texts"
OUTPUT_FILE = "/home/agents/GitHub/vault-semantic-mcp/data/sanskrit_embeddings.jsonl"

def collect_files(root):
    files = []
    for ext in [".txt", ".md"]:
        files.extend(Path(root).rglob(f"*{ext}"))
    return files

def read_file(path):
    for enc in ["utf-8-sig", "utf-8", "utf-16le"]:
        try:
            return path.read_text(encoding=enc), enc
        except UnicodeDecodeError:
            continue
    return None, None

def chunk_text(text, max_len=512, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += max_len - overlap
    return chunks

def main():
    # Optional partial-run filter: pass one or more subfolder prefixes,
    # e.g. `python embed_corpus.py vedic-literature/upanishad poetry/kavya`.
    # Lets us embed the corpus in small GPU-friendly parts.
    filters = [a for a in sys.argv[1:] if not a.startswith("-")]
    embedder = BGEEmbedder("config.json")
    files = collect_files(SRC_DIR)
    if filters:
        files = [f for f in files if any(str(f.relative_to(SRC_DIR)).startswith(pfx) for pfx in filters)]
    print(f"Found {len(files)} files (filters: {filters or 'ALL'})", file=sys.stderr)

    # Resume: find already processed files
    processed = set()
    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    processed.add(d["source_file"])
                except:
                    pass
        print(f"Already processed: {len(processed)} files", file=sys.stderr)

    with open(OUTPUT_FILE, "a") as out:
        for i, fpath in enumerate(files):
            rel = fpath.relative_to(SRC_DIR)
            if str(rel) in processed:
                continue
            text, enc = read_file(fpath)
            if not text or not text.strip():
                continue

            chunks = chunk_text(text)
            embeddings = embedder.encode(chunks)

            for j, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                record = {
                    "source_file": str(rel),
                    "chunk_index": j,
                    "chunk_text": chunk[:200],
                    "embedding": emb.tolist(),
                    "model": "BAAI/bge-m3",
                    "sha256": hashlib.sha256(chunk.encode()).hexdigest()[:16]
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")

            if (i + 1) % 50 == 0:
                print(f"Processed {i+1}/{len(files)} files", file=sys.stderr)

    print(f"Done. Embeddings saved to {OUTPUT_FILE}", file=sys.stderr)

if __name__ == "__main__":
    main()