/**
 * EventCard - Calendar event display
 * Shows event details with color coding and context
 */

import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '../../theme';
import { Text } from '../common';

export interface CalendarEvent {
  id: string;
  title: string;
  startTime: string; // HH:MM format
  endTime: string;
  duration: number; // in minutes
  location?: string;
  type?: 'meeting' | 'focus' | 'personal' | 'reminder';
  attendees?: string[];
  isHighPriority?: boolean;
  context?: string; // Alfred's context note
  color?: string;
}

interface EventCardProps {
  event: CalendarEvent;
  onPress?: () => void;
  isCompact?: boolean;
}

export function EventCard({ event, onPress, isCompact = false }: EventCardProps) {
  const { theme } = useTheme();

  const getEventColor = () => {
    if (event.color) return event.color;
    switch (event.type) {
      case 'meeting':
        return theme.colors.primary;
      case 'focus':
        return theme.colors.success;
      case 'personal':
        return theme.colors.info;
      case 'reminder':
        return theme.colors.warning;
      default:
        return theme.colors.primary;
    }
  };

  const getTypeIcon = () => {
    switch (event.type) {
      case 'meeting':
        return '🎥';
      case 'focus':
        return '🛡️';
      case 'personal':
        return '📌';
      case 'reminder':
        return '⏰';
      default:
        return '📅';
    }
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  const eventColor = getEventColor();

  if (isCompact) {
    return (
      <TouchableOpacity
        style={[
          styles.compactContainer,
          {
            backgroundColor: eventColor + '15',
            borderLeftColor: eventColor,
          },
        ]}
        onPress={onPress}
        activeOpacity={0.7}
      >
        <Text variant="bodySmall" style={{ fontWeight: '600' }} numberOfLines={1}>
          {event.title}
        </Text>
        <Text variant="caption" color="tertiary">
          {event.startTime}
        </Text>
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      style={[
        styles.container,
        {
          backgroundColor: event.isHighPriority
            ? eventColor
            : theme.colors.bgSurface,
          borderLeftColor: eventColor,
          borderLeftWidth: event.isHighPriority ? 0 : 3,
        },
      ]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {/* Time Badge */}
      <View style={styles.timeSection}>
        <Text
          style={[
            styles.startTime,
            { color: event.isHighPriority ? '#FFFFFF' : theme.colors.textPrimary },
          ]}
        >
          {event.startTime}
        </Text>
        <Text
          style={[
            styles.duration,
            {
              color: event.isHighPriority
                ? 'rgba(255,255,255,0.7)'
                : theme.colors.textTertiary,
            },
          ]}
        >
          {formatDuration(event.duration)}
        </Text>
      </View>

      {/* Content */}
      <View style={styles.content}>
        <View style={styles.header}>
          <Text
            variant="body"
            style={[
              styles.title,
              { color: event.isHighPriority ? '#FFFFFF' : theme.colors.textPrimary },
            ]}
            numberOfLines={1}
          >
            {event.title}
          </Text>
          {event.isHighPriority && (
            <View style={styles.priorityBadge}>
              <Text style={styles.priorityIcon}>◆</Text>
            </View>
          )}
        </View>

        {/* Location or Type */}
        <View style={styles.metaRow}>
          <Text style={styles.typeIcon}>{getTypeIcon()}</Text>
          <Text
            variant="bodySmall"
            style={{
              color: event.isHighPriority
                ? 'rgba(255,255,255,0.8)'
                : theme.colors.textSecondary,
            }}
            numberOfLines={1}
          >
            {event.location || (event.type === 'focus' ? 'Focus Time (Protected)' : event.type)}
          </Text>
        </View>

        {/* Attendees */}
        {event.attendees && event.attendees.length > 0 && (
          <View style={styles.attendeesRow}>
            {event.attendees.slice(0, 3).map((_, index) => (
              <View
                key={index}
                style={[
                  styles.attendeeAvatar,
                  {
                    backgroundColor: event.isHighPriority
                      ? 'rgba(255,255,255,0.3)'
                      : theme.colors.bgHover,
                    marginLeft: index > 0 ? -8 : 0,
                  },
                ]}
              />
            ))}
            {event.attendees.length > 3 && (
              <Text
                variant="caption"
                style={{
                  marginLeft: 4,
                  color: event.isHighPriority
                    ? 'rgba(255,255,255,0.7)'
                    : theme.colors.textTertiary,
                }}
              >
                +{event.attendees.length - 3}
              </Text>
            )}
          </View>
        )}

        {/* Context from Alfred */}
        {event.context && (
          <View
            style={[
              styles.contextBox,
              {
                backgroundColor: event.isHighPriority
                  ? 'rgba(255,255,255,0.15)'
                  : theme.colors.bgHover,
              },
            ]}
          >
            <Text
              variant="bodySmall"
              style={{
                color: event.isHighPriority
                  ? 'rgba(255,255,255,0.9)'
                  : theme.colors.textSecondary,
                fontStyle: 'italic',
              }}
              numberOfLines={2}
            >
              "{event.context}"
            </Text>
          </View>
        )}

        {/* Action button for high priority */}
        {event.isHighPriority && event.type === 'meeting' && (
          <TouchableOpacity style={styles.prepButton}>
            <Text style={styles.prepButtonText}>Prep Now</Text>
            <Text style={styles.prepButtonHint}>30min before</Text>
          </TouchableOpacity>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  compactContainer: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    marginBottom: 6,
  },
  timeSection: {
    width: 50,
    marginRight: 12,
  },
  startTime: {
    fontSize: 14,
    fontWeight: '700',
  },
  duration: {
    fontSize: 11,
    marginTop: 2,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  title: {
    flex: 1,
    fontWeight: '600',
  },
  priorityBadge: {
    marginLeft: 8,
  },
  priorityIcon: {
    color: '#FFFFFF',
    fontSize: 10,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  typeIcon: {
    fontSize: 12,
    marginRight: 6,
  },
  attendeesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  attendeeAvatar: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  contextBox: {
    marginTop: 8,
    padding: 10,
    borderRadius: 8,
  },
  prepButton: {
    marginTop: 12,
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  prepButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  prepButtonHint: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 12,
  },
});

export default EventCard;
