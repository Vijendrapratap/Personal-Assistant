/**
 * TaskCard Component
 * Displays a task with swipe actions, priority colors, and project badge
 */

import React from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  ViewStyle,
} from 'react-native';
import { useTheme } from '../../theme';
import { Text } from '../common';

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

export function TaskCard({
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

  const getPriorityColor = () => {
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
  };

  const getPriorityBgColor = () => {
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
  };

  const getStatusColor = () => {
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
  };

  const formatDueDate = () => {
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
  };

  const isCompleted = status === 'completed';
  const dueDateFormatted = formatDueDate();

  return (
    <TouchableOpacity
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.bgSurface,
          borderColor: theme.colors.border,
        },
        isCompleted && styles.completedContainer,
        style,
      ]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {/* Checkbox */}
      <TouchableOpacity
        style={[
          styles.checkbox,
          {
            borderColor: getPriorityColor(),
            backgroundColor: isCompleted ? theme.colors.success : 'transparent',
          },
        ]}
        onPress={onComplete}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      >
        {isCompleted && (
          <Text style={styles.checkmark}>✓</Text>
        )}
      </TouchableOpacity>

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
              { backgroundColor: getPriorityBgColor() },
            ]}
          >
            <Text
              style={[
                styles.badgeText,
                { color: getPriorityColor() },
              ]}
            >
              {priority.toUpperCase()}
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

          {/* Status badge (if not pending) */}
          {status !== 'pending' && status !== 'completed' && (
            <View
              style={[
                styles.badge,
                { backgroundColor: `${getStatusColor()}20` },
              ]}
            >
              <Text
                style={[
                  styles.badgeText,
                  { color: getStatusColor() },
                ]}
              >
                {status.replace('_', ' ').toUpperCase()}
              </Text>
            </View>
          )}

          {/* Due date */}
          {dueDateFormatted && (
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
              {isOverdue && '! '}
              {dueDateFormatted}
            </Text>
          )}
        </View>
      </View>

      {/* Quick action (Start button for pending tasks) */}
      {status === 'pending' && onStart && (
        <TouchableOpacity
          style={[
            styles.startButton,
            { backgroundColor: theme.colors.primarySoft },
          ]}
          onPress={onStart}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Text
            style={[
              styles.startButtonText,
              { color: theme.colors.primary },
            ]}
          >
            Start
          </Text>
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
}

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
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  checkmark: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
  },
  content: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  title: {
    flex: 1,
    fontWeight: '500',
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
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  dueDate: {
    marginLeft: 'auto',
  },
  startButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    marginLeft: 10,
  },
  startButtonText: {
    fontSize: 13,
    fontWeight: '600',
  },
});

export default TaskCard;
