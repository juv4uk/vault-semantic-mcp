#!/usr/bin/env python3
"""Second enrichment pass, targeting ONLY the 34 terms Monier-Williams
didn't cover (see data/mw_enrichment_report.jsonl) -- try Apte (1890)
instead. Apte's citation form differs from MW's (nominative -H ending,
e.g. DarmaH not Darma) and its markup differs ({#...#}, {@N@}, {%...%}
instead of MW's <s>/<lex>/<info> tags), so this is a separate parser,
not a reuse of enrich_ontology_from_mw.py's.

DRY RUN BY DEFAULT, same safety pattern as the rest of this repo.
"""
import json, os, re, sys

VAULT = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian"
ONTO_DIR = os.path.join(VAULT, "🕉️ Онтологія")
AP90_FILE = "/home/agents/GitHub/vault-semantic-mcp/external-sources/AP90/issues/markup_fix/ap90_fixed.txt"
MW_REPORT = "/home/agents/GitHub/vault-semantic-mcp/data/mw_enrichment_report.jsonl"
OUT_REPORT = "/home/agents/GitHub/vault-semantic-mcp/data/ap90_enrichment_report.jsonl"

IAST_TO_SLP1 = [
    ("kh", "K"), ("gh", "G"), ("ch", "C"), ("jh", "J"),
    ("ṭh", "W"), ("ḍh", "Q"), ("th", "T"), ("dh", "D"), ("ph", "P"), ("bh", "B"),
    ("ā", "A"), ("ī", "I"), ("ū", "U"), ("ṛ", "f"), ("ṝ", "F"),
    ("ḷ", "x"), ("ḹ", "X"), ("ṃ", "M"), ("ṁ", "M"), ("ḥ", "H"),
    ("ṅ", "N"), ("ñ", "Y"), ("ṭ", "w"), ("ḍ", "q"), ("ṇ", "R"),
    ("ś", "S"), ("ṣ", "z"),
]


def iast_to_slp1(term):
    t = term
    for iast, slp1 in IAST_TO_SLP1:
        t = t.replace(iast, slp1)
    return t


def clean_ap90_body(text):
    text = re.sub(r"<lbinfo[^>]*/?>", "", text)
    text = re.sub(r"<[a-zA-Z][^>]*>", "", text)
    text = re.sub(r"</[a-zA-Z0-9]+>", "", text)
    text = re.sub(r"\{[#@%]+", "", text)
    text = re.sub(r"[#@%]+\}", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_ap90(path):
    index = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        block = []
        k1 = k2 = None
        for line in f:
            if line.startswith("<L>"):
                block = [line]
                m1 = re.search(r"<k1>([^<]+)", line)
                k1 = m1.group(1) if m1 else None
            elif line.startswith("<LEND>"):
                body = "".join(block[1:])
                gloss = clean_ap90_body(body)
                if k1:
                    index.setdefault(k1, []).append(gloss)
                block = []
            else:
                block.append(line)
    return index


def get_not_found_terms():
    terms = []
    with open(MW_REPORT, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if not d.get("matched"):
                terms.append(d["term"])
    return terms


def main():
    apply = "--apply" in sys.argv[1:]

    print("Parsing Apte (this takes a moment)...", file=sys.stderr)
    ap_index = parse_ap90(AP90_FILE)
    print(f"AP90 index: {len(ap_index)} distinct SLP1 headwords", file=sys.stderr)

    targets = get_not_found_terms()
    print(f"Targeting {len(targets)} MW-not-found terms", file=sys.stderr)

    found = 0
    applied = 0
    results = []

    for term in targets:
        slp1 = iast_to_slp1(term)
        candidates = [slp1, slp1 + "H", slp1 + "am", slp1 + "A"]
        entries = None
        matched_key = None
        for c in candidates:
            if c in ap_index:
                entries = ap_index[c]
                matched_key = c
                break

        if entries:
            found += 1
            results.append({
                "term": term, "slp1_tried": matched_key, "matched": True,
                "n_senses": len(entries), "preview": entries[:2],
            })
            if apply:
                path = os.path.join(ONTO_DIR, term + ".md")
                if not os.path.exists(path):
                    continue
                txt = open(path, encoding="utf-8", errors="replace").read()
                if "Apte (авто-збагачення)" in txt:
                    continue
                section = (
                    f"\n---\n\n## 📖 Apte (авто-збагачення)\n"
                    f"*Автоматично додано з Apte (1890), SLP1-ключ `{matched_key}` "
                    f"(MW цього терміну не мав). Цитата зовнішнього словника.*\n\n"
                    f"**Значення (Apte, скорочено):**\n"
                )
                for s in entries[:3]:
                    section += f"- {s}\n"
                with open(path, "w", encoding="utf-8") as wf:
                    wf.write(txt.rstrip("\n") + "\n" + section)
                applied += 1
        else:
            results.append({"term": term, "slp1_tried": candidates, "matched": False})

    with open(OUT_REPORT, "w", encoding="utf-8") as out:
        for r in results:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nAPTE COVERAGE OF MW-GAPS: {found}/{len(targets)}")
    print(f"Report: {OUT_REPORT}")
    still_missing = [r["term"] for r in results if not r["matched"]]
    print(f"Still not found ({len(still_missing)}): {still_missing}")
    if apply:
        print(f"\nAPPLIED: {applied} notes enriched.")
    else:
        print("\nDRY RUN. Re-run with --apply to write.")


if __name__ == "__main__":
    main()
