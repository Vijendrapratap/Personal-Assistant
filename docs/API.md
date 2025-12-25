# Alfred API Documentation

## Overview
The Alfred API is built using FastAPI and provides endpoints for managing projects, tasks, habits, and chatting with the assistant.

## Base URL
`http://localhost:8000`

## Authentication
Most endpoints require a Bearer Token obtained via login/signup.

---

## Auth Endpoints

### 1. User Signup
**POST** `/auth/signup`

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

### 3. Get Profile
**GET** `/auth/profile`

### 4. Update Profile
**PUT** `/auth/profile`

**Request Body:**
```json
{
  "bio": "COO of Codesstellar, Founder of Pratap.ai",
  "work_type": "Operations & Product Management",
  "personality_prompt": "Witty Butler",
  "interaction_type": "formal",
  "morning_briefing_time": "08:00",
  "evening_review_time": "18:00"
}
```

---

## Chat Endpoints

### 5. Chat with Alfred
**POST** `/chat`

**Request Body:**
```json
{
  "message": "What's my status for today?",
  "context": {}
}
```

**Response:**
```json
{
  "response": "Good morning, Sir. You have 5 pending tasks...",
  "metadata": {}
}
```

---

## Project Endpoints

### 6. Create Project
**POST** `/projects`

**Request Body:**
```json
{
  "name": "Muay Thai Tickets",
  "organization": "Codesstellar",
  "role": "pm",
  "description": "Website and app development for client"
}
```

### 7. List Projects
**GET** `/projects?status=active`

### 8. Get Project
**GET** `/projects/{project_id}`

### 9. Update Project
**PUT** `/projects/{project_id}`

**Request Body:**
```json
{
  "status": "on_hold",
  "description": "Updated description"
}
```

### 10. Delete Project
**DELETE** `/projects/{project_id}`

### 11. Add Project Update
**POST** `/projects/{project_id}/updates`

**Request Body:**
```json
{
  "content": "Completed the booking flow today. Blocked on payment gateway.",
  "update_type": "progress",
  "action_items": ["Follow up with payment provider"],
  "blockers": ["Payment gateway integration"]
}
```

### 12. Get Project Updates
**GET** `/projects/{project_id}/updates?limit=20`

### 13. Get Project Tasks
**GET** `/projects/{project_id}/tasks?status=pending`

---

## Task Endpoints

### 14. Create Task
**POST** `/tasks`

**Request Body:**
```json
{
  "title": "Review client proposal",
  "project_id": "uuid-here",
  "description": "Review and send feedback",
  "priority": "high",
  "due_date": "2024-12-26T10:00:00",
  "tags": ["client", "review"]
}
```

### 15. List Tasks
**GET** `/tasks?project_id=xxx&status=pending&priority=high`

### 16. Get Tasks Due Today
**GET** `/tasks/today`

**Response:**
```json
{
  "overdue": [...],
  "due_today": [...],
  "total": 5
}
```

### 17. Get Pending Tasks
**GET** `/tasks/pending`

### 18. Get Task
**GET** `/tasks/{task_id}`

### 19. Update Task
**PUT** `/tasks/{task_id}`

### 20. Complete Task
**POST** `/tasks/{task_id}/complete`

### 21. Start Task
**POST** `/tasks/{task_id}/start`

### 22. Block Task
**POST** `/tasks/{task_id}/block?blocker=Waiting%20for%20client`

### 23. Delete Task
**DELETE** `/tasks/{task_id}`

---

## Habit Endpoints

### 24. Create Habit
**POST** `/habits`

**Request Body:**
```json
{
  "name": "Daily Workout",
  "description": "Strength training or cardio",
  "frequency": "daily",
  "time_preference": "07:00",
  "motivation": "Building discipline and health",
  "category": "fitness"
}
```

### 25. List Habits
**GET** `/habits?active_only=true`

### 26. Get Habits Due Today
**GET** `/habits/today`

**Response:**
```json
{
  "pending": [...],
  "completed": [...],
  "total_streaks": 15
}
```

### 27. Get Streaks
**GET** `/habits/streaks`

### 28. Get Habit
**GET** `/habits/{habit_id}`

### 29. Update Habit
**PUT** `/habits/{habit_id}`

### 30. Log Habit Completion
**POST** `/habits/{habit_id}/log`

**Request Body:**
```json
{
  "logged_date": "2024-12-25",
  "notes": "30 min strength training",
  "duration_minutes": 30
}
```

**Response:**
```json
{
  "message": "Habit logged successfully",
  "current_streak": 5,
  "best_streak": 12,
  "total_completions": 45
}
```

### 31. Get Habit History
**GET** `/habits/{habit_id}/history?start_date=2024-12-01&end_date=2024-12-31`

### 32. Delete Habit
**DELETE** `/habits/{habit_id}`

---

## Dashboard Endpoints

### 33. Get Today's Overview
**GET** `/dashboard/today`

**Response:**
```json
{
  "date": "2024-12-25",
  "greeting": "Good morning",
  "focus": {
    "high_priority_tasks": [...],
    "due_today": [...],
    "overdue": [...]
  },
  "habits": {
    "pending": [...],
    "completed": [...],
    "total_streaks": 15
  },
  "projects": {
    "active_count": 7,
    "needing_attention": [...]
  },
  "stats": {
    "tasks_pending": 12,
    "tasks_overdue": 2,
    "habits_completed_today": 1,
    "habits_pending_today": 2
  }
}
```

### 34. Get Week Overview
**GET** `/dashboard/week`

### 35. Get Project Health
**GET** `/dashboard/project-health`

### 36. Get Stats
**GET** `/dashboard/stats`

### 37. Get Morning Briefing
**GET** `/dashboard/briefing/morning`

### 38. Get Evening Review
**GET** `/dashboard/briefing/evening`

---

## Health Check

### 39. Health
**GET** `/health`

**Response:**
```json
{
  "status": "online",
  "brain": "OpenAIAdapter",
  "storage": "PostgresAdapter"
}
```

---

## Error Responses

All endpoints return standard HTTP error codes:

- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

**Error Response Format:**
```json
{
  "detail": "Error message here"
}
```
