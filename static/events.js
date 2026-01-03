// Fetches an updated events list from the backend
async function getEvents() {
    try {
        allEvents = await (await fetch("/events")).json(); // Fetches events from backend
        displayEvents(allEvents, getExpandedEventIds());
    } catch (err) {
        console.error("getEvents() error: " + err);
        document.getElementById("events-list").innerHTML =
            "<p>Error loading events.</p>";
    }
}

// Calls the backend to make a booking for the event
async function makeBooking(eventId) {
    try {
        const res = await fetch("/book-event", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ eventId }),
        });

        alert(await res.text());
        getEvents(); // Refreshes the events list
    } catch (err) {
        console.error("Booking error:", err);
        alert("Failed to book event");
    }
}

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
        getEvents(); // Refreshes the events list
    } catch (err) {
        console.error("Cancel error:", err);
        alert("Failed to cancel booking");
    }
}

// Checks the user's permissions. Note that this is just a preliminary frontend check.
// Backend code checks again to ensure that the user has the correct permissions.
function checkPermission(event) {
    const role = getCookie("role");

    if (role !== "staff" && role !== "admin") {
        event.preventDefault(); // If not staff, prevents redirect to event creation page
        alert("You must be logged in to create an event.");
    }
}

// Waits for HTML document to finish loading
document.addEventListener("DOMContentLoaded", function () {
    // Finds the create event button and adds a click event listener
    const createButton = document.getElementById("create-event-button");
    if (createButton) createButton.addEventListener("click", checkPermission);

    getEvents(); // Loads events to populate the page
});
