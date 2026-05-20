const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth();
let selectedDate = new Date().toISOString().split("T")[0];

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

function updateCalendarHeader() {
    const header = document.getElementById("calendar-month-year");
    if (!header) return;
    const date = new Date(currentYear, currentMonth);
    const monthName = date.toLocaleString("uk", { month: "long" });
    header.textContent = `${monthName.toUpperCase()} ${currentYear}`;
}

function renderCalendar(completedDates) {
    const grid = document.getElementById("grid");
    if (!grid) return;
    grid.innerHTML = "";

    updateCalendarHeader();

    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const offset = (new Date(currentYear, currentMonth, 1).getDay() + 6) % 7;
    const activeDays = new Set();

    const todayStr = new Date().toISOString().split("T")[0];

    (completedDates || []).forEach((dateStr) => {
        const d = new Date(dateStr);
        if (d.getFullYear() === currentYear && d.getMonth() === currentMonth) {
            activeDays.add(d.getDate());
        }
    });

    for (let i = 0; i < offset; i += 1) {
        grid.appendChild(document.createElement("div"));
    }

    for (let i = 1; i <= daysInMonth; i += 1) {
        const cell = document.createElement("div");
        cell.classList.add("cell");
        
        const d = new Date(currentYear, currentMonth, i);
        const cellDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
        
        if (activeDays.has(i)) cell.classList.add("active");
        if (cellDate === todayStr) cell.classList.add("today");
        if (cellDate === selectedDate) cell.style.boxShadow = "inset 0 0 0 2px #0097C1";
        
        cell.textContent = i;
        cell.style.cursor = "pointer";
        cell.addEventListener("click", () => {
            selectedDate = cellDate;
            initExercises();
        });
        
        grid.appendChild(cell);
    }
}

async function setWorkoutDone(workoutId, done) {
    const csrfToken = getCookieValue("csrftoken");
    const response = await fetch(`${API_BASE}/workouts/${workoutId}/done/?format=json`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: JSON.stringify({ done, date: selectedDate }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
}

function getYouTubeId(url) {
    if (!url) return null;
    const s = url.trim();
    // Regex for various YouTube URL formats
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]{11}).*/;
    const match = s.match(regExp);
    if (match && match[2].length === 11) return match[2];
    // If it's already an 11-char ID
    if (s.length === 11 && /^[a-zA-Z0-9_-]{11}$/.test(s)) return s;
    return null;
}

