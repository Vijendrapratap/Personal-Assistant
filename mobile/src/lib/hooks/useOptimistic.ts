/**
 * useOptimistic - Hook for optimistic updates with rollback
 *
 * Provides instant UI feedback while API calls are in progress,
 * with automatic rollback on failure.
 */

import { useCallback, useRef } from 'react';
import { useAlfredStore } from '../store/alfredStore';
import { tasksApi, habitsApi } from '../../api/services';
import { useHaptics } from './useHaptics';

interface OptimisticUpdate<T> {
  apply: () => void;
  rollback: () => void;
  data?: T;
}

export function useOptimisticTasks() {
  const { tasks, setTasks, updateTask, removeTask } = useAlfredStore();
  const haptics = useHaptics();
  const rollbackRef = useRef<(() => void) | null>(null);

  /**
   * Optimistically complete a task
   */
  const completeTask = useCallback(
    async (taskId: string) => {
      // Store original state for rollback
      const originalTasks = [...tasks];
      const task = tasks.find((t) => t.task_id === taskId);

      if (!task) return;

      // Optimistically update UI
      updateTask(taskId, { status: 'completed' });

      // Trigger haptic feedback
      haptics.taskComplete();

      // Store rollback function
      rollbackRef.current = () => setTasks(originalTasks);

      try {
        // Make API call
        await tasksApi.complete(taskId);
        rollbackRef.current = null;
        return true;
      } catch (error) {
        // Rollback on failure
        console.error('Failed to complete task:', error);
        rollbackRef.current?.();
        rollbackRef.current = null;
        haptics.error();
        return false;
      }
    },
    [tasks, updateTask, setTasks, haptics]
  );

  /**
   * Optimistically start a task
   */
  const startTask = useCallback(
    async (taskId: string) => {
      const originalTasks = [...tasks];

      updateTask(taskId, { status: 'in_progress' });
      haptics.buttonPress();

      rollbackRef.current = () => setTasks(originalTasks);

      try {
        await tasksApi.start(taskId);
        rollbackRef.current = null;
        return true;
      } catch (error) {
        console.error('Failed to start task:', error);
        rollbackRef.current?.();
        rollbackRef.current = null;
        haptics.error();
        return false;
      }
    },
    [tasks, updateTask, setTasks, haptics]
  );

  /**
   * Optimistically delete a task
   */
  const deleteTask = useCallback(
    async (taskId: string) => {
      const originalTasks = [...tasks];

      removeTask(taskId);
      haptics.swipeAction();

      rollbackRef.current = () => setTasks(originalTasks);

      try {
        await tasksApi.delete(taskId);
        rollbackRef.current = null;
        return true;
      } catch (error) {
        console.error('Failed to delete task:', error);
        rollbackRef.current?.();
        rollbackRef.current = null;
        haptics.error();
        return false;
      }
    },
    [tasks, removeTask, setTasks, haptics]
  );

  /**
   * Optimistically create a task
   */
  const createTask = useCallback(
    async (title: string, options?: { priority?: string; projectId?: string; dueDate?: string }) => {
      // Create temporary task with temp ID
      const tempId = `temp-${Date.now()}`;
      const tempTask = {
        task_id: tempId,
        title,
        priority: (options?.priority || 'medium') as 'high' | 'medium' | 'low',
        status: 'pending' as const,
        project_id: options?.projectId || null,
        project_name: null,
        due_date: options?.dueDate || null,
        created_at: new Date().toISOString(),
      };

      const originalTasks = [...tasks];

      // Add to top of list
      setTasks([tempTask, ...tasks]);
      haptics.buttonPress();

      rollbackRef.current = () => setTasks(originalTasks);

      try {
        const result = await tasksApi.create({
          title,
          priority: options?.priority,
          project_id: options?.projectId,
          due_date: options?.dueDate,
        });

        // Replace temp task with real one
        setTasks([result, ...originalTasks]);
        rollbackRef.current = null;
        return result;
      } catch (error) {
        console.error('Failed to create task:', error);
        rollbackRef.current?.();
        rollbackRef.current = null;
        haptics.error();
        return null;
      }
    },
    [tasks, setTasks, haptics]
  );

  return {
    completeTask,
    startTask,
    deleteTask,
    createTask,
  };
}

export function useOptimisticHabits() {
  const { habits, setHabits, updateHabit } = useAlfredStore();
  const haptics = useHaptics();
  const rollbackRef = useRef<(() => void) | null>(null);

  /**
   * Optimistically log a habit
   */
  const logHabit = useCallback(
    async (habitId: string) => {
      const originalHabits = [...habits];
      const habit = habits.find((h) => h.habit_id === habitId);

      if (!habit) return false;

      const today = new Date().toISOString().split('T')[0];
      const newStreak = habit.current_streak + 1;
      const isMilestone = [7, 14, 21, 30, 60, 90, 100, 365].includes(newStreak);

      // Optimistically update
      updateHabit(habitId, {
        current_streak: newStreak,
        best_streak: Math.max(habit.best_streak, newStreak),
        total_completions: habit.total_completions + 1,
      });

      // Trigger appropriate haptic
      if (isMilestone) {
        haptics.streakMilestone();
      } else {
        haptics.habitLogged();
      }

      rollbackRef.current = () => setHabits(originalHabits);

      try {
        const result = await habitsApi.log(habitId);

        // Update with server response
        updateHabit(habitId, {
          current_streak: result.current_streak,
          best_streak: result.best_streak,
          total_completions: result.total_completions,
        });

        rollbackRef.current = null;
        return { success: true, isMilestone, newStreak };
      } catch (error) {
        console.error('Failed to log habit:', error);
        rollbackRef.current?.();
        rollbackRef.current = null;
        haptics.error();
        return { success: false };
      }
    },
    [habits, updateHabit, setHabits, haptics]
  );

  return {
    logHabit,
  };
}

/**
 * Combined hook for all optimistic updates
 */
export function useOptimistic() {
  const tasks = useOptimisticTasks();
  const habits = useOptimisticHabits();

  return {
    tasks,
    habits,
  };
}

export default useOptimistic;
