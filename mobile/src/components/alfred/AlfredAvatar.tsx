import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, ViewStyle } from 'react-native';
import { useTheme } from '../../theme';
import { AlfredState } from '../../lib/store/alfredStore';

type AvatarSize = 'sm' | 'md' | 'lg' | 'xl';

interface AlfredAvatarProps {
  state?: AlfredState;
  size?: AvatarSize;
  showGlow?: boolean;
  style?: ViewStyle;
}

/**
 * AlfredAvatar - The visual identity of Alfred
 *
 * States:
 * - idle: Subtle breathing animation
 * - listening: Pulsing glow, larger scale
 * - thinking: Rotating/orbiting effect
 * - speaking: Waveform-like animation
 * - working: Progress indicator style
 */
export function AlfredAvatar({
  state = 'idle',
  size = 'md',
  showGlow = true,
  style,
}: AlfredAvatarProps) {
  const { theme } = useTheme();

  // Animation values
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const opacityAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.3)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;

  const getSizeValue = (): number => {
    switch (size) {
      case 'sm':
        return theme.componentSize.avatar.sm;
      case 'lg':
        return theme.componentSize.avatar.lg;
      case 'xl':
        return theme.componentSize.avatar.xl;
      default:
        return theme.componentSize.avatar.md;
    }
  };

  const avatarSize = getSizeValue();
  const innerSize = avatarSize * 0.6;
  const glowSize = avatarSize * 1.5;

  // Animations based on state
  useEffect(() => {
    // Stop all animations first
    scaleAnim.stopAnimation();
    opacityAnim.stopAnimation();
    glowAnim.stopAnimation();
    rotateAnim.stopAnimation();

    switch (state) {
      case 'idle':
        // Subtle breathing animation
        Animated.loop(
          Animated.sequence([
            Animated.timing(scaleAnim, {
              toValue: 1.02,
              duration: 2000,
              useNativeDriver: true,
            }),
            Animated.timing(scaleAnim, {
              toValue: 1,
              duration: 2000,
              useNativeDriver: true,
            }),
          ])
        ).start();
        break;

      case 'listening':
        // Pulsing glow effect
        Animated.loop(
          Animated.sequence([
            Animated.timing(scaleAnim, {
              toValue: 1.1,
              duration: 500,
              useNativeDriver: true,
            }),
            Animated.timing(scaleAnim, {
              toValue: 1,
              duration: 500,
              useNativeDriver: true,
            }),
          ])
        ).start();
        Animated.loop(
          Animated.sequence([
            Animated.timing(glowAnim, {
              toValue: 0.8,
              duration: 500,
              useNativeDriver: true,
            }),
            Animated.timing(glowAnim, {
              toValue: 0.3,
              duration: 500,
              useNativeDriver: true,
            }),
          ])
        ).start();
        break;

      case 'thinking':
        // Rotating/pulsing effect
        Animated.loop(
          Animated.timing(rotateAnim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          })
        ).start();
        Animated.loop(
          Animated.sequence([
            Animated.timing(opacityAnim, {
              toValue: 0.7,
              duration: 800,
              useNativeDriver: true,
            }),
            Animated.timing(opacityAnim, {
              toValue: 1,
              duration: 800,
              useNativeDriver: true,
            }),
          ])
        ).start();
        break;

      case 'speaking':
        // Quick pulse effect
        Animated.loop(
          Animated.sequence([
            Animated.timing(scaleAnim, {
              toValue: 1.05,
              duration: 200,
              useNativeDriver: true,
            }),
            Animated.timing(scaleAnim, {
              toValue: 0.98,
              duration: 200,
              useNativeDriver: true,
            }),
            Animated.timing(scaleAnim, {
              toValue: 1,
              duration: 200,
              useNativeDriver: true,
            }),
          ])
        ).start();
        break;

      case 'working':
        // Steady pulse with glow
        Animated.loop(
          Animated.sequence([
            Animated.timing(glowAnim, {
              toValue: 0.6,
              duration: 1000,
              useNativeDriver: true,
            }),
            Animated.timing(glowAnim, {
              toValue: 0.3,
              duration: 1000,
              useNativeDriver: true,
            }),
          ])
        ).start();
        break;
    }

    return () => {
      scaleAnim.stopAnimation();
      opacityAnim.stopAnimation();
      glowAnim.stopAnimation();
      rotateAnim.stopAnimation();
    };
  }, [state]);

  const rotate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={[styles.container, { width: glowSize, height: glowSize }, style]}>
      {/* Glow effect */}
      {showGlow && (
        <Animated.View
          style={[
            styles.glow,
            {
              width: glowSize,
              height: glowSize,
              borderRadius: glowSize / 2,
              backgroundColor: theme.colors.primary,
              opacity: glowAnim,
            },
          ]}
        />
      )}

      {/* Main avatar circle */}
      <Animated.View
        style={[
          styles.avatar,
          {
            width: avatarSize,
            height: avatarSize,
            borderRadius: avatarSize / 2,
            backgroundColor: theme.colors.primary,
            transform: [{ scale: scaleAnim }, { rotate }],
            opacity: opacityAnim,
          },
        ]}
      >
        {/* Inner icon/symbol */}
        <View
          style={[
            styles.inner,
            {
              width: innerSize,
              height: innerSize,
              borderRadius: innerSize / 2,
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
            },
          ]}
        >
          {/* Alfred symbol - simple "A" or abstract mark */}
          <View style={styles.symbolContainer}>
            {state === 'listening' ? (
              // Waveform bars for listening
              <View style={styles.waveform}>
                {[0.4, 0.7, 1, 0.7, 0.4].map((height, i) => (
                  <View
                    key={i}
                    style={[
                      styles.waveBar,
                      {
                        height: innerSize * 0.4 * height,
                        backgroundColor: theme.colors.white,
                      },
                    ]}
                  />
                ))}
              </View>
            ) : state === 'thinking' ? (
              // Dots for thinking
              <View style={styles.thinkingDots}>
                {[0, 1, 2].map((i) => (
                  <View
                    key={i}
                    style={[
                      styles.dot,
                      {
                        backgroundColor: theme.colors.white,
                        width: innerSize * 0.12,
                        height: innerSize * 0.12,
                      },
                    ]}
                  />
                ))}
              </View>
            ) : (
              // Default: Alfred "A" mark
              <View style={styles.alfredMark}>
                <View
                  style={[
                    styles.markLine,
                    {
                      width: innerSize * 0.3,
                      height: 2,
                      backgroundColor: theme.colors.white,
                      transform: [{ rotate: '45deg' }],
                    },
                  ]}
                />
                <View
                  style={[
                    styles.markLine,
                    {
                      width: innerSize * 0.3,
                      height: 2,
                      backgroundColor: theme.colors.white,
                      transform: [{ rotate: '-45deg' }],
                      marginTop: -2,
                    },
                  ]}
                />
              </View>
            )}
          </View>
        </View>
      </Animated.View>

      {/* State indicator ring */}
      {state !== 'idle' && (
        <View
          style={[
            styles.stateRing,
            {
              width: avatarSize + 8,
              height: avatarSize + 8,
              borderRadius: (avatarSize + 8) / 2,
              borderColor:
                state === 'listening'
                  ? theme.colors.success
                  : state === 'thinking'
                  ? theme.colors.warning
                  : theme.colors.primary,
            },
          ]}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  glow: {
    position: 'absolute',
  },
  avatar: {
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  },
  inner: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  symbolContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  waveform: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  waveBar: {
    width: 3,
    borderRadius: 2,
  },
  thinkingDots: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  dot: {
    borderRadius: 100,
  },
  alfredMark: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  markLine: {
    borderRadius: 1,
  },
  stateRing: {
    position: 'absolute',
    borderWidth: 2,
    zIndex: 0,
  },
});

export default AlfredAvatar;