function renderWorkoutActions(workouts, completedIds) {
    const container = document.getElementById("workout-api-list");
    if (!container) return;
    container.innerHTML = "";

    const titleEl = document.getElementById("workout-list-title");
    if (titleEl) {
        const todayStr = new Date().toISOString().split("T")[0];
        titleEl.textContent = `ТРЕНУВАННЯ (${selectedDate === todayStr ? "СЬОГОДНІ" : selectedDate})`;
    }

    const doneSet = new Set(completedIds || []);
    if (!workouts || !workouts.length) {
        container.innerHTML = "<p style='padding: 20px; color: #666;'>Тренувань не знайдено за вашим запитом.</p>";
        return;
    }

    workouts.forEach((workout) => {
        const card = document.createElement("div");
        card.className = "card"; // Use the same class as static cards
        card.style.marginBottom = "30px";
        card.style.background = "#fff";
        card.style.padding = "15px";
        card.style.borderRadius = "12px";
        card.style.boxShadow = "0 2px 10px rgba(0,0,0,0.05)";

        const done = doneSet.has(workout.id);
        const ytId = getYouTubeId(workout.link);
        const origin = window.location.origin;

        const videoHtml = ytId ? `
            <iframe 
                width="350" 
                height="200"
                src="https://www.youtube.com/embed/${ytId}?enablejsapi=1&origin=${encodeURIComponent(origin)}" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
                style="border: 2px solid #0097C1; border-radius: 8px; width: 350px !important; height: 200px !important;">
            </iframe>
        ` : (workout.link ? `
            <div style="width: 350px; height: 200px; border: 2px solid #0097C1; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: #f9f9f9;">
                <a href="${workout.link}" target="_blank" style="color: #0097C1; font-weight: 600; text-decoration: none;">ДИВИТИСЬ ВІДЕО →</a>
            </div>
        ` : `
            <div style="width: 350px; height: 200px; border: 2px solid #ddd; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: #eee; color: #999;">
                ВІДЕО ВІДСУТНЄ
            </div>
        `);

        card.innerHTML = `
            ${videoHtml}
            <div class="text" style="flex: 1;">
                <div class="title-row" onclick="toggle(this)">
                    <div class="left">
                        <span class="arrow">→</span>
                        <div class="title-card" style="font-size: 1.2em; font-family: 'Jost';">${workout.name.toUpperCase()}</div>
                    </div>
                    <span class="down" style="padding: 0 10px;">v</span>
                </div>
                <div class="info" style="color: #0097C1; font-weight: 600; font-size: 0.85em; margin: 5px 0 10px 30px; font-family: 'Jost';">
                    ${workout.category.toUpperCase()} • ${workout.difficulty.toUpperCase()} • ${workout.duration} ХВ • ${workout.calories_burned} ККАЛ
                </div>
                <div class="hidden">
                    <div style="margin-left: 30px; font-family: 'Jost';">
                        <p style="color: #555; line-height: 1.4; margin-bottom: 15px;">${workout.description || "Опис відсутній."}</p>
                        <button class="mark-done-btn" style="
                            background: ${done ? "#27ae60" : "#0097C1"};
                            color: #fff;
                            border: none;
                            border-radius: 8px;
                            padding: 10px 20px;
                            cursor: pointer;
                            font-weight: 700;
                            transition: background 0.2s;
                        ">
                            ${done ? "✓ ВИКОНАНО" : "ВІДМІТИТИ ЯК ВИКОНАНЕ"}
                        </button>
                    </div>
                </div>
            </div>
        `;

        const button = card.querySelector(".mark-done-btn");
        button.addEventListener("click", async (e) => {
            e.stopPropagation(); // Prevent toggle
            try {
                button.disabled = true;
                button.textContent = "...";
                await setWorkoutDone(workout.id, !done);
                await initExercises();
            } catch (error) {
                alert("Не вдалося оновити статус.");
                button.disabled = false;
                button.textContent = done ? "✓ ВИКОНАНО" : "ВІДМІТИТИ ЯК ВИКОНАНЕ";
            }
        });

        container.appendChild(card);
    });
}

async function initExercises() {
    try {
        const q = document.getElementById("search-input")?.value || "";
        const category = document.getElementById("category-filter")?.value || "";
        const difficulty = document.getElementById("difficulty-filter")?.value || "";
        
        const params = new URLSearchParams({
            format: "json",
            date: selectedDate,
            year: currentYear,
            month: currentMonth + 1,
            q,
            category,
            difficulty
        });

        const response = await fetch(`${API_BASE}/workouts/?${params.toString()}`, {
            credentials: "include",
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        renderCalendar(data.completed_dates || []);
        renderWorkoutActions(data.workouts || [], data.completed_workout_ids || []);
    } catch (error) {
        console.error("Failed to load workouts:", error);
    }
}

function changeMonth(delta) {
    currentMonth += delta;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear -= 1;
    } else if (currentMonth > 11) {
        currentMonth = 0;
        currentYear += 1;
    }
    initExercises();
}

function resetToToday() {
    const today = new Date();
    currentYear = today.getFullYear();
    currentMonth = today.getMonth();
    selectedDate = today.toISOString().split("T")[0];
    initExercises();
}

function applyFilters() {
    initExercises();
}

function toggle(el) {
    const content = el.parentElement.querySelector(".hidden");
    if (!content) return;
    content.style.display = content.style.display === "block" ? "none" : "block";
}

window.addEventListener("DOMContentLoaded", initExercises);
