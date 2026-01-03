import React from 'react';
import {
  View,
  StyleSheet,
  ViewStyle,
  TouchableOpacity,
  TouchableOpacityProps,
} from 'react-native';
import { useTheme } from '../../theme';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'default' | 'elevated' | 'outlined' | 'primary';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  onPress?: () => void;
  disabled?: boolean;
}

export function Card({
  children,
  style,
  variant = 'default',
  padding = 'md',
  onPress,
  disabled = false,
}: CardProps) {
  const { theme } = useTheme();

  const getVariantStyle = (): ViewStyle => {
    switch (variant) {
      case 'elevated':
        return {
          backgroundColor: theme.colors.bgElevated,
          ...theme.shadows.md,
        };
      case 'outlined':
        return {
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderColor: theme.colors.border,
        };
      case 'primary':
        return {
          backgroundColor: theme.colors.primary,
          ...theme.shadows.glow,
        };
      default:
        return {
          backgroundColor: theme.colors.bgSurface,
          ...theme.shadows.sm,
        };
    }
  };

  const getPaddingStyle = (): ViewStyle => {
    switch (padding) {
      case 'none':
        return { padding: 0 };
      case 'sm':
        return { padding: theme.spacing[3] };
      case 'lg':
        return { padding: theme.spacing[6] };
      default:
        return { padding: theme.spacing[4] };
    }
  };

  const cardStyle: ViewStyle = {
    borderRadius: theme.radius.lg,
    ...getVariantStyle(),
    ...getPaddingStyle(),
    ...(style as object),
  };

  if (onPress) {
    return (
      <TouchableOpacity
        style={cardStyle}
        onPress={onPress}
        disabled={disabled}
        activeOpacity={0.7}
      >
        {children}
      </TouchableOpacity>
    );
  }

  return <View style={cardStyle}>{children}</View>;
}

export default Card;
