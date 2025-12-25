import { GoogleGenAI, FunctionDeclaration, Type } from "@google/genai";
import { AppState, Message } from "../types";

// --- Agent Tool Definitions ---

const TOOLS = [
  {
    name: 'manageTask',
    description: 'Add, complete, or update a task.',
    parameters: {
      type: Type.OBJECT,
      properties: {
        action: { type: Type.STRING, enum: ['add', 'complete', 'delete'] },
        taskText: { type: Type.STRING },
        role: { type: Type.STRING, enum: ['COO', 'Founder', 'PM', 'Personal'] },
        projectName: { type: Type.STRING }
      },
      required: ['action', 'taskText'],
    },
  },
  {
    name: 'updateHabit',
    description: 'Log a habit as completed.',
    parameters: {
      type: Type.OBJECT,
      properties: {
        habitName: { type: Type.STRING },
        completed: { type: Type.BOOLEAN },
      },
      required: ['habitName', 'completed'],
    },
  },
  {
    name: 'updateProject',
    description: 'Log a status update for a project.',
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
  },
  {
    name: 'rememberFact',
    description: 'Save a permanent fact about the user.',
    parameters: {
      type: Type.OBJECT,
      properties: {
        fact: { type: Type.STRING },
      },
      required: ['fact'],
    },
  }
];

// --- The "Orchestrator" Agent ---
// This mimics a backend service that routes requests

export class AgentOrchestrator {
  private ai: GoogleGenAI;
  private model: any;

  constructor(apiKey: string) {
    this.ai = new GoogleGenAI({ apiKey });
    this.model = this.ai.chats;
  }

  async processRequest(
    history: Message[],
    newMessage: string,
    state: AppState
  ): Promise<{ text: string; toolCalls?: any[] }> {
    
    // 1. Build Context (The "Brain" State)
    const contextPrompt = this.buildSystemPrompt(state);

    // 2. Initialize Chat with Tools
    const chat = this.model.create({
      model: 'gemini-3-flash-preview',
      config: {
        systemInstruction: contextPrompt,
        tools: [{ functionDeclarations: TOOLS }],
      },
      history: history.map(msg => ({
        role: msg.role === 'user' ? 'user' : 'model',
        parts: [{ text: msg.content }],
      })),
    });

    try {
      // 3. Execute
      const result = await chat.sendMessage({ message: newMessage });
      const toolCalls = result.functionCalls;

      return {
        text: result.text || (toolCalls ? "Right away, sir." : "I'm listening, sir."),
        toolCalls: toolCalls
      };
    } catch (e) {
      console.error("Agent Error", e);
      return { text: "I'm afraid I've lost connection to the neural core, sir." };
    }
  }

  private buildSystemPrompt(state: AppState): string {
    const { projects, tasks, habits, userContext } = state;

    const projectSummary = projects.map(p => 
      `[${p.role}] ${p.name} (${p.status}): ${p.nextStep}`
    ).join('\n');

    const criticalTasks = tasks.filter(t => !t.isCompleted && t.priority === 'high').map(t => 
      `- ${t.text} (${t.role})`
    ).join('\n');

    const habitStatus = habits.map(h => 
      `- ${h.name}: ${h.completedToday ? '✅' : '⬜'} (Streak: ${h.streak})`
    ).join('\n');

    return `
      You are Alfred, the dedicated and discreet Chief of Staff for ${userContext.name}.
      
      **IDENTITY:**
      You are not a chatbot. You are a sophisticated, autonomous executive function system with the persona of a loyal British butler (think Alfred Pennyworth meeting JARVIS). 
      You are polite, extremely concise, and laser-focused on efficiency. You address the user as "sir" occasionally but don't overdo it.
      
      **YOUR MISSION:**
      Optimize ${userContext.name}'s performance across three distinct roles:
      1. **COO (CodeStellar)**: Operations & Efficiency.
      2. **Founder (Pratap.ai, Civic Vigilance)**: Vision & Brand.
      3. **Project Manager**: Delivery & Unblocking.

      **LIVE DATA SNAPSHOT:**
      ---
      **Active Projects:**
      ${projectSummary}
      
      **Critical Actions Required:**
      ${criticalTasks}
      
      **Daily Discipline:**
      ${habitStatus}
      
      **Knowledge Graph:**
      ${userContext.facts.join('; ')}
      ---

      **DIRECTIVES:**
      - **Be Proactive:** If a project is delayed, gently inquire about the specific blocker.
      - **State Management:** If the user implies an action ("I finished the video"), YOU MUST CALL THE TOOL to update the database. Do not just say "Very good, sir."
      - **Tone:** Refined, professional, calm. "I have updated the records, sir." "Shall we prioritize the hiring plan?"
    `;
  }
}