const PROFILE_API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

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

function clearProfileAuthState() {
    localStorage.removeItem("nutfitAuth");
    localStorage.removeItem("nutfitUser");
}

async function logoutFromProfile() {
    try {
        const csrfToken = getCookieValue("csrftoken");
        const headers = csrfToken ? { "X-CSRFToken": csrfToken } : {};
        await fetch(`${PROFILE_API_BASE}/api/accounts/logout/`, {
            method: "POST",
            credentials: "include",
            headers,
        });
    } catch (error) {
        console.error("Logout request failed:", error);
    } finally {
        clearProfileAuthState();
        window.location.href = "/login/";
    }
}

function bindTopNav() {
    const homeLink = document.getElementById("golovna");
    const authLink = document.getElementById("uvijty");
    const profileLink = document.getElementById("osobistiy-kabinet");
    let notificationsLink = document.getElementById("spovishennya");
    let statsLink = document.getElementById("statistika");

    if (!statsLink) {
        const nav = document.querySelector("header nav");
        if (nav) {
            statsLink = document.createElement("a");
            statsLink.id = "statistika";
            statsLink.href = "/dashboard/";
            statsLink.textContent = "Статистика";

            notificationsLink = document.getElementById("spovishennya");
            if (notificationsLink) {
                nav.insertBefore(statsLink, notificationsLink);
            } else {
                nav.appendChild(statsLink);
            }
        }
    }

    if (homeLink) {
        homeLink.addEventListener("click", function (event) {
            event.preventDefault();
            window.location.href = "/profile/";
        });
    }

    if (authLink) {
        if (localStorage.getItem("nutfitAuth") === "1") {
            authLink.textContent = "Logout";
        }

        authLink.addEventListener(
            "click",
            async function (event) {
                event.preventDefault();
                if (localStorage.getItem("nutfitAuth") === "1") {
                    await logoutFromProfile();
                    return;
                }
                window.location.href = "/login/";
            },
            true
        );
    }

    if (statsLink) {
        statsLink.addEventListener("click", function (event) {
            event.preventDefault();
            window.location.href = "/dashboard/";
        });
    }

    if (profileLink) {
        profileLink.addEventListener("click", function (event) {
            event.preventDefault();
            window.location.href = "/profile/";
        });
    }

    if (notificationsLink) {
        notificationsLink.addEventListener("click", function (event) {
            event.preventDefault();
            window.location.href = "/notifications/";
        });
    }
}

function loadSection(pageUrl) {
    fetch(pageUrl, { credentials: "include" })
        .then((response) => response.text())
        .then(async (data) => {
            const content = document.getElementById("content");
            if (!content) return;
            applySectionStyles(pageUrl);
            const parser = new DOMParser();
            const doc = parser.parseFromString(data, "text/html");
            const body = doc.querySelector("body");
            if (body) {
                const clonedBody = body.cloneNode(true);
                const nestedHeader = clonedBody.querySelector("header");
                if (nestedHeader) nestedHeader.remove();
                content.innerHTML = clonedBody.innerHTML;
            } else {
                content.innerHTML = data;
            }

            if (pageUrl.includes("/pages/recipes/")) await initRecipes();
            if (pageUrl.includes("/pages/exercise/")) initExercises();
        })
        .catch((error) => console.error("Load section failed:", error));
}

function applySectionStyles(pageUrl) {
    let href = "";
    if (pageUrl.includes("/pages/test/")) href = "/static/test.css";
    if (pageUrl.includes("/pages/exercise/")) href = "/static/exercise.css";
    if (pageUrl.includes("/pages/recipes/")) href = "/static/recipes.css";

    const styleId = "dynamic-section-style";
    let link = document.getElementById(styleId);

    if (!href) {
        if (link) link.remove();
        return;
    }

    if (!link) {
        link = document.createElement("link");
        link.rel = "stylesheet";
        link.id = styleId;
        document.head.appendChild(link);
    }
    link.href = href;
}

function mapGoalToBackend(goalValue) {
    if (goalValue === "lose") return "weight_loss";
    if (goalValue === "gain") return "weight_gain";
    return "maintenance";
}

function formatGoalErrors(errors) {
    if (!errors || typeof errors !== "object") return "";
    return Object.entries(errors)
        .map(([field, messages]) => {
            const joined = Array.isArray(messages)
                ? messages.join(", ")
                : String(messages);
            return `${field}: ${joined}`;
        })
        .join("; ");
}

