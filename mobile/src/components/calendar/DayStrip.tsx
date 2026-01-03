/**
 * DayStrip - Horizontal scrollable date selector
 * Shows a week of dates with the selected day highlighted
 */

import React, { useRef, useEffect } from 'react';
import {
  View,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { useTheme } from '../../theme';
import { Text } from '../common';

interface DayStripProps {
  selectedDate: Date;
  onDateSelect: (date: Date) => void;
  events?: Record<string, number>; // date string -> event count
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DAY_WIDTH = 56;

export function DayStrip({ selectedDate, onDateSelect, events = {} }: DayStripProps) {
  const { theme } = useTheme();
  const scrollRef = useRef<ScrollView>(null);

  // Generate 14 days (7 before and 7 after today)
  const generateDays = () => {
    const days: Date[] = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let i = -7; i <= 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      days.push(date);
    }
    return days;
  };

  const days = generateDays();

  const isToday = (date: Date) => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const isSelected = (date: Date) => {
    return (
      date.getDate() === selectedDate.getDate() &&
      date.getMonth() === selectedDate.getMonth() &&
      date.getFullYear() === selectedDate.getFullYear()
    );
  };

  const getDateKey = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  const getEventCount = (date: Date) => {
    return events[getDateKey(date)] || 0;
  };

  // Scroll to selected date on mount
  useEffect(() => {
    const selectedIndex = days.findIndex((d) => isSelected(d));
    if (selectedIndex >= 0 && scrollRef.current) {
      const screenWidth = Dimensions.get('window').width;
      const scrollPosition = selectedIndex * DAY_WIDTH - screenWidth / 2 + DAY_WIDTH / 2;
      setTimeout(() => {
        scrollRef.current?.scrollTo({ x: Math.max(0, scrollPosition), animated: false });
      }, 100);
    }
  }, []);

  return (
    <View style={styles.container}>
      <ScrollView
        ref={scrollRef}
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {days.map((date, index) => {
          const selected = isSelected(date);
          const today = isToday(date);
          const eventCount = getEventCount(date);

          return (
            <TouchableOpacity
              key={index}
              style={[
                styles.dayItem,
                selected && {
                  backgroundColor: theme.colors.primary,
                  ...theme.shadows.glow,
                },
              ]}
              onPress={() => onDateSelect(date)}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.dayName,
                  {
                    color: selected
                      ? 'rgba(255,255,255,0.8)'
                      : today
                      ? theme.colors.primary
                      : theme.colors.textTertiary,
                  },
                ]}
              >
                {DAYS[date.getDay()]}
              </Text>
              <Text
                style={[
                  styles.dayNumber,
                  {
                    color: selected
                      ? '#FFFFFF'
                      : today
                      ? theme.colors.primary
                      : theme.colors.textPrimary,
                  },
                ]}
              >
                {date.getDate()}
              </Text>
              {eventCount > 0 && (
                <View
                  style={[
                    styles.eventDots,
                    { backgroundColor: selected ? 'rgba(255,255,255,0.3)' : theme.colors.bgHover },
                  ]}
                >
                  {Array.from({ length: Math.min(eventCount, 3) }).map((_, i) => (
                    <View
                      key={i}
                      style={[
                        styles.eventDot,
                        {
                          backgroundColor: selected
                            ? '#FFFFFF'
                            : theme.colors.primary,
                        },
                      ]}
                    />
                  ))}
                </View>
              )}
              {today && !selected && (
                <View
                  style={[styles.todayIndicator, { backgroundColor: theme.colors.primary }]}
                />
              )}
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: 88,
  },
  scrollContent: {
    paddingHorizontal: 12,
    alignItems: 'center',
  },
  dayItem: {
    width: DAY_WIDTH,
    height: 76,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
    marginHorizontal: 4,
  },
  dayName: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  dayNumber: {
    fontSize: 20,
    fontWeight: '700',
  },
  eventDots: {
    flexDirection: 'row',
    marginTop: 6,
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 10,
    gap: 3,
  },
  eventDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  todayIndicator: {
    position: 'absolute',
    bottom: 8,
    width: 4,
    height: 4,
    borderRadius: 2,
  },
});

export default DayStrip;
