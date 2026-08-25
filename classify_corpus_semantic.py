#!/usr/bin/env python3
"""Production semantic-suggest classifier (Step 3 of uk-sa roadmap).

Anchor set: v3-bilingual — Devanagari term + IAST + category + body.
Also builds a bidirectional search index:
  uk query → top sanskrit corpus texts
  sa/IAST query → top corpus texts
"""
import json, os, re
import numpy as np

VAULT = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian"
ONTO_DIR = os.path.join(VAULT, "🕉️ Онтологія")
COGNATES = "/home/agents/GitHub/shiva-sutras/extensions/cognates-uk-sa.yaml"
EMB_FILE = "/home/agents/GitHub/vault-semantic-mcp/data/sanskrit_embeddings.jsonl"
OUT = "/home/agents/GitHub/shiva-sutras/ksetra/corpus_semantic_tags.suggestions.jsonl"
TOP_K = 3
THRESHOLD = 0.55
STOPWEIGHT = {"vākya": 0.90}

def read_note(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    fm_raw, body = '', txt
    if txt.startswith('---'):
        parts = txt.split('---', 2)
        if len(parts) == 3:
            fm_raw, body = parts[1], parts[2]
    body = re.sub(r'```.*?```', '', body, flags=re.S)
    body = re.sub(r'\s+', ' ', body).strip()
    def field(key):
        m = re.search(rf'^{key}:\s*"?([^"\n]+)"?\s*$', fm_raw, re.M)
        return m.group(1).strip() if m else ''
    aliases = re.findall(r'-\s*"([^"]+)"', fm_raw)
    return field, body, aliases

# ---- v3-bilingual anchors ----
anchors = []
for f in sorted(os.listdir(ONTO_DIR)):
    if not f.endswith('.md'):
        continue
    term = f[:-3]
    field, body, aliases = read_note(os.path.join(ONTO_DIR, f))
    deva = field('sanskrit')
    iast = field('iast')
    cat = field('category')
    alias_s = ' '.join(aliases[:4])
    text = f"{term} {deva} {iast}. {cat}. {alias_s}. {body[:400]}".strip()
    if len(text) < 40:
        continue
    anchors.append((term, text))
print(f"v3-bilingual anchors: {len(anchors)}", flush=True)

# ---- cognates as extra uk-side anchors (roadmap step 1 feeds step 3) ----
import yaml
cog = yaml.safe_load(open(COGNATES, encoding='utf-8'))
cog_uk_terms = [e['uk'] for e in cog.get('entries', [])]
print(f"cognate uk bridge terms: {len(cog_uk_terms)}", flush=True)

# ---- corpus vectors ----
acc = {}
with open(EMB_FILE) as fh:
    for line in fh:
        d = json.loads(line)
        sf = d['source_file'].rsplit('.', 1)[0]
        acc.setdefault(sf, []).append(np.asarray(d['embedding'], dtype=np.float32))
files = sorted(acc)
M = np.stack([np.mean(acc[s], axis=0) for s in files])
M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-9
print(f"corpus files embedded: {len(files)}", flush=True)

from embeddings import BGEEmbedder
emb = BGEEmbedder("/home/agents/GitHub/vault-semantic-mcp/config.json")

def enc(texts):
    r = emb.model.encode(texts, batch_size=8, max_length=256,
                         return_dense=True, return_sparse=False, return_colbert_vecs=False)
    A = np.asarray(r['dense_vecs'], dtype=np.float32)
    return A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9)

A = enc([a[1] for a in anchors])
S = A @ M.T

n_sugg = 0
with open(OUT, 'w', encoding='utf-8') as out:
    for fi, sf in enumerate(files):
        sims = S[:, fi]
        idx = np.argsort(-sims)[:TOP_K]
        tags = []
        for i in idx:
            concept = anchors[i][0]
            eff = float(sims[i]) * STOPWEIGHT.get(concept, 1.0)
            if eff >= THRESHOLD and sims[i] >= THRESHOLD - 0.02:
                tags.append({"concept": concept, "sim": round(float(sims[i]), 4)})
        rec = {"corpus_file": sf + ".md", "status": "semantic-suggest",
               "review": "pending-shiva-panini", "model": "BAAI/bge-m3",
               "anchor_set": "v3-bilingual",
               "suggested_tags": tags}
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_sugg += len(tags)
print(f"suggestions: {n_sugg} -> {OUT}", flush=True)

# ---- bidirectional search index (step 3 deliverable) ----
# save anchor vectors for runtime search: uk/sa query → nearest corpus texts
index_out = {
    "version": "v3-bilingual",
    "anchors": [{"concept": t, "text": txt} for t, txt in anchors],
    "cognate_uk_terms": cog_uk_terms,
    "corpus_files": files,
}
os.makedirs("/home/agents/GitHub/vault-semantic-mcp/data/index-uk-sa", exist_ok=True)
np.save("/home/agents/GitHub/vault-semantic-mcp/data/index-uk-sa/anchor_matrix.npy", A)
np.save("/home/agents/GitHub/vault-semantic-mcp/data/index-uk-sa/corpus_matrix.npy", M)
json.dump(index_out, open("/home/agents/GitHub/vault-semantic-mcp/data/index-uk-sa/meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print("search index saved to data/index-uk-sa/")
