# Curiosity Blocks API Documentation

## Overview

The Curiosity Blocks API is a FastAPI-based backend service that powers the Curiosity Blocks educational topic explorer. It provides endpoints for generating topics, explaining topics in detail, and finding related topics based on user interests and exploration history.

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **API Layer**: FastAPI routes and endpoints
- **Service Layer**: Business logic and core functionality
- **Models**: Pydantic schemas for data validation and serialization
- **Core**: Configuration and application settings

## Key Features

- Topic generation with personalization
- Detailed topic explanations with subtopics
- Related topic exploration
- Web search integration for additional resources
- User interest tracking and learning journey analysis
- Two-phase approach: general (first 3 topics) and personalized (after 3 topics)

## API Endpoints

### Root and Health

- `GET /`: Root endpoint with API information
- `GET /health`: Health check endpoint to verify the API is running

### Topics

- `POST /api/v1/topics/`: Generate interesting topics
- `POST /api/v1/topics/reset`: Reset conversation history

### Explanations

- `POST /api/v1/explanations/`: Generate detailed topic explanations

### Related Topics

- `POST /api/v1/related-topics/`: Find topics related to a given topic

## Request/Response Examples

### Health Check

**Request:**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "api_version": "1.0.0",
  "timestamp": "2025-05-02T12:05:45.123456",
  "dependencies": {
    "openai": "connected",
    "exa_search": "connected"
  }
}
```

### Generate Topics

**Request:**
```json
{
  "user_role": "Student",
  "usage_intent": "Learn about new topics",
  "n_topics": 4
}
```

**Response:**
```json
[
  {
    "topic": "Quantum Computing",
    "description": "The revolutionary field merging quantum physics and computer science"
  },
  {
    "topic": "Biomimicry",
    "description": "How engineers and designers take inspiration from nature's solutions"
  },
  {
    "topic": "Cultural Anthropology",
    "description": "The study of human societies, cultures, and their development"
  },
  {
    "topic": "Renewable Energy",
    "description": "Sustainable power sources that help combat climate change"
  }
]
```

### Explain Topic

**Request:**
```json
{
  "topic": "Quantum Computing",
  "user_role": "Student",
  "usage_intent": "Learn about new topics",
  "sub_topic": "Quantum Entanglement",
  "intent": "curious"
}
```

**Response:**
```json
{
  "main_topic": {
    "title": "Quantum Computing: The Next Frontier",
    "explanation": "Quantum computing is a revolutionary approach to computation that harnesses the principles of quantum mechanics...",
    "image_url": "https://example.com/quantum_computing.jpg",
    "web_resources": "Wikipedia Article: [Quantum Computing](https://en.wikipedia.org/wiki/Quantum_computing)..."
  },
  "subtopics": [
    {
      "title": "Quantum Entanglement",
      "explanation": "Quantum entanglement is a phenomenon where two particles become correlated in such a way that...",
      "web_resources": "YouTube Video: [Quantum Entanglement Explained](https://youtube.com/...)..."
    },
    {
      "title": "Quantum Algorithms",
      "explanation": "Quantum algorithms are designed to run on quantum computers and can solve certain problems...",
      "web_resources": "Educational Resource: [Introduction to Quantum Algorithms](https://...)..."
    }
  ],
  "related_topics": [
    {
      "topic": "Quantum Physics",
      "summary": "The fundamental theory that underlies quantum computing and describes nature at the atomic scale."
    },
    {
      "topic": "Cryptography",
      "summary": "Quantum computing poses both threats and opportunities for modern encryption methods."
    },
    {
      "topic": "Artificial Intelligence",
      "summary": "Quantum computing could revolutionize AI by enabling more complex calculations and simulations."
    }
  ]
}
```

### Explore Related Topics

**Request:**
```json
{
  "topic": "Quantum Computing",
  "user_role": "Student",
  "usage_intent": "Learn about new topics"
}
```

**Response:**
```json
[
  {
    "topic": "Quantum Machine Learning",
    "description": "The intersection of quantum computing and machine learning algorithms"
  },
  {
    "topic": "Post-Quantum Cryptography",
    "description": "Encryption methods designed to withstand attacks from quantum computers"
  },
  {
    "topic": "Quantum Simulation",
    "description": "Using quantum computers to model complex quantum systems"
  }
]
```

## Installation and Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   EXA_API_KEY=your_exa_api_key
   ```
6. Run the application: `uvicorn app.main:app --reload`

## Development

### Project Structure

```
app/
├── api/
│   ├── __init__.py
│   ├── dependencies.py
│   └── routes.py
├── core/
│   ├── __init__.py
│   └── config.py
├── models/
│   ├── __init__.py
│   └── schemas.py
├── services/
│   ├── __init__.py
│   ├── curiosity_service.py
│   ├── explanation_service.py
│   ├── llm_service.py
│   ├── related_topics_service.py
│   └── search_service.py
├── __init__.py
└── main.py
```

### Adding New Features

1. Define new schemas in `app/models/schemas.py`
2. Implement business logic in appropriate service classes
3. Add new routes in `app/api/routes.py`
4. Update dependencies in `app/api/dependencies.py` if needed

## Testing

Run tests using pytest:

```bash
pytest
```

## API Documentation

Interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
