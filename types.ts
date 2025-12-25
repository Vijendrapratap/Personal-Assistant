export enum Page {
  DASHBOARD = 'dashboard',
  CHAT = 'chat',
  PROJECTS = 'projects',
  HABITS = 'habits',
  DECISIONS = 'decisions',
  ALERTS = 'alerts',
  AUTOMATIONS = 'automations',
  INTEGRATIONS = 'integrations',
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  confidence?: number;
  // Visualizing the Agent's thought process
  thoughtChain?: {
    agent: 'Orchestrator' | 'ProjectManager' | 'Executive' | 'Memory';
    action: string;
    status: 'pending' | 'complete';
  }[];
}

export type RoleType = 'COO' | 'Founder' | 'PM' | 'Personal';

export interface Project {
  id: string;
  name: string;
  role: RoleType;
  description: string;
  status: 'on_track' | 'at_risk' | 'delayed' | 'maintenance';
  lastUpdate: string;
  nextStep: string;
  updates: ProjectUpdate[];
}

export interface ProjectUpdate {
  id: string;
  date: string;
  content: string;
  sentiment: 'positive' | 'neutral' | 'negative';
}

export interface Task {
  id: string;
  text: string;
  projectId?: string;
  role: RoleType;
  isCompleted: boolean;
  dueDate?: string;
  priority: 'high' | 'medium' | 'low';
}

export interface Habit {
  id: string;
  name: string;
  streak: number;
  completedToday: boolean;
  category: 'health' | 'content' | 'learning';
}

export interface UserContext {
  name: string;
  title: string;
  facts: string[];
}

export interface AppState {
  projects: Project[];
  tasks: Task[];
  habits: Habit[];
  userContext: UserContext;
}