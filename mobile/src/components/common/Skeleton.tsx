/**
 * Skeleton - Loading placeholder components
 *
 * Provides smooth shimmer animations for loading states
 */

import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, ViewStyle, Dimensions } from 'react-native';
import { useTheme } from '../../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: ViewStyle;
}

/**
 * Basic skeleton element with shimmer animation
 */
export function Skeleton({
  width = '100%',
  height = 16,
  borderRadius = 8,
  style,
}: SkeletonProps) {
  const { theme } = useTheme();
  const shimmerAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(shimmerAnim, {
        toValue: 1,
        duration: 1500,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  const translateX = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-SCREEN_WIDTH, SCREEN_WIDTH],
  });

  return (
    <View
      style={[
        styles.skeleton,
        {
          width,
          height,
          borderRadius,
          backgroundColor: theme.colors.bgSurface,
          overflow: 'hidden',
        },
        style,
      ]}
    >
      <Animated.View
        style={[
          styles.shimmer,
          {
            transform: [{ translateX }],
            backgroundColor: theme.colors.bgHover,
          },
        ]}
      />
    </View>
  );
}

/**
 * Skeleton for text lines
 */
export function SkeletonText({
  lines = 1,
  lineHeight = 16,
  spacing = 8,
  lastLineWidth = '60%',
  style,
}: {
  lines?: number;
  lineHeight?: number;
  spacing?: number;
  lastLineWidth?: string | number;
  style?: ViewStyle;
}) {
  return (
    <View style={style}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          height={lineHeight}
          width={i === lines - 1 && lines > 1 ? lastLineWidth : '100%'}
          style={i < lines - 1 ? { marginBottom: spacing } : undefined}
        />
      ))}
    </View>
  );
}

/**
 * Skeleton for avatar/circular elements
 */
export function SkeletonAvatar({
  size = 48,
  style,
}: {
  size?: number;
  style?: ViewStyle;
}) {
  return <Skeleton width={size} height={size} borderRadius={size / 2} style={style} />;
}

/**
 * Skeleton for cards
 */
export function SkeletonCard({ style }: { style?: ViewStyle }) {
  const { theme } = useTheme();

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: theme.colors.bgSurface,
          borderRadius: theme.radius.lg,
        },
        style,
      ]}
    >
      <View style={styles.cardHeader}>
        <SkeletonAvatar size={40} />
        <View style={styles.cardHeaderText}>
          <Skeleton width="60%" height={14} />
          <Skeleton width="40%" height={12} style={{ marginTop: 6 }} />
        </View>
      </View>
      <SkeletonText lines={2} style={{ marginTop: 12 }} />
    </View>
  );
}

/**
 * Skeleton for the Today screen
 */
export function TodayScreenSkeleton() {
  const { theme } = useTheme();

  return (
    <View style={[styles.screenContainer, { backgroundColor: theme.colors.bg }]}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Skeleton width={100} height={12} />
          <Skeleton width={180} height={28} style={{ marginTop: 8 }} />
        </View>
        <SkeletonAvatar size={44} />
      </View>

      {/* Status */}
      <Skeleton width="70%" height={14} style={{ marginTop: 8, marginBottom: 24 }} />

      {/* Focus Card */}
      <Skeleton width={80} height={12} style={{ marginBottom: 12 }} />
      <View
        style={[
          styles.focusCard,
          { backgroundColor: theme.colors.primary + '20', borderRadius: theme.radius.lg },
        ]}
      >
        <Skeleton width={100} height={20} borderRadius={6} />
        <Skeleton width="80%" height={24} style={{ marginTop: 12 }} />
        <Skeleton width="50%" height={14} style={{ marginTop: 8 }} />
        <View style={styles.focusActions}>
          <Skeleton width={80} height={36} borderRadius={10} />
          <Skeleton width={80} height={36} borderRadius={10} />
        </View>
      </View>

      {/* Habits */}
      <View style={styles.sectionHeader}>
        <Skeleton width={100} height={12} />
        <Skeleton width={30} height={12} />
      </View>
      <View style={styles.habitsGrid}>
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Skeleton
            key={i}
            width="30%"
            height={80}
            borderRadius={16}
            style={{ marginBottom: 10 }}
          />
        ))}
      </View>

      {/* Due Today */}
      <Skeleton width={80} height={12} style={{ marginTop: 24, marginBottom: 12 }} />
      {[1, 2, 3].map((i) => (
        <SkeletonCard key={i} style={{ marginBottom: 8 }} />
      ))}
    </View>
  );
}

/**
 * Skeleton for task list
 */
export function TaskListSkeleton({ count = 5 }: { count?: number }) {
  const { theme } = useTheme();

  return (
    <View style={{ padding: 20 }}>
      {Array.from({ length: count }).map((_, i) => (
        <View
          key={i}
          style={[
            styles.taskItem,
            {
              backgroundColor: theme.colors.bgSurface,
              borderRadius: theme.radius.md,
            },
          ]}
        >
          <Skeleton width={22} height={22} borderRadius={11} />
          <View style={styles.taskContent}>
            <Skeleton width="70%" height={16} />
            <Skeleton width="40%" height={12} style={{ marginTop: 6 }} />
          </View>
        </View>
      ))}
    </View>
  );
}

/**
 * Skeleton for calendar/timeline
 */
export function TimelineSkeleton() {
  const { theme } = useTheme();

  return (
    <View style={{ padding: 20 }}>
      {/* Day strip */}
      <View style={styles.dayStrip}>
        {[1, 2, 3, 4, 5, 6, 7].map((i) => (
          <View key={i} style={styles.dayItem}>
            <Skeleton width={24} height={12} />
            <Skeleton width={32} height={32} borderRadius={16} style={{ marginTop: 4 }} />
          </View>
        ))}
      </View>

      {/* Timeline */}
      <View style={{ marginTop: 24 }}>
        {[9, 10, 11, 12, 13, 14].map((hour) => (
          <View key={hour} style={styles.timeSlot}>
            <Skeleton width={40} height={12} />
            <View
              style={[
                styles.timeSlotContent,
                { borderColor: theme.colors.border },
              ]}
            >
              {hour === 10 || hour === 14 ? (
                <Skeleton width="80%" height={60} borderRadius={8} />
              ) : null}
            </View>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  skeleton: {
    overflow: 'hidden',
  },
  shimmer: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: '50%',
    opacity: 0.3,
  },
  card: {
    padding: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardHeaderText: {
    flex: 1,
    marginLeft: 12,
  },
  screenContainer: {
    flex: 1,
    padding: 20,
    paddingTop: 60,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  focusCard: {
    padding: 20,
  },
  focusActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 24,
    marginBottom: 12,
  },
  habitsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  taskItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    marginBottom: 8,
  },
  taskContent: {
    flex: 1,
    marginLeft: 12,
  },
  dayStrip: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  dayItem: {
    alignItems: 'center',
  },
  timeSlot: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  timeSlotContent: {
    flex: 1,
    marginLeft: 12,
    minHeight: 60,
    borderLeftWidth: 1,
    paddingLeft: 12,
  },
});

export default Skeleton;
