/**
 * VoiceModal - Full-screen voice interface with Alfred
 * Shows avatar, waveform, conversation history, and transparency panel
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Animated,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../theme';
import { Text, Card, Button } from '../components/common';
import { AlfredAvatar, TransparencyPanel, ThinkingStep } from '../components/alfred';
import { chatApi } from '../api/services';

interface VoiceModalProps {
  navigation: any;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  thinkingSteps?: ThinkingStep[];
}

// Waveform visualization component
function Waveform({ isActive, theme }: { isActive: boolean; theme: any }) {
  const bars = 7;
  const animations = useRef(
    Array.from({ length: bars }, () => new Animated.Value(0.3))
  ).current;

  useEffect(() => {
    if (isActive) {
      const animateBar = (index: number) => {
        Animated.loop(
          Animated.sequence([
            Animated.timing(animations[index], {
              toValue: Math.random() * 0.7 + 0.3,
              duration: 150 + Math.random() * 100,
              useNativeDriver: true,
            }),
            Animated.timing(animations[index], {
              toValue: 0.3,
              duration: 150 + Math.random() * 100,
              useNativeDriver: true,
            }),
          ])
        ).start();
      };

      animations.forEach((_, index) => animateBar(index));
    } else {
      animations.forEach((anim) => {
        anim.stopAnimation();
        Animated.timing(anim, {
          toValue: 0.3,
          duration: 200,
          useNativeDriver: true,
        }).start();
      });
    }

    return () => {
      animations.forEach((anim) => anim.stopAnimation());
    };
  }, [isActive]);

  return (
    <View style={waveformStyles.container}>
      {animations.map((anim, index) => (
        <Animated.View
          key={index}
          style={[
            waveformStyles.bar,
            {
              backgroundColor: isActive ? theme.colors.primary : theme.colors.textTertiary,
              transform: [{ scaleY: anim }],
            },
          ]}
        />
      ))}
    </View>
  );
}

const waveformStyles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 40,
    gap: 4,
  },
  bar: {
    width: 4,
    height: 40,
    borderRadius: 2,
  },
});

// Quick action suggestions
const QUICK_ACTIONS = [
  'Add a task',
  'Schedule meeting',
  'Log workout',
  'Set reminder',
  'Update project',
];

export default function VoiceModal({ navigation }: VoiceModalProps) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const scrollRef = useRef<ScrollView>(null);

  // State
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [alfredState, setAlfredState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        scrollRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  // Simulate thinking steps
  const simulateThinking = async (query: string) => {
    const steps: ThinkingStep[] = [
      { id: '1', text: 'Understanding your request', status: 'pending' },
      { id: '2', text: 'Checking relevant context', status: 'pending' },
      { id: '3', text: 'Processing action', status: 'pending' },
      { id: '4', text: 'Preparing response', status: 'pending' },
    ];

    setThinkingSteps(steps);

    // Animate through steps
    for (let i = 0; i < steps.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 400));
      setThinkingSteps((prev) =>
        prev.map((s, idx) => ({
          ...s,
          status: idx < i ? 'completed' : idx === i ? 'in_progress' : 'pending',
        }))
      );
    }

    // Complete all steps
    await new Promise((resolve) => setTimeout(resolve, 300));
    setThinkingSteps((prev) =>
      prev.map((s) => ({ ...s, status: 'completed' as const }))
    );
  };

  // Handle sending a message
  const handleSend = async (text?: string) => {
    const messageText = text || inputText.trim();
    if (!messageText) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsProcessing(true);
    setAlfredState('thinking');

    try {
      // Simulate thinking
      await simulateThinking(messageText);

      // Call API
      const response = await chatApi.send(messageText);

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        thinkingSteps: [...thinkingSteps],
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setAlfredState('speaking');

      // Reset after speaking
      setTimeout(() => {
        setAlfredState('idle');
        setThinkingSteps([]);
      }, 2000);
    } catch (error) {
      console.error('Chat error:', error);
      setThinkingSteps((prev) =>
        prev.map((s, i) =>
          i === prev.length - 1 ? { ...s, status: 'error' as const } : s
        )
      );
      setAlfredState('idle');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle voice button press
  const handleVoicePress = () => {
    if (isListening) {
      setIsListening(false);
      setAlfredState('idle');
      // TODO: Stop recording and process
    } else {
      setIsListening(true);
      setAlfredState('listening');
      // TODO: Start recording with expo-av
    }
  };

  // Handle quick action
  const handleQuickAction = (action: string) => {
    handleSend(action);
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.bg }]}>
      {/* Header */}
      <View
        style={[
          styles.header,
          {
            paddingTop: insets.top + 12,
            borderBottomColor: theme.colors.border,
          },
        ]}
      >
        <View style={styles.headerSpacer} />
        <Text variant="body" style={{ fontWeight: '600' }}>
          Alfred
        </Text>
        <TouchableOpacity
          style={styles.doneButton}
          onPress={() => navigation.goBack()}
        >
          <Text variant="body" color="accent">
            Done
          </Text>
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        style={styles.content}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        {/* Messages Area */}
        <ScrollView
          ref={scrollRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Alfred Avatar - shown when no messages or listening */}
          {(messages.length === 0 || isListening) && (
            <View style={styles.avatarSection}>
              <AlfredAvatar state={alfredState} size="xl" />
              <Text
                variant="body"
                color="secondary"
                style={styles.stateText}
              >
                {isListening
                  ? 'Listening...'
                  : isProcessing
                  ? 'Thinking...'
                  : 'How can I help?'}
              </Text>
              {isListening && <Waveform isActive={isListening} theme={theme} />}
            </View>
          )}

          {/* Conversation */}
          {messages.map((message) => (
            <View
              key={message.id}
              style={[
                styles.messageWrapper,
                message.role === 'user' && styles.userMessageWrapper,
              ]}
            >
              <View
                style={[
                  styles.messageBubble,
                  message.role === 'user'
                    ? {
                        backgroundColor: theme.colors.primary,
                        borderBottomRightRadius: 4,
                      }
                    : {
                        backgroundColor: theme.colors.bgSurface,
                        borderBottomLeftRadius: 4,
                      },
                ]}
              >
                <Text
                  style={{
                    color: message.role === 'user' ? '#FFFFFF' : theme.colors.textPrimary,
                  }}
                >
                  {message.content}
                </Text>
              </View>
            </View>
          ))}

          {/* Thinking Panel (shown while processing) */}
          {isProcessing && thinkingSteps.length > 0 && (
            <View style={styles.thinkingWrapper}>
              <TransparencyPanel steps={thinkingSteps} />
            </View>
          )}
        </ScrollView>

        {/* Quick Actions (shown when idle) */}
        {messages.length === 0 && !isListening && !isProcessing && (
          <View style={styles.quickActionsContainer}>
            <Text variant="caption" color="tertiary" style={styles.quickActionsLabel}>
              SUGGESTIONS
            </Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.quickActions}
            >
              {QUICK_ACTIONS.map((action) => (
                <TouchableOpacity
                  key={action}
                  style={[
                    styles.quickActionChip,
                    { backgroundColor: theme.colors.bgSurface },
                  ]}
                  onPress={() => handleQuickAction(action)}
                >
                  <Text variant="bodySmall">{action}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Input Area */}
        <View
          style={[
            styles.inputArea,
            {
              backgroundColor: theme.colors.bg,
              paddingBottom: insets.bottom + 16,
              borderTopColor: theme.colors.border,
            },
          ]}
        >
          {/* Text Input Row */}
          <View style={styles.inputRow}>
            <TouchableOpacity
              style={[styles.keyboardButton, { backgroundColor: theme.colors.bgSurface }]}
              onPress={() => {
                // Focus on text input
              }}
            >
              <Text style={{ fontSize: 18 }}>⌨️</Text>
            </TouchableOpacity>

            <TextInput
              style={[
                styles.textInput,
                {
                  backgroundColor: theme.colors.bgSurface,
                  color: theme.colors.textPrimary,
                },
              ]}
              placeholder="Type a message..."
              placeholderTextColor={theme.colors.textTertiary}
              value={inputText}
              onChangeText={setInputText}
              onSubmitEditing={() => handleSend()}
              returnKeyType="send"
              editable={!isProcessing}
            />

            {inputText.length > 0 ? (
              <TouchableOpacity
                style={[styles.sendButton, { backgroundColor: theme.colors.primary }]}
                onPress={() => handleSend()}
                disabled={isProcessing}
              >
                <Text style={styles.sendButtonText}>↑</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity style={styles.moreButton}>
                <Text style={{ fontSize: 18, color: theme.colors.textTertiary }}>
                  •••
                </Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Voice Button */}
          <TouchableOpacity
            style={[
              styles.voiceButton,
              {
                backgroundColor: isListening
                  ? theme.colors.danger
                  : theme.colors.primary,
                ...theme.shadows.glow,
              },
            ]}
            onPress={handleVoicePress}
            disabled={isProcessing}
            activeOpacity={0.8}
          >
            <Text style={styles.voiceButtonText}>
              {isListening ? '■' : '🎤'}
            </Text>
            <Text style={styles.voiceButtonLabel}>
              {isListening ? 'Stop' : 'Hold to speak'}
            </Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  headerSpacer: {
    width: 60,
  },
  doneButton: {
    width: 60,
    alignItems: 'flex-end',
  },
  content: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  avatarSection: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  stateText: {
    marginTop: 20,
    marginBottom: 16,
  },
  messageWrapper: {
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  userMessageWrapper: {
    alignItems: 'flex-end',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 14,
    borderRadius: 18,
  },
  thinkingWrapper: {
    marginTop: 8,
    marginBottom: 12,
  },
  quickActionsContainer: {
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  quickActionsLabel: {
    marginBottom: 8,
  },
  quickActions: {
    gap: 8,
  },
  quickActionChip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  inputArea: {
    paddingHorizontal: 20,
    paddingTop: 12,
    borderTopWidth: 1,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 16,
  },
  keyboardButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  textInput: {
    flex: 1,
    height: 44,
    paddingHorizontal: 16,
    borderRadius: 22,
    fontSize: 15,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
  moreButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  voiceButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 16,
  },
  voiceButtonText: {
    fontSize: 24,
    color: '#FFFFFF',
  },
  voiceButtonLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 4,
  },
});
