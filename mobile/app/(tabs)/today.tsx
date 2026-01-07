/**
 * Today Screen (Expo Router)
 *
 * The heart of Alfred - morning briefing, proactive cards, and today's overview.
 * Adapted from src/screens/TodayScreen for file-based routing.
 */

import React, { useEffect, useCallback, useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../src/theme';
import { Text, Card, TodayScreenSkeleton } from '../../src/components/common';
import { AlfredAvatar, ProactiveCard } from '../../src/components/alfred';
import { ConversationInput } from '../../src/components/input';
import { useAlfred } from '../../src/lib/hooks/useAlfred';
import { useHaptics, useOptimisticTasks, useOptimisticHabits } from '../../src/lib/hooks';
import { useAlfredStore } from '../../src/lib/store/alfredStore';
import { dashboardApi, habitsApi } from '../../src/api/services';

export default function TodayScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const haptics = useHaptics();
  const { completeTask } = useOptimisticTasks();
  const { logHabit } = useOptimisticHabits();

  const {
    briefing,
    briefingLoading,
    proactiveCards,
    alfredState,
    loadTodayOverview,
    handleDismissCard,
    sendMessage,
  } = useAlfred();

  const { habits, setHabits } = useAlfredStore();

  const [refreshing, setRefreshing] = useState(false);
  const [todayData, setTodayData] = useState<any>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [overview, habitsData] = await Promise.all([
        dashboardApi.getToday(),
        habitsApi.getToday(),
      ]);
      setTodayData(overview);
      setHabits([...habitsData.pending, ...habitsData.completed]);
    } catch (err) {
      console.error('Failed to load today data:', err);
    } finally {
      setIsInitialLoad(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    haptics.pullRefresh();
    await loadData();
    setRefreshing(false);
  }, [haptics]);

  const handleConversationSubmit = async (message: string) => {
    try {
      const response = await sendMessage(message);
      console.log('Alfred:', response);
      loadData();
    } catch (err) {
      console.error('Chat error:', err);
    }
  };

  const handleLogHabit = async (habitId: string) => {
    const result = await logHabit(habitId);
    if (result.success) {
      loadData();
    }
  };

  const handleCompleteTask = async (taskId: string) => {
    const success = await completeTask(taskId);
    if (success) {
      loadData();
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const formatDate = () => {
    return new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isInitialLoad && !todayData) {
    return <TodayScreenSkeleton />;
  }

  const focusTask = todayData?.focus?.high_priority_tasks?.[0];
  const pendingHabits = habits.filter((h: any) => {
    const lastLogged = h.last_logged;
    if (!lastLogged) return true;
    const today = new Date().toISOString().split('T')[0];
    return lastLogged < today;
  });
  const completedHabits = habits.filter((h: any) => {
    const lastLogged = h.last_logged;
    if (!lastLogged) return false;
    const today = new Date().toISOString().split('T')[0];
    return lastLogged >= today;
  });

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.content,
          { paddingTop: insets.top + 16, paddingBottom: 120 },
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
        {/* Header with greeting */}
        <View style={styles.header}>
          <View style={styles.headerTop}>
            <View>
              <Text variant="caption" color="secondary">
                {formatDate()}
              </Text>
              <Text variant="h2" style={styles.greeting}>
                {getGreeting()}, Sir
              </Text>
            </View>
            <TouchableOpacity
              onPress={() => router.push('/you')}
              style={[styles.profileButton, { backgroundColor: theme.colors.bgSurface }]}
            >
              <AlfredAvatar state={alfredState} size="sm" showGlow={false} />
            </TouchableOpacity>
          </View>

          {/* Quick status */}
          {todayData && (
            <Text variant="body" color="secondary" style={styles.statusText}>
              {todayData.stats.tasks_pending} tasks pending
              {todayData.stats.tasks_overdue > 0 && (
                <Text color="danger"> ({todayData.stats.tasks_overdue} overdue)</Text>
              )}
              {' · '}
              {completedHabits.length}/{habits.length} habits done
            </Text>
          )}
        </View>

        {/* Focus Card */}
        {focusTask && (
          <View style={styles.section}>
            <Text variant="label" color="secondary" style={styles.sectionLabel}>
              YOUR FOCUS
            </Text>
            <Card variant="primary" style={styles.focusCard}>
              <View style={styles.focusContent}>
                <View style={styles.focusHeader}>
                  <View
                    style={[
                      styles.focusBadge,
                      { backgroundColor: 'rgba(255,255,255,0.2)' },
                    ]}
                  >
                    <Text style={{ color: '#fff', fontSize: 12, fontWeight: '600' }}>
                      HIGH PRIORITY
                    </Text>
                  </View>
                </View>
                <Text variant="h3" style={{ color: '#fff', marginBottom: 4 }}>
                  {focusTask.title}
                </Text>
                {focusTask.project_name && (
                  <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13 }}>
                    {focusTask.project_name}
                    {focusTask.due_date && ` · Due ${new Date(focusTask.due_date).toLocaleDateString()}`}
                  </Text>
                )}
                <View style={styles.focusActions}>
                  <TouchableOpacity
                    style={[styles.focusButton, { backgroundColor: 'rgba(255,255,255,0.2)' }]}
                    onPress={() => handleCompleteTask(focusTask.task_id)}
                  >
                    <Text style={{ color: '#fff', fontWeight: '600' }}>Done</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.focusButton, { backgroundColor: 'rgba(255,255,255,0.1)' }]}
                    onPress={() => router.push('/do')}
                  >
                    <Text style={{ color: 'rgba(255,255,255,0.8)', fontWeight: '500' }}>View All</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </Card>
          </View>
        )}

        {/* Proactive Cards */}
        {proactiveCards.length > 0 && (
          <View style={styles.section}>
            <Text variant="label" color="secondary" style={styles.sectionLabel}>
              ALFRED NOTICED
            </Text>
            {proactiveCards.slice(0, 3).map((card) => (
              <ProactiveCard
                key={card.id}
                type={card.type}
                title={card.title}
                description={card.description}
                onDismiss={() => handleDismissCard(card.id)}
                actions={card.actions.map((action) => ({
                  label: action,
                  onPress: () => {
                    handleDismissCard(card.id);
                  },
                  variant: action === card.actions[0] ? 'primary' : 'secondary',
                }))}
              />
            ))}
          </View>
        )}

        {/* Habits */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text variant="label" color="secondary">
              HABITS TODAY
            </Text>
            <Text variant="bodySmall" color="tertiary">
              {completedHabits.length}/{habits.length}
            </Text>
          </View>
          <View style={styles.habitsGrid}>
            {habits.slice(0, 6).map((habit: any) => {
              const isCompleted = completedHabits.some((h: any) => h.habit_id === habit.habit_id);
              return (
                <TouchableOpacity
                  key={habit.habit_id}
                  style={[
                    styles.habitChip,
                    {
                      backgroundColor: isCompleted
                        ? theme.colors.success + '20'
                        : theme.colors.bgSurface,
                      borderColor: isCompleted
                        ? theme.colors.success
                        : theme.colors.border,
                    },
                  ]}
                  onPress={() => !isCompleted && handleLogHabit(habit.habit_id)}
                  disabled={isCompleted}
                >
                  <Text style={{ fontSize: 20, marginBottom: 4 }}>
                    {isCompleted ? '✓' : getCategoryEmoji(habit.category)}
                  </Text>
                  <Text
                    variant="bodySmall"
                    color={isCompleted ? 'success' : 'primary'}
                    style={{ textAlign: 'center' }}
                    numberOfLines={1}
                  >
                    {habit.name}
                  </Text>
                  {habit.current_streak > 0 && (
                    <Text variant="caption" color="warning" style={{ marginTop: 2 }}>
                      {habit.current_streak}
                    </Text>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Due Today */}
        {todayData?.focus?.due_today?.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text variant="label" color="secondary">
                DUE TODAY
              </Text>
              <TouchableOpacity onPress={() => router.push('/do')}>
                <Text variant="bodySmall" color="accent">
                  See All
                </Text>
              </TouchableOpacity>
            </View>
            {todayData.focus.due_today.slice(0, 3).map((task: any) => (
              <Card key={task.task_id} style={styles.taskCard}>
                <TouchableOpacity
                  style={styles.taskRow}
                  onPress={() => handleCompleteTask(task.task_id)}
                >
                  <View
                    style={[
                      styles.taskCheckbox,
                      { borderColor: getPriorityColor(task.priority, theme) },
                    ]}
                  />
                  <View style={styles.taskContent}>
                    <Text variant="body">{task.title}</Text>
                    <Text variant="caption" color="tertiary">
                      {task.project_name || 'Personal'}
                    </Text>
                  </View>
                </TouchableOpacity>
              </Card>
            ))}
          </View>
        )}
      </ScrollView>

      {/* Conversation Input */}
      <View
        style={[
          styles.inputContainer,
          {
            backgroundColor: theme.colors.bg,
            paddingBottom: insets.bottom + 80,
            borderTopColor: theme.colors.border,
          },
        ]}
      >
        <ConversationInput
          placeholder="Ask Alfred..."
          onSubmit={handleConversationSubmit}
          onVoicePress={() => router.push('/voice')}
          suggestions={['Add task', 'Update project', 'Log habit']}
        />
      </View>
    </View>
  );
}

function getCategoryEmoji(category: string): string {
  const emojis: Record<string, string> = {
    fitness: '💪',
    health: '❤️',
    productivity: '⚡',
    learning: '📚',
    mindfulness: '🧘',
    social: '👥',
    finance: '💰',
    creativity: '🎨',
  };
  return emojis[category?.toLowerCase()] || '✨';
}

function getPriorityColor(priority: string, theme: any): string {
  switch (priority) {
    case 'high':
      return theme.colors.danger;
    case 'medium':
      return theme.colors.warning;
    default:
      return theme.colors.info;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
  },
  header: {
    marginBottom: 24,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  greeting: {
    marginTop: 4,
  },
  profileButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusText: {
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  focusCard: {
    padding: 20,
  },
  focusContent: {},
  focusHeader: {
    marginBottom: 12,
  },
  focusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  focusActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
  },
  focusButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
  },
  habitsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  habitChip: {
    width: '30%',
    aspectRatio: 1,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    padding: 8,
  },
  taskCard: {
    marginBottom: 8,
    padding: 14,
  },
  taskRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  taskCheckbox: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    marginRight: 12,
  },
  taskContent: {
    flex: 1,
  },
  inputContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    paddingTop: 16,
    borderTopWidth: 1,
  },
});
