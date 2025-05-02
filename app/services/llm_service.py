import openai
from typing import List, Dict, Any
from app.core.config import settings

class LLMService:
    """
    Service for interacting with the OpenAI LLM API.
    """
    def __init__(self):
        """Initialize the LLM service with OpenAI client."""
        self.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=self.api_key)
        
    def get_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        temperature: float = None, 
        max_tokens: int = None
    ) -> str:
        """
        Get a completion from the OpenAI API.
        
        Args:
            messages: List of message dictionaries with role and content
            model: The model to use (defaults to settings.DEFAULT_MODEL)
            temperature: The temperature to use (defaults to settings.DEFAULT_TEMPERATURE)
            max_tokens: The maximum number of tokens to generate (defaults to settings.DEFAULT_MAX_TOKENS)
            
        Returns:
            The generated text response
        """
        try:
            response = self.client.chat.completions.create(
                model=model or settings.DEFAULT_MODEL,
                messages=messages,
                temperature=temperature or settings.DEFAULT_TEMPERATURE,
                max_tokens=max_tokens or settings.DEFAULT_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in OpenAI API call: {str(e)}")
            return "I'm having trouble processing that right now. Let's try something else."
            
    def get_completion_with_history(
        self, 
        prompt: str, 
        conversation_history: List[Dict[str, str]],
        topic_history: List[str] = None,
        temperature: float = None, 
        max_tokens: int = None
    ) -> str:
        """
        Get a completion using conversation history and topic history for context.
        
        Args:
            prompt: The prompt to send to the API
            conversation_history: List of previous messages
            topic_history: Optional list of previously explored topics
            temperature: The temperature to use
            max_tokens: The maximum number of tokens to generate
            
        Returns:
            The generated text response
        """
        # Add topic history context to the prompt
        topic_history_context = ""
        if topic_history and len(topic_history) > 0:
            recent_topics = topic_history[-5:]  # Last 5 topics
            topic_history_context = f"\nPrevious topics explored: {', '.join(recent_topics)}.\n"
            topic_history_context += "Please ensure your response connects to these previous topics when relevant.\n"
        
        enhanced_prompt = topic_history_context + prompt
        
        # Create messages for the API call
        messages = conversation_history + [{"role": "user", "content": enhanced_prompt}]
        
        # Get completion
        reply = self.get_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return reply
