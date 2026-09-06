"""
Legal document chunk data structures and schemas.
Conforms to MVP_BUILD_SPEC.md and MASTER_BUILD_SPEC.md.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any


@dataclass
class ChunkMetadata:
    """Metadata schema for a legal knowledge chunk."""
    document: str                    # e.g. 'rules2011.pdf' or 'rules2009.pdf'
    document_name: str               # Alias for document
    document_title: str              # Full title of the act/rules
    rule: Optional[str] = None       # Rule or Section number (e.g. '6', '18')
    rule_number: Optional[str] = None # Alias for rule
    sub_rule: Optional[str] = None   # Sub-rule number (e.g. '1', '2')
    clause: Optional[str] = None     # Clause letter (e.g. 'a', 'b', 'e')
    chapter: Optional[str] = None    # Chapter (e.g. 'I', 'II', 'V')
    page: int = 1                    # 1-indexed PDF page number
    page_number: int = 1             # Alias for page
    chunk_type: str = "rule"         # 'rule', 'definition', 'schedule', 'section', 'penalty'
    title: str = ""                  # Section / Rule title
    section_title: str = ""          # Alias for title
    citation: str = ""               # Formatted legal citation string

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """Convert metadata to ChromaDB-safe types (str, int, float, bool - no None)."""
        clean = {}
        for k, v in asdict(self).items():
            if v is None:
                clean[k] = ""
            else:
                clean[k] = v
        return clean


@dataclass
class LegalChunk:
    """Represents a rule-aware chunk extracted from legal documents."""
    chunk_id: str                    # Unique identifier (e.g. 'rules2011_rule6_1_e')
    text: str                        # Chunk text with parent context header
    metadata: ChunkMetadata          # Detailed metadata for citation and filtering

    @property
    def id(self) -> str:
        return self.chunk_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata.to_dict()
        }

    def to_chroma_format(self) -> Dict[str, Any]:
        """Format suitable for ChromaDB add() call."""
        return {
            "id": self.chunk_id,
            "document": self.text,
            "metadata": self.metadata.to_chroma_metadata()
        }
