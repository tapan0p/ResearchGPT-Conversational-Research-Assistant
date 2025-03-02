#backend/agents/future_works_agent.py
import logging
from typing import List, Dict, Any, Optional
import ollama
from datetime import datetime
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FutureWorksAgent:
    def __init__(self, model_name: str = "deepseek-r1:1.5b"):
        """
        Initialize the Future Works agent for generating research ideas and review papers.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.model_name = model_name
        logger.info(f"Future Works Agent initialized with model: {model_name}")
    
    def _ask_llm(self, prompt: str) -> str:
        """
        Send a prompt to the LLM and get a response.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM's response
        """
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Error asking LLM: {str(e)}")
            return f"Error: Failed to get a response from the model. {str(e)}"
        
    def generate_future_work(self, topic: str, years_back: int) -> Dict[str, Any]:
        try:
            prompt = f"Generate future research ideas for the topic: {topic} based on research from the past {years_back} years."
            response = ollama.chat(model=self.model_name, messages=[{"role": "user", "content": prompt}])
            return {"topic": topic, "future_work": response["message"]["content"]}
        except Exception as e:
            logger.error(f"Error generating future works: {str(e)}")
            return {"topic": topic, "future_work": f"Error: {str(e)}"}
        
    def generate_future_research_ideas(self, papers: List[Dict[str, Any]], topic: str) -> Dict[str, Any]:
        """
        Generate ideas for future research based on a set of papers.
        
        Args:
            papers: List of paper dictionaries
            topic: The research topic
            
        Returns:
            Dictionary with generated ideas and metadata
        """
        try:
            logger.info(f"Generating future research ideas for topic: {topic}")
            
            # Sort papers by year (most recent first)
            sorted_papers = sorted(papers, key=lambda p: p.get("year", 0) or 0, reverse=True)
            
            # Create a summary of each paper
            paper_summaries = []
            
            for i, paper in enumerate(sorted_papers[:10]):  # Limit to 10 most recent papers
                title = paper.get("title", "Unknown Title")
                authors = ", ".join(paper.get("authors", ["Unknown"]))
                year = paper.get("year", "Unknown Year")
                abstract = paper.get("abstract", "No abstract available")
                
                summary = f"""
Paper {i+1}:
Title: {title}
Authors: {authors}
Year: {year}
Abstract: {abstract}
"""
                paper_summaries.append(summary)
            
            # Create the prompt
            prompt = f"""
You are an expert academic researcher in the field of {topic}. Based on the recent papers I'll provide, 
generate 5-7 promising ideas for future research directions. These ideas should build upon the current 
state of the art and address gaps or open challenges in the field.

Recent papers in {topic}:
{"".join(paper_summaries)}

For each research idea:
1. Provide a clear title for the potential research
2. Explain the key concept and approach
3. Describe why this direction is promising and how it addresses limitations in current research
4. Suggest potential methods or techniques that could be used
5. Note potential challenges or obstacles to overcome

Focus on novel, impactful ideas that could lead to significant advancements. Be specific rather than general.
"""
            
            # Get ideas from the LLM
            ideas_text = self._ask_llm(prompt)
            
            # Format the response
            result = {
                "topic": topic,
                "ideas_text": ideas_text,
                "based_on_papers": [
                    {
                        "paper_id": p.get("paper_id", "unknown"),
                        "title": p.get("title", "Unknown Title"),
                        "year": p.get("year", "Unknown Year")
                    } 
                    for p in sorted_papers[:10]
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating future research ideas: {str(e)}")
            return {
                "topic": topic,
                "ideas_text": f"Error: Failed to generate research ideas. {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_review_paper(self, papers: List[Dict[str, Any]], topic: str) -> Dict[str, Any]:
        """
        Generate a review paper summarizing the state of research and future directions.
        
        Args:
            papers: List of paper dictionaries
            topic: The research topic
            
        Returns:
            Dictionary with the review paper and metadata
        """
        try:
            logger.info(f"Generating review paper for topic: {topic}")
            
            # Sort papers by year
            sorted_papers = sorted(papers, key=lambda p: p.get("year", 0) or 0)
            
            # Create a summary of each paper
            paper_summaries = []
            
            for i, paper in enumerate(sorted_papers):
                title = paper.get("title", "Unknown Title")
                authors = ", ".join(paper.get("authors", ["Unknown"]))
                year = paper.get("year", "Unknown Year")
                abstract = paper.get("abstract", "No abstract available")
                
                # Include key sections if available
                key_sections = ""
                sections = paper.get("sections", {})
                for section_name in ["Introduction", "Method", "Methodology", "Results", "Conclusion"]:
                    if section_name in sections:
                        section_text = sections[section_name]
                        # Truncate long sections
                        if len(section_text) > 1000:
                            section_text = section_text[:1000] + "... [truncated]"
                        key_sections += f"\n{section_name}: {section_text}"
                
                summary = f"""
