#!/usr/bin/env python3
"""Enrich the vault's 270-concept Ontology notes using Monier-Williams
(external-sources/MWS/mwtranscode/mw.txt).

Finding that motivated this: only 53/270 notes have an `iast:`
frontmatter field, only 3/270 have `category:` -- the note's filename
IS already the IAST term (e.g. dharma.md, abhyāsa.md), so this script
uses the filename, not frontmatter, as the lookup key.

Pipeline: filename (IAST) -> SLP1 (standard deterministic mapping) ->
lookup in MW's <k1>/<k2> headwords -> extract cleaned definition(s) +
part-of-speech (<lex>) -> propose iast/category frontmatter fields +
an enriched body appendix citing MW as the source.

DRY RUN BY DEFAULT (writes nothing) -- report coverage and a preview
of proposed changes. Pass --apply to actually write. The vault has a
daily tar.gz backup (vault-backup.timer) but no git safety net, so
default to caution same as apply_vault_tags.py.
"""
import json, os, re, sys

VAULT = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian"
ONTO_DIR = os.path.join(VAULT, "🕉️ Онтологія")
MW_FILE = "/home/agents/GitHub/vault-semantic-mcp/external-sources/MWS/mwtranscode/mw.txt"
OUT_REPORT = "/home/agents/GitHub/vault-semantic-mcp/data/mw_enrichment_report.jsonl"

# ---- IAST -> SLP1, deterministic, longest-match-first ----
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


def clean_mw_body(text):
    """Strip MW's markup tags, keep readable English gloss text."""
    text = re.sub(r"<info[^>]*/?>", "", text)
    text = re.sub(r"<hom>[^<]*</hom>", "", text)
    text = re.sub(r"<[a-zA-Z][^>]*>", "", text)     # opening tags with attrs
    text = re.sub(r"</[a-zA-Z0-9]+>", "", text)      # closing tags (e.g. </s1>, digits included)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.lstrip("¦").strip()
    return text


def parse_mw(path):
    """Build slp1_key -> list of (pos, gloss) from mw.txt's <L>...<LEND> records."""
    index = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        block = []
        k1 = k2 = None
        for line in f:
            if line.startswith("<L>"):
                block = [line]
                m1 = re.search(r"<k1>([^<]+)", line)
                m2 = re.search(r"<k2>([^<]+)", line)
                k1 = m1.group(1) if m1 else None
                k2 = re.sub(r"/", "", m2.group(1)) if m2 else None  # strip accent marks
            elif line.startswith("<LEND>"):
                body = "".join(block[1:])
                pos_m = re.search(r"<lex[^>]*>([^<]+)</lex>", body)
                pos = pos_m.group(1) if pos_m else ""
                gloss = clean_mw_body(body)
                for key in {k1, k2} - {None}:
                    index.setdefault(key, []).append((pos, gloss))
                block = []
            else:
                block.append(line)
    return index


