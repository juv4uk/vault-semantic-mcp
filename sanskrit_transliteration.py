#!/usr/bin/env python3
"""Single source of truth for Sanskrit transliteration used across this
repo's scripts (IAST <-> SLP1 <-> Devanagari).

Extracted 2026-08-28 after the same IAST->SLP1 table (and the same
missing-"ai"/"au"-diphthong bug) had been copy-pasted into THREE
separate scripts (enrich_ontology_from_mw.py, discover_new_concepts.py,
create_new_concept_notes.py) and had to be fixed in three places
separately. Import from here instead of redefining these tables again.
"""
import re

# ---- IAST -> SLP1, deterministic, longest-match-first ----
IAST_TO_SLP1_TABLE = [
    ("kh", "K"), ("gh", "G"), ("ch", "C"), ("jh", "J"),
    ("ṭh", "W"), ("ḍh", "Q"), ("th", "T"), ("dh", "D"), ("ph", "P"), ("bh", "B"),
    ("ai", "E"), ("au", "O"),
    ("ā", "A"), ("ī", "I"), ("ū", "U"), ("ṛ", "f"), ("ṝ", "F"),
    ("ḷ", "x"), ("ḹ", "X"), ("ṃ", "M"), ("ṁ", "M"), ("ḥ", "H"),
    ("ṅ", "N"), ("ñ", "Y"), ("ṭ", "w"), ("ḍ", "q"), ("ṇ", "R"),
    ("ś", "S"), ("ṣ", "z"),
]

# ---- SLP1 -> IAST (reverse; single-pass safe, SLP1 is one char/phoneme) ----
SLP1_TO_IAST_TABLE = [
    ("K", "kh"), ("G", "gh"), ("C", "ch"), ("J", "jh"),
    ("W", "ṭh"), ("Q", "ḍh"), ("T", "th"), ("D", "dh"), ("P", "ph"), ("B", "bh"),
    ("E", "ai"), ("O", "au"),
    ("A", "ā"), ("I", "ī"), ("U", "ū"), ("f", "ṛ"), ("F", "ṝ"),
    ("x", "ḷ"), ("X", "ḹ"), ("M", "ṃ"), ("H", "ḥ"),
    ("N", "ṅ"), ("Y", "ñ"), ("w", "ṭ"), ("q", "ḍ"), ("R", "ṇ"),
    ("S", "ś"), ("z", "ṣ"),
]

# ---- Devanagari -> SLP1 ----
_DEVA_VOWELS_INDEP = {
    "अ": "a", "आ": "A", "इ": "i", "ई": "I", "उ": "u", "ऊ": "U",
    "ऋ": "f", "ॠ": "F", "ऌ": "x", "ॡ": "X",
    "ए": "e", "ऐ": "E", "ओ": "o", "औ": "O",
}
_DEVA_MATRAS = {
    "ा": "A", "ि": "i", "ी": "I", "ु": "u", "ू": "U",
    "ृ": "f", "ॄ": "F", "ॢ": "x", "ॣ": "X",
    "े": "e", "ै": "E", "ो": "o", "ौ": "O",
}
_DEVA_CONSONANTS = {
    "क": "k", "ख": "K", "ग": "g", "घ": "G", "ङ": "N",
    "च": "c", "छ": "C", "ज": "j", "झ": "J", "ञ": "Y",
    "ट": "w", "ठ": "W", "ड": "q", "ढ": "Q", "ण": "R",
    "त": "t", "थ": "T", "द": "d", "ध": "D", "न": "n",
    "प": "p", "फ": "P", "ब": "b", "भ": "B", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v",
    "श": "S", "ष": "z", "स": "s", "ह": "h", "ळ": "L",
}
_DEVA_VIRAMA = "्"
_DEVA_ANUSVARA = "ं"
_DEVA_VISARGA = "ः"
_DEVA_AVAGRAHA = "ऽ"
_DEVA_CANDRABINDU = "ँ"


def iast_to_slp1(term: str) -> str:
    t = term
    for iast, slp1 in IAST_TO_SLP1_TABLE:
        t = t.replace(iast, slp1)
    return t


def slp1_to_iast(term: str) -> str:
    out = []
    for ch in term:
        mapped = ch
        for slp1, iast in SLP1_TO_IAST_TABLE:
            if ch == slp1:
                mapped = iast
                break
        out.append(mapped)
    return "".join(out)


def deva_to_slp1(text: str) -> str:
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in _DEVA_CONSONANTS:
            out.append(_DEVA_CONSONANTS[ch])
            j = i + 1
            if j < n and text[j] == _DEVA_VIRAMA:
                i = j + 1
                continue
            if j < n and text[j] in _DEVA_MATRAS:
                out.append(_DEVA_MATRAS[text[j]])
                i = j + 1
                continue
            out.append("a")
            i += 1
            continue
        if ch in _DEVA_VOWELS_INDEP:
            out.append(_DEVA_VOWELS_INDEP[ch]); i += 1; continue
        if ch == _DEVA_ANUSVARA:
            out.append("M"); i += 1; continue
        if ch == _DEVA_VISARGA:
            out.append("H"); i += 1; continue
        if ch == _DEVA_AVAGRAHA:
            out.append("'"); i += 1; continue
        if ch == _DEVA_CANDRABINDU:
            out.append("~"); i += 1; continue
        if ch.isspace() or ch in ".,;।॥\"'()[]{}0123456789":
            out.append(" "); i += 1; continue
        out.append(" ")  # unknown char (Latin, punctuation, etc.)
        i += 1
    return "".join(out)
