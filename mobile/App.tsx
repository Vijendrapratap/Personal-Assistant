import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ActivityIndicator, View, Text, StyleSheet, TouchableOpacity } from 'react-native';

// Theme
import { ThemeProvider, useTheme } from './src/theme';

// Auth Screens
import LoginScreen from './src/screens/LoginScreen';
import SignupScreen from './src/screens/SignupScreen';

// Main Tab Screens (New Architecture)
import TodayScreen from './src/screens/TodayScreen';
import DoScreen from './src/screens/DoScreen';
import FocusScreen from './src/screens/FocusScreen';
import YouScreen from './src/screens/YouScreen';

// Settings Screens
import EditProfileScreen from './src/screens/EditProfileScreen';
import NotificationSettingsScreen from './src/screens/NotificationSettingsScreen';
import PrivacySettingsScreen from './src/screens/PrivacySettingsScreen';

// Voice Modal
import VoiceModal from './src/screens/VoiceModal';

// Evening Review Modal
import EveningReviewModal from './src/screens/EveningReviewModal';

// Entity Screens
import PeopleScreen from './src/screens/PeopleScreen';
import CompaniesScreen from './src/screens/CompaniesScreen';
import EntityDetailScreen from './src/screens/EntityDetailScreen';

// Settings/Info Screens
import PreferencesScreen from './src/screens/PreferencesScreen';
import VoiceSettingsScreen from './src/screens/VoiceSettingsScreen';
import IntegrationsScreen from './src/screens/IntegrationsScreen';
import AboutScreen from './src/screens/AboutScreen';

// Legacy Screens (for backward compatibility)
import ProfileScreen from './src/screens/ProfileScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import ProjectsScreen from './src/screens/ProjectsScreen';
import TasksScreen from './src/screens/TasksScreen';
import HabitsScreen from './src/screens/HabitsScreen';
import ChatScreen from './src/screens/ChatScreen';

import { getAuthToken } from './src/api/client';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// Placeholder Focus Screen until Phase 1.3
function FocusScreenPlaceholder({ navigation }: any) {
    const { theme } = useTheme();
    return (
        <View style={[placeholderStyles.container, { backgroundColor: theme.colors.bg }]}>
            <Text style={[placeholderStyles.icon]}>📅</Text>
            <Text style={[placeholderStyles.title, { color: theme.colors.textPrimary }]}>
                Focus
            </Text>
            <Text style={[placeholderStyles.subtitle, { color: theme.colors.textSecondary }]}>
                Calendar & Voice interface coming soon
            </Text>
        </View>
    );
}

const placeholderStyles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 40,
    },
    icon: {
        fontSize: 48,
        marginBottom: 16,
    },
    title: {
        fontSize: 24,
        fontWeight: '700',
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 15,
        textAlign: 'center',
    },
});

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
    const [initialRoute, setInitialRoute] = useState('Auth');
    const { theme } = useTheme();

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const token = await getAuthToken();
            if (token) {
                setInitialRoute('Main');
            }
        } catch (e) {
            console.log(e);
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
            }}
        >
            <Stack.Navigator initialRouteName={initialRoute}>
                {/* Auth Screens */}
                <Stack.Screen
                    name="Auth"
                    component={LoginScreen}
                    options={{ headerShown: false }}
                />
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
