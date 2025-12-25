# Alfred API Documentation

## Overview
The Alfred API is built using FastAPI and provides endpoints for chatting with the assistant, managing history, and uploading knowledge.

## Base URL
`http://localhost:8000`

## Endpoints

### 1. Chat with Alfred
**POST** `/chat`

Sends a message to the agent and receives a response.

**Request Body:**
```json
{
  "message": "Hello Alfred, what is the weather?",
  "user_id": "optional_user_id"
}
```

**Response:**
```json
{
  "response": "The weather is..."
}
```

### 2. Get Chat History
**GET** `/history`

Retrieves the conversation history for a user.

**Parameters:**
- `user_id` (query param, optional, default="default_user")

**Response:**
```json
{
    "status": "...",
    "message": "..."
}
```

### 3. Submit Feedback
**POST** `/feedback`

Save user corrections for self-improvement.

**Request Body:**
```json
{
  "user_id": "user123",
  "correction": "My name is spelled 'Pratap', not 'Pratrap'.",
  "original_query": "What is my name?"
}
```

### 4. Upload Knowledge
**POST** `/upload-knowledge`

Upload a file (PDF, Text, Markdown) to be ingested into the Vector Database.

**Form Data:**
- `file`: The file object.

**Response:**
```json
{
  "status": "success",
  "filename": "document.pdf",
  "message": "File uploaded and scheduled for ingestion."
}
```
