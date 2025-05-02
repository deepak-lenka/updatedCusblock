from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class Topic(BaseModel):
    """Topic model with title and description"""
    topic: str = Field(..., max_length=50, description="The name of the topic")
    description: str = Field(..., max_length=100, description="A brief description of the topic")

class SubTopic(BaseModel):
    """SubTopic model with title, explanation and optional web resources"""
    title: str = Field(..., description="The title of the subtopic")
    explanation: str = Field(..., description="A concise explanation of the subtopic")
    web_resources: Optional[Union[str, List[str]]] = Field(None, description="Links to resources related to the subtopic")

class RelatedTopic(BaseModel):
    """Related topic model with topic name and summary"""
    topic: str = Field(..., description="Name of a related topic")
    summary: str = Field(..., description="A brief summary of how it relates to the main topic")
    web_resources: Optional[Union[str, List[str]]] = Field(None, description="Links to resources related to the topic")

class MainTopic(BaseModel):
    """Main topic model with title, explanation and optional image URL"""
    title: str = Field(..., description="A catchy title for the topic")
    explanation: str = Field(..., description="A detailed explanation of the topic")
    image_url: Optional[str] = Field(None, description="URL to a relevant image")
    web_resources: Optional[Union[str, List[str]]] = Field(None, description="Links to resources related to the topic")

class TopicExplanation(BaseModel):
    """Complete topic explanation with main topic, subtopics and related topics"""
    main_topic: MainTopic
    subtopics: List[SubTopic]
    related_topics: List[RelatedTopic]

class TopicRequest(BaseModel):
    """Request model for generating topics"""
    user_role: Optional[str] = Field(None, description="The role of the user (e.g., Student, Professional)")
    usage_intent: Optional[str] = Field(None, description="How the user plans to use Curiosity Blocks")
    n_topics: Optional[int] = Field(4, description="Number of topics to generate")

class ExplainTopicRequest(BaseModel):
    """Request model for explaining a topic"""
    topic: str = Field(..., description="The topic to explain")
    user_role: Optional[str] = Field(None, description="The role of the user")
    usage_intent: Optional[str] = Field(None, description="How the user plans to use Curiosity Blocks")
    sub_topic: Optional[str] = Field(None, description="Optional sub-topic to focus on")
    intent: Optional[str] = Field(None, description="Optional intent or angle for the explanation")

class RelatedTopicsRequest(BaseModel):
    """Request model for exploring related topics"""
    topic: str = Field(..., description="The topic to find related topics for")
    user_role: Optional[str] = Field(None, description="The role of the user")
    usage_intent: Optional[str] = Field(None, description="How the user plans to use Curiosity Blocks")

class UserProfile(BaseModel):
    """User profile with role and usage intent"""
    user_role: str = Field(..., description="The role of the user")
    usage_intent: str = Field(..., description="How the user plans to use Curiosity Blocks")

class WebSearchResult(BaseModel):
    """Web search result model"""
    formatted_text: str
    image_url: Optional[str] = None
