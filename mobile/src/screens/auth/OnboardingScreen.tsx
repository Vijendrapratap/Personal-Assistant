/**
 * Onboarding Screen
 *
 * Multi-step onboarding flow:
 * 1. Welcome
 * 2. AI Provider Setup (API Key)
 * 3. Connect Integrations (Optional)
 * 4. Personal Details
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography, shadows } from '../../theme/tokens';
import { Sparkles, Key, Calendar, User, ChevronRight, Check, ExternalLink } from 'lucide-react-native';
import client from '../../api/client';

const { width } = Dimensions.get('window');

type OnboardingStep = 'welcome' | 'api_key' | 'integrations' | 'profile' | 'complete';

interface OnboardingScreenProps {
  onComplete: () => void;
}

export default function OnboardingScreen({ onComplete }: OnboardingScreenProps) {
  const [step, setStep] = useState<OnboardingStep>('welcome');
  const [apiKey, setApiKey] = useState('');
  const [apiProvider, setApiProvider] = useState<'openai' | 'anthropic' | 'ollama'>('openai');
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [loading, setLoading] = useState(false);

  const handleNext = () => {
    switch (step) {
      case 'welcome':
        setStep('api_key');
        break;
      case 'api_key':
        validateAndProceed();
        break;
      case 'integrations':
        setStep('profile');
        break;
      case 'profile':
        completeOnboarding();
        break;
    }
  };

  const validateAndProceed = async () => {
    if (apiProvider === 'ollama') {
      // No API key needed for Ollama
      setStep('integrations');
      return;
    }

    if (!apiKey) {
      Alert.alert('API Key Required', 'Please enter your API key to continue.');
      return;
    }

    // Validate key format
    if (apiProvider === 'openai' && !apiKey.startsWith('sk-')) {
      Alert.alert('Invalid Key', 'OpenAI API keys start with "sk-"');
      return;
    }

    if (apiProvider === 'anthropic' && !apiKey.startsWith('sk-ant-')) {
      Alert.alert('Invalid Key', 'Anthropic API keys start with "sk-ant-"');
      return;
    }

    setLoading(true);
    try {
      // Validate with backend
      const response = await client.post('/setup/configure', {
        [`${apiProvider}_api_key`]: apiKey
      });

      if (response.data.success) {
        setStep('integrations');
      }
    } catch (error: any) {
      Alert.alert('Validation Failed', error.response?.data?.detail || 'Could not validate API key');
    } finally {
      setLoading(false);
    }
  };

  const completeOnboarding = async () => {
    setLoading(true);
    try {
      // Save profile
      if (name) {
        await client.put('/auth/profile', {
          name,
          work_type: role,
          onboarding_completed: true
        });
      }
      setStep('complete');
      setTimeout(onComplete, 2000);
    } catch (error) {
      console.error('Profile save error:', error);
      onComplete(); // Complete anyway
    } finally {
      setLoading(false);
    }
  };

  const openLink = (url: string) => {
    Linking.openURL(url);
  };

  const renderWelcome = () => (
    <View style={styles.stepContainer}>
      <LinearGradient
        colors={[colors.primary, colors.primaryDark]}
        style={styles.iconContainer}
      >
        <Sparkles size={48} color={colors.white} />
      </LinearGradient>

      <Text style={styles.title}>Welcome to Alfred</Text>
      <Text style={styles.subtitle}>
        Your intelligent personal assistant that anticipates your needs
        and helps you stay on top of everything.
      </Text>

      <View style={styles.featureList}>
        <FeatureItem icon="check" text="Manage tasks, projects, and habits" />
        <FeatureItem icon="check" text="Get proactive reminders and briefings" />
        <FeatureItem icon="check" text="Alfred learns and adapts to you" />
        <FeatureItem icon="check" text="Connect calendars and email" />
      </View>

      <TouchableOpacity style={styles.primaryButton} onPress={handleNext}>
        <Text style={styles.primaryButtonText}>Get Started</Text>
        <ChevronRight size={20} color={colors.white} />
      </TouchableOpacity>
    </View>
  );

  const renderApiKey = () => (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.stepContainer}
    >
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.iconContainerSmall}>
          <Key size={32} color={colors.primary} />
        </View>

        <Text style={styles.title}>Connect Your AI</Text>
        <Text style={styles.subtitle}>
          Alfred needs an AI brain to work. Choose your provider and enter your API key.
        </Text>

        {/* Provider Selection */}
        <View style={styles.providerContainer}>
          <ProviderOption
            name="OpenAI"
            description="GPT-4o (Recommended)"
            selected={apiProvider === 'openai'}
            onPress={() => setApiProvider('openai')}
          />
          <ProviderOption
            name="Anthropic"
            description="Claude (Coming Soon)"
            selected={apiProvider === 'anthropic'}
            onPress={() => setApiProvider('anthropic')}
            disabled
          />
          <ProviderOption
            name="Ollama"
            description="Free, Local AI"
            selected={apiProvider === 'ollama'}
            onPress={() => setApiProvider('ollama')}
          />
        </View>

        {apiProvider !== 'ollama' && (
          <>
            <Text style={styles.inputLabel}>API Key</Text>
            <TextInput
              style={styles.input}
              placeholder={apiProvider === 'openai' ? 'sk-...' : 'sk-ant-...'}
              placeholderTextColor={colors.dark.textTertiary}
              value={apiKey}
              onChangeText={setApiKey}
              autoCapitalize="none"
              autoCorrect={false}
              secureTextEntry
            />

            <TouchableOpacity
              style={styles.linkButton}
              onPress={() => openLink(
                apiProvider === 'openai'
                  ? 'https://platform.openai.com/api-keys'
                  : 'https://console.anthropic.com/'
              )}
            >
              <Text style={styles.linkText}>Get an API key</Text>
              <ExternalLink size={16} color={colors.primary} />
            </TouchableOpacity>
          </>
        )}

        {apiProvider === 'ollama' && (
          <View style={styles.ollamaInfo}>
            <Text style={styles.ollamaTitle}>Using Ollama</Text>
            <Text style={styles.ollamaText}>
              Make sure Ollama is running on your computer.
              Alfred will connect automatically.
            </Text>
            <TouchableOpacity
              style={styles.linkButton}
              onPress={() => openLink('https://ollama.ai')}
            >
              <Text style={styles.linkText}>Download Ollama</Text>
              <ExternalLink size={16} color={colors.primary} />
            </TouchableOpacity>
          </View>
        )}

        <TouchableOpacity
          style={[styles.primaryButton, loading && styles.buttonDisabled]}
          onPress={handleNext}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color={colors.white} />
          ) : (
            <>
              <Text style={styles.primaryButtonText}>Continue</Text>
              <ChevronRight size={20} color={colors.white} />
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );

  const renderIntegrations = () => (
    <View style={styles.stepContainer}>
      <View style={styles.iconContainerSmall}>
        <Calendar size={32} color={colors.primary} />
      </View>

      <Text style={styles.title}>Connect Your Life</Text>
      <Text style={styles.subtitle}>
        Alfred works best when connected to your tools. You can always add these later.
      </Text>

      <View style={styles.integrationList}>
        <IntegrationItem
          name="Google Calendar"
          description="Sync events and check availability"
          status="available"
        />
        <IntegrationItem
          name="Gmail"
          description="Read and draft emails"
          status="coming_soon"
        />
        <IntegrationItem
          name="Outlook"
          description="Calendar and email"
          status="coming_soon"
        />
        <IntegrationItem
          name="Todoist"
          description="Sync your tasks"
          status="coming_soon"
        />
      </View>

      <TouchableOpacity style={styles.primaryButton} onPress={handleNext}>
        <Text style={styles.primaryButtonText}>Continue</Text>
        <ChevronRight size={20} color={colors.white} />
      </TouchableOpacity>

      <TouchableOpacity style={styles.skipButton} onPress={handleNext}>
        <Text style={styles.skipButtonText}>Skip for now</Text>
      </TouchableOpacity>
    </View>
  );

  const renderProfile = () => (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.stepContainer}
    >
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.iconContainerSmall}>
          <User size={32} color={colors.primary} />
        </View>

        <Text style={styles.title}>Tell Alfred About You</Text>
        <Text style={styles.subtitle}>
          Help Alfred personalize your experience.
        </Text>

        <Text style={styles.inputLabel}>What should Alfred call you?</Text>
        <TextInput
          style={styles.input}
          placeholder="Your name"
          placeholderTextColor={colors.dark.textTertiary}
          value={name}
          onChangeText={setName}
          autoCapitalize="words"
        />

        <Text style={styles.inputLabel}>What's your primary role?</Text>
        <View style={styles.roleContainer}>
          <RoleOption
            label="Founder / CEO"
            selected={role === 'founder'}
            onPress={() => setRole('founder')}
          />
          <RoleOption
            label="Professional"
            selected={role === 'professional'}
            onPress={() => setRole('professional')}
          />
          <RoleOption
            label="Creative"
            selected={role === 'creative'}
            onPress={() => setRole('creative')}
          />
          <RoleOption
            label="Student"
            selected={role === 'student'}
            onPress={() => setRole('student')}
          />
        </View>

        <TouchableOpacity
          style={[styles.primaryButton, loading && styles.buttonDisabled]}
          onPress={handleNext}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color={colors.white} />
          ) : (
            <>
              <Text style={styles.primaryButtonText}>Meet Alfred</Text>
              <ChevronRight size={20} color={colors.white} />
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );

  const renderComplete = () => (
    <View style={[styles.stepContainer, styles.centered]}>
      <LinearGradient
        colors={[colors.success, '#059669']}
        style={styles.iconContainer}
      >
        <Check size={48} color={colors.white} />
      </LinearGradient>

      <Text style={styles.title}>You're All Set!</Text>
      <Text style={styles.subtitle}>
        Alfred is ready to assist you. Say hello to your new digital butler.
      </Text>

      <ActivityIndicator color={colors.primary} style={{ marginTop: spacing[8] }} />
    </View>
  );

  const renderStep = () => {
    switch (step) {
      case 'welcome':
        return renderWelcome();
      case 'api_key':
        return renderApiKey();
      case 'integrations':
        return renderIntegrations();
      case 'profile':
        return renderProfile();
      case 'complete':
        return renderComplete();
    }
  };

  return (
    <View style={styles.container}>
      {/* Progress Indicator */}
      {step !== 'welcome' && step !== 'complete' && (
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                {
                  width: step === 'api_key' ? '33%' :
                         step === 'integrations' ? '66%' : '100%'
                }
              ]}
            />
          </View>
        </View>
      )}

      {renderStep()}
    </View>
  );
}

