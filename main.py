from fastmcp import FastMCP, Context
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
    import sqlite3
    with sqlite3.connect(DB_PATH) as c:
        c.execute("PRAGMA journal_mode=WAL")

        # create table with user_id
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

        print("Database initialized with user isolation")


init_db()


# -------------------- HELPER: GET USER --------------------
def get_user_id(ctx: Context):
    return ctx.headers.get("x-user-id", "default_user")


# -------------------- ADD EXPENSE --------------------
@mcp.tool()
async def add_expense(ctx: Context, date, amount, category, subcategory="", note=""):
    user_id = get_user_id(ctx)

    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """INSERT INTO expenses(user_id, date, amount, category, subcategory, note)
                   VALUES (?,?,?,?,?,?)""",
                (user_id, date, amount, category, subcategory, note)
            )
            await c.commit()

            return {
                "status": "ok",
                "user_id": user_id,
                "id": cur.lastrowid,
                "summary": f"Added {amount} {BASE_CURRENCY} for {category}"
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- DELETE EXPENSE --------------------
@mcp.tool()
async def delete_expense(ctx: Context, expense_id: int):
    user_id = get_user_id(ctx)

    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "DELETE FROM expenses WHERE id = ? AND user_id = ?",
                (expense_id, user_id)
            )
            await c.commit()

            if cur.rowcount == 0:
                return {"status": "error", "message": "Expense not found"}

            return {"status": "ok", "deleted_id": expense_id}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- LIST EXPENSES --------------------
@mcp.tool()
async def list_expenses(ctx: Context, start_date, end_date):
    user_id = get_user_id(ctx)

    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """SELECT id, date, amount, category, subcategory, note
                   FROM expenses
                   WHERE user_id = ? AND date BETWEEN ? AND ?
                   ORDER BY date DESC, id DESC""",
                (user_id, start_date, end_date)
            )

            cols = [d[0] for d in cur.description]
            rows = await cur.fetchall()

            return {
                "user_id": user_id,
                "count": len(rows),
                "data": [dict(zip(cols, r)) for r in rows]
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- SUMMARY --------------------
@mcp.tool()
async def summarize(ctx: Context, start_date, end_date):
    user_id = get_user_id(ctx)

    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT category, SUM(amount)
                FROM expenses
                WHERE user_id = ? AND date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY SUM(amount) DESC
                """,
                (user_id, start_date, end_date)
            )
            rows = await cur.fetchall()

        total = sum(r[1] for r in rows) if rows else 0

        return {
            "user_id": user_id,
            "total_spent": total,
            "breakdown": dict(rows),
            "summary": f"Total spending is {total} {BASE_CURRENCY}"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -------------------- INSIGHTS --------------------
@mcp.tool()
async def spending_insights(ctx: Context, start_date, end_date):
    user_id = get_user_id(ctx)

    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT category, SUM(amount)
                FROM expenses
                WHERE user_id = ? AND date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY SUM(amount) DESC
                """,
                (user_id, start_date, end_date)
            )
            rows = await cur.fetchall()

        total = sum(r[1] for r in rows) if rows else 0
        top = rows[0] if rows else ("None", 0)

        return {
            "user_id": user_id,
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
async def category_spending_chart(ctx: Context, start_date, end_date):
    user_id = get_user_id(ctx)

    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT category, SUM(amount)
                FROM expenses
                WHERE user_id = ? AND date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY SUM(amount) DESC
                """,
                (user_id, start_date, end_date)
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
async def daily_spending_trend(ctx: Context, start_date, end_date):
    user_id = get_user_id(ctx)

    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT date, SUM(amount)
                FROM expenses
                WHERE user_id = ? AND date BETWEEN ? AND ?
                GROUP BY date
                ORDER BY date
                """,
                (user_id, start_date, end_date)
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


# -------------------- INSTRUCTIONS --------------------
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