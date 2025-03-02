#backend\agents\database_agent.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

from backend.database.neo4j_client import Neo4jClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseAgent:
    def __init__(self, neo4j_uri: str, neo4j_username: str, neo4j_password: str):
        """
        Initialize the database agent for storing and retrieving research papers.
        
        Args:
            neo4j_uri: URI for the Neo4j database
            neo4j_username: Username for the Neo4j database
            neo4j_password: Password for the Neo4j database
        """
        self.neo4j_client = Neo4jClient(neo4j_uri, neo4j_username, neo4j_password)
        logger.info("Database Agent initialized")
    
    def store_papers(self, papers: List[Dict[str, Any]], topic: str) -> int:
        """
        Store multiple papers in the database.
        
        Args:
            papers: List of paper dictionaries
            topic: Research topic
            
        Returns:
            Number of papers successfully stored
        """
        count = 0
        
        for paper in papers:
            success = self.neo4j_client.store_paper(paper, topic)
            if success:
                count += 1
                
        logger.info(f"Stored {count} papers for topic: {topic}")
        return count
    
    def get_papers_by_topic(self, topic: str, year_from: Optional[int] = None, year_to: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve papers for a specific topic with optional time filtering.
        
        Args:
            topic: Research topic
            year_from: Start year (inclusive)
            year_to: End year (inclusive)
            
        Returns:
            List of paper dictionaries
        """
        papers = self.neo4j_client.get_papers_by_topic(topic, year_from, year_to)
        
        # Sort papers by year, most recent first
        papers.sort(key=lambda p: p.get('year', 0) or 0, reverse=True)
        
        logger.info(f"Retrieved {len(papers)} papers for topic: {topic}")
        return papers
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific paper by ID.
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            Paper dictionary or None if not found
        """
        paper = self.neo4j_client.get_paper_by_id(paper_id)
        
        if paper:
            logger.info(f"Retrieved paper: {paper.get('title', 'Unknown')}")
        else:
            logger.warning(f"Paper not found with ID: {paper_id}")
            
        return paper
    
    def get_papers_last_n_years(self, topic: str, years: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve papers for a specific topic from the last N years.
        
        Args:
            topic: Research topic
            years: Number of years to look back
            
        Returns:
            List of paper dictionaries
        """
        current_year = datetime.now().year
        year_from = current_year - years
        
        return self.get_papers_by_topic(topic, year_from, current_year)
    
    def get_all_topics(self) -> List[str]:
        """
        Get all research topics in the database.
        
        Returns:
            List of topic names
        """
        topics = self.neo4j_client.get_topics()
        logger.info(f"Retrieved {len(topics)} research topics")
        return topics
    
    def clear_topic_data(self, topic: str) -> bool:
        """
        Remove all papers for a specific topic.
        
        Args:
            topic: Research topic to clear
            
        Returns:
            Success status
        """
        success = self.neo4j_client.clear_topic_data(topic)
        
        if success:
            logger.info(f"Cleared all papers for topic: {topic}")
        else:
            logger.error(f"Failed to clear papers for topic: {topic}")
            
        return success
    
    def close(self):
        """Close the database connection."""
        self.neo4j_client.close()
        logger.info("Database connection closed")