// Helper Components

const FeatureItem = ({ icon, text }: { icon: string; text: string }) => (
  <View style={styles.featureItem}>
    <View style={styles.featureIcon}>
      <Check size={16} color={colors.success} />
    </View>
    <Text style={styles.featureText}>{text}</Text>
  </View>
);

const ProviderOption = ({
  name,
  description,
  selected,
  onPress,
  disabled = false
}: {
  name: string;
  description: string;
  selected: boolean;
  onPress: () => void;
  disabled?: boolean;
}) => (
  <TouchableOpacity
    style={[
      styles.providerOption,
      selected && styles.providerOptionSelected,
      disabled && styles.providerOptionDisabled
    ]}
    onPress={onPress}
    disabled={disabled}
  >
    <View style={styles.providerContent}>
      <Text style={[styles.providerName, disabled && styles.textDisabled]}>{name}</Text>
      <Text style={[styles.providerDescription, disabled && styles.textDisabled]}>
        {description}
      </Text>
    </View>
    {selected && (
      <View style={styles.providerCheck}>
        <Check size={16} color={colors.primary} />
      </View>
    )}
  </TouchableOpacity>
);

const IntegrationItem = ({
  name,
  description,
  status
}: {
  name: string;
  description: string;
  status: 'available' | 'connected' | 'coming_soon';
}) => (
  <View style={styles.integrationItem}>
    <View style={styles.integrationContent}>
      <Text style={styles.integrationName}>{name}</Text>
      <Text style={styles.integrationDescription}>{description}</Text>
    </View>
    {status === 'available' && (
      <TouchableOpacity style={styles.connectButton}>
        <Text style={styles.connectButtonText}>Connect</Text>
      </TouchableOpacity>
    )}
    {status === 'connected' && (
      <View style={styles.connectedBadge}>
        <Check size={14} color={colors.success} />
        <Text style={styles.connectedText}>Connected</Text>
      </View>
    )}
    {status === 'coming_soon' && (
      <Text style={styles.comingSoonText}>Coming Soon</Text>
    )}
  </View>
);

