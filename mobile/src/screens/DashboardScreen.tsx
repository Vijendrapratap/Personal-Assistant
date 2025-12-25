import React, { useState, useEffect, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    RefreshControl,
    TouchableOpacity,
    ActivityIndicator,
} from 'react-native';
import { dashboardApi, tasksApi, habitsApi, DashboardData, Task, Habit } from '../api/services';

interface Props {
    navigation: any;
}

export default function DashboardScreen({ navigation }: Props) {
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [dashboard, setDashboard] = useState<DashboardData | null>(null);
    const [error, setError] = useState<string | null>(null);

    const loadData = async () => {
        try {
            setError(null);
            const data = await dashboardApi.getToday();
            setDashboard(data);
        } catch (err: any) {
            setError(err.message || 'Failed to load dashboard');
            console.error(err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const onRefresh = useCallback(() => {
        setRefreshing(true);
        loadData();
    }, []);

    const handleCompleteTask = async (taskId: string) => {
        try {
            await tasksApi.complete(taskId);
            loadData();
        } catch (err) {
            console.error(err);
        }
    };

    const handleLogHabit = async (habitId: string) => {
        try {
            await habitsApi.log(habitId);
            loadData();
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" color="#1a73e8" />
                <Text style={styles.loadingText}>Loading your day...</Text>
            </View>
        );
    }

    if (error) {
        return (
            <View style={styles.centered}>
                <Text style={styles.errorText}>{error}</Text>
                <TouchableOpacity style={styles.retryButton} onPress={loadData}>
                    <Text style={styles.retryButtonText}>Retry</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <ScrollView
            style={styles.container}
            refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
        >
            {/* Header */}
            <View style={styles.header}>
                <Text style={styles.greeting}>{dashboard?.greeting || 'Good day'}, Sir</Text>
                <Text style={styles.date}>{new Date().toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric'
                })}</Text>
            </View>

            {/* Stats Cards */}
            <View style={styles.statsRow}>
                <View style={[styles.statCard, styles.statPending]}>
                    <Text style={styles.statNumber}>{dashboard?.stats.tasks_pending || 0}</Text>
                    <Text style={styles.statLabel}>Tasks Pending</Text>
                </View>
                <View style={[styles.statCard, styles.statCompleted]}>
                    <Text style={styles.statNumber}>{dashboard?.stats.habits_completed_today || 0}/{(dashboard?.habits.pending.length || 0) + (dashboard?.habits.completed.length || 0)}</Text>
                    <Text style={styles.statLabel}>Habits Today</Text>
                </View>
                <View style={[styles.statCard, styles.statProjects]}>
                    <Text style={styles.statNumber}>{dashboard?.projects.active_count || 0}</Text>
                    <Text style={styles.statLabel}>Active Projects</Text>
                </View>
            </View>

            {/* Overdue Tasks */}
            {dashboard?.focus.overdue && dashboard.focus.overdue.length > 0 && (
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <Text style={[styles.sectionTitle, styles.overdueTitle]}>Overdue</Text>
                        <Text style={styles.sectionCount}>{dashboard.focus.overdue.length}</Text>
                    </View>
                    {dashboard.focus.overdue.slice(0, 3).map((task) => (
                        <TaskCard
                            key={task.task_id}
                            task={task}
                            onComplete={() => handleCompleteTask(task.task_id)}
                            onPress={() => navigation.navigate('Tasks')}
                            isOverdue
                        />
                    ))}
                </View>
            )}

            {/* Priority Tasks */}
            {dashboard?.focus.high_priority_tasks && dashboard.focus.high_priority_tasks.length > 0 && (
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <Text style={styles.sectionTitle}>Priority Tasks</Text>
                        <TouchableOpacity onPress={() => navigation.navigate('Tasks')}>
                            <Text style={styles.seeAll}>See All</Text>
                        </TouchableOpacity>
                    </View>
                    {dashboard.focus.high_priority_tasks.slice(0, 3).map((task) => (
                        <TaskCard
                            key={task.task_id}
                            task={task}
                            onComplete={() => handleCompleteTask(task.task_id)}
                            onPress={() => navigation.navigate('Tasks')}
                        />
                    ))}
                </View>
            )}

            {/* Habits */}
            <View style={styles.section}>
                <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>Today's Habits</Text>
                    <TouchableOpacity onPress={() => navigation.navigate('Habits')}>
                        <Text style={styles.seeAll}>See All</Text>
                    </TouchableOpacity>
                </View>
                {dashboard?.habits.pending.map((habit) => (
                    <HabitCard
                        key={habit.habit_id}
                        habit={habit}
                        completed={false}
                        onLog={() => handleLogHabit(habit.habit_id)}
                    />
                ))}
                {dashboard?.habits.completed.map((habit) => (
                    <HabitCard
                        key={habit.habit_id}
                        habit={habit}
                        completed={true}
                        onLog={() => {}}
                    />
                ))}
                {(!dashboard?.habits.pending.length && !dashboard?.habits.completed.length) && (
                    <Text style={styles.emptyText}>No habits configured yet</Text>
                )}
            </View>

            {/* Projects Needing Attention */}
            {dashboard?.projects.needing_attention && dashboard.projects.needing_attention.length > 0 && (
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <Text style={[styles.sectionTitle, styles.warningTitle]}>Projects Need Updates</Text>
                    </View>
                    {dashboard.projects.needing_attention.slice(0, 3).map((project: any) => (
                        <TouchableOpacity
                            key={project.project_id}
                            style={styles.projectCard}
                            onPress={() => navigation.navigate('Projects')}
                        >
                            <View style={styles.projectInfo}>
                                <Text style={styles.projectName}>{project.name}</Text>
                                <Text style={styles.projectOrg}>{project.organization}</Text>
                            </View>
                            <Text style={styles.projectDays}>
                                {project.days_since_update ? `${project.days_since_update}d ago` : 'No updates'}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </View>
            )}

            <View style={{ height: 100 }} />
        </ScrollView>
    );
}

// Task Card Component
function TaskCard({ task, onComplete, onPress, isOverdue = false }: {
    task: Task;
    onComplete: () => void;
    onPress: () => void;
    isOverdue?: boolean;
}) {
    return (
        <TouchableOpacity style={[styles.taskCard, isOverdue && styles.overdueCard]} onPress={onPress}>
            <TouchableOpacity style={styles.checkbox} onPress={onComplete}>
                <View style={styles.checkboxInner} />
            </TouchableOpacity>
            <View style={styles.taskContent}>
                <Text style={styles.taskTitle}>{task.title}</Text>
                <View style={styles.taskMeta}>
                    {task.project_name && (
                        <Text style={styles.taskProject}>[{task.project_name}]</Text>
                    )}
                    <Text style={[styles.taskPriority, styles[`priority_${task.priority}`]]}>
                        {task.priority.toUpperCase()}
                    </Text>
                </View>
            </View>
        </TouchableOpacity>
    );
}

// Habit Card Component
function HabitCard({ habit, completed, onLog }: {
    habit: Habit;
    completed: boolean;
    onLog: () => void;
}) {
    return (
        <View style={[styles.habitCard, completed && styles.habitCompleted]}>
            <TouchableOpacity
                style={[styles.habitCheckbox, completed && styles.habitChecked]}
                onPress={onLog}
                disabled={completed}
            >
                {completed && <Text style={styles.checkmark}>✓</Text>}
            </TouchableOpacity>
            <View style={styles.habitContent}>
                <Text style={[styles.habitName, completed && styles.habitNameCompleted]}>
                    {habit.name}
                </Text>
                <Text style={styles.habitStreak}>
                    🔥 {habit.current_streak} day streak
                </Text>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    centered: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
    },
    loadingText: {
        marginTop: 10,
        color: '#666',
    },
    errorText: {
        color: '#d32f2f',
        marginBottom: 20,
    },
    retryButton: {
        backgroundColor: '#1a73e8',
        paddingHorizontal: 20,
        paddingVertical: 10,
        borderRadius: 5,
    },
    retryButtonText: {
        color: '#fff',
        fontWeight: '600',
    },
    header: {
        padding: 20,
        backgroundColor: '#1a73e8',
    },
    greeting: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#fff',
    },
    date: {
        fontSize: 14,
        color: 'rgba(255,255,255,0.8)',
        marginTop: 5,
    },
    statsRow: {
        flexDirection: 'row',
        padding: 15,
        marginTop: -20,
    },
    statCard: {
        flex: 1,
        backgroundColor: '#fff',
        borderRadius: 10,
        padding: 15,
        marginHorizontal: 5,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    statPending: {
        borderTopColor: '#ff9800',
        borderTopWidth: 3,
    },
    statCompleted: {
        borderTopColor: '#4caf50',
        borderTopWidth: 3,
    },
    statProjects: {
        borderTopColor: '#1a73e8',
        borderTopWidth: 3,
    },
    statNumber: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
    },
    statLabel: {
        fontSize: 11,
        color: '#666',
        marginTop: 5,
        textAlign: 'center',
    },
    section: {
        margin: 15,
        marginTop: 10,
    },
    sectionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 10,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#333',
    },
    sectionCount: {
        backgroundColor: '#d32f2f',
        color: '#fff',
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 10,
        fontSize: 12,
        fontWeight: '600',
    },
    overdueTitle: {
        color: '#d32f2f',
    },
    warningTitle: {
        color: '#ff9800',
    },
    seeAll: {
        color: '#1a73e8',
        fontSize: 14,
    },
    taskCard: {
        flexDirection: 'row',
        backgroundColor: '#fff',
        borderRadius: 10,
        padding: 15,
        marginBottom: 10,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
    overdueCard: {
        borderLeftColor: '#d32f2f',
        borderLeftWidth: 3,
    },
    checkbox: {
        width: 24,
        height: 24,
        borderRadius: 12,
        borderWidth: 2,
        borderColor: '#ccc',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    checkboxInner: {
        width: 12,
        height: 12,
        borderRadius: 6,
    },
    taskContent: {
        flex: 1,
    },
    taskTitle: {
        fontSize: 16,
        color: '#333',
        marginBottom: 4,
    },
    taskMeta: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    taskProject: {
        fontSize: 12,
        color: '#666',
        marginRight: 8,
    },
    taskPriority: {
        fontSize: 10,
        fontWeight: '600',
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 3,
    },
    priority_high: {
        backgroundColor: '#ffebee',
        color: '#d32f2f',
    },
    priority_medium: {
        backgroundColor: '#fff3e0',
        color: '#ff9800',
    },
    priority_low: {
        backgroundColor: '#e3f2fd',
        color: '#1976d2',
    },
    habitCard: {
        flexDirection: 'row',
        backgroundColor: '#fff',
        borderRadius: 10,
        padding: 15,
        marginBottom: 10,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
    habitCompleted: {
        backgroundColor: '#e8f5e9',
    },
    habitCheckbox: {
        width: 28,
        height: 28,
        borderRadius: 14,
        borderWidth: 2,
        borderColor: '#4caf50',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    habitChecked: {
        backgroundColor: '#4caf50',
    },
    checkmark: {
        color: '#fff',
        fontWeight: 'bold',
    },
    habitContent: {
        flex: 1,
    },
    habitName: {
        fontSize: 16,
        color: '#333',
    },
    habitNameCompleted: {
        textDecorationLine: 'line-through',
        color: '#666',
    },
    habitStreak: {
        fontSize: 12,
        color: '#ff9800',
        marginTop: 4,
    },
    projectCard: {
        flexDirection: 'row',
        backgroundColor: '#fff',
        borderRadius: 10,
        padding: 15,
        marginBottom: 10,
        alignItems: 'center',
        justifyContent: 'space-between',
        borderLeftColor: '#ff9800',
        borderLeftWidth: 3,
    },
    projectInfo: {
        flex: 1,
    },
    projectName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
    },
    projectOrg: {
        fontSize: 12,
        color: '#666',
        marginTop: 2,
    },
    projectDays: {
        fontSize: 12,
        color: '#ff9800',
        fontWeight: '600',
    },
    emptyText: {
        color: '#999',
        fontStyle: 'italic',
        textAlign: 'center',
        padding: 20,
    },
});
