/**
 * Alfred API Services
 * Provides typed API calls for all Alfred endpoints
 */

import client from './client';

// ============================================
// TYPES
// ============================================

export interface Project {
    project_id: string;
    name: string;
    organization: string;
    role: string;
    status: string;
    description: string;
    task_count: number;
    completed_task_count: number;
    health_score: number;
    created_at: string;
}

export interface Task {
    task_id: string;
    project_id: string | null;
    project_name: string | null;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    status: 'pending' | 'in_progress' | 'blocked' | 'completed' | 'cancelled';
    due_date: string | null;
    tags: string[];
    created_at: string;
}

export interface Habit {
    habit_id: string;
    name: string;
    description: string;
    frequency: string;
    time_preference: string | null;
    current_streak: number;
    best_streak: number;
    total_completions: number;
    last_logged: string | null;
    motivation: string;
    category: string;
    active: boolean;
    reminder_enabled: boolean;
}

export interface DashboardData {
    date: string;
    greeting: string;
    focus: {
        high_priority_tasks: Task[];
        due_today: Task[];
        overdue: Task[];
    };
    habits: {
        pending: Habit[];
        completed: Habit[];
        total_streaks: number;
    };
    projects: {
        active_count: number;
        needing_attention: Project[];
    };
    stats: {
        tasks_pending: number;
        tasks_overdue: number;
        habits_completed_today: number;
        habits_pending_today: number;
    };
}

export interface ProjectUpdate {
    update_id: string;
    content: string;
    update_type: string;
    action_items: string[];
    blockers: string[];
    created_at: string;
}

// ============================================
// DASHBOARD API
// ============================================

export const dashboardApi = {
    getToday: async (): Promise<DashboardData> => {
        const response = await client.get('/dashboard/today');
        return response.data;
    },

    getStats: async () => {
        const response = await client.get('/dashboard/stats');
        return response.data;
    },

    getMorningBriefing: async () => {
        const response = await client.get('/dashboard/briefing/morning');
        return response.data;
    },

    getEveningReview: async () => {
        const response = await client.get('/dashboard/briefing/evening');
        return response.data;
    },

    getProjectHealth: async () => {
        const response = await client.get('/dashboard/project-health');
        return response.data;
    }
};

// ============================================
// PROJECTS API
// ============================================

export const projectsApi = {
    list: async (status?: string): Promise<{ projects: Project[] }> => {
        const params = status ? { status } : {};
        const response = await client.get('/projects', { params });
        return response.data;
    },

    get: async (projectId: string): Promise<Project> => {
        const response = await client.get(`/projects/${projectId}`);
        return response.data;
    },

    create: async (data: {
        name: string;
        organization?: string;
        role?: string;
        description?: string;
    }) => {
        const response = await client.post('/projects', data);
        return response.data;
    },

    update: async (projectId: string, data: Partial<Project>) => {
        const response = await client.put(`/projects/${projectId}`, data);
        return response.data;
    },

    delete: async (projectId: string) => {
        const response = await client.delete(`/projects/${projectId}`);
        return response.data;
    },

    addUpdate: async (projectId: string, data: {
        content: string;
        update_type?: string;
        action_items?: string[];
        blockers?: string[];
    }) => {
        const response = await client.post(`/projects/${projectId}/updates`, data);
        return response.data;
    },

    getUpdates: async (projectId: string, limit = 20): Promise<{ updates: ProjectUpdate[] }> => {
        const response = await client.get(`/projects/${projectId}/updates`, { params: { limit } });
        return response.data;
    },

    getTasks: async (projectId: string, status?: string): Promise<{ tasks: Task[] }> => {
        const params = status ? { status } : {};
        const response = await client.get(`/projects/${projectId}/tasks`, { params });
        return response.data;
    }
};

// ============================================
// TASKS API
// ============================================

