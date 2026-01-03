/**
 * AnimatedCard - Card with press animations and haptic feedback
 */

import React, { useCallback, useRef } from 'react';
import {
  Animated,
  Pressable,
  StyleSheet,
  ViewStyle,
  GestureResponderEvent,
} from 'react-native';
import { useTheme } from '../../theme';
import { useHaptics } from '../../lib/hooks/useHaptics';

interface AnimatedCardProps {
  children: React.ReactNode;
  onPress?: () => void;
  onLongPress?: () => void;
  disabled?: boolean;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
  style?: ViewStyle;
  hapticType?: 'light' | 'medium' | 'selection' | 'none';
  scaleOnPress?: number;
}

export function AnimatedCard({
  children,
  onPress,
  onLongPress,
  disabled = false,
  variant = 'default',
  style,
  hapticType = 'light',
  scaleOnPress = 0.98,
}: AnimatedCardProps) {
  const { theme } = useTheme();
  const haptics = useHaptics();
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const opacityAnim = useRef(new Animated.Value(1)).current;

  const getBackgroundColor = () => {
    switch (variant) {
      case 'primary':
        return theme.colors.primary;
      case 'success':
        return theme.colors.success + '20';
      case 'warning':
        return theme.colors.warning + '20';
      case 'danger':
        return theme.colors.danger + '20';
      default:
        return theme.colors.bgSurface;
    }
  };

  const handlePressIn = useCallback(() => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: scaleOnPress,
        useNativeDriver: true,
        speed: 50,
        bounciness: 4,
      }),
      Animated.timing(opacityAnim, {
        toValue: 0.9,
        duration: 100,
        useNativeDriver: true,
      }),
    ]).start();
  }, [scaleOnPress]);

  const handlePressOut = useCallback(() => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
        speed: 50,
        bounciness: 8,
      }),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 100,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handlePress = useCallback(() => {
    if (hapticType !== 'none') {
      haptics.trigger(hapticType);
    }
    onPress?.();
  }, [hapticType, onPress, haptics]);

  const handleLongPress = useCallback(() => {
    haptics.trigger('medium');
    onLongPress?.();
  }, [onLongPress, haptics]);

  return (
    <Pressable
      onPress={handlePress}
      onLongPress={onLongPress ? handleLongPress : undefined}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      disabled={disabled || !onPress}
    >
      <Animated.View
        style={[
          styles.card,
          {
            backgroundColor: getBackgroundColor(),
            borderRadius: theme.radius.lg,
            borderColor: theme.colors.border,
            transform: [{ scale: scaleAnim }],
            opacity: opacityAnim,
          },
          disabled && styles.disabled,
          style,
        ]}
      >
        {children}
      </Animated.View>
    </Pressable>
  );
}

/**
 * AnimatedButton - Button with press animations
 */
interface AnimatedButtonProps {
  children: React.ReactNode;
  onPress: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  style?: ViewStyle;
  fullWidth?: boolean;
}

