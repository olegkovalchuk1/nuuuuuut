const API_BASE =
    window.location.origin === "http://127.0.0.1:8000" ||
    window.location.origin === "http://localhost:8000"
        ? ""
        : "http://127.0.0.1:8000";

function getCookieValue(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (const cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith(`${name}=`)) {
            return decodeURIComponent(trimmed.substring(name.length + 1));
        }
    }
    return "";
}

async function logout() {
    const csrfToken = getCookieValue("csrftoken");
    try {
        await fetch(`${API_BASE}/api/accounts/logout/`, {
            method: "POST",
            credentials: "include",
            headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
        });
    } catch (error) {
        console.error("Logout failed:", error);
    } finally {
        localStorage.removeItem("nutfitAuth");
        localStorage.removeItem("nutfitUser");
        window.location.href = "/login/";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const authLink = document.getElementById("uvijty");
    if (!authLink) return;

    if (localStorage.getItem("nutfitAuth") === "1") {
        authLink.textContent = "Logout";
    }

    authLink.addEventListener("click", async (event) => {
        if (localStorage.getItem("nutfitAuth") !== "1") return;
        event.preventDefault();
        await logout();
    });
});
