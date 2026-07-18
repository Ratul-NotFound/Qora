"""
Neo4j Graph Database Handler
Populates the citation and knowledge graph with Papers, Authors, Methods, and Datasets.
"""
from neo4j import GraphDatabase
from config import settings

class Neo4jGraphHandler:
    def __init__(self):
        self.uri = settings.neo4j_uri
        self.user = settings.neo4j_user
        self.password = settings.neo4j_password
        self._driver = None

    def _get_driver(self):
        if not self._driver:
            try:
                self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            except Exception as e:
                print(f"[Neo4j] Failed to create driver: {e}")
        return self._driver

    def save_session_graph(self, session_id: str, papers: list, intelligence_data: dict):
        driver = self._get_driver()
        if not driver:
            print("[Neo4j] No driver available. Skipping database write.")
            return

        try:
            with driver.session() as session:
                # 1. Create Paper nodes & Author relationships
                for paper in papers:
                    # Merge paper
                    session.execute_write(
                        self._create_paper_node,
                        paper.id,
                        paper.title,
                        paper.year or 0,
                        paper.citations,
                        paper.source,
                        paper.url
                    )

                    # Merge authors and link them
                    for author_name in paper.authors:
                        if author_name:
                            session.execute_write(self._create_author_link, author_name, paper.id)

                    # Merge methods and link them
                    methods = paper.methods if hasattr(paper, 'methods') else []
                    for method in methods:
                        if method:
                            session.execute_write(self._create_method_link, method, paper.id)

                    # Merge datasets and link them
                    datasets = paper.datasets if hasattr(paper, 'datasets') else []
                    for dataset in datasets:
                        if dataset:
                            session.execute_write(self._create_dataset_link, dataset, paper.id)

                # 2. Create citation relationships
                # Extract references if present (fallback search tracing)
                # In this demo model, we can link them based on common topics or keywords if explicit references aren't in the schema,
                # but if papers contain citations, we can link them.
                graph_data = intelligence_data.get("graph_data", {})
                edges = graph_data.get("edges", [])
                for edge in edges:
                    source = edge.get("source")
                    target = edge.get("target")
                    edge_type = edge.get("type", "CITES")
                    if source and target:
                        session.execute_write(self._create_citation_link, source, target, edge_type)

            print(f"[Neo4j] Successfully wrote graph for session {session_id}")
        except Exception as e:
            print(f"[Neo4j] Operational error: {e}. Please ensure Neo4j container is running.")

    @staticmethod
    def _create_paper_node(tx, paper_id, title, year, citations, source, url):
        query = (
            "MERGE (p:Paper {id: $paper_id}) "
            "SET p.title = $title, p.year = $year, p.citations = $citations, p.source = $source, p.url = $url "
            "RETURN p"
        )
        tx.run(query, paper_id=paper_id, title=title, year=year, citations=citations, source=source, url=url)

    @staticmethod
    def _create_author_link(tx, author_name, paper_id):
        query = (
            "MERGE (a:Author {name: $author_name}) "
            "MERGE (p:Paper {id: $paper_id}) "
            "MERGE (a)-[:AUTHORED]->(p)"
        )
        tx.run(query, author_name=author_name, paper_id=paper_id)

    @staticmethod
    def _create_method_link(tx, method_name, paper_id):
        query = (
            "MERGE (m:Method {name: $method_name}) "
            "MERGE (p:Paper {id: $paper_id}) "
            "MERGE (p)-[:USES]->(m)"
        )
        tx.run(query, method_name=method_name, paper_id=paper_id)

    @staticmethod
    def _create_dataset_link(tx, dataset_name, paper_id):
        query = (
            "MERGE (d:Dataset {name: $dataset_name}) "
            "MERGE (p:Paper {id: $paper_id}) "
            "MERGE (p)-[:BENCHMARKED_ON]->(d)"
        )
        tx.run(query, dataset_name=dataset_name, paper_id=paper_id)

    @staticmethod
    def _create_citation_link(tx, source_id, target_id, relation_type):
        # Dynamically inject relation type (sanitizing alphanumeric to prevent cypher injection)
        rel_type = "".join(c for c in relation_type if c.isalnum()).upper() or "CITES"
        query = (
            f"MERGE (s:Paper {{id: $source_id}}) "
            f"MERGE (t:Paper {{id: $target_id}}) "
            f"MERGE (s)-[:{rel_type}]->(t)"
        )
        tx.run(query, source_id=source_id, target_id=target_id)

    def close(self):
        if self._driver:
            self._driver.close()
