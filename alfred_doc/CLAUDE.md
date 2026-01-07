# CLAUDE.md - Alfred Development Guide

> This file instructs Claude Code (and AI assistants) on how to build and work with the Alfred codebase.

---

## 🎯 Project Overview

**Alfred** is a proactive AI personal assistant that manages tasks, projects, habits, and learns user preferences over time. Unlike reactive chatbots, Alfred initiates conversations through briefings, nudges, and contextual reminders.

### Key Differentiators
- **Proactive**: Alfred reaches out to users, not just responds
- **Memory-Enabled**: Knowledge graph learns entities and relationships
- **Multi-LLM**: Supports Claude, GPT-4, Gemini, Qwen, Ollama, and more
- **Connector-Rich**: 50+ app integrations via MCP protocol
- **Mobile-First**: React Native app with voice support

---

## 📁 Complete Project Structure

```
alfred/
├── .github/                              # GitHub Configuration
│   ├── workflows/
│   │   ├── backend-ci.yml               # Backend lint, test, deploy
│   │   ├── mobile-ci.yml                # Mobile lint, test
│   │   ├── mobile-preview.yml           # EAS preview builds
│   │   ├── mobile-production.yml        # EAS production builds
│   │   └── release.yml                  # Version tagging
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── config.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   └── CODEOWNERS
│
├── alfred/                               # Python Backend (FastAPI)
│   ├── __init__.py
│   ├── main.py                          # FastAPI app entry point
│   │
│   ├── api/                             # REST API Layer
│   │   ├── __init__.py
│   │   ├── deps.py                      # Dependency injection
│   │   ├── router.py                    # Main router
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  # Authentication endpoints
│   │   │   ├── users.py                 # User management
│   │   │   ├── chat.py                  # Conversation endpoints
│   │   │   ├── projects.py              # Project CRUD
│   │   │   ├── tasks.py                 # Task CRUD
│   │   │   ├── habits.py                # Habit tracking
│   │   │   ├── briefings.py             # Morning/evening briefings
│   │   │   ├── notifications.py         # Push notifications
│   │   │   ├── connectors.py            # Connector management
│   │   │   ├── oauth.py                 # OAuth flows
│   │   │   ├── voice.py                 # Voice processing
│   │   │   └── webhooks.py              # Incoming webhooks
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── auth.py                  # JWT middleware
│   │       ├── logging.py               # Request logging
│   │       └── rate_limit.py            # Rate limiting
│   │
│   ├── core/                            # Domain Logic (Clean Architecture)
│   │   ├── __init__.py
│   │   ├── entities.py                  # Domain entities & enums
│   │   ├── interfaces.py                # Abstract interfaces
│   │   ├── exceptions.py                # Custom exceptions
│   │   │
│   │   ├── agents/                      # Agent System
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Base agent class
│   │   │   ├── butler.py                # Main Alfred agent
│   │   │   ├── planner.py               # Task decomposition
│   │   │   ├── executor.py              # Tool execution loop
│   │   │   ├── memory.py                # Memory extraction
│   │   │   └── context.py               # Context building
│   │   │
│   │   ├── tools/                       # Agent Tools
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Tool base class
│   │   │   ├── registry.py              # Tool registry
│   │   │   ├── user.py                  # User context tools
│   │   │   ├── tasks.py                 # Task management tools
│   │   │   ├── projects.py              # Project tools
│   │   │   ├── habits.py                # Habit tools
│   │   │   ├── calendar.py              # Calendar tools
│   │   │   ├── email.py                 # Email tools
│   │   │   ├── notes.py                 # Notes/docs tools
│   │   │   ├── search.py                # Web search tools
│   │   │   └── notifications.py         # Notification tools
│   │   │
│   │   ├── proactive/                   # Proactive Engine
│   │   │   ├── __init__.py
│   │   │   ├── engine.py                # Main proactive engine
│   │   │   ├── triggers.py              # Trigger definitions
│   │   │   ├── evaluator.py             # Trigger evaluation
│   │   │   ├── scheduler.py             # Job scheduling
│   │   │   ├── batcher.py               # Notification batching
│   │   │   └── builder.py               # Notification builder
│   │   │
│   │   └── services/                    # Business Services
│   │       ├── __init__.py
│   │       ├── auth_service.py          # Authentication
│   │       ├── user_service.py          # User management
│   │       ├── project_service.py       # Project logic
│   │       ├── task_service.py          # Task logic
│   │       ├── habit_service.py         # Habit logic
│   │       └── briefing_service.py      # Briefing generation
│   │
│   ├── infrastructure/                   # External Services
│   │   ├── __init__.py
│   │   │
│   │   ├── llm/                         # LLM Providers
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Provider interface
│   │   │   ├── factory.py               # Provider factory
│   │   │   ├── anthropic.py             # Claude API
│   │   │   ├── openai.py                # OpenAI GPT
│   │   │   ├── google.py                # Gemini
│   │   │   ├── groq.py                  # Groq
│   │   │   ├── together.py              # Together AI
│   │   │   ├── ollama.py                # Local Ollama
│   │   │   ├── qwen.py                  # Alibaba Qwen
│   │   │   ├── deepseek.py              # DeepSeek
│   │   │   ├── mistral.py               # Mistral
│   │   │   ├── perplexity.py            # Perplexity (search)
│   │   │   └── cohere.py                # Cohere
│   │   │
│   │   ├── connectors/                  # App Connectors (50+)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Connector interface
│   │   │   ├── registry.py              # Connector registry
│   │   │   ├── oauth_handler.py         # OAuth flow handler
│   │   │   │
│   │   │   ├── communication/           # Email & Messaging
│   │   │   │   ├── gmail.py
│   │   │   │   ├── outlook.py
│   │   │   │   ├── slack.py
│   │   │   │   ├── discord.py
│   │   │   │   ├── teams.py
│   │   │   │   ├── telegram.py
│   │   │   │   └── whatsapp.py
│   │   │   │
│   │   │   ├── calendar/                # Calendar & Scheduling
│   │   │   │   ├── google_calendar.py
│   │   │   │   ├── outlook_calendar.py
│   │   │   │   ├── calendly.py
│   │   │   │   ├── cal_com.py
│   │   │   │   ├── zoom.py
│   │   │   │   └── google_meet.py
│   │   │   │
│   │   │   ├── productivity/            # Task & Project Management
│   │   │   │   ├── notion.py
│   │   │   │   ├── trello.py
│   │   │   │   ├── asana.py
│   │   │   │   ├── linear.py
│   │   │   │   ├── jira.py
│   │   │   │   ├── monday.py
│   │   │   │   ├── clickup.py
│   │   │   │   ├── todoist.py
│   │   │   │   ├── things.py
│   │   │   │   └── basecamp.py
│   │   │   │
│   │   │   ├── notes/                   # Notes & Documentation
│   │   │   │   ├── notion_docs.py
│   │   │   │   ├── obsidian.py
│   │   │   │   ├── roam.py
│   │   │   │   ├── evernote.py
│   │   │   │   ├── google_docs.py
│   │   │   │   ├── confluence.py
│   │   │   │   └── coda.py
│   │   │   │
│   │   │   ├── storage/                 # Cloud Storage
│   │   │   │   ├── google_drive.py
│   │   │   │   ├── dropbox.py
│   │   │   │   ├── onedrive.py
│   │   │   │   └── box.py
│   │   │   │
│   │   │   ├── development/             # Dev & Code
│   │   │   │   ├── github.py
│   │   │   │   ├── gitlab.py
│   │   │   │   ├── bitbucket.py
│   │   │   │   ├── vercel.py
│   │   │   │   ├── netlify.py
│   │   │   │   ├── railway.py
│   │   │   │   ├── supabase.py
│   │   │   │   └── firebase.py
│   │   │   │
│   │   │   ├── finance/                 # Finance & Payments
│   │   │   │   ├── stripe.py
│   │   │   │   ├── paypal.py
│   │   │   │   ├── quickbooks.py
│   │   │   │   ├── xero.py
│   │   │   │   └── wise.py
│   │   │   │
│   │   │   ├── analytics/               # Analytics & Data
│   │   │   │   ├── google_analytics.py
│   │   │   │   ├── mixpanel.py
│   │   │   │   ├── amplitude.py
│   │   │   │   ├── airtable.py
│   │   │   │   └── google_sheets.py
│   │   │   │
│   │   │   ├── crm/                     # CRM & E-commerce
│   │   │   │   ├── hubspot.py
│   │   │   │   ├── salesforce.py
│   │   │   │   ├── pipedrive.py
│   │   │   │   ├── intercom.py
│   │   │   │   ├── zendesk.py
│   │   │   │   └── shopify.py
│   │   │   │
│   │   │   ├── design/                  # Design & Creative
│   │   │   │   ├── figma.py
│   │   │   │   ├── canva.py
│   │   │   │   └── miro.py
│   │   │   │
│   │   │   ├── social/                  # Social Media
│   │   │   │   ├── twitter.py
│   │   │   │   ├── linkedin.py
│   │   │   │   ├── instagram.py
│   │   │   │   ├── youtube.py
│   │   │   │   └── buffer.py
│   │   │   │
│   │   │   ├── voice/                   # Voice & Audio
│   │   │   │   ├── elevenlabs.py
│   │   │   │   ├── whisper.py
│   │   │   │   ├── assemblyai.py
│   │   │   │   └── deepgram.py
│   │   │   │
│   │   │   ├── automation/              # Automation & Webhooks
│   │   │   │   ├── zapier.py
│   │   │   │   ├── make.py
│   │   │   │   └── webhooks.py
│   │   │   │
│   │   │   ├── browser/                 # Browser & Web
│   │   │   │   ├── browserless.py
│   │   │   │   └── brave_search.py
│   │   │   │
│   │   │   └── smarthome/               # Smart Home
│   │   │       ├── homeassistant.py
│   │   │       └── hue.py
│   │   │
│   │   ├── storage/                     # Database Adapters
│   │   │   ├── __init__.py
│   │   │   ├── postgres.py              # PostgreSQL
│   │   │   ├── redis_cache.py           # Redis cache
│   │   │   └── migrations/              # Alembic migrations
│   │   │
│   │   ├── knowledge/                   # Knowledge Stores
│   │   │   ├── __init__.py
│   │   │   ├── neo4j.py                 # Knowledge graph
│   │   │   └── qdrant.py                # Vector search
│   │   │
│   │   └── notifications/               # Push Notifications
│   │       ├── __init__.py
│   │       ├── expo.py                  # Expo push
│   │       ├── apns.py                  # Apple Push
│   │       └── fcm.py                   # Firebase Cloud
│   │
│   └── config/                          # Configuration
│       ├── __init__.py
│       ├── settings.py                  # Pydantic settings
│       ├── logging.py                   # Logging config
│       └── prompts/                     # System Prompts
│           ├── __init__.py
│           ├── butler.py                # Main agent prompt
│           ├── planner.py               # Planning prompt
│           ├── memory.py                # Memory extraction
│           └── briefing.py              # Briefing generation
│
├── mobile/                              # React Native + Expo
│   ├── app/                             # Expo Router (file-based)
│   │   ├── _layout.tsx                  # Root layout
│   │   ├── index.tsx                    # Redirect to tabs
│   │   ├── (auth)/                      # Auth group
│   │   │   ├── _layout.tsx
│   │   │   ├── login.tsx
│   │   │   ├── register.tsx
│   │   │   └── forgot-password.tsx
│   │   ├── (tabs)/                      # Main tab navigator
│   │   │   ├── _layout.tsx
│   │   │   ├── index.tsx                # Today screen
│   │   │   ├── do.tsx                   # Tasks + Habits
│   │   │   ├── focus.tsx                # Calendar + Voice
│   │   │   └── you.tsx                  # Profile + Settings
│   │   ├── chat/
│   │   │   ├── _layout.tsx
│   │   │   └── [conversationId].tsx     # Chat screen
│   │   ├── project/
│   │   │   └── [projectId].tsx          # Project detail
│   │   ├── connectors/
│   │   │   ├── index.tsx                # Connector list
│   │   │   └── [connectorId].tsx        # Setup flow
│   │   └── settings/
│   │       ├── index.tsx
│   │       ├── profile.tsx
│   │       ├── preferences.tsx
│   │       ├── notifications.tsx
│   │       └── about.tsx
│   │
│   ├── src/
│   │   ├── components/                  # UI Components
│   │   │   ├── ui/                      # Base components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Badge.tsx
│   │   │   │   ├── Avatar.tsx
│   │   │   │   └── index.ts
│   │   │   ├── alfred/                  # Alfred-specific
│   │   │   │   ├── AlfredGreeting.tsx
│   │   │   │   ├── ProactiveCard.tsx
│   │   │   │   ├── FocusBlock.tsx
│   │   │   │   ├── BriefingView.tsx
│   │   │   │   └── AlfredMind.tsx       # Transparency panel
│   │   │   ├── tasks/
│   │   │   │   ├── TaskCard.tsx
│   │   │   │   ├── TaskList.tsx
│   │   │   │   └── TaskForm.tsx
│   │   │   ├── habits/
│   │   │   │   ├── HabitCard.tsx
│   │   │   │   ├── HabitStreak.tsx
│   │   │   │   └── HabitGrid.tsx
│   │   │   ├── projects/
│   │   │   │   ├── ProjectCard.tsx
│   │   │   │   └── ProjectList.tsx
│   │   │   ├── chat/
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   └── VoiceButton.tsx
│   │   │   └── connectors/
│   │   │       ├── ConnectorCard.tsx
│   │   │       └── ConnectorSetup.tsx
│   │   │
│   │   ├── hooks/                       # Custom Hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useBriefing.ts
│   │   │   ├── useTasks.ts
│   │   │   ├── useHabits.ts
│   │   │   ├── useProjects.ts
│   │   │   ├── useChat.ts
│   │   │   ├── useVoiceInput.ts
│   │   │   ├── useSpeech.ts
│   │   │   ├── useNotifications.ts
│   │   │   ├── useConnectors.ts
│   │   │   └── useNetworkStatus.ts
│   │   │
│   │   ├── stores/                      # Zustand Stores
│   │   │   ├── index.ts
│   │   │   ├── authStore.ts
│   │   │   ├── userStore.ts
│   │   │   ├── tasksStore.ts
│   │   │   ├── habitsStore.ts
│   │   │   ├── projectsStore.ts
│   │   │   ├── chatStore.ts
│   │   │   └── connectorsStore.ts
│   │   │
│   │   ├── api/                         # API Client
│   │   │   ├── client.ts                # Axios instance
│   │   │   ├── auth.ts                  # Auth endpoints
│   │   │   ├── briefings.ts             # Briefing endpoints
│   │   │   ├── tasks.ts                 # Task endpoints
│   │   │   ├── habits.ts                # Habit endpoints
│   │   │   ├── projects.ts              # Project endpoints
│   │   │   ├── chat.ts                  # Chat endpoints
│   │   │   ├── connectors.ts            # Connector endpoints
│   │   │   └── queryClient.ts           # React Query setup
│   │   │
│   │   ├── services/                    # Device Services
│   │   │   ├── notifications.ts         # Push notification handling
│   │   │   ├── storage.ts               # Secure storage
│   │   │   ├── offline.ts               # Offline queue
│   │   │   └── analytics.ts             # Event tracking
│   │   │
│   │   ├── utils/                       # Utilities
│   │   │   ├── date.ts
│   │   │   ├── format.ts
│   │   │   └── validation.ts
│   │   │
│   │   ├── constants/                   # App Constants
│   │   │   ├── colors.ts
│   │   │   ├── spacing.ts
│   │   │   └── config.ts
│   │   │
│   │   └── types/                       # TypeScript Types
│   │       ├── api.ts
│   │       ├── entities.ts
│   │       └── navigation.ts
│   │
│   ├── assets/                          # Static Assets
│   │   ├── images/
│   │   │   ├── icon.png
│   │   │   ├── splash.png
│   │   │   ├── adaptive-icon.png
│   │   │   └── favicon.png
│   │   └── fonts/
│   │
│   ├── app.json                         # Expo config
│   ├── eas.json                         # EAS Build config
│   ├── metro.config.js                  # Metro bundler
│   ├── babel.config.js                  # Babel config
│   ├── tailwind.config.js               # NativeWind/Tailwind
│   ├── tsconfig.json                    # TypeScript config
│   ├── package.json
│   └── .env.example
│
├── tests/                               # Test Suites
│   ├── unit/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── services/
│   │   └── connectors/
│   ├── integration/
│   │   ├── api/
│   │   └── connectors/
│   ├── e2e/
│   │   └── mobile/
│   ├── fixtures/
│   │   ├── users.json
│   │   ├── tasks.json
│   │   └── conversations.json
│   ├── conftest.py                      # Pytest fixtures
│   └── pytest.ini
│
├── docs/                                # Documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── CONNECTORS.md
│   ├── MOBILE_SETUP.md
│   ├── DEPLOYMENT.md
│   └── CONTRIBUTING.md
│
├── scripts/                             # Utility Scripts
│   ├── seed_data.py                     # Seed database
│   ├── create_migration.py              # Alembic helper
│   └── setup_dev.sh                     # Dev environment setup
│
├── docker-compose.yml                   # Local services
├── docker-compose.prod.yml              # Production services
├── Dockerfile                           # Backend container
├── Dockerfile.worker                    # Celery worker container
│
├── .env.example                         # Environment template
├── .gitignore
├── .pre-commit-config.yaml              # Pre-commit hooks
├── pyproject.toml                       # Python project config
├── requirements.txt                     # Python dependencies
├── requirements-dev.txt                 # Dev dependencies
│
├── CLAUDE.md                            # This file
├── README.md                            # Project readme
├── LICENSE                              # MIT License
└── CONTRIBUTING.md                      # Contribution guide
```

