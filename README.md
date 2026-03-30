# Agency Certification Dashboard

Streamlit dashboard — runs locally in VS Code, connects to **MySQL**, **Snowflake**, or uploads **CSV / Excel** files.

---

## Quick Start

### 1. Prerequisites
- Python 3.10 or 3.11 recommended
- VS Code with the **Python** extension installed

---

### 2. Clone / Download
Place the `agency_dashboard/` folder anywhere on your machine, for example:
```
C:\Projects\agency_dashboard\
```

---

### 3. Create a virtual environment (recommended)

Open the `agency_dashboard` folder in VS Code, then open the **Terminal** (`` Ctrl+` ``):

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

---

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** If you do not need Snowflake, you can skip that package:
> ```bash
> pip install streamlit pandas plotly numpy openpyxl xlrd mysql-connector-python
> ```

---

### 5. Run the app

```bash
streamlit run app.py
```

The browser opens automatically at `http://localhost:8501`.

---

## Data Source Options

### A — Upload File (CSV or Excel)
1. In the sidebar select **"Upload File (CSV / Excel)"**.
2. Drag-and-drop or browse for your `.csv`, `.xlsx`, or `.xls` file.
3. If the Excel file has multiple sheets you will be prompted to pick one.

---

### B — MySQL
1. Select **"MySQL"** in the sidebar.
2. Fill in the connection form:

| Field    | Example            |
|----------|--------------------|
| Host     | `localhost`        |
| Port     | `3306`             |
| User     | `root`             |
| Password | `your_password`    |
| Database | `my_database`      |
| Query    | `SELECT * FROM agency_certs LIMIT 100000` |

3. Click **Connect & Load**.

**Required MySQL packages are already in requirements.txt.**  
If you get a connection error check that:
- MySQL server is running
- The user has `SELECT` privileges on the database
- Firewall / VPN allows the connection

---

### C — Snowflake
1. Select **"Snowflake"** in the sidebar.
2. Fill in:

| Field     | Example                   |
|-----------|---------------------------|
| Account   | `myorg-myaccount`         |
| User      | `your_user`               |
| Password  | `your_password`           |
| Warehouse | `COMPUTE_WH`              |
| Database  | `MY_DB`                   |
| Schema    | `PUBLIC`                  |
| Query     | `SELECT * FROM my_table`  |

3. Click **Connect & Load**.

---

## Expected Data Columns

The dashboard auto-detects columns by name. Use the **Column Mapping** section in the sidebar to override.

| Logical Field     | Common column names looked for                              |
|-------------------|-------------------------------------------------------------|
| Agency ID         | `AGENCY_ID`, `Agency ID`, `AgencyID`                       |
| Agency Name       | `AGENCY_NAME`, `Agency Name`, `AgencyName`                 |
| Certification Type| `FINAL_CERTTYPE`, `CERTIFICATION_TYPE`, `CertType`         |
| Month             | `MONTH_NAME`, `MONTHNAME`, `Month Name`, `Month`           |
| Year              | `YEAR`, `Year`                                              |
| Count             | `RECORD_COUNT`, `Record Count`, `RecordCount`, `Count`     |

Month values can be full names (`January`) or 3-letter abbreviations (`Jan`).

---

## VS Code Tips

- Install the **Python** and **Pylance** extensions for IntelliSense.
- Set your interpreter to the `.venv` you created: `Ctrl+Shift+P` → *Python: Select Interpreter*.
- To stop the app press `Ctrl+C` in the terminal.
- To restart after code changes just save the file — Streamlit hot-reloads automatically.

---

## Project Structure

```
agency_dashboard/
├── app.py            ← main application
├── requirements.txt  ← all Python dependencies
└── README.md         ← this file
```
