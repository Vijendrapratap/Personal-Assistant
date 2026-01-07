/**
 * Tabs Layout
 *
 * Main app navigation with bottom tabs.
 */

import { Tabs } from 'expo-router';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { useTheme } from '../../src/theme';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from 'react-native-reanimated';

// Tab icons mapping
const TAB_ICONS: Record<string, string> = {
  today: '☀️',
  do: '✓',
  focus: '📅',
  you: '👤',
};

const TAB_LABELS: Record<string, string> = {
  today: 'Today',
  do: 'Do',
  focus: 'Focus',
  you: 'You',
};

interface TabIconProps {
  name: string;
  focused: boolean;
  color: string;
}

function TabIcon({ name, focused, color }: TabIconProps) {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  // Animate on focus change
  if (focused) {
    scale.value = withSpring(1.1, { damping: 15 });
  } else {
    scale.value = withSpring(1, { damping: 15 });
  }

  return (
    <Animated.View style={[styles.tabIconContainer, animatedStyle]}>
      <Text style={styles.tabIcon}>{TAB_ICONS[name] || '•'}</Text>
    </Animated.View>
  );
}

export default function TabsLayout() {
  const { theme } = useTheme();

  return (
    <Tabs
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused, color }) => (
          <TabIcon name={route.name} focused={focused} color={color} />
        ),
        tabBarLabel: TAB_LABELS[route.name] || route.name,
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textTertiary,
        tabBarStyle: {
          backgroundColor: theme.colors.bgElevated,
          borderTopWidth: 1,
          borderTopColor: theme.colors.border,
          paddingTop: 8,
          paddingBottom: 8,
          height: 80,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 4,
        },
        tabBarButton: (props) => (
          <Pressable
            {...props}
            android_ripple={{ color: theme.colors.primary + '20', borderless: true }}
          />
        ),
      })}
    >
      <Tabs.Screen
        name="today"
        options={{
          title: 'Today',
        }}
      />
      <Tabs.Screen
        name="do"
        options={{
          title: 'Do',
        }}
      />
      <Tabs.Screen
        name="focus"
        options={{
          title: 'Focus',
        }}
      />
      <Tabs.Screen
        name="you"
        options={{
          title: 'You',
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabIconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabIcon: {
    fontSize: 22,
  },
});
