import json
import re
from typing import List, Dict, Any, Optional
import random

from app.core.config import settings
from app.services.llm_service import LLMService

class RelatedTopicsService:
    """
    Service for generating related topics based on a main topic.
    """
    def __init__(self, llm_service: LLMService):
        """
        Initialize the related topics service.
        
        Args:
            llm_service: LLM service for generating content
        """
        self.llm_service = llm_service
        
    def explore_related_topics(
        self,
        topic: str,
        conversation_history: List[Dict[str, str]],
        topic_history: List[str],
        is_general_phase: bool,
        user_role: str = None,
        usage_intent: str = None,
        interest_context: str = ""
    ) -> List[Dict[str, str]]:
        """
        Generate personalized related topics based on the current topic and user interests.
        
        Args:
            topic: The topic to find related topics for
            conversation_history: Conversation history for context
            topic_history: Topic history for context
            is_general_phase: Whether the user is in the general phase
            user_role: The role of the user (for personalized phase)
            usage_intent: How the user plans to use Curiosity Blocks (for personalized phase)
            interest_context: User interest context
            
        Returns:
            List of related topic dictionaries with topic and description
        """
        try:
            # Get ALL previous topics to explicitly connect with
            previous_topics_context = ""
            if topic_history and len(topic_history) > 1:
                prev_topics = [t for t in topic_history if t.lower() != topic.lower()]
                if prev_topics:
                    all_prev_topics = ", ".join(prev_topics)
                    previous_topics_context = f"\nThe user has previously explored these topics: {all_prev_topics}. Now they are exploring '{topic}'."
                    previous_topics_context += f"\nYour task is to create CREATIVE and MEANINGFUL connections between '{topic}' and ALL previously explored topics."
                    previous_topics_context += f"\nEven if the topics seem completely unrelated, find innovative ways to connect them."

            # Prompt logic
            if is_general_phase:
                prompt = f"""
                Based on the topic "{topic}" and ALL previously explored topics, suggest exactly 3 creative and general-purpose related topics for a wide audience.
                {interest_context}
                {previous_topics_context}

                Each topic must create connections between the current topic and at least one previously explored topic.
                Be creative and innovative in finding connections between seemingly unrelated topics.
                The connections should be meaningful and provide new insights.
                Topics should be suitable for a general audience and expand their understanding.

                For each topic, provide:
                1. A clear and engaging title that shows the creative connection (max 50 chars)
                2. A brief description of how this topic connects previously explored topics (max 100 chars)

                RESPOND IN THIS EXACT FORMAT - A JSON ARRAY WITH 3 OBJECTS:
                [
                  {{
                    "topic": "Topic Title",
                    "description": "Brief description of connection"
                  }},
                  {{
                    "topic": "Topic Title 2",
                    "description": "Brief description of connection 2"
                  }},
                  {{
                    "topic": "Topic Title 3",
                    "description": "Brief description of connection 3"
                  }}
                ]
                ONLY RETURN THE JSON. NO OTHER TEXT.
                """
            else:
                if not user_role or not usage_intent:
                    raise ValueError("user_role and usage_intent are required after 3 topics are explored.")
                
                prompt = f"""
                The user is a {user_role}. They plan to use Curiosity Blocks as follows: "{usage_intent}".
                Based on the topic "{topic}" and ALL previously explored topics, suggest exactly 3 creative and personalized related topics for this user.
                {interest_context}
                {previous_topics_context}

                Each topic must create connections between the current topic and at least one previously explored topic.
                Be creative and innovative in finding connections between seemingly unrelated topics.
                The connections should be meaningful and provide new insights.
                Topics should be relevant to the user's background and intent, and expand their understanding.

                For each topic, provide:
                1. A clear and engaging title that shows the creative connection (max 50 chars)
                2. A brief description of how this topic connects previously explored topics (max 100 chars)

                RESPOND IN THIS EXACT FORMAT - A JSON ARRAY WITH 3 OBJECTS:
                [
                  {{
                    "topic": "Topic Title",
                    "description": "Brief description of connection"
                  }},
                  {{
                    "topic": "Topic Title 2",
                    "description": "Brief description of connection 2"
                  }},
                  {{
                    "topic": "Topic Title 3",
                    "description": "Brief description of connection 3"
                  }}
                ]
                ONLY RETURN THE JSON. NO OTHER TEXT.
                """

            # Use GPT-4 specifically for related topics to get better responses
            try:
                response = self.llm_service.get_completion(
                    messages=[
                        {"role": "system", "content": conversation_history[0]["content"]}, 
                        {"role": "user", "content": prompt}
                    ],
                    model="gpt-4-1106-preview",
                    temperature=0.9,
                    max_tokens=1000,
                )
            except Exception as e:
                print(f"Error using GPT-4, falling back to default model: {e}")
                response = self.llm_service.get_completion_with_history(
                    prompt=prompt,
                    conversation_history=conversation_history,
                    topic_history=topic_history,
                    temperature=0.9
                )
                
            try:
                # Try to extract JSON from the response if it's not pure JSON
                if not response.strip().startswith('['):
                    json_match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        related_topics = json.loads(json_str)
                    else:
                        json_match = re.search(r'```(?:json)?\s*\n?(\[\s*\{.*?\}\s*\])\s*```', response, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                            related_topics = json.loads(json_str)
                        else:
                            related_topics = self._manually_parse_topics(response)
                else:
                    related_topics = json.loads(response)

                # Validate and format the response
                formatted_topics = []
                for rt in related_topics:
                    if isinstance(rt, dict):
                        topic_name = str(rt.get("topic", ""))[:50]
                        description = rt.get("description", rt.get("summary", "No description provided."))
                        description = str(description)
                        connection = rt.get("connection", "")
                        if connection:
                            if "connection" in rt and len(connection) > len(description):
                                description = connection
                            else:
                                description += f" {connection}"
                        formatted_topics.append({
                            "topic": topic_name if topic_name else f"Related Topic {len(formatted_topics) + 1}",
                            "description": description
                        })

                # Ensure exactly 3 topics by using previously explored topics or related fields
                if len(formatted_topics) < 3:
                    previous_topics = [t for t in topic_history if t.lower() != topic.lower()]
                    if previous_topics:
                        for i in range(3 - len(formatted_topics)):
                            if i < len(previous_topics):
                                prev_topic = previous_topics[i]
                                formatted_topics.append({
                                    "topic": prev_topic,
                                    "description": f"You previously explored this topic. Revisiting {prev_topic} may help deepen your understanding and see connections with {topic}."
                                })
                            else:
                                related_field = self._generate_related_field(topic)
                                formatted_topics.append({
                                    "topic": related_field,
                                    "description": f"This area is connected to {topic} and exploring it will broaden your perspective."
                                })
                    else:
                        for i in range(3 - len(formatted_topics)):
                            related_field = self._generate_related_field(topic)
                            formatted_topics.append({
                                "topic": related_field,
                                "description": f"This area is connected to {topic} and exploring it will broaden your perspective."
                            })

                return formatted_topics[:3]
            except json.JSONDecodeError as e:
                print(f"Error parsing related topics JSON: {e}")
                print(f"Raw response: {response}")
                related_topics = self._manually_parse_topics(response)
                if not related_topics:
                    return []
                return [
                    {"topic": f"Related Topic {i+1}", "description": "Related topic description"}
                    for i in range(3)
                ]
        except Exception as e:
            print(f"Error in explore_related_topics: {e}")
            raise
            
    def _manually_parse_topics(self, text: str) -> List[Dict[str, str]]:
        """
        Manually parse topics from text when JSON parsing fails.
        
        Args:
            text: The text to parse
            
        Returns:
            List of topic dictionaries with topic and description
        """
        import re
        topics = []
        
        # Look for numbered topics (1. Topic: "Title" or 1. "Title" or Topic 1: "Title")
        topic_patterns = [
            r'\d+\.\s*(?:Topic:|")(.*?)(?:"|-)\s*(?:-|:)\s*(.*?)(?=\d+\.|$|\n\n)',  # 1. Topic: "Title" - Description
            r'\d+\.\s*"(.*?)"\s*(?:-|:)\s*(.*?)(?=\d+\.|$|\n\n)',  # 1. "Title" - Description
            r'Topic\s*\d+:?\s*"?(.*?)"?\s*(?:-|:)\s*(.*?)(?=Topic\s*\d+|$|\n\n)'  # Topic 1: Title - Description
        ]
        
        for pattern in topic_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                for match in matches[:3]:  # Take up to 3 topics
                    topic = match[0].strip()
                    description = match[1].strip() if len(match) > 1 else ""
                    topics.append({"topic": topic, "description": description})
                break
        
        # If no matches found, try to extract any topic-like sections
        if not topics:
            # Look for sections that might contain topics
            sections = re.split(r'\n\s*\n', text)
            for i, section in enumerate(sections[:3]):  # Take up to 3 sections
                # Try to extract a title and description
                title_match = re.search(r'(?:"|")([^"]+)(?:"|"|:)|([A-Z][^\n:]+):', section)
                if title_match:
                    title = title_match.group(1) or title_match.group(2)
                    # Get the rest as description
                    desc_text = re.sub(r'(?:"|")([^"]+)(?:"|"|:)|([A-Z][^\n:]+):', '', section, 1)
                    topics.append({"topic": title.strip(), "description": desc_text.strip()})
                else:
                    # Just use the first line as title and the rest as description
                    lines = section.strip().split('\n', 1)
                    title = lines[0].strip()
                    desc = lines[1].strip() if len(lines) > 1 else ""
                    topics.append({"topic": title, "description": desc})
        
        # If we still don't have topics, create generic ones
        if not topics:
            for i in range(1, 4):  # Create 3 generic topics
                topics.append({
                    "topic": f"Related Topic {i}",
                    "description": f"A topic related to your exploration journey."
                })
        
        return topics
        
    def _generate_related_field(self, topic: str) -> str:
        """
        Generate a related field to a topic when we need to fill in additional topics.
        
        Args:
            topic: The topic to find a related field for
            
        Returns:
            A related field name
        """
        # Use broad, general-purpose categories
        general_fields = [
            "science and nature",
            "technology and innovation",
            "arts and creativity",
            "history and culture",
            "society and people",
            "philosophy and ideas",
            "health and wellness",
            "business and economy",
            "travel and geography",
            "media and communication"
        ]
        
        # Pick a random general-purpose field not obviously matching the topic
        topic_lower = topic.lower()
        non_matching_fields = [f for f in general_fields if f not in topic_lower]
        if non_matching_fields:
            return random.choice(non_matching_fields)
        return random.choice(general_fields)
