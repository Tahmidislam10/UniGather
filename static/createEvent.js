fetch("/admin/analytics")
    .then(res => res.json())
    .then(data => {

        const eventDays = Object.keys(data.events_per_day);
        const eventCounts = Object.values(data.events_per_day);

        const attendanceDays = Object.keys(data.attendees_per_day);
        const attendanceCounts = Object.values(data.attendees_per_day);

        new Chart(document.getElementById("eventsChart"), {
            type: "bar",
            data: {
                labels: eventDays,
                datasets: [{
                    label: "Events Hosted Per Day",
                    data: eventCounts
                }]
            }
        });

        new Chart(document.getElementById("attendanceChart"), {
            type: "line",
            data: {
                labels: attendanceDays,
                datasets: [{
                    label: "People Attending Events Per Day",
                    data: attendanceCounts
                }]
            }
        });

    })
    .catch(err => console.error("Analytics error:", err));