async function saveGoalToBackend(payload) {
    if (window.location.protocol === "file:") {
        return {
            ok: false,
            error: "Open profile via HTTP, not file://",
        };
    }

    const csrfToken = getCookieValue("csrftoken");
    const headers = {
        "Content-Type": "application/json",
    };
    if (csrfToken) {
        headers["X-CSRFToken"] = csrfToken;
    }

    try {
        const response = await fetch(`${PROFILE_API_BASE}/api/accounts/goal/`, {
            method: "POST",
            credentials: "include",
            headers,
            body: JSON.stringify(payload),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const baseError = data?.message || "Goal save failed.";
            const details = formatGoalErrors(data?.errors);
            return {
                ok: false,
                status: response.status,
                error: details ? `${baseError} ${details}` : baseError,
            };
        }

        return { ok: true, data };
    } catch (error) {
        return {
            ok: false,
            error: "Server connection error while saving goal.",
        };
    }
}

async function calculateAndSaveNorma() {
    const age = parseFloat(document.getElementById("age")?.value);
    const height = parseFloat(document.getElementById("height")?.value);
    const weight = parseFloat(document.getElementById("weight")?.value);
    const genderEl = document.querySelector('input[name="gender"]:checked');
    const activityEl = document.querySelector('input[name="activity"]:checked');
    const goalEl = document.querySelector('input[name="goal"]:checked');

    if (!age || !height || !weight || !genderEl || !activityEl || !goalEl) {
        alert("Please fill in all test fields.");
        return;
    }

    let bmr = (10 * weight) + (6.25 * height) - (5 * age);
    bmr = genderEl.value === "male" ? bmr + 5 : bmr - 161;
    let totalCalories = bmr * parseFloat(activityEl.value);

    if (goalEl.value === "lose") totalCalories -= 300;
    if (goalEl.value === "gain") totalCalories += 300;

    localStorage.setItem("normaCalories", Math.round(totalCalories));
    localStorage.setItem("normaProteins", Math.round((totalCalories * 0.3) / 4));
    localStorage.setItem("normaFats", Math.round((totalCalories * 0.3) / 9));
    localStorage.setItem("normaCarbs", Math.round((totalCalories * 0.4) / 4));

    const goalPayload = {
        age: Math.round(age),
        weight,
        height,
        activity_level: activityEl.dataset.level || activityEl.value,
        goal: mapGoalToBackend(goalEl.value),
        date: new Date().toISOString().slice(0, 10),
    };

    const saveResult = await saveGoalToBackend(goalPayload);
    if (!saveResult.ok) {
        alert(`Saved locally. Backend save failed: ${saveResult.error}`);
    } else {
        alert("Data saved successfully.");
    }

    loadSection("/pages/recipes/");
}

function loadScriptOnce(src) {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
        if (existing.dataset.loaded === "1") return Promise.resolve();
        return new Promise((resolve, reject) => {
            existing.addEventListener("load", () => resolve(), { once: true });
            existing.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)), { once: true });
        });
    }

    return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = src;
        script.async = false;
        script.addEventListener(
            "load",
            () => {
                script.dataset.loaded = "1";
                resolve();
            },
            { once: true }
        );
        script.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)), {
            once: true,
        });
        document.body.appendChild(script);
    });
}

async function initRecipes() {
    displayNorma();
    await loadNutritionTotals();
    try {
        await loadScriptOnce("/static/recipes.js");
        if (typeof window.initRecipesPage === "function") {
            await window.initRecipesPage();
        } else if (typeof window.fetchRecipes === "function") {
            await window.fetchRecipes();
        }
    } catch (error) {
        console.error("Failed to initialize recipes section:", error);
    }
}

function handleWaterClick(clickedCup) {
    const cups = document.querySelectorAll(".cup");
    const index = [...cups].indexOf(clickedCup);
    const isActive = clickedCup.classList.contains("active");

    cups.forEach((cup, i) => {
        cup.classList.toggle("active", !isActive && i <= index);
    });
}

