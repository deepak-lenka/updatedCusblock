# Curiosity Blocks API

A FastAPI-based REST API for exploring educational topics and generating personalized learning content.

## Setup

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
EXA_API_KEY=your_exa_api_key
```

## Running the API

Start the FastAPI server:
```bash
uvicorn fastapi_app:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Generate Topics
```http
POST /generate-topics
```
Generate interesting topics based on user role and intent.

Request body:
```json
{
    "user_role": "Student",
    "usage_intent": "Learn about new topics",
    "n_topics": 4
}
```

### 2. Explore Topic
```http
POST /explore-topic
```
Get detailed explanation and content for a specific topic.

Request body:
```json
{
    "topic": "Quantum Physics",
    "user_role": "Student",
    "usage_intent": "Learn about new topics",
    "sub_topic": "Wave-Particle Duality",
    "intent": "general"
}
```

### 3. Get Related Topics
```http
POST /related-topics
```
Get related topics for a given topic.

Request body:
```json
{
    "topic": "Quantum Physics",
    "user_role": "Student",
    "usage_intent": "Learn about new topics"
}
```

### 4. Reset Conversation
```http
POST /reset
```
Reset the conversation history and topic tracking.

## Example Usage with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Generate topics
response = requests.post(
    f"{BASE_URL}/generate-topics",
    json={
        "user_role": "Student",
        "usage_intent": "Learn about new topics",
        "n_topics": 4
    }
)
topics = response.json()

# Explore a topic
response = requests.post(
    f"{BASE_URL}/explore-topic",
    json={
        "topic": "Quantum Physics",
        "user_role": "Student",
        "usage_intent": "Learn about new topics",
        "sub_topic": "Wave-Particle Duality"
    }
)
content = response.json()

# Get related topics
response = requests.post(
    f"{BASE_URL}/related-topics",
    json={
        "topic": "Quantum Physics",
        "user_role": "Student",
        "usage_intent": "Learn about new topics"
    }
)
related_topics = response.json()
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:
- 200: Successful request
- 400: Bad request (invalid parameters)
- 500: Server error (with error details in response)
