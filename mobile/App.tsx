import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ActivityIndicator, View, Text, StyleSheet, TouchableOpacity } from 'react-native';

import LoginScreen from './src/screens/LoginScreen';
import SignupScreen from './src/screens/SignupScreen';
import ChatScreen from './src/screens/ChatScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import ProjectsScreen from './src/screens/ProjectsScreen';
import TasksScreen from './src/screens/TasksScreen';
import HabitsScreen from './src/screens/HabitsScreen';
import { getAuthToken } from './src/api/client';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// Tab bar icons using text/emoji (can be replaced with proper icons later)
const TabIcon = ({ name, focused }: { name: string; focused: boolean }) => {
    const icons: Record<string, string> = {
        Dashboard: '🏠',
        Projects: '📁',
        Tasks: '✓',
        Habits: '🔥',
        Chat: '💬',
    };
    return (
        <Text style={[styles.tabIcon, focused && styles.tabIconFocused]}>
            {icons[name] || '•'}
        </Text>
    );
};

// Main Tab Navigator (after login)
function MainTabs() {
    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                tabBarIcon: ({ focused }) => <TabIcon name={route.name} focused={focused} />,
                tabBarActiveTintColor: '#1a73e8',
                tabBarInactiveTintColor: '#999',
                tabBarStyle: styles.tabBar,
                tabBarLabelStyle: styles.tabLabel,
                headerStyle: styles.header,
                headerTitleStyle: styles.headerTitle,
            })}
        >
            <Tab.Screen
                name="Dashboard"
                component={DashboardScreen}
                options={{
                    title: 'Today',
                    headerTitle: 'Alfred',
                }}
            />
            <Tab.Screen
                name="Projects"
                component={ProjectsScreen}
                options={{ title: 'Projects' }}
            />
            <Tab.Screen
                name="Tasks"
                component={TasksScreen}
                options={{ title: 'Tasks' }}
            />
            <Tab.Screen
                name="Habits"
                component={HabitsScreen}
                options={{ title: 'Habits' }}
            />
            <Tab.Screen
                name="Chat"
                component={ChatScreen}
                options={{
                    title: 'Alfred',
                    headerTitle: 'Chat with Alfred',
                }}
            />
        </Tab.Navigator>
    );
}

export default function App() {
    const [loading, setLoading] = useState(true);
    const [initialRoute, setInitialRoute] = useState('Login');

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
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#1a73e8" />
                <Text style={styles.loadingText}>Loading Alfred...</Text>
            </View>
        );
    }

    return (
        <SafeAreaProvider>
            <NavigationContainer>
                <Stack.Navigator initialRouteName={initialRoute}>
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
                    <Stack.Screen
                        name="Main"
                        component={MainTabs}
                        options={({ navigation }) => ({
                            headerShown: false,
                        })}
                    />
                    <Stack.Screen
                        name="Profile"
                        component={ProfileScreen}
                        options={{
                            title: 'Profile Settings',
                            headerStyle: styles.header,
                            headerTitleStyle: styles.headerTitle,
                        }}
                    />
                </Stack.Navigator>
            </NavigationContainer>
        </SafeAreaProvider>
    );
}

const styles = StyleSheet.create({
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
    },
    loadingText: {
        marginTop: 10,
        color: '#666',
        fontSize: 14,
    },
    tabBar: {
        backgroundColor: '#fff',
        borderTopWidth: 1,
        borderTopColor: '#e0e0e0',
        paddingTop: 5,
        paddingBottom: 5,
        height: 60,
    },
    tabLabel: {
        fontSize: 11,
        fontWeight: '500',
    },
    tabIcon: {
        fontSize: 20,
    },
    tabIconFocused: {
        transform: [{ scale: 1.1 }],
    },
    header: {
        backgroundColor: '#1a73e8',
    },
    headerTitle: {
        color: '#fff',
        fontWeight: '600',
    },
});
