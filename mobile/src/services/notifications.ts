/**
 * Alfred Push Notification Service
 * Handles push notification registration and handling for the mobile app.
 */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import client from '../api/client';

// Configure how notifications are handled when app is in foreground
Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
    }),
});

/**
 * Request push notification permissions and get the Expo push token.
 */
export async function registerForPushNotifications(): Promise<string | null> {
    // Must be a physical device for push notifications
    if (!Device.isDevice) {
        console.log('Push notifications require a physical device');
        return null;
    }

    // Check existing permissions
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    // Request permissions if not granted
    if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
    }

    if (finalStatus !== 'granted') {
        console.log('Failed to get push notification permissions');
        return null;
    }

    // Get Expo push token
    try {
        const tokenData = await Notifications.getExpoPushTokenAsync({
            projectId: process.env.EXPO_PROJECT_ID, // Set in app.json or .env
        });

        const token = tokenData.data;
        console.log('Expo push token:', token);

        // Configure Android notification channel
        if (Platform.OS === 'android') {
            await setupAndroidChannels();
        }

        return token;
    } catch (error) {
        console.error('Error getting push token:', error);
        return null;
    }
}

/**
 * Set up Android notification channels for different notification types.
 */
async function setupAndroidChannels(): Promise<void> {
    // Main Alfred channel
    await Notifications.setNotificationChannelAsync('alfred-main', {
        name: 'Alfred Notifications',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#1a73e8',
    });

    // Habit reminders channel
    await Notifications.setNotificationChannelAsync('alfred-habits', {
        name: 'Habit Reminders',
        importance: Notifications.AndroidImportance.DEFAULT,
        vibrationPattern: [0, 100, 100, 100],
        lightColor: '#4caf50',
    });

    // Task due reminders
    await Notifications.setNotificationChannelAsync('alfred-tasks', {
        name: 'Task Reminders',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#ff9800',
    });

    // Daily briefings
    await Notifications.setNotificationChannelAsync('alfred-briefings', {
        name: 'Daily Briefings',
        importance: Notifications.AndroidImportance.DEFAULT,
        lightColor: '#1a73e8',
    });
}

/**
 * Register the push token with Alfred backend.
 */
export async function registerTokenWithBackend(token: string): Promise<boolean> {
    try {
        await client.post('/notifications/register-token', {
            push_token: token,
            device_type: 'expo',
        });
        console.log('Push token registered with backend');
        return true;
    } catch (error) {
        console.error('Failed to register push token with backend:', error);
        return false;
    }
}

/**
 * Unregister push token from backend (e.g., on logout).
 */
export async function unregisterToken(): Promise<void> {
    try {
        await client.delete('/notifications/unregister-token', {
            params: { device_type: 'expo' },
        });
        console.log('Push token unregistered');
    } catch (error) {
        console.error('Failed to unregister push token:', error);
    }
}

/**
 * Handle incoming notification when app is in foreground.
 */
export function addNotificationReceivedListener(
    handler: (notification: Notifications.Notification) => void
): Notifications.Subscription {
    return Notifications.addNotificationReceivedListener(handler);
}

/**
 * Handle notification tap/response.
 */
export function addNotificationResponseListener(
    handler: (response: Notifications.NotificationResponse) => void
): Notifications.Subscription {
    return Notifications.addNotificationResponseReceivedListener(handler);
}

/**
 * Get notification preferences from backend.
 */
export async function getNotificationPreferences(): Promise<NotificationPreferences> {
    try {
        const response = await client.get('/notifications/preferences');
        return response.data;
    } catch (error) {
        console.error('Failed to get notification preferences:', error);
        return defaultPreferences;
    }
}

/**
 * Update notification preferences on backend.
 */
export async function updateNotificationPreferences(
    preferences: NotificationPreferences
): Promise<boolean> {
    try {
        await client.put('/notifications/preferences', preferences);
        return true;
    } catch (error) {
        console.error('Failed to update notification preferences:', error);
        return false;
    }
}

/**
 * Send a test notification to verify setup.
 */
export async function sendTestNotification(): Promise<boolean> {
    try {
        await client.post('/notifications/test');
        return true;
    } catch (error) {
        console.error('Failed to send test notification:', error);
        return false;
    }
}

// Types
export interface NotificationPreferences {
    morning_briefing: boolean;
    evening_review: boolean;
    habit_reminders: boolean;
    task_due_reminders: boolean;
    project_nudges: boolean;
}

const defaultPreferences: NotificationPreferences = {
    morning_briefing: true,
    evening_review: true,
    habit_reminders: true,
    task_due_reminders: true,
    project_nudges: true,
};

/**
 * Initialize push notifications for the app.
 * Call this on app startup after user is authenticated.
 */
export async function initializePushNotifications(): Promise<void> {
    const token = await registerForPushNotifications();

    if (token) {
        await registerTokenWithBackend(token);
    }
}

/**
 * Schedule a local notification (for testing or offline reminders).
 */
export async function scheduleLocalNotification(
    title: string,
    body: string,
    triggerSeconds: number,
    data?: Record<string, unknown>
): Promise<string> {
    const id = await Notifications.scheduleNotificationAsync({
        content: {
            title,
            body,
            data,
            sound: true,
        },
        trigger: {
            seconds: triggerSeconds,
        },
    });

    return id;
}

/**
 * Cancel a scheduled local notification.
 */
export async function cancelLocalNotification(notificationId: string): Promise<void> {
    await Notifications.cancelScheduledNotificationAsync(notificationId);
}

/**
 * Clear all delivered notifications from the notification center.
 */
export async function clearAllNotifications(): Promise<void> {
    await Notifications.dismissAllNotificationsAsync();
}

/**
 * Get the count of delivered notifications.
 */
export async function getBadgeCount(): Promise<number> {
    return await Notifications.getBadgeCountAsync();
}

/**
 * Set the badge count.
 */
export async function setBadgeCount(count: number): Promise<void> {
    await Notifications.setBadgeCountAsync(count);
}
