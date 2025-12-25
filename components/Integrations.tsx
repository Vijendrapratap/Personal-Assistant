import React from 'react';
import { MOCK_INTEGRATIONS } from '../constants';
import { LucideCheckCircle, LucideXCircle, LucideRefreshCw, LucidePauseCircle } from 'lucide-react';

const Integrations: React.FC = () => {
  return (
    <div className="space-y-8 animate-fade-in">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">🔗 Integrations</h1>
        <p className="text-slate-400 text-sm">Connect your tools to build your Knowledge Graph</p>
      </header>

      {/* Sync Status Bar */}
      <div className="bg-bg-glass border border-white/5 rounded-2xl p-6 flex flex-col md:flex-row justify-between items-center gap-6">
         <div className="flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-success opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-status-success"></span>
            </span>
            <span className="text-sm font-medium text-slate-200">All systems syncing normally</span>
         </div>
         <div className="flex gap-8 text-xs font-medium text-slate-400">
            <div className="flex items-center gap-2">
               <span className="text-lg">📊</span> 40,930 data points
            </div>
            <div className="flex items-center gap-2">
               <span className="text-lg">🧠</span> 1,284 entities
            </div>
            <div className="flex items-center gap-2">
               <span className="text-lg">🔗</span> 3,420 relationships
            </div>
         </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {MOCK_INTEGRATIONS.map((app) => (
          <div key={app.id} className="group bg-bg-glass backdrop-blur-md border border-white/5 rounded-3xl p-6 transition-all duration-300 hover:border-accent-primary/30 hover:-translate-y-1">
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 flex items-center justify-center bg-white/5 rounded-2xl text-2xl group-hover:scale-110 transition-transform duration-300">
                {app.icon}
              </div>
              <div className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                app.status === 'connected' ? 'bg-status-success/15 text-status-success' :
                app.status === 'disconnected' ? 'bg-slate-700/50 text-slate-400' :
                app.status === 'syncing' ? 'bg-status-warning/15 text-status-warning' :
                'bg-status-info/15 text-status-info'
              }`}>
                {app.status === 'connected' && <LucideCheckCircle size={10} />}
                {app.status === 'disconnected' && <LucideXCircle size={10} />}
                {app.status === 'syncing' && <LucideRefreshCw size={10} className="animate-spin" />}
                {app.status === 'paused' && <LucidePauseCircle size={10} />}
                {app.status}
              </div>
            </div>

            <h3 className="text-lg font-bold text-white mb-2">{app.name}</h3>
            
            <div className="space-y-1 mb-6">
               <div className="text-xs text-slate-500 flex justify-between">
                  <span>Last sync:</span>
                  <span className="text-slate-300">{app.lastSync}</span>
               </div>
               <div className="text-xs text-slate-500 flex justify-between">
                  <span>Data points:</span>
                  <span className="text-slate-300">{app.dataPoints.toLocaleString()}</span>
               </div>
            </div>

            <button className={`w-full py-2.5 rounded-xl text-xs font-bold transition-all ${
              app.status === 'connected' 
                ? 'bg-transparent border border-white/10 text-slate-300 hover:border-white/20 hover:text-white'
                : 'bg-gradient-to-r from-accent-primary to-accent-secondary text-white hover:shadow-lg hover:shadow-accent-primary/25'
            }`}>
               {app.status === 'connected' ? 'Configure' : 'Connect'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Integrations;