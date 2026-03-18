from fastmcp import FastMCP
import os
import aiosqlite
import tempfile
import json

# -------------------- PATH SETUP --------------------
TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print(f"Database path: {DB_PATH}")

mcp = FastMCP("ExpenseTracker")

BASE_CURRENCY = "INR"


# -------------------- DATABASE INITIALIZATION --------------------
def init_db():
    try:
        import sqlite3
        with sqlite3.connect(DB_PATH) as c:
            c.execute("PRAGMA journal_mode=WAL")
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
            c.execute("INSERT OR IGNORE INTO expenses(date, amount, category) VALUES ('2000-01-01', 0, 'test')")
            c.execute("DELETE FROM expenses WHERE category = 'test'")
            print("Database initialized with write access")
    except Exception as e:
        print(f"DB Init Error: {e}")
        raise

init_db()


# -------------------- ADD EXPENSE --------------------
@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """INSERT INTO expenses(date, amount, category, subcategory, note)
                   VALUES (?,?,?,?,?)""",
                (date, amount, category, subcategory, note)
            )
            await c.commit()

            return {
                "status": "ok",
                "id": cur.lastrowid,
                "summary": f"Added {amount} {BASE_CURRENCY} for {category}"
            }

    except Exception as e:
        if "readonly" in str(e).lower():
            return {"status": "error", "message": "Database is read-only"}
        return {"status": "error", "message": str(e)}


# -------------------- DELETE EXPENSE --------------------
@mcp.tool()
async def delete_expense(expense_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            await c.commit()

            if cur.rowcount == 0:
                return {"status": "error", "message": "Expense not found"}

            return {"status": "ok", "deleted_id": expense_id}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- LIST EXPENSES --------------------
@mcp.tool()
async def list_expenses(start_date, end_date):
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """SELECT id, date, amount, category, subcategory, note
                   FROM expenses
                   WHERE date BETWEEN ? AND ?
                   ORDER BY date DESC, id DESC""",
                (start_date, end_date)
            )

            cols = [d[0] for d in cur.description]
            rows = await cur.fetchall()

            return {
                "count": len(rows),
                "data": [dict(zip(cols, r)) for r in rows]
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- SUMMARY --------------------
@mcp.tool()
async def summarize(start_date, end_date):
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT category, SUM(amount)
                FROM expenses
                WHERE date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY SUM(amount) DESC
                """,
                (start_date, end_date)
            )
            rows = await cur.fetchall()

        total = sum(r[1] for r in rows)

        return {
            "total_spent": total,
            "breakdown": dict(rows),
            "summary": f"Total spending is {total} {BASE_CURRENCY}"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- INSIGHTS --------------------
@mcp.tool()
async def spending_insights(start_date, end_date):
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT category, SUM(amount)
                FROM expenses
                WHERE date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY SUM(amount) DESC
                """,
                (start_date, end_date)
            )
            rows = await cur.fetchall()

        total = sum(r[1] for r in rows)
        top = rows[0] if rows else ("None", 0)

        return {
            "total_spent": total,
            "top_category": top[0],
            "top_amount": top[1],
            "breakdown": dict(rows),
            "summary": f"Most spent on {top[0]} ({top[1]})"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- PIE CHART --------------------
@mcp.tool()
async def category_spending_chart(start_date, end_date):
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT category, SUM(amount)
                FROM expenses
                WHERE date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY SUM(amount) DESC
                """,
                (start_date, end_date)
            )
            rows = await cur.fetchall()

        return {
            "type": "pie_chart",
            "labels": [r[0] for r in rows],
            "values": [r[1] for r in rows]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- DAILY TREND --------------------
@mcp.tool()
async def daily_spending_trend(start_date, end_date):
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT date, SUM(amount)
                FROM expenses
                WHERE date BETWEEN ? AND ?
                GROUP BY date
                ORDER BY date
                """,
                (start_date, end_date)
            )
            rows = await cur.fetchall()

        return {
            "type": "line_chart",
            "labels": [r[0] for r in rows],
            "values": [r[1] for r in rows]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- CATEGORIES RESOURCE --------------------
@mcp.resource("expense:///categories", mime_type="application/json")
def categories():
    default = {
        "categories": [
            "Food", "Transport", "Shopping", "Bills",
            "Entertainment", "Health", "Travel", "Other"
        ]
    }

    try:
        if os.path.exists(CATEGORIES_PATH):
            with open(CATEGORIES_PATH, "r") as f:
                return f.read()
        return json.dumps(default)

    except Exception as e:
        return json.dumps({"error": str(e)})


# -------------------- CLAUDE INSTRUCTIONS --------------------
@mcp.resource("expense:///instructions", mime_type="text/plain")
def instructions():
    return """
You are an intelligent expense tracking assistant.

STRICT RULES:
- ALWAYS call tools when user mentions money/spending
- NEVER hallucinate values
- ALWAYS return structured JSON
- Use summarize for totals
- Use spending_insights for analysis
- Use charts for visualization
"""


# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        path="/mcp"
    )