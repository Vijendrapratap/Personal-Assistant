/**
 * useHaptics - Hook for haptic feedback throughout the app
 *
 * Provides consistent haptic feedback for various interactions:
 * - Light: Button presses, selections
 * - Medium: Task completion, habit logging
 * - Heavy: Errors, important actions
 * - Success: Celebrations, achievements
 */

import * as Haptics from 'expo-haptics';
import { useCallback } from 'react';

type HapticType = 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' | 'selection';

export function useHaptics() {
  /**
   * Trigger haptic feedback
   */
  const trigger = useCallback(async (type: HapticType = 'light') => {
    try {
      switch (type) {
        case 'light':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          break;
        case 'medium':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          break;
        case 'heavy':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
          break;
        case 'success':
          await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          break;
        case 'warning':
          await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
          break;
        case 'error':
          await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
          break;
        case 'selection':
          await Haptics.selectionAsync();
          break;
      }
    } catch (e) {
      // Haptics not supported on this device
      console.debug('Haptics not available');
    }
  }, []);

  /**
   * Pre-defined haptic patterns for common actions
   */
  const patterns = {
    // Task completed - satisfying double tap
    taskComplete: useCallback(async () => {
      await trigger('medium');
      setTimeout(() => trigger('success'), 100);
    }, [trigger]),

    // Habit logged - celebratory
    habitLogged: useCallback(async () => {
      await trigger('success');
    }, [trigger]),

    // Streak milestone - extra celebration
    streakMilestone: useCallback(async () => {
      await trigger('heavy');
      setTimeout(() => trigger('success'), 150);
      setTimeout(() => trigger('light'), 300);
    }, [trigger]),

    // Button press - subtle feedback
    buttonPress: useCallback(async () => {
      await trigger('light');
    }, [trigger]),

    // Tab switch - selection feedback
    tabSwitch: useCallback(async () => {
      await trigger('selection');
    }, [trigger]),

    // Swipe action - medium impact
    swipeAction: useCallback(async () => {
      await trigger('medium');
    }, [trigger]),

    // Error occurred
    error: useCallback(async () => {
      await trigger('error');
    }, [trigger]),

    // Card dismissed
    cardDismiss: useCallback(async () => {
      await trigger('light');
    }, [trigger]),

    // Pull to refresh
    pullRefresh: useCallback(async () => {
      await trigger('medium');
    }, [trigger]),

    // Voice recording start
    voiceStart: useCallback(async () => {
      await trigger('medium');
    }, [trigger]),

    // Voice recording stop
    voiceStop: useCallback(async () => {
      await trigger('heavy');
    }, [trigger]),
  };

  return {
    trigger,
    ...patterns,
  };
}

export default useHaptics;
