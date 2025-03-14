"""
Developer Agent implementation that interfaces with LLM services and databases.
"""
from typing import Dict, List, Any, Optional
import logging

from langchain.llms.base import BaseLLM

from ..db.vector import VectorDBClient
from ..db.graph import GraphDBClient

logger = logging.getLogger(__name__)

class DeveloperAgent:
    """
    Developer Agent that interfaces with LLM services and databases to perform
    development tasks based on code repositories and requirements.
    """
    
    def __init__(
        self,
        llm_service: BaseLLM,
        vector_db: VectorDBClient,
        graph_db: GraphDBClient,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Developer Agent.
        
        Args:
            llm_service: LLM service for generating responses
            vector_db: Vector database client for semantic search
            graph_db: Graph database client for relationship queries
            config: Optional configuration parameters
        """
        self.llm = llm_service
        self.vector_db = vector_db
        self.graph_db = graph_db
        self.config = config or {}
        
        logger.info("Developer Agent initialized")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query about the codebase or requirements.
        
        Args:
            query: Natural language query
            
        Returns:
            Response with relevant information
        """
        # Search vector database for relevant code chunks
        vector_results = await self.vector_db.search(query)
        
        # Query graph database for relationships
        graph_results = await self.graph_db.query_relationships(query, vector_results)
        
        # Generate response using LLM
        response = await self.generate_response(query, vector_results, graph_results)
        
        return response
    
    async def generate_response(
        self, 
        query: str, 
        vector_results: List[Dict[str, Any]], 
        graph_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a response using the LLM service.
        
        Args:
            query: Original query
            vector_results: Results from vector database
            graph_results: Results from graph database
            
        Returns:
            Generated response
        """
        # Construct prompt with context from vector and graph results
        prompt = self._construct_prompt(query, vector_results, graph_results)
        
        # Generate response from LLM
        llm_response = await self.llm.agenerate([prompt])
        
        return {
            "query": query,
            "response": llm_response.generations[0][0].text,
            "sources": self._extract_sources(vector_results, graph_results)
        }
    
    def _construct_prompt(
        self, 
        query: str, 
        vector_results: List[Dict[str, Any]], 
        graph_results: List[Dict[str, Any]]
    ) -> str:
        """
        Construct a prompt for the LLM with context from search results.
        
        Args:
            query: Original query
            vector_results: Results from vector database
            graph_results: Results from graph database
            
        Returns:
            Constructed prompt
        """
        # TODO: Implement prompt construction with proper context
        prompt = f"Query: {query}\n\nContext:\n"
        
        # Add vector results
        prompt += "\nCode Context:\n"
        for i, result in enumerate(vector_results[:5]):  # Limit to top 5 results
            prompt += f"{i+1}. {result.get('content', '')}\n"
            prompt += f"   Source: {result.get('source', '')}\n\n"
        
        # Add graph results
        prompt += "\nRelationships:\n"
        for i, result in enumerate(graph_results[:5]):  # Limit to top 5 results
            prompt += f"{i+1}. {result.get('relationship', '')}\n"
            
        prompt += "\nBased on the above context, please respond to the query."
        
        return prompt
    
    def _extract_sources(
        self, 
        vector_results: List[Dict[str, Any]], 
        graph_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract source information from search results.
        
        Args:
            vector_results: Results from vector database
            graph_results: Results from graph database
            
        Returns:
            List of source information
        """
        sources = []
        
        # Extract sources from vector results
        for result in vector_results:
            if "source" in result and result["source"] not in [s.get("source") for s in sources]:
                sources.append({
                    "type": "code",
                    "source": result["source"],
                    "relevance": result.get("score", 0)
                })
        
        # Extract sources from graph results
        for result in graph_results:
            if "source" in result and result["source"] not in [s.get("source") for s in sources]:
                sources.append({
                    "type": "relationship",
                    "source": result["source"],
                    "relevance": result.get("score", 0)
                })
        
        return sources