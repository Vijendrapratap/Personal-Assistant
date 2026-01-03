/**
 * TransparencyPanel - Shows Alfred's thinking process
 * Inspired by Manus.ai's transparent agent view
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  Animated,
  ScrollView,
} from 'react-native';
import { useTheme } from '../../theme';
import { Text } from '../common';

export interface ThinkingStep {
  id: string;
  text: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  detail?: string;
}

interface TransparencyPanelProps {
  steps: ThinkingStep[];
  isExpanded?: boolean;
  onToggle?: () => void;
  title?: string;
}

function StepItem({ step, index }: { step: ThinkingStep; index: number }) {
  const { theme } = useTheme();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        delay: index * 100,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 100,
        friction: 8,
        delay: index * 100,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const getStatusIcon = () => {
    switch (step.status) {
      case 'completed':
        return '✓';
      case 'in_progress':
        return '◉';
      case 'error':
        return '✗';
      default:
        return '○';
    }
  };

  const getStatusColor = () => {
    switch (step.status) {
      case 'completed':
        return theme.colors.success;
      case 'in_progress':
        return theme.colors.primary;
      case 'error':
        return theme.colors.danger;
      default:
        return theme.colors.textTertiary;
    }
  };

  return (
    <Animated.View
      style={[
        styles.stepItem,
        {
          opacity: fadeAnim,
          transform: [{ scale: scaleAnim }],
        },
      ]}
    >
      <View style={styles.stepIconContainer}>
        <Text
          style={[
            styles.stepIcon,
            { color: getStatusColor() },
            step.status === 'in_progress' && styles.stepIconPulsing,
          ]}
        >
          {getStatusIcon()}
        </Text>
        {index > 0 && (
          <View
            style={[
              styles.stepLine,
              {
                backgroundColor:
                  step.status === 'pending'
                    ? theme.colors.border
                    : getStatusColor(),
              },
            ]}
          />
        )}
      </View>
      <View style={styles.stepContent}>
        <Text
          variant="bodySmall"
          style={{
            color:
              step.status === 'pending'
                ? theme.colors.textTertiary
                : theme.colors.textPrimary,
          }}
        >
          {step.text}
        </Text>
        {step.detail && step.status === 'completed' && (
          <Text
            variant="caption"
            color="tertiary"
            style={styles.stepDetail}
          >
            {step.detail}
          </Text>
        )}
      </View>
    </Animated.View>
  );
}

export function TransparencyPanel({
  steps,
  isExpanded = true,
  onToggle,
  title = "Alfred is working...",
}: TransparencyPanelProps) {
  const { theme } = useTheme();

  const completedCount = steps.filter((s) => s.status === 'completed').length;
  const isComplete = completedCount === steps.length && steps.length > 0;
  const hasError = steps.some((s) => s.status === 'error');

  if (steps.length === 0) return null;

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.bgSurface,
          borderColor: hasError
            ? theme.colors.danger + '40'
            : isComplete
            ? theme.colors.success + '40'
            : theme.colors.border,
        },
      ]}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View
            style={[
              styles.statusDot,
              {
                backgroundColor: hasError
                  ? theme.colors.danger
                  : isComplete
                  ? theme.colors.success
                  : theme.colors.primary,
              },
            ]}
          />
          <Text variant="bodySmall" style={{ fontWeight: '600' }}>
            {hasError
              ? 'Something went wrong'
              : isComplete
              ? 'Done'
              : title}
          </Text>
        </View>
        <Text variant="caption" color="tertiary">
          {completedCount}/{steps.length}
        </Text>
      </View>

      {/* Steps */}
      {isExpanded && (
        <ScrollView
          style={styles.stepsContainer}
          showsVerticalScrollIndicator={false}
        >
          {steps.map((step, index) => (
            <StepItem key={step.id} step={step} index={index} />
          ))}
        </ScrollView>
      )}

      {/* Collapse indicator */}
      {onToggle && steps.length > 3 && (
        <View style={styles.collapseBar}>
          <Text
            variant="caption"
            color="tertiary"
            onPress={onToggle}
            style={styles.collapseText}
          >
            {isExpanded ? 'Show less' : `Show ${steps.length} steps`}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    borderWidth: 1,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 10,
  },
  stepsContainer: {
    paddingHorizontal: 14,
    paddingBottom: 14,
    maxHeight: 200,
  },
  stepItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  stepIconContainer: {
    width: 24,
    alignItems: 'center',
    position: 'relative',
  },
  stepIcon: {
    fontSize: 14,
    fontWeight: '700',
  },
  stepIconPulsing: {
    // Animation would be applied here
  },
  stepLine: {
    position: 'absolute',
    top: -12,
    width: 2,
    height: 12,
  },
  stepContent: {
    flex: 1,
    paddingLeft: 8,
  },
  stepDetail: {
    marginTop: 2,
    fontStyle: 'italic',
  },
  collapseBar: {
    alignItems: 'center',
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.05)',
  },
  collapseText: {
    textDecorationLine: 'underline',
  },
});

export default TransparencyPanel;