export function AnimatedButton({
  children,
  onPress,
  disabled = false,
  variant = 'primary',
  size = 'md',
  style,
  fullWidth = false,
}: AnimatedButtonProps) {
  const { theme } = useTheme();
  const haptics = useHaptics();
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const getStyles = () => {
    const base = {
      backgroundColor: theme.colors.primary,
      borderColor: 'transparent',
      borderWidth: 0,
    };

    switch (variant) {
      case 'secondary':
        return {
          ...base,
          backgroundColor: theme.colors.bgSurface,
          borderColor: theme.colors.border,
          borderWidth: 1,
        };
      case 'ghost':
        return {
          ...base,
          backgroundColor: 'transparent',
        };
      case 'danger':
        return {
          ...base,
          backgroundColor: theme.colors.danger,
        };
      default:
        return base;
    }
  };

  const getHeight = () => {
    switch (size) {
      case 'sm':
        return theme.componentSize.button.sm;
      case 'lg':
        return theme.componentSize.button.lg;
      default:
        return theme.componentSize.button.md;
    }
  };

  const handlePressIn = () => {
    Animated.spring(scaleAnim, {
      toValue: 0.96,
      useNativeDriver: true,
      speed: 50,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
      speed: 50,
      bounciness: 6,
    }).start();
  };

  const handlePress = () => {
    haptics.buttonPress();
    onPress();
  };

  const buttonStyles = getStyles();

  return (
    <Pressable
      onPress={handlePress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      disabled={disabled}
    >
      <Animated.View
        style={[
          styles.button,
          {
            height: getHeight(),
            backgroundColor: buttonStyles.backgroundColor,
            borderColor: buttonStyles.borderColor,
            borderWidth: buttonStyles.borderWidth,
            borderRadius: theme.radius.md,
            transform: [{ scale: scaleAnim }],
          },
          fullWidth && styles.fullWidth,
          disabled && styles.disabled,
          style,
        ]}
      >
        {children}
      </Animated.View>
    </Pressable>
  );
}

/**
 * SwipeableCard - Card with swipe actions
 */
interface SwipeableCardProps {
  children: React.ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  leftAction?: React.ReactNode;
  rightAction?: React.ReactNode;
  style?: ViewStyle;
}

export function SwipeableCard({
  children,
  onSwipeLeft,
  onSwipeRight,
  leftAction,
  rightAction,
  style,
}: SwipeableCardProps) {
  const { theme } = useTheme();
  const haptics = useHaptics();
  const translateX = useRef(new Animated.Value(0)).current;
  const startX = useRef(0);

  const handleTouchStart = (e: GestureResponderEvent) => {
    startX.current = e.nativeEvent.pageX;
  };

  const handleTouchMove = (e: GestureResponderEvent) => {
    const diff = e.nativeEvent.pageX - startX.current;
    // Limit swipe distance
    const limited = Math.max(-100, Math.min(100, diff));
    translateX.setValue(limited);
  };

  const handleTouchEnd = () => {
    const currentValue = (translateX as any)._value;

    if (currentValue < -60 && onSwipeLeft) {
      haptics.swipeAction();
      Animated.timing(translateX, {
        toValue: -100,
        duration: 200,
        useNativeDriver: true,
      }).start(() => {
        onSwipeLeft();
        translateX.setValue(0);
      });
    } else if (currentValue > 60 && onSwipeRight) {
      haptics.swipeAction();
      Animated.timing(translateX, {
        toValue: 100,
        duration: 200,
        useNativeDriver: true,
      }).start(() => {
        onSwipeRight();
        translateX.setValue(0);
      });
    } else {
      Animated.spring(translateX, {
        toValue: 0,
        useNativeDriver: true,
      }).start();
    }
  };

  return (
    <Animated.View
      style={[
        styles.swipeableContainer,
        {
          backgroundColor: theme.colors.bgSurface,
          borderRadius: theme.radius.lg,
        },
        style,
      ]}
    >
      {/* Background actions */}
      <Animated.View style={[styles.swipeAction, styles.swipeActionLeft]}>
        {leftAction}
      </Animated.View>
      <Animated.View style={[styles.swipeAction, styles.swipeActionRight]}>
        {rightAction}
      </Animated.View>

      {/* Main content */}
      <Animated.View
        style={[
          styles.swipeableContent,
          {
            backgroundColor: theme.colors.bgSurface,
            transform: [{ translateX }],
          },
        ]}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {children}
      </Animated.View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 16,
    borderWidth: 1,
  },
  disabled: {
    opacity: 0.5,
  },
  button: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  fullWidth: {
    width: '100%',
  },
  swipeableContainer: {
    position: 'relative',
    overflow: 'hidden',
  },
  swipeableContent: {
    zIndex: 1,
  },
  swipeAction: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  swipeActionLeft: {
    left: 0,
  },
  swipeActionRight: {
    right: 0,
  },
});

export default AnimatedCard;
