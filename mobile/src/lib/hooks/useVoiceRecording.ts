/**
 * useVoiceRecording - Hook for voice recording functionality
 * Uses expo-av for audio recording when available
 */

import { useState, useRef, useCallback, useEffect } from 'react';
// Note: expo-av needs to be installed: npx expo install expo-av
// import { Audio } from 'expo-av';

export interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number; // in seconds
  audioLevel: number; // 0-1 for visualization
}

export interface UseVoiceRecordingOptions {
  maxDuration?: number; // in seconds
  onRecordingComplete?: (audioBase64: string, duration: number) => void;
  onError?: (error: Error) => void;
}

export function useVoiceRecording(options: UseVoiceRecordingOptions = {}) {
  const { maxDuration = 60, onRecordingComplete, onError } = options;

  const [state, setState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
    audioLevel: 0,
  });

  const recordingRef = useRef<any>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioLevelRef = useRef<NodeJS.Timeout | null>(null);

  // Request permissions
  const requestPermissions = useCallback(async () => {
    try {
      // Uncomment when expo-av is installed:
      // const { status } = await Audio.requestPermissionsAsync();
      // return status === 'granted';

      // Placeholder: assume permission granted
      console.log('Voice permissions would be requested here');
      return true;
    } catch (error) {
      onError?.(error as Error);
      return false;
    }
  }, [onError]);

  // Start recording
  const startRecording = useCallback(async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) {
      onError?.(new Error('Microphone permission not granted'));
      return false;
    }

    try {
      // Uncomment when expo-av is installed:
      /*
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      recordingRef.current = recording;
      */

      setState((prev) => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        duration: 0,
      }));

      // Start duration timer
      timerRef.current = setInterval(() => {
        setState((prev) => {
          if (prev.duration >= maxDuration) {
            stopRecording();
            return prev;
          }
          return { ...prev, duration: prev.duration + 1 };
        });
      }, 1000);

      // Simulate audio level changes for visualization
      audioLevelRef.current = setInterval(() => {
        setState((prev) => ({
          ...prev,
          audioLevel: Math.random() * 0.6 + 0.2, // Random level 0.2-0.8
        }));
      }, 100);

      return true;
    } catch (error) {
      onError?.(error as Error);
      return false;
    }
  }, [maxDuration, onError, requestPermissions]);

  // Stop recording
  const stopRecording = useCallback(async () => {
    // Clear timers
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (audioLevelRef.current) {
      clearInterval(audioLevelRef.current);
      audioLevelRef.current = null;
    }

    const duration = state.duration;

    setState((prev) => ({
      ...prev,
      isRecording: false,
      isPaused: false,
      audioLevel: 0,
    }));

    try {
      // Uncomment when expo-av is installed:
      /*
      if (recordingRef.current) {
        await recordingRef.current.stopAndUnloadAsync();
        const uri = recordingRef.current.getURI();

        // Convert to base64
        const response = await fetch(uri);
        const blob = await response.blob();
        const reader = new FileReader();

        reader.onloadend = () => {
          const base64 = reader.result as string;
          const base64Data = base64.split(',')[1];
          onRecordingComplete?.(base64Data, duration);
        };

        reader.readAsDataURL(blob);
        recordingRef.current = null;
      }
      */

      // Placeholder: simulate recording completion
      console.log('Recording stopped, duration:', duration);
      onRecordingComplete?.('placeholder_audio_base64', duration);

      return true;
    } catch (error) {
      onError?.(error as Error);
      return false;
    }
  }, [state.duration, onRecordingComplete, onError]);

  // Pause recording
  const pauseRecording = useCallback(async () => {
    try {
      // Uncomment when expo-av is installed:
      // await recordingRef.current?.pauseAsync();

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (audioLevelRef.current) {
        clearInterval(audioLevelRef.current);
        audioLevelRef.current = null;
      }

      setState((prev) => ({
        ...prev,
        isPaused: true,
        audioLevel: 0,
      }));

      return true;
    } catch (error) {
      onError?.(error as Error);
      return false;
    }
  }, [onError]);

  // Resume recording
  const resumeRecording = useCallback(async () => {
    try {
      // Uncomment when expo-av is installed:
      // await recordingRef.current?.startAsync();

      setState((prev) => ({
        ...prev,
        isPaused: false,
      }));

      // Restart timers
      timerRef.current = setInterval(() => {
        setState((prev) => {
          if (prev.duration >= maxDuration) {
            stopRecording();
            return prev;
          }
          return { ...prev, duration: prev.duration + 1 };
        });
      }, 1000);

      audioLevelRef.current = setInterval(() => {
        setState((prev) => ({
          ...prev,
          audioLevel: Math.random() * 0.6 + 0.2,
        }));
      }, 100);

      return true;
    } catch (error) {
      onError?.(error as Error);
      return false;
    }
  }, [maxDuration, onError, stopRecording]);

  // Cancel recording
  const cancelRecording = useCallback(async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (audioLevelRef.current) {
      clearInterval(audioLevelRef.current);
      audioLevelRef.current = null;
    }

    try {
      // Uncomment when expo-av is installed:
      /*
      if (recordingRef.current) {
        await recordingRef.current.stopAndUnloadAsync();
        recordingRef.current = null;
      }
      */

      setState({
        isRecording: false,
        isPaused: false,
        duration: 0,
        audioLevel: 0,
      });

      return true;
    } catch (error) {
      onError?.(error as Error);
      return false;
    }
  }, [onError]);

  // Format duration as mm:ss
  const formatDuration = useCallback((seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (audioLevelRef.current) clearInterval(audioLevelRef.current);
      // Cancel any active recording
      if (recordingRef.current) {
        // recordingRef.current.stopAndUnloadAsync();
      }
    };
  }, []);

  return {
    ...state,
    formattedDuration: formatDuration(state.duration),
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    cancelRecording,
    requestPermissions,
  };
}

export default useVoiceRecording;