function displayNorma() {
    const calories = document.getElementById("norma-calories-display");
    const proteins = document.getElementById("norma-proteins-display");
    const fats = document.getElementById("norma-fats-display");
    const carbs = document.getElementById("norma-carbs-display");

    if (calories) calories.innerText = `${localStorage.getItem("normaCalories") || 0} ккал`;
    if (proteins) proteins.innerText = `${localStorage.getItem("normaProteins") || 0} г`;
    if (fats) fats.innerText = `${localStorage.getItem("normaFats") || 0} г`;
    if (carbs) carbs.innerText = `${localStorage.getItem("normaCarbs") || 0} г`;
}

function parseNumberFromCell(id) {
    const element = document.getElementById(id);
    if (!element) return 0;
    return parseFloat(String(element.innerText).replace(",", ".")) || 0;
}

async function loadNutritionTotals() {
    try {
        const response = await fetch(`${PROFILE_API_BASE}/api/nutrition/today`, {
            credentials: "include",
        });
        if (!response.ok) return;
        const data = await response.json();

        const totalCalories = document.getElementById("total-calories");
        const totalProteins = document.getElementById("total-proteins");
        const totalFats = document.getElementById("total-fats");
        const totalCarbs = document.getElementById("total-carbs");

        if (totalCalories) totalCalories.innerText = `${Math.round(data.calories || 0)} ккал`;
        if (totalProteins) totalProteins.innerText = `${Math.round(data.protein || 0)} г`;
        if (totalFats) totalFats.innerText = `${Math.round(data.fat || 0)} г`;
        if (totalCarbs) totalCarbs.innerText = `${Math.round(data.carbs || 0)} г`;
    } catch (error) {
        console.error("Failed to load nutrition totals:", error);
    }
}

async function saveNutritionTotals() {
    const csrfToken = getCookieValue("csrftoken");
    const payload = {
        calories: parseNumberFromCell("total-calories"),
        protein: parseNumberFromCell("total-proteins"),
        fat: parseNumberFromCell("total-fats"),
        carbs: parseNumberFromCell("total-carbs"),
    };

    try {
        await fetch(`${PROFILE_API_BASE}/api/nutrition/today`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
            },
            body: JSON.stringify(payload),
        });
    } catch (error) {
        console.error("Failed to save nutrition totals:", error);
    }
}

function calculateTotal() {
    const categories = [
        { class: "input-calories", id: "total-calories", unit: " ккал" },
        { class: "input-proteins", id: "total-proteins", unit: " г" },
        { class: "input-fats", id: "total-fats", unit: " г" },
        { class: "input-carbs", id: "total-carbs", unit: " г" },
    ];

    categories.forEach((cat) => {
        const inputs = document.querySelectorAll(`.${cat.class}`);
        const display = document.getElementById(cat.id);
        if (!display) return;

        const current = parseFloat(display.innerText) || 0;
        let added = 0;
        inputs.forEach((input) => {
            added += parseFloat(input.value) || 0;
            input.value = "";
        });
        display.innerText = `${Math.round(current + added)}${cat.unit}`;
    });

    saveNutritionTotals();
}

function filterRecipes() {
    const input = document.getElementById("recipeSearch")?.value.toLowerCase() || "";
    const grids = document.querySelectorAll(".recipe-grid");

    grids.forEach((grid) => {
        const recipes = grid.querySelectorAll(".recipe-card");
        let hasVisible = false;

        recipes.forEach((recipe) => {
            const title = recipe.querySelector(".recipe-title")?.innerText.toLowerCase() || "";
            if (title.includes(input)) {
                recipe.style.display = "block";
                hasVisible = true;
            } else {
                recipe.style.display = "none";
            }
        });

        const section = grid.closest("section");
        if (hasVisible) {
            grid.style.display = "grid";
            if (section) section.style.display = "";
        } else {
            grid.style.display = "none";
            if (section) section.style.display = "none";
        }
    });
}

function renderExerciseCalendar(completedDates) {
    const grid = document.getElementById("grid");
    if (!grid) return;
    grid.innerHTML = "";

    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const offset = (new Date(year, month, 1).getDay() + 6) % 7;
    const activeDays = new Set();

    (completedDates || []).forEach((dateStr) => {
        const date = new Date(dateStr);
        if (Number.isNaN(date.getTime())) return;
        if (date.getFullYear() === year && date.getMonth() === month) {
            activeDays.add(date.getDate());
        }
    });

    for (let i = 0; i < offset; i += 1) {
        grid.appendChild(document.createElement("div"));
    }

    for (let i = 1; i <= daysInMonth; i += 1) {
        const cell = document.createElement("div");
        cell.classList.add("cell");
        if (activeDays.has(i)) cell.classList.add("active");
        if (i === today.getDate()) cell.classList.add("today");
        grid.appendChild(cell);
    }
}

