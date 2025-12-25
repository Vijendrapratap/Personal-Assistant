#!/usr/bin/env python3
"""
Seed data script for Pratap's Alfred personal assistant.
This creates his actual projects, sample tasks, and habits.

Usage:
    python scripts/seed_pratap_data.py

Requires:
    - PostgreSQL database running
    - Environment variables set (see .env.example)
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, date
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alfred:alfred_secret@localhost:5432/alfred_db")

# Pratap's user ID (will be created or fetched)
PRATAP_EMAIL = "pratap@codesstellar.com"
PRATAP_USER_ID = None

# ============================================
# PROJECTS DATA
# ============================================

PROJECTS = [
    {
        "name": "Codesstellar Operations",
        "organization": "Codesstellar",
        "role": "coo",
        "status": "active",
        "description": "Overall company operations, team management, client relations, and strategic planning for Codesstellar.",
    },
    {
        "name": "Muay Thai Tickets",
        "organization": "Codesstellar",
        "role": "pm",
        "status": "active",
        "description": "Website and mobile app for Muay Thai event ticket booking and management.",
    },
    {
        "name": "No Excuse",
        "organization": "Codesstellar",
        "role": "pm",
        "status": "active",
        "description": "Fitness and accountability app helping users stay consistent with their workout routines.",
    },
    {
        "name": "PlantOgram",
        "organization": "Codesstellar",
        "role": "pm",
        "status": "active",
        "description": "Plant care and identification app with AI-powered plant health diagnostics.",
    },
    {
        "name": "RSN",
        "organization": "Codesstellar",
        "role": "pm",
        "status": "active",
        "description": "Social networking platform project for Codesstellar client.",
    },
    {
        "name": "Pratap.ai",
        "organization": "Personal",
        "role": "founder",
        "status": "active",
        "description": "Personal brand and AI consulting platform. Building thought leadership in AI/ML space.",
    },
    {
        "name": "Civic Vigilance",
        "organization": "Personal",
        "role": "founder",
        "status": "active",
        "description": "Civic tech platform for community reporting and engagement. Making democracy more accessible.",
    },
]

# ============================================
# TASKS DATA
# ============================================

def get_tasks():
    """Generate tasks with dynamic dates."""
    today = date.today()
    return [
        # Codesstellar Operations tasks
        {
            "title": "Weekly team standup preparation",
            "project_name": "Codesstellar Operations",
            "priority": "high",
            "status": "pending",
            "due_date": today + timedelta(days=1),
            "description": "Prepare agenda for Monday team standup. Review blockers from last week.",
            "tags": ["operations", "team"],
        },
        {
            "title": "Review Q1 financial projections",
            "project_name": "Codesstellar Operations",
            "priority": "high",
            "status": "pending",
            "due_date": today + timedelta(days=3),
            "description": "Go through Q1 numbers with finance team. Prepare summary for founders.",
            "tags": ["finance", "quarterly"],
        },
        {
            "title": "Client onboarding call - New Project",
            "project_name": "Codesstellar Operations",
            "priority": "medium",
            "status": "pending",
            "due_date": today + timedelta(days=2),
            "description": "Initial discovery call with potential client for new web development project.",
            "tags": ["client", "sales"],
        },

        # Muay Thai Tickets tasks
        {
            "title": "Review booking flow UI mockups",
            "project_name": "Muay Thai Tickets",
            "priority": "high",
            "status": "in_progress",
            "due_date": today,
            "description": "Review and approve UI designs for the new booking flow from design team.",
            "tags": ["design", "review"],
        },
        {
            "title": "Test payment gateway integration",
            "project_name": "Muay Thai Tickets",
            "priority": "high",
            "status": "pending",
            "due_date": today + timedelta(days=2),
            "description": "Test end-to-end payment flow with Stripe integration.",
            "tags": ["testing", "payment"],
        },
        {
            "title": "Write API documentation",
            "project_name": "Muay Thai Tickets",
            "priority": "medium",
            "status": "pending",
            "due_date": today + timedelta(days=5),
            "description": "Document all REST API endpoints for mobile team.",
            "tags": ["documentation", "api"],
        },

        # No Excuse tasks
        {
            "title": "Define workout tracking data model",
            "project_name": "No Excuse",
            "priority": "high",
            "status": "pending",
            "due_date": today + timedelta(days=1),
            "description": "Finalize database schema for tracking workouts, sets, reps, and progress.",
            "tags": ["backend", "database"],
        },
        {
            "title": "Research push notification providers",
            "project_name": "No Excuse",
            "priority": "medium",
            "status": "pending",
            "due_date": today + timedelta(days=4),
            "description": "Compare OneSignal, Firebase, and Expo notifications for the app.",
            "tags": ["research", "notifications"],
        },

        # PlantOgram tasks
        {
            "title": "Integrate plant identification API",
            "project_name": "PlantOgram",
            "priority": "high",
            "status": "blocked",
            "due_date": today - timedelta(days=1),  # Overdue
            "description": "Blocked on API key approval from Plant.id service.",
            "tags": ["api", "integration"],
        },
        {
            "title": "Design care schedule notification system",
            "project_name": "PlantOgram",
            "priority": "medium",
            "status": "pending",
            "due_date": today + timedelta(days=3),
            "description": "Design the notification system for plant watering and care reminders.",
            "tags": ["design", "notifications"],
        },

        # Pratap.ai tasks
        {
            "title": "Write blog post on AI agents",
            "project_name": "Pratap.ai",
            "priority": "medium",
            "status": "pending",
            "due_date": today + timedelta(days=7),
            "description": "Write thought leadership piece on the future of AI agents in enterprise.",
            "tags": ["content", "blog"],
        },
        {
            "title": "Update LinkedIn profile with new projects",
            "project_name": "Pratap.ai",
            "priority": "low",
            "status": "pending",
            "due_date": today + timedelta(days=5),
            "description": "Refresh LinkedIn with recent achievements and project highlights.",
            "tags": ["personal-brand", "social"],
        },

        # Civic Vigilance tasks
        {
            "title": "Design community reporting workflow",
            "project_name": "Civic Vigilance",
            "priority": "high",
            "status": "pending",
            "due_date": today + timedelta(days=2),
            "description": "Map out the complete flow from issue reporting to resolution tracking.",
            "tags": ["design", "ux"],
        },
        {
            "title": "Research local government API integrations",
            "project_name": "Civic Vigilance",
            "priority": "medium",
            "status": "pending",
            "due_date": today + timedelta(days=10),
            "description": "Identify available APIs for connecting with municipal systems.",
            "tags": ["research", "integration"],
        },

        # Personal tasks (no project)
        {
            "title": "Book flight for upcoming conference",
            "project_name": None,
            "priority": "medium",
            "status": "pending",
            "due_date": today + timedelta(days=3),
            "description": "Book flights and hotel for tech conference next month.",
            "tags": ["travel", "personal"],
        },
        {
            "title": "Renew gym membership",
            "project_name": None,
            "priority": "low",
            "status": "pending",
            "due_date": today + timedelta(days=7),
            "description": "Annual gym membership renewal due.",
            "tags": ["personal", "health"],
        },
    ]

# ============================================
# HABITS DATA
# ============================================

HABITS = [
    {
        "name": "Daily Workout",
        "description": "Strength training, cardio, or Muay Thai practice",
        "frequency": "daily",
        "time_preference": "07:00",
        "motivation": "Building discipline, strength, and mental clarity. Practicing what I preach for No Excuse app.",
        "category": "fitness",
        "current_streak": 12,
        "best_streak": 30,
        "total_completions": 156,
    },
    {
        "name": "Read 30 minutes",
        "description": "Reading books on business, tech, or personal development",
        "frequency": "daily",
        "time_preference": "21:00",
        "motivation": "Continuous learning and staying sharp in the ever-evolving tech landscape.",
        "category": "learning",
        "current_streak": 5,
        "best_streak": 45,
        "total_completions": 89,
    },
    {
        "name": "Morning Meditation",
        "description": "10 minutes of mindfulness meditation",
        "frequency": "daily",
        "time_preference": "06:30",
        "motivation": "Starting the day with clarity and focus. Managing stress proactively.",
        "category": "mindfulness",
        "current_streak": 8,
        "best_streak": 21,
        "total_completions": 67,
    },
    {
        "name": "Project Updates",
        "description": "Log updates for all active projects",
        "frequency": "weekdays",
        "time_preference": "18:00",
        "motivation": "Maintaining visibility across all projects. Never let anything slip through the cracks.",
        "category": "productivity",
        "current_streak": 3,
        "best_streak": 15,
        "total_completions": 52,
    },
    {
        "name": "Weekly Review",
        "description": "Review accomplishments, set next week priorities",
        "frequency": "weekly",
        "time_preference": "17:00",
        "motivation": "Strategic thinking time. Stepping back to see the big picture.",
        "category": "productivity",
        "current_streak": 2,
        "best_streak": 8,
        "total_completions": 24,
    },
    {
        "name": "Content Creation",
        "description": "Write, record, or create content for personal brand",
        "frequency": "weekdays",
        "time_preference": "20:00",
        "motivation": "Building Pratap.ai thought leadership. Sharing knowledge with the community.",
        "category": "productivity",
        "current_streak": 0,
        "best_streak": 10,
        "total_completions": 35,
    },
]

# ============================================
# PROFILE DATA
# ============================================

PROFILE = {
    "bio": "COO of Codesstellar, Founder of Pratap.ai and Civic Vigilance. Building products that matter. Muay Thai enthusiast.",
    "work_type": "Operations & Product Management",
    "voice_id": "british_butler",
    "personality_prompt": "Professional British butler with wit",
    "interaction_type": "formal",
    "morning_briefing_time": "08:00",
    "evening_review_time": "18:00",
    "proactivity_level": "high",
    "reminder_style": "assertive",
}


def get_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL)


def create_or_get_user(conn):
    """Create Pratap's user account or get existing."""
    global PRATAP_USER_ID

    with conn.cursor() as cur:
        # Check if user exists
        cur.execute("SELECT user_id FROM users WHERE email = %s", (PRATAP_EMAIL,))
        result = cur.fetchone()

        if result:
            PRATAP_USER_ID = result[0]
            print(f"Found existing user: {PRATAP_USER_ID}")

            # Update profile
            cur.execute(
                "UPDATE users SET profile = %s WHERE user_id = %s",
                (Json(PROFILE), PRATAP_USER_ID)
            )
        else:
            # Create new user (password: alfred123)
            import bcrypt
            password_hash = bcrypt.hashpw("alfred123".encode(), bcrypt.gensalt()).decode()
            PRATAP_USER_ID = str(uuid.uuid4())

            cur.execute(
                """
                INSERT INTO users (user_id, email, password_hash, profile, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (PRATAP_USER_ID, PRATAP_EMAIL, password_hash, Json(PROFILE), datetime.now())
            )
            print(f"Created new user: {PRATAP_USER_ID}")

        conn.commit()

    return PRATAP_USER_ID


def seed_projects(conn):
    """Seed projects data."""
    project_ids = {}

    with conn.cursor() as cur:
        for project in PROJECTS:
            project_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO projects (project_id, user_id, name, organization, role, status, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    project_id,
                    PRATAP_USER_ID,
                    project["name"],
                    project["organization"],
                    project["role"],
                    project["status"],
                    project["description"],
                    datetime.now() - timedelta(days=30),  # Created 30 days ago
                    datetime.now(),
                )
            )
            project_ids[project["name"]] = project_id
            print(f"  Created project: {project['name']}")

        conn.commit()

    return project_ids


def seed_tasks(conn, project_ids):
    """Seed tasks data."""
    tasks = get_tasks()

    with conn.cursor() as cur:
        for task in tasks:
            task_id = str(uuid.uuid4())
            project_id = project_ids.get(task["project_name"]) if task["project_name"] else None

            cur.execute(
                """
                INSERT INTO tasks (task_id, user_id, project_id, title, description, priority, status, due_date, tags, source, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    task_id,
                    PRATAP_USER_ID,
                    project_id,
                    task["title"],
                    task.get("description", ""),
                    task["priority"],
                    task["status"],
                    task.get("due_date"),
                    Json(task.get("tags", [])),
                    "user",
                    datetime.now() - timedelta(days=7),
                    datetime.now(),
                )
            )
            print(f"  Created task: {task['title'][:50]}...")

        conn.commit()


