/**
 * Offline Request Queue
 *
 * Queues API requests when offline and processes them when back online.
 * Persists queue to AsyncStorage to survive app restarts.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { AxiosRequestConfig } from 'axios';

const QUEUE_STORAGE_KEY = '@alfred_offline_queue';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // ms

export interface QueuedRequest {
  id: string;
  method: string;
  url: string;
  data?: any;
  headers?: Record<string, string>;
  timestamp: number;
  retries: number;
}

export type QueueEventType = 'enqueued' | 'processing' | 'completed' | 'failed' | 'online' | 'offline';

export interface QueueEvent {
  type: QueueEventType;
  request?: QueuedRequest;
  error?: string;
  queueLength: number;
}

type QueueEventListener = (event: QueueEvent) => void;

class OfflineQueue {
  private queue: QueuedRequest[] = [];
  private isOnline: boolean = true;
  private isProcessing: boolean = false;
  private listeners: Set<QueueEventListener> = new Set();
  private unsubscribeNetInfo: (() => void) | null = null;
  private apiClient: any = null;

  /**
   * Initialize the offline queue.
   * Call this once at app startup.
   */
  async initialize(apiClient: any): Promise<void> {
    this.apiClient = apiClient;

    // Load persisted queue
    await this.loadQueue();

    // Monitor connectivity
    this.unsubscribeNetInfo = NetInfo.addEventListener(this.handleConnectivityChange);

    // Check initial connectivity
    const state = await NetInfo.fetch();
    this.isOnline = state.isConnected ?? false;

    // Process queue if online
    if (this.isOnline && this.queue.length > 0) {
      this.processQueue();
    }
  }

  /**
   * Cleanup - call when app is closing
   */
  cleanup(): void {
    if (this.unsubscribeNetInfo) {
      this.unsubscribeNetInfo();
      this.unsubscribeNetInfo = null;
    }
    this.listeners.clear();
  }

  /**
   * Add a listener for queue events
   */
  addListener(listener: QueueEventListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Check if currently online
   */
  getIsOnline(): boolean {
    return this.isOnline;
  }

  /**
   * Get current queue length
   */
  getQueueLength(): number {
    return this.queue.length;
  }

  /**
   * Get all queued requests (for debugging/display)
   */
  getQueue(): QueuedRequest[] {
    return [...this.queue];
  }

  /**
   * Enqueue a request for later processing
   */
  async enqueue(config: AxiosRequestConfig): Promise<string> {
    const request: QueuedRequest = {
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      method: config.method || 'GET',
      url: config.url || '',
      data: config.data,
      headers: config.headers as Record<string, string>,
      timestamp: Date.now(),
      retries: 0,
    };

    this.queue.push(request);
    await this.persistQueue();

    this.emit({
      type: 'enqueued',
      request,
      queueLength: this.queue.length,
    });

    return request.id;
  }

  /**
   * Remove a specific request from the queue
   */
  async remove(id: string): Promise<boolean> {
    const index = this.queue.findIndex((r) => r.id === id);
    if (index !== -1) {
      this.queue.splice(index, 1);
      await this.persistQueue();
      return true;
    }
    return false;
  }

  /**
   * Clear the entire queue
   */
  async clear(): Promise<void> {
    this.queue = [];
    await this.persistQueue();
  }

  /**
   * Handle connectivity changes
   */
  private handleConnectivityChange = (state: NetInfoState): void => {
    const wasOnline = this.isOnline;
    this.isOnline = state.isConnected ?? false;

    if (!wasOnline && this.isOnline) {
      // Just came online
      this.emit({
        type: 'online',
        queueLength: this.queue.length,
      });

      // Process queued requests
      if (this.queue.length > 0) {
        this.processQueue();
      }
    } else if (wasOnline && !this.isOnline) {
      // Just went offline
      this.emit({
        type: 'offline',
        queueLength: this.queue.length,
      });
    }
  };

  /**
   * Process all queued requests
   */
  async processQueue(): Promise<void> {
    if (this.isProcessing || !this.isOnline || this.queue.length === 0) {
      return;
    }

    this.isProcessing = true;

    while (this.queue.length > 0 && this.isOnline) {
      const request = this.queue[0];

      this.emit({
        type: 'processing',
        request,
        queueLength: this.queue.length,
      });

      try {
        await this.executeRequest(request);

        // Success - remove from queue
        this.queue.shift();
        await this.persistQueue();

        this.emit({
          type: 'completed',
          request,
          queueLength: this.queue.length,
        });
      } catch (error) {
        request.retries++;

        if (request.retries >= MAX_RETRIES) {
          // Max retries reached - remove and notify
          this.queue.shift();
          await this.persistQueue();

          this.emit({
            type: 'failed',
            request,
            error: error instanceof Error ? error.message : 'Unknown error',
            queueLength: this.queue.length,
          });
        } else {
          // Wait before retrying
          await this.delay(RETRY_DELAY * request.retries);

          // If we went offline, stop processing
          if (!this.isOnline) {
            break;
          }
        }
      }
    }

    this.isProcessing = false;
  }

  /**
   * Execute a single request
   */
  private async executeRequest(request: QueuedRequest): Promise<any> {
    if (!this.apiClient) {
      throw new Error('API client not initialized');
    }

    return this.apiClient({
      method: request.method,
      url: request.url,
      data: request.data,
      headers: request.headers,
    });
  }

  /**
   * Load queue from storage
   */
  private async loadQueue(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem(QUEUE_STORAGE_KEY);
      if (stored) {
        this.queue = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load offline queue:', error);
      this.queue = [];
    }
  }

  /**
   * Persist queue to storage
   */
  private async persistQueue(): Promise<void> {
    try {
      await AsyncStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(this.queue));
    } catch (error) {
      console.error('Failed to persist offline queue:', error);
    }
  }

  /**
   * Emit an event to all listeners
   */
  private emit(event: QueueEvent): void {
    this.listeners.forEach((listener) => {
      try {
        listener(event);
      } catch (error) {
        console.error('Queue listener error:', error);
      }
    });
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// Export singleton instance
export const offlineQueue = new OfflineQueue();

export default offlineQueue;
