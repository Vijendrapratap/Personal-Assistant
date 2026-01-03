/**
 * useAlfred - Main hook for Alfred interactions
 * Provides access to briefings, chat, and proactive features
 */

import { useState, useCallback } from 'react';
import { useAlfredStore } from '../store/alfredStore';
import { dashboardApi, chatApi, proactiveApi } from '../../api/services';

export function useAlfred() {
  const {
    briefing,
    setBriefing,
    briefingLoading,
    setBriefingLoading,
    proactiveCards,
    setProactiveCards,
    alfredState,
    setAlfredState,
    dismissCard,
    snoozeCard,
    setError,
  } = useAlfredStore();

  const [chatLoading, setChatLoading] = useState(false);

  /**
   * Load morning briefing
   */
  const loadBriefing = useCallback(async () => {
    setBriefingLoading(true);
    try {
      const data = await dashboardApi.getMorningBriefing();
      setBriefing(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load briefing');
    } finally {
      setBriefingLoading(false);
    }
  }, []);

  /**
   * Load today's overview (combined data)
   */
  const loadTodayOverview = useCallback(async () => {
    setBriefingLoading(true);
    try {
      const [overview, cards] = await Promise.all([
        dashboardApi.getToday(),
        proactiveApi.getCards(),
      ]);

      // Transform overview into briefing format
      setBriefing({
        greeting: overview.greeting,
        focus: overview.focus.high_priority_tasks?.[0]
          ? {
              title: overview.focus.high_priority_tasks[0].title,
              task_id: overview.focus.high_priority_tasks[0].task_id,
              due: overview.focus.high_priority_tasks[0].due_date,
            }
          : undefined,
        stats: overview.stats,
        upcoming_events: [], // Would come from calendar integration
      });

      setProactiveCards(cards);
    } catch (err: any) {
      setError(err.message || 'Failed to load today overview');
    } finally {
      setBriefingLoading(false);
    }
  }, []);

  /**
   * Load proactive cards
   */
  const loadProactiveCards = useCallback(async () => {
    try {
      const cards = await proactiveApi.getCards();
      setProactiveCards(cards);
    } catch (err: any) {
      console.error('Failed to load proactive cards:', err);
    }
  }, []);

  /**
   * Send a message to Alfred
   */
  const sendMessage = useCallback(async (message: string): Promise<string> => {
    setChatLoading(true);
    setAlfredState('thinking');

    try {
      const response = await chatApi.send(message);
      setAlfredState('speaking');

      // Reset to idle after a delay
      setTimeout(() => setAlfredState('idle'), 2000);

      return response.response;
    } catch (err: any) {
      setAlfredState('idle');
      throw err;
    } finally {
      setChatLoading(false);
    }
  }, []);

  /**
   * Handle proactive card dismiss
   */
  const handleDismissCard = useCallback(async (cardId: string) => {
    try {
      await proactiveApi.dismiss(cardId);
      dismissCard(cardId);
    } catch (err: any) {
      console.error('Failed to dismiss card:', err);
    }
  }, []);

  /**
   * Handle proactive card snooze
   */
  const handleSnoozeCard = useCallback(async (cardId: string) => {
    try {
      await proactiveApi.snooze(cardId);
      snoozeCard(cardId);
    } catch (err: any) {
      console.error('Failed to snooze card:', err);
    }
  }, []);

  return {
    // State
    briefing,
    briefingLoading,
    proactiveCards,
    alfredState,
    chatLoading,

    // Actions
    loadBriefing,
    loadTodayOverview,
    loadProactiveCards,
    sendMessage,
    handleDismissCard,
    handleSnoozeCard,
    setAlfredState,
  };
}

export default useAlfred;
