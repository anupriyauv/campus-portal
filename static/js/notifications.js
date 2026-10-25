// Real-time notification system with WebSocket support (optional)

class RealtimeNotifications {
    constructor() {
        this.pollInterval = 30000; // 30 seconds
        this.init();
    }

    init() {
        this.startPolling();
        this.setupEventListeners();
    }

    startPolling() {
        // Initial fetch
        this.checkForNewNotifications();
        
        // Set up interval
        this.intervalId = setInterval(() => {
            this.checkForNewNotifications();
        }, this.pollInterval);
    }

    stopPolling() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    }

    checkForNewNotifications() {
        fetch('/notifications/api/unread-count/')
            .then(response => response.json())
            .then(data => {
                this.updateBadge(data.count);
                if (data.count > 0) {
                    this.showNotificationAlert();
                }
            })
            .catch(error => console.error('Error checking notifications:', error));
    }

    updateBadge(count) {
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            badge.textContent = count;
            if (count > 0) {
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        }
    }

    showNotificationAlert() {
        // Play notification sound (optional)
        // this.playNotificationSound();
        
        // Show desktop notification if permitted
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Campus Portal', {
                body: 'You have new notifications',
                icon: '/static/images/logo.png',
                badge: '/static/images/logo.png'
            });
        }
    }

    playNotificationSound() {
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.3;
        audio.play().catch(e => console.log('Could not play sound:', e));
    }

    setupEventListeners() {
        // Request notification permission
        const notifButton = document.getElementById('enableNotifications');
        if (notifButton) {
            notifButton.addEventListener('click', () => {
                this.requestNotificationPermission();
            });
        }

        // Mark all as read
        const markAllBtn = document.getElementById('markAllAsRead');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }
    }

    requestNotificationPermission() {
        if ('Notification' in window) {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    toastManager.success('Notifications enabled!');
                }
            });
        }
    }

    markAllAsRead() {
        fetch('/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                toastManager.success('All notifications marked as read');
                this.updateBadge(0);
                location.reload();
            }
        })
        .catch(error => console.error('Error marking all as read:', error));
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('notificationBell')) {
        new RealtimeNotifications();
    }
});