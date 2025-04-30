import streamlit as st
from curiosity_blocks_api import CuriosityBlocksAPI
import json

# Initialize API
api = CuriosityBlocksAPI()

# Initialize session state variables
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = ""
if 'explore_clicked' not in st.session_state:
    st.session_state.explore_clicked = False
if 'generate_topics_clicked' not in st.session_state:
    st.session_state.generate_topics_clicked = False
if 'get_related_clicked' not in st.session_state:
    st.session_state.get_related_clicked = False
if 'generated_topics' not in st.session_state:
    st.session_state.generated_topics = []
if 'related_topics' not in st.session_state:
    st.session_state.related_topics = []
if 'topic_content' not in st.session_state:
    st.session_state.topic_content = None
if 'num_explored' not in st.session_state:
    st.session_state.num_explored = 0

# Callback functions for buttons
def explore_topic_callback():
    st.session_state.explore_clicked = True

def generate_topics_callback():
    st.session_state.generate_topics_clicked = True

def get_related_callback():
    st.session_state.get_related_clicked = True
    # Prevent re-exploration of the main topic
    st.session_state.explore_clicked = False

def explore_specific_topic(topic_name):
    st.session_state.current_topic = topic_name
    st.session_state.sub_topic = ""
    # Do NOT set explore_clicked here; wait for user to click "Explore Topic"

