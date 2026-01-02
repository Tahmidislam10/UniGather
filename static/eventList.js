let allEvents = [];

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

// Renders the events to be displayed
function displayEvents(events, expandedEventsIds = []) {
    const eventsSection = document.getElementById("events-list");
    eventsSection.innerHTML = ""; // Resets to a clean slate

    if (events.length === 0) {
        eventsSection.innerHTML = "<p>No events found.</p>";
        return;
    }

    const currentUserId = getCookie("user_id");

    for (const event of events) {
        const isBooked =
            event.booked_users && event.booked_users.includes(currentUserId); // Checks if current user has booked this event
        const wasExpanded = expandedEventsIds.includes(event.id); // Checks if event was previously expanded by the user
        const eventDiv = document.createElement("div");

        eventDiv.className = wasExpanded ? "event-item toggled" : "event-item"; // Expands if previously expanded
        eventDiv.setAttribute("data-eventId", event.id); // Stores event ID for future use

        // Writes the HTML. NOTE: HTML comments below do not appear as green within VSCode
        eventDiv.innerHTML = `
                        <!-- ALWAYS-VISIBLE EVENT SUMMARY/HEADER -->
                        <div class="event-main">
                            <h3>${event.event_name}</h3>
                            <p><b>Host:</b> ${event.host_name}</p>
                            <p><b>Date:</b> ${event.event_date}  <b>Time:</b> ${
            event.event_time
        }</p>
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
                                    <p><b>Date:</b> ${event.event_date}</p>
                                    <p><b>Time:</b> ${event.event_time}</p>
                                    <p><b>Location:</b> ${event.event_loc}</p>
                                </div>
                            </div>

                            <div class="event-details-wide">
                                <p><b>Description:</b></p>
                                <p style="white-space: pre-wrap">${
                                    event.event_desc
                                }</p>
                            </div>

                            <!-- DYNAMIC BOOK/CANCEL BUTTON -->
                            <button 
                                class="${
                                    isBooked ? "cancel-button" : "book-button"
                                }"
                                onclick="${
                                    isBooked
                                        ? `cancelBooking('${event.id}')`
                                        : `makeBooking('${event.id}')`
                                }; event.stopPropagation();">
                                ${isBooked ? "Cancel Booking" : "Book Event"}
                            </button>
                        </div>
                    `;

        eventDiv.onclick = () => eventDiv.classList.toggle("toggled"); // Detects click and expands/collapses the event details
        eventsSection.appendChild(eventDiv); // Adds the new event div to the event section
    }
}

// Fetches the requested cookie
function getCookie(name) {
    const match = document.cookie.match(
        new RegExp("(^| )" + name + "=([^;]+)")
    );
    return match ? decodeURIComponent(match[2]) : null;
}
