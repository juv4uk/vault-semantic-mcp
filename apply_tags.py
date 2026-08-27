import json
import os
import yaml

SUGGESTIONS_FILE = "/home/agents/GitHub/shiva-sutras/ksetra/corpus_semantic_tags.suggestions.jsonl"
CORPUS_MD_DIR = "/home/agents/GitHub/shiva-sutras/ksetra/sanskritworld_texts_md/"
BASE_DIR = "/home/agents/GitHub/shiva-sutras/ksetra/"

def apply_tags():
    print("Reading semantic suggestions...")
    with open(SUGGESTIONS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    updated_files = 0
    total_tags_injected = 0
    
    for line in lines:
        data = json.loads(line.strip())
        tags = [t["concept"] for t in data.get("suggested_tags", [])]
        if not tags:
            continue
            
        corpus_file = data["corpus_file"]
        
        # Determine actual file path
        if os.path.exists(os.path.join(CORPUS_MD_DIR, corpus_file)):
            file_path = os.path.join(CORPUS_MD_DIR, corpus_file)
        elif os.path.exists(os.path.join(BASE_DIR, corpus_file)):
            file_path = os.path.join(BASE_DIR, corpus_file)
        else:
            print(f"Warning: Could not find {corpus_file}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as mf:
            content = mf.read()
            
        # Basic YAML frontmatter manipulation without losing formatting
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body = parts[2]
                
                # Check existing tags to avoid duplicates
                try:
                    fm_dict = yaml.safe_load(frontmatter) or {}
                except:
                    fm_dict = {}
                
                existing_tags = fm_dict.get("tags", [])
                if isinstance(existing_tags, str):
                    existing_tags = [existing_tags]
                if not isinstance(existing_tags, list):
                    existing_tags = []
                
                new_unique_tags = [t for t in tags if t not in existing_tags]
                if not new_unique_tags:
                    continue # already has all tags
                    
                # Reconstruct frontmatter safely
                combined_tags = existing_tags + new_unique_tags
                fm_dict["tags"] = combined_tags
                
                # Write back
                new_frontmatter = yaml.dump(fm_dict, allow_unicode=True, default_flow_style=False, sort_keys=False)
                new_content = f"---\n{new_frontmatter}---\n{body}"
                
                with open(file_path, 'w', encoding='utf-8') as out:
                    out.write(new_content)
                
                updated_files += 1
                total_tags_injected += len(new_unique_tags)
        else:
            # No frontmatter, add it
            new_frontmatter = yaml.dump({"tags": tags}, allow_unicode=True, default_flow_style=False)
            new_content = f"---\n{new_frontmatter}---\n\n{content}"
            with open(file_path, 'w', encoding='utf-8') as out:
                out.write(new_content)
            updated_files += 1
            total_tags_injected += len(tags)
            
    print(f"Done! Updated {updated_files} files, injected {total_tags_injected} new tags.")

if __name__ == "__main__":
    apply_tags()
