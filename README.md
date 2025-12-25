# DPA - Digital Personal Assistant (v2.0)

## 🌟 Vision: From "Chatbot" to "Chief of Staff"

Most AI assistants (ChatGPT, Gemini, Claude) are **passive**. You go to them, ask a question, get an answer, and leave. The context is lost, and the assistant doesn't "care" about your day-to-day progress.

**DPA (Digital Personal Assistant)** flips this model. It is designed to be **proactive, stateful, and context-aware**. It acts as your **Chief of Staff**:

1.  **It knows who you are:** It tracks your specific roles (COO, Founder, PM) and the projects attached to them.
2.  **It holds you accountable:** It tracks habits and tasks, reminding you of missed workouts or stale projects.
3.  **It learns:** It builds a "Knowledge Graph" of facts about you over time (e.g., "Prfers morning meetings", "Focusing on Product-Led Growth").
4.  **It acts:** It doesn't just talk; it updates the database. When you say "I finished the design," it marks the task complete and updates the project status automatically.

---

## 🏗️ Architecture

The application is built as a **State-Driven AI Agent**.

### Core Stack
*   **Frontend:** React 19 (TypeScript)
*   **Styling:** Tailwind CSS (Glassmorphism/Dark Mode aesthetics)
*   **Intelligence:** Google Gemini API (Model: `gemini-3-flash-preview`)
*   **Icons:** Lucide React

### Data Flow & Logic
The "Brain" of the application relies on the interaction between the **React State** and **Gemini Tools**.

1.  **The State (Single Source of Truth):**
    *   `UserContext`: Stores static identity and dynamic "Facts" (Knowledge Graph).
    *   `Projects`: Array of active projects with metadata (status, next steps, role).
    *   `Tasks`: The "Action Matrix" of to-dos linked to roles/projects.
    *   `Habits`: Daily recurring items with streak logic.

2.  **The Loop (Read/Write):**
    *   **READ:** When you open Chat, the System Prompt is dynamically injected with a snapshot of the current state (e.g., "Project X is delayed", "Habit Y is not done"). This allows the AI to ask relevant questions immediately.
    *   **WRITE:** When you speak, Gemini analyzes the intent. If you want to change something, it does **not** just reply with text. It triggers a **Tool Call** (Function Call).
        *   *Example:* User says "Muay Thai tickets QA is done."
        *   *Gemini:* Calls `updateProject({ name: 'Muay Thai', status: 'on_track', nextStep: 'Deploy' })`.
        *   *React:* Executes the function -> Updates State -> UI Rerenders.

---

## 🚀 Key Features

### 1. The Action Matrix (Task Management)
Instead of a generic to-do list, tasks are categorized by **Role** (COO, Founder, PM).
*   **Why?** Context switching is the enemy of productivity. This allows you to "put on the hat" for a specific role and clear those tasks.
*   **AI Integration:** You can say "Add a task to check payroll for CodeStellar," and the AI tags it with `Role: COO`.

### 2. Project Orbit (Status Tracking)
Visualizes your 7+ active projects in a bento-grid layout.
*   **Visual Indicators:** Color-coded status dots (Green/On Track, Red/Delayed, Yellow/At Risk).
*   **Smart Updates:** You don't click buttons to update. You tell DPA, "No Excuse is delayed because of the API." DPA logs the update, changes the color to Red, and sets the update timestamp.

### 3. Habit Stack (Behavior Design)
Tracks recurring personal goals (Workout, Content Creation, Writing).
*   **Gamification:** Tracks streaks.
*   **Accountability:** If you chat with DPA in the evening and haven't logged your habit, it will gently nudge you.

### 4. Knowledge Graph (Long-term Memory)
A persistent list of facts the AI has learned about you.
*   **Mechanism:** If you say, "I want to start writing 500 words daily," DPA calls the `rememberFact` tool.
*   **Usage:** In future conversations, DPA uses this context to prioritize advice (e.g., prioritizing writing tasks because it knows it's a goal).

### 5. Integrations (Mocked for UI)
A visual representation of how DPA connects to external data sources (Gmail, Slack, GitHub). In a production version, this would use MCP (Model Context Protocol) to actually fetch external data.

---

## 🔮 Future Roadmap

1.  **Persistance:** Move state from `useState` (RAM) to `localStorage` or a backend (PostgreSQL/Supabase).
2.  **Gemini Live:** Implement the WebSocket API for real-time voice conversations (Talk to DPA while driving).
3.  **MCP Integration:** Connect real tools (Notion API, GitHub API) so DPA can actually *read* your emails and *create* GitHub issues.
4.  **Decision Journaling:** A structured module to log tough executive decisions and review their outcomes 30/60/90 days later to improve judgment.
