#!/usr/bin/env python3
"""Experiment: do Devanagari-rich anchors improve semantic suggestions?

Hypothesis (owner, 2026-08-22): BGE-M3 works better with Devanagari.
Corpus chunks ARE already Devanagari; the anchors were Ukrainian+IAST.
Compare three anchor sets over the same corpus vectors:
  v1 = note body as-is            (current production behavior)
  v2 = frontmatter only           (title + देवनागरी + iast + category + aliases)
  v3 = frontmatter + body         (bilingual hybrid)
"""
import json, os, re, sys
import numpy as np

VAULT = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian"
ONTO_DIR = os.path.join(VAULT, "🕉️ Онтологія")
EMB_FILE = "/home/agents/GitHub/vault-semantic-mcp/data/sanskrit_embeddings.jsonl"
OUT = "/home/agents/GitHub/shiva-sutras/ksetra/corpus_semantic_tags.experiment.jsonl"
TOP_K = 3
THRESHOLD = 0.55
STOPWEIGHT = {"vākya": 0.90}

def read_note(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    fm, body = {}, txt
    if txt.startswith('---'):
        parts = txt.split('---', 2)
        if len(parts) == 3:
            fm_raw, body = parts[1], parts[2]
    body = re.sub(r'```.*?```', '', body, flags=re.S)
    body = re.sub(r'\s+', ' ', body).strip()
    # minimal YAML scalars from the known schema
    def field(key):
        m = re.search(rf'^{key}:\s*"?([^"\n]+)"?\s*$', fm_raw, re.M)
        return m.group(1).strip() if m else ''
    aliases = re.findall(r'-\s*"([^"]+)"', fm_raw)
    return fm, body, field, aliases

anchors = []
for f in sorted(os.listdir(ONTO_DIR)):
    if not f.endswith('.md'):
        continue
    term = f[:-3]
    fm, body, field, aliases = read_note(os.path.join(ONTO_DIR, f))
    deva = field('sanskrit')
    iast = field('iast')
    cat = field('category')
    alias_s = ' '.join(aliases[:4])
    v1 = f"{term}. {body[:500]}"
    v2 = f"{term} {deva} {iast}. {cat}. {alias_s}".strip()
    v3 = f"{term} {deva} {iast}. {cat}. {body[:400]}".strip()
    if len(body) < 40:
        continue
    anchors.append((term, {'v1': v1, 'v2': v2, 'v3': v3}))
print(f"anchors: {len(anchors)}", flush=True)

# ---- corpus per-file mean vectors (CPU) ----
acc = {}
with open(EMB_FILE) as fh:
    for line in fh:
        d = json.loads(line)
        sf = d['source_file'].rsplit('.', 1)[0]
        acc.setdefault(sf, []).append(np.asarray(d['embedding'], dtype=np.float32))
files = sorted(acc)
M = np.stack([np.mean(acc[s], axis=0) for s in files])
M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-9
print(f"corpus files: {len(files)}", flush=True)

# ---- embed the three anchor sets ----
from embeddings import BGEEmbedder
emb = BGEEmbedder("/home/agents/GitHub/vault-semantic-mcp/config.json")

def embed_texts(texts):
    res = emb.model.encode(texts, batch_size=8, max_length=256,
                           return_dense=True, return_sparse=False, return_colbert_vecs=False)
    A = np.asarray(res['dense_vecs'], dtype=np.float32)
    return A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9)

sets = {}
for version in ('v1', 'v2', 'v3'):
    sets[version] = embed_texts([a[1][version] for a in anchors])
    print(f"embedded anchors {version}", flush=True)

def suggest(A):
    out = {}
    S = A @ M.T
    for fi, sf in enumerate(files):
        sims = S[:, fi]
        idx = np.argsort(-sims)[:TOP_K]
        tags = []
        for i in idx:
            concept = anchors[i][0]
            eff = float(sims[i]) * STOPWEIGHT.get(concept, 1.0)
            if eff >= THRESHOLD and sims[i] >= THRESHOLD - 0.02:
                tags.append({"concept": concept, "sim": round(float(sims[i]), 4)})
        if tags:
            out[sf] = tags
    return out

results = {v: suggest(sets[v]) for v in ('v1', 'v2', 'v3')}

# ---- comparison ----
print("\n=== FILES WITH SUGGESTIONS ===")
for v in ('v1', 'v2', 'v3'):
    print(f"  {v}: {len(results[v])}")

cc = {v: __import__('collections').Counter() for v in ('v1','v2','v3')}
for v in ('v1','v2','v3'):
    for sf, tags in results[v].items():
        for t in tags:
            cc[v][t['concept']] += 1
print("\n=== TOP CONCEPTS PER SET ===")
for v in ('v1','v2','v3'):
    print(f"  {v}: {dict(cc[v].most_common(6))}")

# agreement / new hits between v1 and v3
both = same = new_in_v3 = lost_in_v3 = 0
examples_new = []
for sf in files:
    t1 = {t['concept'] for t in results['v1'].get(sf, [])}
    t3 = {t['concept'] for t in results['v3'].get(sf, [])}
    if not t1 and not t3:
        continue
    if t1 == t3:
        same += 1
    else:
        if t3 - t1:
            new_in_v3 += 1
            if len(examples_new) < 10:
                examples_new.append((sf, sorted(t3 - t1), round(max(
                    [t['sim'] for tt in [t3-t1] for t in results['v3'].get(sf,[]) if t['concept'] in (t3-t1)] or [0]), 3)))
        if t1 - t3:
            lost_in_v3 += 1

print(f"\n=== V1 → V3 DIFF ===\n  identical: {same}\n  files with NEW v3 tags: {new_in_v3}\n  files LOST v3 tags vs v1: {lost_in_v3}")
for sf, concepts, sim in examples_new:
    print(f"  + {sf}: {concepts}")

# write experiment output using v3 (best hypothesis)
with open(OUT, 'w', encoding='utf-8') as out:
    for fi, sf in enumerate(files):
        sims = sets['v3'] @ M[fi]
        idx = np.argsort(-sims)[:TOP_K]
        tags = [{"concept": anchors[i][0], "sim": round(float(sims[i]), 4)}
                for i in idx if sims[i] >= THRESHOLD]
        rec = {"corpus_file": sf + ".md", "status": "semantic-suggest",
               "review": "pending-shiva-panini", "model": "BAAI/bge-m3",
               "anchor_set": "v3-bilingual",
               "suggested_tags": tags}
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"\nwritten: {OUT}")
