from fastapi import Depends
from typing import Callable, Dict, Any

from app.services.curiosity_service import CuriosityService
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.services.explanation_service import ExplanationService
from app.services.related_topics_service import RelatedTopicsService

# Create singleton instances
_curiosity_service = None
_llm_service = None
_search_service = None
_explanation_service = None
_related_topics_service = None

def get_llm_service() -> LLMService:
    """
    Get or create a singleton instance of the LLM service.
    
    Returns:
        LLMService instance
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

def get_search_service() -> SearchService:
    """
    Get or create a singleton instance of the search service.
    
    Returns:
        SearchService instance
    """
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service

def get_curiosity_service() -> CuriosityService:
    """
    Get or create a singleton instance of the curiosity service.
    
    Returns:
        CuriosityService instance
    """
    global _curiosity_service
    if _curiosity_service is None:
        _curiosity_service = CuriosityService()
    return _curiosity_service

def get_explanation_service(
    llm_service: LLMService = Depends(get_llm_service),
    search_service: SearchService = Depends(get_search_service)
) -> ExplanationService:
    """
    Get or create a singleton instance of the explanation service.
    
    Args:
        llm_service: LLM service instance
        search_service: Search service instance
        
    Returns:
        ExplanationService instance
    """
    global _explanation_service
    if _explanation_service is None:
        _explanation_service = ExplanationService(llm_service, search_service)
    return _explanation_service

def get_related_topics_service(
    llm_service: LLMService = Depends(get_llm_service)
) -> RelatedTopicsService:
    """
    Get or create a singleton instance of the related topics service.
    
    Args:
        llm_service: LLM service instance
        
    Returns:
        RelatedTopicsService instance
    """
    global _related_topics_service
    if _related_topics_service is None:
        _related_topics_service = RelatedTopicsService(llm_service)
    return _related_topics_service
