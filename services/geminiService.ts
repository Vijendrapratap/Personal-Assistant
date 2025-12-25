import { GoogleGenAI, FunctionDeclaration, Type } from "@google/genai";
import { Project, UserContext, Message, Task, Habit } from "../types";

// --- Tool Definitions ---

const manageTaskTool: FunctionDeclaration = {
  name: 'manageTask',
  description: 'Add, complete, or update a task. Use this when the user mentions to-dos.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      action: { type: Type.STRING, enum: ['add', 'complete', 'delete'] },
      taskText: { type: Type.STRING, description: 'The content of the task' },
      role: { type: Type.STRING, enum: ['COO', 'Founder', 'PM', 'Personal'], description: 'The role this task falls under' },
      projectName: { type: Type.STRING, description: 'Optional project name to link this task to' }
    },
    required: ['action', 'taskText'],
  },
};

const updateHabitTool: FunctionDeclaration = {
  name: 'updateHabit',
  description: 'Log a habit as completed or ask to track a new habit.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      habitName: { type: Type.STRING },
      completed: { type: Type.BOOLEAN },
    },
    required: ['habitName', 'completed'],
  },
};

const updateProjectTool: FunctionDeclaration = {
  name: 'updateProject',
  description: 'Log a status update for a specific project. Use this when the user gives a progress report.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      projectName: { type: Type.STRING },
      status: { type: Type.STRING, enum: ['on_track', 'at_risk', 'delayed', 'completed'] },
      updateContent: { type: Type.STRING },
      nextStep: { type: Type.STRING }
    },
    required: ['projectName', 'status', 'updateContent'],
  },
};

const rememberFactTool: FunctionDeclaration = {
  name: 'rememberFact',
  description: 'Save a permanent fact about Pratap into the Knowledge Graph.',
  parameters: {
    type: Type.OBJECT,
    properties: {
      fact: { type: Type.STRING },
    },
    required: ['fact'],
  },
};

// --- Service ---

export const sendMessageToGemini = async (
  history: Message[],
  newMessage: string,
  projects: Project[],
  tasks: Task[],
  habits: Habit[],
  userContext: UserContext
): Promise<{ text: string; toolCalls?: any[] }> => {
  try {
    const apiKey = process.env.API_KEY || '';
    if (!apiKey) return { text: "Error: API Key missing." };

    const ai = new GoogleGenAI({ apiKey });

    // Construct Context
    const projectContext = projects.map(p => 
      `[${p.role}] ${p.name}: ${p.status}. Next: ${p.nextStep}`
    ).join('\n');

    const taskContext = tasks.filter(t => !t.isCompleted).map(t => 
      `- ${t.text} (${t.role})`
    ).join('\n');

    const habitContext = habits.map(h => 
      `- ${h.name}: ${h.completedToday ? 'Done' : 'Not Done'} (Streak: ${h.streak})`
    ).join('\n');

    const facts = userContext.facts.join('\n');

    const dynamicSystemInstruction = `
You are DPA, Pratap's proactive Chief of Staff. 
Pratap is a busy executive juggling 3 roles: COO (CodeStellar), Founder (Pratap.ai, Civic Vigilance), and Project Manager (Client Work).

**CURRENT STATE:**
- **Roles:** COO, Founder, PM.
- **Projects:** ${projects.map(p => p.name).join(', ')}.
- **Unfinished Tasks:**
${taskContext}
- **Habits Today:**
${habitContext}
- **Knowledge Graph:**
${facts}

**YOUR BEHAVIOR:**
1. **Be Proactive:** Don't just answer. If a project like "No Excuse" is delayed, ask "What's the blocker on No Excuse today?".
2. **Habit Accountability:** If he hasn't worked out, remind him gently about his discipline goals.
3. **Task Management:** If he mentions a new todo, immediately use the 'manageTask' tool.
4. **Knowledge:** If he mentions a new preference or tool, use 'rememberFact'.
5. **Tone:** Concise, Executive, Action-Oriented. No fluff.

**SCENARIO:**
If he says "Update on Muay Thai", use 'updateProject'.
If he says "I recorded a video", use 'updateHabit'.
`;

    const chat = ai.chats.create({
      model: 'gemini-3-flash-preview',
      config: {
        systemInstruction: dynamicSystemInstruction,
        tools: [{ functionDeclarations: [manageTaskTool, updateHabitTool, updateProjectTool, rememberFactTool] }],
      },
      history: history.map(msg => ({
        role: msg.role === 'user' ? 'user' : 'model',
        parts: [{ text: msg.content }],
      })),
    });

    const result = await chat.sendMessage({ message: newMessage });
    const toolCalls = result.functionCalls;

    return {
      text: result.text || (toolCalls ? "On it." : "I'm listening."),
      toolCalls: toolCalls
    };

  } catch (error) {
    console.error("Gemini API Error:", error);
    return { text: "Connection error." };
  }
};