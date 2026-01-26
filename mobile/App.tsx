import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ActivityIndicator, View, Text, StyleSheet, TouchableOpacity } from 'react-native';

// Theme
import { ThemeProvider, useTheme } from './src/theme';

// Screens - organized by category
import {
    // Auth
    LoginScreen,
    SignupScreen,
    // Main Tabs
    TodayScreen,
    DoScreen,
    FocusScreen,
    YouScreen,
    // Features
    TasksScreen,
    HabitsScreen,
    ProjectsScreen,
    // Settings
    ProfileScreen,
    EditProfileScreen,
    PreferencesScreen,
    NotificationSettingsScreen,
    PrivacySettingsScreen,
    VoiceSettingsScreen,
    AboutScreen,
    // Modals
    VoiceModal,
    EveningReviewModal,
    // Details
    PeopleScreen,
    CompaniesScreen,
    EntityDetailScreen,
    IntegrationsScreen,
} from './src/screens';

import client, { getAuthToken, logout } from './src/api/client';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// Tab bar icons
const TabIcon = ({ name, focused, theme }: { name: string; focused: boolean; theme: any }) => {
    const icons: Record<string, string> = {
        Today: '☀️',
        Do: '✓',
        Focus: '📅',
        You: '👤',
    };
    return (
        <View style={[styles.tabIconContainer, focused && { transform: [{ scale: 1.1 }] }]}>
            <Text style={styles.tabIcon}>{icons[name] || '•'}</Text>
        </View>
    );
};

// New Main Tab Navigator (Today, Do, Focus, You)
function MainTabs() {
    const { theme, mode } = useTheme();

    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                tabBarIcon: ({ focused }) => <TabIcon name={route.name} focused={focused} theme={theme} />,
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
                headerShown: false,
            })}
        >
            <Tab.Screen
                name="Today"
                component={TodayScreen}
                options={{ title: 'Today' }}
            />
            <Tab.Screen
                name="Do"
                component={DoScreen}
                options={{ title: 'Do' }}
            />
            <Tab.Screen
                name="Focus"
                component={FocusScreen}
                options={{ title: 'Focus' }}
            />
            <Tab.Screen
                name="You"
                component={YouScreen}
                options={{ title: 'You' }}
            />
        </Tab.Navigator>
    );
}

function AppNavigator() {
    const [loading, setLoading] = useState(true);
    const [initialRoute, setInitialRoute] = useState('Login');
    const { theme } = useTheme();

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const token = await getAuthToken();
            if (token) {
                // Validate token by calling profile endpoint
                try {
                    await client.get('/auth/profile');
                    setInitialRoute('Main');
                } catch (err: any) {
                    // Token invalid (401/403), clear it and show login
                    console.log('Token invalid, clearing...', err?.response?.status);
                    await logout();
                    setInitialRoute('Login');
                }
            } else {
                setInitialRoute('Login');
            }
        } catch (e) {
            console.log('Auth check failed:', e);
            setInitialRoute('Login');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <View style={[styles.loadingContainer, { backgroundColor: theme.colors.bg }]}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
                <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
                    Loading Alfred...
                </Text>
            </View>
        );
    }

    return (
        <NavigationContainer
            theme={{
                dark: theme.mode === 'dark',
                colors: {
                    primary: theme.colors.primary,
                    background: theme.colors.bg,
                    card: theme.colors.bgElevated,
                    text: theme.colors.textPrimary,
                    border: theme.colors.border,
                    notification: theme.colors.primary,
                },
                fonts: {
                    regular: {
                        fontFamily: 'System',
                        fontWeight: '400' as const,
                    },
                    medium: {
                        fontFamily: 'System',
                        fontWeight: '500' as const,
                    },
                    bold: {
                        fontFamily: 'System',
                        fontWeight: '700' as const,
                    },
                    heavy: {
                        fontFamily: 'System',
                        fontWeight: '900' as const,
                    },
                },
            }}
        >
            <Stack.Navigator initialRouteName={initialRoute}>
                {/* Auth Screens */}
                <Stack.Screen
                    name="Login"
                    component={LoginScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="Signup"
                    component={SignupScreen}
                    options={{ headerShown: false }}
                />

                {/* Main App */}
                <Stack.Screen
                    name="Main"
                    component={MainTabs}
                    options={{ headerShown: false }}
                />

                {/* Settings Screens */}
                <Stack.Screen
                    name="EditProfile"
                    component={EditProfileScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="NotificationSettings"
                    component={NotificationSettingsScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="PrivacySettings"
                    component={PrivacySettingsScreen}
                    options={{ headerShown: false }}
                />

                {/* Legacy/Detail Screens */}
                <Stack.Screen
                    name="Profile"
                    component={ProfileScreen}
                    options={{
                        title: 'Profile Settings',
                        headerStyle: { backgroundColor: theme.colors.bgElevated },
                        headerTintColor: theme.colors.textPrimary,
                    }}
                />
                <Stack.Screen
                    name="Projects"
                    component={ProjectsScreen}
                    options={{
                        title: 'Projects',
                        headerStyle: { backgroundColor: theme.colors.bgElevated },
                        headerTintColor: theme.colors.textPrimary,
                    }}
                />
                <Stack.Screen
                    name="Tasks"
                    component={TasksScreen}
                    options={{
                        title: 'All Tasks',
                        headerStyle: { backgroundColor: theme.colors.bgElevated },
                        headerTintColor: theme.colors.textPrimary,
                    }}
                />
                <Stack.Screen
                    name="Habits"
                    component={HabitsScreen}
                    options={{
                        title: 'Habits',
                        headerStyle: { backgroundColor: theme.colors.bgElevated },
                        headerTintColor: theme.colors.textPrimary,
                    }}
                />
                <Stack.Screen
                    name="Voice"
                    component={VoiceModal}
                    options={{
                        headerShown: false,
                        presentation: 'modal',
                    }}
                />
                <Stack.Screen
                    name="EveningReview"
                    component={EveningReviewModal}
                    options={{
                        headerShown: false,
                        presentation: 'modal',
                    }}
                />

                {/* Entity Screens */}
                <Stack.Screen
                    name="People"
                    component={PeopleScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="Companies"
                    component={CompaniesScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="EntityDetail"
                    component={EntityDetailScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="Preferences"
                    component={PreferencesScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="VoiceSettings"
                    component={VoiceSettingsScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="Integrations"
                    component={IntegrationsScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="About"
                    component={AboutScreen}
                    options={{ headerShown: false }}
                />
                <Stack.Screen
                    name="Support"
                    component={AboutScreen}
                    options={{ headerShown: false }}
                />
            </Stack.Navigator>
        </NavigationContainer>
    );
}

export default function App() {
    return (
        <SafeAreaProvider>
            <ThemeProvider initialMode="dark">
                <AppNavigator />
            </ThemeProvider>
        </SafeAreaProvider>
    );
}

const styles = StyleSheet.create({
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        marginTop: 16,
        fontSize: 14,
    },
    tabIconContainer: {
        alignItems: 'center',
        justifyContent: 'center',
    },
    tabIcon: {
        fontSize: 22,
    },
});
