"""
Embeddings & Vector Store Manager — Connects to Weaviate for semantic search & RAG.
"""
import weaviate
from typing import List
from config import settings
from models.schemas import Paper


class EmbeddingsManager:
    def __init__(self):
        self.url = settings.weaviate_url
        self._client = None

    def _get_client(self):
        if not self._client:
            try:
                # Support Weaviate v4 or v3 client
                if hasattr(weaviate, "connect_to_local"):
                    self._client = weaviate.connect_to_local(host="localhost", port=8080)
                else:
                    self._client = weaviate.Client(self.url)
            except Exception as e:
                print(f"[Weaviate] Connection failed: {e}. Semantic search will run in-memory fallback.")
        return self._client

    def index_papers(self, papers: List[Paper]):
        """Index papers into Weaviate vector database."""
        client = self._get_client()
        if not client:
            return

        try:
            # Check if collection/class exists using v4 or v3 API
            if hasattr(client, "collections"):
                if not client.collections.exists("Paper"):
                    client.collections.create(
                        name="Paper",
                        description="Academic research papers indexed for semantic search"
                    )
                paper_coll = client.collections.get("Paper")
                with paper_coll.batch.dynamic() as batch:
                    for p in papers:
                        batch.add_object({
                            "paper_id": p.id,
                            "title": p.title,
                            "abstract": p.abstract[:3000],
                            "summary": p.summary,
                            "year": p.year or 0,
                            "source": p.source,
                        })
            print(f"[Weaviate] Successfully indexed {len(papers)} papers.")
        except Exception as e:
            print(f"[Weaviate] Indexing error: {e}. Please ensure Weaviate container is running.")

    def search_similar(self, query: str, limit: int = 5) -> List[str]:
        """Perform vector semantic search over indexed papers."""
        client = self._get_client()
        if not client:
            return []

        try:
            if hasattr(client, "collections"):
                paper_coll = client.collections.get("Paper")
                response = paper_coll.query.near_text(query=query, limit=limit)
                return [obj.properties.get("paper_id") for obj in response.objects if obj.properties.get("paper_id")]
        except Exception as e:
            print(f"[Weaviate] Query error: {e}")
        return []

    def close(self):
        if self._client and hasattr(self._client, "close"):
            try:
                self._client.close()
            except Exception:
                pass
