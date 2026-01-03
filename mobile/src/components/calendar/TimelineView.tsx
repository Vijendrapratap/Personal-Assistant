/**
 * TimelineView - Vertical calendar timeline
 * Shows events in a time-based vertical layout with now indicator
 */

import React, { useRef, useEffect } from 'react';
import { View, ScrollView, StyleSheet, Dimensions } from 'react-native';
import { useTheme } from '../../theme';
import { Text } from '../common';
import { EventCard, CalendarEvent } from './EventCard';

interface TimelineViewProps {
  events: CalendarEvent[];
  selectedDate: Date;
  onEventPress?: (event: CalendarEvent) => void;
  startHour?: number;
  endHour?: number;
}

const HOUR_HEIGHT = 80;
const TIME_COLUMN_WIDTH = 50;

export function TimelineView({
  events,
  selectedDate,
  onEventPress,
  startHour = 6,
  endHour = 22,
}: TimelineViewProps) {
  const { theme } = useTheme();
  const scrollRef = useRef<ScrollView>(null);

  const isToday = () => {
    const today = new Date();
    return (
      selectedDate.getDate() === today.getDate() &&
      selectedDate.getMonth() === today.getMonth() &&
      selectedDate.getFullYear() === today.getFullYear()
    );
  };

  const getCurrentTimePosition = () => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const totalMinutes = (hours - startHour) * 60 + minutes;
    return (totalMinutes / 60) * HOUR_HEIGHT;
  };

  const getEventPosition = (event: CalendarEvent) => {
    const [hours, minutes] = event.startTime.split(':').map(Number);
    const totalMinutes = (hours - startHour) * 60 + minutes;
    return (totalMinutes / 60) * HOUR_HEIGHT;
  };

  const getEventHeight = (event: CalendarEvent) => {
    return (event.duration / 60) * HOUR_HEIGHT;
  };

  // Sort events by start time
  const sortedEvents = [...events].sort((a, b) => {
    const aTime = a.startTime.split(':').map(Number);
    const bTime = b.startTime.split(':').map(Number);
    return aTime[0] * 60 + aTime[1] - (bTime[0] * 60 + bTime[1]);
  });

  // Generate hour labels
  const hours = Array.from({ length: endHour - startHour + 1 }, (_, i) => startHour + i);

  // Format hour label
  const formatHour = (hour: number) => {
    if (hour === 0) return '12 AM';
    if (hour === 12) return '12 PM';
    if (hour < 12) return `${hour} AM`;
    return `${hour - 12} PM`;
  };

  // Scroll to current time on mount
  useEffect(() => {
    if (isToday() && scrollRef.current) {
      const position = getCurrentTimePosition() - 100;
      setTimeout(() => {
        scrollRef.current?.scrollTo({ y: Math.max(0, position), animated: false });
      }, 100);
    }
  }, [selectedDate]);

  const currentTimePosition = getCurrentTimePosition();
  const showNowIndicator = isToday() && currentTimePosition >= 0 && currentTimePosition <= (endHour - startHour) * HOUR_HEIGHT;

  return (
    <ScrollView
      ref={scrollRef}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.scrollContent}
    >
      <View style={styles.timeline}>
        {/* Hour lines and labels */}
        {hours.map((hour, index) => (
          <View key={hour} style={[styles.hourRow, { height: HOUR_HEIGHT }]}>
            <View style={[styles.hourLabel, { width: TIME_COLUMN_WIDTH }]}>
              <Text
                style={[styles.hourText, { color: theme.colors.textTertiary }]}
              >
                {formatHour(hour)}
              </Text>
            </View>
            <View
              style={[
                styles.hourLine,
                { backgroundColor: theme.colors.border },
              ]}
            />
          </View>
        ))}

        {/* Events */}
        <View style={[styles.eventsContainer, { left: TIME_COLUMN_WIDTH + 8 }]}>
          {sortedEvents.map((event) => {
            const top = getEventPosition(event);
            const height = getEventHeight(event);
            const isValidPosition = top >= 0 && top < (endHour - startHour) * HOUR_HEIGHT;

            if (!isValidPosition) return null;

            return (
              <View
                key={event.id}
                style={[
                  styles.eventWrapper,
                  {
                    top,
                    height: Math.max(height, 50), // Minimum height
                  },
                ]}
              >
                <EventCard
                  event={event}
                  onPress={() => onEventPress?.(event)}
                />
              </View>
            );
          })}
        </View>

        {/* Now Indicator */}
        {showNowIndicator && (
          <View
            style={[
              styles.nowIndicator,
              {
                top: currentTimePosition,
                left: TIME_COLUMN_WIDTH - 6,
              },
            ]}
          >
            <View
              style={[styles.nowDot, { backgroundColor: theme.colors.danger }]}
            />
            <View
              style={[styles.nowLine, { backgroundColor: theme.colors.danger }]}
            />
            <View style={styles.nowTimeContainer}>
              <Text
                style={[styles.nowTime, { color: theme.colors.danger }]}
              >
                {new Date().toLocaleTimeString('en-US', {
                  hour: 'numeric',
                  minute: '2-digit',
                  hour12: true,
                })}
              </Text>
            </View>
          </View>
        )}
      </View>

      {/* Empty state */}
      {events.length === 0 && (
        <View style={styles.emptyState}>
          <Text variant="body" color="tertiary" style={styles.emptyText}>
            No events scheduled for this day
          </Text>
          <Text variant="bodySmall" color="tertiary">
            Use the input below to add an event
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  timeline: {
    position: 'relative',
    minHeight: 16 * HOUR_HEIGHT,
  },
  hourRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  hourLabel: {
    paddingRight: 8,
    alignItems: 'flex-end',
  },
  hourText: {
    fontSize: 11,
    fontWeight: '500',
    marginTop: -6,
  },
  hourLine: {
    flex: 1,
    height: 1,
  },
  eventsContainer: {
    position: 'absolute',
    top: 0,
    right: 16,
  },
  eventWrapper: {
    position: 'absolute',
    left: 0,
    right: 0,
  },
  nowIndicator: {
    position: 'absolute',
    flexDirection: 'row',
    alignItems: 'center',
    right: 0,
    zIndex: 100,
  },
  nowDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  nowLine: {
    flex: 1,
    height: 2,
    marginLeft: -1,
  },
  nowTimeContainer: {
    position: 'absolute',
    left: -45,
    backgroundColor: 'transparent',
  },
  nowTime: {
    fontSize: 10,
    fontWeight: '700',
  },
  emptyState: {
    position: 'absolute',
    top: '30%',
    left: 0,
    right: 0,
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyText: {
    textAlign: 'center',
    marginBottom: 8,
  },
});

export default TimelineView;
