/**
 * AnimatedTabBar - Custom tab bar with animations and haptic feedback
 */

import React, { useRef, useEffect } from 'react';
import {
  View,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../theme';
import { useHaptics } from '../../lib/hooks/useHaptics';
import { Text } from '../common';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface TabBarProps {
  state: any;
  descriptors: any;
  navigation: any;
}

const TAB_ICONS: Record<string, string> = {
  Today: '☀️',
  Do: '✓',
  Focus: '📅',
  You: '👤',
};

export function AnimatedTabBar({ state, descriptors, navigation }: TabBarProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const haptics = useHaptics();

  // Animation refs for each tab
  const scaleAnims = useRef(
    state.routes.map(() => new Animated.Value(1))
  ).current;
  const translateAnims = useRef(
    state.routes.map(() => new Animated.Value(0))
  ).current;

  // Indicator position
  const indicatorAnim = useRef(new Animated.Value(0)).current;
  const tabWidth = (SCREEN_WIDTH - 40) / state.routes.length;

  // Animate indicator on tab change
  useEffect(() => {
    Animated.spring(indicatorAnim, {
      toValue: state.index * tabWidth,
      useNativeDriver: true,
      speed: 15,
      bounciness: 6,
    }).start();

    // Scale animation for active tab
    state.routes.forEach((_: any, index: number) => {
      Animated.spring(scaleAnims[index], {
        toValue: index === state.index ? 1.1 : 1,
        useNativeDriver: true,
        speed: 20,
      }).start();

      Animated.spring(translateAnims[index], {
        toValue: index === state.index ? -4 : 0,
        useNativeDriver: true,
        speed: 20,
      }).start();
    });
  }, [state.index]);

  const handleTabPress = (route: any, index: number) => {
    const event = navigation.emit({
      type: 'tabPress',
      target: route.key,
      canPreventDefault: true,
    });

    if (!event.defaultPrevented) {
      haptics.tabSwitch();
      navigation.navigate(route.name);
    }
  };

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.bgElevated,
          borderTopColor: theme.colors.border,
          paddingBottom: insets.bottom + 8,
        },
      ]}
    >
      {/* Animated indicator */}
      <Animated.View
        style={[
          styles.indicator,
          {
            width: tabWidth - 20,
            backgroundColor: theme.colors.primary + '20',
            transform: [{ translateX: Animated.add(indicatorAnim, 10) }],
          },
        ]}
      />

      {state.routes.map((route: any, index: number) => {
        const { options } = descriptors[route.key];
        const label = options.tabBarLabel ?? options.title ?? route.name;
        const isFocused = state.index === index;

        return (
          <TouchableOpacity
            key={route.key}
            accessibilityRole="button"
            accessibilityState={isFocused ? { selected: true } : {}}
            accessibilityLabel={options.tabBarAccessibilityLabel}
            testID={options.tabBarTestID}
            onPress={() => handleTabPress(route, index)}
            style={styles.tab}
            activeOpacity={0.7}
          >
            <Animated.View
              style={[
                styles.tabContent,
                {
                  transform: [
                    { scale: scaleAnims[index] },
                    { translateY: translateAnims[index] },
                  ],
                },
              ]}
            >
              <Animated.Text
                style={[
                  styles.icon,
                  {
                    opacity: isFocused ? 1 : 0.6,
                  },
                ]}
              >
                {TAB_ICONS[route.name] || '•'}
              </Animated.Text>
              <Text
                variant="caption"
                style={[
                  styles.label,
                  {
                    color: isFocused
                      ? theme.colors.primary
                      : theme.colors.textTertiary,
                    fontWeight: isFocused ? '600' : '400',
                  },
                ]}
              >
                {label}
              </Text>
            </Animated.View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

/**
 * Floating Alfred Button for center of tab bar
 */
interface AlfredFABProps {
  onPress: () => void;
  onLongPress?: () => void;
}

export function AlfredFAB({ onPress, onLongPress }: AlfredFABProps) {
  const { theme } = useTheme();
  const haptics = useHaptics();
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.3)).current;

  // Continuous glow animation
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 0.6,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0.3,
          duration: 2000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const handlePressIn = () => {
    Animated.spring(scaleAnim, {
      toValue: 0.9,
      useNativeDriver: true,
      speed: 50,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
      speed: 50,
      bounciness: 10,
    }).start();
  };

  const handlePress = () => {
    haptics.buttonPress();
    onPress();
  };

  const handleLongPressAction = () => {
    haptics.trigger('heavy');
    onLongPress?.();
  };

  return (
    <TouchableOpacity
      onPress={handlePress}
      onLongPress={onLongPress ? handleLongPressAction : undefined}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
      style={styles.fabContainer}
    >
      {/* Glow effect */}
      <Animated.View
        style={[
          styles.fabGlow,
          {
            backgroundColor: theme.colors.primary,
            opacity: glowAnim,
          },
        ]}
      />

      {/* Button */}
      <Animated.View
        style={[
          styles.fab,
          {
            backgroundColor: theme.colors.primary,
            transform: [{ scale: scaleAnim }],
            ...theme.shadows.lg,
          },
        ]}
      >
        <Text style={styles.fabIcon}>A</Text>
      </Animated.View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    borderTopWidth: 1,
    paddingTop: 8,
    paddingHorizontal: 20,
  },
  indicator: {
    position: 'absolute',
    top: 8,
    height: 50,
    borderRadius: 12,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabContent: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  icon: {
    fontSize: 22,
    marginBottom: 4,
  },
  label: {
    fontSize: 11,
  },
  fabContainer: {
    position: 'absolute',
    alignSelf: 'center',
    bottom: 30,
  },
  fabGlow: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    left: -12,
    top: -12,
  },
  fab: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  fabIcon: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
  },
});

export default AnimatedTabBar;
