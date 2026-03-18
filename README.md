# 💰 Expense Tracker MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/FastMCP-v3.1.1-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance, lightweight **Model Context Protocol (MCP)** server for managing personal expenses. Built with Python and SQLite, it allows LLMs (like Claude) to track, categorize, and analyze spending patterns directly through a standardized interface.

---

## ✨ Features

- **Quick Entry**: Add expenses with date, amount, category, and notes in seconds.
- **Async Engine**: Powered by `aiosqlite` and `FastMCP` for non-blocking operations.
- **Smart Categorization**: Pre-configured with 160+ subcategories across 20 major categories (Food, Travel, Health, etc.).
- **Spending Insights**: Generate summaries and pinpoint top-spending categories over specific date ranges.
- **Flexible Transport**: Use via Standard Input (stdio) for local clients or HTTP for distributed setups.
- **Persistence**: Local SQLite backend ensuring data ownership and privacy.

---

## 🏗️ Architecture

```text
┌─────────────────┐       ┌──────────────────────────┐       ┌─────────────────┐
│                 │       │   Expense Tracker MCP    │       │                 │
│   MCP Client    │ ─────▶│   (FastMCP / Python)     │ ─────▶│   SQLite DB     │
│ (Claude/Cursor) │ ◀─────│                          │ ◀─────│ (expenses.db)   │
│                 │       └──────────────────────────┘       └─────────────────┘
         │                             │
         └────── Transport Layer ──────┘
              (stdio or HTTP)
```

---

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Framework**: [FastMCP](https://github.com/jlowin/fastmcp)
- **Database**: SQLite (Asynchronous via `aiosqlite`)
- **Dependency Management**: `uv` or `pip`

---

## 🚀 Installation

### 1. Prerequisite
Ensure you have Python 3.10 or higher installed.

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/Expense_Tracker_MCP_Server.git
cd Expense_Tracker_MCP_Server
```

### 3. Setup Virtual Environment
Using `uv` (recommended):
```bash
uv venv
source .venv/bin/activate
uv sync
```

Using `pip`:
```bash
python -m venv .venv
source .venv/bin/activate
pip install fastmcp aiosqlite
```

---

## 🏃 Running the Project

### Local Mode (Standard Input)
Ideal for use with Claude Desktop or other local clients.
```bash
python main.py
```

### HTTP Mode
Run the server as a web service.
```bash
MODE=http python main.py
```
*Accessible at `http://0.0.0.0:8000/mcp`*

### Claude Desktop Configuration
Add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "python",
      "args": ["/path/to/Expense_Tracker_MCP_Server/main.py"]
    }
  }
}
```

---

## 🧰 Available MCP Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `add_expense` | `date`, `amount`, `category`, `subcategory`, `note` | Record a new expense. |
| `delete_expense` | `expense_id` | Remove an existing record by ID. |
| `list_expenses` | `start_date`, `end_date` | Retrieve list of expenses in a range. |
| `summarize` | `start_date`, `end_date` | Get total spent and category breakdown. |
| `spending_insights`| `start_date`, `end_date` | Detailed analysis of top categories. |

---

## 📖 Example Usage

### Input (`add_expense`)
```json
{
  "date": "2024-03-20",
  "amount": 1250.50,
  "category": "food",
  "subcategory": "dining_out",
  "note": "Dinner with team"
}
```

### Output
```json
{
  "status": "ok",
  "user_id": "local_user",
  "id": 42,
  "summary": "Added 1250.5 INR for food"
}
```

---

## ⚠️ Limitations

- **Currency**: Fixed to `INR` (can be modified in `main.py`).
- **Storage**: Default database located at `/tmp/expenses.db` (volatile on restart for some OS).
- **Authentication**: Basic `x-user-id` header/env support; no OAuth/JWT implemented.

---

## 👤 Author

**Mahin Hussain**  

- GitHub: [@mahinhussain1201](https://github.com/mahinhussain1201)
- LinkedIn: [In/MahinHussain](https://linkedin.com/in/mahinhussain)
