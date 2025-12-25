import React from 'react';
import { MOCK_DECISIONS } from '../constants';
import { LucidePlus, LucideCheckCircle, LucideClock } from 'lucide-react';

const Decisions: React.FC = () => {
  return (
    <div className="space-y-8 animate-fade-in">
      <header className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">📓 Decision Journal</h1>
          <p className="text-slate-400 text-sm">Track decisions, outcomes, and learn from patterns</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-accent-primary to-accent-secondary text-white rounded-xl font-bold text-sm hover:shadow-lg hover:shadow-accent-primary/20 hover:scale-105 active:scale-95 transition-all">
          <LucidePlus size={16} />
          Log Decision
        </button>
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Logged', value: '23' },
          { label: 'Accuracy', value: '78%' },
          { label: 'Patterns', value: '12' },
          { label: 'Confidence', value: '85%' },
        ].map((stat) => (
          <div key={stat.label} className="bg-bg-glass border border-white/5 rounded-2xl p-6 text-center hover:border-accent-primary/30 transition-colors">
            <div className="text-3xl font-bold font-mono text-transparent bg-clip-text bg-gradient-to-r from-accent-primary to-accent-secondary mb-2">
              {stat.value}
            </div>
            <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="space-y-6">
        {MOCK_DECISIONS.map((d) => (
          <div key={d.id} className="group relative bg-bg-glass backdrop-blur-md border border-white/5 rounded-3xl p-8 transition-all hover:border-accent-primary/30">
            {/* Status Badge */}
            <div className={`absolute top-6 right-6 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ${
              d.status === 'completed' ? 'bg-status-success/15 text-status-success' : 'bg-status-warning/15 text-status-warning'
            }`}>
              {d.status === 'completed' ? <LucideCheckCircle size={12} /> : <LucideClock size={12} />}
              {d.status === 'tracking' ? 'Tracking' : 'Completed'}
            </div>

            <div className="text-xs text-slate-500 font-medium mb-2">{d.date}</div>
            <h3 className="text-xl font-bold text-white mb-6">{d.title}</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="bg-white/5 rounded-xl p-4">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold mb-2">Reason</div>
                <div className="text-sm text-slate-200">{d.reason}</div>
              </div>
              <div className="bg-white/5 rounded-xl p-4">
                <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold mb-2">Expected Outcome</div>
                <div className="text-sm text-slate-200">{d.expectedOutcome}</div>
              </div>
            </div>

            <div className="border-t border-white/5 pt-6">
              <div className="text-xs font-bold text-slate-400 mb-4 flex items-center gap-2">
                <span>📊</span> Tracked Outcomes
              </div>
              <div className="flex flex-wrap gap-3">
                {d.actualOutcomes.map((outcome, idx) => (
                  <div key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-status-success/10 border border-status-success/20 rounded-lg">
                    <span className="text-xs text-slate-400 font-medium">{outcome.period}:</span>
                    <span className="text-xs text-status-success font-bold">{outcome.result}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

       {/* Learning Card */}
       <div className="bg-gradient-to-br from-accent-primary/10 to-transparent border border-accent-primary/20 rounded-3xl p-6 flex gap-6 items-start">
          <div className="w-14 h-14 flex items-center justify-center bg-accent-primary/20 rounded-2xl text-3xl flex-shrink-0">
            🧠
          </div>
          <div>
            <h4 className="text-base font-bold text-accent-secondary mb-2">Knowledge Graph Learning</h4>
            <p className="text-sm text-slate-300 leading-relaxed">
              For delay decisions in Q3-Q4, your success rate is <strong className="text-status-success">80%</strong>. 
              Pattern detected: Providing team breathing room correlates with improved morale (+15%) and faster delivery post-delay.
            </p>
          </div>
       </div>

    </div>
  );
};

export default Decisions;