---

## 🔧 Development Commands

### Backend

```bash
# Initial setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Database
createdb alfred_db
alembic upgrade head
python scripts/seed_data.py  # Optional

# Run development server
uvicorn alfred.main:app --reload --port 8000

# Run Celery worker (separate terminal)
celery -A alfred.worker worker --loglevel=info

# Run tests
pytest tests/ -v --cov=alfred
pytest tests/unit/ -v  # Unit only
pytest tests/integration/ -v  # Integration only

# Code quality
black alfred/
isort alfred/
mypy alfred/
flake8 alfred/

# Pre-commit (run all checks)
pre-commit run --all-files
```

### Mobile

```bash
cd mobile

# Install dependencies
npm install

# Start development
npx expo start                  # Start Expo dev server
npx expo start --ios            # Start with iOS
npx expo start --android        # Start with Android
npx expo start --web            # Start with web

# Run on devices/simulators
npx expo run:ios                # Build and run iOS
npx expo run:android            # Build and run Android

# Linting and formatting
npm run lint                    # ESLint
npm run lint:fix                # Fix lint issues
npm run format                  # Prettier

# Testing
npm test                        # Jest tests
npm run test:watch              # Watch mode
npm run test:coverage           # With coverage

# EAS Build (cloud builds)
npx eas build --platform ios --profile preview
npx eas build --platform android --profile preview
npx eas build --platform all --profile production

# EAS Submit (app store)
npx eas submit --platform ios
npx eas submit --platform android
```

