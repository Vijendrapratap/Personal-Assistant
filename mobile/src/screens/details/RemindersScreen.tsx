/**
 * RemindersScreen - Reminders/Notifications management
 * Shows active and historical reminders with quick actions
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../theme';
import { Text, Card } from '../../components/common';

interface RemindersScreenProps {
  navigation: any;
}

interface Reminder {
  id: string;
  title: string;
  description?: string;
  time: string;
  date: string;
  type: 'meeting' | 'task' | 'habit' | 'custom';
  isCompleted: boolean;
  priority?: 'high' | 'medium' | 'low';
}

// Mock data - will be replaced with API
const MOCK_REMINDERS: Reminder[] = [
  {
    id: '1',
    title: 'Meeting with Sarah',
    description: 'Discuss Q1 strategy',
    time: '2:00 PM',
    date: 'Today',
    type: 'meeting',
    isCompleted: false,
    priority: 'high',
  },
  {
    id: '2',
    title: 'Drink Water',
    description: 'Stay hydrated',
    time: '3:00 PM',
    date: 'Today',
    type: 'habit',
    isCompleted: false,
  },
  {
    id: '3',
    title: 'Review Q3 Reports',
    description: 'Financial review',
    time: '4:30 PM',
    date: 'Today',
    type: 'task',
    isCompleted: false,
    priority: 'medium',
  },
  {
    id: '4',
    title: 'Flight Check-in',
    description: 'SFO to NYC',
    time: '8:00 AM',
    date: 'Tomorrow',
    type: 'custom',
    isCompleted: false,
    priority: 'high',
  },
];

const MOCK_HISTORY: Reminder[] = [
  {
    id: '5',
    title: 'Team standup',
    time: '9:30 AM',
    date: 'Yesterday',
    type: 'meeting',
    isCompleted: true,
  },
  {
    id: '6',
    title: 'Submit expense report',
    time: '11:00 AM',
    date: 'Yesterday',
    type: 'task',
    isCompleted: true,
  },
  {
    id: '7',
    title: 'Call back investor',
    time: '2:00 PM',
    date: '2 days ago',
    type: 'custom',
    isCompleted: true,
  },
];

const getTypeIcon = (type: Reminder['type']) => {
  switch (type) {
    case 'meeting':
      return '📅';
    case 'task':
      return '✓';
    case 'habit':
      return '💧';
    case 'custom':
      return '🔔';
    default:
      return '📌';
  }
};

const getPriorityColor = (priority: Reminder['priority'], theme: any) => {
  switch (priority) {
    case 'high':
      return theme.colors.danger;
    case 'medium':
      return theme.colors.warning;
    case 'low':
      return theme.colors.info;
    default:
      return theme.colors.textTertiary;
  }
};

export default function RemindersScreen({ navigation }: RemindersScreenProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [activeTab, setActiveTab] = useState<'active' | 'history'>('active');
  const [reminders, setReminders] = useState<Reminder[]>(MOCK_REMINDERS);
  const [history, setHistory] = useState<Reminder[]>(MOCK_HISTORY);
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    // Simulate API call
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  }, []);

  const handleComplete = (reminder: Reminder) => {
    setReminders((prev) => prev.filter((r) => r.id !== reminder.id));
    setHistory((prev) => [{ ...reminder, isCompleted: true }, ...prev]);
  };

  const handleDelete = (reminder: Reminder) => {
    Alert.alert(
      'Delete Reminder',
      `Are you sure you want to delete "${reminder.title}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            if (activeTab === 'active') {
              setReminders((prev) => prev.filter((r) => r.id !== reminder.id));
            } else {
              setHistory((prev) => prev.filter((r) => r.id !== reminder.id));
            }
          },
        },
      ]
    );
  };

  const handleSnooze = (reminder: Reminder) => {
    Alert.alert('Snooze', 'Reminder snoozed for 15 minutes');
  };

  const groupByDate = (items: Reminder[]) => {
    const groups: { [key: string]: Reminder[] } = {};
    items.forEach((item) => {
      if (!groups[item.date]) {
        groups[item.date] = [];
      }
      groups[item.date].push(item);
    });
    return groups;
  };

  const currentData = activeTab === 'active' ? reminders : history;
  const groupedData = groupByDate(currentData);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.bg }]} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={[styles.backIcon, { color: theme.colors.textPrimary }]}>‹</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerIcon}>🔔</Text>
          <Text style={[styles.headerTitle, { color: theme.colors.textPrimary }]}>
            Reminders
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.settingsButton, { backgroundColor: theme.colors.bgSurface }]}
          onPress={() => navigation.navigate('NotificationSettings')}
        >
          <Text style={{ fontSize: 16 }}>⚙️</Text>
        </TouchableOpacity>
      </View>

      {/* Tabs */}
      <View style={styles.tabsContainer}>
        <TouchableOpacity
          style={[
            styles.tab,
            activeTab === 'active' && { backgroundColor: theme.colors.primary },
            activeTab !== 'active' && { backgroundColor: 'transparent' },
          ]}
          onPress={() => setActiveTab('active')}
        >
          <Text
            style={[
              styles.tabText,
              { color: activeTab === 'active' ? '#FFFFFF' : theme.colors.textSecondary },
            ]}
          >
            Active
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.tab,
            activeTab === 'history' && { backgroundColor: theme.colors.primary },
            activeTab !== 'history' && { backgroundColor: 'transparent' },
          ]}
          onPress={() => setActiveTab('history')}
        >
          <Text
            style={[
              styles.tabText,
              { color: activeTab === 'history' ? '#FFFFFF' : theme.colors.textSecondary },
            ]}
          >
            History
          </Text>
        </TouchableOpacity>
      </View>

      {/* Reminders List */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.listContent, { paddingBottom: insets.bottom + 100 }]}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.colors.primary}
          />
        }
      >
        {Object.entries(groupedData).map(([date, items]) => (
          <View key={date} style={styles.dateGroup}>
            <Text style={[styles.dateLabel, { color: theme.colors.textSecondary }]}>
              {date.toUpperCase()}
            </Text>
            {items.map((reminder) => (
              <TouchableOpacity
                key={reminder.id}
                style={[styles.reminderCard, { backgroundColor: theme.colors.bgSurface }]}
                onLongPress={() => handleDelete(reminder)}
              >
                <View style={styles.reminderLeft}>
                  <View
                    style={[
                      styles.reminderCheckbox,
                      {
                        borderColor: reminder.isCompleted
                          ? theme.colors.success
                          : getPriorityColor(reminder.priority, theme),
                        backgroundColor: reminder.isCompleted
                          ? theme.colors.success + '20'
                          : 'transparent',
                      },
                    ]}
                  >
                    {reminder.isCompleted ? (
                      <Text style={{ color: theme.colors.success, fontSize: 12 }}>✓</Text>
                    ) : (
                      <Text style={{ fontSize: 14 }}>{getTypeIcon(reminder.type)}</Text>
                    )}
                  </View>
                  <View style={styles.reminderContent}>
                    <Text
                      style={[
                        styles.reminderTitle,
                        { color: theme.colors.textPrimary },
                        reminder.isCompleted && styles.completedText,
                      ]}
                    >
                      {reminder.title}
                    </Text>
                    {reminder.description && (
                      <Text
                        style={[styles.reminderDescription, { color: theme.colors.textSecondary }]}
                      >
                        {reminder.description}
                      </Text>
                    )}
                    <Text style={[styles.reminderTime, { color: theme.colors.textTertiary }]}>
                      {reminder.time}
                    </Text>
                  </View>
                </View>
                {activeTab === 'active' && (
                  <View style={styles.reminderActions}>
                    <TouchableOpacity
                      style={[styles.actionButton, { backgroundColor: theme.colors.bgHover }]}
                      onPress={() => handleSnooze(reminder)}
                    >
                      <Text style={{ fontSize: 14 }}>⏰</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.actionButton, { backgroundColor: theme.colors.success + '20' }]}
                      onPress={() => handleComplete(reminder)}
                    >
                      <Text style={{ fontSize: 14, color: theme.colors.success }}>✓</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </TouchableOpacity>
            ))}
          </View>
        ))}

        {currentData.length === 0 && (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>{activeTab === 'active' ? '🎉' : '📭'}</Text>
            <Text style={[styles.emptyTitle, { color: theme.colors.textPrimary }]}>
              {activeTab === 'active' ? 'All caught up!' : 'No history yet'}
            </Text>
            <Text style={[styles.emptyDescription, { color: theme.colors.textSecondary }]}>
              {activeTab === 'active'
                ? 'You have no pending reminders'
                : 'Completed reminders will appear here'}
            </Text>
          </View>
        )}
      </ScrollView>

      {/* Add Reminder FAB */}
      {activeTab === 'active' && (
        <TouchableOpacity
          style={[styles.fab, { backgroundColor: theme.colors.primary }]}
          onPress={() => navigation.navigate('CreateReminder')}
        >
          <Text style={styles.fabIcon}>+</Text>
        </TouchableOpacity>
      )}
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
  headerCenter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerIcon: {
    fontSize: 20,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  settingsButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tabsContainer: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginVertical: 12,
    padding: 4,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
  },
  tabText: {
    fontSize: 15,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  listContent: {
    paddingHorizontal: 20,
  },
  dateGroup: {
    marginBottom: 24,
  },
  dateLabel: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
    marginLeft: 4,
  },
  reminderCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 14,
    marginBottom: 10,
  },
  reminderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  reminderCheckbox: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  reminderContent: {
    flex: 1,
  },
  reminderTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  completedText: {
    textDecorationLine: 'line-through',
    opacity: 0.6,
  },
  reminderDescription: {
    fontSize: 13,
    marginBottom: 4,
  },
  reminderTime: {
    fontSize: 12,
  },
  reminderActions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
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
  emptyDescription: {
    fontSize: 14,
    textAlign: 'center',
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 100,
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  fabIcon: {
    fontSize: 28,
    color: '#FFFFFF',
    fontWeight: '300',
  },
});
