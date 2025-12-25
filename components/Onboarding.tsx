import React, { useState } from 'react';
import { LucideBrain, LucideLink, LucideUser, LucideRepeat, LucideArrowRight, LucideCheckCircle } from 'lucide-react';

interface OnboardingProps {
  onComplete: () => void;
}

const Onboarding: React.FC<OnboardingProps> = ({ onComplete }) => {
  const [step, setStep] = useState(0);

  const steps = [
    {
      icon: <LucideBrain size={48} className="text-accent-secondary" />,
      title: "Welcome to DPA",
      subtitle: "Your Learning Personal Assistant",
      desc: "DPA learns who you are, builds a personalized Knowledge Graph of your work and life, and proactively structures your day with intelligent briefings.",
      content: null
    },
    {
      icon: <LucideLink size={48} className="text-accent-secondary" />,
      title: "Connect Your Tools",
      subtitle: "One-Click OAuth Integration",
      desc: "Connect your existing tools so DPA can learn from your workflow and provide intelligent insights.",
      content: (
        <div className="grid grid-cols-2 gap-3 mt-8">
           {['Gmail', 'Slack', 'Asana', 'Calendar', 'Stripe', 'Notion'].map(tool => (
             <div key={tool} className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-xl cursor-pointer hover:bg-white/10 hover:border-accent-primary/30 transition-all">
               <div className="w-8 h-8 rounded bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-xs">
                 {tool[0]}
               </div>
               <span className="text-sm font-medium flex-1">{tool}</span>
               <span className="text-xs text-accent-secondary">Connect</span>
             </div>
           ))}
        </div>
      )
    },
    {
      icon: <LucideUser size={48} className="text-accent-secondary" />,
      title: "Tell Me About You",
      subtitle: "Quick Personalization",
      desc: "A few quick questions to understand your role, priorities, and decision-making style.",
      content: (
        <div className="grid grid-cols-1 gap-3 mt-8">
           {['CEO / Founder', 'Executive', 'Manager', 'Freelancer'].map(role => (
             <div key={role} className="p-4 bg-white/5 border border-white/10 rounded-xl cursor-pointer hover:bg-accent-primary/10 hover:border-accent-primary/50 transition-all text-center text-sm font-medium">
                {role}
             </div>
           ))}
        </div>
      )
    },
    {
      icon: <LucideRepeat size={48} className="text-accent-secondary" />,
      title: "Your Daily Loop",
      subtitle: "Morning Brief → Work → Evening Retro",
      desc: "DPA structures your day with proactive briefings, real-time assistance, and reflective tracking.",
      content: (
        <div className="mt-8 space-y-6 relative pl-4 border-l-2 border-white/5">
           <div className="relative">
             <div className="absolute -left-[21px] top-0 w-3 h-3 rounded-full bg-status-warning border-2 border-bg-secondary"></div>
             <div className="text-xs font-bold text-slate-500 mb-1">6:00 AM</div>
             <div className="p-3 bg-white/5 rounded-lg border border-white/5">
                <div className="text-sm font-bold text-white">☀️ Morning Brief</div>
                <div className="text-xs text-slate-400">Priorities, metrics, risks & opportunities</div>
             </div>
           </div>
           <div className="relative">
             <div className="absolute -left-[21px] top-0 w-3 h-3 rounded-full bg-status-info border-2 border-bg-secondary"></div>
             <div className="text-xs font-bold text-slate-500 mb-1">9 AM - 5 PM</div>
             <div className="p-3 bg-white/5 rounded-lg border border-white/5">
                <div className="text-sm font-bold text-white">💼 Work Mode</div>
                <div className="text-xs text-slate-400">Queries, alerts, tasks & automations</div>
             </div>
           </div>
        </div>
      )
    }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg-primary/90 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-bg-secondary border border-white/10 rounded-3xl p-8 md:p-12 relative overflow-hidden shadow-2xl">
        
        {/* Background blobs */}
        <div className="absolute -top-[100px] -right-[100px] w-[300px] h-[300px] bg-accent-primary rounded-full blur-[80px] opacity-20" />
        <div className="absolute -bottom-[100px] -left-[100px] w-[200px] h-[200px] bg-status-info rounded-full blur-[80px] opacity-15" />

        <div className="relative z-10 text-center">
           {/* Progress Dots */}
           <div className="flex justify-center gap-2 mb-8">
             {steps.map((_, i) => (
               <div key={i} className={`h-1.5 rounded-full transition-all duration-300 ${i === step ? 'w-8 bg-accent-primary' : i < step ? 'w-1.5 bg-accent-secondary' : 'w-1.5 bg-white/10'}`} />
             ))}
           </div>

           <div className="mb-6 flex justify-center">{steps[step].icon}</div>
           
           <h2 className="text-3xl font-bold text-white mb-2">{steps[step].title}</h2>
           <p className="text-accent-secondary font-medium mb-4">{steps[step].subtitle}</p>
           <p className="text-slate-400 text-sm leading-relaxed max-w-sm mx-auto">{steps[step].desc}</p>
           
           {steps[step].content}

           <div className="flex justify-between mt-12 pt-6 border-t border-white/5">
             <button 
               onClick={() => setStep(Math.max(0, step - 1))}
               className={`text-slate-400 text-sm font-medium hover:text-white transition-colors ${step === 0 ? 'invisible' : ''}`}
             >
               Back
             </button>
             <button 
               onClick={() => {
                 if (step === steps.length - 1) {
                   onComplete();
                 } else {
                   setStep(step + 1);
                 }
               }}
               className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-accent-primary to-accent-secondary text-white rounded-xl text-sm font-bold shadow-lg shadow-accent-primary/25 hover:scale-105 active:scale-95 transition-all"
             >
               {step === steps.length - 1 ? 'Get Started' : 'Continue'}
               <LucideArrowRight size={16} />
             </button>
           </div>
        </div>
      </div>
    </div>
  );
};

export default Onboarding;