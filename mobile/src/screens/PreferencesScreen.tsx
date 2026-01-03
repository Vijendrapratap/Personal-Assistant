/**
 * PreferencesScreen - View and manage Alfred's learned preferences
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../theme';
import { knowledgeApi } from '../api/services';

interface PreferenceItemProps {
  preference: {
    key: string;
    value: string;
    confidence: number;
    source: string;
  };
  theme: any;
}

const PreferenceItem: React.FC<PreferenceItemProps> = ({ preference, theme }) => {
  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'conversation':
        return '💬';
      case 'observation':
        return '👁️';
      case 'inferred':
        return '🧠';
      default:
        return '📝';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return theme.colors.success;
    if (confidence >= 0.6) return theme.colors.warning;
    return theme.colors.textTertiary;
  };

  const formatKey = (key: string) => {
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <View style={[styles.preferenceItem, { backgroundColor: theme.colors.bgElevated }]}>
      <View style={styles.preferenceHeader}>
        <Text style={[styles.preferenceKey, { color: theme.colors.textSecondary }]}>
          {formatKey(preference.key)}
        </Text>
        <View style={styles.preferenceMetadata}>
          <Text style={styles.sourceIcon}>{getSourceIcon(preference.source)}</Text>
          <View
            style={[
              styles.confidenceDot,
              { backgroundColor: getConfidenceColor(preference.confidence) },
            ]}
          />
        </View>
      </View>
      <Text style={[styles.preferenceValue, { color: theme.colors.textPrimary }]}>
        {preference.value}
      </Text>
      <View style={styles.preferenceFooter}>
        <Text style={[styles.confidenceText, { color: theme.colors.textTertiary }]}>
          {Math.round(preference.confidence * 100)}% confident
        </Text>
        <Text style={[styles.sourceText, { color: theme.colors.textTertiary }]}>
          via {preference.source}
        </Text>
      </View>
    </View>
  );
};

export default function PreferencesScreen() {
  const { theme } = useTheme();
  const navigation = useNavigation();

  const [preferences, setPreferences] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPreferences = useCallback(async () => {
    try {
      setError(null);
      const response = await knowledgeApi.getPreferences();
      setPreferences(response.preferences || []);
    } catch (err) {
      console.error('Failed to fetch preferences:', err);
      setError('Failed to load preferences');
      // Use mock data for demo
      setPreferences([
        {
          key: 'communication_style',
          value: 'Concise and direct',
          confidence: 0.85,
          source: 'conversation',
        },
        {
          key: 'preferred_work_hours',
          value: 'Morning (6am - 12pm)',
          confidence: 0.92,
          source: 'observation',
        },
        {
          key: 'meeting_preference',
          value: 'Prefers async communication',
          confidence: 0.78,
          source: 'inferred',
        },
        {
          key: 'task_priority',
          value: 'Focus on high-impact items first',
          confidence: 0.81,
          source: 'conversation',
        },
        {
          key: 'break_frequency',
          value: 'Short breaks every 90 minutes',
          confidence: 0.65,
          source: 'inferred',
        },
      ]);
    }
  }, []);

  useEffect(() => {
    fetchPreferences().finally(() => setLoading(false));
  }, [fetchPreferences]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchPreferences();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.bg }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
            Loading preferences...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

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
          Learned Preferences
        </Text>
        <View style={styles.headerRight} />
      </View>

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={theme.colors.primary}
          />
        }
      >
        {/* Description */}
        <View style={styles.descriptionContainer}>
          <Text style={[styles.description, { color: theme.colors.textSecondary }]}>
            Alfred learns your preferences from conversations and behavior to
            provide better suggestions. Tap any preference to correct it.
          </Text>
        </View>

        {/* Legend */}
        <View style={[styles.legend, { backgroundColor: theme.colors.bgElevated }]}>
          <View style={styles.legendItem}>
            <Text style={styles.legendIcon}>💬</Text>
            <Text style={[styles.legendText, { color: theme.colors.textSecondary }]}>
              From chat
            </Text>
          </View>
          <View style={styles.legendItem}>
            <Text style={styles.legendIcon}>👁️</Text>
            <Text style={[styles.legendText, { color: theme.colors.textSecondary }]}>
              Observed
            </Text>
          </View>
          <View style={styles.legendItem}>
            <Text style={styles.legendIcon}>🧠</Text>
            <Text style={[styles.legendText, { color: theme.colors.textSecondary }]}>
              Inferred
            </Text>
          </View>
        </View>

        {/* Preferences List */}
        <View style={styles.preferencesList}>
          {preferences.map((pref, index) => (
            <PreferenceItem key={index} preference={pref} theme={theme} />
          ))}
        </View>

        {/* Empty State */}
        {preferences.length === 0 && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🧠</Text>
            <Text style={[styles.emptyTitle, { color: theme.colors.textPrimary }]}>
              No preferences yet
            </Text>
            <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
              Alfred will learn your preferences as you use the app.
            </Text>
          </View>
        )}

        {/* Info */}
        <View style={[styles.infoCard, { backgroundColor: theme.colors.primaryGlow }]}>
          <Text style={styles.infoIcon}>💡</Text>
          <Text style={[styles.infoText, { color: theme.colors.textSecondary }]}>
            You can teach Alfred your preferences by telling it directly.
            Try saying "I prefer morning meetings" or "I like concise updates".
          </Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 15,
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
    marginBottom: 16,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 12,
    borderRadius: 12,
    marginBottom: 20,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  legendText: {
    fontSize: 12,
  },
  preferencesList: {
    gap: 12,
  },
  preferenceItem: {
    padding: 16,
    borderRadius: 16,
  },
  preferenceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  preferenceKey: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  preferenceMetadata: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sourceIcon: {
    fontSize: 14,
  },
  confidenceDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  preferenceValue: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  preferenceFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  confidenceText: {
    fontSize: 12,
  },
  sourceText: {
    fontSize: 12,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 32,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 16,
    borderRadius: 16,
    marginTop: 24,
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
