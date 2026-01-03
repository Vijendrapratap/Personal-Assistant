/**
 * EveningReviewModal - Daily reflection and planning for tomorrow
 * Inspired by Sunsama's end-of-day ritual
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../theme';
import { Text, Card, Button } from '../components/common';
import { AlfredAvatar } from '../components/alfred';
import { dashboardApi, tasksApi, habitsApi, Task, Habit } from '../api/services';

interface EveningReviewModalProps {
  navigation: any;
}

interface ReviewData {
  completed_tasks: Task[];
  incomplete_tasks: Task[];
  habits_completed: Habit[];
  habits_missed: Habit[];
  greeting: string;
}

type MoodType = 'great' | 'good' | 'okay' | 'tired' | 'stressed';

const MOODS: { type: MoodType; emoji: string; label: string }[] = [
  { type: 'stressed', emoji: '😫', label: 'Stressed' },
  { type: 'tired', emoji: '😕', label: 'Tired' },
  { type: 'okay', emoji: '😐', label: 'Okay' },
  { type: 'good', emoji: '🙂', label: 'Good' },
  { type: 'great', emoji: '😊', label: 'Great' },
];

export default function EveningReviewModal({ navigation }: EveningReviewModalProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  // State
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState(0); // 0: accomplishments, 1: blockers, 2: tomorrow, 3: mood
  const [reviewData, setReviewData] = useState<ReviewData | null>(null);

  // Form state
  const [blockersNote, setBlockersNote] = useState('');
  const [tomorrowNote, setTomorrowNote] = useState('');
  const [selectedMood, setSelectedMood] = useState<MoodType | null>(null);
  const [movedTasks, setMovedTasks] = useState<Set<string>>(new Set());

  // Load review data
  useEffect(() => {
    loadReviewData();
  }, []);

  const loadReviewData = async () => {
    try {
      const [todayData, habitsData] = await Promise.all([
        dashboardApi.getEveningReview(),
        habitsApi.getToday(),
      ]);

      setReviewData({
        completed_tasks: todayData.completed_today || [],
        incomplete_tasks: todayData.incomplete || [],
        habits_completed: habitsData.completed || [],
        habits_missed: habitsData.pending || [],
        greeting: todayData.greeting || 'Good evening',
      });
    } catch (err) {
      console.error('Failed to load review data:', err);
      // Use mock data for demo
      setReviewData({
        completed_tasks: [],
        incomplete_tasks: [],
        habits_completed: [],
        habits_missed: [],
        greeting: 'Good evening',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMoveToTomorrow = (taskId: string) => {
    setMovedTasks((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      // Submit review data
      // In a real implementation, this would call an API
      console.log('Submitting review:', {
        blockers: blockersNote,
        tomorrowPlan: tomorrowNote,
        mood: selectedMood,
        movedTasks: Array.from(movedTasks),
      });

      // Move tasks to tomorrow
      for (const taskId of movedTasks) {
        try {
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          await tasksApi.update(taskId, { due_date: tomorrow.toISOString() });
        } catch (err) {
          console.error('Failed to move task:', err);
        }
      }

      // Navigate back
      navigation.goBack();
    } catch (err) {
      console.error('Failed to submit review:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSkip = () => {
    navigation.goBack();
  };

  const nextStep = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      handleSubmit();
    }
  };

  const prevStep = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.bg }]}>
        <AlfredAvatar state="thinking" size="lg" />
        <Text variant="body" color="secondary" style={styles.loadingText}>
          Preparing your review...
        </Text>
      </View>
    );
  }

  const renderStepIndicator = () => (
    <View style={styles.stepIndicator}>
      {[0, 1, 2, 3].map((s) => (
        <View
          key={s}
          style={[
            styles.stepDot,
            {
              backgroundColor:
                s === step
                  ? theme.colors.primary
                  : s < step
                  ? theme.colors.success
                  : theme.colors.bgHover,
            },
          ]}
        />
      ))}
    </View>
  );

  const renderAccomplishments = () => (
    <View style={styles.stepContent}>
      <Text variant="h3" style={styles.stepTitle}>
        What you accomplished
      </Text>
      <Text variant="body" color="secondary" style={styles.stepSubtitle}>
        Celebrate your wins today
      </Text>

      {reviewData?.completed_tasks.length === 0 &&
      reviewData?.habits_completed.length === 0 ? (
        <Card style={styles.emptyCard}>
          <Text variant="body" color="tertiary" style={{ textAlign: 'center' }}>
            No tasks or habits completed today.{'\n'}That's okay - tomorrow is a new day.
          </Text>
        </Card>
      ) : (
        <>
          {/* Completed Tasks */}
          {reviewData?.completed_tasks.map((task) => (
            <View
              key={task.task_id}
              style={[styles.itemRow, { borderBottomColor: theme.colors.border }]}
            >
              <Text style={styles.checkmark}>✓</Text>
              <Text variant="body" style={styles.itemText}>
                {task.title}
              </Text>
            </View>
          ))}

          {/* Completed Habits */}
          {reviewData?.habits_completed.map((habit) => (
            <View
              key={habit.habit_id}
              style={[styles.itemRow, { borderBottomColor: theme.colors.border }]}
            >
              <Text style={styles.checkmark}>✓</Text>
              <View style={styles.habitInfo}>
                <Text variant="body" style={styles.itemText}>
                  {habit.name}
                </Text>
                {habit.current_streak > 0 && (
                  <Text variant="caption" color="warning">
                    🔥 {habit.current_streak}
                  </Text>
                )}
              </View>
            </View>
          ))}
        </>
      )}
    </View>
  );

  const renderIncomplete = () => (
    <View style={styles.stepContent}>
      <Text variant="h3" style={styles.stepTitle}>
        Didn't get done
      </Text>
      <Text variant="body" color="secondary" style={styles.stepSubtitle}>
        What happened? Move to tomorrow if needed.
      </Text>

      {reviewData?.incomplete_tasks.length === 0 &&
      reviewData?.habits_missed.length === 0 ? (
        <Card style={styles.emptyCard}>
          <Text variant="body" color="success" style={{ textAlign: 'center' }}>
            You completed everything! 🎉
          </Text>
        </Card>
      ) : (
        <>
          {/* Incomplete Tasks */}
          {reviewData?.incomplete_tasks.map((task) => (
            <TouchableOpacity
              key={task.task_id}
              style={[
                styles.itemRow,
                styles.incompleteRow,
                { borderBottomColor: theme.colors.border },
                movedTasks.has(task.task_id) && {
                  backgroundColor: theme.colors.primarySoft,
                },
              ]}
              onPress={() => handleMoveToTomorrow(task.task_id)}
            >
              <View style={styles.incompleteLeft}>
                <View
                  style={[styles.emptyCircle, { borderColor: theme.colors.textTertiary }]}
                />
                <Text variant="body" style={styles.itemText}>
                  {task.title}
                </Text>
              </View>
              <Text
                variant="caption"
                style={{
                  color: movedTasks.has(task.task_id)
                    ? theme.colors.primary
                    : theme.colors.textTertiary,
                }}
              >
                {movedTasks.has(task.task_id) ? '→ Tomorrow' : 'Tap to move'}
              </Text>
            </TouchableOpacity>
          ))}

          {/* Missed Habits */}
          {reviewData?.habits_missed.map((habit) => (
            <View
              key={habit.habit_id}
              style={[styles.itemRow, { borderBottomColor: theme.colors.border }]}
            >
              <View style={styles.incompleteLeft}>
                <View
                  style={[styles.emptyCircle, { borderColor: theme.colors.warning }]}
                />
                <Text variant="body" style={styles.itemText}>
                  {habit.name}
                </Text>
              </View>
              {habit.current_streak > 0 && (
                <Text variant="caption" color="danger">
                  Streak at risk!
                </Text>
              )}
            </View>
          ))}
        </>
      )}

      {/* Blockers note */}
      <View style={styles.noteSection}>
        <Text variant="label" color="secondary" style={styles.noteLabel}>
          What got in the way?
        </Text>
        <TextInput
          style={[
            styles.noteInput,
            {
              backgroundColor: theme.colors.bgSurface,
              color: theme.colors.textPrimary,
              borderColor: theme.colors.border,
            },
          ]}
          placeholder="Got pulled into an urgent issue..."
          placeholderTextColor={theme.colors.textTertiary}
          value={blockersNote}
          onChangeText={setBlockersNote}
          multiline
          numberOfLines={3}
          textAlignVertical="top"
        />
      </View>
    </View>
  );

  const renderTomorrow = () => (
    <View style={styles.stepContent}>
      <Text variant="h3" style={styles.stepTitle}>
        Tomorrow's priorities
      </Text>
      <Text variant="body" color="secondary" style={styles.stepSubtitle}>
        What's most important tomorrow?
      </Text>

      {/* Moved tasks preview */}
      {movedTasks.size > 0 && (
        <View style={styles.movedSection}>
          <Text variant="label" color="secondary" style={styles.noteLabel}>
            MOVED FROM TODAY
          </Text>
          {Array.from(movedTasks).map((taskId) => {
            const task = reviewData?.incomplete_tasks.find((t) => t.task_id === taskId);
            return task ? (
              <View key={taskId} style={[styles.movedItem, { backgroundColor: theme.colors.bgSurface }]}>
                <Text variant="bodySmall">{task.title}</Text>
              </View>
            ) : null;
          })}
        </View>
      )}

      {/* Tomorrow note */}
      <View style={styles.noteSection}>
        <Text variant="label" color="secondary" style={styles.noteLabel}>
          ANYTHING ELSE FOR TOMORROW?
        </Text>
        <TextInput
          style={[
            styles.noteInput,
            {
              backgroundColor: theme.colors.bgSurface,
              color: theme.colors.textPrimary,
              borderColor: theme.colors.border,
            },
          ]}
          placeholder="Start the day with..."
          placeholderTextColor={theme.colors.textTertiary}
          value={tomorrowNote}
          onChangeText={setTomorrowNote}
          multiline
          numberOfLines={3}
          textAlignVertical="top"
        />
      </View>
    </View>
  );

  const renderMood = () => (
    <View style={styles.stepContent}>
      <Text variant="h3" style={styles.stepTitle}>
        How are you feeling?
      </Text>
      <Text variant="body" color="secondary" style={styles.stepSubtitle}>
        Taking stock helps Alfred understand you better
      </Text>

      <View style={styles.moodGrid}>
        {MOODS.map((mood) => (
          <TouchableOpacity
            key={mood.type}
            style={[
              styles.moodOption,
              {
                backgroundColor:
                  selectedMood === mood.type
                    ? theme.colors.primary
                    : theme.colors.bgSurface,
                borderColor:
                  selectedMood === mood.type
                    ? theme.colors.primary
                    : theme.colors.border,
              },
            ]}
            onPress={() => setSelectedMood(mood.type)}
          >
            <Text style={styles.moodEmoji}>{mood.emoji}</Text>
            <Text
              variant="bodySmall"
              style={{
                color: selectedMood === mood.type ? '#FFFFFF' : theme.colors.textSecondary,
                marginTop: 4,
              }}
            >
              {mood.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Final message */}
      <View style={styles.finalMessage}>
        <AlfredAvatar state="idle" size="md" />
        <Text variant="body" color="secondary" style={styles.finalText}>
          Sleep well, Sir. Tomorrow awaits.
        </Text>
      </View>
    </View>
  );

  const renderCurrentStep = () => {
    switch (step) {
      case 0:
        return renderAccomplishments();
      case 1:
        return renderIncomplete();
      case 2:
        return renderTomorrow();
      case 3:
        return renderMood();
      default:
        return null;
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      {/* Header */}
      <View
        style={[
          styles.header,
          { paddingTop: insets.top + 12, borderBottomColor: theme.colors.border },
        ]}
      >
        <TouchableOpacity onPress={handleSkip} style={styles.skipButton}>
          <Text variant="body" color="tertiary">
            Skip
          </Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text variant="body" style={{ fontWeight: '600' }}>
            Evening Review
          </Text>
          {renderStepIndicator()}
        </View>
        <View style={styles.skipButton} />
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 100 }]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Greeting */}
          <View style={styles.greetingSection}>
            <Text variant="h2">{reviewData?.greeting || 'Good evening'}</Text>
            <Text variant="body" color="secondary">
              Let's review your day.
            </Text>
          </View>

          {renderCurrentStep()}
        </ScrollView>

        {/* Navigation */}
        <View
          style={[
            styles.navigation,
            { paddingBottom: insets.bottom + 16, backgroundColor: theme.colors.bg },
          ]}
        >
          {step > 0 && (
            <Button
              title="Back"
              variant="ghost"
              onPress={prevStep}
              style={styles.navButton}
            />
          )}
          <Button
            title={step === 3 ? 'Done, Alfred' : 'Continue'}
            onPress={nextStep}
            loading={submitting}
            style={[styles.navButton, { flex: step === 0 ? 1 : undefined }]}
          />
        </View>
      </KeyboardAvoidingView>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  skipButton: {
    width: 60,
  },
  headerCenter: {
    alignItems: 'center',
  },
  stepIndicator: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 6,
  },
  stepDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  greetingSection: {
    paddingVertical: 24,
  },
  stepContent: {
    paddingBottom: 24,
  },
  stepTitle: {
    marginBottom: 4,
  },
  stepSubtitle: {
    marginBottom: 20,
  },
  emptyCard: {
    alignItems: 'center',
    padding: 24,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  incompleteRow: {
    justifyContent: 'space-between',
  },
  incompleteLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  checkmark: {
    fontSize: 16,
    color: '#10B981',
    marginRight: 12,
    fontWeight: '700',
  },
  emptyCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    marginRight: 12,
  },
  itemText: {
    flex: 1,
  },
  habitInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  noteSection: {
    marginTop: 20,
  },
  noteLabel: {
    marginBottom: 8,
  },
  noteInput: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    fontSize: 15,
    minHeight: 80,
  },
  movedSection: {
    marginBottom: 20,
  },
  movedItem: {
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  moodGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  moodOption: {
    alignItems: 'center',
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    minWidth: 60,
  },
  moodEmoji: {
    fontSize: 28,
  },
  finalMessage: {
    alignItems: 'center',
    marginTop: 40,
    paddingTop: 20,
  },
  finalText: {
    marginTop: 16,
    textAlign: 'center',
  },
  navigation: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 16,
    gap: 12,
  },
  navButton: {
    minWidth: 100,
  },
});