def main():
    st.title("Curiosity Blocks - Educational Topic Explorer")
    
    # Determine phase: general (first 3 topics) or personalized (after 3 topics)
    # Use session state to track number of explored topics for UI logic
    general_phase = st.session_state.num_explored < 3

    # Session state for user profile (after 3 topics)
    if 'user_role' not in st.session_state:
        st.session_state.user_role = ""
    if 'usage_intent' not in st.session_state:
        st.session_state.usage_intent = ""

    st.header("Generate Topics")

    # Personalized phase: show user profile fields
    if not general_phase:
        st.subheader("Tell us about yourself to personalize your experience:")
        st.session_state.user_role = st.selectbox(
            "What do you do?",
            ["", "Student", "Professional", "Parent", "Other"],
            index=0
        )
        st.session_state.usage_intent = st.selectbox(
            "How do you plan to use Curiosity Blocks?",
            [
                "",
                "Learn about new topics",
                "Pick up a new skill",
                "Expand my online reading",
                "Get inspired",
                "Other"
            ],
            index=0
        )

    if st.button("Generate Topics", on_click=generate_topics_callback):
        pass

    # Show personalization summary/confirmation if in personalized phase
    if not general_phase:
        if (
            st.session_state.user_role
            and st.session_state.user_role != ""
            and st.session_state.usage_intent
            and st.session_state.usage_intent != ""
        ):
            st.success(
                f"Personalization active: You are a **{st.session_state.user_role}** and you want to **{st.session_state.usage_intent}** with Curiosity Blocks. "
                "All responses are now tailored to your profile."
            )
        else:
            st.info("Please select both options above to personalize your experience.")

    # Process generate topics request
    if st.session_state.generate_topics_clicked:
        with st.spinner("Generating topics..."):
            if general_phase:
                topics = api.generate_topics()
            else:
                # Require both user_role and usage_intent (not blank)
                if (
                    not st.session_state.user_role
                    or st.session_state.user_role == ""
                    or not st.session_state.usage_intent
                    or st.session_state.usage_intent == ""
                ):
                    st.error("Please select your role and how you plan to use Curiosity Blocks.")
                    topics = []
                else:
                    topics = api.generate_topics(
                        user_role=st.session_state.user_role,
                        usage_intent=st.session_state.usage_intent
                    )
            st.session_state.generated_topics = topics
            st.session_state.generate_topics_clicked = False

    # Display generated topics
    # Robustly display generated topics or a warning if none
    if st.session_state.generated_topics is None or len(st.session_state.generated_topics) == 0:
        st.warning("No topics could be generated. Please try again or adjust your personalization settings.")
    else:
        st.subheader("Suggested Topics")
        for i, topic in enumerate(st.session_state.generated_topics):
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"Explore", key=f"gen_topic_{i}"):
                    # When exploring a new topic, set as current and reset sub_topic, but do NOT trigger search yet
                    explore_specific_topic(topic['topic'])
            with col2:
                st.markdown(f"**{topic['topic']}**: {topic['description']}")

    # Topic exploration section
    st.header("Explore Topic")
    
    # Show previous topics for context if available
    if hasattr(api, 'topic_history') and api.topic_history and len(api.topic_history) > 0:
        st.caption(f"Previously explored: {', '.join(api.topic_history[-3:])}")
    
    topic = st.text_input("Enter a topic to explore", value=st.session_state.current_topic)
    # Sub-topic input area (now used for intent/angle as well)
    if 'sub_topic' not in st.session_state:
        st.session_state.sub_topic = ""
    st.session_state.sub_topic = st.text_input("Optional: Enter a sub-topic to explore within the main topic (or an angle/intention, e.g., 'general', 'psychology', 'history', etc.)", value=st.session_state.sub_topic)

    if st.button("Explore Topic") and topic:
        # Directly update the session state with the manually entered topic
        st.session_state.current_topic = topic
        st.session_state.explore_clicked = True
        # Clear any previous topic content to ensure fresh content is generated
        st.session_state.topic_content = None
        # Store the sub-topic/intent for this exploration
        st.session_state.last_intent = st.session_state.sub_topic
    
    # Process explore topic request
    if st.session_state.explore_clicked and st.session_state.current_topic and not st.session_state.get_related_clicked:
        with st.spinner("Generating explanation..."):
            sub_topic = st.session_state.sub_topic.strip() if 'sub_topic' in st.session_state else ""
            intent = sub_topic  # Use sub-topic as intent/angle
            if general_phase:
                content = api.explain_topic(
                    st.session_state.current_topic,
                    sub_topic=sub_topic if sub_topic else None,
                    intent=intent if intent else None
                )
                # Only increment if successful
                if content and content.get("main_topic"):
                    st.session_state.num_explored += 1
            else:
                if (
                    not st.session_state.user_role
                    or st.session_state.user_role == ""
                    or not st.session_state.usage_intent
                    or st.session_state.usage_intent == ""
                ):
                    st.error("Please select your role and how you plan to use Curiosity Blocks.")
                    content = None
                else:
                    content = api.explain_topic(
                        st.session_state.current_topic,
                        user_role=st.session_state.user_role,
                        usage_intent=st.session_state.usage_intent,
                        sub_topic=sub_topic if sub_topic else None,
                        intent=intent if intent else None
                    )
            st.session_state.topic_content = content
            st.session_state.explore_clicked = False
    
    # Display topic content
    if st.session_state.topic_content:
        content = st.session_state.topic_content
        
        # Show image if available
        image_url = content["main_topic"].get("image_url")
        if image_url:
            try:
                # Validate the image URL before trying to display it
                if isinstance(image_url, str) and (image_url.startswith('http://') or image_url.startswith('https://')):
                    st.image(image_url, caption=content["main_topic"]["title"], use_container_width=True)
                else:
                    print(f"Invalid image URL format: {image_url}")
                    st.text("Image could not be loaded - invalid URL format")
            except Exception as e:
                print(f"Error displaying image: {e}")
                st.text("Image could not be loaded")
        
        # Display main topic title and explanation
        st.subheader(content["main_topic"]["title"])
        st.markdown(content["main_topic"]["explanation"])

        # Display subtopics with web resources
        if content["subtopics"]:
            st.subheader("Subtopics")
            for subtopic in content["subtopics"]:
                st.markdown(f"- **{subtopic['title']}**: {subtopic['explanation']}")
                if subtopic.get("web_resources"):
                    st.markdown(f"  Web Resources: {subtopic['web_resources']}")

        # Display related topics with web resources directly from the main topic content
        if content["related_topics"]:
            st.subheader("Related Topics")
            for i, related in enumerate(content["related_topics"]):
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button(f"Explore", key=f"content_related_{i}"):
                        # When exploring a related topic, reset sub_topic to empty
                        explore_specific_topic(related['topic'])
                with col2:
                    st.markdown(f"**{related['topic']}**: {related['summary']}")
                    # Removed web resources from related topics as requested
        
        # Only show the "Get More Related Topics" button if a topic has been explored
        st.header("Get More Related Topics")
        if st.button("Get More Related Topics", key="more_related_topics", on_click=get_related_callback):
            # This prevents the main topic from being re-explored
            pass
    
    # Process get related topics request - only if a topic has been explored
    if st.session_state.get_related_clicked and st.session_state.current_topic:
        with st.spinner("Finding more related topics..."):
            if general_phase:
                related_topics = api.explore_related_topics(st.session_state.current_topic)
            else:
                if (
                    not st.session_state.user_role
                    or st.session_state.user_role == ""
                    or not st.session_state.usage_intent
                    or st.session_state.usage_intent == ""
                ):
                    st.error("Please select your role and how you plan to use Curiosity Blocks.")
                    related_topics = []
                else:
                    related_topics = api.explore_related_topics(
                        st.session_state.current_topic,
                        user_role=st.session_state.user_role,
                        usage_intent=st.session_state.usage_intent
                    )
            st.session_state.related_topics = related_topics
            st.session_state.get_related_clicked = False
    
    # Display additional related topics only if they exist and a main topic has been explored
    if st.session_state.related_topics and st.session_state.topic_content:
        st.subheader("Additional Related Topics")
        for i, related_topic in enumerate(st.session_state.related_topics):
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"Explore", key=f"related_{i}"):
                    # When exploring an additional related topic, reset sub_topic to empty
                    explore_specific_topic(related_topic['topic'])
            with col2:
                st.markdown(f"**{related_topic['topic']}**: {related_topic['description']}")

    # Reset conversation
    if st.button("Reset Conversation"):
        api.reset_conversation()
        # Clear all session state variables
        st.session_state.current_topic = ""
        st.session_state.explore_clicked = False
        st.session_state.generate_topics_clicked = False
        st.session_state.get_related_clicked = False
        st.session_state.generated_topics = []
        st.session_state.related_topics = []
        st.session_state.topic_content = None
        st.success("Conversation history has been cleared!")

    # Show intent framing note if present and content is valid
    if (
        'last_intent' in st.session_state and st.session_state.last_intent
        and content is not None
        and content.get('main_topic') is not None
        and content['main_topic'].get('title') is not None
    ):
        st.info(f"{content['main_topic']['title']} × {st.session_state.last_intent.title()} Exploration")

if __name__ == "__main__":
    main()
