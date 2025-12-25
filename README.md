# Alfred - The Digital Butler

> *"Very good, Sir. I shall attend to it at once."*

Alfred is an **Agentic Personal Assistant** designed to be your proactive digital chief of staff. Unlike passive AI chatbots that wait for instructions, Alfred actively manages your projects, tracks your habits, and keeps you accountable—all while maintaining the demeanor of a professional British butler.

## The Vision

Traditional AI assistants are **reactive**—they respond when prompted but forget everything between sessions. Alfred is different:

- **Proactive**: Sends morning briefings, evening reviews, and timely nudges without being asked
- **Stateful**: Remembers your projects, preferences, and patterns across sessions
- **Context-Aware**: Understands your roles (Founder, COO, PM) and adapts accordingly
- **Personality-Driven**: Maintains a consistent butler persona that can be customized

## What Makes Alfred Different?

| Feature | ChatGPT/Gemini/Claude | Alfred |
|---------|----------------------|--------|
| Memory | Session-based | Persistent knowledge graph |
| Behavior | Passive (waits for input) | Proactive (sends reminders) |
| Context | Generic | Role-aware (knows your projects) |
| Notifications | None | Push notifications & briefings |
| Task Tracking | Conversational only | Integrated task management |
| Habit Tracking | None | Built-in with streaks |

---

## Architecture

Alfred follows **Clean Architecture** principles with clear separation of concerns:

```
alfred/
├── core/                    # Domain Layer (Pure Business Logic)
│   ├── entities.py          # Project, Task, Habit, User models
│   ├── interfaces.py        # Abstract contracts (ports)
│   ├── butler.py            # Core Alfred personality & logic
│   └── proactive_engine.py  # Briefings & scheduled actions
│
├── infrastructure/          # Adapters Layer (External Integrations)
│   ├── llm/                 # LLM providers (OpenAI, Ollama)
│   ├── storage/             # Database adapters (PostgreSQL)
│   ├── knowledge/           # Knowledge graph (Neo4j)
│   └── notifications/       # Push notifications (Expo)
│
├── api/                     # Interface Layer (REST API)
│   ├── auth.py              # Authentication endpoints
│   ├── projects.py          # Project management
│   ├── tasks.py             # Task management
│   ├── habits.py            # Habit tracking
│   ├── dashboard.py         # Aggregated views
│   └── notifications.py     # Push notification management
│
└── main.py                  # FastAPI application entry

mobile/                      # React Native Mobile App
├── src/
│   ├── screens/             # UI screens
│   │   ├── DashboardScreen  # Today's overview
│   │   ├── ProjectsScreen   # Project management
│   │   ├── TasksScreen      # Task management
│   │   ├── HabitsScreen     # Habit tracking
│   │   └── ChatScreen       # Conversation with Alfred
│   ├── api/                 # API client & services
│   └── services/            # Push notifications
└── App.tsx                  # Navigation & app shell
```

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Mobile    │────▶│   FastAPI   │────▶│  PostgreSQL │
│    App      │◀────│   Backend   │◀────│  (Storage)  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  OpenAI  │ │  Neo4j   │ │   Expo   │
        │  (LLM)   │ │ (Graph)  │ │  (Push)  │
        └──────────┘ └──────────┘ └──────────┘
