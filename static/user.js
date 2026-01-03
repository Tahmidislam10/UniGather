// Fetches the requested cookie
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
}

document.addEventListener("DOMContentLoaded", function () {
    const username = getCookie("username");
    const role = getCookie("role");

    const userStatusDiv = document.getElementById("user-status");
    const displayUsername = document.getElementById("display-username");
    const loginNavItem = document.getElementById("nav-login");
    const adminNavItem = document.getElementById("nav-admin");

    // Check if user is logged in
    if (username && username !== "") {
        // Show welcome message and set name
        if (userStatusDiv) userStatusDiv.style.display = "block";
        if (displayUsername)
            displayUsername.innerText = decodeURIComponent(username);

        // Hide Login link (user is already authenticated)
        if (loginNavItem) loginNavItem.style.display = "none";

        // Show Staff-only navigation links
        if (role === "staff") {
            if (adminNavItem) adminNavItem.style.display = "block";
        }
    } else {
        // Ensure Login / Register is visible if NOT logged in
        if (loginNavItem) loginNavItem.style.display = "block";
    }
});
