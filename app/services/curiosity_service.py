import os
import json
import re
import threading
from typing import List, Dict, Any, Optional
import random

from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.models.schemas import Topic, TopicExplanation, RelatedTopic

class CuriosityService:
    """
    Main service for handling curiosity-based topic exploration.
    """
    def __init__(self):
        """Initialize the curiosity service with required components."""
        # Initialize LLM service
        self.llm_service = LLMService()
        
        # Initialize search service
        self.search_service = SearchService()
        
        # System prompts
        self.general_system_prompt = (
            "You are a helpful, engaging, and informative assistant. "
            "You help users explore any topic of curiosity in a clear, accessible, and interesting way. "
            "Avoid educational framing or references to grade, school, or curriculum unless specifically asked."
        )
        self.personalized_system_prompt = (
            "You are a helpful, engaging, and informative assistant. "
            "You tailor your responses based on the user's background and intent. "
            "Use the user's role and how they plan to use Curiosity Blocks to make your responses more relevant."
        )
        
        # Start with general prompt
        self.system_prompt = self.general_system_prompt
        
        # Maintain conversation history
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Topic tracking
        self.topic_history = []  # List of topics explored
        self.subtopic_history = []  # List of subtopics explored
        self.user_interests = {}  # Dictionary to track user interests and their weights
        self.interest_categories = {}  # Map topics to broader categories
        self.max_history = settings.MAX_HISTORY
        
        # User profile
        self.user_role = None
        self.usage_intent = None
        
        # Current topic for context
        self.current_topic = None
        self.topic_category = "general"
        
        # Initialize document index if data directory exists
        self._initialize_data_directory()
        
    def _initialize_data_directory(self):
        """Initialize the data directory with sample content if needed."""
        try:
            # Create data directory if it doesn't exist
            if not os.path.exists(settings.DATA_DIR):
                os.makedirs(settings.DATA_DIR, exist_ok=True)
                print(f"Created data directory: {settings.DATA_DIR}")
            
            # Check if directory is empty
            if os.path.exists(settings.DATA_DIR) and not os.listdir(settings.DATA_DIR):
                # Create a sample file with general content
                sample_file_path = os.path.join(settings.DATA_DIR, "sample_content.txt")
                with open(sample_file_path, "w") as f:
                    f.write("""This is a sample educational content file for the Curiosity Blocks application.

The application uses this file to initialize the document index when no other content is available.

Topics covered in this application include:
- Science (Physics, Chemistry, Biology, Astronomy)
- Mathematics (Algebra, Geometry, Calculus)
- History (Ancient, Medieval, Modern)
- Literature and Language Arts
- Geography and Social Studies
- Technology and Computer Science
                    """)
                print(f"Created sample content file: {sample_file_path}")
        except Exception as e:
            print(f"Error initializing data directory: {e}")
            
    def is_general_phase(self) -> bool:
        """Return True if user is in the first 3 topics (general phase), else False (personalized phase)."""
        return len(self.topic_history) < 3
        
    def set_user_profile(self, user_role: str, usage_intent: str):
        """Set user profile for personalized phase."""
        self.user_role = user_role
        self.usage_intent = usage_intent
        # Switch to personalized system prompt
        self.system_prompt = self.personalized_system_prompt
        # Update conversation history system prompt
        if self.conversation_history and self.conversation_history[0]["role"] == "system":
            self.conversation_history[0]["content"] = self.system_prompt
            
    def generate_topics(
        self, 
        n_topics: int = 4, 
        user_role: str = None, 
        usage_intent: str = None
    ) -> List[Dict[str, str]]:
        """
        Generate curiosity topics.
        
        Args:
            n_topics: Number of topics to generate
            user_role: The role of the user (for personalized phase)
            usage_intent: How the user plans to use Curiosity Blocks (for personalized phase)
            
        Returns:
            List of topic dictionaries with topic and description
        """
        try:
            # General phase: first 3 topics, no user_role/usage_intent
            if self.is_general_phase():
                # Get user interest context to personalize suggestions
                interest_context = self._get_user_interest_context() if self.user_interests else ""
                excluded_topics = ""
                if self.topic_history:
                    excluded_topics = f"\nDo NOT suggest any of these previously explored topics: {', '.join(self.topic_history[-10:])}\n"
                import time
                current_time = time.time()
                randomization = f"\nThe current timestamp is {current_time}. Use this as a seed to generate diverse topics.\n"
                subject_focus = ""
                if self.topic_history and len(self.topic_history) >= 2:
                    learning_focus = self._infer_learning_focus(self.topic_history)
                    subject_focus = f"\nBased on the user's exploration pattern, they seem to be {learning_focus}. Provide a mix of topics that both extend this focus and introduce complementary areas.\n"
                else:
                    subject_focus = "\nProvide a diverse mix of topics across different areas (science, technology, arts, society, nature, innovation, etc.).\n"
                prompt = f"""
                Generate {n_topics} interesting and DIVERSE general-purpose topics for a wide audience.
                {interest_context}
                {subject_focus}
                {excluded_topics}
                {randomization}

                Each topic should be:
                1. Engaging and spark curiosity
                2. Suitable for a general audience (not just students)
                3. Specific enough to explore in depth (avoid overly broad topics)
                4. DIFFERENT from each other (cover various areas)

                Format the response as a JSON array with {n_topics} topic objects, each containing:
                - topic (string): The name of the topic (max 50 chars)
                - description (string): A brief 1-sentence description (max 100 chars)
                """
                response = self.llm_service.get_completion_with_history(
                    prompt=prompt,
                    conversation_history=self.conversation_history,
                    topic_history=self.topic_history,
                    temperature=0.9
                )
            else:
                # Personalized phase: after 3 topics, use user_role and usage_intent
                if not user_role or not usage_intent:
                    raise ValueError("user_role and usage_intent are required after 3 topics are explored.")
                self.set_user_profile(user_role, usage_intent)
                interest_context = self._get_user_interest_context() if self.user_interests else ""
                excluded_topics = ""
                if self.topic_history:
                    excluded_topics = f"\nDo NOT suggest any of these previously explored topics: {', '.join(self.topic_history[-10:])}\n"
                import time
                current_time = time.time()
                randomization = f"\nThe current timestamp is {current_time}. Use this as a seed to generate diverse topics.\n"
                subject_focus = ""
                if self.topic_history and len(self.topic_history) >= 2:
                    learning_focus = self._infer_learning_focus(self.topic_history)
                    subject_focus = f"\nBased on the user's exploration pattern, they seem to be {learning_focus}. Provide a mix of topics that both extend this focus and introduce complementary areas.\n"
                else:
                    subject_focus = "\nProvide a diverse mix of topics across different areas (science, technology, arts, society, nature, innovation, etc.).\n"
                prompt = f"""
                The user is a {user_role}. They plan to use Curiosity Blocks as follows: "{usage_intent}".
                {interest_context}
                {subject_focus}
                {excluded_topics}
                {randomization}

                Generate {n_topics} interesting and DIVERSE topics tailored for this user.
                Each topic should be:
                1. Engaging and spark curiosity
                2. Relevant to the user's background and intent
                3. Specific enough to explore in depth (avoid overly broad topics)
                4. DIFFERENT from each other (cover various areas)

                Format the response as a JSON array with {n_topics} topic objects, each containing:
                - topic (string): The name of the topic (max 50 chars)
                - description (string): A brief 1-sentence description (max 100 chars)
                """
                response = self.llm_service.get_completion_with_history(
                    prompt=prompt,
                    conversation_history=self.conversation_history,
                    topic_history=self.topic_history,
                    temperature=0.9
                )

            try:
                topics = json.loads(response)
                # Validate the response format
                if not isinstance(topics, list):
                    raise ValueError("Response is not a list")
                formatted_topics = []
                for topic in topics:
                    if isinstance(topic, dict) and "topic" in topic and "description" in topic:
                        formatted_topics.append({
                            "topic": str(topic["topic"])[:50],  # Ensure string and length limit
                            "description": str(topic["description"])[:100]  # Ensure string and length limit
                        })
                return formatted_topics[:n_topics]  # Ensure we return exactly n_topics
            except json.JSONDecodeError as e:
                print(f"Error parsing topics JSON: {e}")
                print(f"Raw response: {response}")
                # Try to manually parse topics
                topics = self._manually_parse_topics(response)
                if topics:
                    return topics[:n_topics]
                # Return a fallback response
                return [{"topic": f"Topic {i+1}", "description": "Generic topic description"} for i in range(n_topics)]
        except Exception as e:
            print(f"Error in generate_topics: {e}")
            raise
            
    def _manually_parse_topics(self, text: str) -> List[Dict[str, str]]:
        """Manually parse topics from text when JSON parsing fails."""
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
        """Generate a related field to a topic when we need to fill in additional topics."""
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
        
    def reset_conversation(self):
        """Reset the conversation context and topic history."""
        # Reset conversation history
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Clear topic and interest tracking
        self.topic_history = []
        self.subtopic_history = []
        self.user_interests = {}
        self.interest_categories = {}
        
    def _manage_topic_history(self, topic: str):
        """
        Manage the topic history and update user interests based on explored topics.
        Ensures proper connections between topics in the learning journey.
        """
        # Normalize topic for case-insensitive comparison
        normalized_topic = topic.lower().strip()
        
        # Check if topic is already in history (case-insensitive)
        existing_topics = [t.lower().strip() for t in self.topic_history]
        if normalized_topic not in existing_topics:
            # Add new topic to history
            self.topic_history.append(topic)
            
            # Limit history size
            if len(self.topic_history) > self.max_history:
                self.topic_history.pop(0)
            
            # Update user interests with the new topic
            self._update_user_interests(topic)
        else:
            # If topic exists but in different case/format, update to the new format
            # but don't change its position in history (to maintain chronology)
            for i, t in enumerate(self.topic_history):
                if t.lower().strip() == normalized_topic:
                    self.topic_history[i] = topic
                    break
            
            # Still update interests to reinforce this topic
            self._update_user_interests(topic)
            
    def _update_user_interests(self, topic: str):
        """Update user interests based on a topic."""
        # Normalize topic
        topic = topic.strip()
        
        # Increment interest in this topic
        if topic in self.user_interests:
            self.user_interests[topic] += 1
        else:
            self.user_interests[topic] = 1
            
        # Categorize the topic if not already done
        if topic not in self.interest_categories:
            self._categorize_topic(topic)
            
    def _categorize_topic(self, topic: str):
        """Categorize a topic into broad, general-purpose areas."""
        try:
            topic_lower = topic.lower()
            categories = {
                "science and nature": ["science", "nature", "biology", "physics", "chemistry", "astronomy", "earth", "environment"],
                "technology and innovation": ["technology", "innovation", "computer", "internet", "ai", "robotics", "digital"],
                "arts and creativity": ["art", "music", "painting", "sculpture", "dance", "theater", "film", "photography", "creativity"],
                "history and culture": ["history", "culture", "civilization", "ancient", "modern", "tradition"],
                "society and people": ["society", "people", "community", "psychology", "sociology", "politics"],
                "philosophy and ideas": ["philosophy", "ideas", "ethics", "logic", "thought"],
                "health and wellness": ["health", "wellness", "medicine", "fitness", "nutrition"],
                "business and economy": ["business", "economy", "finance", "trade", "entrepreneurship"],
                "travel and geography": ["travel", "geography", "country", "continent", "city", "exploration"],
                "media and communication": ["media", "communication", "news", "journalism", "broadcast", "social media"]
            }
            for category, keywords in categories.items():
                if any(keyword in topic_lower for keyword in keywords):
                    self.interest_categories[topic] = category
                    return
            self.interest_categories[topic] = "general"
        except Exception as e:
            print(f"Error categorizing topic: {e}")
            
    def _infer_learning_focus(self, topics):
        """
        Analyze a list of topics to infer the user's learning focus or exploration journey.
        """
        if not topics or len(topics) < 2:
            return "exploring foundational concepts"
        # Use a simple approach to categorize the journey by broad area
        broad_areas = [
            "science and nature", "technology and innovation", "arts and creativity",
            "history and culture", "society and people", "philosophy and ideas",
            "health and wellness", "business and economy", "travel and geography", "media and communication"
        ]
        area_counts = {area: 0 for area in broad_areas}
        for topic in topics:
            topic_lower = topic.lower()
            for area in broad_areas:
                if area.split()[0] in topic_lower or area.split()[-1] in topic_lower:
                    area_counts[area] += 1
        dominant_area = max(area_counts.items(), key=lambda x: x[1])
        if dominant_area[1] > 0:
            return f"exploring {dominant_area[0]}"
        if len(topics) >= 3:
            if len(topics[0]) < len(topics[-1]) and any(t in topics[-1].lower() for t in topics[0].lower().split()):
                return "exploring topics in increasing depth and specificity"
            elif any(topics[-1].lower() in t.lower() or t.lower() in topics[-1].lower() for t in topics[:-1]):
                return "exploring related concepts in a connected area"
        return "building a comprehensive understanding across multiple topics"
    
    def _get_user_interest_context(self):
        """
        Generate a context string based on user interests to guide topic recommendations.
        """
        if not self.user_interests:
            return ""
            
        # Sort interests by weight
        sorted_interests = sorted(self.user_interests.items(), key=lambda x: x[1], reverse=True)
        top_interests = sorted_interests[:5]  # Take top 5 interests
        
        interest_context = "Based on the user's exploration history, they appear interested in: " + \
                          ", ".join([f"{interest} (weight: {weight})" for interest, weight in top_interests])
        
        # Add recent topics
        if self.topic_history:
            recent_topics = self.topic_history[-3:]
            interest_context += f"\nTheir most recent topics were: {', '.join(recent_topics)}"
            
        # Add inferred learning focus if we have enough topics
        if len(self.topic_history) >= 2:
            learning_focus = self._infer_learning_focus(self.topic_history)
            interest_context += f"\nTheir learning journey suggests they are {learning_focus}."
            
        return interest_context