def seed_habits(conn):
    """Seed habits data."""
    with conn.cursor() as cur:
        for habit in HABITS:
            habit_id = str(uuid.uuid4())

            # Calculate last_logged based on current streak
            last_logged = None
            if habit["current_streak"] > 0:
                last_logged = date.today() - timedelta(days=1)

            cur.execute(
                """
                INSERT INTO habits (habit_id, user_id, name, description, frequency, time_preference, current_streak, best_streak, total_completions, last_logged, motivation, category, active, reminder_enabled, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    habit_id,
                    PRATAP_USER_ID,
                    habit["name"],
                    habit.get("description", ""),
                    habit["frequency"],
                    habit.get("time_preference"),
                    habit["current_streak"],
                    habit["best_streak"],
                    habit["total_completions"],
                    last_logged,
                    habit.get("motivation", ""),
                    habit.get("category", "productivity"),
                    True,
                    True,
                    datetime.now() - timedelta(days=60),
                )
            )
            print(f"  Created habit: {habit['name']}")

        conn.commit()


def seed_project_updates(conn, project_ids):
    """Add some sample project updates."""
    updates = [
        {
            "project_name": "Muay Thai Tickets",
            "content": "Completed the booking flow UI implementation. Payment gateway integration in progress.",
            "update_type": "progress",
        },
        {
            "project_name": "Muay Thai Tickets",
            "content": "Blocked on Stripe account verification. Need business documents.",
            "update_type": "blocker",
        },
        {
            "project_name": "Codesstellar Operations",
            "content": "Closed two new client deals this week. Team capacity looking good for Q1.",
            "update_type": "progress",
        },
        {
            "project_name": "Civic Vigilance",
            "content": "Initial MVP wireframes approved. Starting backend development next sprint.",
            "update_type": "milestone",
        },
    ]

    with conn.cursor() as cur:
        for i, update in enumerate(updates):
            update_id = str(uuid.uuid4())
            project_id = project_ids.get(update["project_name"])

            if project_id:
                cur.execute(
                    """
                    INSERT INTO project_updates (update_id, project_id, user_id, content, update_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        update_id,
                        project_id,
                        PRATAP_USER_ID,
                        update["content"],
                        update["update_type"],
                        datetime.now() - timedelta(days=len(updates) - i),
                    )
                )
                print(f"  Created update for: {update['project_name']}")

        conn.commit()


def main():
    """Main function to seed all data."""
    print("\n" + "=" * 50)
    print("Alfred Seed Data Script")
    print("=" * 50 + "\n")

    try:
        conn = get_connection()
        print("Connected to database.\n")

        print("[1/5] Creating/updating user...")
        create_or_get_user(conn)

        print("\n[2/5] Seeding projects...")
        project_ids = seed_projects(conn)

        print("\n[3/5] Seeding tasks...")
        seed_tasks(conn, project_ids)

        print("\n[4/5] Seeding habits...")
        seed_habits(conn)

        print("\n[5/5] Seeding project updates...")
        seed_project_updates(conn, project_ids)

        conn.close()

        print("\n" + "=" * 50)
        print("Seed data complete!")
        print("=" * 50)
        print(f"\nLogin credentials:")
        print(f"  Email: {PRATAP_EMAIL}")
        print(f"  Password: alfred123")
        print()

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
