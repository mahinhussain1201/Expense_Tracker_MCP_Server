from fastmcp import FastMCP
import os
import sqlite3
import json

# -------------------- PATH SETUP --------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

BASE_CURRENCY = "USD"


# -------------------- DATABASE INITIALIZATION --------------------
def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()


# -------------------- ADD EXPENSE --------------------
@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    """
    Add a new expense entry.

    Claude will use this tool when user mentions spending money.
    """
    try:
        with sqlite3.connect(DB_PATH) as c:
            cur = c.execute(
                """INSERT INTO expenses
                   (date, amount, category, subcategory, note)
                   VALUES (?,?,?,?,?)""",
                (date, amount, category, subcategory, note)
            )

        return {
            "status": "ok",
            "id": cur.lastrowid,
            "summary": f"Added expense: {amount} {BASE_CURRENCY} for {category}"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- DELETE EXPENSE --------------------
@mcp.tool()
def delete_expense(expense_id: int):
    """
    Delete an expense by ID.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cur.rowcount == 0:
            return {"status": "error", "message": "Expense not found"}
        return {"status": "ok", "deleted_id": expense_id}


# -------------------- LIST EXPENSES --------------------
@mcp.tool()
def list_expenses(start_date, end_date):
    """
    Retrieve all expenses within a date range.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """SELECT id, date, amount, category, subcategory, note
               FROM expenses
               WHERE date BETWEEN ? AND ?
               ORDER BY date ASC""",
            (start_date, end_date)
        )

        cols = [d[0] for d in cur.description]
        data = [dict(zip(cols, r)) for r in cur.fetchall()]

    return {
        "count": len(data),
        "data": data
    }


# -------------------- SUMMARY --------------------
@mcp.tool()
def summarize(start_date, end_date):
    """
    Category-wise summary of spending.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT category, SUM(amount)
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """,
            (start_date, end_date)
        )
        rows = cur.fetchall()

    total = sum(r[1] for r in rows)

    return {
        "total_spent": total,
        "breakdown": dict(rows),
        "summary": f"Total spending is {total} {BASE_CURRENCY}"
    }


# -------------------- INSIGHTS --------------------
@mcp.tool()
def spending_insights(start_date, end_date):
    """
    High-level analysis of spending.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT category, SUM(amount)
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """,
            (start_date, end_date)
        )
        rows = cur.fetchall()

    total = sum(r[1] for r in rows)
    top = rows[0] if rows else ("None", 0)

    return {
        "total_spent": total,
        "top_category": top[0],
        "top_amount": top[1],
        "breakdown": dict(rows),
        "summary": f"You spent most on {top[0]} ({top[1]})"
    }


# -------------------- PIE CHART --------------------
@mcp.tool()
def category_spending_chart(start_date, end_date):
    """
    Returns category-wise spending for charts.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT category, SUM(amount)
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """,
            (start_date, end_date)
        )
        rows = cur.fetchall()

    return {
        "type": "pie_chart",
        "labels": [r[0] for r in rows],
        "values": [r[1] for r in rows],
        "summary": "Category-wise spending distribution"
    }


# -------------------- DAILY TREND --------------------
@mcp.tool()
def daily_spending_trend(start_date, end_date):
    """
    Returns daily spending trend.
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT date, SUM(amount)
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
            """,
            (start_date, end_date)
        )
        rows = cur.fetchall()

    return {
        "type": "line_chart",
        "labels": [r[0] for r in rows],
        "values": [r[1] for r in rows],
        "summary": "Daily spending trend"
    }


# -------------------- CATEGORIES RESOURCE --------------------
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    if not os.path.exists(CATEGORIES_PATH):
        return "[]"
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()


# -------------------- CLAUDE INSTRUCTIONS --------------------
@mcp.resource("expense://instructions", mime_type="text/plain")
def instructions():
    return """
You are an expense tracking assistant.

Rules:
- Always use tools when user mentions money
- Never guess values
- Prefer structured responses
- Use insights for analysis
- Use charts for visualization
"""


# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    mcp.run()