### Docker

```bash
# Development environment
docker-compose up -d                    # Start all services
docker-compose logs -f alfred-api       # View API logs
docker-compose exec alfred-api bash     # Shell into container
docker-compose down                     # Stop services

# Rebuild after changes
docker-compose build alfred-api
docker-compose up -d alfred-api

# Production
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🚀 CI/CD Pipeline Setup

### GitHub Actions Workflows

#### Backend CI (`backend-ci.yml`)

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'alfred/**'
      - 'tests/**'
      - 'requirements*.txt'
      - '.github/workflows/backend-ci.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'alfred/**'
      - 'tests/**'

env:
  PYTHON_VERSION: '3.11'

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run Black
        run: black --check alfred/
      
      - name: Run isort
        run: isort --check-only alfred/
      
      - name: Run flake8
        run: flake8 alfred/
      
      - name: Run mypy
        run: mypy alfred/

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: alfred_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/alfred_test
          REDIS_URL: redis://localhost:6379
          SECRET_KEY: test-secret-key
        run: |
          pytest tests/ -v --cov=alfred --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: alfred-api
```

#### Mobile CI (`mobile-ci.yml`)

```yaml
# .github/workflows/mobile-ci.yml
name: Mobile CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'mobile/**'
      - '.github/workflows/mobile-ci.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'mobile/**'

defaults:
  run:
    working-directory: mobile

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run ESLint
        run: npm run lint
      
      - name: Run TypeScript
        run: npx tsc --noEmit

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          directory: mobile/coverage
```

