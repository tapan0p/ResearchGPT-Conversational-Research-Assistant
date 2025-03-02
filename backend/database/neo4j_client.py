from neo4j import GraphDatabase
import os
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self, uri: str, username: str, password: str):
        """Initialize Neo4j database connection."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self._create_constraints()
        logger.info("Neo4j client initialized")
        
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()
        
    def _create_constraints(self):
        """Create necessary constraints in Neo4j."""
        with self.driver.session() as session:
            # Check if constraints exist before creating them
            constraints = session.run("SHOW CONSTRAINTS").data()
            constraint_names = [c.get('name') for c in constraints]
            
            # Create constraints if they don't exist
            if 'unique_paper_id' not in constraint_names:
                session.run("CREATE CONSTRAINT unique_paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE")
            
            if 'unique_topic_name' not in constraint_names:
                session.run("CREATE CONSTRAINT unique_topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE")
                
            logger.info("Neo4j constraints created or verified")
    
    def store_paper(self, paper_data: Dict[str, Any], topic_name: str) -> bool:
        """
        Store a research paper and its relationship to a topic in the database.
        
        Args:
            paper_data: Dictionary containing paper details
            topic_name: Name of the research topic
            
        Returns:
            bool: Success status
        """
        try:
            with self.driver.session() as session:
                # Convert date string to Neo4j date if available
                if 'published_date' in paper_data and paper_data['published_date']:
                    if isinstance(paper_data['published_date'], str):
                        try:
                            date_obj = datetime.strptime(paper_data['published_date'], '%Y-%m-%d')
                            paper_data['year'] = date_obj.year
                        except ValueError:
                            # If date parsing fails, try to extract year
                            try:
                                paper_data['year'] = int(paper_data['published_date'][:4])
                            except (ValueError, TypeError):
                                paper_data['year'] = None
                
                # Create or update the paper node
                result = session.run("""
                    MERGE (p:Paper {paper_id: $paper_id})
                    ON CREATE SET 
                        p.title = $title,
                        p.authors = $authors,
                        p.abstract = $abstract,
                        p.published_date = $published_date,
                        p.year = $year,
                        p.url = $url,
                        p.content = $content,
                        p.created_at = datetime()
                    ON MATCH SET 
                        p.title = $title,
                        p.authors = $authors,
                        p.abstract = $abstract,
                        p.published_date = $published_date,
                        p.year = $year,
                        p.url = $url,
                        p.updated_at = datetime()
                    
                    WITH p
                    
                    MERGE (t:Topic {name: $topic_name})
                    MERGE (p)-[r:BELONGS_TO]->(t)
                    RETURN p.paper_id
                """, {**paper_data, "topic_name": topic_name})
                
                record = result.single()
                return record is not None
                
        except Exception as e:
            logger.error(f"Error storing paper: {str(e)}")
            return False
    
    def get_papers_by_topic(self, topic_name: str, year_from: Optional[int] = None, year_to: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve papers related to a specific topic with optional time filtering.
        
        Args:
            topic_name: Name of the research topic
            year_from: Start year for filtering (inclusive)
            year_to: End year for filtering (inclusive)
            
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        with self.driver.session() as session:
            query = """
                MATCH (p:Paper)-[:BELONGS_TO]->(t:Topic {name: $topic_name})
                WHERE 1=1
            """
            
            params = {"topic_name": topic_name}
            
            if year_from is not None:
                query += " AND p.year >= $year_from"
                params["year_from"] = year_from
                
            if year_to is not None:
                query += " AND p.year <= $year_to"
                params["year_to"] = year_to
                
            query += " RETURN p ORDER BY p.year DESC, p.title"
            
            result = session.run(query, params)
            
            for record in result:
                paper_node = record["p"]
                paper = dict(paper_node.items())
                papers.append(paper)
                
        return papers
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a paper by its ID."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                RETURN p
            """, {"paper_id": paper_id})
            
            record = result.single()
            if record:
                paper_node = record["p"]
                return dict(paper_node.items())
            return None
    
    def get_topics(self) -> List[str]:
        """Get all available research topics."""
        topics = []
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Topic)
                RETURN t.name AS topic
                ORDER BY t.name
            """)
            
            for record in result:
                topics.append(record["topic"])
                
        return topics
    
    def clear_topic_data(self, topic_name: str) -> bool:
        """Remove all papers associated with a topic."""
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (p:Paper)-[r:BELONGS_TO]->(t:Topic {name: $topic_name})
                    DETACH DELETE p
                """, {"topic_name": topic_name})
                return True
        except Exception as e:
            logger.error(f"Error clearing topic data: {str(e)}")
            return False