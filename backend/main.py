#backend/main.py 
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

from backend.agents.search_agent import SearchAgent
from backend.agents.database_agent import DatabaseAgent
from backend.agents.qa_agent import QAAgent
from backend.agents.future_works_agent import FutureWorksAgent


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Academic Research Paper Assistant",
    description="An API for searching, analyzing, and querying research papers",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get database connection details from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://3d954014.databases.neo4j.io")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-r1:1.5b")

# Initialize agents
search_agent = SearchAgent()
database_agent = DatabaseAgent(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
qa_agent = QAAgent(model_name=LLM_MODEL)
future_works_agent = FutureWorksAgent(model_name=LLM_MODEL)

# API Models
class SearchRequest(BaseModel):
    topic: str
    max_results: int = Field(default=10, ge=1, le=50)
    years_back: int = Field(default=5, ge=1, le=20)
    fetch_content: bool = Field(default=True)

class QuestionRequest(BaseModel):
    question: str
    paper_ids: List[str] = Field(default=[])
    topic: Optional[str] = None
    
class GenerateRequest(BaseModel):
    topic: str
    years_back: int = Field(default=5, ge=1, le=20)

class PaperResponse(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    year: Optional[int] = None
    url: Optional[str] = None

# Root Endpoint
@app.get("/")
async def root():
    return {"message": "Academic Research Paper Assistant API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/search", response_model=Dict[str, Any])
async def search_papers(request: SearchRequest, background_tasks: BackgroundTasks):
    try:
        papers = search_agent.search_arxiv(
            topic=request.topic,
            max_results=request.max_results,
            years_back=request.years_back
        )
        if request.fetch_content and papers:
            background_tasks.add_task(
                database_agent.store_papers,
                papers=papers,
                topic=request.topic
            )
            return {"message": f"Processing {len(papers)} papers in background.", "papers": papers}
        else:
            database_agent.store_papers(papers, request.topic)
            return {"message": f"Stored {len(papers)} papers.", "papers": papers}
    except Exception as e:
        logger.error(f"Error in search_papers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching papers: {str(e)}")

@app.get("/papers/{topic}", response_model=Dict[str, Any])
async def get_papers_by_topic(
    topic: str,
    year_from: Optional[int] = Query(None, ge=1900, le=2100),
    year_to: Optional[int] = Query(None, ge=1900, le=2100)
):
    try:
        papers = database_agent.get_papers_by_topic(topic, year_from, year_to)
        return {"topic": topic, "paper_count": len(papers), "papers": papers}
    except Exception as e:
        logger.error(f"Error fetching papers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching papers: {str(e)}")

@app.post("/qa", response_model=Dict[str, Any])
async def answer_question(request: QuestionRequest):
    try:
        answer = qa_agent.answer_question(
            question=request.question,
            paper_ids=request.paper_ids,
            topic=request.topic
        )
        return {"question": request.question, "answer": answer}
    except Exception as e:
        logger.error(f"Error in Q&A: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in Q&A: {str(e)}")

@app.post("/generate-future-works", response_model=Dict[str, Any])
async def generate_future_works(request: GenerateRequest):
    try:
        future_work = future_works_agent.generate_future_work(request.topic, request.years_back)
        return {"topic": request.topic, "future_work": future_work}
    except Exception as e:
        logger.error(f"Error generating future works: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating future works: {str(e)}")

# Run FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
