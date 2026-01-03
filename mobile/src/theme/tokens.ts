/**
 * Alfred Design Tokens
 * Minimal, goal-oriented personal assistant design system
 */

// ============================================================================
// COLORS
// ============================================================================

export const colors = {
  // Primary - Alfred Blue
  primary: '#1337EC',
  primaryLight: '#3B5BFD',
  primaryDark: '#0D2494',
  primarySoft: '#E8EDFF',
  primaryGlow: 'rgba(19, 55, 236, 0.15)',

  // Semantic
  success: '#10B981',
  successSoft: '#D1FAE5',
  warning: '#F59E0B',
  warningSoft: '#FEF3C7',
  danger: '#EF4444',
  dangerSoft: '#FEE2E2',
  info: '#6366F1',
  infoSoft: '#E0E7FF',

  // Dark Mode (Default)
  dark: {
    bg: '#0D0F1A',
    bgElevated: '#151929',
    bgSurface: '#1C2136',
    bgHover: '#252B45',
    textPrimary: '#FFFFFF',
    textSecondary: '#929BC9',
    textTertiary: '#5A6282',
    textDisabled: '#3D4463',
    border: 'rgba(255, 255, 255, 0.08)',
    borderLight: 'rgba(255, 255, 255, 0.05)',
  },

  // Light Mode
  light: {
    bg: '#F8F9FC',
    bgElevated: '#FFFFFF',
    bgSurface: '#FFFFFF',
    bgHover: '#F1F3F9',
    textPrimary: '#111422',
    textSecondary: '#5A6282',
    textTertiary: '#929BC9',
    textDisabled: '#C4C9D4',
    border: 'rgba(0, 0, 0, 0.08)',
    borderLight: 'rgba(0, 0, 0, 0.05)',
  },

  // Priority Colors
  priority: {
    high: '#EF4444',
    highBg: 'rgba(239, 68, 68, 0.15)',
    medium: '#F59E0B',
    mediumBg: 'rgba(245, 158, 11, 0.15)',
    low: '#3B82F6',
    lowBg: 'rgba(59, 130, 246, 0.15)',
  },

  // Category Colors (for habits, events, etc.)
  category: {
    work: '#3B82F6',
    personal: '#10B981',
    health: '#EC4899',
    learning: '#8B5CF6',
    social: '#F97316',
    finance: '#14B8A6',
  },

  // Transparent
  transparent: 'transparent',
  white: '#FFFFFF',
  black: '#000000',
} as const;

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  // Font family - Using system fonts, Manrope will be loaded separately
  fontFamily: {
    display: 'Manrope',
    body: 'System',
  },

  // Font sizes
  size: {
    xs: 11,
    sm: 13,
    base: 15,
    lg: 17,
    xl: 20,
    '2xl': 24,
    '3xl': 32,
    '4xl': 40,
  },

  // Font weights
  weight: {
    normal: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
    extrabold: '800' as const,
  },

  // Line heights (multipliers)
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.7,
  },

  // Letter spacing
  letterSpacing: {
    tight: -0.5,
    normal: 0,
    wide: 0.5,
    wider: 1,
  },
} as const;

// ============================================================================
// SPACING
// ============================================================================

export const spacing = {
  0: 0,
  0.5: 2,
  1: 4,
  1.5: 6,
  2: 8,
  2.5: 10,
  3: 12,
  3.5: 14,
  4: 16,
  5: 20,
  6: 24,
  7: 28,
  8: 32,
  9: 36,
  10: 40,
  11: 44,
  12: 48,
  14: 56,
  16: 64,
  20: 80,
  24: 96,
} as const;

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const radius = {
  none: 0,
  sm: 4,
  DEFAULT: 8,
  md: 12,
  lg: 16,
  xl: 20,
  '2xl': 24,
  '3xl': 32,
  full: 9999,
} as const;

// ============================================================================
// SHADOWS
// ============================================================================

export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 2,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 8,
  },
  glow: {
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 10,
  },
} as const;

// ============================================================================
// ANIMATION
// ============================================================================

export const animation = {
  duration: {
    fast: 150,
    normal: 250,
    slow: 400,
  },
  easing: {
    easeIn: 'ease-in',
    easeOut: 'ease-out',
    easeInOut: 'ease-in-out',
  },
} as const;

// ============================================================================
// Z-INDEX
// ============================================================================

export const zIndex = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  overlay: 30,
  modal: 40,
  toast: 50,
} as const;

// ============================================================================
// COMPONENT SIZES
// ============================================================================

export const componentSize = {
  // Avatar sizes
  avatar: {
    sm: 32,
    md: 48,
    lg: 72,
    xl: 96,
  },

  // Button heights
  button: {
    sm: 32,
    md: 44,
    lg: 56,
  },

  // Input heights
  input: {
    sm: 40,
    md: 48,
    lg: 56,
  },

  // Icon sizes
  icon: {
    xs: 16,
    sm: 20,
    md: 24,
    lg: 32,
    xl: 40,
  },

  // Tab bar
  tabBar: {
    height: 80,
    iconSize: 24,
  },

  // Card
  card: {
    minHeight: 60,
  },
} as const;

// ============================================================================
// THEME OBJECT (Combines all tokens)
// ============================================================================

export type ThemeMode = 'dark' | 'light';

export const createTheme = (mode: ThemeMode = 'dark') => ({
  mode,
  colors: {
    ...colors,
    // Spread mode-specific colors
    bg: colors[mode].bg,
    bgElevated: colors[mode].bgElevated,
    bgSurface: colors[mode].bgSurface,
    bgHover: colors[mode].bgHover,
    textPrimary: colors[mode].textPrimary,
    textSecondary: colors[mode].textSecondary,
    textTertiary: colors[mode].textTertiary,
    textDisabled: colors[mode].textDisabled,
    border: colors[mode].border,
    borderLight: colors[mode].borderLight,
  },
  typography,
  spacing,
  radius,
  shadows,
  animation,
  zIndex,
  componentSize,
});

// Default theme (dark mode)
export const theme = createTheme('dark');

// Type for theme
export type Theme = ReturnType<typeof createTheme>;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get spacing value
 */
export const getSpacing = (value: keyof typeof spacing): number => spacing[value];

/**
 * Get color with opacity
 */
export const withOpacity = (color: string, opacity: number): string => {
  // Handle hex colors
  if (color.startsWith('#')) {
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color;
};