const RoleOption = ({
  label,
  selected,
  onPress
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
}) => (
  <TouchableOpacity
    style={[styles.roleOption, selected && styles.roleOptionSelected]}
    onPress={onPress}
  >
    <Text style={[styles.roleText, selected && styles.roleTextSelected]}>{label}</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.dark.bg,
  },
  progressContainer: {
    paddingHorizontal: spacing[6],
    paddingTop: spacing[16],
  },
  progressBar: {
    height: 4,
    backgroundColor: colors.dark.bgSurface,
    borderRadius: radius.full,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: radius.full,
  },
  stepContainer: {
    flex: 1,
    paddingHorizontal: spacing[6],
    paddingTop: spacing[12],
    paddingBottom: spacing[8],
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconContainer: {
    width: 96,
    height: 96,
    borderRadius: radius.xl,
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    marginBottom: spacing[8],
    ...shadows.glow,
  },
  iconContainerSmall: {
    width: 64,
    height: 64,
    borderRadius: radius.lg,
    backgroundColor: colors.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    marginBottom: spacing[6],
  },
  title: {
    fontSize: typography.size['3xl'],
    fontWeight: typography.weight.bold,
    color: colors.dark.textPrimary,
    textAlign: 'center',
    marginBottom: spacing[3],
  },
  subtitle: {
    fontSize: typography.size.lg,
    color: colors.dark.textSecondary,
    textAlign: 'center',
    lineHeight: typography.size.lg * typography.lineHeight.relaxed,
    marginBottom: spacing[8],
  },
  featureList: {
    marginBottom: spacing[8],
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing[4],
  },
  featureIcon: {
    width: 24,
    height: 24,
    borderRadius: radius.full,
    backgroundColor: colors.successSoft,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing[3],
  },
  featureText: {
    fontSize: typography.size.base,
    color: colors.dark.textPrimary,
  },
  primaryButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing[4],
    paddingHorizontal: spacing[6],
    borderRadius: radius.lg,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing[4],
  },
  primaryButtonText: {
    color: colors.white,
    fontSize: typography.size.lg,
    fontWeight: typography.weight.semibold,
    marginRight: spacing[2],
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  skipButton: {
    paddingVertical: spacing[4],
    alignItems: 'center',
  },
  skipButtonText: {
    color: colors.dark.textTertiary,
    fontSize: typography.size.base,
  },
  inputLabel: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.medium,
    color: colors.dark.textSecondary,
    marginBottom: spacing[2],
    marginTop: spacing[4],
  },
  input: {
    backgroundColor: colors.dark.bgSurface,
    borderWidth: 1,
    borderColor: colors.dark.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing[4],
    paddingVertical: spacing[3],
    fontSize: typography.size.base,
    color: colors.dark.textPrimary,
  },
  linkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing[3],
  },
  linkText: {
    color: colors.primary,
    fontSize: typography.size.sm,
    marginRight: spacing[1],
  },
  providerContainer: {
    marginTop: spacing[4],
  },
  providerOption: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.dark.bgSurface,
    borderWidth: 1,
    borderColor: colors.dark.border,
    borderRadius: radius.md,
    padding: spacing[4],
    marginBottom: spacing[3],
  },
  providerOptionSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryGlow,
  },
  providerOptionDisabled: {
    opacity: 0.5,
  },
  providerContent: {
    flex: 1,
  },
  providerName: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.semibold,
    color: colors.dark.textPrimary,
  },
  providerDescription: {
    fontSize: typography.size.sm,
    color: colors.dark.textSecondary,
    marginTop: spacing[0.5],
  },
  providerCheck: {
    width: 24,
    height: 24,
    borderRadius: radius.full,
    backgroundColor: colors.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
  },
  textDisabled: {
    color: colors.dark.textDisabled,
  },
  ollamaInfo: {
    backgroundColor: colors.dark.bgSurface,
    borderRadius: radius.md,
    padding: spacing[4],
    marginTop: spacing[4],
  },
  ollamaTitle: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.semibold,
    color: colors.dark.textPrimary,
    marginBottom: spacing[2],
  },
  ollamaText: {
    fontSize: typography.size.sm,
    color: colors.dark.textSecondary,
    lineHeight: typography.size.sm * typography.lineHeight.relaxed,
  },
  integrationList: {
    marginBottom: spacing[6],
  },
  integrationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.dark.bgSurface,
    borderRadius: radius.md,
    padding: spacing[4],
    marginBottom: spacing[3],
  },
  integrationContent: {
    flex: 1,
  },
  integrationName: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.medium,
    color: colors.dark.textPrimary,
  },
  integrationDescription: {
    fontSize: typography.size.sm,
    color: colors.dark.textSecondary,
    marginTop: spacing[0.5],
  },
  connectButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing[2],
    paddingHorizontal: spacing[4],
    borderRadius: radius.DEFAULT,
  },
  connectButtonText: {
    color: colors.white,
    fontSize: typography.size.sm,
    fontWeight: typography.weight.medium,
  },
  connectedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.successSoft,
    paddingVertical: spacing[1],
    paddingHorizontal: spacing[3],
    borderRadius: radius.full,
  },
  connectedText: {
    color: colors.success,
    fontSize: typography.size.sm,
    marginLeft: spacing[1],
  },
  comingSoonText: {
    fontSize: typography.size.sm,
    color: colors.dark.textTertiary,
  },
  roleContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: spacing[2],
    marginBottom: spacing[6],
  },
  roleOption: {
    backgroundColor: colors.dark.bgSurface,
    borderWidth: 1,
    borderColor: colors.dark.border,
    borderRadius: radius.full,
    paddingVertical: spacing[2],
    paddingHorizontal: spacing[4],
    marginRight: spacing[2],
    marginBottom: spacing[2],
  },
  roleOptionSelected: {
    backgroundColor: colors.primaryGlow,
    borderColor: colors.primary,
  },
  roleText: {
    fontSize: typography.size.sm,
    color: colors.dark.textSecondary,
  },
  roleTextSelected: {
    color: colors.primary,
    fontWeight: typography.weight.medium,
  },
});
