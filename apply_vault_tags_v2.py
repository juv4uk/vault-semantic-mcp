#!/usr/bin/env python3
"""Apply classify_vault_semantic_v2.py's tiered suggestions into vault
notes' YAML frontmatter.

Differences from apply_vault_tags.py (v1):
  - tag strings are CONCEPT-first, tier second: "atman/core",
    "atman/supporting" -- not "core/atman". Obsidian's tag pane groups
    nested tags by the LEFT-most segment, so concept-first means
    clicking "atman" shows every note that touches it at any tier;
    tier-first would fragment one concept across three separate parent
    tags. (Critic correction #1 from the design session.)
  - meta-doc notes (is_meta_doc=true) get their capped tags PLUS one
    hub tag (e.g. "index/vyakarana") -- same merge path as any other
    note, not a special case, per Critic correction #3: nothing here
    bypasses the existing dry-run-by-default apply flow.
  - every touched note gets a `tag_source` frontmatter field
    ("semantic-auto-v2 (unreviewed)") so a reader can tell these tags
    were machine-suggested and not yet reviewed -- v1's applied tags
    carried no such marker once written.

DRY RUN BY DEFAULT. The vault (/mnt/c/.../Obsidian) is not a git repo
-- no version-control safety net -- so this script only *reports* what
it would change unless you pass --apply.

Usage:
  python3 apply_vault_tags_v2.py            # dry run: report only
  python3 apply_vault_tags_v2.py --apply    # actually write frontmatter
"""
import json, os, sys
import yaml

VAULT = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian"
SUGGESTIONS_FILE = "/home/agents/GitHub/vault-semantic-mcp/data/vault_semantic_tags_v2.suggestions.jsonl"
TAG_SOURCE = "semantic-auto-v2 (unreviewed)"


def tag_strings(rec):
    tags = [f"{t['concept']}/{t['tier']}" for t in rec.get("tags", [])]
    if rec.get("hub_tag"):
        tags.append(rec["hub_tag"])
    return tags


def plan():
    """Yield (file_path, existing_tags, new_unique_tags, fm_dict, body, has_frontmatter)."""
    with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        data = json.loads(line.strip())
        tags = tag_strings(data)
        if not tags:
            continue

        file_path = os.path.join(VAULT, data["vault_file"])
        if not os.path.exists(file_path):
            print(f"Warning: could not find {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as mf:
            content = mf.read()

        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) < 3:
                continue
            frontmatter, body = parts[1], parts[2]
            try:
                fm_dict = yaml.safe_load(frontmatter) or {}
            except Exception:
                fm_dict = {}
            existing_tags = fm_dict.get("tags", [])
            if isinstance(existing_tags, str):
                existing_tags = [existing_tags]
            if not isinstance(existing_tags, list):
                existing_tags = []
            new_unique_tags = [t for t in tags if t not in existing_tags]
            already_marked = fm_dict.get("tag_source") == TAG_SOURCE
            if not new_unique_tags and already_marked:
                continue
            yield file_path, existing_tags, new_unique_tags, fm_dict, body, True
        else:
            yield file_path, [], tags, {}, content, False


def main():
    apply = "--apply" in sys.argv[1:]
    changed_files = 0
    total_tags = 0

    for file_path, existing_tags, new_unique_tags, fm_dict, body, has_frontmatter in plan():
        rel = os.path.relpath(file_path, VAULT)
        print(f"  {rel}: +{new_unique_tags}")
        changed_files += 1
        total_tags += len(new_unique_tags)

        if not apply:
            continue

        if has_frontmatter:
            fm_dict["tags"] = existing_tags + new_unique_tags
            fm_dict["tag_source"] = TAG_SOURCE
            new_frontmatter = yaml.dump(fm_dict, allow_unicode=True, default_flow_style=False, sort_keys=False)
            new_content = f"---\n{new_frontmatter}---\n{body}"
        else:
            new_frontmatter = yaml.dump(
                {"tags": new_unique_tags, "tag_source": TAG_SOURCE},
                allow_unicode=True, default_flow_style=False,
            )
            new_content = f"---\n{new_frontmatter}---\n\n{body}"

        with open(file_path, "w", encoding="utf-8") as out:
            out.write(new_content)

    if apply:
        print(f"\nDone! Updated {changed_files} files, injected {total_tags} new tags.")
    else:
        print(f"\nDRY RUN: {changed_files} files would change, {total_tags} tags would be injected.")
        print("Re-run with --apply to actually write.")


if __name__ == "__main__":
    main()
