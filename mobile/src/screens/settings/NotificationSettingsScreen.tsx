/**
 * NotificationSettingsScreen - Configure Alfred's notifications
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Switch,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../theme';
import { Text, Card, Button } from '../../components/common';
import { notificationsApi, NotificationPreferences } from '../../api/services';

interface NotificationSettingsScreenProps {
  navigation: any;
}

export default function NotificationSettingsScreen({
  navigation,
}: NotificationSettingsScreenProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    morning_briefing: true,
    evening_review: true,
    habit_reminders: true,
    task_due_reminders: true,
    project_nudges: true,
  });

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const prefs = await notificationsApi.getPreferences();
      setPreferences(prefs);
    } catch (err) {
      console.error('Failed to load notification preferences:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (key: keyof NotificationPreferences) => {
    const newPrefs = {
      ...preferences,
      [key]: !preferences[key],
    };
    setPreferences(newPrefs);

    try {
      await notificationsApi.updatePreferences(newPrefs);
    } catch (err) {
      console.error('Failed to update preferences:', err);
      // Revert on error
      setPreferences(preferences);
      Alert.alert('Error', 'Failed to save preference. Please try again.');
    }
  };

  const handleTestNotification = async () => {
    setSaving(true);
    try {
      await notificationsApi.sendTest();
      Alert.alert('Success', 'Test notification sent! Check your device.');
    } catch (err) {
      Alert.alert('Error', 'Failed to send test notification.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.bg }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  const notificationOptions = [
    {
      key: 'morning_briefing' as const,
      icon: '🌅',
      title: 'Morning Briefing',
      description: "Start your day with Alfred's personalized summary",
    },
    {
      key: 'evening_review' as const,
      icon: '🌙',
      title: 'Evening Review',
      description: 'Reflect on your day and plan for tomorrow',
    },
    {
      key: 'habit_reminders' as const,
      icon: '🔥',
      title: 'Habit Reminders',
      description: 'Get reminded to maintain your streaks',
    },
    {
      key: 'task_due_reminders' as const,
      icon: '⏰',
      title: 'Task Due Reminders',
      description: 'Alerts for upcoming and overdue tasks',
    },
    {
      key: 'project_nudges' as const,
      icon: '💡',
      title: 'Project Nudges',
      description: 'Proactive reminders when projects need attention',
    },
  ];

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      {/* Header */}
      <View
        style={[
          styles.header,
          {
            paddingTop: insets.top + 12,
            backgroundColor: theme.colors.bg,
            borderBottomColor: theme.colors.border,
          },
        ]}
      >
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={[styles.backText, { color: theme.colors.primary }]}>
            ← Back
          </Text>
        </TouchableOpacity>
        <Text variant="h3" style={styles.headerTitle}>
          Notifications
        </Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Info Card */}
        <Card
          variant="outlined"
          style={[styles.infoCard, { borderColor: theme.colors.primarySoft }]}
        >
          <Text variant="body" color="secondary">
            Alfred uses notifications to keep you informed and help you stay on
            track. Customize which notifications you receive below.
          </Text>
        </Card>

        {/* Notification Toggles */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            NOTIFICATION TYPES
          </Text>
          <Card padding="none" style={styles.optionsCard}>
            {notificationOptions.map((option, index) => (
              <View
                key={option.key}
                style={[
                  styles.optionRow,
                  index < notificationOptions.length - 1 && {
                    borderBottomWidth: 1,
                    borderBottomColor: theme.colors.border,
                  },
                ]}
              >
                <View style={styles.optionLeft}>
                  <Text style={styles.optionIcon}>{option.icon}</Text>
                  <View style={styles.optionText}>
                    <Text variant="body">{option.title}</Text>
                    <Text variant="bodySmall" color="tertiary" style={styles.optionDesc}>
                      {option.description}
                    </Text>
                  </View>
                </View>
                <Switch
                  value={preferences[option.key]}
                  onValueChange={() => handleToggle(option.key)}
                  trackColor={{
                    false: theme.colors.bgHover,
                    true: theme.colors.primary,
                  }}
                  thumbColor={theme.colors.white}
                />
              </View>
            ))}
          </Card>
        </View>

        {/* Schedule Section */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            SCHEDULE
          </Text>
          <Card padding="none" style={styles.optionsCard}>
            <TouchableOpacity
              style={[
                styles.scheduleRow,
                { borderBottomWidth: 1, borderBottomColor: theme.colors.border },
              ]}
              onPress={() => {
                // TODO: Time picker
                Alert.alert('Coming Soon', 'Time picker will be available soon.');
              }}
            >
              <View style={styles.scheduleLeft}>
                <Text variant="body">Morning Briefing Time</Text>
              </View>
              <View style={styles.scheduleRight}>
                <Text variant="body" color="secondary">
                  7:00 AM
                </Text>
                <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>
                  ›
                </Text>
              </View>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.scheduleRow}
              onPress={() => {
                Alert.alert('Coming Soon', 'Time picker will be available soon.');
              }}
            >
              <View style={styles.scheduleLeft}>
                <Text variant="body">Evening Review Time</Text>
              </View>
              <View style={styles.scheduleRight}>
                <Text variant="body" color="secondary">
                  9:00 PM
                </Text>
                <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>
                  ›
                </Text>
              </View>
            </TouchableOpacity>
          </Card>
        </View>

        {/* Quiet Hours */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            QUIET HOURS
          </Text>
          <Card padding="none" style={styles.optionsCard}>
            <View
              style={[
                styles.optionRow,
                { borderBottomWidth: 1, borderBottomColor: theme.colors.border },
              ]}
            >
              <View style={styles.optionLeft}>
                <Text style={styles.optionIcon}>🔕</Text>
                <View style={styles.optionText}>
                  <Text variant="body">Enable Quiet Hours</Text>
                  <Text variant="bodySmall" color="tertiary" style={styles.optionDesc}>
                    No notifications during set hours
                  </Text>
                </View>
              </View>
              <Switch
                value={false}
                onValueChange={() => {
                  Alert.alert('Coming Soon', 'Quiet hours will be available soon.');
                }}
                trackColor={{
                  false: theme.colors.bgHover,
                  true: theme.colors.primary,
                }}
                thumbColor={theme.colors.white}
              />
            </View>
            <TouchableOpacity style={styles.scheduleRow} disabled>
              <View style={styles.scheduleLeft}>
                <Text variant="body" color="tertiary">
                  Quiet Hours
                </Text>
              </View>
              <View style={styles.scheduleRight}>
                <Text variant="body" color="tertiary">
                  10:00 PM - 7:00 AM
                </Text>
              </View>
            </TouchableOpacity>
          </Card>
        </View>

        {/* Test Notification */}
        <View style={styles.section}>
          <Button
            title="Send Test Notification"
            variant="secondary"
            onPress={handleTestNotification}
            loading={saving}
            fullWidth
          />
        </View>
      </ScrollView>
    </View>
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
    paddingHorizontal: 20,
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  backButton: {
    width: 80,
  },
  backText: {
    fontSize: 15,
    fontWeight: '500',
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
  },
  headerSpacer: {
    width: 80,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  infoCard: {
    marginBottom: 24,
    backgroundColor: 'transparent',
  },
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    marginBottom: 12,
  },
  optionsCard: {
    overflow: 'hidden',
  },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  optionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 12,
  },
  optionIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  optionText: {
    flex: 1,
  },
  optionDesc: {
    marginTop: 2,
  },
  scheduleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  scheduleLeft: {
    flex: 1,
  },
  scheduleRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  chevron: {
    fontSize: 22,
    fontWeight: '300',
    marginLeft: 8,
  },
});