export const tasksApi = {
    list: async (filters?: {
        project_id?: string;
        status?: string;
        priority?: string;
    }): Promise<{ tasks: Task[] }> => {
        const response = await client.get('/tasks', { params: filters });
        return response.data;
    },

    getToday: async (): Promise<{ overdue: Task[]; due_today: Task[]; total: number }> => {
        const response = await client.get('/tasks/today');
        return response.data;
    },

    getPending: async (): Promise<{
        pending: Task[];
        in_progress: Task[];
        blocked: Task[];
        total: number;
    }> => {
        const response = await client.get('/tasks/pending');
        return response.data;
    },

    get: async (taskId: string): Promise<Task> => {
        const response = await client.get(`/tasks/${taskId}`);
        return response.data;
    },

    create: async (data: {
        title: string;
        project_id?: string;
        description?: string;
        priority?: string;
        due_date?: string;
        tags?: string[];
    }) => {
        const response = await client.post('/tasks', data);
        return response.data;
    },

    update: async (taskId: string, data: Partial<Task>) => {
        const response = await client.put(`/tasks/${taskId}`, data);
        return response.data;
    },

    complete: async (taskId: string) => {
        const response = await client.post(`/tasks/${taskId}/complete`);
        return response.data;
    },

    start: async (taskId: string) => {
        const response = await client.post(`/tasks/${taskId}/start`);
        return response.data;
    },

    block: async (taskId: string, blocker?: string) => {
        const params = blocker ? { blocker } : {};
        const response = await client.post(`/tasks/${taskId}/block`, null, { params });
        return response.data;
    },

    delete: async (taskId: string) => {
        const response = await client.delete(`/tasks/${taskId}`);
        return response.data;
    }
};

// ============================================
// HABITS API
// ============================================

export const habitsApi = {
    list: async (activeOnly = true): Promise<{ habits: Habit[] }> => {
        const response = await client.get('/habits', { params: { active_only: activeOnly } });
        return response.data;
    },

    getToday: async (): Promise<{
        pending: Habit[];
        completed: Habit[];
        total_streaks: number;
    }> => {
        const response = await client.get('/habits/today');
        return response.data;
    },

    getStreaks: async (): Promise<{ streaks: Array<{
        habit_id: string;
        name: string;
        current_streak: number;
        best_streak: number;
        total_completions: number;
    }> }> => {
        const response = await client.get('/habits/streaks');
        return response.data;
    },

    get: async (habitId: string): Promise<Habit> => {
        const response = await client.get(`/habits/${habitId}`);
        return response.data;
    },

    create: async (data: {
        name: string;
        description?: string;
        frequency?: string;
        time_preference?: string;
        motivation?: string;
        category?: string;
    }) => {
        const response = await client.post('/habits', data);
        return response.data;
    },

    update: async (habitId: string, data: Partial<Habit>) => {
        const response = await client.put(`/habits/${habitId}`, data);
        return response.data;
    },

    log: async (habitId: string, data?: {
        logged_date?: string;
        notes?: string;
        duration_minutes?: number;
    }): Promise<{
        message: string;
        current_streak: number;
        best_streak: number;
        total_completions: number;
    }> => {
        const response = await client.post(`/habits/${habitId}/log`, data || {});
        return response.data;
    },

    getHistory: async (habitId: string, startDate?: string, endDate?: string) => {
        const params: any = {};
        if (startDate) params.start_date = startDate;
        if (endDate) params.end_date = endDate;
        const response = await client.get(`/habits/${habitId}/history`, { params });
        return response.data;
    },

    delete: async (habitId: string) => {
        const response = await client.delete(`/habits/${habitId}`);
        return response.data;
    }
};

// ============================================
// CHAT API
// ============================================

export const chatApi = {
    send: async (message: string, context?: any): Promise<{ response: string; metadata?: any }> => {
        const response = await client.post('/chat', { message, context });
        return response.data;
    }
};

// ============================================
// PROFILE API
// ============================================

