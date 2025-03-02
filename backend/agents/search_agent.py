import arxiv
import logging
import re
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import random

from backend.utils.pdf_processor import PDFProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchAgent:
    def __init__(self):
        """Initialize the search agent for finding research papers."""
        self.pdf_processor = PDFProcessor()
        logger.info("Search Agent initialized")
    
    def search_arxiv(self, topic: str, max_results: int = 10, years_back: int = 5) -> List[Dict[str, Any]]:
        """
        Search for papers on ArXiv related to a given topic.
        
        Args:
            topic: Research topic to search for
            max_results: Maximum number of results to return
            years_back: How many years back to search
            
        Returns:
            List of paper dictionaries
        """
        try:
            # Determine the date range
            current_year = datetime.now().year
            year_lower_bound = current_year - years_back
            
            # Format the search query
            query = f"ti:{topic} OR abs:{topic}"
            
            logger.info(f"Searching ArXiv for: {query}")
            
            # Search ArXiv
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            
            for result in search.results():
                # Extract authors as a list of names
                authors = [author.name for author in result.authors]
                
                # Ensure the paper is within the desired date range
                paper_year = result.published.year if result.published else None
                if paper_year and paper_year >= year_lower_bound:
                    paper_data = {
                        "paper_id": result.entry_id.split('/')[-1],
                        "title": result.title,
                        "authors": authors,
                        "abstract": result.summary,
                        "published_date": result.published.strftime("%Y-%m-%d") if result.published else None,
                        "year": paper_year,
                        "url": result.pdf_url,
                        "content": None  
                    }
                    papers.append(paper_data)
                
            logger.info(f"Found {len(papers)} relevant papers on ArXiv for topic: {topic}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching ArXiv: {str(e)}")
            return []
    
    def process_papers(self, papers: List[Dict[str, Any]], fetch_content: bool = True) -> List[Dict[str, Any]]:
        """
        Process papers by downloading and extracting content if requested.
        
        Args:
            papers: List of paper dictionaries
            fetch_content: Whether to fetch and process the full content
            
        Returns:
            List of processed paper dictionaries
        """
        processed_papers = []
        
        for paper in papers:
            try:
                if fetch_content and paper.get("url"):
                    logger.info(f"Processing paper: {paper['title']}")
                    
                    # Process the PDF
                    pdf_data = self.pdf_processor.process_pdf(paper["url"])
                    
                    if pdf_data:
                        paper["content"] = pdf_data["full_text"]
                        paper["sections"] = pdf_data["sections"]
                        
                        # Extract figures and tables
                        paper["figures_tables"] = self.pdf_processor.extract_figures_and_tables(pdf_data["full_text"])
                    else:
                        logger.warning(f"Failed to process PDF for paper: {paper['title']}")
                
                processed_papers.append(paper)
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.error(f"Error processing paper {paper.get('title', 'Unknown')}: {str(e)}")
        
        return processed_papers
    
    def search_and_process(self, topic: str, max_results: int = 10, years_back: int = 5, fetch_content: bool = True) -> List[Dict[str, Any]]:
        """
        Search for papers and process them.
        
        Args:
            topic: Research topic to search for
            max_results: Maximum number of results to return
            years_back: How many years back to search
            fetch_content: Whether to fetch and process the full content
            
        Returns:
            List of processed paper dictionaries
        """
        # Search for papers
        papers = self.search_arxiv(topic, max_results, years_back)
        
        # Process the papers
        if fetch_content:
            papers = self.process_papers(papers, fetch_content)
        
        return papers