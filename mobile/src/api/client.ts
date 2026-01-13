import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import { offlineQueue } from '../lib/offline/offlineQueue';

// Android Emulator uses 10.0.2.2 to access host localhost
// iOS Simulator uses localhost
const BASE_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

const client = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 second timeout
});

// Interceptor to add Token
client.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
    const token = await SecureStore.getItemAsync('auth_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor for offline handling
client.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config;

        // Check if we're offline
        const netState = await NetInfo.fetch();
        const isOffline = !netState.isConnected;

        // If offline and this is a mutation request (not GET), queue it
        if (isOffline && originalRequest) {
            const method = originalRequest.method?.toLowerCase();

            // Only queue mutation requests (POST, PUT, PATCH, DELETE)
            if (method && ['post', 'put', 'patch', 'delete'].includes(method)) {
                // Queue the request for later
                const requestId = await offlineQueue.enqueue({
                    method: originalRequest.method,
                    url: originalRequest.url,
                    data: originalRequest.data,
                    headers: originalRequest.headers as Record<string, string>,
                });

                // Return a "queued" response instead of throwing
                return Promise.resolve({
                    data: {
                        queued: true,
                        requestId,
                        message: 'Request queued for when online',
                    },
                    status: 202, // Accepted
                    statusText: 'Queued',
                    headers: {},
                    config: originalRequest,
                });
            }
        }

        // Re-throw the error for other cases
        return Promise.reject(error);
    }
);

/**
 * Initialize the API client and offline queue
 * Call this once at app startup
 */
export const initializeApiClient = async (): Promise<void> => {
    await offlineQueue.initialize(client);
};

/**
 * Get the current offline queue status
 */
export const getOfflineStatus = () => ({
    isOnline: offlineQueue.getIsOnline(),
    queueLength: offlineQueue.getQueueLength(),
    queue: offlineQueue.getQueue(),
});

/**
 * Add a listener for offline queue events
 */
export const addOfflineQueueListener = offlineQueue.addListener.bind(offlineQueue);

export const setAuthToken = async (token: string) => {
    await SecureStore.setItemAsync('auth_token', token);
};

export const getAuthToken = async () => {
    return await SecureStore.getItemAsync('auth_token');
};

export const logout = async () => {
    await SecureStore.deleteItemAsync('auth_token');
    // Clear offline queue on logout
    await offlineQueue.clear();
};

export default client;
