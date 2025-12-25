import React, { useState, useRef, useEffect } from 'react';
import { Message, Project, UserContext, Task, Habit } from '../types';
import { AgentOrchestrator } from '../services/agentSystem';
import { LucideSend, LucideBot, LucideUser, LucideSparkles, LucideLoader2, LucideCheck, LucideBrainCircuit, LucideCpu } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface ChatProps {
  projects: Project[];
  tasks: Task[];
  habits: Habit[];
  userContext: UserContext;
  onUpdateProject: (name: string, status: string, content: string, next: string) => void;
  onRememberFact: (fact: string) => void;
  onManageTask: (action: string, text: string, role?: string, project?: string) => void;
  onUpdateHabit: (name: string, completed: boolean) => void;
}

const SUGGESTED_QUERIES = [
  "Update No Excuse: dev team is blocking API",
  "I recorded my video today",
  "Add task: Review Q1 hiring plan for CodeStellar",
  "What's on my plate for Civic Vigilance?"
];

const Chat: React.FC<ChatProps> = ({ projects, tasks, habits, userContext, onUpdateProject, onRememberFact, onManageTask, onUpdateHabit }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init-1',
      role: 'assistant',
      content: `Good morning, ${userContext.name}. I'm synced with your project database. What's the priority?`,
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, agentStatus]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);
    setAgentStatus("Analyzing Intent...");

    try {
      // Initialize Agent
      const agent = new AgentOrchestrator(process.env.API_KEY || '');
      
      // Execute (Simulating A2A communication delay)
      const currentState = { projects, tasks, habits, userContext };
      
      const result = await agent.processRequest(messages, text, currentState);
      
      // Handle Tool Calls (The Agent "Acting")
      if (result.toolCalls && result.toolCalls.length > 0) {
        for (const call of result.toolCalls) {
          const args = call.args;
          setAgentStatus(`Executing: ${call.name}`);
          
          await new Promise(r => setTimeout(r, 800)); // Artificial delay for UX "Thinking" feel

          if (call.name === 'updateProject') {
            onUpdateProject(args.projectName, args.status, args.updateContent, args.nextStep);
          } else if (call.name === 'rememberFact') {
            onRememberFact(args.fact);
          } else if (call.name === 'manageTask') {
            onManageTask(args.action, args.taskText, args.role, args.projectName);
          } else if (call.name === 'updateHabit') {
            onUpdateHabit(args.habitName, args.completed);
          }
        }
      }

      setAgentStatus("Synthesizing Response...");
      await new Promise(r => setTimeout(r, 400));

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: result.text,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: "I lost connection to the agent core.", timestamp: new Date() }]);
    } finally {
      setIsLoading(false);
      setAgentStatus(null);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] md:h-[calc(100vh-4rem)] max-w-4xl mx-auto">
      <header className="mb-6 flex-shrink-0">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <LucideBot className="w-8 h-8 text-accent-primary" />
          Agent Neural Link
        </h1>
        <p className="text-slate-400 text-sm">Direct line to your Chief of Staff agent.</p>
      </header>

      {/* Suggested Queries */}
      <div className="flex gap-3 overflow-x-auto pb-4 mb-4 scrollbar-hide flex-shrink-0">
        {SUGGESTED_QUERIES.map((query) => (
          <button
            key={query}
            onClick={() => handleSendMessage(query)}
            className="whitespace-nowrap px-4 py-2 bg-white/5 border border-white/10 rounded-full text-slate-300 text-xs hover:bg-accent-primary/10 hover:border-accent-primary/30 hover:text-white transition-all"
          >
            {query}
          </button>
        ))}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-6 min-h-0 custom-scrollbar">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''} animate-fade-in`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
              msg.role === 'user' 
                ? 'bg-slate-700' 
                : 'bg-gradient-to-br from-accent-primary to-blue-600 shadow-lg shadow-accent-primary/20'
            }`}>
              {msg.role === 'user' ? <LucideUser size={16} className="text-white" /> : <LucideSparkles size={16} className="text-white" />}
            </div>

            <div className={`max-w-[85%] space-y-2 ${msg.role === 'user' ? 'items-end flex flex-col' : ''}`}>
              <div className={`p-5 rounded-2xl text-sm leading-relaxed shadow-lg backdrop-blur-sm ${
                msg.role === 'user'
                  ? 'bg-white/10 text-white rounded-tr-sm'
                  : 'bg-black/40 border border-white/10 text-slate-200 rounded-tl-sm'
              }`}>
                {msg.role === 'assistant' ? (
                   <ReactMarkdown 
                    className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-strong:text-white"
                    components={{
                      strong: ({node, ...props}) => <span className="font-bold text-accent-secondary" {...props} />
                    }}
                   >
                     {msg.content}
                   </ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          </div>
        ))}
        
        {/* Agent Thinking State */}
        {(isLoading || agentStatus) && (
           <div className="flex gap-4 animate-fade-in">
              <div className="w-8 h-8" /> 
              <div className="bg-accent-primary/5 border border-accent-primary/20 p-4 rounded-xl flex items-center gap-4">
                 <div className="relative">
                    <LucideCpu size={20} className="text-accent-primary animate-pulse" />
                    <div className="absolute inset-0 bg-accent-primary blur-lg opacity-20 animate-pulse"></div>
                 </div>
                 <div className="flex flex-col">
                    <span className="text-xs font-bold text-accent-secondary uppercase tracking-wider mb-1">Agent Active</span>
                    <span className="text-sm text-slate-300 font-mono">{agentStatus || "Processing..."}</span>
                 </div>
              </div>
           </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="mt-4 pt-4 border-t border-white/5 flex-shrink-0 bg-transparent">
        <div className="flex gap-3 p-2 bg-black/40 border border-white/10 rounded-2xl focus-within:border-accent-primary/50 focus-within:bg-black/60 transition-all backdrop-blur-md">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(inputValue)}
            placeholder="Direct the agent (e.g., 'Update Project Phoenix status')..."
            className="flex-1 bg-transparent border-none text-white text-sm px-4 py-3 focus:outline-none placeholder:text-slate-600"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSendMessage(inputValue)}
            disabled={!inputValue.trim() || isLoading}
            className="px-6 py-2 bg-white text-black rounded-xl font-bold text-sm hover:bg-slate-200 hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <LucideSend size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;