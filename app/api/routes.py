from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.models.schemas import (
    Topic, TopicRequest, ExplainTopicRequest, 
    RelatedTopicsRequest, TopicExplanation
)
from app.services.curiosity_service import CuriosityService
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.services.explanation_service import ExplanationService
from app.services.related_topics_service import RelatedTopicsService
from app.api.dependencies import get_curiosity_service, get_explanation_service, get_related_topics_service

# Create routers
topics_router = APIRouter(prefix="/topics", tags=["Topics"])
explanations_router = APIRouter(prefix="/explanations", tags=["Explanations"])
related_topics_router = APIRouter(prefix="/related-topics", tags=["Related Topics"])

@topics_router.post("/", response_model=List[Topic], status_code=status.HTTP_200_OK)
async def generate_topics(
    request: TopicRequest,
    curiosity_service: CuriosityService = Depends(get_curiosity_service)
):
    """
    Generate a list of interesting topics based on user profile.
    
    - For the first 3 topics: general-purpose, no user_role/usage_intent required.
    - After 3 topics: user_role and usage_intent are required for personalization.
    
    Args:
        request: Topic request with optional user_role, usage_intent, and n_topics
        
    Returns:
        List of topics with topic name and description
    """
    try:
        topics = curiosity_service.generate_topics(
            n_topics=request.n_topics,
            user_role=request.user_role,
            usage_intent=request.usage_intent
        )
        return topics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating topics: {str(e)}"
        )

@explanations_router.post("/", response_model=TopicExplanation, status_code=status.HTTP_200_OK)
async def explain_topic(
    request: ExplainTopicRequest,
    curiosity_service: CuriosityService = Depends(get_curiosity_service),
    explanation_service: ExplanationService = Depends(get_explanation_service)
):
    """
    Generate a detailed explanation for a given topic.
    
    - For the first 3 topics: general-purpose, no user_role/usage_intent required.
    - After 3 topics: user_role and usage_intent are required for personalization.
    - If sub_topic is provided, the explanation will focus on that aspect of the main topic.
    - If intent is provided, the explanation will be framed according to that intent.
    
    Args:
        request: Explanation request with topic, optional user_role, usage_intent, sub_topic, and intent
        
    Returns:
        Topic explanation with main topic, subtopics, and related topics
    """
    try:
        # Store current topic for context
        curiosity_service.current_topic = request.topic
        
        # Update topic history and user interests
        curiosity_service._manage_topic_history(request.topic)
        interest_context = curiosity_service._get_user_interest_context()
        
        # Check if we need to set user profile
        if not curiosity_service.is_general_phase():
            if not request.user_role or not request.usage_intent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="user_role and usage_intent are required after 3 topics are explored."
                )
            curiosity_service.set_user_profile(request.user_role, request.usage_intent)
        
        # Generate explanation
        explanation = explanation_service.explain_topic(
            topic=request.topic,
            conversation_history=curiosity_service.conversation_history,
            topic_history=curiosity_service.topic_history,
            is_general_phase=curiosity_service.is_general_phase(),
            user_role=request.user_role,
            usage_intent=request.usage_intent,
            sub_topic=request.sub_topic,
            intent=request.intent,
            interest_context=interest_context
        )
        
        return explanation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error explaining topic: {str(e)}"
        )

@related_topics_router.post("/", response_model=List[Topic], status_code=status.HTTP_200_OK)
async def explore_related_topics(
    request: RelatedTopicsRequest,
    curiosity_service: CuriosityService = Depends(get_curiosity_service),
    related_topics_service: RelatedTopicsService = Depends(get_related_topics_service)
):
    """
    Generate personalized related topics based on the current topic and user interests.
    
    - For the first 3 topics: general-purpose, no user_role/usage_intent required.
    - After 3 topics: user_role and usage_intent are required for personalization.
    
    Args:
        request: Related topics request with topic, optional user_role and usage_intent
        
    Returns:
        List of related topics with topic name and description
    """
    try:
        # Update topic history and user interests
        curiosity_service._manage_topic_history(request.topic)
        interest_context = curiosity_service._get_user_interest_context()
        
        # Check if we need to set user profile
        if not curiosity_service.is_general_phase():
            if not request.user_role or not request.usage_intent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="user_role and usage_intent are required after 3 topics are explored."
                )
            curiosity_service.set_user_profile(request.user_role, request.usage_intent)
        
        # Generate related topics
        related_topics = related_topics_service.explore_related_topics(
            topic=request.topic,
            conversation_history=curiosity_service.conversation_history,
            topic_history=curiosity_service.topic_history,
            is_general_phase=curiosity_service.is_general_phase(),
            user_role=request.user_role,
            usage_intent=request.usage_intent,
            interest_context=interest_context
        )
        
        return related_topics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exploring related topics: {str(e)}"
        )

@topics_router.post("/reset", status_code=status.HTTP_200_OK)
async def reset_conversation(
    curiosity_service: CuriosityService = Depends(get_curiosity_service)
):
    """
    Reset the conversation context and topic history.
    
    Returns:
        Success message
    """
    try:
        curiosity_service.reset_conversation()
        return {"message": "Conversation history has been cleared!"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting conversation: {str(e)}"
        )
