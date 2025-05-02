import json
import threading
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.models.schemas import TopicExplanation

class ExplanationService:
    """
    Service for generating detailed explanations about topics.
    """
    def __init__(self, llm_service: LLMService, search_service: SearchService):
        """
        Initialize the explanation service.
        
        Args:
            llm_service: LLM service for generating content
            search_service: Search service for web searches
        """
        self.llm_service = llm_service
        self.search_service = search_service
        self.main_topic_results = []
        
    def explain_topic(
        self,
        topic: str,
        conversation_history: List[Dict[str, str]],
        topic_history: List[str],
        is_general_phase: bool,
        user_role: str = None,
        usage_intent: str = None,
        sub_topic: str = None,
        intent: str = None,
        interest_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a detailed explanation for a given topic.
        
        Args:
            topic: The topic to explain
            conversation_history: Conversation history for context
            topic_history: Topic history for context
            is_general_phase: Whether the user is in the general phase
            user_role: The role of the user (for personalized phase)
            usage_intent: How the user plans to use Curiosity Blocks (for personalized phase)
            sub_topic: Optional sub-topic to focus on
            intent: Optional intent or angle for the explanation
            interest_context: User interest context
            
        Returns:
            Dictionary with main_topic, subtopics, and related_topics
        """
        # Store the topic category for better image selection
        topic_categories = {
            'science': ['physics', 'chemistry', 'biology', 'astronomy', 'space', 'earth', 'environment', 'technology', 'engineering'],
            'math': ['mathematics', 'algebra', 'geometry', 'calculus', 'statistics', 'arithmetic', 'number', 'equation'],
            'history': ['history', 'civilization', 'war', 'ancient', 'medieval', 'modern', 'revolution', 'empire', 'kingdom'],
            'geography': ['geography', 'map', 'country', 'continent', 'ocean', 'river', 'mountain', 'climate', 'weather'],
            'literature': ['literature', 'book', 'novel', 'poem', 'author', 'writer', 'story', 'character', 'fiction'],
            'art': ['art', 'painting', 'sculpture', 'music', 'dance', 'theater', 'film', 'photography', 'design'],
        }
        topic_lower = topic.lower()
        topic_category = 'general'
        for category, keywords in topic_categories.items():
            if any(keyword in topic_lower for keyword in keywords):
                topic_category = category
                break

        # Start web search in parallel with explanation generation
        self.main_topic_results = []

        def background_search():
            # For general phase, just search for general info
            if is_general_phase:
                general_query = f"{topic} information facts summary"
                self.main_topic_results = self.search_service.search_web(general_query, educational_focus=False)
            else:
                # For personalized phase, use user intent if available
                if not user_role or not usage_intent:
                    general_query = f"{topic} information facts summary"
                    self.main_topic_results = self.search_service.search_web(general_query, educational_focus=False)
                else:
                    personalized_query = f"{topic} for a {user_role} who wants to '{usage_intent}'"
                    self.main_topic_results = self.search_service.search_web(personalized_query, educational_focus=False)

        # Start the search in a background thread
        search_thread = threading.Thread(target=background_search)
        search_thread.daemon = True
        search_thread.start()

        # Generate the explanation
        try:
            previous_topics_context = ""
            user_intent_analysis = ""

            if topic_history and len(topic_history) > 1:
                prev_topics = [t for t in topic_history if t.lower() != topic.lower()]
                if prev_topics:
                    most_recent = prev_topics[-1] if prev_topics else ""
                    user_intent_analysis = f"\nThe user has moved from exploring '{most_recent}' to '{topic}'."
                    user_intent_analysis += f"\n1. Building on knowledge from '{most_recent}' to understand '{topic}'"
                    user_intent_analysis += f"\n2. Comparing or contrasting '{most_recent}' with '{topic}'"
                    user_intent_analysis += f"\n3. Exploring a specific aspect mentioned in '{most_recent}' in more depth"
                    user_intent_analysis += f"\n4. Following a logical learning progression in this subject area\n"
                    previous_topics_context = f"\nThe user recently explored '{most_recent}'."
                    previous_topics_context += f" Please make explicit connections between '{topic}' and '{most_recent}' in your explanation."
                    if len(prev_topics) > 1:
                        other_topics = prev_topics[:-1]
                        previous_topics_context += f"\nThe user's broader exploration journey includes: {', '.join(other_topics)}."
                        previous_topics_context += " Connect your explanation to this broader learning journey.\n"

            # Prompt logic
            sub_topic_instruction = ""
            if sub_topic:
                sub_topic_instruction = (
                    f"\nThe user is especially interested in the sub-topic: '{sub_topic}'. "
                    "Focus the explanation primarily on the main topic, but also address the sub-topic, making sure the main topic is the central theme and the sub-topic is explored as a related aspect or example."
                )
                
            # Intent framing note and explicit style instructions
            intent_note = ""
            extra_instruction = ""
            if intent:
                intent_note = f"\nFraming Note: {topic} × {intent.title()} Exploration\n"
                lowered = intent.strip().lower()
                if lowered in ["fun", "playful", "humor", "humorous"]:
                    extra_instruction = "Write the explanation in a playful, humorous, and engaging way. Use analogies, jokes, or surprising facts to make it enjoyable."
                elif lowered in ["curious", "curiosity", "make curious"]:
                    extra_instruction = "Spark curiosity with surprising facts, questions, and engaging language."
                elif lowered in ["sexy", "in a sexy way", "alluring", "seductive"]:
                    extra_instruction = "Use alluring, captivating, and stylish language, but remain professional and appropriate."
                elif lowered in ["for kids", "child", "children", "kid-friendly"]:
                    extra_instruction = "Make the explanation simple, friendly, and suitable for children. Use easy words and fun examples."
                elif lowered in ["history", "historical"]:
                    extra_instruction = "Focus on the historical development, context, and key milestones of the topic."
                elif lowered in ["psychology", "psychological"]:
                    extra_instruction = "Focus on the psychological, cognitive, and emotional aspects of the topic."
                else:
                    extra_instruction = f"Frame the explanation according to the intent: {intent}."
                    
            if is_general_phase:
                prompt = f"""
                {intent_note}
                {extra_instruction}
                Write an engaging, informative, and accessible explanation about "{topic}" for a general audience.
                {sub_topic_instruction}
                {interest_context}
                {previous_topics_context}
                {user_intent_analysis}

                Structure the response as a JSON object with the following sections:
                1. main_topic: An object containing:
                   - title: A catchy title for the topic
                   - explanation: A detailed, engaging explanation (300-500 words) that connects to the user's interests and previous topics where relevant. If a sub-topic is provided, address it as a related aspect, but keep the main topic as the focus.
                   - image_url: (optional) A URL to a relevant image

                2. subtopics: An array of 2-3 objects, each containing:
                   - title: A clear title for the subtopic
                   - explanation: A concise explanation (100-150 words)
                   - web_resources: (optional) Links to resources

                3. related_topics: An array of 2-3 objects, each containing:
                   - topic: Name of a related topic that connects to both the main topic and the user's previous explorations
                   - summary: A brief summary of how it relates (1-2 sentences)
                   - web_resources: (optional) Links to resources
                """
            else:
                if not user_role or not usage_intent:
                    raise ValueError("user_role and usage_intent are required after 3 topics are explored.")
                
                prompt = f"""
                {intent_note}
                {extra_instruction}
                The user is a {user_role}. They plan to use Curiosity Blocks as follows: "{usage_intent}".
                Write an engaging, informative, and accessible explanation about "{topic}" tailored to this user's background and intent.
                {sub_topic_instruction}
                {interest_context}
                {previous_topics_context}
                {user_intent_analysis}

                Structure the response as a JSON object with the following sections:
                1. main_topic: An object containing:
                   - title: A catchy title for the topic
                   - explanation: A detailed, engaging explanation (300-500 words) that connects to the user's interests and previous topics where relevant. If a sub-topic is provided, address it as a related aspect, but keep the main topic as the focus.
                   - image_url: (optional) A URL to a relevant image

                2. subtopics: An array of 2-3 objects, each containing:
                   - title: A clear title for the subtopic
                   - explanation: A concise explanation (100-150 words)
                   - web_resources: (optional) Links to resources

                3. related_topics: An array of 2-3 objects, each containing:
                   - topic: Name of a related topic that connects to both the main topic and the user's previous explorations
                   - summary: A brief summary of how it relates (1-2 sentences)
                   - web_resources: (optional) Links to resources
                """

            # Get response from OpenAI
            response = self.llm_service.get_completion_with_history(
                prompt=prompt,
                conversation_history=conversation_history,
                topic_history=topic_history
            )

            # Parse the JSON response
            try:
                content = json.loads(response)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw response: {response}")
                return {
                    "main_topic": {"title": topic, "explanation": "Failed to parse the explanation. Please try again."},
                    "subtopics": [],
                    "related_topics": []
                }

            # Process main topic explanation
            main_topic = content["main_topic"]
            explanation = main_topic["explanation"]

            # Ensure explanation is at least 100 words and ends with a complete sentence
            words = explanation.split()
            if len(words) < 100:
                sentences = explanation.split('.')
                new_explanation = []
                word_count = 0
                for sentence in sentences:
                    sentence_words = sentence.split()
                    word_count += len(sentence_words)
                    new_explanation.append(sentence)
                    if word_count >= 100:
                        break
                explanation = '.'.join(new_explanation).strip() + '.'
            else:
                current_length = 0
                sentences = explanation.split('.')
                new_explanation = []
                for sentence in sentences:
                    sentence_words = sentence.split()
                    if current_length + len(sentence_words) > 100:
                        break
                    current_length += len(sentence_words)
                    new_explanation.append(sentence)
                explanation = '.'.join(new_explanation).strip() + '.'

            main_topic["explanation"] = explanation

            # Ensure we have exactly 3 related topics
            related_topics = content["related_topics"]
            if len(related_topics) > 3:
                related_topics = related_topics[:3]
            elif len(related_topics) < 3:
                previous_topics = [t for t in topic_history if t.lower() != topic.lower()]
                if previous_topics:
                    for i in range(3 - len(related_topics)):
                        if i < len(previous_topics):
                            prev_topic = previous_topics[i]
                            related_topics.append({
                                "topic": prev_topic,
                                "summary": f"This topic is related to {topic} and was previously explored. Revisiting it may help deepen your understanding of both subjects."
                            })
                        else:
                            related_field = self._generate_related_field(topic)
                            related_topics.append({
                                "topic": related_field,
                                "summary": f"This field is connected to {topic} and exploring it will broaden your understanding of the subject area."
                            })
                else:
                    for i in range(3 - len(related_topics)):
                        related_field = self._generate_related_field(topic)
                        related_topics.append({
                            "topic": related_field,
                            "summary": f"This field is connected to {topic} and exploring it will broaden your understanding of the subject area."
                        })

            # Wait for a maximum of 3 seconds for the thread to complete
            import time
            start_time = time.time()
            while not self.main_topic_results and time.time() - start_time < 3:
                time.sleep(0.1)

            # Use whatever results we have, even if the search is still running
            web_resources = self.search_service.format_web_results(self.main_topic_results, topic)
            main_topic['web_resources'] = web_resources['formatted_text']
            main_topic['image_url'] = web_resources['image_url']

            # Get web resources for subtopics
            for subtopic in content["subtopics"]:
                try:
                    subtopic_query = f"{subtopic['title']} information facts summary"
                    subtopic_results = self.search_service.search_web(subtopic_query, educational_focus=False)
                    subtopic['web_resources'] = self.search_service.format_web_results(subtopic_results)['formatted_text']
                except Exception as e:
                    print(f"Error getting web resources for subtopic: {e}")
                    subtopic['web_resources'] = ""

            return {
                "main_topic": main_topic,
                "subtopics": content["subtopics"],
                "related_topics": related_topics
            }

        except Exception as e:
            print(f"Error in explain_topic: {e}")
            return {
                "main_topic": {"title": topic, "explanation": "Failed to generate explanation due to an error."},
                "subtopics": [],
                "related_topics": []
            }
            
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
        import random
        # Pick a random general-purpose field not obviously matching the topic
        topic_lower = topic.lower()
        non_matching_fields = [f for f in general_fields if f not in topic_lower]
        if non_matching_fields:
            return random.choice(non_matching_fields)
        return random.choice(general_fields)
