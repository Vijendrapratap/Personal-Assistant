/**
 * Auth Layout
 *
 * Layout for authentication screens (login, signup, onboarding).
 */

import { Stack } from 'expo-router';
import { useTheme } from '../../src/theme';

export default function AuthLayout() {
  const { theme } = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.bg },
        animation: 'fade',
      }}
    >
      <Stack.Screen name="login" />
      <Stack.Screen name="signup" />
      <Stack.Screen name="onboarding" />
    </Stack>
  );
}
