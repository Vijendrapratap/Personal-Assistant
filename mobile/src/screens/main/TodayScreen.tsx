/**
 * TodayScreen - The heart of Alfred
 * Shows morning briefing, proactive cards, and today's overview
 *
 * UI/UX Features:
 * - FlatList for virtualized scrolling performance
 * - 48px minimum touch targets per iOS HIG
 * - Ionicons instead of emojis
 * - Haptic feedback on interactions
 * - Proper accessibility labels
 */

import React, { useEffect, useCallback, useState, useMemo } from 'react';
import {
  View,
  FlatList,
  StyleSheet,
  RefreshControl,
  Pressable,
  useWindowDimensions,
  ListRenderItem,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../theme';
import { Text, Card, TodayScreenSkeleton } from '../../components/common';
import { AlfredAvatar, ProactiveCard } from '../../components/alfred';
import { ConversationInput } from '../../components/input';
import { HabitChip } from '../../components/habits';
import { useAlfred } from '../../lib/hooks/useAlfred';
import { useHaptics, useOptimisticTasks, useOptimisticHabits } from '../../lib/hooks';
import { useAlfredStore } from '../../lib/store/alfredStore';
import { dashboardApi, habitsApi } from '../../api/services';

interface TodayScreenProps {
  navigation: any;
}

// Section types for FlatList
type SectionType =
  | { type: 'header' }
  | { type: 'focus'; data: any }
  | { type: 'proactive'; data: any[] }
  | { type: 'habits'; data: { pending: any[]; completed: any[]; all: any[] } }
  | { type: 'dueTasks'; data: any[] };

// Category icons mapping
const CATEGORY_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  fitness: 'fitness',
  health: 'heart',
  productivity: 'flash',
  learning: 'book',
  mindfulness: 'leaf',
  social: 'people',
  finance: 'wallet',
  creativity: 'brush',
  work: 'briefcase',
  personal: 'star',
};

const CATEGORY_COLORS: Record<string, string> = {
  fitness: '#10B981',
  health: '#EC4899',
  productivity: '#3B82F6',
  learning: '#8B5CF6',
  mindfulness: '#F59E0B',
  social: '#F97316',
  finance: '#14B8A6',
  creativity: '#6366F1',
  work: '#3B82F6',
  personal: '#10B981',
};