export const profileApi = {
    get: async () => {
        const response = await client.get('/auth/profile');
        return response.data;
    },

    update: async (data: {
        bio?: string;
        work_type?: string;
        personality_prompt?: string;
        interaction_type?: string;
        morning_briefing_time?: string;
        evening_review_time?: string;
    }) => {
        const response = await client.put('/auth/profile', data);
        return response.data;
    }
};

// ============================================
// NOTIFICATIONS API
// ============================================

export interface NotificationPreferences {
    morning_briefing: boolean;
    evening_review: boolean;
    habit_reminders: boolean;
    task_due_reminders: boolean;
    project_nudges: boolean;
}

export interface ScheduledNotification {
    notification_id: string;
    notification_type: string;
    title: string;
    content: string;
    trigger_time: string;
    status: string;
    created_at: string;
}

// ============================================
// PROACTIVE API
// ============================================

export interface ProactiveCard {
    id: string;
    type: 'warning' | 'insight' | 'reminder' | 'celebration';
    title: string;
    description: string;
    actions: string[];
    entity_id?: string;
    entity_type?: 'task' | 'habit' | 'project' | 'event';
    priority: number;
    created_at: string;
}

export const proactiveApi = {
    getCards: async (limit = 10): Promise<ProactiveCard[]> => {
        const response = await client.get('/proactive/cards', { params: { limit } });
        return response.data;
    },

    dismiss: async (cardId: string, reason?: string) => {
        const response = await client.post('/proactive/dismiss', { card_id: cardId, reason });
        return response.data;
    },

    snooze: async (cardId: string, snoozeUntil?: string) => {
        const response = await client.post('/proactive/snooze', { card_id: cardId, snooze_until: snoozeUntil });
        return response.data;
    },

    act: async (cardId: string, action: string) => {
        const response = await client.post(`/proactive/act/${cardId}`, null, { params: { action } });
        return response.data;
    }
};

// ============================================
// KNOWLEDGE API (Entity Management)
// ============================================

export interface Entity {
    entity_id: string;
    entity_type: 'person' | 'company' | 'topic';
    name: string;
    properties: Record<string, any>;
    relationships: Array<{
        type: string;
        target_id: string;
        target_name: string;
    }>;
    created_at: string;
    updated_at: string;
}

export interface KnowledgeStats {
    people: number;
    companies: number;
    projects: number;
    preferences: number;
    total_facts: number;
}

export const knowledgeApi = {
    getStats: async (): Promise<KnowledgeStats> => {
        const response = await client.get('/knowledge/stats');
        return response.data;
    },

    getPeople: async (limit = 50): Promise<{ entities: Entity[] }> => {
        const response = await client.get('/knowledge/entities', {
            params: { entity_type: 'person', limit },
        });
        return response.data;
    },

    getCompanies: async (limit = 50): Promise<{ entities: Entity[] }> => {
        const response = await client.get('/knowledge/entities', {
            params: { entity_type: 'company', limit },
        });
        return response.data;
    },

    getEntity: async (entityId: string): Promise<Entity> => {
        const response = await client.get(`/knowledge/entities/${entityId}`);
        return response.data;
    },

    search: async (query: string): Promise<{ entities: Entity[] }> => {
        const response = await client.get('/knowledge/search', {
            params: { q: query },
        });
        return response.data;
    },

    getPreferences: async (): Promise<{
        preferences: Array<{
            key: string;
            value: string;
            confidence: number;
            source: string;
        }>;
    }> => {
        const response = await client.get('/knowledge/preferences');
        return response.data;
    },
};

// ============================================
// NOTIFICATIONS API
// ============================================