async function setWorkoutDone(workoutId, done) {
    const csrfToken = getCookieValue("csrftoken");
    const response = await fetch(
        `${PROFILE_API_BASE}/workouts/${workoutId}/done/?format=json`,
        {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
            },
            body: JSON.stringify({ done }),
        }
    );
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
}

function renderWorkoutActions(workouts, completedWorkoutIds) {
    const container = document.getElementById("workout-api-list");
    if (!container) return;

    container.innerHTML = "";
    const completedSet = new Set(completedWorkoutIds || []);

    if (!workouts || !workouts.length) {
        container.innerHTML = "<p>No workouts found in backend.</p>";
        return;
    }

    workouts.forEach((workout) => {
        const row = document.createElement("div");
        row.style.display = "flex";
        row.style.justifyContent = "space-between";
        row.style.alignItems = "center";
        row.style.gap = "10px";
        row.style.padding = "8px 0";
        row.style.borderBottom = "1px solid #e5e5e5";

        const isDone = completedSet.has(workout.id);
        const name = document.createElement("div");
        name.innerHTML = `<strong>${workout.name}</strong> (${workout.duration} min)`;

        const action = document.createElement("button");
        action.type = "button";
        action.textContent = isDone ? "Undo" : "Mark done";
        action.style.background = isDone ? "#f3f4f6" : "#0097C1";
        action.style.color = isDone ? "#111827" : "#ffffff";
        action.style.border = "none";
        action.style.borderRadius = "6px";
        action.style.padding = "6px 10px";
        action.style.cursor = "pointer";

        action.addEventListener("click", async () => {
            try {
                await setWorkoutDone(workout.id, !isDone);
                await initExercises();
            } catch (error) {
                alert("Failed to update workout status.");
            }
        });

        row.appendChild(name);
        row.appendChild(action);
        container.appendChild(row);
    });
}

async function initExercises() {
    const grid = document.getElementById("grid");
    if (!grid) return;

    try {
        const response = await fetch(`${PROFILE_API_BASE}/workouts/?format=json`, {
            credentials: "include",
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        renderExerciseCalendar(data.completed_dates || []);
        renderWorkoutActions(data.workouts || [], data.completed_workout_ids || []);
    } catch (error) {
        console.error("Failed to load workouts:", error);
        renderExerciseCalendar([]);
        const container = document.getElementById("workout-api-list");
        if (container) container.innerHTML = "<p>Failed to load workouts from backend.</p>";
    }
}

function resetGrid() {
    initExercises();
}

function toggle(el) {
    const content = el.parentElement.querySelector(".hidden");
    if (!content) return;
    content.style.display = content.style.display === "block" ? "none" : "block";
}

document.addEventListener("click", function (e) {
    if (e.target.classList.contains("cup")) {
        handleWaterClick(e.target);
    }

    if (e.target.id === "finishTestBtn") {
        calculateAndSaveNorma();
    }

    if (e.target.classList.contains("calculate-btn")) {
        calculateTotal();
    }
});

document.addEventListener("DOMContentLoaded", function () {
    bindTopNav();

    const sidebar = document.querySelector(".sidebar-nav");
    if (sidebar) {
        sidebar.addEventListener(
            "click",
            function (event) {
                const button = event.target.closest("button.nav-btn");
                if (!button) return;

                const label = (button.textContent || "").trim().toLowerCase();
                if (label.includes("вправ")) {
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    window.location.href = "/pages/exercise/";
                    return;
                }
                if (label.includes("рецеп")) {
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    window.location.href = "/pages/recipes/";
                }
            },
            true
        );
    }

    const exerciseBtn = document.getElementById("profile-exercise-btn");
    if (exerciseBtn) {
        exerciseBtn.addEventListener("click", function () {
            window.location.href = "/pages/exercise/";
        });
    }

    const recipesBtn = document.getElementById("profile-recipes-btn");
    if (recipesBtn) {
        recipesBtn.addEventListener("click", function () {
            window.location.href = "/pages/recipes/";
        });
    }
});
