# Alfred - The Digital Butler

Alfred is a state-of-the-art Personal Assistant designed to be proactive, stateful, and context-aware. Unlike passive chatbots, Alfred acts as your "Chief of Staff," managing your specific roles, tasks, and habits.

## 🏗 Architecture

The project follows a **Clean Architecture** pattern to ensure scalability and maintainability.

### Backend (`alfred/`)
*   **Language:** Python 3.11+
*   **API Framework:** FastAPI
*   **Agent Framework:** Agno (formerly Phidata)
*   **Database:** PostgreSQL (User Data, Chat History, Preferences)
*   **Knowledge Base:** Qdrant (Vector DB for Long-term Memory)
*   **Architecture:**
    *   `core/`: Pure domain logic (Entities, Interfaces, Butler).
    *   `infrastructure/`: Adapters for LLM (OpenAI/Ollama), Database (Postgres), and Tools.
    *   `api/`: REST Endpoints (Auth, Chat).

### Frontend (`mobile/`)
*   **Framework:** React Native (Expo)
*   **Platform:** Android & iOS
*   **UI Library:** React Native Gifted Chat
*   **Navigation:** React Navigation (Auth & App Stacks)
*   **State:** Local SecureStore for JWT tokens.

## 🚀 Key Features

1.  **Identity & Profile**: Alfred knows who you are. You can configure your **Bio**, **Work Type**, and **Personality Preferences** (e.g., "Witty Butler", "Sarcastic Sidekick").
2.  **Authentication**: Secure Signup and Login system using JWT.
3.  **Reflexive Memory**: Alfred learns from your corrections. If you say "I prefer bullet points," he saves that preference and uses it forever.
4.  **Privacy First**: Your data is stored in your own PostgreSQL instance.

## 🛠 Getting Started

### Prerequisites
*   Python 3.11+
*   Node.js & npm
*   PostgreSQL
*   Expo Go (on your phone) or Android Emulator

### 1. Backend Setup
```bash
# 1. Run the setup script to create venv and install dependencies
./setup.sh

# 2. Activate Virtual Environment
source venv/bin/activate

# 3. Configure Environment
# Copy .env.example to .env and set your OPENAI_API_KEY and DATABASE_URL
cp .env.example .env

# 4. Run the Server
python -m uvicorn alfred.main:app --reload --host 0.0.0.0
```

### 2. Mobile App Setup
```bash
cd mobile

# 1. Install Dependencies
npx expo install

# 2. Run on Android Emulator
npm run android

# 3. Run on iOS Simulator (macOS only)
npm run ios
```

*Note: The mobile app defaults to `10.0.2.2:8000` for Android Emulator access to localhost. Update `mobile/src/api/client.ts` if running on a physical device.*

## 📚 Documentation
*   [API Documentation](docs/API.md)
*   [Database Schema](docs/DB_SCHEMA.md)
*   [Knowledge Base](docs/KNOWLEDGE_BASE.md)
*   [MCP Setup](docs/MCP_SETUP.md)
