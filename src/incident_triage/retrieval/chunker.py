import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Chunk:
    content: str
    doc_id: str
    doc_type: str
    team: str
    incident_family: str
    section: str
    source_file: str
    systems: list[str]
    severity_range: list[str]
    status: str
    related_runbook: Optional[str] = None


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and return metadata dict and remaining content."""
    pattern = r"^---\n(.*?)\n---\n(.*)$"
    match = re.match(pattern, text, re.DOTALL)
    if not match:
        return {}, text
    try:
        metadata = yaml.safe_load(match.group(1))
        content = match.group(2)
        return metadata, content
    except yaml.YAMLError:
        return {}, text


def chunk_by_section(content: str) -> list[tuple[str, str]]:
    """
    Split markdown content by ## headers.
    Returns list of (section_name, section_content) tuples.
    """
    sections = []
    current_section = "overview"
    current_content = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_content:
                sections.append((
                    current_section,
                    "\n".join(current_content).strip()
                ))
            current_section = line.replace("## ", "").strip().lower()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections.append((
            current_section,
            "\n".join(current_content).strip()
        ))

    return [(name, content) for name, content in sections if content.strip()]


def chunk_document(file_path: Path) -> list[Chunk]:
    """Parse a markdown file and return list of chunks with metadata."""
    text = file_path.read_text(encoding="utf-8")
    metadata, content = parse_frontmatter(text)

    if not metadata:
        print(f"Warning: No frontmatter found in {file_path}")
        return []

    sections = chunk_by_section(content)
    chunks = []

    for section_name, section_content in sections:
        # Skip very short sections — not useful for retrieval
        if len(section_content.split()) < 10:
            continue

        chunk = Chunk(
            content=section_content,
            doc_id=metadata.get("doc_id", file_path.stem),
            doc_type=metadata.get("doc_type", "unknown"),
            team=metadata.get("team", "unknown"),
            incident_family=metadata.get("incident_family", "unknown"),
            section=section_name,
            source_file=str(file_path),
            systems=metadata.get("systems", []),
            severity_range=metadata.get("severity_range", []),
            status=metadata.get("status", "unknown"),
            related_runbook=metadata.get("related_runbook"),
        )
        chunks.append(chunk)

    return chunks


def chunk_corpus(data_dir: Path) -> list[Chunk]:
    """Walk data directory and chunk all markdown files."""
    all_chunks = []
    markdown_files = list(data_dir.rglob("*.md"))

    print(f"Found {len(markdown_files)} markdown files")

    for file_path in markdown_files:
        if file_path.name == ".gitkeep":
            continue
        chunks = chunk_document(file_path)
        all_chunks.extend(chunks)
        print(f"  {file_path.name}: {len(chunks)} chunks")

    print(f"Total chunks: {len(all_chunks)}")
    return all_chunks
