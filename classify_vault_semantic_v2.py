#!/usr/bin/env python3
"""Vault-wide semantic-suggest classifier v2 -- chunk-level tiered
tagging with relative-density normalization and mechanical meta-doc
detection (breadth cap). Designed via a Dreamer->Realist->Critic (Walt
Disney Method) session -- see TAGGING-V2-DESIGN-2026-08-28.md for the
full rationale and the 3 corrections this implements.

Differences from v1 (classify_vault_semantic.py):
  - similarity computed per CHUNK, not on one mean-pooled note vector
  - tags are tiered (core/supporting/adjacent) via density RELATIVE to
    a vault-wide per-concept baseline, not one flat absolute threshold
  - meta-documents (breadth > BREADTH_CAP concepts touched) get a
    capped frontmatter tag set + one hub tag, instead of hundreds of
    tags -- this is the fix for the confirmed v1 bug where index/
    glossary notes got 200+ tags
  - the baseline is VERSIONED (tied to the exact line-count of
    vault_embeddings.jsonl it was computed from), because the vault
    index is not yet complete -- rel_density values computed against
    different baseline_version snapshots are not comparable; a later
    re-tag pass can find and refresh stale-baseline notes instead of
    silently trusting numbers computed against a smaller vault.

Output is a suggestions sidecar only -- does NOT touch any vault note.
Use apply_vault_tags.py --apply to write into frontmatter (dry-run by
default, matches this repo's existing safety pattern -- the vault has
no git safety net).
"""
import json, os, re
import numpy as np

VAULT = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian"
ONTO_DIR = os.path.join(VAULT, "🕉️ Онтологія")
EMB_FILE = "/home/agents/GitHub/vault-semantic-mcp/data/index-vault-live/vault_embeddings.jsonl"
OUT = "/home/agents/GitHub/vault-semantic-mcp/data/vault_semantic_tags_v2.suggestions.jsonl"
EXCLUDE_PARTS = ("Corpus_IAST", "node_modules", ".git", ".obsidian", ".gemini",
                  "🕉️ Онтологія", "Templates")

HIT_THRESHOLD = 0.60           # predicted, not calibrated -- see design doc
CORE_PEAK, CORE_REL = 0.72, 2.0
SUPPORTING_PEAK, SUPPORTING_REL = 0.65, 1.0
BREADTH_CAP = 15               # predicted -- meta-doc if a note touches more concepts than this
FRONTMATTER_CORE_LIMIT = 10    # meta-docs keep at most this many CORE tags in frontmatter
EPS = 1e-9


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


# ---- anchors: same Ontology folder + fields as v1, plus category (needed for hub tags) ----
anchors = []  # (concept_name, anchor_text, category)
for f in sorted(os.listdir(ONTO_DIR)):
    if not f.endswith(".md"):
        continue
    term = f[:-3]
    field, body, aliases = read_note(os.path.join(ONTO_DIR, f))
    deva = field("sanskrit")
    iast = field("iast")
    cat = field("category") or "uncategorized"
    alias_s = " ".join(aliases[:4])
    text = f"{term} {deva} {iast}. {cat}. {alias_s}. {body[:400]}".strip()
    if len(text) < 40:
        continue
    anchors.append((term, text, cat))
print(f"anchors: {len(anchors)}", flush=True)

# ---- vault chunks: keep EVERY chunk, do not mean-pool ----
if not os.path.exists(EMB_FILE):
    raise SystemExit(f"Missing {EMB_FILE} -- run embed_vault_live.py first.")

chunk_vecs = []
by_file_chunk_idx = {}
n_lines = 0
with open(EMB_FILE) as fh:
    for line in fh:
        n_lines += 1
        d = json.loads(line)
        sf = d["source_file"]
        v = np.asarray(d["embedding"], dtype=np.float32)
        idx = len(chunk_vecs)
        chunk_vecs.append(v)
        by_file_chunk_idx.setdefault(sf, []).append(idx)

baseline_version = n_lines  # ties rel_density to the exact snapshot used
files = sorted(by_file_chunk_idx)
C = np.stack(chunk_vecs)  # chunks x dim
C /= np.linalg.norm(C, axis=1, keepdims=True) + EPS
print(
    f"vault files in index: {len(files)}, total chunks: {len(chunk_vecs)}, "
    f"baseline_version(lines): {baseline_version}",
    flush=True,
)

