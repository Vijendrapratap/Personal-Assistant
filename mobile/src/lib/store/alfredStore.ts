import { create } from 'zustand';

// ============================================================================
// TYPES
// ============================================================================

export type AlfredState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'working';

export interface User {
  id: string;
  email: string;
  name: string;
  bio?: string;
  work_type?: string;
  personality?: string;
  interaction_type?: string;
  created_at: string;
}

export interface Task {
  task_id: string;
  title: string;
  description?: string;
  project_id?: string;
  project_name?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'blocked' | 'completed' | 'cancelled';
  due_date?: string;
  created_at: string;
}

export interface Habit {
  habit_id: string;
  name: string;
  description?: string;
  frequency: 'daily' | 'weekly' | 'weekdays' | 'custom';
  category: string;
  reminder_time?: string;
  current_streak: number;
  best_streak: number;
  total_completions: number;
  is_active: boolean;
}

export interface Project {
  project_id: string;
  name: string;
  description?: string;
  organization?: string;
  status: 'active' | 'on_hold' | 'completed' | 'archived';
  role?: string;
  health_score: number;
  task_count: number;
  days_since_update?: number;
}

export interface ProactiveCard {
  id: string;
  type: 'warning' | 'insight' | 'reminder' | 'celebration';
  title: string;
  description: string;
  actions: string[];
  entity_id?: string;
  entity_type?: 'task' | 'habit' | 'project' | 'event';
  created_at: string;
}

export interface Briefing {
  greeting: string;
  focus?: {
    title: string;
    context?: string;
    due?: string;
    task_id?: string;
  };
  stats: {
    tasks_pending: number;
    tasks_completed_today: number;
    habits_pending: number;
    habits_completed_today: number;
  };
  upcoming_events: Array<{
    title: string;
    time: string;
    duration?: string;
  }>;
}

// ============================================================================
// STORE
// ============================================================================

interface AlfredStore {
  // User state
  user: User | null;
  setUser: (user: User | null) => void;

  // Alfred state
  alfredState: AlfredState;
  setAlfredState: (state: AlfredState) => void;

  // Briefing
  briefing: Briefing | null;
  briefingLoading: boolean;
  setBriefing: (briefing: Briefing | null) => void;
  setBriefingLoading: (loading: boolean) => void;

  // Tasks
  tasks: Task[];
  tasksLoading: boolean;
  setTasks: (tasks: Task[]) => void;
  setTasksLoading: (loading: boolean) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  removeTask: (taskId: string) => void;

  // Habits
  habits: Habit[];
  habitsLoading: boolean;
  setHabits: (habits: Habit[]) => void;
  setHabitsLoading: (loading: boolean) => void;
  updateHabit: (habitId: string, updates: Partial<Habit>) => void;

  // Projects
  projects: Project[];
  projectsLoading: boolean;
  setProjects: (projects: Project[]) => void;
  setProjectsLoading: (loading: boolean) => void;

  // Proactive cards
  proactiveCards: ProactiveCard[];
  setProactiveCards: (cards: ProactiveCard[]) => void;
  dismissCard: (cardId: string) => void;
  snoozeCard: (cardId: string) => void;

  // Global loading
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Error handling
  error: string | null;
  setError: (error: string | null) => void;

  // Reset store
  reset: () => void;
}

const initialState = {
  user: null,
  alfredState: 'idle' as AlfredState,
  briefing: null,
  briefingLoading: false,
  tasks: [],
  tasksLoading: false,
  habits: [],
  habitsLoading: false,
  projects: [],
  projectsLoading: false,
  proactiveCards: [],
  isLoading: false,
  error: null,
};

export const useAlfredStore = create<AlfredStore>((set) => ({
  ...initialState,

  // User
  setUser: (user) => set({ user }),

  // Alfred state
  setAlfredState: (alfredState) => set({ alfredState }),

  // Briefing
  setBriefing: (briefing) => set({ briefing }),
  setBriefingLoading: (briefingLoading) => set({ briefingLoading }),

  // Tasks
  setTasks: (tasks) => set({ tasks }),
  setTasksLoading: (tasksLoading) => set({ tasksLoading }),
  updateTask: (taskId, updates) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.task_id === taskId ? { ...task, ...updates } : task
      ),
    })),
  removeTask: (taskId) =>
    set((state) => ({
      tasks: state.tasks.filter((task) => task.task_id !== taskId),
    })),

  // Habits
  setHabits: (habits) => set({ habits }),
  setHabitsLoading: (habitsLoading) => set({ habitsLoading }),
  updateHabit: (habitId, updates) =>
    set((state) => ({
      habits: state.habits.map((habit) =>
        habit.habit_id === habitId ? { ...habit, ...updates } : habit
      ),
    })),

  // Projects
  setProjects: (projects) => set({ projects }),
  setProjectsLoading: (projectsLoading) => set({ projectsLoading }),

  // Proactive cards
  setProactiveCards: (proactiveCards) => set({ proactiveCards }),
  dismissCard: (cardId) =>
    set((state) => ({
      proactiveCards: state.proactiveCards.filter((card) => card.id !== cardId),
    })),
  snoozeCard: (cardId) =>
    set((state) => ({
      proactiveCards: state.proactiveCards.filter((card) => card.id !== cardId),
    })),

  // Global
  setIsLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  // Reset
  reset: () => set(initialState),
}));

// ============================================================================
// SELECTORS (for optimized re-renders)
// ============================================================================

export const selectUser = (state: AlfredStore) => state.user;
export const selectAlfredState = (state: AlfredStore) => state.alfredState;
export const selectBriefing = (state: AlfredStore) => state.briefing;
export const selectTasks = (state: AlfredStore) => state.tasks;
export const selectHabits = (state: AlfredStore) => state.habits;
export const selectProjects = (state: AlfredStore) => state.projects;
export const selectProactiveCards = (state: AlfredStore) => state.proactiveCards;

// Derived selectors
export const selectPendingTasks = (state: AlfredStore) =>
  state.tasks.filter((t) => t.status === 'pending' || t.status === 'in_progress');

export const selectCompletedTasks = (state: AlfredStore) =>
  state.tasks.filter((t) => t.status === 'completed');

export const selectHighPriorityTasks = (state: AlfredStore) =>
  state.tasks.filter((t) => t.priority === 'high' && t.status !== 'completed');

export const selectActiveHabits = (state: AlfredStore) =>
  state.habits.filter((h) => h.is_active);

export const selectActiveProjects = (state: AlfredStore) =>
  state.projects.filter((p) => p.status === 'active');
