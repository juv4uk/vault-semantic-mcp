#!/usr/bin/env python3
"""Discover candidate NEW Ontology concepts from the real classical
Sanskrit corpus (shiva-sutras/ksetra/sanskritworld_texts, Devanagari),
rather than enriching the 270 that already exist.

Method: Devanagari -> SLP1 (deterministic transliteration) -> tokenize
on whitespace/punctuation -> frequency count across the whole corpus
-> keep only tokens that are real MW headwords (filters transliteration
noise and inflectional junk) -> drop anything already covered by one
of the 270 Ontology concepts (by SLP1 key, same mapping used in
enrich_ontology_from_mw.py) -> rank what's left by corpus frequency.

This does NOT create new Ontology notes -- it only proposes candidates
for review, ranked by real usage evidence. Creating a new concept note
is a bigger, more consequential step than enriching an existing one
(new authority claim, not just added citation) and should go through
the same "propose first, apply on confirmation" pattern as the rest of
this repo.
"""
import json, os, re, sys
from collections import Counter

from sanskrit_transliteration import deva_to_slp1, iast_to_slp1

CORPUS_DIR = "/home/agents/GitHub/shiva-sutras/ksetra/sanskritworld_texts"
ONTO_DIR = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian/🕉️ Онтологія"
MW_FILE = "/home/agents/GitHub/vault-semantic-mcp/external-sources/MWS/mwtranscode/mw.txt"
OUT = "/home/agents/GitHub/vault-semantic-mcp/data/new_concept_candidates.jsonl"

CONTENT_POS = {"m.", "f.", "n.", "mfn.", "mf.", "mn.", "fn."}  # nouns/adjectives only


def parse_mw_keys(path):
    """Return {slp1_key: pos} for entries whose FIRST recorded sense
    has a content-word part of speech -- excludes ind. (particles),
    pronouns, and unlabeled function-word entries so frequency ranking
    doesn't just surface iti/tathA/eva/yena/etc."""
    keys = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        k1 = None
        for line in f:
            if line.startswith("<L>"):
                m1 = re.search(r"<k1>([^<]+)", line)
                k1 = m1.group(1) if m1 else None
            elif k1 and "<lex" in line:
                pos_m = re.search(r"<lex[^>]*>([^<]+)</lex>", line)
                pos = pos_m.group(1) if pos_m else None
                if k1 not in keys and pos in CONTENT_POS:
                    keys[k1] = pos
                k1 = None  # only look at the first line after <L> for pos
            elif line.startswith("<LEND>"):
                k1 = None
    return keys


def ontology_slp1_terms():
    covered = set()
    for f in os.listdir(ONTO_DIR):
        if not f.endswith(".md"):
            continue
        covered.add(iast_to_slp1(f[:-3]))
    return covered


def main():
    print("Loading MW headword set...", file=sys.stderr)
    mw_keys = parse_mw_keys(MW_FILE)
    print(f"MW headwords: {len(mw_keys)}", file=sys.stderr)

    covered = ontology_slp1_terms()
    print(f"Already-covered ontology terms (SLP1): {len(covered)}", file=sys.stderr)

    counter = Counter()
    n_files = 0
    for root, dirs, files in os.walk(CORPUS_DIR):
        for fname in files:
            if not fname.endswith(".txt"):
                continue
            n_files += 1
            path = os.path.join(root, fname)
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            slp1_text = deva_to_slp1(text)
            for tok in slp1_text.split():
                if len(tok) >= 3:
                    counter[tok] += 1

    print(f"Corpus files scanned: {n_files}, distinct tokens: {len(counter)}", file=sys.stderr)

    # Observed noise (2026-08-28 run): MW mis-tags these as nominal via a
    # rare homonym entry, but their dominant real-corpus use is as a
    # pronoun/particle inflected form -- targeted list from the actual
    # top-30 output, not a speculative general stopword list.
    PRONOUN_PARTICLE_NOISE = {
        "iti", "eva", "tena", "atra", "yasya", "saha", "Bavanti", "mayA",
        "sati", "eza", "prati", "tat", "ityAdi", "asti", "pra", "purA",
        "anena", "tata",
    }

    candidates = []
    for tok, freq in counter.most_common():
        if tok not in mw_keys:
            continue  # not a real content-word MW headword -- noise, inflection, or function word
        if tok in covered:
            continue  # already have this concept
        if tok in PRONOUN_PARTICLE_NOISE:
            continue
        candidates.append((tok, freq, mw_keys[tok]))
        if len(candidates) >= 200:
            break

    with open(OUT, "w", encoding="utf-8") as out:
        for tok, freq, pos in candidates:
            out.write(json.dumps({"slp1": tok, "corpus_freq": freq, "pos": pos}, ensure_ascii=False) + "\n")

    print(f"\nTop 30 new-concept candidates (MW noun/adjective headwords, not yet in Ontology, ranked by corpus frequency):")
    for tok, freq, pos in candidates[:30]:
        print(f"  {freq:5d}  {tok:20s} {pos}")
    print(f"\nFull list ({len(candidates)}): {OUT}")


if __name__ == "__main__":
    main()
