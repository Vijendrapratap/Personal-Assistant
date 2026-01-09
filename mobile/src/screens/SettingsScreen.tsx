/**
 * SettingsScreen - Comprehensive settings matching Alfred design
 * Includes profile, Alfred persona, integrations, notifications, and privacy
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Switch,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../theme';
import { Text, Card } from '../components/common';
import { profileApi } from '../api/services';
import { logout } from '../api/client';

interface SettingsScreenProps {
  navigation: any;
}

interface SettingRowProps {
  icon: string;
  label: string;
  value?: string;
  onPress?: () => void;
  showChevron?: boolean;
  isLast?: boolean;
  theme: any;
}

const SettingRow = ({ icon, label, value, onPress, showChevron = true, isLast, theme }: SettingRowProps) => (
  <TouchableOpacity
    style={[
      styles.settingRow,
      !isLast && { borderBottomWidth: 1, borderBottomColor: theme.colors.border },
    ]}
    onPress={onPress}
    disabled={!onPress}
    activeOpacity={onPress ? 0.7 : 1}
  >
    <View style={styles.settingLeft}>
      <Text style={styles.settingIcon}>{icon}</Text>
      <Text style={[styles.settingLabel, { color: theme.colors.textPrimary }]}>{label}</Text>
    </View>
    <View style={styles.settingRight}>
      {value && (
        <Text style={[styles.settingValue, { color: theme.colors.textSecondary }]}>{value}</Text>
      )}
      {showChevron && onPress && (
        <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>›</Text>
      )}
    </View>
  </TouchableOpacity>
);

interface ToggleRowProps {
  icon: string;
  label: string;
  value: boolean;
  onToggle: (value: boolean) => void;
  isLast?: boolean;
  theme: any;
}

const ToggleRow = ({ icon, label, value, onToggle, isLast, theme }: ToggleRowProps) => (
  <View
    style={[
      styles.settingRow,
      !isLast && { borderBottomWidth: 1, borderBottomColor: theme.colors.border },
    ]}
  >
    <View style={styles.settingLeft}>
      <Text style={styles.settingIcon}>{icon}</Text>
      <Text style={[styles.settingLabel, { color: theme.colors.textPrimary }]}>{label}</Text>
    </View>
    <Switch
      value={value}
      onValueChange={onToggle}
      trackColor={{ false: theme.colors.bgHover, true: theme.colors.primary }}
      thumbColor={theme.colors.white}
    />
  </View>
);

export default function SettingsScreen({ navigation }: SettingsScreenProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<any>(null);

  // Settings state
  const [dailyBriefing, setDailyBriefing] = useState(true);
  const [pushReminders, setPushReminders] = useState(true);
  const [suggestions, setSuggestions] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await profileApi.get();
      setProfile(data);
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            await logout();
            navigation.reset({ index: 0, routes: [{ name: 'Auth' }] });
          },
        },
      ]
    );
  };

  const handleClearHistory = () => {
    Alert.alert(
      'Clear Assistant History',
      'This will delete all conversation history with Alfred. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: () => {
            // TODO: Implement clear history
          },
        },
      ]
    );
  };

  const getInitial = () => {
    if (profile?.name) return profile.name.charAt(0).toUpperCase();
    if (profile?.email) return profile.email.charAt(0).toUpperCase();
    return 'U';
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.bg }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.bg }]} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={[styles.backIcon, { color: theme.colors.textPrimary }]}>‹</Text>
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.colors.textPrimary }]}>Settings</Text>
        <TouchableOpacity onPress={() => navigation.navigate('EditProfile')}>
          <Text style={[styles.doneButton, { color: theme.colors.primary }]}>Done</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 100 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Profile Section */}
        <TouchableOpacity
          style={[styles.profileSection, { backgroundColor: theme.colors.bgSurface }]}
          onPress={() => navigation.navigate('EditProfile')}
        >
          <View style={[styles.profileAvatar, { backgroundColor: theme.colors.primary }]}>
            <Text style={styles.avatarText}>{getInitial()}</Text>
          </View>
          <View style={styles.profileInfo}>
            <View style={styles.profileNameRow}>
              <Text style={[styles.profileName, { color: theme.colors.textPrimary }]}>
                {profile?.name || 'User'}
              </Text>
              <View style={[styles.activeBadge, { backgroundColor: theme.colors.success }]}>
                <Text style={styles.activeBadgeText}>Active</Text>
              </View>
            </View>
            <Text style={[styles.profileEmail, { color: theme.colors.textSecondary }]}>
              {profile?.email || 'user@example.com'}
            </Text>
          </View>
          <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>›</Text>
        </TouchableOpacity>

        <Text style={[styles.manageAccount, { color: theme.colors.primary }]}>
          Manage Account
        </Text>

        {/* Alfred Persona Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
            ALFRED PERSONA
          </Text>
          <Card style={styles.sectionCard} padding="none">
            <SettingRow
              icon="🎤"
              label="Voice"
              value="British Male"
              onPress={() => navigation.navigate('VoiceSettings')}
              theme={theme}
            />
            <SettingRow
              icon="👋"
              label="Wake Word"
              value="Hey Alfred"
              onPress={() => navigation.navigate('WakeWordSettings')}
              theme={theme}
            />
            <SettingRow
              icon="💬"
              label="Response Style"
              value="Concise"
              onPress={() => navigation.navigate('ResponseStyleSettings')}
              isLast
              theme={theme}
            />
          </Card>
        </View>

        {/* Integrations Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
            INTEGRATIONS
          </Text>
          <Card style={styles.sectionCard} padding="none">
            <SettingRow
              icon="📅"
              label="Calendar"
              value="Google"
              onPress={() => navigation.navigate('CalendarSettings')}
              theme={theme}
            />
            <SettingRow
              icon="🎵"
              label="Music Service"
              value="Spotify"
              onPress={() => navigation.navigate('MusicSettings')}
              theme={theme}
            />
            <SettingRow
              icon="🏠"
              label="Smart Home"
              value="HomeKit"
              onPress={() => navigation.navigate('SmartHomeSettings')}
              isLast
              theme={theme}
            />
          </Card>
        </View>

        {/* Notifications Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
            NOTIFICATIONS
          </Text>
          <Card style={styles.sectionCard} padding="none">
            <ToggleRow
              icon="☀️"
              label="Daily Briefing"
              value={dailyBriefing}
              onToggle={setDailyBriefing}
              theme={theme}
            />
            <ToggleRow
              icon="🔔"
              label="Push Reminders"
              value={pushReminders}
              onToggle={setPushReminders}
              theme={theme}
            />
            <ToggleRow
              icon="💡"
              label="Suggestions"
              value={suggestions}
              onToggle={setSuggestions}
              isLast
              theme={theme}
            />
          </Card>
        </View>

        {/* Privacy & Data Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
            PRIVACY & DATA
          </Text>
          <Card style={styles.sectionCard} padding="none">
            <SettingRow
              icon="📤"
              label="Export My Data"
              onPress={() => {}}
              theme={theme}
            />
            <TouchableOpacity
              style={[styles.settingRow]}
              onPress={handleClearHistory}
            >
              <View style={styles.settingLeft}>
                <Text style={styles.settingIcon}>🗑️</Text>
                <Text style={[styles.settingLabel, { color: theme.colors.danger }]}>
                  Clear Assistant History
                </Text>
              </View>
            </TouchableOpacity>
          </Card>
        </View>

        {/* Sign Out Button */}
        <TouchableOpacity
          style={[styles.signOutButton, { backgroundColor: theme.colors.bgSurface }]}
          onPress={handleLogout}
        >
          <Text style={[styles.signOutText, { color: theme.colors.danger }]}>Sign Out</Text>
        </TouchableOpacity>

        {/* Version */}
        <Text style={[styles.versionText, { color: theme.colors.textTertiary }]}>
          Alfred v2.0.0
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'flex-start',
  },
  backIcon: {
    fontSize: 32,
    fontWeight: '300',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  doneButton: {
    fontSize: 17,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
  },
  profileSection: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 16,
    marginTop: 8,
  },
  profileAvatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  profileInfo: {
    flex: 1,
    marginLeft: 14,
  },
  profileNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  profileName: {
    fontSize: 18,
    fontWeight: '600',
  },
  activeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  activeBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  profileEmail: {
    fontSize: 14,
    marginTop: 2,
  },
  manageAccount: {
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 24,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
    marginLeft: 4,
  },
  sectionCard: {
    overflow: 'hidden',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  settingLabel: {
    fontSize: 16,
  },
  settingRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingValue: {
    fontSize: 15,
    marginRight: 4,
  },
  chevron: {
    fontSize: 22,
    fontWeight: '300',
  },
  signOutButton: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  signOutText: {
    fontSize: 16,
    fontWeight: '600',
  },
  versionText: {
    fontSize: 13,
    textAlign: 'center',
    marginTop: 24,
    marginBottom: 20,
  },
});
