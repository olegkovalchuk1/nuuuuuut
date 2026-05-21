const API_BASE = "";

const cups = document.querySelectorAll(".cup");
let searchTimeout;

cups.forEach((cup, index) => {
    cup.addEventListener("click", () => {
        if (cup.classList.contains("active")) {
            for (let i = index; i < cups.length; i += 1) {
                cups[i].classList.remove("active");
            }
        } else {
            for (let i = 0; i <= index; i += 1) {
                cups[i].classList.add("active");
            }
        }
    });
});

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

function parseNumberFromCell(id) {
    const element = document.getElementById(id);
    if (!element) return 0;
    return parseFloat(String(element.innerText).replace(",", ".")) || 0;
}

function setCellValue(id, value, unit) {
    const element = document.getElementById(id);
    if (!element) return;
    element.innerText = `${Math.round(value)} ${unit}`;
}

function displayNorma() {
    setCellValue("norma-calories-display", localStorage.getItem("normaCalories") || 0, "ккал");
    setCellValue("norma-proteins-display", localStorage.getItem("normaProteins") || 0, "г");
    setCellValue("norma-fats-display", localStorage.getItem("normaFats") || 0, "г");
    setCellValue("norma-carbs-display", localStorage.getItem("normaCarbs") || 0, "г");
}

async function loadNutritionTotals() {
    try {
        const response = await fetch(`${API_BASE}/api/nutrition/today`, {
            credentials: "include",
        });
        if (!response.ok) return;
        const data = await response.json();
        setCellValue("total-calories", data.calories || 0, "ккал");
        setCellValue("total-proteins", data.protein || 0, "г");
        setCellValue("total-fats", data.fat || 0, "г");
        setCellValue("total-carbs", data.carbs || 0, "г");
    } catch (error) {
        console.error("Failed to load nutrition totals:", error);
    }
}

