import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert } from 'react-native';
import client, { setAuthToken } from '../api/client';

export default function LoginScreen({ navigation }: any) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async () => {
        if (!email || !password) {
            Alert.alert('Error', 'Please fill in all fields');
            return;
        }

        setLoading(true);
        try {
            const response = await client.post('/auth/login', `username=${email}&password=${password}`, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            const { access_token } = response.data;
            await setAuthToken(access_token);

            // Navigate to App (Chat)
            // We assume the parent navigator will handle the state change or we navigate
            // For now, let's assume we have an 'App' stack
            // But typically we update a global context. 
            // For simplicity in this step, let's just assume navigation works.
            // But practically, we need a root navigator to switch stacks.
            // Let's reload or use a callback if passed, or just navigate if structure allows.
            // Actually, standard practice is to have a context. 
            // I will implement a basic navigation structure in App.tsx that checks token.
            Alert.alert("Success", "Logged in!");
        } catch (error: any) {
            console.log(error);
            Alert.alert('Login Failed', error.response?.data?.detail || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Alfred</Text>
            <TextInput
                style={styles.input}
                placeholder="Email"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
            />
            <TextInput
                style={styles.input}
                placeholder="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
            />
            <Button title={loading ? "Logging in..." : "Login"} onPress={handleLogin} disabled={loading} />
            <Button title="Create Account" onPress={() => navigation.navigate('Signup')} />
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', padding: 20 },
    title: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', marginBottom: 40 },
    input: { borderWidth: 1, borderColor: '#ccc', padding: 10, marginBottom: 20, borderRadius: 5 },
});
