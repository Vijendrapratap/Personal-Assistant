# Getting Started with Alfred

> Quick guide to get Alfred running locally in 15 minutes

---

## Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** (LTS) - [Download](https://nodejs.org/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
- **Expo CLI** - `npm install -g expo-cli`
- **EAS CLI** - `npm install -g eas-cli`

## Step 1: Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/alfred.git
cd alfred

# Copy environment files
cp .env.example .env
cp mobile/.env.example mobile/.env
```

## Step 2: Configure API Keys

Edit `.env` and add at minimum:

```bash
# Required for LLM functionality
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Or use OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Or use local Ollama (free)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

## Step 3: Start Services with Docker

```bash
# Start all backend services
docker-compose up -d

# This starts:
# - PostgreSQL (port 5432)
# - Redis (port 6379)
# - Neo4j (ports 7474, 7687)
# - Qdrant (port 6333)
# - Alfred API (port 8000)

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f alfred-api
```

## Step 4: Initialize Database

```bash
# Run migrations (first time only)
docker-compose exec alfred-api alembic upgrade head

# Seed sample data (optional)
docker-compose exec alfred-api python scripts/seed_data.py
```

## Step 5: Start Mobile App

```bash
# Navigate to mobile directory
cd mobile

# Install dependencies
npm install

# Start Expo development server
npx expo start
```

Then:
- Press `i` to open in iOS Simulator
- Press `a` to open in Android Emulator
- Scan QR code with Expo Go app on your phone

## Step 6: Create Your Account

1. Open the app
2. Tap "Create Account"
3. Enter your email and password
4. You're in! 🎉

---

## Quick Commands Reference

### Backend

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f alfred-api

# Run tests
docker-compose exec alfred-api pytest tests/ -v

# Access API docs
open http://localhost:8000/docs
```

### Mobile

```bash
# Start dev server
cd mobile && npx expo start

# Run on iOS
npx expo run:ios

# Run on Android
npx expo run:android

# Run tests
npm test

# Build preview (for testers)
npx eas build --platform all --profile preview

# Build production
npx eas build --platform all --profile production
```

### Database

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U alfred -d alfred_db

# Access Neo4j browser
open http://localhost:7474

# Access Redis CLI
docker-compose exec redis redis-cli
```

---

## Connecting Services (Connectors)

### Google (Calendar, Gmail, Drive)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Calendar, Gmail, and Drive APIs
4. Create OAuth 2.0 credentials
5. Add to `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

### Notion

1. Go to [Notion Developers](https://www.notion.so/my-integrations)
2. Create a new integration
3. Add to `.env`:
   ```
   NOTION_CLIENT_ID=your-client-id
   NOTION_CLIENT_SECRET=your-client-secret
   ```

### Slack

1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app
3. Add OAuth scopes: `channels:read`, `chat:write`, etc.
4. Add to `.env`:
   ```
   SLACK_CLIENT_ID=your-client-id
   SLACK_CLIENT_SECRET=your-client-secret
   ```

See `docs/CONNECTORS.md` for all 50+ available connectors.

---

## Troubleshooting

### Docker Issues

```bash
# Reset everything
docker-compose down -v
docker-compose up -d --build

# Check container health
docker-compose ps
docker-compose logs [service-name]
```

### Mobile Issues

```bash
# Clear cache
npx expo start --clear

# Reset node modules
rm -rf node_modules
npm install

# Reset Expo cache
npx expo start --clear
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec alfred-api alembic upgrade head
```

---

## Next Steps

1. **Explore the API**: Visit `http://localhost:8000/docs`
2. **Connect services**: Add your favorite apps in Settings > Connectors
3. **Configure briefings**: Set your morning and evening times
4. **Add projects**: Create your first project and tasks
5. **Try voice**: Tap the microphone to talk to Alfred

---

## Getting Help

- 📚 **Documentation**: See `/docs` folder
- 🐛 **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/alfred/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/alfred/discussions)

---

*Happy building with Alfred! 🤖*