#### Mobile Preview Builds (`mobile-preview.yml`)

```yaml
# .github/workflows/mobile-preview.yml
name: Mobile Preview Build

on:
  pull_request:
    branches: [main]
    paths:
      - 'mobile/**'
  workflow_dispatch:

defaults:
  run:
    working-directory: mobile

jobs:
  build:
    name: EAS Preview Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json
      
      - name: Setup Expo
        uses: expo/expo-github-action@v8
        with:
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build iOS Preview
        run: eas build --platform ios --profile preview --non-interactive
      
      - name: Build Android Preview
        run: eas build --platform android --profile preview --non-interactive
```

#### Mobile Production (`mobile-production.yml`)

```yaml
# .github/workflows/mobile-production.yml
name: Mobile Production Build & Submit

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

defaults:
  run:
    working-directory: mobile

jobs:
  build-and-submit:
    name: Production Build & Submit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json
      
      - name: Setup Expo
        uses: expo/expo-github-action@v8
        with:
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build iOS
        run: eas build --platform ios --profile production --non-interactive
      
      - name: Submit to App Store
        run: eas submit --platform ios --latest --non-interactive
      
      - name: Build Android
        run: eas build --platform android --profile production --non-interactive
      
      - name: Submit to Play Store
        run: eas submit --platform android --latest --non-interactive
```

