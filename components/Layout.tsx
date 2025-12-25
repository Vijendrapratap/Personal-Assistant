import React from 'react';
import { Page } from '../types';
import { LucideLayoutDashboard, LucideMessageSquare, LucideBell, LucideBook, LucideZap, LucideLink, LucideLogOut, LucideSettings } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  currentPage: Page;
  setPage: (page: Page) => void;
}

const Layout: React.FC<LayoutProps> = ({ children, currentPage, setPage }) => {
  const navItems = [
    { page: Page.DASHBOARD, label: 'Command Center', icon: <LucideLayoutDashboard size={18} /> },
    { page: Page.CHAT, label: 'Alfred Chat', icon: <LucideMessageSquare size={18} /> },
    { page: Page.DECISIONS, label: 'Journal', icon: <LucideBook size={18} /> },
    { page: Page.INTEGRATIONS, label: 'Neural Link', icon: <LucideLink size={18} /> },
  ];

  return (
    <div className="flex min-h-screen bg-bg-primary text-slate-200 font-sans selection:bg-accent-primary/30 relative overflow-hidden">
      
      {/* Dynamic Background - Refined for Slate/Blue Theme */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] bg-accent-primary/5 rounded-full blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-900/10 rounded-full blur-[120px]" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] brightness-100 contrast-150 mix-blend-overlay"></div>
      </div>

      {/* Glass Sidebar */}
      <aside className="w-20 lg:w-72 flex flex-col fixed h-screen z-40 border-r border-white/5 bg-bg-secondary/60 backdrop-blur-xl transition-all duration-300">
        <div className="p-6 border-b border-white/5 flex items-center gap-4 justify-center lg:justify-start">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-primary to-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-accent-primary/20 shrink-0 font-serif">
            A
          </div>
          <div className="hidden lg:block">
            <div className="text-xl font-bold text-white tracking-tight leading-none font-sans">Alfred <span className="text-[10px] font-mono text-accent-secondary opacity-60 ml-1">v2.0</span></div>
            <div className="text-[10px] text-slate-500 font-medium tracking-wide uppercase mt-1">Chief of Staff</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-8 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.page}
              onClick={() => setPage(item.page)}
              className={`w-full flex items-center gap-4 px-3 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden ${
                currentPage === item.page 
                  ? 'bg-white/5 text-white shadow-inner shadow-white/5' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {currentPage === item.page && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-accent-primary rounded-r-full shadow-[0_0_12px_rgba(14,165,233,0.6)]" />
              )}
              <span className={`transition-transform duration-300 ${currentPage === item.page ? 'text-accent-secondary' : ''} lg:group-hover:translate-x-1`}>
                {item.icon}
              </span>
              <span className="hidden lg:block text-sm font-medium tracking-wide">{item.label}</span>
              
              {/* Hover glow */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 pointer-events-none" />
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 justify-center lg:justify-start p-3 rounded-xl hover:bg-white/5 cursor-pointer transition-colors group border border-transparent hover:border-white/5">
             <div className="w-8 h-8 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center shrink-0">
                <LucideSettings size={14} className="text-slate-400 group-hover:text-accent-primary group-hover:rotate-90 transition-all duration-500" />
             </div>
             <div className="hidden lg:block">
               <div className="text-xs text-slate-200 font-medium">System Config</div>
               <div className="text-[10px] text-slate-500">Connected</div>
             </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 ml-20 lg:ml-72 relative z-10 p-6 lg:p-10 overflow-x-hidden min-h-screen">
        {children}
      </main>
    </div>
  );
};

export default Layout;