```

---

## Tech Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Language** | Python 3.11+ | Core backend language |
| **API Framework** | FastAPI | REST API with async support |
| **Primary Database** | PostgreSQL | User data, projects, tasks, habits |
| **Knowledge Graph** | Neo4j | Long-term memory & relationships |
| **Vector Database** | Qdrant | Semantic search & context retrieval |
| **LLM Provider** | OpenAI / Ollama | Natural language understanding |
| **Agent Framework** | Agno | Tool use & MCP integration |
| **Push Notifications** | Expo Push | Mobile notifications |

### Mobile App

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | React Native + Expo | Cross-platform mobile |
| **Navigation** | React Navigation | Screen routing & tabs |
| **Chat UI** | Gifted Chat | Conversation interface |
| **HTTP Client** | Axios | API communication |
| **Secure Storage** | Expo SecureStore | JWT token storage |
| **Notifications** | Expo Notifications | Push notification handling |

### DevOps & Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Containerization** | Docker | Consistent environments |
| **Database Hosting** | Self-hosted / Cloud | Your data, your control |
| **API Documentation** | OpenAPI/Swagger | Auto-generated at `/docs` |

---

## Key Features

### 1. Project Management
- Track multiple projects with different roles (Founder, COO, PM, Developer)
- Log daily updates with blockers and action items
- Health score calculation based on activity
- Organization-level grouping

### 2. Task Management
- Priority-based task lists (High, Medium, Low)
- Status workflow (Pending → In Progress → Blocked → Completed)
- Due date tracking with overdue alerts
- Project association for context

### 3. Habit Tracking
- Daily, weekly, or custom frequency habits
- Streak tracking with best streak records
- Category organization (Fitness, Productivity, Learning, etc.)
- Motivation reminders

### 4. Proactive Notifications
- **Morning Briefing**: Today's priorities, pending tasks, habits due
- **Evening Review**: What was accomplished, what's pending
- **Habit Reminders**: Timely nudges to maintain streaks
- **Task Due Alerts**: Before deadlines hit
- **Project Nudges**: When projects need attention

### 5. Knowledge Graph
- Learns facts about you over time
- Understands relationships (people, projects, concepts)
- Provides contextual responses based on history
- Pattern recognition for personalized suggestions

### 6. Butler Personality
- Professional, polite, slightly witty responses
- Customizable interaction style (Formal, Casual, Sarcastic)
- Consistent persona across all interactions
- "Sir/Madam" addressing based on preference

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 14+
- Neo4j 5+ (optional, for knowledge graph)
- Expo Go app (for mobile testing)

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/alfred.git
cd alfred

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings:
#   OPENAI_API_KEY=your_key
#   DATABASE_URL=postgresql://user:pass@localhost:5432/alfred_db
#   NEO4J_URI=bolt://localhost:7687 (optional)

# Run database migrations (tables auto-create on first run)

# Start the server
uvicorn alfred.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Seed Sample Data (Optional)

```bash
# Load Pratap's sample projects, tasks, and habits
python scripts/seed_pratap_data.py

# Login credentials after seeding:
# Email: pratap@codesstellar.com
# Password: alfred123
```

### 3. Mobile App Setup

```bash
cd mobile

# Install dependencies
npm install

# Start Expo development server
npx expo start

# Run on specific platform
npm run android  # Android Emulator
npm run ios      # iOS Simulator (macOS only)
```

**Note**: For Android Emulator, the app uses `10.0.2.2:8000` to reach localhost. For physical devices, update `mobile/src/api/client.ts` with your machine's IP address.

---

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/signup` | POST | Create new account |
| `/auth/login` | POST | Authenticate user |
| `/auth/profile` | GET/PUT | User profile management |
| `/chat` | POST | Converse with Alfred |
| `/projects` | CRUD | Project management |
| `/projects/{id}/updates` | POST/GET | Project updates |
| `/tasks` | CRUD | Task management |
| `/tasks/{id}/complete` | POST | Mark task complete |
| `/habits` | CRUD | Habit management |
| `/habits/{id}/log` | POST | Log habit completion |
| `/dashboard/today` | GET | Today's overview |
| `/dashboard/briefing/morning` | GET | Morning briefing |
| `/notifications/register-token` | POST | Register push token |

Full API documentation available at `http://localhost:8000/docs` when running.

---

## Documentation

- [API Reference](docs/API.md) - Complete endpoint documentation
- [Database Schema](docs/DB_SCHEMA.md) - Table structures and relationships
- [Product Specification](docs/ALFRED_SPECIFICATION.md) - Full product vision
- [MCP Setup](docs/MCP_SETUP.md) - Model Context Protocol integration

---

## Project Structure

```
Personal-Assistant/
├── alfred/                 # Python backend
├── mobile/                 # React Native app
├── scripts/                # Utility scripts
│   └── seed_pratap_data.py # Sample data loader
├── docs/                   # Documentation
├── docker-compose.yml      # Container orchestration
├── requirements.txt        # Python dependencies
└── README.md               # You are here
```

---

## Roadmap

- [ ] Voice interaction (Speech-to-Text, Text-to-Speech)
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Email integration for briefings
- [ ] Web dashboard
- [ ] Multi-user support (teams)
- [ ] Plugin system for custom integrations
- [ ] Apple Watch / Wear OS companion apps

---

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*"Will there be anything else, Sir?"*