---

## 📱 Complete Mobile Setup

### package.json

```json
{
  "name": "alfred-mobile",
  "version": "1.0.0",
  "main": "expo-router/entry",
  "scripts": {
    "start": "expo start",
    "android": "expo run:android",
    "ios": "expo run:ios",
    "web": "expo start --web",
    "lint": "eslint . --ext .ts,.tsx",
    "lint:fix": "eslint . --ext .ts,.tsx --fix",
    "format": "prettier --write \"**/*.{ts,tsx,json}\"",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "expo": "~50.0.0",
    "expo-router": "~3.4.0",
    "expo-status-bar": "~1.11.0",
    "expo-splash-screen": "~0.26.0",
    "expo-font": "~11.10.0",
    "expo-linking": "~6.2.0",
    "expo-constants": "~15.4.0",
    "expo-device": "~5.9.0",
    "expo-notifications": "~0.27.0",
    "expo-secure-store": "~12.8.0",
    "expo-speech": "~11.7.0",
    "expo-haptics": "~12.8.0",
    "expo-image": "~1.10.0",
    "expo-linear-gradient": "~12.7.0",
    "expo-blur": "~12.9.0",
    "expo-web-browser": "~12.8.0",
    "expo-auth-session": "~5.4.0",
    "expo-crypto": "~12.8.0",
    
    "react": "18.2.0",
    "react-native": "0.73.0",
    "react-native-reanimated": "~3.6.0",
    "react-native-gesture-handler": "~2.14.0",
    "react-native-safe-area-context": "4.8.2",
    "react-native-screens": "~3.29.0",
    "react-native-svg": "14.1.0",
    
    "@react-native-voice/voice": "^3.2.4",
    "react-native-gifted-chat": "^2.4.0",
    "react-native-mmkv": "^2.11.0",
    "react-native-keyboard-aware-scroll-view": "^0.9.5",
    
    "@tanstack/react-query": "^5.28.0",
    "zustand": "^4.5.0",
    "axios": "^1.6.0",
    "date-fns": "^3.3.0",
    "zod": "^3.22.0",
    
    "nativewind": "^2.0.11",
    "tailwindcss": "^3.4.0",
    
    "lucide-react-native": "^0.344.0"
  },
  "devDependencies": {
    "@babel/core": "^7.20.0",
    "@types/react": "~18.2.45",
    "@types/react-native": "~0.73.0",
    "typescript": "^5.3.0",
    
    "eslint": "^8.57.0",
    "eslint-config-expo": "~7.0.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    
    "prettier": "^3.2.0",
    
    "jest": "^29.7.0",
    "jest-expo": "~50.0.0",
    "@testing-library/react-native": "^12.4.0",
    "@testing-library/jest-native": "^5.4.0"
  },
  "private": true
}
```

### app.json

