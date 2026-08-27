#!/usr/bin/env python3
"""One-off fix: enrich_ontology_from_mw.py wrote `category:` (a
grammatical POS label like "іменник, чол. рід") into notes that had no
category before -- but classify_vault_semantic_v2.py reads `category:`
as a SEMANTIC/topical label (e.g. "Darśana / Етика", as in the
original dharma.md) to build hub tags for meta-documents. The two
collided, producing hub tags like "index/іменник, жін. рід".

Fix: rename category: -> mw_pos: in every note that (a) has the MW
enrichment section marker (proof this script touched it) and (b) whose
category value is one of the exact pos_label() outputs this script
could have written -- never touches a genuinely pre-existing semantic
category (only 3/270 notes had one before enrichment).
"""
import os, re, sys

ONTO_DIR = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian/🕉️ Онтологія"
MARKER = "Monier-Williams (авто-збагачення)"
POS_LABELS = {
    "іменник, чол. рід", "іменник, жін. рід", "іменник, сер. рід",
    "прикметник", "незмінне слово", "дієслово", "невизначено",
}


def main():
    apply = "--apply" in sys.argv[1:]
    fixed = 0
    for f in sorted(os.listdir(ONTO_DIR)):
        if not f.endswith(".md"):
            continue
        path = os.path.join(ONTO_DIR, f)
        txt = open(path, encoding="utf-8", errors="replace").read()
        if MARKER not in txt or not txt.startswith("---"):
            continue
        m = re.search(r"^category:\s*(.+)$", txt, re.M)
        if not m or m.group(1).strip() not in POS_LABELS:
            continue
        new_txt = re.sub(r"^category:", "mw_pos:", txt, count=1, flags=re.M)
        fixed += 1
        print(f"  {f}: category: {m.group(1).strip()!r} -> mw_pos:")
        if apply:
            with open(path, "w", encoding="utf-8") as wf:
                wf.write(new_txt)
    if apply:
        print(f"\nAPPLIED: {fixed} files fixed.")
    else:
        print(f"\nDRY RUN: {fixed} files would be fixed. Re-run with --apply.")


if __name__ == "__main__":
    main()
