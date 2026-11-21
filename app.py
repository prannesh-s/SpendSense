from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from flask import send_file
from io import BytesIO
from flask import Flask, render_template, request, jsonify, Response
import sqlite3
import os
import csv
import io
from datetime import date, datetime
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

# Use a persistent disk path in deployment if configured.
DB_PATH = Path(os.environ.get(
    "DATABASE_PATH",
    str(BASE_DIR / "spendsense.db")
))

CATEGORIES = [
    "Food", "Transport", "Education", "Shopping",
    "Entertainment", "Health", "Bills", "Other"
]

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('income', 'expense')),
                transaction_date TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                monthly_limit REAL NOT NULL
            )
        """)

        conn.execute("""
            INSERT OR IGNORE INTO budgets (id, monthly_limit)
            VALUES (1, 5000)
        """)

init_db()


@app.route("/")
def home():
    return render_template("index.html")


def error(message, status=400):
    return jsonify({"error": message}), status


@app.route("/api/transactions", methods=["GET", "POST"])
def transactions():

    if request.method == "POST":
        data = request.get_json(silent=True) or {}

        title = str(data.get("title", "")).strip()
        category = data.get("category")
        kind = data.get("kind")
        transaction_date = data.get("date")

        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            return error("Enter a valid amount.")

        if not title or len(title) > 80:
            return error("Title must contain 1–80 characters.")

        if amount <= 0 or amount > 10000000:
            return error("Enter an amount between 0 and 10,000,000.")

        if category not in CATEGORIES:
            return error("Select a valid category.")

        if kind not in ("income", "expense"):
            return error("Select income or expense.")

        try:
            parsed_date = date.fromisoformat(transaction_date)
            if parsed_date > date.today():
                return error("Future transaction dates are not allowed.")
        except (ValueError, TypeError):
            return error("Enter a valid transaction date.")

        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO transactions
                (title, amount, category, kind, transaction_date)
                VALUES (?, ?, ?, ?, ?)
            """, (title, amount, category, kind, transaction_date))

        return jsonify({
            "message": "Transaction added successfully.",
            "id": cursor.lastrowid
        }), 201

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM transactions
            ORDER BY transaction_date DESC, id DESC
        """).fetchall()

    return jsonify([dict(row) for row in rows])


@app.route("/api/transactions/<int:transaction_id>",
           methods=["DELETE"])
def delete_transaction(transaction_id):

    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
        )

    if cursor.rowcount == 0:
        return error("Transaction not found.", 404)

    return jsonify({"message": "Transaction deleted."})


@app.route("/api/budget", methods=["GET", "PUT"])
def budget():

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}

        try:
            amount = float(data.get("amount"))
        except (TypeError, ValueError):
            return error("Enter a valid budget.")

        if not 0 < amount <= 10000000:
            return error("Budget must be greater than zero.")

        with get_db() as conn:
            conn.execute("""
                UPDATE budgets SET monthly_limit = ?
                WHERE id = 1
            """, (amount,))

    with get_db() as conn:
        row = conn.execute("""
            SELECT monthly_limit FROM budgets WHERE id = 1
        """).fetchone()

    return jsonify({"monthly_limit": row["monthly_limit"]})


@app.route("/api/summary")
def summary():

    month = date.today().strftime("%Y-%m")

    with get_db() as conn:

        totals = conn.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN kind='income'
                    THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN kind='expense'
                    THEN amount ELSE 0 END), 0) AS expense
            FROM transactions
            WHERE substr(transaction_date, 1, 7) = ?
        """, (month,)).fetchone()

        categories = conn.execute("""
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE kind='expense'
              AND substr(transaction_date, 1, 7) = ?
            GROUP BY category
            ORDER BY total DESC
        """, (month,)).fetchall()

        budget_row = conn.execute("""
            SELECT monthly_limit FROM budgets WHERE id=1
        """).fetchone()

        all_rows = conn.execute("""
            SELECT kind, SUM(amount) AS total
            FROM transactions
            WHERE substr(transaction_date, 1, 7) = ?
            GROUP BY kind
        """, (month,)).fetchall()

    income = float(totals["income"])
    expense = float(totals["expense"])
    budget_limit = float(budget_row["monthly_limit"])

    daily_average = expense / max(date.today().day, 1)

    # Simple estimate based on the current daily average.
    days_in_month = (
        date(date.today().year + (date.today().month == 12),
             date.today().month % 12 + 1, 1) - date.today()
    ).days + date.today().day - 1

    projected_expense = daily_average * days_in_month

    return jsonify({
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "budget": budget_limit,
        "budget_used": round(expense / budget_limit * 100, 1),
        "daily_average": round(daily_average, 2),
        "projected_expense": round(projected_expense, 2),
        "categories": [dict(row) for row in categories]
    })



@app.route("/api/export")
def export_excel():

    with get_db() as conn:
        rows = conn.execute("""
            SELECT title, amount, category, kind, transaction_date
            FROM transactions
            ORDER BY transaction_date DESC
        """).fetchall()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "SpendSense Report"

    # Excel headings
    headers = [
        "Title", "Amount (INR)", "Category",
        "Type", "Date"
    ]

    sheet.append(headers)

    # Style headings
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            start_color="244A77",
            end_color="244A77",
            fill_type="solid"
        )
        cell.alignment = Alignment(horizontal="center")

    # Add transaction data
    for row in rows:

        transaction_date = datetime.strptime(
            row["transaction_date"], "%Y-%m-%d"
        ).date()

        sheet.append([
            row["title"],
            row["amount"],
            row["category"],
            row["kind"],
            transaction_date
        ])

    # Format amount and date columns
    for row in range(2, sheet.max_row + 1):
        sheet.cell(row, 2).number_format = '₹#,##0.00'
        sheet.cell(row, 5).number_format = 'DD-MM-YYYY'

    # Automatically adjust column widths
    for column in sheet.columns:
        max_length = max(
            len(str(cell.value or "")) for cell in column
        )
        column_letter = get_column_letter(column[0].column)
        sheet.column_dimensions[column_letter].width = max(
            max_length + 5, 15
        )

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    # Create Excel file in memory
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="SpendSense_Report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



@app.route("/api/health")
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True)
