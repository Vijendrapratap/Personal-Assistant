import React, { useState } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    StyleSheet,
    ActivityIndicator,
    KeyboardAvoidingView,
    Platform,
    TouchableWithoutFeedback,
    Keyboard,
    SafeAreaView,
    useWindowDimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { theme } from '../../theme/tokens';
import client, { setAuthToken } from '../../api/client';

export default function LoginScreen({ navigation }: any) {
    const { width: screenWidth, height: screenHeight } = useWindowDimensions();
    const [email, setEmail] = useState('test@example.com');
    const [password, setPassword] = useState('password');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showPassword, setShowPassword] = useState(false);

    // Responsive values
    const horizontalPadding = Math.max(16, Math.min(24, screenWidth * 0.06));
    const isSmallScreen = screenHeight < 700;

    const handleLogin = async () => {
        setError(null);
        if (!email || !password) {
            setError('Please fill in all fields');
            return;
        }

        setLoading(true);
        try {
            const response = await client.post('/auth/login', `username=${email}&password=${password}`, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            const { access_token } = response.data;
            await setAuthToken(access_token);

            // Navigate to Main App
            navigation.replace('Main');
        } catch (err: any) {
            console.log(err);
            setError(err.response?.data?.detail || 'Invalid email or password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <SafeAreaView style={styles.safeArea}>
            <KeyboardAvoidingView
                behavior={Platform.OS === "ios" ? "padding" : "height"}
                style={styles.container}
            >
                <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
                    <View style={[styles.content, { paddingHorizontal: horizontalPadding }]}>
                        {/* Header */}
                        <View style={[styles.header, isSmallScreen && { marginBottom: theme.spacing[4] }]}>
                            <Text style={styles.title}>Welcome Back</Text>
                            <Text style={styles.subtitle}>Sign in to continue to Alfred</Text>
                        </View>

                        {/* Form */}
                        <View style={styles.form}>
                            {/* Email Input */}
                            <View style={styles.inputGroup}>
                                <Text style={styles.label}>Email</Text>
                                <View style={[styles.inputContainer, error ? styles.inputError : null]}>
                                    <Ionicons name="mail-outline" size={20} color={theme.colors.textSecondary} style={styles.inputIcon} />
                                    <TextInput
                                        style={styles.input}
                                        placeholder="Enter your email"
                                        placeholderTextColor={theme.colors.textDisabled}
                                        value={email}
                                        onChangeText={(text) => { setEmail(text); setError(null); }}
                                        autoCapitalize="none"
                                        keyboardType="email-address"
                                    />
                                </View>
                            </View>

                            {/* Password Input */}
                            <View style={styles.inputGroup}>
                                <Text style={styles.label}>Password</Text>
                                <View style={[styles.inputContainer, error ? styles.inputError : null]}>
                                    <Ionicons name="lock-closed-outline" size={20} color={theme.colors.textSecondary} style={styles.inputIcon} />
                                    <TextInput
                                        style={styles.input}
                                        placeholder="Enter your password"
                                        placeholderTextColor={theme.colors.textDisabled}
                                        value={password}
                                        onChangeText={(text) => { setPassword(text); setError(null); }}
                                        secureTextEntry={!showPassword}
                                    />
                                    <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                                        <Ionicons
                                            name={showPassword ? "eye-off-outline" : "eye-outline"}
                                            size={20}
                                            color={theme.colors.textSecondary}
                                        />
                                    </TouchableOpacity>
                                </View>
                            </View>

                            {/* Error Message via rule: error-feedback */}
                            {error && (
                                <View style={styles.errorContainer}>
                                    <Ionicons name="alert-circle" size={16} color={theme.colors.danger} />
                                    <Text style={styles.errorText}>{error}</Text>
                                </View>
                            )}

                            {/* Primary Button via rule: touch-target-size (min 44px) */}
                            <TouchableOpacity
                                style={[styles.button, loading && styles.buttonDisabled]}
                                onPress={handleLogin}
                                disabled={loading}
                                activeOpacity={0.8}
                            >
                                {loading ? (
                                    <ActivityIndicator color={theme.colors.white} />
                                ) : (
                                    <Text style={styles.buttonText}>Sign In</Text>
                                )}
                            </TouchableOpacity>

                            {/* Secondary Action */}
                            <TouchableOpacity
                                style={styles.secondaryButton}
                                onPress={() => navigation.navigate('Signup')}
                            >
                                <Text style={styles.secondaryButtonText}>
                                    Don't have an account? <Text style={styles.linkText}>Sign up</Text>
                                </Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </TouchableWithoutFeedback>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: theme.colors.bg,
    },
    container: {
        flex: 1,
    },
    content: {
        flex: 1,
        paddingVertical: theme.spacing[4],
        justifyContent: 'center',
    },
    header: {
        marginBottom: theme.spacing[6],
    },
    title: {
        fontSize: theme.typography.size['3xl'], // 32
        fontWeight: theme.typography.weight.bold,
        color: theme.colors.textPrimary,
        marginBottom: theme.spacing[2],
    },
    subtitle: {
        fontSize: theme.typography.size.base,
        color: theme.colors.textSecondary,
    },
    form: {
        gap: theme.spacing[4],
    },
    inputGroup: {
        gap: theme.spacing[2],
    },
    label: {
        fontSize: theme.typography.size.sm,
        fontWeight: theme.typography.weight.medium,
        color: theme.colors.textPrimary, // High contrast label
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: theme.colors.bgSurface,
        borderWidth: 1,
        borderColor: theme.colors.border,
        borderRadius: theme.radius.md,
        paddingHorizontal: theme.spacing[3],
        height: 56, // Large touch target/visual
    },
    inputError: {
        borderColor: theme.colors.danger,
    },
    inputIcon: {
        marginRight: theme.spacing[3],
    },
    input: {
        flex: 1,
        color: theme.colors.textPrimary,
        fontSize: theme.typography.size.base,
        height: '100%',
    },
    errorContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: theme.spacing[2],
        marginBottom: theme.spacing[2],
    },
    errorText: {
        color: theme.colors.danger,
        fontSize: theme.typography.size.sm,
    },
    button: {
        backgroundColor: theme.colors.primary,
        height: 56, // 56px > 44px rule
        borderRadius: theme.radius.full,
        justifyContent: 'center',
        alignItems: 'center',
        marginTop: theme.spacing[4],
        ...theme.shadows.glow, // Glow effect
    },
    buttonDisabled: {
        opacity: 0.7,
    },
    buttonText: {
        color: theme.colors.white,
        fontSize: theme.typography.size.lg,
        fontWeight: theme.typography.weight.semibold,
    },
    secondaryButton: {
        alignItems: 'center',
        padding: theme.spacing[2],
    },
    secondaryButtonText: {
        color: theme.colors.textSecondary,
        fontSize: theme.typography.size.sm,
    },
    linkText: {
        color: theme.colors.primary,
        fontWeight: theme.typography.weight.bold,
    },
});
