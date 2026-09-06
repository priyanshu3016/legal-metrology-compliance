"""
RAG Legal Retriever for Legal Metrology (Packaged Commodities) Compliance.

Indexes the 141 rule-aware legal chunks into ChromaDB and provides top-k
context retrieval for compliance check citations.
"""

import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import chromadb
from chromadb.utils import embedding_functions

from backend.rag.ingest import ingest_documents, prepare_chroma_batches


@dataclass
class RetrievedContext:
    """Single retrieved legal chunk for citation attachment."""
    text: str
    citation: str
    page: int
    document: str
    rule: Optional[str] = None
    sub_rule: Optional[str] = None
    clause: Optional[str] = None
    distance: float = 0.0


CHECK_QUERIES = {
    "CHK-01": "common or generic name of commodity declaration package",
    "CHK-02": "packages intended for retail sale net quantity of the commodity contained in the package standard units",
    "CHK-03": "maximum retail price MRP inclusive of all taxes retail sale price",
    "CHK-04": "name and complete address of manufacturer packer importer",
    "CHK-05": "month and year of manufacture pre-packing import date",
    "CHK-06": "consumer care details name address telephone email complaints",
    "CHK-07": "quantity declaration misleading words minimum approximate average",
    "CHK-09": "imported package country of origin name address importer",
}


class LegalRetriever:
    """Retriever for legal chunks stored in ChromaDB."""

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: str = "legal_chunks",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        if persist_dir is None:
            # Default to backend/data/chroma_db relative to project root
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db"))
            persist_dir = base_dir
        elif not os.path.isabs(persist_dir):
            persist_dir = os.path.abspath(persist_dir)

        os.makedirs(persist_dir, exist_ok=True)
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn
        )

        # Populate collection if empty
        if self.collection.count() == 0:
            chunks = ingest_documents()
            batch = prepare_chroma_batches(chunks)
            self.collection.add(
                ids=batch["ids"],
                documents=batch["documents"],
                metadatas=batch["metadatas"]
            )

    def retrieve_raw(self, query: str, k: int = 3) -> List[RetrievedContext]:
        """Direct semantic query for top-k legal chunks."""
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )

        contexts: List[RetrievedContext] = []
        if not results or not results.get("documents") or not results["documents"][0]:
            return contexts

        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

        for doc_text, meta, dist in zip(docs, metas, distances):
            rule_val = meta.get("rule") or None
            sub_rule_val = meta.get("sub_rule") or None
            clause_val = meta.get("clause") or None
            page_val = int(meta.get("page", 1)) if meta.get("page") else 1
            citation_val = meta.get("citation", "")
            document_val = meta.get("document", "")

            contexts.append(
                RetrievedContext(
                    text=doc_text,
                    citation=citation_val,
                    page=page_val,
                    document=document_val,
                    rule=rule_val,
                    sub_rule=sub_rule_val,
                    clause=clause_val,
                    distance=float(dist)
                )
            )

        return contexts

    def retrieve_for_check(self, check_id: str, k: int = 3) -> List[RetrievedContext]:
        """Query top-k context using canonical query for the given check ID."""
        if check_id not in CHECK_QUERIES:
            raise ValueError(f"Unknown check_id: {check_id}. Must be one of {list(CHECK_QUERIES.keys())}")
        query = CHECK_QUERIES[check_id]
        return self.retrieve_raw(query, k=k)
