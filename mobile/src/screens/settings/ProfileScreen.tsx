import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert, ScrollView } from 'react-native';
import client, { logout } from '../../api/client';

export default function ProfileScreen({ navigation }: any) {
    const [profile, setProfile] = useState({
        bio: '',
        work_type: '',
        personality_prompt: '',
        interaction_type: 'formal'
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadProfile();
    }, []);

    const loadProfile = async () => {
        try {
            const res = await client.get('/auth/profile');
            setProfile(res.data);
        } catch (error) {
            console.log(error);
        }
    };

    const handleUpdate = async () => {
        setLoading(true);
        try {
            await client.put('/auth/profile', profile);
            Alert.alert("Success", "Profile updated.");
        } catch (error) {
            Alert.alert("Error", "Could not update profile.");
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = async () => {
        await logout();
        navigation.reset({ index: 0, routes: [{ name: 'Auth' }] });
    };

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <Text style={styles.header}>Your Profile</Text>

            <Text style={styles.label}>Bio (About You)</Text>
            <TextInput
                style={styles.input}
                value={profile.bio}
                onChangeText={(text) => setProfile({ ...profile, bio: text })}
                multiline
            />

            <Text style={styles.label}>Work Type</Text>
            <TextInput
                style={styles.input}
                value={profile.work_type}
                onChangeText={(text) => setProfile({ ...profile, work_type: text })}
            />

            <Text style={styles.label}>Personality Prompt</Text>
            <TextInput
                style={styles.input}
                value={profile.personality_prompt}
                onChangeText={(text) => setProfile({ ...profile, personality_prompt: text })}
                placeholder="e.g. Witty Butler"
            />

            <Button title={loading ? "Saving..." : "Save Profile"} onPress={handleUpdate} disabled={loading} />

            <View style={{ marginTop: 20 }}>
                <Button title="Logout" color="red" onPress={handleLogout} />
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { padding: 20 },
    header: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
    label: { fontSize: 16, marginBottom: 5, fontWeight: '600' },
    input: { borderWidth: 1, borderColor: '#ccc', padding: 10, marginBottom: 20, borderRadius: 5, backgroundColor: '#fff' },
});
