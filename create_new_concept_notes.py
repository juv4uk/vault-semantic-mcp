#!/usr/bin/env python3
"""Create new Ontology notes for the top candidates found by
discover_new_concepts.py, after manual review filtered out residual
pronoun/verb/particle noise (see comms-log / conversation for the
exclusion list -- not re-derived here, hardcoded from that review).

Each note is clearly marked as auto-generated from MW, in the same
visual format as the existing hand-authored notes (blockquote intro +
tags:) but with an explicit note that the Ukrainian gloss is a rough
MW-based rendering, not curated the way the other 269 notes are --
this is the same "don't silently promote a hypothesis to the status of
curated fact" discipline used throughout this session (yantra.my's
epistemic-status tagging, the semantic-suggest sidecar convention).

DRY RUN BY DEFAULT.
"""
import os, re, sys

ONTO_DIR = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian/🕉️ Онтологія"
MW_FILE = "/home/agents/GitHub/vault-semantic-mcp/external-sources/MWS/mwtranscode/mw.txt"

# Reviewed 2026-08-28: top candidates from data/new_concept_candidates.jsonl,
# residual pronoun/verb/particle noise excluded by hand after inspection.
SELECTED = [
    "svAhA", "wIkA", "soma", "BAzya", "brahma", "devA", "deva", "wippaRI",
    "prajYApAramitA", "sADu", "anuvyAKyAna", "pfzWa", "veda", "devI",
    "nyAyasuDA", "vEdya", "kulaputra", "vastu", "devatA", "kOSika",
]

SLP1_TO_IAST = [
    ("K", "kh"), ("G", "gh"), ("C", "ch"), ("J", "jh"),
    ("W", "ṭh"), ("Q", "ḍh"), ("T", "th"), ("D", "dh"), ("P", "ph"), ("B", "bh"),
    ("A", "ā"), ("I", "ī"), ("U", "ū"), ("f", "ṛ"), ("F", "ṝ"),
    ("x", "ḷ"), ("X", "ḹ"), ("E", "ai"), ("O", "au"), ("M", "ṃ"), ("H", "ḥ"),
    ("N", "ṅ"), ("Y", "ñ"), ("w", "ṭ"), ("q", "ḍ"), ("R", "ṇ"),
    ("S", "ś"), ("z", "ṣ"),
]


def slp1_to_iast(term):
    # two-char SLP1 codes don't exist (SLP1 is one-char-per-phoneme),
    # so a straight single-pass replace is safe here (unlike IAST->SLP1
    # which had to handle multi-char IAST digraphs).
    out = []
    for ch in term:
        mapped = ch
        for slp1, iast in SLP1_TO_IAST:
            if ch == slp1:
                mapped = iast
                break
        out.append(mapped)
    return "".join(out)


def clean_mw_body(text):
    text = re.sub(r"<info[^>]*/?>", "", text)
    text = re.sub(r"<hom>[^<]*</hom>", "", text)
    text = re.sub(r"<[a-zA-Z][^>]*>", "", text)
    text = re.sub(r"</[a-zA-Z0-9]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lstrip("¦").strip()


def lookup_mw(path, target_keys):
    result = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        block = []
        k1 = k2 = None
        for line in f:
            if line.startswith("<L>"):
                block = [line]
                m1 = re.search(r"<k1>([^<]+)", line)
                m2 = re.search(r"<k2>([^<]+)", line)
                k1 = m1.group(1) if m1 else None
                k2 = re.sub(r"/", "", m2.group(1)) if m2 else None
            elif line.startswith("<LEND>"):
                body = "".join(block[1:])
                for key in {k1, k2} - {None}:
                    if key in target_keys:
                        pos_m = re.search(r"<lex[^>]*>([^<]+)</lex>", body)
                        pos = pos_m.group(1) if pos_m else ""
                        gloss = clean_mw_body(body)
                        result.setdefault(key, []).append((pos, gloss))
                block = []
            else:
                block.append(line)
    return result


def build_note(slp1, iast, pos, senses):
    top_gloss = senses[0][1] if senses else ""
    lines = []
    lines.append("---\ntags:\n")
    lines.append(f"  - {iast}\n---\n")
    lines.append(f"# {iast}\n\n")
    lines.append(
        f"> **{iast}** (санскр. {iast}, SLP1 `{slp1}`) — *автоматично додано з "
        f"Monier-Williams, потребує людської перевірки/переформулювання, "
        f"не куратор-написаний опис як інші нотатки цієї Онтології.*\n"
    )
    lines.append(f"> **MW gloss:** {top_gloss[:200]}\n---\n\n")
    lines.append("## 🔗 Пов'язані поняття\n\n---\n\n")
    lines.append("## 📑 Згадки у сховищі (Backlinks)\n\n")
    lines.append(f"\n---\n\n## 📖 Monier-Williams (авто-збагачення)\n")
    lines.append(
        f"*Автоматично додано, SLP1-ключ `{slp1}`. Знайдено як частотний "
        f"кандидат у класичному корпусі (shiva-sutras/ksetra/sanskritworld_texts) "
        f"через `discover_new_concepts.py`, не в жодній наявній нотатці "
        f"Онтології.*\n"
    )
    if pos:
        lines.append(f"**Частина мови (MW):** {pos}\n")
    lines.append("**Значення (MW, скорочено):**\n")
    for p, g in senses[:5]:
        lines.append(f"- {g}\n")
    return "".join(lines)


def main():
    apply = "--apply" in sys.argv[1:]

    print("Parsing MW for selected terms...", file=sys.stderr)
    mw = lookup_mw(MW_FILE, set(SELECTED))

    created = []
    for slp1 in SELECTED:
        iast = slp1_to_iast(slp1)
        path = os.path.join(ONTO_DIR, iast + ".md")
        entries = mw.get(slp1, [])
        top_pos = next((p for p, g in entries if p), "")
        note = build_note(slp1, iast, top_pos, entries)
        exists = os.path.exists(path)
        created.append((slp1, iast, exists, len(entries)))
        print(f"  {'[EXISTS, skip]' if exists else '[NEW]':16s} {iast}.md  (MW senses: {len(entries)})")
        if apply and not exists:
            with open(path, "w", encoding="utf-8") as f:
                f.write(note)

    n_new = sum(1 for _, _, exists, _ in created if not exists)
    if apply:
        print(f"\nAPPLIED: {n_new} new notes created.")
    else:
        print(f"\nDRY RUN: {n_new} new notes would be created. Re-run with --apply.")


if __name__ == "__main__":
    main()