def read_note_frontmatter(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    if not txt.startswith("---"):
        return {}, txt, txt
    parts = txt.split("---\n", 2)
    if len(parts) < 3:
        return {}, txt, txt
    fm_raw, body = parts[1], parts[2]

    def field(key):
        m = re.search(rf'^{key}:\s*"?([^"\n]+)"?\s*$', fm_raw, re.M)
        return m.group(1).strip() if m else None

    return {"iast": field("iast"), "category": field("category"), "raw_fm": fm_raw}, body, txt


MW_SECTION_MARKER = "## 📖 Monier-Williams (авто-збагачення)"


def pos_label(pos):
    labels = {
        "m.": "іменник, чол. рід", "f.": "іменник, жін. рід", "n.": "іменник, сер. рід",
        "mfn.": "прикметник", "ind.": "незмінне слово", "cl.": "дієслово",
    }
    return labels.get(pos, pos) if pos else "невизначено"


def build_mw_section(term, slp1, pos, senses):
    lines = [f"\n---\n\n{MW_SECTION_MARKER}\n"]
    lines.append(f"*Автоматично додано з Monier-Williams (1899), SLP1-ключ `{slp1}`. "
                 f"Це цитата зовнішнього словника, не редакція власного опису вище.*\n")
    if pos:
        lines.append(f"**Частина мови (MW):** {pos_label(pos)}\n")
    lines.append("**Значення (MW, скорочено):**\n")
    for s in senses[:5]:
        lines.append(f"- {s}\n")
    return "".join(lines)


def main():
    apply = "--apply" in sys.argv[1:]

    print("Parsing Monier-Williams (this takes a moment)...", file=sys.stderr)
    mw_index = parse_mw(MW_FILE)
    print(f"MW index: {len(mw_index)} distinct SLP1 headwords", file=sys.stderr)

    files = sorted(f for f in os.listdir(ONTO_DIR) if f.endswith(".md"))
    print(f"Ontology notes: {len(files)}", file=sys.stderr)

    found = 0
    not_found = []
    results = []

    applied = 0
    skipped_already_enriched = 0

    for f in files:
        term = f[:-3]
        path = os.path.join(ONTO_DIR, f)
        fm, body, full_txt = read_note_frontmatter(path)

        slp1 = iast_to_slp1(term)
        entries = mw_index.get(slp1)
        # karma/karman-style fallback: n-stem citation form
        if (not entries or (len(entries) <= 1 and entries[0][1].lower().startswith("in comp"))) \
                and mw_index.get(slp1 + "n"):
            entries = mw_index.get(slp1 + "n")
        if not entries:
            for suffix in ("a", "As", "i", "u"):
                if slp1.endswith(suffix) and mw_index.get(slp1[: -len(suffix)]):
                    entries = mw_index.get(slp1[: -len(suffix)])
                    break

        if entries:
            found += 1
            top_pos = next((p for p, g in entries if p), "")
            senses = [g for p, g in entries[:5] if g]
            results.append({
                "term": term, "slp1": slp1, "matched": True,
                "pos": top_pos, "n_senses_in_mw": len(entries),
                "senses_preview": senses[:3],
                "had_iast_field": bool(fm.get("iast")),
                "had_category_field": bool(fm.get("category")),
            })

            if apply:
                if MW_SECTION_MARKER in full_txt:
                    skipped_already_enriched += 1
                    continue
                new_body = body.rstrip("\n") + "\n" + build_mw_section(term, slp1, top_pos, senses)
                if full_txt.startswith("---") and fm.get("raw_fm") is not None:
                    fm_raw = fm["raw_fm"]
                    additions = ""
                    if not fm.get("iast"):
                        additions += f"iast: {term}\n"
                    if not fm.get("category") and top_pos:
                        additions += f"category: {pos_label(top_pos)}\n"
                    new_fm = fm_raw.rstrip("\n") + "\n" + additions if additions else fm_raw
                    new_txt = f"---\n{new_fm}---\n{new_body}"
                else:
                    new_txt = new_body
                with open(path, "w", encoding="utf-8") as wf:
                    wf.write(new_txt)
                applied += 1
        else:
            not_found.append(term)
            results.append({"term": term, "slp1": slp1, "matched": False})

    with open(OUT_REPORT, "w", encoding="utf-8") as out:
        for r in results:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nCOVERAGE: {found}/{len(files)} ontology terms found in MW ({found*100//len(files)}%)")
    print(f"Report written to {OUT_REPORT}")
    print(f"\nNot found (first 20 of {len(not_found)}): {not_found[:20]}")

    if not apply:
        print("\nDRY RUN. Re-run with --apply to write iast:/category: fields "
              "and an MW-sourced definition appendix into matched notes.")
        return

    print(f"\nAPPLIED: {applied} notes enriched, {skipped_already_enriched} already had the MW section (skipped).")


if __name__ == "__main__":
    main()
