// Fetches the requested cookie
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
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

    // Check if user is logged in
    if (username && username !== "") {
        // Show welcome message and set name
        if (userStatusDiv) userStatusDiv.style.display = "block";
        if (usernameText) usernameText.innerText = decodeURIComponent(username);

        // Hide Login link (user is already authenticated)
        if (loginButton) loginButton.style.display = "none";
        if (logoutButton) logoutButton.style.display = "block";

        // Show admin button
        if (role === "admin") {
            if (adminButton) adminButton.style.display = "block";
        } else {
            if (adminButton) adminButton.style.display = "none";
        }
    } else {
        if (userStatusDiv) userStatusDiv.style.display = "none"; // Hides User Status

        if (loginButton) loginButton.style.display = "block"; // Reenables Login / Register
        if (logoutButton) logoutButton.style.display = "none"; // Hides Logout
    }
});
