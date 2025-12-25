import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Chat from './components/Chat';
import Integrations from './components/Integrations';
import Decisions from './components/Decisions';
import Onboarding from './components/Onboarding';
import { Page, Project, UserContext, Task, Habit, AppState, ProjectUpdate } from './types';
import { initDB, StorageService } from './lib/storage';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>(Page.DASHBOARD);
  const [showOnboarding, setShowOnboarding] = useState(false);
  
  // App State - Loaded from LocalStorage Service
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [habits, setHabits] = useState<Habit[]>([]);
  const [userContext, setUserContext] = useState<UserContext>({ name: '', title: '', facts: [] });

  // Initialize Data
  useEffect(() => {
    // Check if onboarded
    const hasOnboarded = localStorage.getItem('dpa_has_onboarded');
    if (!hasOnboarded) {
      setShowOnboarding(true);
    }

    // Load Data from 'Backend'
    const db = initDB();
    setProjects(db.projects);
    setTasks(db.tasks);
    setHabits(db.habits);
    setUserContext(db.userContext);
  }, []);

  const handleOnboardingComplete = () => {
    localStorage.setItem('dpa_has_onboarded', 'true');
    setShowOnboarding(false);
  };

  // --- Wrapper Functions that Sync UI and Storage ---
  
  const handleUpdateProject = (projectName: string, status: any, content: string, nextStep: string) => {
    const existing = projects.find(p => p.name.toLowerCase().includes(projectName.toLowerCase()));
    if (existing) {
        const newUpdate: ProjectUpdate = {
          id: Date.now().toString(),
          date: new Date().toLocaleDateString(),
          content,
          sentiment: 'neutral'
        };

        const updated: Project = {
            ...existing,
            status: status || existing.status,
            lastUpdate: 'Just now',
            nextStep: nextStep || existing.nextStep,
            updates: [newUpdate, ...existing.updates]
        };
        // Optimistic UI Update
        const newProjects = projects.map(p => p.id === existing.id ? updated : p);
        setProjects(newProjects);
        // Backend Update
        StorageService.updateProject(updated);
    }
  };

  const handleManageTask = (action: string, text: string, role?: any, projectName?: string) => {
    if (action === 'add') {
      const newTask: Task = {
        id: Date.now().toString(),
        text,
        role: role || 'Personal',
        isCompleted: false,
        priority: 'medium',
        projectId: projectName ? projects.find(p => p.name.toLowerCase().includes(projectName.toLowerCase()))?.id : undefined
      };
      const newTasks = [newTask, ...tasks];
      setTasks(newTasks);
      StorageService.saveTasks(newTasks);

    } else if (action === 'complete') {
      const newTasks = tasks.map(t => t.text.toLowerCase().includes(text.toLowerCase()) ? { ...t, isCompleted: true } : t);
      setTasks(newTasks);
      StorageService.saveTasks(newTasks);
    }
  };

  const handleUpdateHabit = (name: string, completed: boolean) => {
    const newHabits = habits.map(h => {
      if (h.name.toLowerCase().includes(name.toLowerCase())) {
        return {
           ...h,
           completedToday: completed,
           streak: completed ? h.streak + 1 : h.streak
        };
      }
      return h;
    });
    setHabits(newHabits);
    StorageService.saveHabits(newHabits);
  };

  const handleRememberFact = (fact: string) => {
    const newContext = { ...userContext, facts: [...userContext.facts, fact] };
    setUserContext(newContext);
    StorageService.saveContext(newContext);
  };

  // Manual toggle handlers for Dashboard
  const toggleHabit = (id: string) => {
    const newHabits = habits.map(h => h.id === id ? { ...h, completedToday: !h.completedToday } : h);
    setHabits(newHabits);
    StorageService.saveHabits(newHabits);
  };

  const toggleTask = (id: string) => {
    const newTasks = tasks.map(t => t.id === id ? { ...t, isCompleted: !t.isCompleted } : t);
    setTasks(newTasks);
    StorageService.saveTasks(newTasks);
  };

  const renderPage = () => {
    switch (currentPage) {
      case Page.DASHBOARD:
        return <Dashboard 
          setPage={setCurrentPage} 
          projects={projects}
          tasks={tasks}
          habits={habits}
          userContext={userContext}
          onToggleHabit={toggleHabit}
          onToggleTask={toggleTask}
        />;
      case Page.CHAT:
        return <Chat 
          projects={projects}
          tasks={tasks}
          habits={habits}
          userContext={userContext}
          onUpdateProject={handleUpdateProject}
          onRememberFact={handleRememberFact}
          onManageTask={handleManageTask}
          onUpdateHabit={handleUpdateHabit}
        />;
      case Page.INTEGRATIONS:
        return <Integrations />;
      case Page.DECISIONS:
        return <Decisions />;
      default:
        return (
          <div className="flex flex-col items-center justify-center h-full text-center">
             <h2 className="text-xl font-bold text-white mb-2">Coming Soon</h2>
          </div>
        );
    }
  };

  return (
    <>
      {showOnboarding && <Onboarding onComplete={handleOnboardingComplete} />}
      <Layout currentPage={currentPage} setPage={setCurrentPage}>
        {renderPage()}
      </Layout>
    </>
  );
}

export default App;