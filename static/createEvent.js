// Handles the submission of a form for the creation of a new event
async function createEvent(event) {
    event.preventDefault();

    const formData = new FormData(event.target); // Obtains the data from the form that triggered this event call

    try {
        const response = await fetch("/create/submit-event", {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            alert("Event created successfully!");
            window.location.href = "/events-page"; // Redirects to event page to view created event
        } else {
            alert(await response.text());
        }
    } catch (err) {
        console.error("Event Submission Error: ", err);
        alert("Event Submission Error.");
    }
}

// Waits for HTML document to finish loading.
document.addEventListener("DOMContentLoaded", () => {
    for (const form of document.querySelectorAll(".create-event-form")) {
        form.addEventListener("submit", createEvent); // Adds listener waiting for submission event
    }
});
