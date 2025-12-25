import { Project, Task, Habit, UserContext } from './types';

export const INITIAL_CONTEXT: UserContext = {
  name: 'Pratap',
  title: 'COO & Founder',
  facts: [
    'COO of CodeStellar - Managing Operations',
    'Founder of Pratap AI - Building Personal Brand & Tools',
    'Founder of Civic Vigilance - Building MVP from scratch',
    'Project Manager for multiple client apps (Muay Thai, No Excuse, RSN)',
    'Focusing on discipline: Workout, Video Recording, Writing',
    'Prefers "Atomic Habits" style small wins'
  ]
};

export const INITIAL_PROJECTS: Project[] = [
  {
    id: 'p1',
    name: 'Muay Thai Tickets',
    role: 'PM',
    description: 'Client App & Website Development',
    status: 'on_track',
    lastUpdate: 'Yesterday',
    nextStep: 'Review QA feedback on ticket booking flow',
    updates: []
  },
  {
    id: 'p2',
    name: 'No Excuse',
    role: 'PM',
    description: 'Client App Development',
    status: 'delayed',
    lastUpdate: '2 days ago',
    nextStep: 'Chase dev team for API integration',
    updates: []
  },
  {
    id: 'p3',
    name: 'PlantOgram',
    role: 'PM',
    description: 'Marketing & WordPress Dev',
    status: 'at_risk',
    lastUpdate: '3 days ago',
    nextStep: 'Approve new landing page copy',
    updates: []
  },
  {
    id: 'p4',
    name: 'Pratap.ai',
    role: 'Founder',
    description: 'Personal Brand & Tooling',
    status: 'on_track',
    lastUpdate: 'Today',
    nextStep: 'Script next video on AI Agents',
    updates: []
  },
  {
    id: 'p5',
    name: 'RSN',
    role: 'PM',
    description: 'Client App Development',
    status: 'maintenance',
    lastUpdate: 'Last week',
    nextStep: 'Monthly maintenance check',
    updates: []
  },
  {
    id: 'p6',
    name: 'Civic Vigilance',
    role: 'Founder',
    description: 'Community App (Building from scratch)',
    status: 'on_track',
    lastUpdate: 'Yesterday',
    nextStep: 'Database schema finalization',
    updates: []
  },
  {
    id: 'p7',
    name: 'CodeStellar Ops',
    role: 'COO',
    description: 'Company Operations',
    status: 'on_track',
    lastUpdate: 'Today',
    nextStep: 'Review Q1 hiring plan',
    updates: []
  }
];

export const INITIAL_TASKS: Task[] = [
  { id: 't1', text: 'Review QA for Muay Thai', projectId: 'p1', role: 'PM', isCompleted: false, priority: 'high' },
  { id: 't2', text: 'Write script for YouTube', projectId: 'p4', role: 'Founder', isCompleted: false, priority: 'medium' },
  { id: 't3', text: 'Update PlantOgram client', projectId: 'p3', role: 'PM', isCompleted: false, priority: 'high' },
  { id: 't4', text: 'Finalize Civic Vigilance DB Schema', projectId: 'p6', role: 'Founder', isCompleted: false, priority: 'high' },
  { id: 't5', text: 'Approve Payroll', projectId: 'p7', role: 'COO', isCompleted: true, priority: 'high' },
];

export const INITIAL_HABITS: Habit[] = [
  { id: 'h1', name: 'Workout / Gym', streak: 4, completedToday: false, category: 'health' },
  { id: 'h2', name: 'Record Video', streak: 1, completedToday: false, category: 'content' },
  { id: 'h3', name: 'Write 500 words', streak: 12, completedToday: true, category: 'learning' },
];

export const MOCK_INTEGRATIONS = [
  { id: '1', name: 'Gmail', icon: '📧', status: 'connected', lastSync: '2m ago', dataPoints: 1200 },
  { id: '2', name: 'Slack', icon: '💬', status: 'connected', lastSync: '5m ago', dataPoints: 850 },
  { id: '3', name: 'Notion', icon: '📝', status: 'syncing', lastSync: 'Syncing...', dataPoints: 340 },
  { id: '4', name: 'Github', icon: '💻', status: 'connected', lastSync: '1h ago', dataPoints: 5600 },
];

export const MOCK_DECISIONS = [
  {
    id: 'd1',
    status: 'completed',
    date: 'Oct 12',
    title: 'Delay No Excuse Launch',
    reason: 'Critical API bug found in late QA.',
    expectedOutcome: 'Launch stable version 1 week later.',
    actualOutcomes: [
      { period: 'Week 1', result: '4.8 Star Rating' },
      { period: 'Month 1', result: '90% Retention' }
    ]
  },
  {
    id: 'd2',
    status: 'tracking',
    date: 'Oct 28',
    title: 'Switch to Gemini 2.5',
    reason: 'Better reasoning for complex PM tasks.',
    expectedOutcome: 'Faster response times and better context handling.',
    actualOutcomes: [
      { period: 'Day 1', result: '30% Faster' }
    ]
  }
];