// This JavaScript file is not used solo, but is called with events.js or index.js.

let allEvents = []; // All events that could be displayed

// Fetches the requested cookie
function getCookie(name) {
    const value = `; ${document.cookie}`; // Normalises the format
    const parts = value.split(`; ${name}=`); // Splits the cookie
    if (parts.length === 2) return parts.pop().split(";").shift(); // Keeps desired data
    return null;
}

// Returns the event IDs of events currently expanded by the user
function getExpandedEventIds() {
    const expandedEvents = document.querySelectorAll(".event-item.toggled"); // Gets all expanded events

    const expandedEventsIds = [];
    for (const event of expandedEvents)
        expandedEventsIds.push(event.getAttribute("data-eventId")); // Obtains the event IDs

    return expandedEventsIds;
}

// Searches current event list - intentionally does not call for up-to-date events list
function searchEvents() {
    const searchInput = document
        .getElementById("search-input")
        .value.toLowerCase()
        .trim(); // Non-case-sensitive searching and removes whitespace

    // For empty searches, display unsearched list of events
    if (searchInput === "") {
        displayEvents(allEvents, getExpandedEventIds());
        return;
    }

    const filteredEvents = allEvents.filter(function (event) {
        return event.event_name.toLowerCase().includes(searchInput);
    }); // Filters out events not including the search input
    displayEvents(filteredEvents, getExpandedEventIds());
}

