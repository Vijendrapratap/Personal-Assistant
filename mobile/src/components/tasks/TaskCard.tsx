/**
 * TaskCard Component
 * Displays a task with proper touch targets (48px), haptic feedback,
 * animations, and accessibility support per iOS HIG guidelines.
 */

import React, { memo, useCallback, useState } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  ViewStyle,
  Pressable,
  ActivityIndicator,
} from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolateColor,
  runOnJS,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../theme';
import { Text } from '../common';
import { useHaptics } from '../../lib/hooks';

export interface TaskCardProps {
  id: string;
  title: string;
  description?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'blocked' | 'completed';
  projectName?: string;
  projectColor?: string;
  dueDate?: string;
  dueDateLabel?: string;
  isOverdue?: boolean;
  onPress?: () => void;
  onComplete?: () => void;
  onStart?: () => void;
  style?: ViewStyle;
}

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

function TaskCardComponent({
  id,
  title,
  description,
  priority,
  status,
  projectName,
  projectColor,
  dueDate,
  dueDateLabel,
  isOverdue = false,
  onPress,
  onComplete,
  onStart,
  style,
}: TaskCardProps) {
  const { theme } = useTheme();
  const haptics = useHaptics();
  const [isCompleting, setIsCompleting] = useState(false);

  // Animation values
  const cardScale = useSharedValue(1);
  const checkboxScale = useSharedValue(1);
  const checkboxProgress = useSharedValue(status === 'completed' ? 1 : 0);

  const getPriorityColor = useCallback(() => {
    switch (priority) {
      case 'high':
        return theme.colors.priority.high;
      case 'medium':
        return theme.colors.priority.medium;
      case 'low':
        return theme.colors.priority.low;
      default:
        return theme.colors.textTertiary;
    }
  }, [priority, theme.colors]);

  const getPriorityBgColor = useCallback(() => {
    switch (priority) {
      case 'high':
        return theme.colors.priority.highBg;
      case 'medium':
        return theme.colors.priority.mediumBg;
      case 'low':
        return theme.colors.priority.lowBg;
      default:
        return theme.colors.bgHover;
    }
  }, [priority, theme.colors]);

  const getStatusColor = useCallback(() => {
    switch (status) {
      case 'in_progress':
        return theme.colors.info;
      case 'blocked':
        return theme.colors.danger;
      case 'completed':
        return theme.colors.success;
      default:
        return theme.colors.textTertiary;
    }
  }, [status, theme.colors]);

  const formatDueDate = useCallback(() => {
    if (dueDateLabel) return dueDateLabel;
    if (!dueDate) return null;

    const date = new Date(dueDate);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  }, [dueDate, dueDateLabel]);

  // Handlers with haptic feedback
  const handleCardPress = useCallback(() => {
    haptics.buttonPress();
    onPress?.();
  }, [haptics, onPress]);

  const handleComplete = useCallback(async () => {
    if (isCompleting) return;

    setIsCompleting(true);

    // Animate checkbox
    checkboxScale.value = withSpring(0.8, { damping: 10 }, () => {
      checkboxScale.value = withSpring(1, { damping: 8 });
    });

    // Animate to completed state
    checkboxProgress.value = withTiming(1, { duration: 300 });

    // Haptic feedback
    haptics.taskComplete();

    // Call the completion handler
    setTimeout(() => {
      onComplete?.();
      setIsCompleting(false);
    }, 200);
  }, [isCompleting, checkboxScale, checkboxProgress, haptics, onComplete]);

  const handleStart = useCallback(() => {
    haptics.buttonPress();
    onStart?.();
  }, [haptics, onStart]);

  const handlePressIn = useCallback(() => {
    cardScale.value = withSpring(0.98, { damping: 15 });
  }, [cardScale]);

  const handlePressOut = useCallback(() => {
    cardScale.value = withSpring(1, { damping: 15 });
  }, [cardScale]);

  // Animated styles
  const cardAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: cardScale.value }],
  }));

  const checkboxAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: checkboxScale.value }],
    backgroundColor: interpolateColor(
      checkboxProgress.value,
      [0, 1],
      ['transparent', theme.colors.success]
    ),
  }));

  const isCompleted = status === 'completed';
  const dueDateFormatted = formatDueDate();
  const priorityColor = getPriorityColor();
  const priorityBgColor = getPriorityBgColor();
  const statusColor = getStatusColor();

  return (
    <AnimatedPressable
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.bgSurface,
          borderColor: theme.colors.border,
        },
        isCompleted && styles.completedContainer,
        cardAnimatedStyle,
        style,
      ]}
      onPress={handleCardPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      accessibilityRole="button"
      accessibilityLabel={`Task: ${title}. Priority: ${priority}. Status: ${status}`}
      accessibilityHint="Double tap to view task details"
    >
      {/* Checkbox - 48px touch target per iOS HIG */}
      <Pressable
        style={styles.checkboxTouchArea}
        onPress={handleComplete}
        disabled={isCompleting || isCompleted}
        accessibilityRole="checkbox"
        accessibilityState={{ checked: isCompleted }}
        accessibilityLabel={`Mark ${title} as complete`}
      >
        <Animated.View
          style={[
            styles.checkbox,
            {
              borderColor: isCompleted ? theme.colors.success : priorityColor,
            },
            checkboxAnimatedStyle,
          ]}
        >
          {isCompleting ? (
            <ActivityIndicator size="small" color={theme.colors.success} />
          ) : isCompleted ? (
            <Ionicons name="checkmark" size={16} color="#fff" />
          ) : null}
        </Animated.View>
      </Pressable>

      {/* Content */}
      <View style={styles.content}>
        <View style={styles.titleRow}>
          <Text
            variant="body"
            style={[
              styles.title,
              isCompleted && {
                textDecorationLine: 'line-through',
                color: theme.colors.textTertiary,
              },
            ]}
            numberOfLines={2}
          >
            {title}
          </Text>
        </View>

        {description && !isCompleted && (
          <Text
            variant="bodySmall"
            color="tertiary"
            numberOfLines={1}
            style={styles.description}
          >
            {description}
          </Text>
        )}

        {/* Meta row */}
        <View style={styles.metaRow}>
          {/* Priority badge */}
          <View
            style={[
              styles.badge,
              { backgroundColor: priorityBgColor },
            ]}
          >
            <Ionicons
              name={
                priority === 'high'
                  ? 'flame'
                  : priority === 'medium'
                  ? 'arrow-up'
                  : 'arrow-down'
              }
              size={10}
              color={priorityColor}
              style={styles.badgeIcon}
            />
            <Text
              style={[
                styles.badgeText,
                { color: priorityColor },
              ]}
            >
              {priority.charAt(0).toUpperCase() + priority.slice(1)}
            </Text>
          </View>

          {/* Project badge */}
          {projectName && (
            <View
              style={[
                styles.badge,
                {
                  backgroundColor: projectColor
                    ? `${projectColor}20`
                    : theme.colors.primarySoft,
                },
              ]}
            >
              <Ionicons
                name="folder-outline"
                size={10}
                color={projectColor || theme.colors.primary}
                style={styles.badgeIcon}
              />
              <Text
                style={[
                  styles.badgeText,
                  { color: projectColor || theme.colors.primary },
                ]}
                numberOfLines={1}
              >
                {projectName}
              </Text>
            </View>
          )}

          {/* Status badge (if not pending or completed) */}
          {status !== 'pending' && status !== 'completed' && (
            <View
              style={[
                styles.badge,
                { backgroundColor: `${statusColor}20` },
              ]}
            >
              <Ionicons
                name={status === 'in_progress' ? 'play' : 'pause'}
                size={10}
                color={statusColor}
                style={styles.badgeIcon}
              />
              <Text
                style={[
                  styles.badgeText,
                  { color: statusColor },
                ]}
              >
                {status === 'in_progress' ? 'In Progress' : 'Blocked'}
              </Text>
            </View>
          )}

          {/* Due date */}
          {dueDateFormatted && (
            <View style={styles.dueDateContainer}>
              <Ionicons
                name={isOverdue ? 'alert-circle' : 'calendar-outline'}
                size={12}
                color={isOverdue ? theme.colors.danger : theme.colors.textTertiary}
                style={styles.dueDateIcon}
              />
              <Text
                variant="caption"
                style={[
                  styles.dueDate,
                  {
                    color: isOverdue
                      ? theme.colors.danger
                      : theme.colors.textTertiary,
                  },
                ]}
              >
                {dueDateFormatted}
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Quick action (Start button for pending tasks) - 44px minimum touch target */}
      {status === 'pending' && onStart && (
        <Pressable
          style={({ pressed }) => [
            styles.startButton,
            { backgroundColor: pressed ? theme.colors.primaryLight : theme.colors.primarySoft },
          ]}
          onPress={handleStart}
          accessibilityRole="button"
          accessibilityLabel={`Start task: ${title}`}
        >
          <Ionicons name="play" size={14} color={theme.colors.primary} />
          <Text
            style={[
              styles.startButtonText,
              { color: theme.colors.primary },
            ]}
          >
            Start
          </Text>
        </Pressable>
      )}
    </AnimatedPressable>
  );
}

// Memoize for FlatList performance
export const TaskCard = memo(TaskCardComponent);

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 10,
  },
  completedContainer: {
    opacity: 0.7,
  },
  // 48px touch target area (iOS HIG recommends 44px minimum)
  checkboxTouchArea: {
    width: 48,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: -12,
    marginTop: -12,
    marginBottom: -12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flex: 1,
    marginLeft: 4,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  title: {
    flex: 1,
    fontWeight: '500',
    lineHeight: 22,
  },
  description: {
    marginTop: 4,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    marginTop: 8,
    gap: 6,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  badgeIcon: {
    marginRight: 4,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  dueDateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 'auto',
  },
  dueDateIcon: {
    marginRight: 4,
  },
  dueDate: {
    fontSize: 12,
    fontWeight: '500',
  },
  // 44px minimum touch target for start button
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    marginLeft: 10,
    minHeight: 44,
    gap: 4,
  },
  startButtonText: {
    fontSize: 13,
    fontWeight: '600',
  },
});

export default TaskCard;
