// Main JavaScript file for Campus Portal

// CSRF Token Setup for AJAX
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Configure AJAX to send CSRF token
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// Notification System
class NotificationManager {
    constructor() {
        this.notificationBell = document.getElementById('notificationBell');
        this.notificationBadge = document.getElementById('notificationBadge');
        this.notificationDropdown = document.getElementById('notificationDropdown');
        this.init();
    }

    init() {
        if (!this.notificationBell) return;
        
        // Fetch unread count on page load
        this.updateNotificationCount();
        
        // Poll for new notifications every 30 seconds
        setInterval(() => {
            this.updateNotificationCount();
        }, 30000);
        
        // Fetch recent notifications when bell is clicked
        this.notificationBell.addEventListener('click', (e) => {
            e.preventDefault();
            this.fetchRecentNotifications();
        });
    }

    updateNotificationCount() {
        fetch('/notifications/api/unread-count/')
            .then(response => response.json())
            .then(data => {
                if (data.count > 0) {
                    this.notificationBadge.textContent = data.count;
                    this.notificationBadge.classList.remove('d-none');
                } else {
                    this.notificationBadge.classList.add('d-none');
                }
            })
            .catch(error => console.error('Error fetching notification count:', error));
    }

    fetchRecentNotifications() {
        fetch('/notifications/api/recent/')
            .then(response => response.json())
            .then(data => {
                this.renderNotifications(data.notifications);
            })
            .catch(error => console.error('Error fetching notifications:', error));
    }

    renderNotifications(notifications) {
        if (!this.notificationDropdown) return;
        
        if (notifications.length === 0) {
            this.notificationDropdown.innerHTML = `
                <div class="dropdown-item text-center text-muted py-3">
                    <i class="fas fa-inbox"></i>
                    <p class="mb-0 mt-2">No new notifications</p>
                </div>
            `;
            return;
        }

        let html = '';
        notifications.forEach(notif => {
            const readClass = notif.is_read ? 'bg-white' : 'bg-light';
            html += `
                <a href="${notif.link}" class="dropdown-item ${readClass} notification-item" data-id="${notif.id}">
                    <div class="d-flex align-items-start">
                        <div class="flex-grow-1">
                            <strong>${notif.title}</strong>
                            <p class="mb-0 small text-muted">${notif.message}</p>
                            <small class="text-muted">${notif.created_at}</small>
                        </div>
                        ${!notif.is_read ? '<span class="badge bg-primary ms-2">New</span>' : ''}
                    </div>
                </a>
            `;
        });

        html += `
            <div class="dropdown-divider"></div>
            <a href="/notifications/" class="dropdown-item text-center text-primary">
                View All Notifications
            </a>
        `;

        this.notificationDropdown.innerHTML = html;
        
        // Mark as read on click
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const notifId = e.currentTarget.dataset.id;
                this.markAsRead(notifId);
            });
        });
    }

    markAsRead(notificationId) {
        fetch(`/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                this.updateNotificationCount();
            }
        })
        .catch(error => console.error('Error marking notification as read:', error));
    }
}

// Form Validation Enhancement
class FormValidator {
    constructor(formSelector) {
        this.form = document.querySelector(formSelector);
        if (this.form) {
            this.init();
        }
    }

    init() {
        this.form.addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.form.classList.add('was-validated');
        }, false);

        // Real-time validation
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });
    }

    validateForm() {
        return this.form.checkValidity();
    }

    validateField(field) {
        const isValid = field.checkValidity();
        const feedback = field.parentElement.querySelector('.invalid-feedback');
        
        if (!isValid) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
        
        return isValid;
    }
}

// Image Preview
function setupImagePreviews() {
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    let preview = input.parentElement.querySelector('.image-preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.className = 'image-preview img-thumbnail mt-2';
                        preview.style.maxWidth = '200px';
                        input.parentElement.appendChild(preview);
                    }
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    });
}

// Confirm Dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Toast Notifications
class ToastManager {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1050';
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        this.container.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: duration
        });
        
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    success(message) {
        this.show(message, 'success');
    }

    error(message) {
        this.show(message, 'danger', 5000);
    }

    warning(message) {
        this.show(message, 'warning');
    }

    info(message) {
        this.show(message, 'info');
    }
}

// Initialize Toast Manager
const toastManager = new ToastManager();

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href !== '#!') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Search functionality with debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize components on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize notification manager
    if (document.getElementById('notificationBell')) {
        new NotificationManager();
    }

    // Initialize form validators
    new FormValidator('form');

    // Setup image previews
    setupImagePreviews();

    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Table search functionality
    const searchInputs = document.querySelectorAll('[data-table-search]');
    searchInputs.forEach(input => {
        const tableId = input.dataset.tableSearch;
        const table = document.getElementById(tableId);
        
        if (table) {
            input.addEventListener('keyup', debounce(function(e) {
                const searchTerm = e.target.value.toLowerCase();
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            }, 300));
        }
    });
});

// Export functions for global use
window.toastManager = toastManager;
window.confirmAction = confirmAction;