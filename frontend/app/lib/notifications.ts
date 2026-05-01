/**
 * Notification service for managing in-app notifications
 */

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
  actionUrl?: string;
  actionLabel?: string;
}

const STORAGE_KEY = 'AETHER-SCORE_notifications';

export class NotificationService {
  private static notifications: Notification[] = [];

  static init() {
    if (typeof window === 'undefined') return;
    
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        this.notifications = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load notifications from storage:', error);
      this.notifications = [];
    }
  }

  static save() {
    if (typeof window === 'undefined') return;
    
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.notifications));
    } catch (error) {
      console.error('Failed to save notifications to storage:', error);
    }
  }

  static add(notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) {
    const newNotification: Notification = {
      ...notification,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      read: false,
    };

    this.notifications.unshift(newNotification);
    
    // Keep only last 100 notifications
    if (this.notifications.length > 100) {
      this.notifications = this.notifications.slice(0, 100);
    }

    this.save();
    return newNotification;
  }

  static getAll(): Notification[] {
    return [...this.notifications];
  }

  static getUnread(): Notification[] {
    return this.notifications.filter((n) => !n.read);
  }

  static getUnreadCount(): number {
    return this.notifications.filter((n) => !n.read).length;
  }

  static markAsRead(id: string) {
    const notification = this.notifications.find((n) => n.id === id);
    if (notification) {
      notification.read = true;
      this.save();
    }
  }

  static markAllAsRead() {
    this.notifications.forEach((n) => (n.read = true));
    this.save();
  }

  static remove(id: string) {
    this.notifications = this.notifications.filter((n) => n.id !== id);
    this.save();
  }

  static clear() {
    this.notifications = [];
    this.save();
  }

  static clearOld(days: number = 30) {
    const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
    this.notifications = this.notifications.filter((n) => n.timestamp > cutoff);
    this.save();
  }
}

// Initialize on module load
if (typeof window !== 'undefined') {
  NotificationService.init();
}


