import React from 'react';
import { Project, Task, Habit, Page, UserContext } from '../types';
import { LucideCheckCircle, LucideCircle, LucideAlertOctagon, LucideZap, LucideBriefcase, LucideUser, LucideLayers, LucideTarget, LucideArrowRight } from 'lucide-react';

interface DashboardProps {
  setPage: (page: Page) => void;
  projects: Project[];
  tasks: Task[];
  habits: Habit[];
  userContext: UserContext;
  onToggleHabit: (id: string) => void;
  onToggleTask: (id: string) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ setPage, projects, tasks, habits, userContext, onToggleHabit, onToggleTask }) => {
  
  const tasksByRole = {
    COO: tasks.filter(t => t.role === 'COO' && !t.isCompleted),
    Founder: tasks.filter(t => t.role === 'Founder' && !t.isCompleted),
    PM: tasks.filter(t => t.role === 'PM' && !t.isCompleted),
  };

  const completedTasks = tasks.filter(t => t.isCompleted).length;
  const totalHabits = habits.length;
  const completedHabits = habits.filter(h => h.completedToday).length;
  const progress = Math.round(((completedTasks + completedHabits) / (tasks.length + totalHabits)) * 100) || 0;

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      
      {/* Hero / Greeting */}
      <div className="flex flex-col md:flex-row justify-between items-end gap-6 pb-6 border-b border-white/5">
        <div>
          <h1 className="text-4xl font-bold text-white tracking-tight mb-2">
            Command Center
          </h1>
          <p className="text-slate-400 font-medium">
            Welcome back, {userContext.name}. Systems are <span className="text-status-success">Online</span>.
          </p>
        </div>
        
        {/* Daily Progress Widget */}
        <div className="flex items-center gap-6 bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-sm">
           <div className="text-right">
              <div className="text-xs text-slate-400 uppercase tracking-wider font-bold">Daily Velocity</div>
              <div className="text-2xl font-bold text-white font-mono">{progress}%</div>
           </div>
           <div className="w-16 h-16 relative flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                <path className="text-white/10" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
                <path className="text-accent-primary" strokeDasharray={`${progress}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
              </svg>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* COLUMN 1: Habit Stack (Slim) */}
        <div className="lg:col-span-3 space-y-4">
           <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
             <LucideTarget size={14} /> Daily Protocol
           </h3>
           <div className="grid grid-cols-1 gap-3">
             {habits.map(h => (
               <button 
                  key={h.id}
                  onClick={() => onToggleHabit(h.id)}
                  className={`relative overflow-hidden w-full flex items-center justify-between p-4 rounded-2xl border transition-all duration-300 group ${
                    h.completedToday 
                      ? 'bg-accent-primary/20 border-accent-primary/50' 
                      : 'bg-white/5 border-white/5 hover:bg-white/10'
                  }`}
               >
                  <div className="flex items-center gap-3 z-10">
                     <div className={`w-8 h-8 rounded-full flex items-center justify-center text-lg ${h.completedToday ? 'bg-accent-primary text-white' : 'bg-white/5 text-slate-500'}`}>
                        {h.category === 'health' ? '💪' : h.category === 'content' ? '📹' : '🧠'}
                     </div>
                     <div className="text-left">
                       <div className={`text-sm font-bold ${h.completedToday ? 'text-white' : 'text-slate-300'}`}>{h.name}</div>
                       <div className="text-[10px] text-slate-500 font-mono">Streak: {h.streak} days</div>
                     </div>
                  </div>
                  {h.completedToday && <LucideCheckCircle size={18} className="text-accent-primary z-10" />}
                  {/* Progress Fill Animation */}
                  <div className={`absolute inset-0 bg-accent-primary/10 transition-transform duration-500 origin-left ${h.completedToday ? 'scale-x-100' : 'scale-x-0'}`} />
               </button>
             ))}
           </div>
        </div>

        {/* COLUMN 2: Task Matrix (Wide) */}
        <div className="lg:col-span-5 space-y-4">
           <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                <LucideZap size={14} /> Action Matrix
              </h3>
              <button onClick={() => setPage(Page.CHAT)} className="text-[10px] bg-white/5 hover:bg-white/10 px-2 py-1 rounded border border-white/5 transition-colors">+ Add Task</button>
           </div>
           
           <div className="bg-black/20 backdrop-blur-md border border-white/5 rounded-3xl p-1 overflow-hidden min-h-[400px]">
             {Object.entries(tasksByRole).map(([role, roleTasks]) => (
                roleTasks.length > 0 && (
                  <div key={role} className="mb-2 last:mb-0">
                    <div className="px-4 py-2 bg-white/5 border-y border-white/5 text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                       {role === 'COO' || role === 'Founder' ? <LucideBriefcase size={10} /> : <LucideLayers size={10} />}
                       {role}
                    </div>
                    <div>
                      {roleTasks.map(task => (
                        <div key={task.id} 
                             onClick={() => onToggleTask(task.id)}
                             className="group flex items-start gap-3 p-4 hover:bg-white/5 transition-colors cursor-pointer border-b border-white/5 last:border-0"
                        >
                          <div className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${task.isCompleted ? 'bg-status-success border-status-success' : 'border-slate-600 group-hover:border-accent-primary'}`}>
                            {task.isCompleted && <LucideCheckCircle size={12} className="text-white" />}
                          </div>
                          <div className="flex-1">
                             <div className={`text-sm font-medium leading-tight ${task.isCompleted ? 'text-slate-500 line-through' : 'text-slate-200 group-hover:text-white'}`}>
                                {task.text}
                             </div>
                             {task.priority === 'high' && (
                               <span className="inline-block mt-1.5 text-[9px] px-1.5 py-0.5 rounded bg-status-danger/20 text-status-danger font-bold uppercase">High Priority</span>
                             )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
             ))}
             {Object.values(tasksByRole).flat().length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 py-20">
                   <LucideCheckCircle size={32} className="mb-2 opacity-50" />
                   <p className="text-sm">All clear. Good work.</p>
                </div>
             )}
           </div>
        </div>

        {/* COLUMN 3: Project Orbit (Compact) */}
        <div className="lg:col-span-4 space-y-4">
           <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
             <LucideBriefcase size={14} /> Active Orbit
           </h3>
           <div className="grid grid-cols-1 gap-3">
              {projects.map(project => (
                <div key={project.id} className="group bg-bg-glass backdrop-blur-xl border border-white/5 rounded-2xl p-4 hover:border-accent-primary/40 transition-all hover:translate-x-1">
                   <div className="flex justify-between items-start mb-2">
                      <div className="font-bold text-slate-200 text-sm">{project.name}</div>
                      <div className={`w-2 h-2 rounded-full shadow-[0_0_8px_currentColor] ${
                        project.status === 'on_track' ? 'text-status-success bg-status-success' :
                        project.status === 'at_risk' ? 'text-status-warning bg-status-warning' :
                        'text-status-danger bg-status-danger'
                      }`} />
                   </div>
                   <div className="text-xs text-slate-400 mb-3">{project.role}</div>
                   
                   <div className="bg-black/20 rounded-lg p-2 flex items-center justify-between group-hover:bg-accent-primary/5 transition-colors">
                      <div className="truncate text-xs text-slate-300 pr-2">
                        <span className="text-slate-500 mr-2">→</span> 
                        {project.nextStep}
                      </div>
                   </div>
                </div>
              ))}
              <button onClick={() => setPage(Page.PROJECTS)} className="w-full py-3 rounded-xl border border-dashed border-white/10 text-xs text-slate-500 hover:text-white hover:border-white/30 transition-all">
                View All Projects
              </button>
           </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;