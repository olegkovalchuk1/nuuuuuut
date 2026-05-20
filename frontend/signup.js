const links = document.querySelectorAll(".menu-link");
const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

links.forEach((link) => {
    link.addEventListener("click", function () {
        links.forEach((l) => l.classList.remove("active"));
        this.classList.add("active");
    });
});

function togglePassword() {
    const password = document.getElementById("password");
    if (!password) return;
    password.type = password.type === "password" ? "text" : "password";
}

document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll("button");
    const signupForm = document.getElementById("signup-form");
    const submitBtn = document.getElementById("submit-btn");
    const errorContainer = document.getElementById("error-messages");
    const loginBtn = document.getElementById("login-btn");

    buttons.forEach((button) => {
        button.addEventListener("mousedown", function () {
            button.style.filter = "brightness(80%)";
        });
        button.addEventListener("mouseup", function () {
            button.style.filter = "brightness(100%)";
        });
        button.addEventListener("mouseleave", function () {
            button.style.filter = "brightness(100%)";
        });
    });

    if (loginBtn) {
        loginBtn.addEventListener("click", (e) => {
            e.preventDefault();
            window.location.href = "/login/";
        });
    }

    if (!signupForm || !submitBtn || !errorContainer) return;

    signupForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorContainer.innerHTML = "";

        const username = document.getElementById("username")?.value.trim();
        const email = document.getElementById("email")?.value.trim();
        const password = document.getElementById("password")?.value;

        if (!username || !email || !password) {
            errorContainer.innerText = "Fill all fields.";
            return;
        }

        submitBtn.disabled = true;
        const originalLabel = submitBtn.innerText;
        submitBtn.innerText = "Loading...";

        try {
            const response = await fetch(`${API_BASE}/api/accounts/register/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ username, email, password }),
            });

            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                displayErrors(data, errorContainer);
                return;
            }

            alert("Registration successful.");
            window.location.href = "/login/";
        } catch (error) {
            errorContainer.innerText = "Server connection error.";
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = originalLabel;
        }
    });
});

function displayErrors(errors, container) {
    container.innerHTML = "";
    if (!errors || typeof errors !== "object") {
        container.innerText = "Registration failed.";
        return;
    }
    Object.entries(errors).forEach(([field, messages]) => {
        const msgText = Array.isArray(messages) ? messages.join(" ") : String(messages);
        const p = document.createElement("p");
        p.innerText = `${field}: ${msgText}`;
        container.appendChild(p);
    });
}