async function saveNutritionTotals() {
    if (window.location.protocol === "file:") return;
    const csrfToken = getCookieValue("csrftoken");
    const payload = {
        calories: parseNumberFromCell("total-calories"),
        protein: parseNumberFromCell("total-proteins"),
        fat: parseNumberFromCell("total-fats"),
        carbs: parseNumberFromCell("total-carbs"),
    };
    try {
        await fetch(`${API_BASE}/api/nutrition/today`, {
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
        { class: "input-calories", id: "total-calories", unit: "ккал" },
        { class: "input-proteins", id: "total-proteins", unit: "г" },
        { class: "input-fats", id: "total-fats", unit: "г" },
        { class: "input-carbs", id: "total-carbs", unit: "г" },
    ];

    categories.forEach((cat) => {
        const inputs = document.querySelectorAll(`.${cat.class}`);
        const displayElement = document.getElementById(cat.id);
        if (!displayElement) return;

        const currentTotal = parseFloat(displayElement.innerText) || 0;
        let addedValue = 0;
        inputs.forEach((input) => {
            addedValue += parseFloat(input.value) || 0;
            input.value = "";
        });
        const newTotal = currentTotal + addedValue;
        displayElement.innerText = `${Math.round(newTotal)} ${cat.unit}`;
    });

    document.querySelectorAll(".meal-card input[type='text']").forEach((nameInput) => {
        nameInput.value = "";
    });

    saveNutritionTotals();
}

function filterRecipes() {
    const query = document.getElementById("recipeSearch")?.value.trim() || "";
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => fetchRecipes(query), 300);
}

async function fetchRecipes(query = "") {
    const recipesSection = document.querySelector(".recipes");
    if (!recipesSection) return;

    let loadingMessage = document.getElementById("loading-status");
    if (!loadingMessage) {
        loadingMessage = document.createElement("div");
        loadingMessage.id = "loading-status";
        const title = recipesSection.querySelector("h1") || recipesSection.firstChild;
        recipesSection.insertBefore(loadingMessage, title.nextSibling || title);
    }
    loadingMessage.style.display = "block";
    loadingMessage.innerHTML = '<p style="text-align:center;font-size:1.1rem;margin:20px;">Loading recipes...</p>';

    if (window.location.protocol === "file:") {
        loadingMessage.innerHTML = '<p style="text-align:center;color:#b00020;margin:20px;">Open via HTTP server to use API.</p>';
        return;
    }

    try {
        const queryPart = query ? `?q=${encodeURIComponent(query)}` : "";
        const primaryUrl = `${API_BASE}/api/recipes/${queryPart}`;
        const fallbackUrl = `${API_BASE}/recipes/${queryPart}`;

        let response = await fetch(primaryUrl, { credentials: "include" });
        if (!response.ok && response.status === 404) {
            response = await fetch(fallbackUrl, { credentials: "include" });
        }
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        renderRecipes(data.results || []);
        loadingMessage.style.display = "none";
    } catch (error) {
        console.error(error);
        loadingMessage.innerHTML = `<p style="text-align:center;color:#b00020;margin:20px;">Failed to load recipes: ${error.message}</p>`;
    }
}

function renderRecipes(recipes) {
    const breakfastGrid = document.querySelector(".breakfast-section .recipe-grid");
    const lunchGrid = document.querySelector(".lunch-section .recipe-grid");
    const dinnerGrid = document.querySelector(".dinner-section .recipe-grid");

    if (breakfastGrid) breakfastGrid.innerHTML = "";
    if (lunchGrid) lunchGrid.innerHTML = "";
    if (dinnerGrid) dinnerGrid.innerHTML = "";

    if (!recipes.length) {
        const noResults = '<p style="text-align:center;width:100%;grid-column:1/-1;margin:20px;">No results found.</p>';
        if (breakfastGrid) breakfastGrid.innerHTML = noResults;
        return;
    }

    recipes.forEach((recipe) => {
        const card = createRecipeCard(recipe);
        const category = (recipe.category || "").toLowerCase();

        if (category === "breakfast") {
            if (breakfastGrid) breakfastGrid.appendChild(card);
        } else if (category === "dessert" || category === "side" || category === "starter") {
            if (dinnerGrid) dinnerGrid.appendChild(card);
        } else {
            if (lunchGrid) lunchGrid.appendChild(card);
        }
    });
}

function createRecipeCard(recipe) {
    const card = document.createElement("div");
    card.className = "recipe-card";

    const ingredients = recipe.ingredients || [];
    const ingredientsHtml = ingredients
        .map((ing) => `<li>${ing.name} - ${Math.round(ing.grams)} г</li>`)
        .join("");

    const calories = Math.round(recipe.calories) || 0;
    const proteins = Math.round(recipe.protein) || 0;
    const fats = Math.round(recipe.fat) || 0;
    const carbs = Math.round(recipe.carbs) || 0;

    card.innerHTML = `
        <img src="${recipe.image_url || "/static/foods.jpg"}" alt="${recipe.name}" class="recipe-img">
        <h3 class="recipe-title">${recipe.name}</h3>
        <div class="recipe-content">
            <h3 class="section-label">Склад:</h3>
            <ul class="ingredient-list">${ingredientsHtml}</ul>
            <h3 class="section-label">Поживність:</h3>
            <ul class="nutrition-list">
                <li>Калорії - ${calories} ккал</li>
                <li>Білки - ${proteins} г</li>
                <li>Жири - ${fats} г</li>
                <li>Вуглеводи - ${carbs} г</li>
            </ul>
            <div class="recipe-actions" style="margin-top: 15px; display: flex; gap: 5px; flex-wrap: wrap;">
                <button onclick="addToPlan('${recipe.name}', ${calories}, ${proteins}, ${fats}, ${carbs}, 0)" class="add-to-plan-btn">Сніданок</button>
                <button onclick="addToPlan('${recipe.name}', ${calories}, ${proteins}, ${fats}, ${carbs}, 1)" class="add-to-plan-btn">Обід</button>
                <button onclick="addToPlan('${recipe.name}', ${calories}, ${proteins}, ${fats}, ${carbs}, 2)" class="add-to-plan-btn">Вечеря</button>
            </div>
        </div>
    `;
    return card;
}

function addToPlan(name, cals, prots, fats, carbs, mealIndex) {
    const mealCards = document.querySelectorAll(".meal-card");
    if (mealIndex >= mealCards.length) return;

    const card = mealCards[mealIndex];
    const nameInput = card.querySelector("input[type='text']");
    const calInput = card.querySelector(".input-calories");
    const protInput = card.querySelector(".input-proteins");
    const fatInput = card.querySelector(".input-fats");
    const carbInput = card.querySelector(".input-carbs");

    if (nameInput) nameInput.value = name;
    if (calInput) calInput.value = cals || "";
    if (protInput) protInput.value = prots || "";
    if (fatInput) fatInput.value = fats || "";
    if (carbInput) carbInput.value = carbs || "";

    card.scrollIntoView({ behavior: "smooth", block: "center" });
    card.style.boxShadow = "0 0 15px #ff6b6b";
    setTimeout(() => { card.style.boxShadow = ""; }, 2000);
}

async function initRecipesPage() {
    displayNorma();
    await loadNutritionTotals();
    await fetchRecipes();
}

window.initRecipesPage = initRecipesPage;
window.fetchRecipes = fetchRecipes;

if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", initRecipesPage);
} else {
    initRecipesPage();
}
