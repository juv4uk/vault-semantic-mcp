#!/usr/bin/env python3
"""lookup-concept — consumer for the semantic-suggest sidecar.

Usage:
  python3 lookup_concept.py anumāna            # all texts tagged with concept
  python3 lookup_concept.py --file kAshikā     # reverse: tags of one file
  python3 lookup_concept.py --search "серце"   # uk/sa free-text → nearest texts

Reads ONLY the processed sidecar + embeddings index. Never recomputes.
"""
import json, sys, os
import numpy as np

SIDECAR = "/home/agents/GitHub/shiva-sutras/ksetra/corpus_semantic_tags.suggestions.jsonl"
INDEX_DIR = "/home/agents/GitHub/vault-semantic-mcp/data/index-uk-sa"
EMB_FILE = "/home/agents/GitHub/vault-semantic-mcp/data/sanskrit_embeddings.jsonl"

def load_sidecar():
    recs = []
    with open(SIDECAR, encoding="utf-8") as f:
        for line in f:
            recs.append(json.loads(line))
    return recs

def by_concept(recs, concept):
    hits = []
    for r in recs:
        for t in r.get("suggested_tags", []):
            if t["concept"].lower() == concept.lower():
                hits.append((r["corpus_file"], t["sim"], r["status"]))
    return sorted(hits, key=lambda x: -x[1])

def by_file(recs, needle):
    out = []
    for r in recs:
        if needle.lower() in r["corpus_file"].lower():
            tags = ", ".join(f"{t['concept']}({t['sim']})" for t in r["suggested_tags"])
            out.append(f"  {r['corpus_file']}\n    → {tags or '(no suggestions)'}")
    return out

def free_search(query):
    """Embed the query on GPU (one text — negligible load), rank corpus."""
    sys.path.insert(0, "/home/agents/GitHub/vault-semantic-mcp")
    from embeddings import BGEEmbedder
    emb = BGEEmbedder("/home/agents/GitHub/vault-semantic-mcp/config.json")
    q = np.asarray(emb.model.encode([query], max_length=256,
                    return_dense=True, return_sparse=False,
                    return_colbert_vecs=False)["dense_vecs"][0], dtype=np.float32)
    q /= np.linalg.norm(q) + 1e-9

    M = np.load(os.path.join(INDEX_DIR, "corpus_matrix.npy"))
    meta = json.load(open(os.path.join(INDEX_DIR, "meta.json"), encoding="utf-8"))
    files = meta["corpus_files"]
    # embeddings jsonl is chunk-level; mean per file already == corpus_matrix rows order? 
    # corpus_matrix was built from acc dict keyed by file stem; meta.json preserves order.
    sims = M @ q
    ranked = sorted(zip(files, sims), key=lambda x: -x[1])[:10]
    return ranked

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return

    recs = load_sidecar()

    if args[0] == "--file":
        for line in by_file(recs, args[1]): print(line)
        return

    if args[0] == "--search":
        ranked = free_search(args[1])
        print(f"Пошук «{args[1]}» — найближчі тексти корпусу:")
        for f, sim in ranked:
            print(f"  {sim:.3f}  {f}")
        return

    concept = args[0]
    hits = by_concept(recs, concept)
    if not hits:
        print(f"Концепт «{concept}» — пропозицій нема (ще не embedded або нижче порогу).")
        return
    print(f"«{concept}» — {len(hits)} текст(ів):")
    for f, sim, status in hits:
        print(f"  {sim:.3f}  [{status}]  {f}")

if __name__ == "__main__":
    main()