export default function TodayScreen({ navigation }: TodayScreenProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const { width: screenWidth } = useWindowDimensions();
  const haptics = useHaptics();

  // Responsive values
  const horizontalPadding = Math.max(16, Math.min(20, screenWidth * 0.05));
  const contentWidth = screenWidth - (horizontalPadding * 2);
  const habitGap = 12;
  const habitColumns = screenWidth < 380 ? 2 : 3;
  const habitChipSize = Math.floor((contentWidth - (habitGap * (habitColumns - 1))) / habitColumns);

  // Bottom spacing: input container (~70) + tab bar (80) + safe area
  const bottomPadding = 70 + 80 + insets.bottom;
  const { completeTask } = useOptimisticTasks();
  const { logHabit } = useOptimisticHabits();

  const {
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

  // Load data on mount
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

  const handleConversationSubmit = useCallback(async (message: string) => {
    try {
      const response = await sendMessage(message);
      console.log('Alfred:', response);
      loadData();
    } catch (err) {
      console.error('Chat error:', err);
    }
  }, [sendMessage]);

  const handleLogHabit = useCallback(async (habitId: string) => {
    const result = await logHabit(habitId);
    if (result.success) {
      loadData();
    }
  }, [logHabit]);

  const handleCompleteTask = useCallback(async (taskId: string) => {
    const success = await completeTask(taskId);
    if (success) {
      loadData();
    }
  }, [completeTask]);

  const handleProfilePress = useCallback(() => {
    haptics.buttonPress();
    navigation.navigate('Profile');
  }, [haptics, navigation]);

  const handleTasksPress = useCallback(() => {
    haptics.buttonPress();
    navigation.navigate('Tasks');
  }, [haptics, navigation]);

  // Get greeting based on time
  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  }, []);

  const formattedDate = useMemo(() => {
    return new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
    });
  }, []);

  // Compute habit data
  const { pendingHabits, completedHabits } = useMemo(() => {
    const today = new Date().toISOString().split('T')[0];
    const pending = habits.filter((h: any) => {
      const lastLogged = h.last_logged;
      if (!lastLogged) return true;
      return lastLogged < today;
    });
    const completed = habits.filter((h: any) => {
      const lastLogged = h.last_logged;
      if (!lastLogged) return false;
      return lastLogged >= today;
    });
    return { pendingHabits: pending, completedHabits: completed };
  }, [habits]);

  // Build sections for FlatList
  const sections = useMemo((): SectionType[] => {
    const result: SectionType[] = [{ type: 'header' }];

    const focusTask = todayData?.focus?.high_priority_tasks?.[0];
    if (focusTask) {
      result.push({ type: 'focus', data: focusTask });
    }

    if (proactiveCards.length > 0) {
      result.push({ type: 'proactive', data: proactiveCards.slice(0, 3) });
    }

    if (habits.length > 0) {
      result.push({
        type: 'habits',
        data: { pending: pendingHabits, completed: completedHabits, all: habits },
      });
    }

    if (todayData?.focus?.due_today?.length > 0) {
      result.push({ type: 'dueTasks', data: todayData.focus.due_today.slice(0, 3) });
    }

    return result;
  }, [todayData, proactiveCards, habits, pendingHabits, completedHabits]);

  // Show skeleton on initial load
  if (isInitialLoad && !todayData) {
    return <TodayScreenSkeleton />;
  }

  // Render section item
  const renderSection: ListRenderItem<SectionType> = useCallback(({ item }) => {
    switch (item.type) {
      case 'header':
        return (
          <View style={styles.header}>
            <View style={styles.headerTop}>
              <View>
                <Text variant="caption" color="secondary">
                  {formattedDate}
                </Text>
                <Text variant="h2" style={styles.greeting}>
                  {greeting}, Sir
                </Text>
              </View>
              {/* Profile button - 48px touch target */}
              <Pressable
                onPress={handleProfilePress}
                style={({ pressed }) => [
                  styles.profileButton,
                  {
                    backgroundColor: pressed
                      ? theme.colors.bgHover
                      : theme.colors.bgSurface,
                  },
                ]}
                accessibilityRole="button"
                accessibilityLabel="Open profile settings"
              >
                <AlfredAvatar state={alfredState} size="sm" showGlow={false} />
              </Pressable>
            </View>

            {/* Quick status */}
            {todayData && (
              <View style={styles.statusRow}>
                <Ionicons
                  name="checkbox-outline"
                  size={16}
                  color={theme.colors.textSecondary}
                />
                <Text variant="body" color="secondary" style={styles.statusText}>
                  {todayData.stats.tasks_pending} tasks pending
                  {todayData.stats.tasks_overdue > 0 && (
                    <Text color="danger"> ({todayData.stats.tasks_overdue} overdue)</Text>
                  )}
                </Text>
                <View style={styles.statusDot} />
                <Ionicons
                  name="flame-outline"
                  size={16}
                  color={theme.colors.textSecondary}
                />
                <Text variant="body" color="secondary">
                  {completedHabits.length}/{habits.length} habits
                </Text>
              </View>
            )}
          </View>
        );

      case 'focus':
        return (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="flag" size={14} color={theme.colors.textSecondary} />
              <Text variant="label" color="secondary" style={styles.sectionLabelText}>
                YOUR FOCUS
              </Text>
            </View>
            <Card variant="primary" style={styles.focusCard}>
              <View style={styles.focusContent}>
                <View style={styles.focusHeader}>
                  <View
                    style={[
                      styles.focusBadge,
                      { backgroundColor: 'rgba(255,255,255,0.2)' },
                    ]}
                  >
                    <Ionicons name="flame" size={12} color="#fff" />
                    <Text style={styles.focusBadgeText}>HIGH PRIORITY</Text>
                  </View>
                </View>
                <Text variant="h3" style={styles.focusTitle}>
                  {item.data.title}
                </Text>
                {item.data.project_name && (
                  <View style={styles.focusMeta}>
                    <Ionicons name="folder-outline" size={14} color="rgba(255,255,255,0.7)" />
                    <Text style={styles.focusMetaText}>
                      {item.data.project_name}
                      {item.data.due_date && ` · Due ${new Date(item.data.due_date).toLocaleDateString()}`}
                    </Text>
                  </View>
                )}
                <View style={styles.focusActions}>
                  {/* Done button - 48px touch target */}
                  <Pressable
                    style={({ pressed }) => [
                      styles.focusButton,
                      styles.focusButtonPrimary,
                      pressed && { opacity: 0.8 },
                    ]}
                    onPress={() => handleCompleteTask(item.data.task_id)}
                    accessibilityRole="button"
                    accessibilityLabel={`Mark ${item.data.title} as complete`}
                  >
                    <Ionicons name="checkmark" size={18} color="#fff" />
                    <Text style={styles.focusButtonText}>Done</Text>
                  </Pressable>
                  {/* View All button - 48px touch target */}
                  <Pressable
                    style={({ pressed }) => [
                      styles.focusButton,
                      styles.focusButtonSecondary,
                      pressed && { opacity: 0.8 },
                    ]}
                    onPress={handleTasksPress}
                    accessibilityRole="button"
                    accessibilityLabel="View all tasks"
                  >
                    <Text style={styles.focusButtonTextSecondary}>View All</Text>
                  </Pressable>
                </View>
              </View>
            </Card>
          </View>
        );

      case 'proactive':
        return (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="bulb-outline" size={14} color={theme.colors.textSecondary} />
              <Text variant="label" color="secondary" style={styles.sectionLabelText}>
                ALFRED NOTICED
              </Text>
            </View>
            {item.data.map((card: any) => (
              <ProactiveCard
                key={card.id}
                type={card.type}
                title={card.title}
                description={card.description}
                onDismiss={() => handleDismissCard(card.id)}
                actions={card.actions.map((action: string) => ({
                  label: action,
                  onPress: () => handleDismissCard(card.id),
                  variant: action === card.actions[0] ? 'primary' : 'secondary',
                }))}
              />
            ))}
          </View>
        );

      case 'habits':
        return (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="repeat-outline" size={14} color={theme.colors.textSecondary} />
              <Text variant="label" color="secondary" style={styles.sectionLabelText}>
                HABITS TODAY
              </Text>
              <View style={{ flex: 1 }} />
              <Text variant="bodySmall" color="tertiary">
                {item.data.completed.length}/{item.data.all.length}
              </Text>
            </View>
            <View style={[styles.habitsGrid, { gap: habitGap }]}>
              {item.data.all.slice(0, habitColumns * 2).map((habit: any) => {
                const isCompleted = item.data.completed.some(
                  (h: any) => h.habit_id === habit.habit_id
                );
                const categoryColor = CATEGORY_COLORS[habit.category?.toLowerCase()] || '#6B7280';
                const categoryIcon = CATEGORY_ICONS[habit.category?.toLowerCase()] || 'sparkles';

                return (
                  <Pressable
                    key={habit.habit_id}
                    style={({ pressed }) => [
                      styles.habitChip,
                      {
                        width: habitChipSize,
                        height: habitChipSize,
                        backgroundColor: isCompleted
                          ? theme.colors.success + '20'
                          : pressed
                          ? theme.colors.bgHover
                          : theme.colors.bgSurface,
                        borderColor: isCompleted
                          ? theme.colors.success
                          : theme.colors.border,
                      },
                    ]}
                    onPress={() => {
                      if (!isCompleted) {
                        haptics.habitLogged();
                        handleLogHabit(habit.habit_id);
                      }
                    }}
                    disabled={isCompleted}
                    accessibilityRole="button"
                    accessibilityLabel={`${habit.name} habit. ${isCompleted ? 'Completed' : 'Tap to log'}`}
                    accessibilityState={{ disabled: isCompleted }}
                  >
                    <View
                      style={[
                        styles.habitIconContainer,
                        {
                          backgroundColor: isCompleted
                            ? theme.colors.success
                            : `${categoryColor}20`,
                        },
                      ]}
                    >
                      {isCompleted ? (
                        <Ionicons name="checkmark" size={20} color="#fff" />
                      ) : (
                        <Ionicons name={categoryIcon} size={20} color={categoryColor} />
                      )}
                    </View>
                    <Text
                      variant="bodySmall"
                      color={isCompleted ? 'success' : 'primary'}
                      style={styles.habitName}
                      numberOfLines={1}
                    >
                      {habit.name}
                    </Text>
                    {habit.current_streak > 0 && (
                      <View style={styles.streakBadge}>
                        <Ionicons
                          name="flame"
                          size={12}
                          color={theme.colors.warning}
                        />
                        <Text
                          variant="caption"
                          style={{ color: theme.colors.warning, fontWeight: '600' }}
                        >
                          {habit.current_streak}
                        </Text>
                      </View>
                    )}
                  </Pressable>
                );
              })}
            </View>
          </View>
        );

      case 'dueTasks':
        return (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="calendar-outline" size={14} color={theme.colors.textSecondary} />
              <Text variant="label" color="secondary" style={styles.sectionLabelText}>
                DUE TODAY
              </Text>
              <View style={{ flex: 1 }} />
              <Pressable
                onPress={handleTasksPress}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                accessibilityRole="button"
                accessibilityLabel="See all tasks"
              >
                <Text variant="bodySmall" color="accent">
                  See All
                </Text>
              </Pressable>
            </View>
            {item.data.map((task: any) => {
              const priorityColor = getPriorityColor(task.priority, theme);
              return (
                <Card key={task.task_id} style={styles.taskCard}>
                  {/* Task row - 48px touch target via checkboxTouchArea */}
                  <View style={styles.taskRow}>
                    <Pressable
                      style={styles.checkboxTouchArea}
                      onPress={() => {
                        haptics.taskComplete();
                        handleCompleteTask(task.task_id);
                      }}
                      accessibilityRole="checkbox"
                      accessibilityState={{ checked: false }}
                      accessibilityLabel={`Mark ${task.title} as complete`}
                    >
                      <View
                        style={[
                          styles.taskCheckbox,
                          { borderColor: priorityColor },
                        ]}
                      />
                    </Pressable>
                    <View style={styles.taskContent}>
                      <Text variant="body">{task.title}</Text>
                      <View style={styles.taskMeta}>
                        <Ionicons
                          name="folder-outline"
                          size={12}
                          color={theme.colors.textTertiary}
                        />
                        <Text variant="caption" color="tertiary">
                          {task.project_name || 'Personal'}
                        </Text>
                      </View>
                    </View>
                    <Ionicons
                      name="chevron-forward"
                      size={20}
                      color={theme.colors.textTertiary}
                    />
                  </View>
                </Card>
              );
            })}
          </View>
        );

      default:
        return null;
    }
  }, [
    formattedDate,
    greeting,
    handleProfilePress,
    theme,
    alfredState,
    todayData,
    completedHabits,
    habits,
    handleCompleteTask,
    handleTasksPress,
    handleDismissCard,
    habitGap,
    habitColumns,
    habitChipSize,
    haptics,
    handleLogHabit,
  ]);

  const keyExtractor = useCallback((item: SectionType, index: number) => {
    return `${item.type}-${index}`;
  }, []);

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      <FlatList
        data={sections}
        renderItem={renderSection}
        keyExtractor={keyExtractor}
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
        removeClippedSubviews={true}
        maxToRenderPerBatch={5}
        windowSize={5}
      />

      {/* Conversation Input - Fixed at bottom */}
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
          placeholder="Ask Alfred..."
          onSubmit={handleConversationSubmit}
          onVoicePress={() => navigation.navigate('Voice')}
          suggestions={['Add task', 'Update project', 'Log habit']}
        />
      </View>
    </View>
  );
}

