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
    const loginForm = document.getElementById("login-form");
    const usernameInput =
        document.getElementById("username") ||
        loginForm?.querySelector('input[type="text"]');
    const passwordInput = document.getElementById("password");
    const submitBtn =
        document.getElementById("submit-btn") ||
        loginForm?.querySelector("button.login");
    const registerBtn =
        document.getElementById("register-btn") ||
        loginForm?.querySelector("button.register");
    const errorContainer = document.getElementById("error-messages");

    if (usernameInput) {
        if (!usernameInput.id) {
            usernameInput.id = "username";
        }
        usernameInput.required = true;
        usernameInput.autocomplete = "username";
        usernameInput.placeholder = "Username";
    }

    if (passwordInput) {
        passwordInput.required = true;
        passwordInput.autocomplete = "current-password";
    }

    buttons.forEach(function (button) {
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

    if (registerBtn) {
        registerBtn.addEventListener("click", function (event) {
            event.preventDefault();
            window.location.href = "/signup/";
        });
    }

    if (!loginForm || !usernameInput || !passwordInput || !submitBtn) return;

    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        if (errorContainer) errorContainer.textContent = "";
        if (window.location.protocol === "file:") {
            if (errorContainer) {
                errorContainer.textContent =
                    "Open this page via HTTP (for example http://127.0.0.1:5500), not file://.";
            }
            return;
        }

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username || !password) {
            if (errorContainer) {
                errorContainer.textContent = "Username and password are required.";
            }
            return;
        }

        const originalLabel = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = "Loading...";

        try {
            const response = await fetch(`${API_BASE}/api/accounts/login/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                const errorText =
                    data?.errors?.detail || data?.message || "Login failed.";
                if (errorContainer) errorContainer.textContent = errorText;
                return;
            }

            localStorage.setItem("nutfitAuth", "1");
            localStorage.setItem("nutfitUser", JSON.stringify(data.user || {}));
            window.location.href = "/profile/";
        } catch (error) {
            if (errorContainer) {
                errorContainer.textContent = "Server connection error.";
            }
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalLabel;
        }
    });
});