```json
{
  "expo": {
    "name": "Alfred",
    "slug": "alfred",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/images/icon.png",
    "scheme": "alfred",
    "userInterfaceStyle": "automatic",
    "splash": {
      "image": "./assets/images/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#1a1a2e"
    },
    "assetBundlePatterns": ["**/*"],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.yourcompany.alfred",
      "buildNumber": "1",
      "infoPlist": {
        "NSMicrophoneUsageDescription": "Alfred needs microphone access for voice commands",
        "NSSpeechRecognitionUsageDescription": "Alfred needs speech recognition for voice input",
        "UIBackgroundModes": ["remote-notification", "fetch"]
      }
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/images/adaptive-icon.png",
        "backgroundColor": "#1a1a2e"
      },
      "package": "com.yourcompany.alfred",
      "versionCode": 1,
      "permissions": [
        "RECORD_AUDIO",
        "RECEIVE_BOOT_COMPLETED",
        "VIBRATE"
      ],
      "googleServicesFile": "./google-services.json"
    },
    "web": {
      "bundler": "metro",
      "output": "static",
      "favicon": "./assets/images/favicon.png"
    },
    "plugins": [
      "expo-router",
      "expo-secure-store",
      [
        "expo-notifications",
        {
          "icon": "./assets/images/notification-icon.png",
          "color": "#4f46e5"
        }
      ],
      [
        "expo-speech",
        {
          "microphonePermission": "Allow Alfred to use the microphone for voice commands."
        }
      ],
      [
        "@react-native-voice/voice",
        {
          "microphonePermission": "Allow Alfred to access the microphone for voice input.",
          "speechRecognitionPermission": "Allow Alfred to use speech recognition."
        }
      ]
    ],
    "experiments": {
      "typedRoutes": true
    },
    "extra": {
      "router": {
        "origin": false
      },
      "eas": {
        "projectId": "your-project-id"
      }
    }
  }
}
```

### eas.json

```json
{
  "cli": {
    "version": ">= 7.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "simulator": true
      },
      "android": {
        "buildType": "apk"
      }
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "simulator": false
      },
      "android": {
        "buildType": "apk"
      },
      "env": {
        "APP_ENV": "preview",
        "API_URL": "https://alfred-api-preview.railway.app"
      }
    },
    "production": {
      "distribution": "store",
      "ios": {
        "resourceClass": "m-medium"
      },
      "android": {
        "buildType": "app-bundle"
      },
      "env": {
        "APP_ENV": "production",
        "API_URL": "https://api.alfred.app"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "your-apple-id@email.com",
        "ascAppId": "your-app-store-connect-app-id",
        "appleTeamId": "YOUR_TEAM_ID"
      },
      "android": {
        "serviceAccountKeyPath": "./play-store-key.json",
        "track": "internal"
      }
    }
  }
}
```

### tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        dark: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        alfred: {
          bg: '#1a1a2e',
          card: '#16213e',
          accent: '#4f46e5',
          text: '#e2e8f0',
          muted: '#94a3b8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
```

### tsconfig.json

```json
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@hooks/*": ["./src/hooks/*"],
      "@stores/*": ["./src/stores/*"],
      "@api/*": ["./src/api/*"],
      "@utils/*": ["./src/utils/*"],
      "@constants/*": ["./src/constants/*"],
      "@types/*": ["./src/types/*"]
    }
  },
  "include": [
    "**/*.ts",
    "**/*.tsx",
    ".expo/types/**/*.ts",
    "expo-env.d.ts"
  ]
}
```

---

## 🏗️ Architecture Patterns

### Clean Architecture (Backend)

```
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER                                 │
│  FastAPI routes, request/response models, authentication        │
│  NO business logic - only HTTP handling                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CORE LAYER                                 │
│  Business logic, entities, interfaces (contracts)               │
│  PURE PYTHON - no external dependencies                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                           │
│  External service adapters (database, LLM, connectors)          │
│  IMPLEMENTS interfaces from core layer                          │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Architecture (Manus-Inspired)

```python
# alfred/core/agents/executor.py

class AgentExecutor:
    """
    Main agent loop following Manus's CodeAct paradigm:
    1. Analyze - Understand context and intent
    2. Plan - Decompose into steps if complex
    3. Execute - Run tools one at a time
    4. Observe - Check results
    5. Repeat until done
    """
    
    async def run(
        self, 
        user_input: str, 
        context: AgentContext
    ) -> AgentResult:
        iterations = 0
        max_iterations = 10
        
        while iterations < max_iterations:
            # Build prompt with history, memory, knowledge
            prompt_context = await self.build_context(user_input, context)
            
            # Get LLM decision
            decision = await self.llm.complete(
                messages=prompt_context.messages,
                tools=self.get_available_tools(context),
            )
            
            if decision.tool_calls:
                # Execute tool
                for tool_call in decision.tool_calls:
                    result = await self.execute_tool(
                        tool_call.name, 
                        tool_call.arguments
                    )
                    context.add_observation(tool_call.name, result)
                
                iterations += 1
            else:
                # Final response - extract learnings and return
                await self.memory.extract_learnings(context)
                return AgentResult(
                    response=decision.content,
                    tool_calls_made=iterations
                )
        
        return AgentResult(
            response="I couldn't complete this task within the limit.",
            tool_calls_made=iterations
        )
```

### LLM Provider Interface

```python
# alfred/infrastructure/llm/base.py

from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator
from pydantic import BaseModel

class LLMMessage(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: Optional[str] = None

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict  # JSON Schema

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict

class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    usage: dict

class LLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier"""
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate completion from messages"""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
    ) -> AsyncIterator[str]:
        """Stream completion tokens"""
        pass
```

