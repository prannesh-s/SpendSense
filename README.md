# SpendSense – Smart Personal Finance Tracker

## 1. About the Project

SpendSense is a smart personal finance tracking web application designed to help users manage their income, expenses, and monthly budgets efficiently.

It provides a simple dashboard where users can record transactions, monitor spending habits, analyse expenses by category, and view their overall financial summary.

The main objective of SpendSense is to make personal money management easier, more organised, and more understandable.

## 2. Problem Statement

Many people find it difficult to track their daily expenses and manage their monthly budgets. Without proper expense tracking, it becomes challenging to understand spending patterns and control unnecessary expenses.

SpendSense addresses this problem by providing a centralised platform to record transactions, monitor budgets, and analyse financial activities.

## 3. Key Features

- **Income Tracking:** Record and monitor different sources of income.
- **Expense Tracking:** Add and manage daily expenses.
- **Budget Management:** Set a budget and monitor spending against it.
- **Category-wise Analysis:** Understand spending across different categories.
- **Financial Dashboard:** View total income, expenses, and balance.
- **Transaction History:** View previously recorded transactions.
- **Excel Export:** Download transaction reports in Excel format.
- **Simple Interface:** Easy-to-use dashboard with a clean design.

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| SQLite | Database management |
| HTML | Webpage structure |
| CSS | Styling and design |
| JavaScript | Frontend functionality |
| Chart.js | Financial data visualisation |
| OpenPyXL | Excel report generation |

## 5. Project Structure

```text
SpendSense/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── app.js
```

## 6. How SpendSense Works

1. The user opens the SpendSense dashboard.
2. The user enters income or expense details.
3. Flask processes the submitted information.
4. Transaction details are stored in an SQLite database.
5. The dashboard displays updated financial summaries.
6. Charts help users understand category-wise expenses.
7. Users can export their transaction records as an Excel report.

## 7. Installation and Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/prannesh-s/SpendSense.git
```

### Step 2: Open the Project Folder

```bash
cd SpendSense
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 4: Activate the Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Run the Application

```bash
python app.py
```

### Step 7: Open in Browser

Visit:

```text
http://127.0.0.1:5000
```

## 8. Future Enhancements

- User login and authentication.
- Monthly and yearly financial reports.
- Smart spending recommendations.
- Improved data visualisation.
- Cloud database integration.
- Mobile-friendly interface.

## 9. Benefits

- Helps users understand their spending habits.
- Makes expense tracking easier.
- Supports better budget management.
- Provides organised financial records.
- Saves time through automated summaries and Excel exports.

## 10. Project Information

**Project Name:** SpendSense

**Category:** FinTech / Personal Finance Management

**Developed Using:** Python Flask, SQLite, HTML, CSS and JavaScript

**Project Type:** Web Application

**GitHub Repository:**  
https://github.com/prannesh-s/SpendSense
