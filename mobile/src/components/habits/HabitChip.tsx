/**
 * HabitChip Component
 * Compact circular habit display with streak badge
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

export interface HabitChipProps {
  id: string;
  name: string;
  category: string;
  currentStreak: number;
  isCompleted: boolean;
  onPress?: () => void;
  size?: 'sm' | 'md' | 'lg';
  style?: ViewStyle;
}

const CATEGORY_EMOJIS: Record<string, string> = {
  fitness: '💪',
  health: '❤️',
  productivity: '⚡',
  learning: '📚',
  mindfulness: '🧘',
  social: '👥',
  finance: '💰',
  creativity: '🎨',
  work: '💼',
  personal: '🌟',
  other: '✨',
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
  other: '#6B7280',
};

export function HabitChip({
  id,
  name,
  category,
  currentStreak,
  isCompleted,
  onPress,
  size = 'md',
  style,
}: HabitChipProps) {
  const { theme } = useTheme();

  const getCategoryColor = () => {
    return CATEGORY_COLORS[category?.toLowerCase()] || CATEGORY_COLORS.other;
  };

  const getCategoryEmoji = () => {
    return CATEGORY_EMOJIS[category?.toLowerCase()] || CATEGORY_EMOJIS.other;
  };

  const getSize = () => {
    switch (size) {
      case 'sm':
        return { chip: 64, emoji: 18, text: 10 };
      case 'lg':
        return { chip: 96, emoji: 28, text: 13 };
      default:
        return { chip: 80, emoji: 24, text: 11 };
    }
  };

  const sizeConfig = getSize();
  const categoryColor = getCategoryColor();

  return (
    <TouchableOpacity
      style={[
        styles.container,
        {
          width: sizeConfig.chip,
          height: sizeConfig.chip,
          backgroundColor: isCompleted
            ? `${theme.colors.success}15`
            : theme.colors.bgSurface,
          borderColor: isCompleted
            ? theme.colors.success
            : theme.colors.border,
        },
        style,
      ]}
      onPress={onPress}
      disabled={isCompleted}
      activeOpacity={0.7}
    >
      {/* Completed checkmark or category emoji */}
      <View
        style={[
          styles.iconContainer,
          isCompleted && {
            backgroundColor: theme.colors.success,
          },
        ]}
      >
        <Text style={{ fontSize: sizeConfig.emoji }}>
          {isCompleted ? '✓' : getCategoryEmoji()}
        </Text>
      </View>

      {/* Habit name */}
      <Text
        variant="caption"
        color={isCompleted ? 'success' : 'primary'}
        style={[
          styles.name,
          { fontSize: sizeConfig.text },
        ]}
        numberOfLines={2}
      >
        {name}
      </Text>

      {/* Streak badge */}
      {currentStreak > 0 && (
        <View
          style={[
            styles.streakBadge,
            {
              backgroundColor: isCompleted
                ? theme.colors.success
                : theme.colors.warning,
            },
          ]}
        >
          <Text style={styles.streakText}>
            🔥{currentStreak}
          </Text>
        </View>
      )}

      {/* Category indicator ring */}
      {!isCompleted && (
        <View
          style={[
            styles.categoryRing,
            { borderColor: categoryColor },
          ]}
        />
      )}
    </TouchableOpacity>
  );
}

// Compact inline version for horizontal lists
export function HabitChipInline({
  id,
  name,
  category,
  currentStreak,
  isCompleted,
  onPress,
  style,
}: HabitChipProps) {
  const { theme } = useTheme();

  const getCategoryColor = () => {
    return CATEGORY_COLORS[category?.toLowerCase()] || CATEGORY_COLORS.other;
  };

  const getCategoryEmoji = () => {
    return CATEGORY_EMOJIS[category?.toLowerCase()] || CATEGORY_EMOJIS.other;
  };

  return (
    <TouchableOpacity
      style={[
        styles.inlineContainer,
        {
          backgroundColor: isCompleted
            ? `${theme.colors.success}15`
            : theme.colors.bgSurface,
          borderColor: isCompleted
            ? theme.colors.success
            : theme.colors.border,
        },
        style,
      ]}
      onPress={onPress}
      disabled={isCompleted}
      activeOpacity={0.7}
    >
      <Text style={styles.inlineEmoji}>
        {isCompleted ? '✓' : getCategoryEmoji()}
      </Text>
      <Text
        variant="bodySmall"
        color={isCompleted ? 'success' : 'primary'}
        style={styles.inlineName}
        numberOfLines={1}
      >
        {name}
      </Text>
      {currentStreak > 0 && (
        <Text style={styles.inlineStreak}>
          🔥{currentStreak}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    position: 'relative',
  },
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  name: {
    textAlign: 'center',
    lineHeight: 14,
  },
  streakBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    minWidth: 28,
    alignItems: 'center',
  },
  streakText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#fff',
  },
  categoryRing: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: 16,
    borderWidth: 2,
    opacity: 0.3,
  },
  // Inline styles
  inlineContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    marginRight: 8,
  },
  inlineEmoji: {
    fontSize: 16,
    marginRight: 6,
  },
  inlineName: {
    fontWeight: '500',
    maxWidth: 100,
  },
  inlineStreak: {
    fontSize: 11,
    marginLeft: 6,
  },
});

export default HabitChip;
