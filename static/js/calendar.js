// Event Calendar Integration using FullCalendar

document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('eventCalendar');
    
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,listMonth'
            },
            events: function(info, successCallback, failureCallback) {
                fetch('/events/api/calendar-events/')
                    .then(response => response.json())
                    .then(data => {
                        successCallback(data);
                    })
                    .catch(error => {
                        console.error('Error fetching events:', error);
                        failureCallback(error);
                    });
            },
            eventClick: function(info) {
                info.jsEvent.preventDefault();
                if (info.event.url) {
                    window.location.href = info.event.url;
                }
            },
            eventDidMount: function(info) {
                // Add tooltip
                tippy(info.el, {
                    content: info.event.title,
                    placement: 'top'
                });
            },
            height: 'auto',
            themeSystem: 'bootstrap5'
        });
        
        calendar.render();
    }
});