/**
 * ErrorBoundary - Global error handling component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs the errors, and displays a fallback UI.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { Text } from './Text';
import { colors, spacing, radius } from '../../theme/tokens';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    this.setState({ errorInfo });

    // Call optional error handler (for error tracking services)
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <View style={styles.container}>
          <View style={styles.content}>
            <View style={styles.iconContainer}>
              <Text style={styles.icon}>!</Text>
            </View>

            <Text variant="h2" style={styles.title}>
              Something went wrong
            </Text>

            <Text variant="body" color="secondary" style={styles.message}>
              We're sorry, but something unexpected happened. Please try again.
            </Text>

            {this.state.error && (
              <ScrollView style={styles.errorBox} horizontal={false}>
                <Text variant="caption" color="tertiary" style={styles.errorText}>
                  {this.state.error.message}
                </Text>
              </ScrollView>
            )}

            <TouchableOpacity
              style={styles.button}
              onPress={this.handleRetry}
              activeOpacity={0.8}
            >
              <Text style={styles.buttonText}>Try Again</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.secondaryButton}
              onPress={() => {
                // Could add navigation to home or help
                this.handleRetry();
              }}
              activeOpacity={0.8}
            >
              <Text variant="body" color="secondary">
                Go to Home
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.dark.bg,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing[6],
  },
  content: {
    alignItems: 'center',
    maxWidth: 320,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: radius.full,
    backgroundColor: colors.dangerSoft,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing[6],
  },
  icon: {
    fontSize: 40,
    fontWeight: '700',
    color: colors.danger,
  },
  title: {
    textAlign: 'center',
    marginBottom: spacing[3],
    color: colors.dark.textPrimary,
  },
  message: {
    textAlign: 'center',
    marginBottom: spacing[6],
  },
  errorBox: {
    backgroundColor: colors.dark.bgSurface,
    borderRadius: radius.md,
    padding: spacing[4],
    marginBottom: spacing[6],
    maxHeight: 100,
    width: '100%',
  },
  errorText: {
    fontFamily: 'monospace',
    fontSize: 12,
  },
  button: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing[8],
    paddingVertical: spacing[4],
    borderRadius: radius.lg,
    marginBottom: spacing[4],
    minWidth: 200,
    alignItems: 'center',
  },
  buttonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    paddingVertical: spacing[3],
  },
});

export default ErrorBoundary;
