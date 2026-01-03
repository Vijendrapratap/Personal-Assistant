import React from 'react';
import {
  TouchableOpacity,
  View,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { useTheme } from '../../theme';
import { Text } from './Text';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  style?: ViewStyle;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  style,
}: ButtonProps) {
  const { theme } = useTheme();

  const getVariantStyle = (): { container: ViewStyle; text: TextStyle } => {
    const isDisabled = disabled || loading;

    switch (variant) {
      case 'secondary':
        return {
          container: {
            backgroundColor: isDisabled
              ? theme.colors.bgHover
              : theme.colors.bgSurface,
            borderWidth: 1,
            borderColor: theme.colors.border,
          },
          text: {
            color: isDisabled
              ? theme.colors.textDisabled
              : theme.colors.textPrimary,
          },
        };
      case 'ghost':
        return {
          container: {
            backgroundColor: 'transparent',
          },
          text: {
            color: isDisabled ? theme.colors.textDisabled : theme.colors.primary,
          },
        };
      case 'danger':
        return {
          container: {
            backgroundColor: isDisabled
              ? theme.colors.dangerSoft
              : theme.colors.danger,
          },
          text: {
            color: isDisabled ? theme.colors.danger : theme.colors.white,
          },
        };
      default: // primary
        return {
          container: {
            backgroundColor: isDisabled
              ? theme.colors.primarySoft
              : theme.colors.primary,
            ...(!isDisabled && theme.shadows.glow),
          },
          text: {
            color: isDisabled ? theme.colors.primary : theme.colors.white,
          },
        };
    }
  };

  const getSizeStyle = (): { container: ViewStyle; text: TextStyle } => {
    switch (size) {
      case 'sm':
        return {
          container: {
            height: theme.componentSize.button.sm,
            paddingHorizontal: theme.spacing[3],
            borderRadius: theme.radius.DEFAULT,
          },
          text: {
            fontSize: theme.typography.size.sm,
          },
        };
      case 'lg':
        return {
          container: {
            height: theme.componentSize.button.lg,
            paddingHorizontal: theme.spacing[6],
            borderRadius: theme.radius.lg,
          },
          text: {
            fontSize: theme.typography.size.lg,
          },
        };
      default: // md
        return {
          container: {
            height: theme.componentSize.button.md,
            paddingHorizontal: theme.spacing[5],
            borderRadius: theme.radius.md,
          },
          text: {
            fontSize: theme.typography.size.base,
          },
        };
    }
  };

  const variantStyle = getVariantStyle();
  const sizeStyle = getSizeStyle();

  const containerStyle: ViewStyle = {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    ...sizeStyle.container,
    ...variantStyle.container,
    ...(fullWidth && { width: '100%' }),
    ...(style as object),
  };

  const textStyle: TextStyle = {
    fontWeight: theme.typography.weight.semibold,
    ...sizeStyle.text,
    ...variantStyle.text,
  };

  const renderContent = () => {
    if (loading) {
      return (
        <ActivityIndicator
          size="small"
          color={variantStyle.text.color as string}
        />
      );
    }

    return (
      <>
        {icon && iconPosition === 'left' && (
          <View style={{ marginRight: theme.spacing[2] }}>{icon}</View>
        )}
        <Text style={textStyle}>{title}</Text>
        {icon && iconPosition === 'right' && (
          <View style={{ marginLeft: theme.spacing[2] }}>{icon}</View>
        )}
      </>
    );
  };

  return (
    <TouchableOpacity
      style={containerStyle}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {renderContent()}
    </TouchableOpacity>
  );
}

export default Button;
