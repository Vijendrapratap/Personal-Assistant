/**
 * IntegrationsScreen - Third-party integrations
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../theme';

interface IntegrationCardProps {
  icon: string;
  name: string;
  description: string;
  connected: boolean;
  comingSoon?: boolean;
  onPress: () => void;
  theme: any;
}

const IntegrationCard: React.FC<IntegrationCardProps> = ({
  icon,
  name,
  description,
  connected,
  comingSoon,
  onPress,
  theme,
}) => (
  <TouchableOpacity
    style={[styles.integrationCard, { backgroundColor: theme.colors.bgElevated }]}
    onPress={onPress}
    activeOpacity={comingSoon ? 1 : 0.7}
    disabled={comingSoon}
  >
    <View style={[styles.integrationIcon, { backgroundColor: theme.colors.bgSurface }]}>
      <Text style={{ fontSize: 28 }}>{icon}</Text>
    </View>
    <View style={styles.integrationContent}>
      <View style={styles.integrationHeader}>
        <Text style={[styles.integrationName, { color: theme.colors.textPrimary }]}>
          {name}
        </Text>
        {comingSoon && (
          <View style={[styles.badge, { backgroundColor: theme.colors.warning + '20' }]}>
            <Text style={[styles.badgeText, { color: theme.colors.warning }]}>
              Coming Soon
            </Text>
          </View>
        )}
        {connected && !comingSoon && (
          <View style={[styles.badge, { backgroundColor: theme.colors.success + '20' }]}>
            <Text style={[styles.badgeText, { color: theme.colors.success }]}>
              Connected
            </Text>
          </View>
        )}
      </View>
      <Text style={[styles.integrationDescription, { color: theme.colors.textSecondary }]}>
        {description}
      </Text>
    </View>
    {!comingSoon && (
      <Text style={[styles.chevron, { color: theme.colors.textTertiary }]}>›</Text>
    )}
  </TouchableOpacity>
);

export default function IntegrationsScreen() {
  const { theme } = useTheme();
  const navigation = useNavigation();

  const integrations = [
    {
      icon: '📅',
      name: 'Google Calendar',
      description: 'Sync events and schedule meetings',
      connected: false,
      comingSoon: true,
    },
    {
      icon: '📧',
      name: 'Gmail',
      description: 'Get email summaries and action items',
      connected: false,
      comingSoon: true,
    },
    {
      icon: '💬',
      name: 'Slack',
      description: 'Sync status and get message summaries',
      connected: false,
      comingSoon: true,
    },
    {
      icon: '📝',
      name: 'Notion',
      description: 'Connect notes and databases',
      connected: false,
      comingSoon: true,
    },
    {
      icon: '🐙',
      name: 'GitHub',
      description: 'Track issues and pull requests',
      connected: false,
      comingSoon: true,
    },
    {
      icon: '📊',
      name: 'Linear',
      description: 'Sync project tasks and issues',
      connected: false,
      comingSoon: true,
    },
  ];

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
          Integrations
        </Text>
        <View style={styles.headerRight} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Description */}
        <View style={styles.descriptionContainer}>
          <Text style={[styles.description, { color: theme.colors.textSecondary }]}>
            Connect Alfred with your favorite tools to get a unified view of your
            work and enable smarter suggestions.
          </Text>
        </View>

        {/* Integrations List */}
        <View style={styles.integrationsList}>
          {integrations.map((integration, index) => (
            <IntegrationCard
              key={index}
              {...integration}
              onPress={() => {
                if (!integration.comingSoon) {
                  // Handle connection
                }
              }}
              theme={theme}
            />
          ))}
        </View>

        {/* Request Integration */}
        <View style={[styles.requestCard, { backgroundColor: theme.colors.primaryGlow }]}>
          <Text style={styles.requestIcon}>💡</Text>
          <View style={styles.requestContent}>
            <Text style={[styles.requestTitle, { color: theme.colors.textPrimary }]}>
              Missing an integration?
            </Text>
            <Text style={[styles.requestText, { color: theme.colors.textSecondary }]}>
              Let us know which tools you'd like to connect with Alfred.
            </Text>
          </View>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
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
  },
  descriptionContainer: {
    marginBottom: 24,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
  },
  integrationsList: {
    gap: 12,
  },
  integrationCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 16,
  },
  integrationIcon: {
    width: 56,
    height: 56,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  integrationContent: {
    flex: 1,
  },
  integrationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  integrationName: {
    fontSize: 16,
    fontWeight: '600',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  integrationDescription: {
    fontSize: 13,
  },
  chevron: {
    fontSize: 24,
    fontWeight: '300',
    marginLeft: 8,
  },
  requestCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 16,
    borderRadius: 16,
    marginTop: 24,
  },
  requestIcon: {
    fontSize: 24,
    marginRight: 14,
  },
  requestContent: {
    flex: 1,
  },
  requestTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 4,
  },
  requestText: {
    fontSize: 13,
    lineHeight: 18,
  },
});
