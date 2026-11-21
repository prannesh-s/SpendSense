
const $ = id => document.getElementById(id);

let expenseChart = null;

const today = new Date();
$("today").textContent = today.toLocaleDateString(
    "en-IN",
    { weekday: "long", year: "numeric", month: "long", day: "numeric" }
);

$("date").value = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0")
].join("-");

async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Something went wrong.");
    }

    return data;
}

function money(value) {
    return Number(value).toLocaleString("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2
    });
}

function showMessage(message, success = true) {
    const element = $("formMessage");
    element.textContent = message;
    element.className = success ? "success-message" : "error-message";
}

$("transactionForm").addEventListener("submit", async event => {
    event.preventDefault();

    const button = event.submitter;
    button.disabled = true;

    const transaction = {
        title: $("title").value.trim(),
        amount: Number($("amount").value),
        category: $("category").value,
        kind: $("kind").value,
        date: $("date").value
    };

    try {
        await api("/api/transactions", {
            method: "POST",
            body: JSON.stringify(transaction)
        });

        showMessage("Transaction added successfully!");

        $("title").value = "";
        $("amount").value = "";

        await refreshDashboard();

    } catch (error) {
        showMessage(error.message, false);
    } finally {
        button.disabled = false;
    }
});


$("budgetForm").addEventListener("submit", async event => {
    event.preventDefault();

    try {
        await api("/api/budget", {
            method: "PUT",
            body: JSON.stringify({
                amount: Number($("budgetInput").value)
            })
        });

        await refreshDashboard();

        $("budgetStatus").textContent = "Budget updated successfully!";

    } catch (error) {
        $("budgetStatus").textContent = error.message;
    }
});


async function loadTransactions() {
    const transactions = await api("/api/transactions");

    const list = $("transactionList");
    list.replaceChildren();

    if (transactions.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 6;
        cell.textContent = "No transactions yet. Add your first transaction!";

        row.appendChild(cell);
        list.appendChild(row);
        return;
    }

    transactions.forEach(transaction => {
        const row = document.createElement("tr");

        const values = [
            transaction.title,
            transaction.category,
            transaction.transaction_date,
            transaction.kind,
            (transaction.kind === "income" ? "+ " : "- ") +
                money(transaction.amount)
        ];

        values.forEach((value, index) => {
            const cell = document.createElement("td");
            cell.textContent = value;

            if (index === 4) {
                cell.className = transaction.kind === "income"
                    ? "income-text"
                    : "expense-text";
            }

            row.appendChild(cell);
        });

        const actionCell = document.createElement("td");
        const deleteButton = document.createElement("button");

        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-button";
        deleteButton.type = "button";

        deleteButton.addEventListener("click", async () => {
            if (!confirm("Delete this transaction?")) return;

            try {
                await api(
                    "/api/transactions/" + transaction.id,
                    { method: "DELETE" }
                );

                await refreshDashboard();

            } catch (error) {
                alert(error.message);
            }
        });

        actionCell.appendChild(deleteButton);
        row.appendChild(actionCell);

        list.appendChild(row);
    });
}


async function loadBudget() {
    const data = await api("/api/budget");
    $("budgetInput").value = data.monthly_limit;
}


function showInsights(data) {
    const container = $("insights");
    container.replaceChildren();

    const addInsight = message => {
        const div = document.createElement("div");
        div.className = "insight";
        div.textContent = message;
        container.appendChild(div);
    };

    if (data.expense === 0) {
        addInsight("Start adding expenses to receive spending insights.");
        return;
    }

    const highest = data.categories[0];

    if (highest) {
        const share = (highest.total / data.expense * 100).toFixed(1);

        addInsight(
            highest.category + " is your highest spending category, " +
            "accounting for " + share + "% of your expenses."
        );
    }

    if (data.budget_used >= 100) {
        addInsight("Your monthly spending has reached or exceeded your budget.");
    } else if (data.budget_used >= 80) {
        addInsight("You have used more than 80% of your monthly budget. Monitor upcoming expenses.");
    } else {
        addInsight("Your spending is currently below your monthly budget.");
    }

    if (data.balance < 0) {
        addInsight("Your recorded expenses exceed your recorded income this month.");
    } else {
        addInsight("Your recorded income is currently higher than your expenses.");
    }

    addInsight(
        "At the current daily spending rate, estimated monthly expenses are " +
        money(data.projected_expense) + ". This is a simple projection, not a guarantee."
    );
}


function drawChart(categories) {
    const canvas = $("expenseChart");

    if (expenseChart) {
        expenseChart.destroy();
        expenseChart = null;
    }

    if (categories.length === 0) {
        const context = canvas.getContext("2d");
        context.clearRect(0, 0, canvas.width, canvas.height);
        return;
    }

    expenseChart = new Chart(canvas, {
        type: "doughnut",

        data: {
            labels: categories.map(item => item.category),

            datasets: [{
                data: categories.map(item => item.total),
                backgroundColor: [
                    "#5478bd",
                    "#36a878",
                    "#f0aa52",
                    "#a77ad4",
                    "#e16e79",
                    "#55a8b7",
                    "#77879b",
                    "#b2a28a"
                ],
                borderWidth: 2,
                borderColor: "#ffffff"
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    position: "bottom"
                },

                tooltip: {
                    callbacks: {
                        label: context =>
                            context.label + ": " + money(context.raw)
                    }
                }
            }
        }
    });
}


async function loadSummary() {
    const data = await api("/api/summary");

    $("income").textContent = money(data.income);
    $("expense").textContent = money(data.expense);
    $("balance").textContent = money(data.balance);
    $("average").textContent = money(data.daily_average);

    $("budgetSpent").textContent = money(data.expense);
    $("budgetLimit").textContent = money(data.budget);

    $("projection").textContent = money(data.projected_expense);

    const percentage = data.budget_used;

    $("progressBar").style.width =
        Math.min(percentage, 100) + "%";

    $("progressBar").style.background =
        percentage >= 100 ? "#d64e58" :
        percentage >= 80 ? "#e9a342" : "#36a878";

    $("budgetStatus").textContent =
        percentage.toFixed(1) + "% of your monthly budget used.";

    drawChart(data.categories);
    showInsights(data);
}


async function refreshDashboard() {
    try {
        await Promise.all([
            loadSummary(),
            loadTransactions()
        ]);

    } catch (error) {
        console.error(error);
        alert("Unable to load dashboard: " + error.message);
    }
}


$("exportButton").addEventListener("click", () => {
    window.location.href = "/api/export";
});


async function startApp() {
    try {
        await loadBudget();
        await refreshDashboard();

    } catch (error) {
        alert("Could not connect to the server: " + error.message);
    }
}

startApp();
