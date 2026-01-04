// Fetches the requested cookie
function getCookie(name) {
    const value = `; ${document.cookie}`; // Normalises the format
    const parts = value.split(`; ${name}=`); // Splits the cookie
    if (parts.length === 2) return parts.pop().split(";").shift(); // Keeps desired data
    return null;
}

// Waits for HTML document to finish loading
document.addEventListener("DOMContentLoaded", function () {
    const username = getCookie("username");
    const role = getCookie("role");

    const userStatusDiv = document.getElementById("user-status");
    const usernameText = document.getElementById("username-text");
    const loginButton = document.getElementById("nav-login");
    const logoutButton = document.getElementById("nav-logout");
    const adminButton = document.getElementById("admin-link");
    const analyticsButton = document.getElementById("analytics-link");

    // Check if user is logged in
    if (username && username !== "") {
        // The if statements below check that the element was found before attempting changes

        // Show welcome message and sets name
        if (userStatusDiv) userStatusDiv.style.display = "block";
        if (usernameText) usernameText.innerText = decodeURIComponent(username);

        // Hide Login link (user is already authenticated)
        if (loginButton) loginButton.style.display = "none";
        if (logoutButton) logoutButton.style.display = "block";

        // Show role-specific buttons
        if (role === "admin") {
            // Admin can see both buttons
            if (adminButton) adminButton.style.display = "block";
            if (analyticsButton) analyticsButton.style.display = "inline-block";
        } else if (role === "staff") {
            // Only staff, only displays analytics button
            if (adminButton) adminButton.style.display = "none";
            if (analyticsButton) analyticsButton.style.display = "inline-block";
        } else {
            // Not staff or admin, so both buttons hidden
            if (adminButton) adminButton.style.display = "none";
            if (analyticsButton) analyticsButton.style.display = "none";
        }
    } else {
        if (userStatusDiv) userStatusDiv.style.display = "none"; // Hides User Status

        if (loginButton) loginButton.style.display = "block"; // Reenables Login / Register
        if (logoutButton) logoutButton.style.display = "none"; // Hides Logout
    }
});