total_md = sum(
    1
    for root, dirs, fnames in os.walk(VAULT)
    for fname in fnames
    if fname.endswith(".md") and not any(p in root for p in EXCLUDE_PARTS)
)
if len(files) < total_md:
    print(
        f"WARNING: index covers {len(files)}/{total_md} vault notes -- "
        f"baseline_version={baseline_version} is tied to THIS partial "
        f"snapshot. Re-run after the index grows; compare a note's stored "
        f"baseline_version against a fresh run's to know which notes need "
        f"re-tagging (their rel_density was computed against a smaller "
        f"vault and is not comparable to a later run's).",
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
    return A / (np.linalg.norm(A, axis=1, keepdims=True) + EPS)


A = enc([a[1] for a in anchors])  # anchors x dim

# ---- chunk-level similarity: anchors x chunks ----
S = A @ C.T
print(f"similarity matrix: {S.shape[0]} anchors x {S.shape[1]} chunks", flush=True)

# ---- vault-wide baseline per concept: fraction of ALL chunks that hit it ----
hits = S >= HIT_THRESHOLD
base = hits.sum(axis=1) / max(len(chunk_vecs), 1)

n_meta = 0
n_tagged = 0
with open(OUT, "w", encoding="utf-8") as out:
    for sf in files:
        idxs = by_file_chunk_idx[sf]
        sub = S[:, idxs]  # anchors x this note's chunks
        coverage = (sub >= HIT_THRESHOLD).sum(axis=1) / len(idxs)
        peak = sub.max(axis=1)
        rel = coverage / (base + EPS)

        touched = np.where(peak >= HIT_THRESHOLD)[0]
        breadth = int(len(touched))

        all_touched = []
        core_or_supporting = []
        for j in touched:
            concept, _, cat = anchors[j]
            p, r = float(peak[j]), float(rel[j])
            if p >= CORE_PEAK and r >= CORE_REL:
                tier = "core"
            elif p >= SUPPORTING_PEAK and r >= SUPPORTING_REL:
                tier = "supporting"
            else:
                tier = "adjacent"
            entry = {"concept": concept, "tier": tier, "peak_sim": round(p, 4), "rel_density": round(r, 4)}
            all_touched.append(entry)
            if tier in ("core", "supporting"):
                core_or_supporting.append((entry, cat))

        all_touched.sort(key=lambda e: -e["peak_sim"])
        is_meta = breadth > BREADTH_CAP

        hub_tag = None
        if is_meta:
            # Rank CORE tags before SUPPORTING (ties broken by peak_sim) so a
            # meta-doc still gets a hub tag even when nothing reaches CORE --
            # e.g. a note whose 66 touched concepts all cap out at
            # "supporting" (moderate similarity, spread thin) would otherwise
            # get zero tags at all, which is as unhelpful as v1's 200-tag bug
            # in the other direction.
            ranked = sorted(core_or_supporting, key=lambda ec: (ec[0]["tier"] != "core", -ec[0]["peak_sim"]))
            frontmatter_tags = [e for e, c in ranked[:FRONTMATTER_CORE_LIMIT]]
            cats = [c for e, c in ranked[:FRONTMATTER_CORE_LIMIT]]
            if cats:
                plurality_cat = max(set(cats), key=cats.count)
                hub_tag = f"index/{plurality_cat}"
        else:
            frontmatter_tags = [e for e, c in core_or_supporting]

        rec = {
            "vault_file": sf,
            "is_meta_doc": is_meta,
            "breadth": breadth,
            "tags": frontmatter_tags,
            "hub_tag": hub_tag,
            "all_touched_concepts": all_touched,
            "status": "semantic-suggest-v2",
            "review": "unreviewed",
            "baseline_version": baseline_version,
        }
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if is_meta:
            n_meta += 1
        if frontmatter_tags or hub_tag:
            n_tagged += 1

print(
    f"done: {len(files)} notes, {n_meta} meta-docs, {n_tagged} notes with "
    f"frontmatter tags -> {OUT}",
    flush=True,
)