export const notificationsApi = {
    registerToken: async (pushToken: string, deviceType: string = 'expo') => {
        const response = await client.post('/notifications/register-token', {
            push_token: pushToken,
            device_type: deviceType,
        });
        return response.data;
    },

    unregisterToken: async (deviceType: string = 'expo') => {
        const response = await client.delete('/notifications/unregister-token', {
            params: { device_type: deviceType },
        });
        return response.data;
    },

    getPreferences: async (): Promise<NotificationPreferences> => {
        const response = await client.get('/notifications/preferences');
        return response.data;
    },

    updatePreferences: async (preferences: NotificationPreferences) => {
        const response = await client.put('/notifications/preferences', preferences);
        return response.data;
    },

    getPending: async (): Promise<ScheduledNotification[]> => {
        const response = await client.get('/notifications/pending');
        return response.data;
    },

    markRead: async (notificationId: string) => {
        const response = await client.post(`/notifications/${notificationId}/read`);
        return response.data;
    },

    dismiss: async (notificationId: string) => {
        const response = await client.post(`/notifications/${notificationId}/dismiss`);
        return response.data;
    },

    sendTest: async () => {
        const response = await client.post('/notifications/test');
        return response.data;
    }
};

// ============================================
// VOICE API
// ============================================

export interface VoiceTranscription {
    text: string;
    confidence: number;
    duration_ms: number;
}

export interface VoiceChatResponse {
    transcription: VoiceTranscription;
    response: string;
    thinking_steps?: Array<{
        step: string;
        status: 'completed' | 'in_progress' | 'pending';
        detail?: string;
    }>;
    actions_taken?: Array<{
        type: string;
        description: string;
        entity_id?: string;
    }>;
}

// ============================================
// EVENING REVIEW API
// ============================================

export interface EveningReviewData {
    incomplete_tasks: Task[];
    completed_tasks: Task[];
    habits_completed: number;
    habits_pending: number;
    suggested_accomplishments: string[];
}

export interface EveningReviewSubmission {
    accomplishments: string[];
    blockers: string[];
    tomorrow_focus: string[];
    mood: 'great' | 'good' | 'okay' | 'tired' | 'stressed';
    tasks_to_move: string[]; // task IDs to move to tomorrow
    notes?: string;
}

export interface EveningReviewResponse {
    message: string;
    tasks_moved: number;
    review_id: string;
}

export const eveningReviewApi = {
    /**
     * Get data needed for evening review (incomplete tasks, today's completions)
     */
    getData: async (): Promise<EveningReviewData> => {
        const response = await client.get('/proactive/evening-review/data');
        return response.data;
    },

    /**
     * Submit evening review reflection
     */
    submit: async (data: EveningReviewSubmission): Promise<EveningReviewResponse> => {
        const response = await client.post('/proactive/evening-review/submit', data);
        return response.data;
    },

    /**
     * Move specific tasks to tomorrow
     */
    moveTasks: async (taskIds: string[]): Promise<{ moved: number }> => {
        const response = await client.post('/proactive/evening-review/move-tasks', {
            task_ids: taskIds,
        });
        return response.data;
    },

    /**
     * Get evening review history
     */
    getHistory: async (limit = 7): Promise<Array<{
        date: string;
        mood: string;
        accomplishments: string[];
        review_id: string;
    }>> => {
        const response = await client.get('/proactive/evening-review/history', {
            params: { limit },
        });
        return response.data;
    },
};

export const voiceApi = {
    /**
     * Transcribe audio to text using Whisper
     */
    transcribe: async (audioBase64: string): Promise<VoiceTranscription> => {
        const response = await client.post('/voice/transcribe', {
            audio: audioBase64,
            format: 'wav',
        });
        return response.data;
    },

    /**
     * Send voice message and get response
     * Combines transcription + chat in one call
     */
    chat: async (audioBase64: string): Promise<VoiceChatResponse> => {
        const response = await client.post('/voice/chat', {
            audio: audioBase64,
            format: 'wav',
        });
        return response.data;
    },

    /**
     * Send text and get response with thinking steps (streaming simulation)
     */
    chatWithSteps: async (
        message: string,
        onStep?: (step: { step: string; status: string }) => void
    ): Promise<{ response: string; steps: any[] }> => {
        // This would use SSE/WebSocket for real streaming
        // For now, just use the regular chat endpoint
        const response = await client.post('/chat', { message });
        return {
            response: response.data.response,
            steps: [],
        };
    },
};
