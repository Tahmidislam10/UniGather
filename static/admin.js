// Fetches the requested cookie
function getCookie(name) {
    const value = `; ${document.cookie}`; // Normalises the format
    const parts = value.split(`; ${name}=`); // Splits the cookie
    if (parts.length === 2) return parts.pop().split(";").shift(); // Keeps desired data
    return null;
}

// Fetches all user and displays them
async function loadUsers() {
    const res = await fetch("/api/users");
    const users = await res.json();
    const tbody = document.getElementById("user-table-body");
    tbody.innerHTML = "";

    for (const user of users) {
        const row = document.createElement("tr");
        let actionBtn = "";

        if (user.role === "student") {
            actionBtn = `<button class="button" onclick="changeRole('${user.id}', 'staff')">Promote to Staff</button>`;
        } else if (user.role === "staff") {
            actionBtn = `<button class="button" onclick="changeRole('${user.id}', 'student')" style="background-color: #1e1e1e; color: white;">Demote to Student</button>`;
        } else {
            actionBtn = "<em>Admin (Protected)</em>";
        }

        row.innerHTML = `
                    <td style="padding: 10px; border: 1px solid #ddd;">${user.full_name}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${user.email}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>${user.role}</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${actionBtn}</td>
                `;
        tbody.appendChild(row);
    }
}

// Updates the user's role
async function changeRole(userId, newRole) {
    if (
        !confirm(
            `Are you sure you want to change this user's role to ${newRole}?`
        )
    )
        return;

    const res = await fetch("/update-role", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId: userId, newRole: newRole }),
    });

    if (res.ok) {
        alert("Role updated successfully!");
        loadUsers(); // Refresh table
    } else {
        alert(await res.text());
    }
}

// Waits for HTML document to finish loading
document.addEventListener("DOMContentLoaded", () => {
    loadUsers();
});
