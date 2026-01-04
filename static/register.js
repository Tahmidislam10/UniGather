// Verifies that the provided email is an academic email address
function validateEmail() {
    const email = document.querySelector('input[name="email"]').value;
    const error = document.getElementById("error-msg"); // For displaying any errors

    if (!email.endsWith(".ac.uk")) {
        error.innerText =
            "Registration is restricted to academic (.ac.uk) email addresses.";
        error.style.display = "block";
        return false;
    }

    error.style.display = "none";
    return true;
}