// Helper to calculate the time remaining/past text to display
function getTime(full, date, time) {
    const eventDate = new Date(`${date}T${time}`);
    const currentDate = new Date();
    const difference = eventDate - currentDate;

    const days = Math.floor(Math.abs(difference) / (1000 * 60 * 60 * 24));
    const hours = Math.floor(
        (Math.abs(difference) % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
    );
    const displayedDays = days > 0 ? `${days}d ` : ``; // Does not display if less than 1 day
    const displayedHours = days <= 0 && hours <= 0 ? `<1h` : `${hours}h`;

    // Checks whether to display full (for details) or short (header) time remaining
    // Then checks if the event is in the past (negative time) before deciding how to format
    if (full) {
        if (difference > 0) {
            return `<b>In:</b> ${displayedDays}${displayedHours}`;
        } else {
            return `<b>Passed:</b> ${displayedDays}${displayedHours} ago`;
        }
    } else {
        if (difference > 0) {
            return `<i>(${displayedDays}${displayedHours})</i>`;
        } else {
            return `<i><b>passed</b></i>`;
        }
    }
}

// Renders the events to be displayed
function displayEvents(events, expandedEventsIds = []) {
    const eventsSection = document.getElementById("events-list");
    eventsSection.innerHTML = ""; // Resets to a clean slate

    if (events.length === 0) {
        eventsSection.innerHTML = "<p>No events to display.</p>";
        return;
    }

    const userId = getCookie("user_id");
    const userRole = getCookie("role");

    for (const event of events) {
        const isStaff = userRole === "staff" || userRole === "admin"; // Checks if user is a staff member
        const isBooked =
            event.booked_users && event.booked_users.includes(userId); // Checks if current user has booked this event
        const isWaitlisted =
            event.waitlist_users && event.waitlist_users.includes(userId);
        const wasExpanded = expandedEventsIds.includes(event.id); // Checks if event was previously expanded by the user
        const eventDiv = document.createElement("div");

        eventDiv.className = wasExpanded ? "event-item toggled" : "event-item"; // Expands if previously expanded
        eventDiv.setAttribute("data-eventId", event.id); // Stores event ID for future use

        // Writes the HTML. NOTE: HTML comments below do not appear as green within VSCode
        // Formatted using "Prettier" VSCode Extension
        eventDiv.innerHTML = `
                        <!-- ALWAYS-VISIBLE EVENT SUMMARY/HEADER -->
                        <div class="event-main">
                            <h3>${event.event_name}</h3>
                            <p><b>Host:</b> ${event.host_name}</p>
                            <p><b>Date:</b> ${event.event_date} ${
            event.event_time
        }</p>
        <p>${getTime(false, event.event_date, event.event_time)}</p>
                            <span class="toggle-icon">▼</span>
                        </div>
                        
                        <!-- SECTION BELOW EXPANDS/COLLAPSES UPON CLICK -->
                        <div class="event-details">
                            <div class="event-details-wide">
                                <p><b>Full Event Title:</b> ${
                                    event.event_name
                                }</p>
                            </div>

                            <div class="event-details-grid">
                                <div>
                                    <p><b>Host Name:</b> ${event.host_name}</p>
                                    <p><b>Host Email:</b> ${
                                        event.host_email
                                    }</p>
                                    <p><b>Availability:</b> ${
                                        event.event_cap -
                                        event.booked_users.length
                                    }/${event.event_cap} ${
            event.booked_users.length < event.event_cap
                ? `<i>spaces remaining</i>`
                : `<i><b>fully booked</b></i>`
        }</p>
                                </div>

                                <div>
                                    <p><b>Date:</b> ${event.event_date} ${
            event.event_time
        }</p>
                                    <p>${getTime(
                                        true,
                                        event.event_date,
                                        event.event_time
                                    )}</p>
                                    <p><b>Location:</b> ${event.event_loc}</p>
                                </div>
                            </div>

                            <div class="event-details-wide">
                                <p><b>Description:</b></p>
                                <p style="white-space: pre-wrap">${
                                    event.event_desc
                                }</p>
                            </div>

                            <!-- DYNAMIC BOOK/CANCEL/WAITLIST BUTTON -->
                            ${
                                isBooked
                                    ? `
                                <button 
                                    class="cancel-button"
                                    onclick="cancelBooking('${event.id}'); event.stopPropagation();">
                                    Cancel Booking
                                </button>
                                `
                                    : isWaitlisted
                                    ? `
                                <button 
                                    class="cancel-button"
                                    onclick="leaveWaitlist('${event.id}'); event.stopPropagation();">
                                    Leave Waitlist
                                </button>
                                `
                                    : `
                                <button 
                                    class="book-button"
                                    onclick="makeBooking('${event.id}'); event.stopPropagation();">
                                    Book Event
                                </button>
                                `
                            }


                             <!-- DOWNLOAD PDF BUTTON -->
                            ${
                                isBooked
                                    ? `
                                <button 
                                    class="download-button"
                                    onclick="downloadBooking('${event.id}'); event.stopPropagation();">
                                    Download Booking (PDF)
                                </button>
                            `
                                    : ``
                            }

                             <!-- STAFF VIEW ATTENDEES BUTTON -->
                             ${
                                 isStaff
                                     ? `
                                <button 
                                    class="attendee-button"
                                    onclick="viewAttendees('${event.id}'); event.stopPropagation();">
                                    View Attendees
                                </button>

                                <button 
                                    class="delete-button"
                                    onclick="deleteEvent('${event.id}'); event.stopPropagation();">
                                    Delete Event
                                </button>
                            `
                                     : ``
                             }
                        </div>
                    `;

        eventDiv.onclick = () => eventDiv.classList.toggle("toggled"); // Detects click and expands/collapses the event details
        eventsSection.appendChild(eventDiv); // Adds the new event div to the event section
    }
}

// Downloads booking confirmation PDF
function downloadBooking(eventId) {
    window.location.href = `/booking-confirmation/${eventId}`;
}

async function leaveWaitlist(eventId) {
    if (!confirm("Are you sure you want to leave the waitlist?")) return;

    try {
        const res = await fetch("/cancel-waitlist", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ eventId }),
        });

        alert(await res.text());
        getEvents(); // Refreshes the events list
    } catch (err) {
        console.error("Leave waitlist error:", err);
        alert("Failed to leave waitlist");
    }
}

async function viewAttendees(eventId) {
    try {
        const res = await fetch("/view-attendees", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ eventId }),
        });

        alert(await res.text());
        getEvents(); // Refreshes the events list
    } catch (err) {
        console.error("viewAttendees():", err);
        alert("Failed to obtain attendees");
    }
}

async function deleteEvent(eventId) {
    if (!confirm("Are you sure you want to delete this event?")) return;

    try {
        const res = await fetch("/delete-event", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ eventId }),
        });

        alert(await res.text());
        getEvents(); // Refreshes the events list
    } catch (err) {
        console.error("deleteEvent():", err);
        alert("Failed to delete event");
    }
}
