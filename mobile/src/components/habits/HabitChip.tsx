/**
 * HabitChip Component
 * Compact circular habit display with proper touch targets (48px+),
 * haptic feedback, animations, and accessibility support.
 */

import React, { memo, useCallback, useState } from 'react';
import {
  View,
  StyleSheet,
  ViewStyle,
  Pressable,
  ActivityIndicator,
} from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../theme';
import { Text } from '../common';
import { useHaptics } from '../../lib/hooks';

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

// Use Ionicons instead of emojis per UI/UX guidelines
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
  other: 'sparkles',
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

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

function HabitChipComponent({
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
  const haptics = useHaptics();
  const [isLogging, setIsLogging] = useState(false);

  // Animation values
  const scale = useSharedValue(1);
  const celebrationScale = useSharedValue(0);

  const getCategoryColor = useCallback(() => {
    return CATEGORY_COLORS[category?.toLowerCase()] || CATEGORY_COLORS.other;
  }, [category]);

  const getCategoryIcon = useCallback((): keyof typeof Ionicons.glyphMap => {
    return CATEGORY_ICONS[category?.toLowerCase()] || CATEGORY_ICONS.other;
  }, [category]);

  const getSize = useCallback(() => {
    switch (size) {
      case 'sm':
        return { chip: 72, icon: 20, text: 10, touchTarget: 72 };
      case 'lg':
        return { chip: 100, icon: 32, text: 13, touchTarget: 100 };
      default:
        return { chip: 84, icon: 26, text: 11, touchTarget: 84 };
    }
  }, [size]);

  const handlePress = useCallback(async () => {
    if (isCompleted || isLogging) return;

    setIsLogging(true);

    // Bounce animation
    scale.value = withSequence(
      withSpring(0.9, { damping: 10 }),
      withSpring(1.1, { damping: 8 }),
      withSpring(1, { damping: 10 })
    );

    // Celebration effect
    celebrationScale.value = withSequence(
      withTiming(1.5, { duration: 200 }),
      withTiming(0, { duration: 300 })
    );

    // Haptic feedback
    haptics.habitLogged();

    // Execute the actual press handler
    setTimeout(() => {
      onPress?.();
      setIsLogging(false);
    }, 150);
  }, [isCompleted, isLogging, scale, celebrationScale, haptics, onPress]);

  const handlePressIn = useCallback(() => {
    if (isCompleted) return;
    scale.value = withSpring(0.95, { damping: 15 });
    haptics.trigger('selection');
  }, [isCompleted, scale, haptics]);

  const handlePressOut = useCallback(() => {
    scale.value = withSpring(1, { damping: 15 });
  }, [scale]);

  // Animated styles
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const celebrationStyle = useAnimatedStyle(() => ({
    transform: [{ scale: celebrationScale.value }],
    opacity: celebrationScale.value > 0 ? 0.5 : 0,
  }));

  const sizeConfig = getSize();
  const categoryColor = getCategoryColor();
  const categoryIcon = getCategoryIcon();

  // Ensure touch target is at least 48px per iOS HIG
  const touchSize = Math.max(sizeConfig.touchTarget, 48);

  return (
    <AnimatedPressable
      style={[
        styles.container,
        {
          width: touchSize,
          minHeight: touchSize,
          backgroundColor: isCompleted
            ? `${theme.colors.success}15`
            : theme.colors.bgSurface,
          borderColor: isCompleted
            ? theme.colors.success
            : theme.colors.border,
        },
        animatedStyle,
        style,
      ]}
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      disabled={isCompleted || isLogging}
      accessibilityRole="button"
      accessibilityLabel={`${name} habit. ${isCompleted ? 'Completed' : 'Tap to log'}. ${currentStreak > 0 ? `${currentStreak} day streak` : ''}`}
      accessibilityState={{ disabled: isCompleted }}
    >
      {/* Celebration ring effect */}
      <Animated.View
        style={[
          styles.celebrationRing,
          { borderColor: theme.colors.success },
          celebrationStyle,
        ]}
      />

      {/* Icon container */}
      <View
        style={[
          styles.iconContainer,
          {
            width: sizeConfig.icon + 12,
            height: sizeConfig.icon + 12,
            backgroundColor: isCompleted
              ? theme.colors.success
              : `${categoryColor}20`,
          },
        ]}
      >
        {isLogging ? (
          <ActivityIndicator size="small" color={categoryColor} />
        ) : isCompleted ? (
          <Ionicons name="checkmark" size={sizeConfig.icon} color="#fff" />
        ) : (
          <Ionicons name={categoryIcon} size={sizeConfig.icon} color={categoryColor} />
        )}
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
          <Ionicons name="flame" size={10} color="#fff" />
          <Text style={styles.streakText}>
            {currentStreak}
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
    </AnimatedPressable>
  );
}

// Compact inline version for horizontal lists
function HabitChipInlineComponent({
  id,
  name,
  category,
  currentStreak,
  isCompleted,
  onPress,
  style,
}: HabitChipProps) {
  const { theme } = useTheme();
  const haptics = useHaptics();
  const [isLogging, setIsLogging] = useState(false);

  const scale = useSharedValue(1);

  const getCategoryColor = useCallback(() => {
    return CATEGORY_COLORS[category?.toLowerCase()] || CATEGORY_COLORS.other;
  }, [category]);

  const getCategoryIcon = useCallback((): keyof typeof Ionicons.glyphMap => {
    return CATEGORY_ICONS[category?.toLowerCase()] || CATEGORY_ICONS.other;
  }, [category]);

  const handlePress = useCallback(async () => {
    if (isCompleted || isLogging) return;

    setIsLogging(true);
    scale.value = withSequence(
      withSpring(0.95, { damping: 10 }),
      withSpring(1, { damping: 8 })
    );

    haptics.habitLogged();

    setTimeout(() => {
      onPress?.();
      setIsLogging(false);
    }, 150);
  }, [isCompleted, isLogging, scale, haptics, onPress]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const categoryColor = getCategoryColor();
  const categoryIcon = getCategoryIcon();

  return (
    <AnimatedPressable
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
        animatedStyle,
        style,
      ]}
      onPress={handlePress}
      disabled={isCompleted || isLogging}
      accessibilityRole="button"
      accessibilityLabel={`${name} habit. ${isCompleted ? 'Completed' : 'Tap to log'}`}
    >
      <View
        style={[
          styles.inlineIconContainer,
          {
            backgroundColor: isCompleted
              ? theme.colors.success
              : `${categoryColor}20`,
          },
        ]}
      >
        {isLogging ? (
          <ActivityIndicator size="small" color={categoryColor} />
        ) : isCompleted ? (
          <Ionicons name="checkmark" size={14} color="#fff" />
        ) : (
          <Ionicons name={categoryIcon} size={14} color={categoryColor} />
        )}
      </View>
      <Text
        variant="bodySmall"
        color={isCompleted ? 'success' : 'primary'}
        style={styles.inlineName}
        numberOfLines={1}
      >
        {name}
      </Text>
      {currentStreak > 0 && (
        <View style={styles.inlineStreakContainer}>
          <Ionicons name="flame" size={12} color={theme.colors.warning} />
          <Text style={[styles.inlineStreak, { color: theme.colors.warning }]}>
            {currentStreak}
          </Text>
        </View>
      )}
    </AnimatedPressable>
  );
}

// Memoize for FlatList performance
export const HabitChip = memo(HabitChipComponent);
export const HabitChipInline = memo(HabitChipInlineComponent);

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    position: 'relative',
  },
  celebrationRing: {
    position: 'absolute',
    top: -10,
    left: -10,
    right: -10,
    bottom: -10,
    borderRadius: 26,
    borderWidth: 3,
  },
  iconContainer: {
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
  },
  name: {
    textAlign: 'center',
    lineHeight: 14,
    fontWeight: '500',
  },
  streakBadge: {
    position: 'absolute',
    top: -6,
    right: -6,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 12,
    minWidth: 32,
    justifyContent: 'center',
    gap: 2,
  },
  streakText: {
    fontSize: 11,
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
    opacity: 0.2,
  },
  // Inline styles - 48px minimum height for touch target
  inlineContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 24,
    borderWidth: 1,
    marginRight: 8,
    minHeight: 48,
  },
  inlineIconContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  inlineName: {
    fontWeight: '500',
    maxWidth: 100,
  },
  inlineStreakContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 8,
    gap: 2,
  },
  inlineStreak: {
    fontSize: 12,
    fontWeight: '600',
  },
});

export default HabitChip;
