from pathlib import Path
from incident_triage.retrieval.chunker import parse_frontmatter, chunk_by_section

# Test on one runbook
file_path = Path("data/runbooks/commodity/RUNBOOK-002-price-feed-failure.md")
text = file_path.read_text(encoding="utf-8")
metadata, content = parse_frontmatter(text)

print("=== METADATA ===")
print(metadata)
print("\n=== FIRST 500 CHARS OF CONTENT ===")
print(content[:500])
print("\n=== SECTIONS FOUND ===")
sections = chunk_by_section(content)
for name, section_content in sections:
    print(f"  [{name}]: {len(section_content.split())} words")

file_path = Path("data/runbooks/commodity/RUNBOOK-002-price-feed-failure.md")
text = file_path.read_text(encoding="utf-8")
metadata, content = parse_frontmatter(text)
sections = chunk_by_section(content)
for name, section_content in sections:
    print(f"[{name}]: {section_content[:100]}")