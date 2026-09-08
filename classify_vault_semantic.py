#!/usr/bin/env python3
"""Vault-wide semantic-suggest classifier -- same threshold-based,
uncapped tagging logic as classify_corpus_semantic.py (no TOP_K cap,
pure THRESHOLD cutoff), applied to the live Obsidian vault instead of
just the Sanskrit corpus.

More distinct senses in a note -> more tags: a note earns a tag for
every ontology concept it clears THRESHOLD similarity with, so a
richer note (touches many concepts) collects many tags and a sparse
one collects none -- content richness IS tag count, not a separate
metric layered on top.

Reads ONLY the already-computed vault embeddings index
(data/index-vault-live/vault_embeddings.jsonl) -- run
embed_vault_live.py first (or again) if that index doesn't yet cover
the whole vault; this script warns but does not block on partial
coverage.

Output is a suggestions sidecar only -- it does NOT touch any vault
note. Use apply_vault_tags.py (dry-run by default) to write tags into
frontmatter.
"""
import json, os, re
import numpy as np

VAULT = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian"
ONTO_DIR = os.path.join(VAULT, "🕉️ Онтологія")
EMB_FILE = "/home/agents/GitHub/vault-semantic-mcp/data/index-vault-live/vault_embeddings.jsonl"
OUT = "/home/agents/GitHub/vault-semantic-mcp/data/vault_semantic_tags.suggestions.jsonl"
EXCLUDE_PARTS = ("Corpus_IAST", "node_modules", ".git", ".obsidian", ".gemini")
THRESHOLD = 0.65
STOPWEIGHT = {"vākya": 0.90}  # same de-weight as the corpus classifier -- harmless if unused here


def read_note(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    fm_raw, body = "", txt
    if txt.startswith("---"):
        parts = txt.split("---", 2)
        if len(parts) == 3:
            fm_raw, body = parts[1], parts[2]
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    body = re.sub(r"\s+", " ", body).strip()

    def field(key):
        m = re.search(rf'^{key}:\s*"?([^"\n]+)"?\s*$', fm_raw, re.M)
        return m.group(1).strip() if m else ""

    aliases = re.findall(r'-\s*"([^"]+)"', fm_raw)
    return field, body, aliases


# ---- anchors: same Ontology folder + fields as classify_corpus_semantic.py ----
anchors = []
for f in sorted(os.listdir(ONTO_DIR)):
    if not f.endswith(".md"):
        continue
    term = f[:-3]
    field, body, aliases = read_note(os.path.join(ONTO_DIR, f))
    deva = field("sanskrit")
    iast = field("iast")
    cat = field("category")
    alias_s = " ".join(aliases[:4])
    text = f"{term} {deva} {iast}. {cat}. {alias_s}. {body[:400]}".strip()
    if len(text) < 40:
        continue
    anchors.append((term, text))
print(f"anchors: {len(anchors)}", flush=True)

# ---- vault vectors, mean-pooled per file ----
if not os.path.exists(EMB_FILE):
    raise SystemExit(f"Missing {EMB_FILE} -- run embed_vault_live.py first.")

acc = {}
with open(EMB_FILE) as fh:
    for line in fh:
        d = json.loads(line)
        acc.setdefault(d["source_file"], []).append(np.asarray(d["embedding"], dtype=np.float32))
files = sorted(acc)
M = np.stack([np.mean(acc[s], axis=0) for s in files])
M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-9
print(f"vault files in index: {len(files)}", flush=True)

# coverage check -- an incomplete index means "0 tags" is not a real
# signal for files outside it; warn instead of silently under-reporting
total_md = sum(
    1
    for root, dirs, fnames in os.walk(VAULT)
    for fname in fnames
    if fname.endswith(".md") and not any(p in root for p in EXCLUDE_PARTS)
)
if len(files) < total_md:
    print(
        f"WARNING: index covers {len(files)}/{total_md} vault notes -- "
        f"re-run embed_vault_live.py to extend coverage before treating "
        f"missing files as genuinely tag-less.",
        flush=True,
    )

from embeddings import BGEEmbedder

emb = BGEEmbedder("/home/agents/GitHub/vault-semantic-mcp/config.json")


def enc(texts):
    r = emb.model.encode(
        texts, batch_size=8, max_length=256,
        return_dense=True, return_sparse=False, return_colbert_vecs=False,
    )
    A = np.asarray(r["dense_vecs"], dtype=np.float32)
    return A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9)


A = enc([a[1] for a in anchors])
S = A @ M.T  # anchors x files

n_sugg = 0
with open(OUT, "w", encoding="utf-8") as out:
    for fi, sf in enumerate(files):
        sims = S[:, fi]
        idx = np.argsort(-sims)  # весь масив, без TOP_K -- більше сенсів = більше тегів
        tags = []
        for i in idx:
            concept = anchors[i][0]
            eff = float(sims[i]) * STOPWEIGHT.get(concept, 1.0)
            if eff >= THRESHOLD:
                tags.append({"concept": concept, "sim": round(float(sims[i]), 4)})
        rec = {
            "vault_file": sf,
            "status": "semantic-suggest",
            "review": "unreviewed",
            "model": "BAAI/bge-m3",
            "anchor_set": "ontology-v1",
            "suggested_tags": tags,
        }
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_sugg += len(tags)
print(f"suggestions: {n_sugg} -> {OUT}", flush=True)
