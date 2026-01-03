import React, { useState, useRef } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Keyboard,
  ViewStyle,
} from 'react-native';
import { useTheme } from '../../theme';
import { Text } from '../common/Text';

interface ConversationInputProps {
  placeholder?: string;
  onSubmit: (message: string) => void;
  onVoicePress?: () => void;
  suggestions?: string[];
  disabled?: boolean;
  autoFocus?: boolean;
  showVoiceButton?: boolean;
  style?: ViewStyle;
}

/**
 * ConversationInput - Universal input for talking to Alfred
 *
 * Features:
 * - Text input with send button
 * - Voice button for voice input
 * - Quick suggestion chips
 * - Animated focus state
 */
export function ConversationInput({
  placeholder = 'Ask Alfred...',
  onSubmit,
  onVoicePress,
  suggestions = [],
  disabled = false,
  autoFocus = false,
  showVoiceButton = true,
  style,
}: ConversationInputProps) {
  const { theme } = useTheme();
  const [value, setValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<TextInput>(null);
  const focusAnim = useRef(new Animated.Value(0)).current;

  const handleFocus = () => {
    setIsFocused(true);
    Animated.timing(focusAnim, {
      toValue: 1,
      duration: 200,
      useNativeDriver: false,
    }).start();
  };

  const handleBlur = () => {
    setIsFocused(false);
    Animated.timing(focusAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: false,
    }).start();
  };

  const handleSubmit = () => {
    if (value.trim()) {
      onSubmit(value.trim());
      setValue('');
      Keyboard.dismiss();
    }
  };

  const handleSuggestionPress = (suggestion: string) => {
    onSubmit(suggestion);
  };

  const borderColor = focusAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [theme.colors.border, theme.colors.primary],
  });

  const hasValue = value.trim().length > 0;

  return (
    <View style={[styles.container, style]}>
      {/* Suggestion chips */}
      {suggestions.length > 0 && !isFocused && !hasValue && (
        <View style={styles.suggestions}>
          {suggestions.slice(0, 3).map((suggestion, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.suggestionChip,
                { backgroundColor: theme.colors.bgSurface },
              ]}
              onPress={() => handleSuggestionPress(suggestion)}
            >
              <Text variant="bodySmall" color="secondary">
                {suggestion}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Input container */}
      <Animated.View
        style={[
          styles.inputContainer,
          {
            backgroundColor: theme.colors.bgSurface,
            borderColor: borderColor,
            ...theme.shadows.sm,
          },
        ]}
      >
        {/* Alfred icon */}
        <View
          style={[
            styles.alfredIcon,
            { backgroundColor: theme.colors.primary },
          ]}
        >
          <Text style={styles.alfredIconText}>A</Text>
        </View>

        {/* Text input */}
        <TextInput
          ref={inputRef}
          style={[
            styles.input,
            {
              color: theme.colors.textPrimary,
            },
          ]}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.textTertiary}
          value={value}
          onChangeText={setValue}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onSubmitEditing={handleSubmit}
          returnKeyType="send"
          autoFocus={autoFocus}
          editable={!disabled}
          multiline={false}
        />

        {/* Action buttons */}
        <View style={styles.actions}>
          {hasValue ? (
            // Send button
            <TouchableOpacity
              style={[
                styles.sendButton,
                { backgroundColor: theme.colors.primary },
              ]}
              onPress={handleSubmit}
              disabled={disabled}
            >
              <Text style={styles.sendIcon}></Text>
            </TouchableOpacity>
          ) : showVoiceButton ? (
            // Voice button
            <TouchableOpacity
              style={[
                styles.voiceButton,
                { backgroundColor: theme.colors.primarySoft },
              ]}
              onPress={onVoicePress}
              disabled={disabled}
            >
              <Text style={[styles.voiceIcon, { color: theme.colors.primary }]}>

              </Text>
            </TouchableOpacity>
          ) : null}
        </View>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  suggestions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  suggestionChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 16,
    borderWidth: 1.5,
    paddingLeft: 6,
    paddingRight: 6,
    minHeight: 52,
  },
  alfredIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  alfredIconText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
  input: {
    flex: 1,
    fontSize: 15,
    fontWeight: '500',
    paddingVertical: 12,
    paddingRight: 8,
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendIcon: {
    fontSize: 18,
    color: '#fff',
  },
  voiceButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  voiceIcon: {
    fontSize: 20,
  },
});

export default ConversationInput;
