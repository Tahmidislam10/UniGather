let eventsChart, attendeesChart;

function renderCharts(labels, eventsData, attendeesData) {
    // Deletes any existing previous charts
    if (eventsChart) eventsChart.destroy();
    if (attendeesChart) attendeesChart.destroy();

    // Finds the eventsCharts element and creates a fresh chart
    eventsChart = new Chart(document.getElementById("eventsChart"), {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Events Hosted",
                    data: eventsData,
                },
            ],
        },
        options: {
            responsive: true,
        },
    });

    // Finds the attendeesChart element and creates a fresh chart
    attendeesChart = new Chart(document.getElementById("attendeesChart"), {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Attendees",
                    data: attendeesData,
                },
            ],
        },
        options: {
            responsive: true,
        },
    });
}

// Summary stats at the top of the page
function loadSummaryStats() {
    fetch("/api/analytics/summary")
        .then((res) => res.json())
        .then((data) => {
            document.getElementById("fillRate").innerText =
                data.average_fill_rate + "%";

            document.getElementById(
                "bookingRatio"
            ).innerText = `${data.booked} booked / ${data.waitlisted} waitlisted`;

            document.getElementById("cancellations").innerText =
                data.cancellations;
        });
}

// Fetches weekly statistics
function loadWeekly() {
    fetch("/api/analytics/weekly")
        .then((res) => res.json())
        .then((data) => {
            renderCharts(data.weeks, data.events, data.attendees); // Reloads the charts
        });
}

// Fetches daily statistics
function loadDaily() {
    fetch("/api/analytics/daily")
        .then((res) => res.json())
        .then((data) => {
            renderCharts(data.days, data.events, data.attendees); // Reloads the charts
        });
}

// Waits for HTML document to finish loading
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("weeklyBtn").onclick = loadWeekly;
    document.getElementById("dailyBtn").onclick = loadDaily;

    // Default view on page load
    loadSummaryStats();
    loadWeekly();
});
