import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

// Android Emulator uses 10.0.2.2 to access host localhost
// iOS Simulator uses localhost
const BASE_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

const client = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor to add Token
client.interceptors.request.use(async (config) => {
    const token = await SecureStore.getItemAsync('auth_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const setAuthToken = async (token: string) => {
    await SecureStore.setItemAsync('auth_token', token);
};

export const getAuthToken = async () => {
    return await SecureStore.getItemAsync('auth_token');
};

export const logout = async () => {
    await SecureStore.deleteItemAsync('auth_token');
};

export default client;
