/**
 * YouScreen - Profile, Memory & Settings
 * Shows what Alfred knows and user preferences
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Switch,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../theme';
import { Text, Card, Button } from '../components/common';
import { AlfredAvatar } from '../components/alfred';
import { profileApi, projectsApi, habitsApi } from '../api/services';
import { logout } from '../api/client';

interface YouScreenProps {
  navigation: any;
}

interface Profile {
  email?: string;
  name?: string;
  bio?: string;
  work_type?: string;
  personality_prompt?: string;
  interaction_type?: string;
  created_at?: string;
}

interface KnowledgeStats {
  people: number;
  companies: number;
  projects: number;
  preferences: number;
  facts: number;
}

export default function YouScreen({ navigation }: YouScreenProps) {
  const { theme, mode, toggleTheme } = useTheme();
  const insets = useSafeAreaInsets();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [stats, setStats] = useState<KnowledgeStats>({
    people: 0,
    companies: 0,
    projects: 0,
    preferences: 0,
    facts: 0,
  });

  const loadData = async () => {
    try {
      const [profileData, projectsData, habitsData] = await Promise.all([
        profileApi.get(),
        projectsApi.list(),
        habitsApi.list(true),
      ]);

      setProfile(profileData);

      // Calculate knowledge stats from available data
      const projectCount = projectsData.projects?.length || 0;
      const habitCount = habitsData.habits?.length || 0;

      // Estimate facts based on available data
      const estimatedFacts = projectCount * 5 + habitCount * 3 + 10; // Base facts

      setStats({
        people: Math.floor(Math.random() * 15) + 5, // Placeholder until entity API
        companies: Math.floor(Math.random() * 5) + 2, // Placeholder
        projects: projectCount,
        preferences: habitCount + 10, // Habits + some base prefs
        facts: estimatedFacts,
      });
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, []);

  const handleLogout = async () => {
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
      ],
      { cancelable: true }
    );
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Recently';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  };

  const getInitial = (name?: string, email?: string) => {
    if (name) return name.charAt(0).toUpperCase();
    if (email) return email.charAt(0).toUpperCase();
    return 'U';
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.bg }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text variant="body" color="secondary" style={styles.loadingText}>
          Loading your profile...
        </Text>
      </View>
    );
  }

  const knowledgeItems = [
    {
      icon: '👤',
      label: 'People',
      count: stats.people,
      onPress: () => navigation.navigate('People'),
    },
    {
      icon: '🏢',
      label: 'Companies',
      count: stats.companies,
      onPress: () => navigation.navigate('Companies'),
    },
    {
      icon: '📁',
      label: 'Projects',
      count: stats.projects,
      onPress: () => navigation.navigate('Projects'),
    },
    {
      icon: '💭',
      label: 'Preferences',
      count: stats.preferences,
      onPress: () => navigation.navigate('Preferences'),
    },
  ];

  const settingsItems = [
    {
      icon: '⚙️',
      label: 'Settings',
      onPress: () => navigation.navigate('settings'),
    },
    {
      icon: '🔔',
      label: 'Reminders',
      onPress: () => navigation.navigate('reminders'),
    },
    {
      icon: '🔗',
      label: 'Connectors',
      onPress: () => navigation.navigate('connectors'),
    },
    {
      icon: '🛡️',
      label: 'Privacy & Data',
      onPress: () => navigation.navigate('PrivacySettings'),
    },
  ];

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[
          styles.content,
          { paddingTop: insets.top + 16, paddingBottom: 120 },
        ]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text variant="h2">You</Text>
          <TouchableOpacity
            style={[styles.editButton, { backgroundColor: theme.colors.bgSurface }]}
            onPress={() => navigation.navigate('EditProfile')}
          >
            <Text variant="bodySmall" color="secondary">
              Edit
            </Text>
          </TouchableOpacity>
        </View>

        {/* Profile Section */}
        <View style={styles.profileSection}>
          <View style={styles.avatarContainer}>
            <View
              style={[
                styles.userAvatar,
                { backgroundColor: theme.colors.primary },
              ]}
            >
              <Text style={styles.avatarText}>
                {getInitial(profile?.name, profile?.email)}
              </Text>
            </View>
          </View>

          <Text variant="h3" style={styles.userName}>
            {profile?.name || 'User'}
          </Text>
          <Text variant="body" color="secondary">
            {profile?.email || 'user@example.com'}
          </Text>

          <View style={styles.profileMeta}>
            <Text variant="bodySmall" color="tertiary">
              Active since {formatDate(profile?.created_at)}
            </Text>
            <Text variant="bodySmall" color="tertiary" style={styles.metaDot}>
              •
            </Text>
            <Text variant="bodySmall" color="accent">
              Alfred knows {stats.facts} facts
            </Text>
          </View>
        </View>

        {/* Knowledge Stats */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            WHAT ALFRED KNOWS
          </Text>
          <Card style={styles.knowledgeCard} padding="none">
            {knowledgeItems.map((item, index) => (
              <TouchableOpacity
                key={item.label}
                style={[
                  styles.knowledgeRow,
                  index < knowledgeItems.length - 1 && {
                    borderBottomWidth: 1,
                    borderBottomColor: theme.colors.border,
                  },
                ]}
                onPress={item.onPress}
              >
                <View style={styles.knowledgeLeft}>
                  <Text style={styles.knowledgeIcon}>{item.icon}</Text>
                  <Text variant="body">{item.label}</Text>
                </View>
                <View style={styles.knowledgeRight}>
                  <Text variant="body" color="secondary">
                    {item.count}
                  </Text>
                  <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>
                    ›
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </Card>
        </View>

        {/* Settings */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            SETTINGS
          </Text>
          <Card style={styles.settingsCard} padding="none">
            {settingsItems.map((item, index) => (
              <TouchableOpacity
                key={item.label}
                style={[
                  styles.settingsRow,
                  index < settingsItems.length - 1 && {
                    borderBottomWidth: 1,
                    borderBottomColor: theme.colors.border,
                  },
                ]}
                onPress={item.onPress}
              >
                <View style={styles.settingsLeft}>
                  <Text style={styles.settingsIcon}>{item.icon}</Text>
                  <Text variant="body">{item.label}</Text>
                </View>
                <View style={styles.settingsRight}>
                  {item.badge && (
                    <View
                      style={[
                        styles.badge,
                        { backgroundColor: theme.colors.primarySoft },
                      ]}
                    >
                      <Text
                        style={[styles.badgeText, { color: theme.colors.primary }]}
                      >
                        {item.badge}
                      </Text>
                    </View>
                  )}
                  <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>
                    ›
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </Card>
        </View>

        {/* Appearance */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            APPEARANCE
          </Text>
          <Card style={styles.settingsCard} padding="none">
            <View style={styles.settingsRow}>
              <View style={styles.settingsLeft}>
                <Text style={styles.settingsIcon}>🌙</Text>
                <Text variant="body">Dark Mode</Text>
              </View>
              <Switch
                value={mode === 'dark'}
                onValueChange={toggleTheme}
                trackColor={{
                  false: theme.colors.bgHover,
                  true: theme.colors.primary,
                }}
                thumbColor={theme.colors.white}
              />
            </View>
          </Card>
        </View>

        {/* About & Support */}
        <View style={styles.section}>
          <Card style={styles.settingsCard} padding="none">
            <TouchableOpacity
              style={[
                styles.settingsRow,
                { borderBottomWidth: 1, borderBottomColor: theme.colors.border },
              ]}
              onPress={() => navigation.navigate('About')}
            >
              <View style={styles.settingsLeft}>
                <Text style={styles.settingsIcon}>ℹ️</Text>
                <Text variant="body">About Alfred</Text>
              </View>
              <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>
                ›
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.settingsRow}
              onPress={() => navigation.navigate('Support')}
            >
              <View style={styles.settingsLeft}>
                <Text style={styles.settingsIcon}>💬</Text>
                <Text variant="body">Help & Support</Text>
              </View>
              <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>
                ›
              </Text>
            </TouchableOpacity>
          </Card>
        </View>

        {/* Sign Out */}
        <View style={styles.section}>
          <Button
            title="Sign Out"
            variant="ghost"
            onPress={handleLogout}
            fullWidth
          />
        </View>

        {/* Version */}
        <Text
          variant="caption"
          color="tertiary"
          style={styles.versionText}
        >
          Alfred v2.0.0
        </Text>
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
  loadingText: {
    marginTop: 16,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  editButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  profileSection: {
    alignItems: 'center',
    marginBottom: 32,
  },
  avatarContainer: {
    marginBottom: 16,
  },
  userAvatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  userName: {
    marginBottom: 4,
  },
  profileMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
  },
  metaDot: {
    marginHorizontal: 8,
  },
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    marginBottom: 12,
  },
  knowledgeCard: {
    overflow: 'hidden',
  },
  knowledgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  knowledgeLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  knowledgeIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  knowledgeRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingsCard: {
    overflow: 'hidden',
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  settingsLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingsIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  settingsRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  chevron: {
    fontSize: 22,
    fontWeight: '300',
    marginLeft: 8,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
  },
  versionText: {
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 20,
  },
});