### Connector Interface

```python
# alfred/infrastructure/connectors/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from enum import Enum

class ConnectorCategory(str, Enum):
    COMMUNICATION = "communication"
    CALENDAR = "calendar"
    PRODUCTIVITY = "productivity"
    NOTES = "notes"
    STORAGE = "storage"
    DEVELOPMENT = "development"
    FINANCE = "finance"
    ANALYTICS = "analytics"
    CRM = "crm"
    DESIGN = "design"
    SOCIAL = "social"
    VOICE = "voice"
    AUTOMATION = "automation"
    BROWSER = "browser"
    SMARTHOME = "smarthome"

class ConnectorAction(BaseModel):
    name: str
    description: str
    parameters: dict  # JSON Schema
    requires_auth: bool = True

class ConnectorConfig(BaseModel):
    name: str
    display_name: str
    description: str
    icon: str  # Emoji or URL
    category: ConnectorCategory
    auth_type: str  # "oauth2", "api_key", "none"
    oauth_scopes: Optional[List[str]] = None

class MCPConnector(ABC):
    """Base class for all MCP connectors"""
    
    config: ConnectorConfig
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the external service"""
        pass
    
    @abstractmethod
    async def refresh_token(self) -> Optional[Dict[str, Any]]:
        """Refresh OAuth token if needed"""
        pass
    
    @abstractmethod
    def get_actions(self) -> List[ConnectorAction]:
        """Return available actions with their schemas"""
        pass
    
    @abstractmethod
    async def execute(
        self, 
        action: str, 
        params: Dict[str, Any]
    ) -> Any:
        """Execute a connector action"""
        pass
    
    def as_tools(self) -> List[ToolDefinition]:
        """Convert connector actions to LLM tools"""
        return [
            ToolDefinition(
                name=f"{self.config.name}_{action.name}",
                description=f"[{self.config.display_name}] {action.description}",
                parameters=action.parameters
            )
            for action in self.get_actions()
        ]
```

---

## 📝 Implementation Guidelines

### When Adding a New LLM Provider

1. Create adapter in `alfred/infrastructure/llm/`
2. Implement `LLMProvider` interface
3. Add to factory in `alfred/infrastructure/llm/factory.py`
4. Add environment variables to `.env.example`
5. Update `alfred/config/settings.py`
6. Write tests in `tests/unit/llm/`

```python
# Example: alfred/infrastructure/llm/anthropic.py

from anthropic import AsyncAnthropic
from alfred.infrastructure.llm.base import (
    LLMProvider, LLMMessage, LLMResponse, ToolDefinition, ToolCall
)

class AnthropicProvider(LLMProvider):
    def __init__(
        self, 
        api_key: str, 
        model: str = "claude-sonnet-4-20250514"
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
    
    @property
    def model_name(self) -> str:
        return self.model
    
    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        # Convert to Anthropic format
        anthropic_messages = self._convert_messages(messages)
        anthropic_tools = self._convert_tools(tools) if tools else None
        
        response = await self.client.messages.create(
            model=self.model,
            messages=anthropic_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=anthropic_tools,
        )
        
        return self._parse_response(response)
```

### When Adding a New Connector

1. Determine category from `ConnectorCategory`
2. Create connector in appropriate subfolder
3. Implement `MCPConnector` interface
4. Register in `alfred/infrastructure/connectors/registry.py`
5. Add OAuth routes if needed in `alfred/api/routes/oauth.py`
6. Write tests in `tests/unit/connectors/`

```python
# Example: alfred/infrastructure/connectors/productivity/notion.py

from alfred.infrastructure.connectors.base import (
    MCPConnector, ConnectorConfig, ConnectorCategory, ConnectorAction
)

class NotionConnector(MCPConnector):
    config = ConnectorConfig(
        name="notion",
        display_name="Notion",
        description="Access and manage Notion pages and databases",
        icon="📝",
        category=ConnectorCategory.PRODUCTIVITY,
        auth_type="oauth2",
        oauth_scopes=["read_content", "update_content", "insert_content"]
    )
    
    def get_actions(self) -> List[ConnectorAction]:
        return [
            ConnectorAction(
                name="search_pages",
                description="Search for pages in Notion",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["query"]
                }
            ),
            ConnectorAction(
                name="get_page",
                description="Get a Notion page by ID",
                parameters={
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string"}
                    },
                    "required": ["page_id"]
                }
            ),
            # ... more actions
        ]
    
    async def execute(self, action: str, params: Dict[str, Any]) -> Any:
        if action == "search_pages":
            return await self._search_pages(params["query"], params.get("limit", 10))
        elif action == "get_page":
            return await self._get_page(params["page_id"])
        # ... handle other actions
```

### When Adding a New Mobile Screen

1. Create screen in `mobile/app/` following Expo Router conventions
2. Create necessary components in `mobile/src/components/`
3. Add API calls in `mobile/src/api/`
4. Add types in `mobile/src/types/`
5. Write tests in `mobile/__tests__/`

