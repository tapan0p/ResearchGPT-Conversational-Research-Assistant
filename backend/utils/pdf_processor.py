import os
import logging
import PyPDF2
import re
from typing import Dict, Any, Optional, List, Tuple
import tempfile
import requests
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        """Initialize the PDF processor."""
        logger.info("PDF Processor initialized")
    
    def download_pdf(self, url: str) -> Optional[BytesIO]:
        """
        Download a PDF file from a URL.
        
        Args:
            url: URL of the PDF file
            
        Returns:
            BytesIO: PDF file content as a BytesIO object or None if download fails
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if the response is a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'application/pdf' not in content_type and not url.lower().endswith('.pdf'):
                logger.warning(f"URL does not point to a PDF: {url} (Content-Type: {content_type})")
                return None
                
            pdf_content = BytesIO(response.content)
            return pdf_content
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, pdf_content: BytesIO) -> Optional[str]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_content: PDF file content as a BytesIO object
            
        Returns:
            str: Extracted text or None if extraction fails
        """
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_content)
            text = ""
            
            # Extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
                
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract sections from the text of a research paper.
        
        Args:
            text: Full text of the research paper
            
        Returns:
            Dict mapping section names to their content
        """
        # Common section headers in research papers
        section_patterns = [
            r'Abstract',
            r'Introduction',
            r'Related Work',
            r'Background',
            r'Methodology',
            r'Method',
            r'Approach',
            r'Experiment[s]?',
            r'Evaluation',
            r'Results? (?:and|&) Discussion',
            r'Results?',
            r'Discussion',
            r'Conclusion[s]?',
            r'Future Work',
            r'References',
            r'Appendix',
        ]
        
        # Create a regex pattern to match section headers
        section_pattern = r'(?:^|\n)(' + '|'.join(section_patterns) + r')(?:\s|\n|:)'
        
        # Find all section headers
        matches = list(re.finditer(section_pattern, text, re.IGNORECASE))
        
        sections = {}
        
        # Extract sections
        for i, match in enumerate(matches):
            section_name = match.group(1)
            start_pos = match.start()
            
            # Determine end position (start of next section or end of text)
            if i < len(matches) - 1:
                end_pos = matches[i+1].start()
            else:
                end_pos = len(text)
                
            # Extract section content
            section_content = text[start_pos:end_pos].strip()
            sections[section_name] = section_content
            
        # If no sections were found, treat the entire text as one section
        if not sections:
            sections['Full Text'] = text
            
        return sections
    
    def process_pdf(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Process a PDF file from a URL, extracting text and sections.
        
        Args:
            url: URL of the PDF file
            
        Returns:
            Dict with extracted text and sections, or None if processing fails
        """
        try:
            pdf_content = self.download_pdf(url)
            if not pdf_content:
                return None
                
            text = self.extract_text_from_pdf(pdf_content)
            if not text:
                return None
                
            sections = self.extract_sections(text)
            
            result = {
                'full_text': text,
                'sections': sections
            }
            
            return result
        except Exception as e:
            logger.error(f"Error processing PDF from {url}: {str(e)}")
            return None
    
    def extract_figures_and_tables(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract references to figures and tables from the text.
        
        Args:
            text: Full text of the research paper
            
        Returns:
            List of dictionaries containing figure/table references and their captions
        """
        figures_tables = []
        
        # Pattern for figures
        figure_pattern = r'(?:Figure|Fig\.?)\s+(\d+)[:\.]?\s*([^\.]+)'
        figure_matches = re.finditer(figure_pattern, text, re.IGNORECASE)
        
        for match in figure_matches:
            figures_tables.append({
                'type': 'figure',
                'number': match.group(1),
                'caption': match.group(2).strip(),
                'text': match.group(0)
            })
            
        # Pattern for tables
        table_pattern = r'Table\s+(\d+)[:\.]?\s*([^\.]+)'
        table_matches = re.finditer(table_pattern, text, re.IGNORECASE)
        
        for match in table_matches:
            figures_tables.append({
                'type': 'table',
                'number': match.group(1),
                'caption': match.group(2).strip(),
                'text': match.group(0)
            })
            
        return figures_tables