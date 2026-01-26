/**
 * VoiceSettingsScreen - Voice & language preferences
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Switch } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../theme';

interface SettingRowProps {
  icon: string;
  title: string;
  subtitle?: string;
  value?: boolean;
  onValueChange?: (value: boolean) => void;
  onPress?: () => void;
  theme: any;
}

const SettingRow: React.FC<SettingRowProps> = ({
  icon,
  title,
  subtitle,
  value,
  onValueChange,
  onPress,
  theme,
}) => (
  <TouchableOpacity
    style={styles.settingRow}
    onPress={onPress}
    disabled={!onPress && !onValueChange}
    activeOpacity={onPress ? 0.7 : 1}
  >
    <View style={[styles.settingIcon, { backgroundColor: theme.colors.bgSurface }]}>
      <Text style={{ fontSize: 18 }}>{icon}</Text>
    </View>
    <View style={styles.settingContent}>
      <Text style={[styles.settingTitle, { color: theme.colors.textPrimary }]}>
        {title}
      </Text>
      {subtitle && (
        <Text style={[styles.settingSubtitle, { color: theme.colors.textSecondary }]}>
          {subtitle}
        </Text>
      )}
    </View>
    {onValueChange !== undefined && (
      <Switch
        value={value}
        onValueChange={onValueChange}
        trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
        thumbColor="#fff"
      />
    )}
    {onPress && (
      <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>›</Text>
    )}
  </TouchableOpacity>
);

export default function VoiceSettingsScreen() {
  const { theme } = useTheme();
  const navigation = useNavigation();

  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [autoListen, setAutoListen] = useState(false);
  const [speechFeedback, setSpeechFeedback] = useState(true);
  const [hapticFeedback, setHapticFeedback] = useState(true);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={[styles.backIcon, { color: theme.colors.textPrimary }]}>‹</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: theme.colors.textPrimary }]}>
          Voice & Language
        </Text>
        <View style={styles.headerRight} />
      </View>

      <View style={styles.content}>
        {/* Voice Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
            VOICE
          </Text>
          <View style={[styles.settingsCard, { backgroundColor: theme.colors.bgElevated }]}>
            <SettingRow
              icon="🎤"
              title="Voice Input"
              subtitle="Enable voice commands"
              value={voiceEnabled}
              onValueChange={setVoiceEnabled}
              theme={theme}
            />
            <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />
            <SettingRow
              icon="👂"
              title="Auto-Listen Mode"
              subtitle="Automatically listen after Alfred responds"
              value={autoListen}
              onValueChange={setAutoListen}
              theme={theme}
            />
            <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />
            <SettingRow
              icon="🔊"
              title="Speech Feedback"
              subtitle="Alfred speaks responses aloud"
              value={speechFeedback}
              onValueChange={setSpeechFeedback}
              theme={theme}
            />
          </View>
        </View>

        {/* Feedback Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
            FEEDBACK
          </Text>
          <View style={[styles.settingsCard, { backgroundColor: theme.colors.bgElevated }]}>
            <SettingRow
              icon="📳"
              title="Haptic Feedback"
              subtitle="Vibration for interactions"
              value={hapticFeedback}
              onValueChange={setHapticFeedback}
              theme={theme}
            />
          </View>
        </View>

        {/* Language Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
            LANGUAGE
          </Text>
          <View style={[styles.settingsCard, { backgroundColor: theme.colors.bgElevated }]}>
            <SettingRow
              icon="🌐"
              title="Language"
              subtitle="English (US)"
              onPress={() => {}}
              theme={theme}
            />
            <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />
            <SettingRow
              icon="🗣️"
              title="Voice Style"
              subtitle="Natural"
              onPress={() => {}}
              theme={theme}
            />
          </View>
        </View>

        {/* Info */}
        <View style={[styles.infoCard, { backgroundColor: theme.colors.primaryGlow }]}>
          <Text style={styles.infoIcon}>🎙️</Text>
          <Text style={[styles.infoText, { color: theme.colors.textSecondary }]}>
            Voice features use Whisper for transcription. Audio is processed
            securely and not stored after transcription.
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: -8,
  },
  backIcon: {
    fontSize: 32,
    fontWeight: '300',
  },
  title: {
    flex: 1,
    fontSize: 17,
    fontWeight: '600',
    textAlign: 'center',
  },
  headerRight: {
    width: 40,
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
    marginLeft: 4,
  },
  settingsCard: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  settingIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  settingContent: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 15,
    fontWeight: '500',
  },
  settingSubtitle: {
    fontSize: 13,
    marginTop: 2,
  },
  chevron: {
    fontSize: 24,
    fontWeight: '300',
  },
  divider: {
    height: 1,
    marginLeft: 66,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 16,
    borderRadius: 12,
    marginTop: 8,
  },
  infoIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
});