Paper {i+1}:
Title: {title}
Authors: {authors}
Year: {year}
Abstract: {abstract}
{key_sections}
"""
                paper_summaries.append(summary)
            
            # Create the prompt
            prompt = f"""
You are an expert academic researcher tasked with writing a comprehensive review paper on {topic}. 
Based on the papers I'll provide, create a well-structured review paper that summarizes the current state 
of research and suggests future directions.

The review paper should have the following sections:
1. Title: An appropriate title for a review paper on {topic}
2. Abstract: A concise summary of the review paper
3. Introduction: Overview of the field and importance of the topic
4. Background: Key concepts and foundational knowledge
5. Current Approaches: Analysis of the main approaches and methods in the field
6. Comparative Analysis: Comparison of different methods and their strengths/weaknesses
7. Open Challenges: Discussion of unsolved problems and limitations
8. Future Directions: Promising research directions and opportunities
9. Conclusion: Summary of the state of the field and outlook

Papers to review:
{"".join(paper_summaries[:15])}  # Limit to 15 papers to avoid exceeding context limits

Write a scholarly review paper based on these papers. Use academic language and be specific about methods, 
findings, and gaps in the research. When referencing specific papers, cite them by their number (e.g., [1]).
"""
            
            # Get the review paper from the LLM
            review_paper = self._ask_llm(prompt)
            
            # Format the response
            result = {
                "topic": topic,
                "review_paper": review_paper,
                "based_on_papers": [
                    {
                        "paper_id": p.get("paper_id", "unknown"),
                        "title": p.get("title", "Unknown Title"),
                        "year": p.get("year", "Unknown Year")
                    } 
                    for p in sorted_papers[:15]
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating review paper: {str(e)}")
            return {
                "topic": topic,
                "review_paper": f"Error: Failed to generate the review paper. {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_improvement_plan(self, papers: List[Dict[str, Any]], topic: str) -> Dict[str, Any]:
        """
        Generate an improvement plan based on existing research.
        
        Args:
            papers: List of paper dictionaries
            topic: The research topic
            
        Returns:
            Dictionary with the improvement plan and metadata
        """
        try:
            logger.info(f"Generating improvement plan for topic: {topic}")
            
            # Sort papers by year (most recent first)
            sorted_papers = sorted(papers, key=lambda p: p.get("year", 0) or 0, reverse=True)
            
            # Create a summary of the most recent papers
            paper_summaries = []
            
            for i, paper in enumerate(sorted_papers[:8]):  # Focus on most recent papers
                title = paper.get("title", "Unknown Title")
                authors = ", ".join(paper.get("authors", ["Unknown"]))
                year = paper.get("year", "Unknown Year")
                abstract = paper.get("abstract", "No abstract available")
                
                # Include key findings if available
                findings = ""
                for section_name in ["Results", "Conclusion", "Discussion"]:
                    if section_name in paper.get("sections", {}):
                        section_text = paper.get("sections", {})[section_name]
                        # Truncate long sections
                        if len(section_text) > 800:
                            section_text = section_text[:800] + "... [truncated]"
                        findings += f"\n{section_name}: {section_text}"
                
                summary = f"""
Paper {i+1}:
Title: {title}
Authors: {authors}
Year: {year}
Abstract: {abstract}
Key Findings: {findings}
"""
                paper_summaries.append(summary)
            
            # Create the prompt
            prompt = f"""
You are a research director at a top institution, specializing in {topic}. Your task is to develop a 
comprehensive improvement plan that builds upon existing research to make significant advances in the field.

Based on the recent papers I'll provide, create a strategic research and development plan that:
1. Identifies key limitations and gaps in current approaches
2. Proposes novel solutions and methodologies to address these limitations
3. Outlines concrete steps for implementing these improvements
4. Describes expected outcomes and potential impact

Recent papers in {topic}:
{"".join(paper_summaries)}

Your improvement plan should be innovative yet practical, with specific technical details rather than 
general suggestions. The plan should be well-structured with clear sections and actionable items. 
When referencing specific papers, cite them by their number (e.g., [1]).
"""
            
            # Get the improvement plan from the LLM
            improvement_plan = self._ask_llm(prompt)
            
            # Format the response
            result = {
                "topic": topic,
                "improvement_plan": improvement_plan,
                "based_on_papers": [
                    {
                        "paper_id": p.get("paper_id", "unknown"),
                        "title": p.get("title", "Unknown Title"),
                        "year": p.get("year", "Unknown Year")
                    } 
                    for p in sorted_papers[:8]
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating improvement plan: {str(e)}")
            return {
                "topic": topic,
                "improvement_plan": f"Error: Failed to generate the improvement plan. {str(e)}",
                "timestamp": datetime.now().isoformat()
            }