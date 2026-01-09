# Alfred - Your Personal Digital Butler

> *"Very good, Sir. I shall attend to it at once."*

**Alfred is an AI-powered personal assistant that actually remembers you.** Unlike ChatGPT or Siri that forget everything between sessions, Alfred keeps track of your projects, habits, relationships, and life—so you don't have to.

---

## Why Alfred?

We all juggle too much. Projects at work. Personal goals. People to follow up with. Things we said we'd do. Important dates we can't forget.

**The problem?** Your brain isn't built to be a database. And current AI assistants are goldfish—helpful in the moment, but they forget you exist the second you close the app.

**Alfred is different.** He's your external brain. Your digital chief of staff. He remembers what you told him last week, nudges you before deadlines, and actually understands the context of your life.

---

## What Can Alfred Do For You?

### Keep Track of Everything

| What You Tell Alfred | What Alfred Remembers |
|---------------------|----------------------|
| "I need to follow up with Priya about the contract" | Who Priya is, which contract, and reminds you in 3 days |
| "The board meeting is next Tuesday" | Alerts you the day before to prep, includes past meeting context |
| "I want to exercise 4x per week" | Tracks your streak, nudges you when you miss a day |
| "I'm working on 3 startups right now" | Keeps separate context for each, switches seamlessly |

### Start Your Day Right

Every morning, Alfred sends you a personalized briefing:

```
Good morning, Sir.

Today's priorities:
• Call with investors at 2 PM (prep notes attached)
• Follow up with Priya - contract pending since last week
• Day 12 of your exercise streak - don't break it!

3 tasks overdue. 2 habits due today.
Shall I walk you through them?
```

### Stay On Top of Your Habits

- **Track any habit** - Exercise, reading, meditation, journaling
- **Maintain streaks** - See your progress, get motivated
- **Gentle nudges** - Alfred reminds you at the right time
- **No judgment** - Missed a day? Alfred helps you get back on track

### Manage Projects Across Roles

Whether you're a founder, employee, freelancer, or all three—Alfred adapts:

- **Track multiple projects** with different contexts
- **Log daily updates** with blockers and wins
- **See health scores** - know which projects need attention
- **Switch contexts** seamlessly between work and personal

### Never Forget a Follow-up

- "Remind me to check in with [person] next week"
- "Follow up on [topic] in 3 days"
- Alfred remembers relationships and past conversations

---

## Connect Your Apps

Alfred becomes more powerful when connected to your digital life:

| Integration | What Alfred Can Do |
|-------------|-------------------|
| **Google Calendar** | Know your schedule, schedule meetings, warn about conflicts |
| **Gmail / Outlook** | Summarize emails, draft responses, remind you to reply |
| **Slack / Teams** | Send messages, summarize channels, stay in the loop |
| **Google Drive / Dropbox** | Find documents, reference past work |
| **Apple Health / Fitbit** | Track sleep, suggest schedule adjustments |
| **Financial Tools** | Bill reminders, spending insights |

*Integrations are added progressively. Start simple, connect more over time.*

---

## How to Hire Alfred

Getting Alfred as your personal assistant takes just a few minutes.

### Option 1: Docker (Recommended)

The fastest way to get Alfred running with all services:

```bash
# Clone Alfred
git clone https://github.com/Vijendrapratap/Personal-Assistant.git
cd Personal-Assistant

# Configure your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start everything with Docker
docker compose up -d

# Alfred is now running at http://localhost:8000
```

That's it! Docker handles PostgreSQL, and everything is configured automatically.

**Want the full setup with Neo4j knowledge graph?**
```bash
docker compose --profile full up -d
```

### Option 2: Manual Setup

If you prefer running without Docker:

```bash
# Clone Alfred
git clone https://github.com/Vijendrapratap/Personal-Assistant.git
cd Personal-Assistant

# Set up Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start Alfred (uses SQLite by default - zero config!)
uvicorn alfred.main:app --reload --host 0.0.0.0 --port 8000
```

### Get the Mobile App

```bash
cd mobile
npm install
npx expo start
```

