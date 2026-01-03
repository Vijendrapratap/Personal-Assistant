import React from 'react';
import { Text as RNText, TextStyle, TextProps as RNTextProps } from 'react-native';
import { useTheme } from '../../theme';

type TextVariant =
  | 'h1'
  | 'h2'
  | 'h3'
  | 'h4'
  | 'body'
  | 'bodySmall'
  | 'caption'
  | 'label'
  | 'button';

type TextColor =
  | 'primary'
  | 'secondary'
  | 'tertiary'
  | 'disabled'
  | 'accent'
  | 'success'
  | 'warning'
  | 'danger'
  | 'white';

interface TextProps extends RNTextProps {
  variant?: TextVariant;
  color?: TextColor;
  weight?: 'normal' | 'medium' | 'semibold' | 'bold' | 'extrabold';
  align?: 'left' | 'center' | 'right';
  children: React.ReactNode;
}

export function Text({
  variant = 'body',
  color = 'primary',
  weight,
  align,
  style,
  children,
  ...props
}: TextProps) {
  const { theme } = useTheme();

  const getVariantStyle = (): TextStyle => {
    switch (variant) {
      case 'h1':
        return {
          fontSize: theme.typography.size['3xl'],
          fontWeight: theme.typography.weight.extrabold,
          lineHeight: theme.typography.size['3xl'] * theme.typography.lineHeight.tight,
          letterSpacing: theme.typography.letterSpacing.tight,
        };
      case 'h2':
        return {
          fontSize: theme.typography.size['2xl'],
          fontWeight: theme.typography.weight.bold,
          lineHeight: theme.typography.size['2xl'] * theme.typography.lineHeight.tight,
        };
      case 'h3':
        return {
          fontSize: theme.typography.size.xl,
          fontWeight: theme.typography.weight.bold,
          lineHeight: theme.typography.size.xl * theme.typography.lineHeight.tight,
        };
      case 'h4':
        return {
          fontSize: theme.typography.size.lg,
          fontWeight: theme.typography.weight.semibold,
          lineHeight: theme.typography.size.lg * theme.typography.lineHeight.normal,
        };
      case 'bodySmall':
        return {
          fontSize: theme.typography.size.sm,
          fontWeight: theme.typography.weight.normal,
          lineHeight: theme.typography.size.sm * theme.typography.lineHeight.normal,
        };
      case 'caption':
        return {
          fontSize: theme.typography.size.xs,
          fontWeight: theme.typography.weight.medium,
          lineHeight: theme.typography.size.xs * theme.typography.lineHeight.normal,
          letterSpacing: theme.typography.letterSpacing.wide,
        };
      case 'label':
        return {
          fontSize: theme.typography.size.xs,
          fontWeight: theme.typography.weight.bold,
          lineHeight: theme.typography.size.xs * theme.typography.lineHeight.normal,
          letterSpacing: theme.typography.letterSpacing.wider,
          textTransform: 'uppercase',
        };
      case 'button':
        return {
          fontSize: theme.typography.size.base,
          fontWeight: theme.typography.weight.semibold,
          lineHeight: theme.typography.size.base * theme.typography.lineHeight.normal,
        };
      default: // body
        return {
          fontSize: theme.typography.size.base,
          fontWeight: theme.typography.weight.normal,
          lineHeight: theme.typography.size.base * theme.typography.lineHeight.normal,
        };
    }
  };

  const getColorStyle = (): TextStyle => {
    switch (color) {
      case 'secondary':
        return { color: theme.colors.textSecondary };
      case 'tertiary':
        return { color: theme.colors.textTertiary };
      case 'disabled':
        return { color: theme.colors.textDisabled };
      case 'accent':
        return { color: theme.colors.primary };
      case 'success':
        return { color: theme.colors.success };
      case 'warning':
        return { color: theme.colors.warning };
      case 'danger':
        return { color: theme.colors.danger };
      case 'white':
        return { color: theme.colors.white };
      default:
        return { color: theme.colors.textPrimary };
    }
  };

  const textStyle: TextStyle = {
    fontFamily: theme.typography.fontFamily.display,
    ...getVariantStyle(),
    ...getColorStyle(),
    ...(weight && { fontWeight: theme.typography.weight[weight] }),
    ...(align && { textAlign: align }),
    ...(style as object),
  };

  return (
    <RNText style={textStyle} {...props}>
      {children}
    </RNText>
  );
}

export default Text;
