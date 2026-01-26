/**
 * DoScreen - Tasks + Habits Unified View
 * Shows all tasks and habits in a unified, conversation-first interface
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  useWindowDimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../theme';
import { Text, Card } from '../../components/common';
import { TaskCard } from '../../components/tasks';
import { HabitChip, HabitChipInline } from '../../components/habits';
import { ConversationInput } from '../../components/input';
import { tasksApi, habitsApi, projectsApi, Task, Habit, Project } from '../../api/services';

type FilterType = 'all' | 'today' | 'overdue' | 'in_progress';

interface DoScreenProps {
  navigation: any;
}

export default function DoScreen({ navigation }: DoScreenProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const { width: screenWidth } = useWindowDimensions();

  // Responsive values
  const horizontalPadding = Math.max(16, Math.min(20, screenWidth * 0.05));
  // Bottom spacing: input container (~70) + tab bar (80) + safe area
  const bottomPadding = 70 + 80 + insets.bottom;

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<FilterType>('today');

  // Data state
  const [tasks, setTasks] = useState<Task[]>([]);
  const [habits, setHabits] = useState<Habit[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [todayHabits, setTodayHabits] = useState<{
    pending: Habit[];
    completed: Habit[];
  }>({ pending: [], completed: [] });

  const loadData = async () => {
    try {
      const [tasksData, habitsData, projectsData, todayHabitsData] = await Promise.all([
        tasksApi.list(),
        habitsApi.list(true),
        projectsApi.list('active'),
        habitsApi.getToday(),
      ]);

      setTasks(tasksData.tasks || []);
      setHabits(habitsData.habits || []);
      setProjects(projectsData.projects || []);
      setTodayHabits({
        pending: todayHabitsData.pending || [],
        completed: todayHabitsData.completed || [],
      });
    } catch (err) {
      console.error('Failed to load data:', err);
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

  // Filter tasks based on selected filter
  const getFilteredTasks = (): Task[] => {
    const today = new Date().toISOString().split('T')[0];

    switch (filter) {
      case 'today':
        return tasks.filter((t) => {
          if (t.status === 'completed' || t.status === 'cancelled') return false;
          if (!t.due_date) return false;
          return t.due_date.startsWith(today);
        });
      case 'overdue':
        return tasks.filter((t) => {
          if (t.status === 'completed' || t.status === 'cancelled') return false;
          if (!t.due_date) return false;
          return t.due_date < today;
        });
      case 'in_progress':
        return tasks.filter((t) => t.status === 'in_progress');
      case 'all':
      default:
        return tasks.filter(
          (t) => t.status !== 'completed' && t.status !== 'cancelled'
        );
    }
  };

  const filteredTasks = getFilteredTasks();

  // Task actions
  const handleCompleteTask = async (taskId: string) => {
    try {
      await tasksApi.complete(taskId);
      loadData();
    } catch (err) {
      console.error('Failed to complete task:', err);
    }
  };

  const handleStartTask = async (taskId: string) => {
    try {
      await tasksApi.start(taskId);
      loadData();
    } catch (err) {
      console.error('Failed to start task:', err);
    }
  };

  // Habit actions
  const handleLogHabit = async (habitId: string) => {
    try {
      await habitsApi.log(habitId);
      loadData();
    } catch (err) {
      console.error('Failed to log habit:', err);
    }
  };

  // Conversation input handler
  const handleConversationSubmit = async (message: string) => {
    // This would integrate with the chat/AI system to create tasks
    console.log('Create task from message:', message);
    // For now, just reload data
    loadData();
  };

  // Get filter counts
  const getFilterCount = (filterType: FilterType): number => {
    const today = new Date().toISOString().split('T')[0];
    const activeTasks = tasks.filter(
      (t) => t.status !== 'completed' && t.status !== 'cancelled'
    );

    switch (filterType) {
      case 'today':
        return activeTasks.filter((t) => t.due_date?.startsWith(today)).length;
      case 'overdue':
        return activeTasks.filter((t) => t.due_date && t.due_date < today).length;
      case 'in_progress':
        return tasks.filter((t) => t.status === 'in_progress').length;
      case 'all':
      default:
        return activeTasks.length;
    }
  };

  // Check if task is overdue
  const isTaskOverdue = (task: Task): boolean => {
    if (!task.due_date) return false;
    const today = new Date().toISOString().split('T')[0];
    return task.due_date < today;
  };

  if (loading) {
    return (
      <View
        style={[styles.loadingContainer, { backgroundColor: theme.colors.bg }]}
      >
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text variant="body" color="secondary" style={styles.loadingText}>
          Loading your tasks...
        </Text>
      </View>
    );
  }

  const allHabits = [...todayHabits.pending, ...todayHabits.completed];
  const pendingHabitsCount = todayHabits.pending.length;
  const completedHabitsCount = todayHabits.completed.length;

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.content,
          {
            paddingTop: insets.top + 16,
            paddingBottom: bottomPadding,
            paddingHorizontal: horizontalPadding,
          },
        ]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text variant="h2">Do</Text>
          <Text variant="body" color="secondary" style={styles.subtitle}>
            {filteredTasks.length} tasks · {pendingHabitsCount} habits pending
          </Text>
        </View>

        {/* Habits Row */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text variant="label" color="secondary">
              TODAY'S HABITS
            </Text>
            <Text variant="bodySmall" color="tertiary">
              {completedHabitsCount}/{allHabits.length}
            </Text>
          </View>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.habitsScroll}
            contentContainerStyle={styles.habitsContainer}
          >
            {allHabits.map((habit) => {
              const isCompleted = todayHabits.completed.some(
                (h) => h.habit_id === habit.habit_id
              );
              return (
                <HabitChip
                  key={habit.habit_id}
                  id={habit.habit_id}
                  name={habit.name}
                  category={habit.category}
                  currentStreak={habit.current_streak}
                  isCompleted={isCompleted}
                  onPress={() => !isCompleted && handleLogHabit(habit.habit_id)}
                  size="md"
                />
              );
            })}
            {allHabits.length === 0 && (
              <View style={styles.emptyHabits}>
                <Text variant="body" color="tertiary">
                  No habits scheduled for today
                </Text>
              </View>
            )}
          </ScrollView>
        </View>

        {/* Filter Tabs */}
        <View style={styles.section}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.filterScroll}
            contentContainerStyle={styles.filterContainer}
          >
            {(['today', 'all', 'in_progress', 'overdue'] as FilterType[]).map(
              (f) => (
                <TouchableOpacity
                  key={f}
                  style={[
                    styles.filterTab,
                    {
                      backgroundColor:
                        filter === f
                          ? theme.colors.primary
                          : theme.colors.bgSurface,
                      borderColor:
                        filter === f
                          ? theme.colors.primary
                          : theme.colors.border,
                    },
                  ]}
                  onPress={() => setFilter(f)}
                >
                  <Text
                    style={[
                      styles.filterText,
                      {
                        color:
                          filter === f ? '#fff' : theme.colors.textSecondary,
                      },
                    ]}
                  >
                    {f === 'in_progress' ? 'In Progress' : f.charAt(0).toUpperCase() + f.slice(1)}
                  </Text>
                  <View
                    style={[
                      styles.filterCount,
                      {
                        backgroundColor:
                          filter === f
                            ? 'rgba(255,255,255,0.2)'
                            : theme.colors.bgHover,
                      },
                    ]}
                  >
                    <Text
                      style={[
                        styles.filterCountText,
                        {
                          color:
                            filter === f ? '#fff' : theme.colors.textTertiary,
                        },
                      ]}
                    >
                      {getFilterCount(f)}
                    </Text>
                  </View>
                </TouchableOpacity>
              )
            )}
          </ScrollView>
        </View>

        {/* Active Task (In Progress) */}
        {tasks.filter((t) => t.status === 'in_progress').length > 0 && filter !== 'in_progress' && (
          <View style={styles.section}>
            <Text variant="label" color="secondary" style={styles.sectionLabel}>
              CURRENTLY WORKING ON
            </Text>
            {tasks
              .filter((t) => t.status === 'in_progress')
              .slice(0, 1)
              .map((task) => (
                <Card
                  key={task.task_id}
                  variant="primary"
                  style={styles.activeTaskCard}
                >
                  <View style={styles.activeTaskContent}>
                    <Text variant="bodySmall" style={{ color: 'rgba(255,255,255,0.7)' }}>
                      IN PROGRESS
                    </Text>
                    <Text variant="h3" style={{ color: '#fff', marginTop: 4 }}>
                      {task.title}
                    </Text>
                    {task.project_name && (
                      <Text
                        variant="bodySmall"
                        style={{ color: 'rgba(255,255,255,0.7)', marginTop: 4 }}
                      >
                        {task.project_name}
                      </Text>
                    )}
                    <View style={styles.activeTaskActions}>
                      <TouchableOpacity
                        style={styles.activeTaskButton}
                        onPress={() => handleCompleteTask(task.task_id)}
                      >
                        <Text style={{ color: '#fff', fontWeight: '600' }}>
                          Done
                        </Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                </Card>
              ))}
          </View>
        )}

        {/* Task List */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            {filter === 'today' ? 'DUE TODAY' : filter === 'overdue' ? 'OVERDUE' : filter === 'in_progress' ? 'IN PROGRESS' : 'ALL TASKS'}
          </Text>
          {filteredTasks.length > 0 ? (
            filteredTasks.map((task) => (
              <TaskCard
                key={task.task_id}
                id={task.task_id}
                title={task.title}
                description={task.description}
                priority={task.priority}
                status={task.status}
                projectName={task.project_name || undefined}
                dueDate={task.due_date || undefined}
                isOverdue={isTaskOverdue(task)}
                onComplete={() => handleCompleteTask(task.task_id)}
                onStart={() => handleStartTask(task.task_id)}
                onPress={() => {
                  // Navigate to task detail or open edit modal
                }}
              />
            ))
          ) : (
            <Card style={styles.emptyCard}>
              <Text variant="body" color="tertiary" style={styles.emptyText}>
                {filter === 'today'
                  ? 'No tasks due today'
                  : filter === 'overdue'
                  ? 'No overdue tasks'
                  : filter === 'in_progress'
                  ? 'No tasks in progress'
                  : 'No pending tasks'}
              </Text>
              <Text variant="bodySmall" color="tertiary" style={styles.emptySubtext}>
                Use the input below to add a task
              </Text>
            </Card>
          )}
        </View>

        {/* Project Quick Access */}
        {projects.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text variant="label" color="secondary">
                PROJECTS
              </Text>
              <TouchableOpacity onPress={() => navigation.navigate('Projects')}>
                <Text variant="bodySmall" color="accent">
                  See All
                </Text>
              </TouchableOpacity>
            </View>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.projectsContainer}
            >
              {projects.slice(0, 5).map((project) => (
                <TouchableOpacity
                  key={project.project_id}
                  style={[
                    styles.projectChip,
                    {
                      backgroundColor: theme.colors.bgSurface,
                      borderColor: theme.colors.border,
                    },
                  ]}
                  onPress={() =>
                    navigation.navigate('ProjectDetail', {
                      projectId: project.project_id,
                    })
                  }
                >
                  <Text variant="bodySmall" numberOfLines={1}>
                    {project.name}
                  </Text>
                  <Text variant="caption" color="tertiary">
                    {project.task_count - project.completed_task_count} tasks
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}
      </ScrollView>

      {/* Conversation Input */}
      <View
        style={[
          styles.inputContainer,
          {
            backgroundColor: theme.colors.bg,
            paddingBottom: insets.bottom + 16,
            paddingHorizontal: horizontalPadding,
            borderTopColor: theme.colors.border,
          },
        ]}
      >
        <ConversationInput
          placeholder="Add a task..."
          onSubmit={handleConversationSubmit}
          onVoicePress={() => navigation.navigate('Voice')}
          suggestions={['Add task', 'Start focus', 'Log habit']}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
  },
  header: {
    marginBottom: 20,
  },
  subtitle: {
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionLabel: {
    marginBottom: 12,
  },
  // Habits
  habitsScroll: {
    marginHorizontal: -20,
  },
  habitsContainer: {
    paddingHorizontal: 20,
    gap: 10,
  },
  emptyHabits: {
    padding: 20,
  },
  // Filters
  filterScroll: {
    marginHorizontal: -20,
  },
  filterContainer: {
    paddingHorizontal: 20,
    gap: 8,
  },
  filterTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  filterText: {
    fontSize: 13,
    fontWeight: '600',
  },
  filterCount: {
    marginLeft: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    minWidth: 20,
    alignItems: 'center',
  },
  filterCountText: {
    fontSize: 11,
    fontWeight: '600',
  },
  // Active task
  activeTaskCard: {
    padding: 16,
  },
  activeTaskContent: {},
  activeTaskActions: {
    flexDirection: 'row',
    marginTop: 12,
  },
  activeTaskButton: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  // Empty state
  emptyCard: {
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    textAlign: 'center',
  },
  emptySubtext: {
    textAlign: 'center',
    marginTop: 8,
  },
  // Projects
  projectsContainer: {
    gap: 10,
  },
  projectChip: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    minWidth: 120,
  },
  // Input
  inputContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingTop: 12,
    borderTopWidth: 1,
  },
});