// Helper functions
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
  content: {
    flexGrow: 1,
  },
  header: {
    marginBottom: 24,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  greeting: {
    marginTop: 4,
  },
  // Profile button - 48px touch target
  profileButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusText: {
    marginRight: 4,
  },
  statusDot: {
    width: 3,
    height: 3,
    borderRadius: 2,
    backgroundColor: '#94A3B8',
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 6,
  },
  sectionLabelText: {
    letterSpacing: 0.5,
  },
  focusCard: {
    padding: 20,
  },
  focusContent: {},
  focusHeader: {
    marginBottom: 12,
  },
  focusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    gap: 6,
  },
  focusBadgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  focusTitle: {
    color: '#fff',
    marginBottom: 6,
  },
  focusMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  focusMetaText: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 13,
  },
  focusActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
  },
  // Focus buttons - 48px height for touch target
  focusButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 18,
    minHeight: 48,
    borderRadius: 12,
    gap: 6,
  },
  focusButtonPrimary: {
    backgroundColor: 'rgba(255,255,255,0.25)',
  },
  focusButtonSecondary: {
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  focusButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 15,
  },
  focusButtonTextSecondary: {
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '500',
    fontSize: 15,
  },
  habitsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  // Habit chips - minimum 48px for touch target
  habitChip: {
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    padding: 10,
    minHeight: 80,
  },
  habitIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
  },
  habitName: {
    textAlign: 'center',
    fontWeight: '500',
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 2,
  },
  taskCard: {
    marginBottom: 8,
    padding: 14,
  },
  taskRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  // 48px touch target for checkbox
  checkboxTouchArea: {
    width: 48,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: -12,
  },
  taskCheckbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
  },
  taskContent: {
    flex: 1,
    marginLeft: 4,
  },
  taskMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  inputContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingTop: 12,
    borderTopWidth: 1,
  },
});
