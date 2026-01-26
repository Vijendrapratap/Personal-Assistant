/**
 * FocusScreen - Calendar + Voice Interface
 * Shows daily schedule with timeline view and voice input
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  Alert,
  useWindowDimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../theme';
import { Text, Card } from '../../components/common';
import { DayStrip, TimelineView, CalendarEvent } from '../../components/calendar';
import { ConversationInput } from '../../components/input';

interface FocusScreenProps {
  navigation: any;
}

// Mock events for demo (will be replaced with API)
const generateMockEvents = (date: Date): CalendarEvent[] => {
  const isToday =
    date.getDate() === new Date().getDate() &&
    date.getMonth() === new Date().getMonth();

  const baseEvents: CalendarEvent[] = [
    {
      id: '1',
      title: 'Team Standup',
      startTime: '09:00',
      endTime: '09:30',
      duration: 30,
      type: 'meeting',
      location: 'Zoom',
      attendees: ['Alice', 'Bob', 'Carol', 'Dave', 'Eve'],
    },
    {
      id: '2',
      title: 'Focus Time',
      startTime: '10:00',
      endTime: '12:00',
      duration: 120,
      type: 'focus',
      context: 'Deep work block - Protected time',
    },
    {
      id: '3',
      title: 'Lunch Break',
      startTime: '12:30',
      endTime: '13:30',
      duration: 60,
      type: 'personal',
      location: 'Local Cafe',
    },
    {
      id: '4',
      title: 'Client Demo Call',
      startTime: '14:00',
      endTime: '15:00',
      duration: 60,
      type: 'meeting',
      location: 'Google Meet',
      attendees: ['Sarah', 'Mike'],
      isHighPriority: true,
      context: 'Contract discussion - they loved the last demo',
    },
    {
      id: '5',
      title: 'Review PRs',
      startTime: '16:00',
      endTime: '17:00',
      duration: 60,
      type: 'focus',
    },
    {
      id: '6',
      title: 'Gym',
      startTime: '18:00',
      endTime: '19:00',
      duration: 60,
      type: 'personal',
      location: 'Local Fitness',
    },
  ];

  // Return different events for different days
  if (isToday) {
    return baseEvents;
  }

  // Random subset for other days
  const shuffled = [...baseEvents].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, Math.floor(Math.random() * 4) + 1).map((e, i) => ({
    ...e,
    id: `${date.getTime()}-${i}`,
  }));
};

export default function FocusScreen({ navigation }: FocusScreenProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const { width: screenWidth } = useWindowDimensions();

  // Responsive values
  const horizontalPadding = Math.max(16, Math.min(20, screenWidth * 0.05));

  const [selectedDate, setSelectedDate] = useState(new Date());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [eventCounts, setEventCounts] = useState<Record<string, number>>({});

  const loadEvents = useCallback((date: Date) => {
    // TODO: Replace with actual API call
    const mockEvents = generateMockEvents(date);
    setEvents(mockEvents);
  }, []);

  const loadEventCounts = useCallback(() => {
    // Generate event counts for the week
    const counts: Record<string, number> = {};
    for (let i = -7; i <= 7; i++) {
      const d = new Date();
      d.setDate(d.getDate() + i);
      const key = d.toISOString().split('T')[0];
      counts[key] = Math.floor(Math.random() * 5) + 1;
    }
    setEventCounts(counts);
  }, []);

  useEffect(() => {
    loadEvents(selectedDate);
    loadEventCounts();
  }, [selectedDate]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadEvents(selectedDate);
    setTimeout(() => setRefreshing(false), 500);
  }, [selectedDate, loadEvents]);

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
    loadEvents(date);
  };

  const handleEventPress = (event: CalendarEvent) => {
    Alert.alert(
      event.title,
      `${event.startTime} - ${event.endTime}\n${event.location || ''}\n${event.context || ''}`,
      [
        { text: 'Edit', onPress: () => {} },
        { text: 'Delete', style: 'destructive', onPress: () => {} },
        { text: 'OK' },
      ]
    );
  };

  const handleConversationSubmit = async (message: string) => {
    // TODO: Integrate with AI to parse and create events
    Alert.alert(
      'Creating Event',
      `Alfred is processing: "${message}"`,
      [{ text: 'OK' }]
    );
  };

  const formatDateHeader = () => {
    const today = new Date();
    const isToday =
      selectedDate.getDate() === today.getDate() &&
      selectedDate.getMonth() === today.getMonth();
    const isTomorrow =
      selectedDate.getDate() === today.getDate() + 1 &&
      selectedDate.getMonth() === today.getMonth();

    if (isToday) return 'Today';
    if (isTomorrow) return 'Tomorrow';

    return selectedDate.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
    });
  };

  const getUpcomingEvent = () => {
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();

    const today = new Date();
    const isToday =
      selectedDate.getDate() === today.getDate() &&
      selectedDate.getMonth() === today.getMonth();

    if (!isToday) return null;

    return events.find((e) => {
      const [hours, minutes] = e.startTime.split(':').map(Number);
      const eventTime = hours * 60 + minutes;
      return eventTime > currentTime;
    });
  };

  const upcomingEvent = getUpcomingEvent();

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      {/* Header */}
      <View
        style={[
          styles.header,
          {
            paddingTop: insets.top + 12,
            paddingHorizontal: horizontalPadding,
            backgroundColor: theme.colors.bg,
          },
        ]}
      >
        <View style={styles.headerContent}>
          <Text variant="h2">Focus</Text>
          <Text variant="body" color="secondary">
            {formatDateHeader()}
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.todayButton, { backgroundColor: theme.colors.bgSurface }]}
          onPress={() => handleDateSelect(new Date())}
        >
          <Text variant="bodySmall" color="accent">
            Today
          </Text>
        </TouchableOpacity>
      </View>

      {/* Day Strip */}
      <View style={[styles.dayStripContainer, { borderBottomColor: theme.colors.border }]}>
        <DayStrip
          selectedDate={selectedDate}
          onDateSelect={handleDateSelect}
          events={eventCounts}
        />
      </View>

      {/* Up Next Card (if today) */}
      {upcomingEvent && (
        <View style={styles.upNextSection}>
          <Card
            variant="outlined"
            style={[styles.upNextCard, { borderColor: theme.colors.primary + '40' }]}
            onPress={() => handleEventPress(upcomingEvent)}
          >
            <View style={styles.upNextContent}>
              <View style={styles.upNextLeft}>
                <Text variant="caption" color="secondary">
                  UP NEXT
                </Text>
                <Text variant="body" style={{ fontWeight: '600', marginTop: 2 }}>
                  {upcomingEvent.title}
                </Text>
                <Text variant="bodySmall" color="tertiary">
                  {upcomingEvent.startTime}
                  {upcomingEvent.location && ` • ${upcomingEvent.location}`}
                </Text>
              </View>
              {upcomingEvent.type === 'meeting' && (
                <TouchableOpacity
                  style={[
                    styles.joinButton,
                    { backgroundColor: theme.colors.primary },
                  ]}
                >
                  <Text style={styles.joinButtonText}>Join</Text>
                </TouchableOpacity>
              )}
            </View>
          </Card>
        </View>
      )}

      {/* Timeline */}
      <View style={styles.timelineContainer}>
        <TimelineView
          events={events}
          selectedDate={selectedDate}
          onEventPress={handleEventPress}
        />
      </View>

      {/* Conversation Input */}
      <View
        style={[
          styles.inputContainer,
          {
            backgroundColor: theme.colors.bg,
            paddingBottom: insets.bottom + 16,
            paddingHorizontal: horizontalPadding,
            borderTopColor: theme.colors.border,
          },
        ]}
      >
        <ConversationInput
          placeholder="Schedule something..."
          onSubmit={handleConversationSubmit}
          onVoicePress={() => navigation.navigate('Voice')}
          suggestions={['Add meeting', 'Block focus time', 'Set reminder']}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingBottom: 12,
  },
  headerContent: {},
  todayButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  dayStripContainer: {
    borderBottomWidth: 1,
    paddingBottom: 12,
  },
  upNextSection: {
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  upNextCard: {
    backgroundColor: 'transparent',
  },
  upNextContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  upNextLeft: {
    flex: 1,
  },
  joinButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  joinButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  timelineContainer: {
    flex: 1,
    paddingHorizontal: 8,
    marginTop: 8,
    marginBottom: 80, // Space for input container
  },
  inputContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingTop: 12,
    borderTopWidth: 1,
  },
});
