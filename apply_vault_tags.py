#!/usr/bin/env python3
"""Apply classify_vault_semantic.py's suggestions into vault notes'
YAML frontmatter -- same merge logic as apply_tags.py (shiva-sutras
corpus), generalized to arbitrary vault-relative paths.

DRY RUN BY DEFAULT. The vault (/mnt/c/.../Obsidian) is not a git repo
-- unlike shiva-sutras/ksetra, there is no version-control safety net
to recover from a bad write, so this script only *reports* what it
would change unless you pass --apply.

Usage:
  python3 apply_vault_tags.py            # dry run: report only
  python3 apply_vault_tags.py --apply    # actually write frontmatter
"""
import json, os, sys
import yaml

VAULT = "/mnt/c/Users/user/Downloads/chatGPT-2023-2026/Obsidian"
SUGGESTIONS_FILE = "/home/agents/GitHub/vault-semantic-mcp/data/vault_semantic_tags.suggestions.jsonl"


def plan():
    """Yield (file_path, new_unique_tags) for every note that would change."""
    with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        data = json.loads(line.strip())
        tags = [t["concept"] for t in data.get("suggested_tags", [])]
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
            if not new_unique_tags:
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
            new_frontmatter = yaml.dump(fm_dict, allow_unicode=True, default_flow_style=False, sort_keys=False)
            new_content = f"---\n{new_frontmatter}---\n{body}"
        else:
            new_frontmatter = yaml.dump({"tags": new_unique_tags}, allow_unicode=True, default_flow_style=False)
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
