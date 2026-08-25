#!/usr/bin/env python3
"""Embed the ENTIRE live Obsidian vault (Windows /mnt/c path) into a
semantic search index. Excludes Corpus_IAST (147MB corpus texts already
covered by sanskrit_embeddings.jsonl from SOURCE Devanagari)."""
import json, os, sys, hashlib
import numpy as np

VAULT = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian"
OUT_DIR = "/home/agents/GitHub/vault-semantic-mcp/data/index-vault-live"
EXCLUDE_PARTS = ("Corpus_IAST", "node_modules", ".git", ".obsidian", ".gemini")

def iter_notes():
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_PARTS and not d.startswith(".")]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(root, f)

def read_note(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    body = txt
    if txt.startswith('---'):
        parts = txt.split('---', 2)
        if len(parts) == 3:
            body = parts[1] + '\n' + parts[2]  # keep tags too, they are signal
    body = re.sub(r'```dataview.*?```', '', body, flags=re.S)
    return re.sub(r'\n{3,}', '\n\n', body).strip()

import re
def chunk(text, max_len=900, overlap=100):
    out, start = [], 0
    while start < len(text):
        end = min(start + max_len, len(text))
        seg = text[start:end].strip()
        if seg:
            out.append(seg)
        if end >= len(text):
            break
        start = end - overlap
    return out or ['']

sys.path.insert(0, "/home/agents/GitHub/vault-semantic-mcp")
from embeddings import BGEEmbedder
emb = BGEEmbedder("/home/agents/GitHub/vault-semantic-mcp/config.json")

os.makedirs(OUT_DIR, exist_ok=True)
out_path = os.path.join(OUT_DIR, "vault_embeddings.jsonl")
done = set()
if os.path.exists(out_path):
    for line in open(out_path, encoding='utf-8', errors='replace'):
        try: done.add(json.loads(line)['source_file'])
        except Exception: pass
print(f"resume: {len(done)} files already embedded", flush=True)

meta_out = open(os.path.join(OUT_DIR, "vault_meta.jsonl"), "a", encoding="utf-8")
emb_out = open(out_path, "a", encoding="utf-8")

total_files = sum(1 for _ in iter_notes())
print(f"files to process: {total_files}", flush=True)
processed = 0
for path in iter_notes():
    rel = os.path.relpath(path, VAULT)
    if rel in done:
        continue
    try:
        text = read_note(path)
    except Exception as e:
        print(f"READ ERR {rel}: {e}", flush=True); continue
    chunks = chunk(text)
    if not chunks:
        continue
    res = emb.model.encode(chunks, batch_size=16, max_length=512,
                           return_dense=True, return_sparse=False,
                           return_colbert_vecs=False)
    vecs = np.asarray(res['dense_vecs'], dtype=np.float32)
    for ci, (seg, vec) in enumerate(zip(chunks, vecs)):
        rec = {"source_file": rel, "chunk_index": ci, "chunk_text": seg[:200],
               "embedding": [round(float(x),6) for x in vec],
               "model": "BAAI/bge-m3",
               "sha256": __import__('hashlib').sha256(seg.encode()).hexdigest()[:12]}
        emb_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    meta_out.write(json.dumps({"file": rel, "chunks": len(chunks)}, ensure_ascii=False) + "\n")
    meta_out.flush(); emb_out.flush()
    processed += 1
    if processed % 50 == 0:
        print(f"... {processed} files embedded", flush=True)

print(f"DONE. total this run: {processed}", flush=True)
