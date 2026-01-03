// Fetches the user's booked events from the backend
async function getBookedEvents() {
    // Checks that the user is signed in for their events to be fetched
    if (!getCookie("username")) {
        document.getElementById("events-list").innerHTML =
            "<p>You must be logged in to display your upcoming events.</p>";
        return;
    }

    try {
        allEvents = await (await fetch("/reminders")).json(); // Fetches events from backend
        displayEvents(allEvents, getExpandedEventIds());
    } catch (err) {
        console.error("getBookedEvents() error: " + err);
        document.getElementById("events-list").innerHTML =
            "<p>Error loading events.</p>";
    }
}

// Empty function - should never be called
async function makeBooking(eventId) {}

// Calls the backend to cancel the booking for an event
async function cancelBooking(eventId) {
    if (!confirm("Are you sure that you wish to cancel this booking?")) return;

    try {
        const res = await fetch("/cancel-booking", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ eventId }),
        });

        alert(await res.text());
        getBookedEvents(); // Refreshes the booked events list
    } catch (err) {
        console.error("Cancel error:", err);
        alert("Failed to cancel booking");
    }
}

getBookedEvents(); // Loads booked events to populate the page
