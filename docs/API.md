# Alfred API Documentation

## Overview
The Alfred API is built using FastAPI and provides endpoints for chatting with the assistant, managing history, and uploading knowledge.

## Base URL
`http://localhost:8000`

## Authentication
Most endpoints require a Bearer Token.

### 1. User Signup
**POST** `/auth/signup`

Create a new account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer"
}
```

### 2. User Login
**POST** `/auth/login`

**Request Body** (OAuth2 Form):
- `username`: email
- `password`: password

**Response:**
```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer"
}
```

### 3. Manage Profile
**GET/PUT** `/auth/profile`

Get or Update user profile settings (Bio, Voice, Personality).

**PUT Request Body:**
```json
{
  "bio": "I am a software engineer...",
  "work_type": "Coding",
  "voice_id": "british_butler_1",
  "personality_prompt": "Formal and Witty",
  "interaction_type": "formal"
}
```

## Chat Endpoints

### 4. Chat with Alfred
**POST** `/chat`

Sends a message to the agent. **Requires Auth Token**.

**Request Body:**
```json
{
  "message": "Hello Alfred, what is the weather?"
}
```
