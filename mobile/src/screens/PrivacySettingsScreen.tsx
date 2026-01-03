/**
 * PrivacySettingsScreen - Data privacy and control
 */

import React, { useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../theme';
import { Text, Card, Button } from '../components/common';

interface PrivacySettingsScreenProps {
  navigation: any;
}

export default function PrivacySettingsScreen({
  navigation,
}: PrivacySettingsScreenProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [exporting, setExporting] = useState(false);

  const handleExportData = async () => {
    setExporting(true);
    try {
      // TODO: Implement actual export
      await new Promise((resolve) => setTimeout(resolve, 2000));
      Alert.alert(
        'Export Ready',
        'Your data export has been prepared. Check your email for the download link.'
      );
    } catch (err) {
      Alert.alert('Error', 'Failed to export data. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const handleClearData = (type: string) => {
    Alert.alert(
      `Clear ${type}?`,
      `This will permanently delete all your ${type.toLowerCase()}. This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: () => {
            // TODO: Implement actual clearing
            Alert.alert('Cleared', `Your ${type.toLowerCase()} has been cleared.`);
          },
        },
      ]
    );
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'This will permanently delete your account and all associated data. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete Account',
          style: 'destructive',
          onPress: () => {
            Alert.alert(
              'Confirm Deletion',
              'Type "DELETE" to confirm account deletion.',
              [{ text: 'Cancel', style: 'cancel' }]
            );
          },
        },
      ]
    );
  };

  const privacyItems = [
    {
      icon: '🧠',
      title: 'What Alfred Learns',
      description: 'Alfred learns your preferences, patterns, and context from conversations',
    },
    {
      icon: '🔒',
      title: 'Data Storage',
      description: 'Your data is encrypted and stored securely on our servers',
    },
    {
      icon: '🚫',
      title: 'No Data Selling',
      description: 'We never sell your personal data to third parties',
    },
    {
      icon: '🤖',
      title: 'AI Processing',
      description: 'Conversations are processed by AI to provide intelligent assistance',
    },
  ];

  const dataManagementItems = [
    {
      icon: '💬',
      title: 'Conversation History',
      action: () => handleClearData('Conversation History'),
    },
    {
      icon: '👤',
      title: 'Learned Preferences',
      action: () => handleClearData('Learned Preferences'),
    },
    {
      icon: '📊',
      title: 'Usage Analytics',
      action: () => handleClearData('Usage Analytics'),
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
          Privacy & Data
        </Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* How Alfred Uses Your Data */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            HOW ALFRED USES YOUR DATA
          </Text>
          <Card padding="none" style={styles.optionsCard}>
            {privacyItems.map((item, index) => (
              <View
                key={item.title}
                style={[
                  styles.infoRow,
                  index < privacyItems.length - 1 && {
                    borderBottomWidth: 1,
                    borderBottomColor: theme.colors.border,
                  },
                ]}
              >
                <Text style={styles.infoIcon}>{item.icon}</Text>
                <View style={styles.infoText}>
                  <Text variant="body">{item.title}</Text>
                  <Text variant="bodySmall" color="tertiary" style={styles.infoDesc}>
                    {item.description}
                  </Text>
                </View>
              </View>
            ))}
          </Card>
        </View>

        {/* Export Data */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            EXPORT YOUR DATA
          </Text>
          <Card style={styles.exportCard}>
            <Text variant="body" color="secondary" style={styles.exportText}>
              Download a copy of all your data including tasks, habits, projects,
              and conversation history.
            </Text>
            <Button
              title="Export All Data"
              variant="secondary"
              onPress={handleExportData}
              loading={exporting}
              fullWidth
            />
          </Card>
        </View>

        {/* Clear Specific Data */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            CLEAR DATA
          </Text>
          <Card padding="none" style={styles.optionsCard}>
            {dataManagementItems.map((item, index) => (
              <TouchableOpacity
                key={item.title}
                style={[
                  styles.clearRow,
                  index < dataManagementItems.length - 1 && {
                    borderBottomWidth: 1,
                    borderBottomColor: theme.colors.border,
                  },
                ]}
                onPress={item.action}
              >
                <View style={styles.clearLeft}>
                  <Text style={styles.clearIcon}>{item.icon}</Text>
                  <Text variant="body">{item.title}</Text>
                </View>
                <Text style={[styles.clearAction, { color: theme.colors.danger }]}>
                  Clear
                </Text>
              </TouchableOpacity>
            ))}
          </Card>
        </View>

        {/* Delete Account */}
        <View style={styles.section}>
          <Text variant="label" color="secondary" style={styles.sectionLabel}>
            DANGER ZONE
          </Text>
          <Card
            style={[styles.dangerCard, { borderColor: theme.colors.danger + '40' }]}
            variant="outlined"
          >
            <View style={styles.dangerContent}>
              <Text variant="body" style={{ fontWeight: '600' }}>
                Delete Account
              </Text>
              <Text variant="bodySmall" color="tertiary" style={styles.dangerText}>
                Permanently delete your account and all associated data. This
                action cannot be undone.
              </Text>
            </View>
            <Button
              title="Delete Account"
              variant="danger"
              size="sm"
              onPress={handleDeleteAccount}
            />
          </Card>
        </View>

        {/* Privacy Policy Link */}
        <View style={styles.section}>
          <TouchableOpacity
            style={styles.linkRow}
            onPress={() => {
              // TODO: Open privacy policy
              Alert.alert('Privacy Policy', 'Opening privacy policy...');
            }}
          >
            <Text variant="body" color="accent">
              Read Full Privacy Policy
            </Text>
            <Text style={{ color: theme.colors.primary }}>→</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.linkRow}
            onPress={() => {
              // TODO: Open terms
              Alert.alert('Terms of Service', 'Opening terms of service...');
            }}
          >
            <Text variant="body" color="accent">
              Terms of Service
            </Text>
            <Text style={{ color: theme.colors.primary }}>→</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    marginBottom: 12,
  },
  optionsCard: {
    overflow: 'hidden',
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  infoIcon: {
    fontSize: 20,
    marginRight: 12,
    marginTop: 2,
  },
  infoText: {
    flex: 1,
  },
  infoDesc: {
    marginTop: 4,
  },
  exportCard: {
    gap: 16,
  },
  exportText: {
    lineHeight: 22,
  },
  clearRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  clearLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  clearIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  clearAction: {
    fontWeight: '600',
    fontSize: 14,
  },
  dangerCard: {
    backgroundColor: 'transparent',
  },
  dangerContent: {
    marginBottom: 16,
  },
  dangerText: {
    marginTop: 4,
    lineHeight: 20,
  },
  linkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
  },
});
