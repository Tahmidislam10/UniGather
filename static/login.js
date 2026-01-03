// Submits login form to the backend
async function login(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    try {
        const response = await fetch("/login", {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            window.location.href = "/events-page";
        } else {
            alert(await response.text());
        }
    } catch (err) {
        console.error("Login Error: ", err);
        alert("Login Error.");
    }
}

// Waits for HTML document to finish loading
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("login-form").addEventListener("submit", login);
});