Scan the QR code with Expo Go on your phone, and you're in.

### Create Your Account

Open the app, sign up, and start talking to Alfred. It's that simple.

---

## What Makes Alfred Different?

| Feature | ChatGPT / Siri / Google | Alfred |
|---------|------------------------|--------|
| **Memory** | Forgets after session | Remembers everything |
| **Proactive** | Waits for you to ask | Sends reminders & briefings |
| **Context** | Generic responses | Knows your projects, people, patterns |
| **Notifications** | None | Morning briefings, timely nudges |
| **Habits** | Can't track | Built-in with streaks |
| **Multi-project** | No understanding | Role-aware context switching |

---

## Alfred Adapts to You

Alfred isn't just for tech workers. He learns YOUR vocabulary and YOUR world.

**For Startup Founders:**
- Track OKRs, runway, investor relationships
- Prepare for board meetings
- Manage across multiple ventures

**For Doctors:**
- Patient follow-up reminders
- Prescription renewal tracking
- Appointment context

**For Lawyers:**
- Case deadline tracking
- Court date management
- Client communication logs

**For Fitness Coaches:**
- Client progress tracking
- Workout plan management
- Session scheduling

**For Anyone:**
- Personal goals and habits
- Relationship maintenance
- Life organization

Alfred learns what matters to YOU.

---

## Your Data, Your Control

- **Self-hosted** - Run Alfred on your own servers
- **Privacy first** - Your data never trains AI models
- **Export anytime** - Download everything you've told Alfred
- **Delete anytime** - Full right to be forgotten

---

## The Vision: Your External Brain

Alfred grows with you:

```
Level 1: "Remind me to call mom tomorrow"
    ↓
Level 2: "Track my habits and keep me accountable"
    ↓
Level 3: "Manage my projects across multiple roles"
    ↓
Level 4: "Understand my whole life context"
    ↓
Level 5: "Be my strategic thinking partner"
```

Start simple. Let Alfred become indispensable.

---

## Technical Overview

For developers who want to understand or contribute:

### Architecture

```
alfred/                     # Python Backend (FastAPI)
├── core/                   # Business logic & personality
├── infrastructure/         # Database, LLM, notifications
├── api/                    # REST endpoints
├── integrations/           # Third-party integrations
└── main.py                 # Application entry

mobile/                     # React Native + Expo Router
├── app/                    # File-based routing
│   ├── (auth)/             # Authentication screens
│   ├── (tabs)/             # Main tab navigation
│   └── settings/           # Settings screens
├── src/
│   ├── screens/            # Screen components
│   ├── components/         # Reusable UI components
│   ├── api/                # API client & services
│   ├── lib/                # Hooks & state management
│   └── theme/              # Design tokens & theming
└── assets/                 # Images & fonts

docs/                       # Technical documentation
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | FastAPI (Python 3.11+) |
| **Database** | PostgreSQL |
| **Knowledge Graph** | Neo4j |
| **Vector Search** | Qdrant |
| **LLM** | OpenAI GPT-4 / Ollama |
| **Mobile** | React Native + Expo |
| **Notifications** | Expo Push |

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- OpenAI API key (or Ollama for local LLM)

### API Documentation

Once running, visit `http://localhost:8000/docs` for the full API reference.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Knowledge Base Setup](docs/KNOWLEDGE_BASE.md) | Vector database and knowledge management |
| [MCP Setup](docs/MCP_SETUP.md) | Model Context Protocol configuration |

---

## Roadmap

- [x] Core conversation interface
- [x] Task and project management
- [x] Habit tracking with streaks
- [x] Push notifications & briefings
- [x] Mobile app (iOS/Android)
- [x] Voice interaction UI
- [x] Calendar view with timeline
- [x] Settings & persona customization
- [x] Connectors framework
- [ ] Email integration
- [ ] Web dashboard
- [ ] Team/multi-user support

---

## Contributing

Contributions welcome! Whether it's bug fixes, new features, or documentation improvements.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <i>"Will there be anything else, Sir?"</i>
</p>
