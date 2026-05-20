const API_BASE =
    window.location.origin === "http://127.0.0.1:8000" ||
    window.location.origin === "http://localhost:8000"
        ? ""
        : "http://127.0.0.1:8000";

const notifications = [];

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

function setupNav() {
    const home = document.getElementById("golovna");
    const auth = document.getElementById("uvijty");
    const profile = document.getElementById("osobistiy-kabinet");
    const current = document.getElementById("spovishennya");

    if (home) home.addEventListener("click", (e) => { e.preventDefault(); window.location.href = "/profile/"; });
    if (profile) profile.addEventListener("click", (e) => { e.preventDefault(); window.location.href = "/profile/"; });
    if (current) current.addEventListener("click", (e) => { e.preventDefault(); window.location.href = "/notifications/"; });

    if (auth) {
        if (localStorage.getItem("nutfitAuth") === "1") auth.textContent = "Logout";
        auth.addEventListener("click", async (e) => {
            if (localStorage.getItem("nutfitAuth") !== "1") return;
            e.preventDefault();
            const csrfToken = getCookieValue("csrftoken");
            try {
                await fetch(`${API_BASE}/api/accounts/logout/`, {
                    method: "POST",
                    credentials: "include",
                    headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
                });
            } catch (error) {
                console.error(error);
            } finally {
                localStorage.removeItem("nutfitAuth");
                localStorage.removeItem("nutfitUser");
                window.location.href = "/login/";
            }
        });
    }
}

function toggleBlock(header) {
    const block = header.parentElement;
    block.classList.toggle("active");
}

function createCard(item) {
    const el = document.createElement("div");
    el.className = "card" + (item.read ? " read" : "");
    el.textContent = item.text;
    el.onclick = async () => {
        if (item.read) return;
        await markAsRead(item.id);
        item.read = true;
        renderNotifications();
    };
    return el;
}

function renderNotifications() {
    const allBlock = document.getElementById("all");
    const importantBlock = document.getElementById("important");
    const unreadBlock = document.getElementById("unread");
    if (!allBlock || !importantBlock || !unreadBlock) return;

    allBlock.innerHTML = "";
    importantBlock.innerHTML = "";
    unreadBlock.innerHTML = "";

    notifications.forEach((item) => {
        allBlock.appendChild(createCard(item));
        if (item.important) importantBlock.appendChild(createCard(item));
        if (!item.read) unreadBlock.appendChild(createCard(item));
    });
}

async function fetchNotifications() {
    const response = await fetch(`${API_BASE}/api/notifications`, {
        credentials: "include",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    notifications.length = 0;
    (data.results || []).forEach((item) => notifications.push(item));
    renderNotifications();
}

async function createNotification(text, important = false, sourceKey = null) {
    const csrfToken = getCookieValue("csrftoken");
    const response = await fetch(`${API_BASE}/api/notifications`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: JSON.stringify({
            text,
            important,
            source_key: sourceKey,
        }),
    });
    if (!response.ok) return;
    const data = await response.json().catch(() => ({}));
    const item = data.notification;
    if (!item) return;
    const index = notifications.findIndex((x) => x.id === item.id);
    if (index >= 0) {
        notifications[index] = item;
    } else {
        notifications.unshift(item);
    }
    renderNotifications();
}

async function markAsRead(id) {
    const csrfToken = getCookieValue("csrftoken");
    await fetch(`${API_BASE}/api/notifications/${id}/read`, {
        method: "POST",
        credentials: "include",
        headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
    });
}

function shouldSendKey(key) {
    const sent = localStorage.getItem(`notif:${key}`);
    if (sent) return false;
    localStorage.setItem(`notif:${key}`, new Date().toISOString());
    return true;
}

function scheduleNotifications() {
    setInterval(async () => {
        const now = new Date();
        const h = now.getHours();
        const m = now.getMinutes();
        const date = now.toISOString().slice(0, 10);

        if (m !== 0) return;

        const queue = [];
        if (h === 8) queue.push({ text: "Сніданок", important: false, key: `${date}-08-breakfast` });
        if (h === 13) queue.push({ text: "Обід", important: false, key: `${date}-13-lunch` });
        if (h === 19) queue.push({ text: "Вечеря", important: false, key: `${date}-19-dinner` });
        if (h === 17) queue.push({ text: "Тренування", important: false, key: `${date}-17-workout` });
        if (h % 3 === 0) queue.push({ text: "Час пити воду", important: true, key: `${date}-${String(h).padStart(2, "0")}-water` });

        for (const item of queue) {
            if (!shouldSendKey(item.key)) continue;
            await createNotification(item.text, item.important, item.key);
        }
    }, 60000);
}

document.addEventListener("DOMContentLoaded", async () => {
    setupNav();
    try {
        await fetchNotifications();
    } catch (error) {
        console.error("Failed to load notifications:", error);
    }
    scheduleNotifications();
});
