import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { useTheme } from '../../theme';
import { Text } from '../common/Text';
import { Card } from '../common/Card';

type CardType = 'warning' | 'insight' | 'reminder' | 'celebration';

interface ProactiveCardProps {
  type: CardType;
  title: string;
  description: string;
  actions?: Array<{
    label: string;
    onPress: () => void;
    variant?: 'primary' | 'secondary';
  }>;
  onDismiss?: () => void;
  icon?: string; // Emoji or icon name
}

/**
 * ProactiveCard - Alfred's suggestion cards
 *
 * Types:
 * - warning: Projects needing attention, overdue tasks
 * - insight: Pattern detection, suggestions
 * - reminder: Upcoming events, follow-ups
 * - celebration: Achievements, streak milestones
 */
export function ProactiveCard({
  type,
  title,
  description,
  actions = [],
  onDismiss,
  icon,
}: ProactiveCardProps) {
  const { theme } = useTheme();

  const getTypeConfig = () => {
    switch (type) {
      case 'warning':
        return {
          color: theme.colors.warning,
          bgColor: theme.colors.warningSoft,
          defaultIcon: '',
        };
      case 'insight':
        return {
          color: theme.colors.info,
          bgColor: theme.colors.infoSoft,
          defaultIcon: '',
        };
      case 'reminder':
        return {
          color: theme.colors.primary,
          bgColor: theme.colors.primarySoft,
          defaultIcon: '',
        };
      case 'celebration':
        return {
          color: theme.colors.success,
          bgColor: theme.colors.successSoft,
          defaultIcon: '',
        };
    }
  };

  const config = getTypeConfig();
  const displayIcon = icon || config.defaultIcon;

  return (
    <Card style={styles.container} variant="elevated">
      {/* Header with icon and dismiss */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View
            style={[
              styles.iconContainer,
              {
                backgroundColor:
                  theme.mode === 'dark'
                    ? `${config.color}20`
                    : config.bgColor,
              },
            ]}
          >
            <Text style={[styles.icon, { fontSize: 16 }]}>{displayIcon}</Text>
          </View>
          <Text variant="label" color="secondary" style={styles.typeLabel}>
            Alfred noticed
          </Text>
        </View>
        {onDismiss && (
          <TouchableOpacity
            onPress={onDismiss}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text color="tertiary" style={styles.dismissIcon}>

            </Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Content */}
      <View style={styles.content}>
        <Text variant="h4" style={styles.title}>
          {title}
        </Text>
        <Text variant="bodySmall" color="secondary" style={styles.description}>
          {description}
        </Text>
      </View>

      {/* Actions */}
      {actions.length > 0 && (
        <View style={styles.actions}>
          {actions.map((action, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.actionButton,
                action.variant === 'primary'
                  ? {
                      backgroundColor: theme.colors.primary,
                    }
                  : {
                      backgroundColor: theme.colors.bgHover,
                    },
              ]}
              onPress={action.onPress}
            >
              <Text
                variant="button"
                style={{
                  color:
                    action.variant === 'primary'
                      ? theme.colors.white
                      : theme.colors.textPrimary,
                  fontSize: theme.typography.size.sm,
                }}
              >
                {action.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 12,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  iconContainer: {
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    textAlign: 'center',
  },
  typeLabel: {
    fontSize: 11,
  },
  dismissIcon: {
    fontSize: 18,
    opacity: 0.5,
  },
  content: {
    marginBottom: 12,
  },
  title: {
    marginBottom: 4,
  },
  description: {
    lineHeight: 20,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap',
  },
  actionButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
  },
});

export default ProactiveCard;
