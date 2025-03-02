#backend/agents/qa_agent.py
import logging
import re
from typing import List, Dict, Any, Optional
import ollama
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAAgent:
    def __init__(self, model_name: str = "deepseek-r1:1.5b"):
        """
        Initialize the Q&A agent for answering questions about research papers.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.model_name = model_name
        logger.info(f"Q&A Agent initialized with model: {model_name}")
    
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
    
    def answer_question(self, question: str, paper_ids: List[str], topic: Optional[str] = None) -> Dict[str, Any]:
        if not paper_ids:
            return {"question": question, "answer": "No papers provided for reference."}
        try:
            prompt = f"Answer the question based on papers: {', '.join(paper_ids)}.\nQuestion: {question}"
            answer = self._ask_llm(prompt)
            return {"question": question, "answer": answer}
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {"question": question, "answer": f"Error: {str(e)}"}
    
    def _create_prompt_for_paper(self, question: str, paper: Dict[str, Any]) -> str:
        """
        Create a prompt for the LLM to answer a question about a specific paper.
        
        Args:
            question: The user's question
            paper: Paper dictionary
            
        Returns:
            Formatted prompt
        """
        max_content_length = 8000  # Limit content to avoid exceeding token limits
        
        title = paper.get("title", "Unknown Title")
        authors = ", ".join(paper.get("authors", ["Unknown"]))
        abstract = paper.get("abstract", "No abstract available")
        year = paper.get("year", "Unknown Year")
        
        content = paper.get("content", "")
        if content and len(content) > max_content_length:
            content = content[:max_content_length] + "... [content truncated]"

        
        prompt = (
            f"You are an academic research assistant. I will provide you with details from a research paper, "
            f"and you need to answer a specific question about it. Please only use information contained in this paper "
            f"to answer the question. If the answer is not found in the paper, state that clearly.\n\n"
            f"Paper Details:\n"
            f"Title: {title}\n"
            f"Authors: {authors}\n"
            f"Year: {year}\n"
            f"Abstract: {abstract}\n\n"
            f"Question: {question}\n\n"
            f"Paper Content:\n{content}\n\n"
            f"Please provide a complete and accurate answer based only on the information in this paper.\n"
        )
        return prompt
    
    def _extract_citations(self, answer: str) -> List[Dict[str, str]]:
        """
        Extract citations from the LLM's answer.
        
        Args:
            answer: The LLM's answer
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        pattern = r'\[Paper\s+(\d+)(?:\s*-\s*([^,]+))?,\s*(?:Section\s+([^\]]+))?\]'

        matches = re.finditer(pattern, answer)
        for match in matches:
            paper_num = match.group(1)
            paper_title = match.group(2) if match.group(2) else ""
            section = match.group(3) if match.group(3) else ""

            citations.append({
                "paper_num": paper_num,
                "paper_title": paper_title.strip() if paper_title else "",
                "section": section.strip() if section else "",
                "full_citation": match.group(0)
            })
        
        return citations
    
    def answer_question_single_paper(self, question: str, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Answer a question about a single paper.
        
        Args:
            question: The user's question
            paper: Paper dictionary
            
        Returns:
            Dictionary with the answer and metadata
        """
        try:
            logger.info(f"Answering question about paper: {paper.get('title', 'Unknown')}")
            
            prompt = self._create_prompt_for_paper(question, paper)
            answer = self._ask_llm(prompt)
            
            return {
                "question": question,
                "answer": answer,
                "paper": {
                    "paper_id": paper.get("paper_id", "unknown"),
                    "title": paper.get("title", "Unknown Title"),
                    "authors": paper.get("authors", ["Unknown"]),
                    "year": paper.get("year", "Unknown Year")
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error answering question about single paper: {str(e)}")
            return {
                "question": question,
                "answer": f"Error: Failed to answer the question. {str(e)}",
                "paper": {
                    "paper_id": paper.get("paper_id", "unknown"),
                    "title": paper.get("title", "Unknown Title")
                },
                "timestamp": datetime.now().isoformat()
            }
