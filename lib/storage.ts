import { AppState, Project, Task, Habit, UserContext } from '../types';
import { INITIAL_PROJECTS, INITIAL_TASKS, INITIAL_HABITS, INITIAL_CONTEXT } from '../constants';

const DB_KEY = 'dpa_db_v1';

// Initialize DB with defaults if empty
export const initDB = (): AppState => {
  const existing = localStorage.getItem(DB_KEY);
  if (existing) {
    try {
      const parsed = JSON.parse(existing);
      // Ensure date strings are handled if necessary, mostly JSON is fine
      return parsed;
    } catch (e) {
      console.error('DB Corrupt, resetting', e);
    }
  }

  const defaults: AppState = {
    projects: INITIAL_PROJECTS,
    tasks: INITIAL_TASKS,
    habits: INITIAL_HABITS,
    userContext: INITIAL_CONTEXT
  };
  
  localStorage.setItem(DB_KEY, JSON.stringify(defaults));
  return defaults;
};

// Generic Saver
export const saveDB = (state: AppState) => {
  localStorage.setItem(DB_KEY, JSON.stringify(state));
};

// "Backend" Controllers
export const StorageService = {
  getProjects: (): Project[] => initDB().projects,
  
  updateProject: (updatedProject: Project) => {
    const db = initDB();
    const newProjects = db.projects.map(p => p.id === updatedProject.id ? updatedProject : p);
    saveDB({ ...db, projects: newProjects });
    return newProjects;
  },

  getTasks: (): Task[] => initDB().tasks,
  
  saveTasks: (tasks: Task[]) => {
    const db = initDB();
    saveDB({ ...db, tasks });
  },

  getHabits: (): Habit[] => initDB().habits,

  saveHabits: (habits: Habit[]) => {
    const db = initDB();
    saveDB({ ...db, habits });
  },

  getContext: (): UserContext => initDB().userContext,

  saveContext: (ctx: UserContext) => {
    const db = initDB();
    saveDB({ ...db, userContext: ctx });
  }
};