```typescript
// Example: mobile/app/(tabs)/index.tsx (Today Screen)

import { View, ScrollView, RefreshControl } from 'react-native';
import { useCallback, useState } from 'react';
import { useBriefing } from '@hooks/useBriefing';
import { AlfredGreeting } from '@components/alfred/AlfredGreeting';
import { FocusBlock } from '@components/alfred/FocusBlock';
import { ProactiveCard } from '@components/alfred/ProactiveCard';
import { HabitGrid } from '@components/habits/HabitGrid';

export default function TodayScreen() {
  const { briefing, isLoading, refetch } = useBriefing();
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  return (
    <ScrollView 
      className="flex-1 bg-alfred-bg"
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <AlfredGreeting name={briefing?.userName} />
      
      {briefing?.topPriority && (
        <FocusBlock task={briefing.topPriority} />
      )}
      
      <View className="px-4 mt-6">
        <Text className="text-lg font-semibold text-alfred-text mb-3">
          Alfred Suggests
        </Text>
        {briefing?.proactiveCards.map(card => (
          <ProactiveCard key={card.id} {...card} />
        ))}
      </View>
      
      <View className="px-4 mt-6 mb-8">
        <Text className="text-lg font-semibold text-alfred-text mb-3">
          Habits Due
        </Text>
        <HabitGrid habits={briefing?.habitsDue} />
      </View>
    </ScrollView>
  );
}
```

---

## 🧪 Testing Guidelines

### Backend Unit Tests

```python
# tests/unit/agents/test_executor.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from alfred.core.agents.executor import AgentExecutor
from alfred.core.agents.context import AgentContext

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.complete = AsyncMock()
    return llm

@pytest.fixture
def executor(mock_llm):
    return AgentExecutor(llm=mock_llm, tools=[])

@pytest.mark.asyncio
async def test_simple_response(executor, mock_llm):
    """Agent returns direct response when no tools needed"""
    mock_llm.complete.return_value = LLMResponse(
        content="Hello! How can I help?",
        tool_calls=None
    )
    
    result = await executor.run(
        "Hi Alfred",
        context=AgentContext(user_id="test")
    )
    
    assert "Hello" in result.response
    assert result.tool_calls_made == 0

@pytest.mark.asyncio
async def test_tool_execution(executor, mock_llm):
    """Agent executes tool and uses result"""
    mock_llm.complete.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[ToolCall(id="1", name="get_tasks", arguments={})]
        ),
        LLMResponse(
            content="You have 3 tasks due today.",
            tool_calls=None
        )
    ]
    
    result = await executor.run(
        "What tasks do I have?",
        context=AgentContext(user_id="test")
    )
    
    assert "3 tasks" in result.response
    assert result.tool_calls_made == 1
```

### Mobile Component Tests

```typescript
// mobile/__tests__/components/ProactiveCard.test.tsx

import { render, fireEvent } from '@testing-library/react-native';
import { ProactiveCard } from '@components/alfred/ProactiveCard';

describe('ProactiveCard', () => {
  const mockCard = {
    id: '1',
    type: 'stale_project',
    title: 'No update on RSN',
    message: "It's been 3 days since you updated RSN project",
    actions: [
      { label: 'Update Now', action: 'update' },
      { label: 'Snooze', action: 'snooze' }
    ]
  };

  it('renders card content correctly', () => {
    const { getByText } = render(<ProactiveCard {...mockCard} />);
    
    expect(getByText('No update on RSN')).toBeTruthy();
    expect(getByText(/3 days/)).toBeTruthy();
  });

  it('calls onAction when button pressed', () => {
    const onAction = jest.fn();
    const { getByText } = render(
      <ProactiveCard {...mockCard} onAction={onAction} />
    );
    
    fireEvent.press(getByText('Update Now'));
    
    expect(onAction).toHaveBeenCalledWith('update');
  });
});
```

---

## 🚫 Anti-Patterns to Avoid

1. **Don't put business logic in API routes** - Routes handle HTTP only
2. **Don't hardcode LLM provider** - Always use the provider interface
3. **Don't skip the observation step** - Agent must check tool results
4. **Don't store secrets in code** - Use environment variables
5. **Don't ignore type hints** - Use Pydantic models for data
6. **Don't create giant files** - Split into focused modules
7. **Don't skip tests** - All new code should have tests
8. **Don't mix async/sync** - Be consistent with async patterns

---

## 📞 Getting Help

- **Architecture questions**: See `docs/ARCHITECTURE.md`
- **API reference**: Run server and visit `/docs`
- **Connector guide**: See `docs/CONNECTORS.md`
- **Mobile setup**: See `docs/MOBILE_SETUP.md`

---

## 🎯 Success Metrics

1. **Agent Intelligence**: Multi-turn conversations with tool use
2. **Memory Persistence**: Facts from conversations stored and retrieved
3. **Model Flexibility**: Easy to switch between 10+ LLM providers
4. **Connector Coverage**: 50+ app integrations available
5. **Proactive Value**: Users receive useful, timely notifications
6. **Mobile Polish**: Responsive, native feel on iOS and Android
7. **Test Coverage**: >70% code coverage
8. **CI/CD**: Automated testing and deployment

---

*Last updated: January 2026*
