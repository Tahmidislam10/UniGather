let eventsChart, attendeesChart;

function renderCharts(labels, eventsData, attendeesData) {
    if (eventsChart) eventsChart.destroy();
    if (attendeesChart) attendeesChart.destroy();

    eventsChart = new Chart(document.getElementById("eventsChart"), {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Events Hosted",
                data: eventsData
            }]
        },
        options: {
            responsive: true
        }
    });

    attendeesChart = new Chart(document.getElementById("attendeesChart"), {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Attendees",
                data: attendeesData
            }]
        },
        options: {
            responsive: true
        }
    });
}

function loadWeekly() {
    fetch("/api/analytics/weekly")
        .then(res => res.json())
        .then(data => {
            renderCharts(data.weeks, data.events, data.attendees);
        });
}

function loadDaily() {
    fetch("/api/analytics/daily")
        .then(res => res.json())
        .then(data => {
            renderCharts(data.days, data.events, data.attendees);
        });
}

document.getElementById("weeklyBtn").onclick = loadWeekly;
document.getElementById("dailyBtn").onclick = loadDaily;

// Default view on page load
loadWeekly();
