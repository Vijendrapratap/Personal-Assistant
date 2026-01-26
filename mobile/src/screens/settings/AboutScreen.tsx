/**
 * AboutScreen - Information about Alfred
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../theme';

export default function AboutScreen() {
  const { theme } = useTheme();
  const navigation = useNavigation();

  const handleLink = (url: string) => {
    Linking.openURL(url);
  };

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
        <Text style={[styles.title, { color: theme.colors.textPrimary }]}>About</Text>
        <View style={styles.headerRight} />
      </View>

      <View style={styles.content}>
        {/* Logo/Avatar */}
        <View style={[styles.logoContainer, { backgroundColor: theme.colors.primarySoft }]}>
          <Text style={styles.logo}>🤖</Text>
        </View>

        <Text style={[styles.appName, { color: theme.colors.textPrimary }]}>
          Alfred
        </Text>
        <Text style={[styles.tagline, { color: theme.colors.textSecondary }]}>
          Your Proactive Digital Butler
        </Text>
        <Text style={[styles.version, { color: theme.colors.textTertiary }]}>
          Version 2.0.0
        </Text>

        {/* Description */}
        <View style={[styles.descriptionCard, { backgroundColor: theme.colors.bgElevated }]}>
          <Text style={[styles.description, { color: theme.colors.textSecondary }]}>
            Alfred is an intelligent personal assistant that helps you manage your time,
            tasks, and habits. Unlike traditional to-do apps, Alfred proactively
            suggests actions, learns your preferences, and adapts to your workflow.
          </Text>
        </View>

        {/* Features */}
        <View style={styles.featuresSection}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textSecondary }]}>
            KEY FEATURES
          </Text>
          <View style={[styles.featureCard, { backgroundColor: theme.colors.bgElevated }]}>
            {[
              { icon: '📋', text: 'Smart task management' },
              { icon: '✨', text: 'Habit tracking with streaks' },
              { icon: '🔔', text: 'Proactive reminders' },
              { icon: '🧠', text: 'Learns your preferences' },
              { icon: '🎤', text: 'Voice interaction' },
            ].map((feature, index) => (
              <View key={index} style={styles.featureRow}>
                <Text style={styles.featureIcon}>{feature.icon}</Text>
                <Text style={[styles.featureText, { color: theme.colors.textPrimary }]}>
                  {feature.text}
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.colors.textTertiary }]}>
            Made with care for productivity enthusiasts
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
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 32,
  },
  logoContainer: {
    width: 100,
    height: 100,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  logo: {
    fontSize: 48,
  },
  appName: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 4,
  },
  tagline: {
    fontSize: 15,
    marginBottom: 4,
  },
  version: {
    fontSize: 13,
    marginBottom: 32,
  },
  descriptionCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 32,
    width: '100%',
  },
  description: {
    fontSize: 14,
    lineHeight: 22,
    textAlign: 'center',
  },
  featuresSection: {
    width: '100%',
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
    marginLeft: 4,
  },
  featureCard: {
    borderRadius: 16,
    padding: 16,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  featureIcon: {
    fontSize: 20,
    marginRight: 14,
  },
  featureText: {
    fontSize: 15,
  },
  footer: {
    position: 'absolute',
    bottom: 32,
  },
  footerText: {
    fontSize: 12,
  },
});
