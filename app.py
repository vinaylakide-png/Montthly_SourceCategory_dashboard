import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from functools import reduce
import io

# ── Optional MySQL driver (graceful if not installed) ──────────────────────
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# ── Optional Snowflake driver ──────────────────────────────────────────────
try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False

# =============================================================================
#  PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Agency Certification Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
#  CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
.stApp { background-color: #f0f2f5; }
.main .block-container { padding-top: 1rem; padding-bottom: 2rem; }
.dashboard-title {
    background-color: #1a2340; border-radius: 6px;
    padding: 14px 22px; margin-bottom: 20px;
}
.dashboard-title h1 { font-size: 22px; color: #ffffff; font-weight: 700; margin: 0; }
.dashboard-title .caption { color: #a8b4cc; font-size: 13px; margin-top: 4px; }
.metric-card {
    background: #ffffff; border: 1px solid #dce3ee;
    border-top: 4px solid #c9a84c; border-radius: 6px;
    padding: 16px 18px; margin-bottom: 0.75rem;
}
.metric-card .label  { font-size: 11px; color: #6b7a99; text-transform: uppercase; letter-spacing:.06em; margin-bottom: 4px; }
.metric-card .value  { font-size: 26px; font-weight: 700; color: #1a2340; line-height: 1.1; }
.metric-card .delta-pos { color: #2e7d32; font-size: 13px; margin-top: 4px; }
.metric-card .delta-neg { color: #c62828; font-size: 13px; margin-top: 4px; }
.metric-card .delta-neu { color: #6b7a99; font-size: 13px; margin-top: 4px; }
.section-header {
    font-size: 15px; font-weight: 700; color: #1a2340;
    border-bottom: 2px solid #c9a84c; padding-bottom: 6px; margin-bottom: 12px;
}
[data-testid="stSidebar"] { background-color: #1a2340 !important; border-right: none; }
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #c8d0e0 !important; }
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #c9a84c !important; font-size: 12px; text-transform: uppercase; letter-spacing:.08em; }
[data-testid="stSidebar"] hr { border-color: #2e3d5e; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #243059 !important; border: 1px solid #3a4d78 !important;
    border-radius: 4px !important; color: #e2e8f0 !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #c9a84c22 !important; color: #c9a84c !important;
    border: 1px solid #c9a84c55 !important;
}
[data-testid="stSidebar"] input {
    background-color: #243059 !important; color: #e2e8f0 !important;
    border: 1px solid #3a4d78 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background-color: #c9a84c !important; color: #1a2340 !important;
    font-weight: 700; border: none; border-radius: 4px;
}
[data-testid="stSidebar"] .stButton > button:hover { background-color: #e0bf6a !important; }
.stTabs [data-baseweb="tab-list"] { background-color: #ffffff; border-bottom: 2px solid #dce3ee; gap: 0; }
.stTabs [data-baseweb="tab"] { color: #6b7a99; font-size: 13px; font-weight: 500; padding: 8px 16px; }
.stTabs [aria-selected="true"] {
    border-bottom: 3px solid #c9a84c !important;
    color: #1a2340 !important; font-weight: 700 !important;
    background-color: transparent !important;
}
.stDataFrame { border: 1px solid #dce3ee; border-radius: 6px; }
hr { border-color: #dce3ee; margin: 1.2rem 0; }
.stDownloadButton > button {
    background-color: #1a2340 !important; color: #c9a84c !important;
    border: 1px solid #c9a84c !important; border-radius: 4px;
    font-weight: 600; font-size: 12px;
}
.stDownloadButton > button:hover { background-color: #c9a84c !important; color: #1a2340 !important; }

/* ── Main content: force all widget labels and radio text to dark ── */
.main label { color: #1a2340 !important; }
.main p { color: #1a2340 !important; }
.main span { color: #1a2340 !important; }
.main [data-baseweb="radio"] label { color: #1a2340 !important; }
.main [data-baseweb="radio"] p { color: #1a2340 !important; }
.main [data-baseweb="radio"] span { color: #1a2340 !important; }
.main [role="radiogroup"] label { color: #1a2340 !important; }
.main [role="radiogroup"] span { color: #1a2340 !important; }
.main [data-testid="stWidgetLabel"] p { color: #1a2340 !important; }
.main [data-testid="stWidgetLabel"] span { color: #1a2340 !important; }
/* Keep alert/info boxes using their own colours */
.main [data-testid="stAlert"] p { color: inherit !important; }
.main [data-testid="stAlert"] span { color: inherit !important; }
/* Keep chart/dataframe text unaffected */
.main .js-plotly-plot text { color: unset !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
#  CHART CONSTANTS
# =============================================================================
CHART_TEMPLATE = dict(layout=dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(255,255,255,0.97)',
    font=dict(color='#3a4d6e', family='sans-serif', size=12),
    xaxis=dict(gridcolor='#e8ecf2', linecolor='#dce3ee', tickcolor='#6b7a99', showgrid=True),
    yaxis=dict(gridcolor='#e8ecf2', linecolor='#dce3ee', tickcolor='#6b7a99', showgrid=True),
))
BAR_LATEST  = '#c9a84c'; BORD_LATEST  = '#e0bf6a'
BAR_COMPARE = '#8a6fc0'; BORD_COMPARE = '#a98fda'
BAR_DEFAULT = '#1a2340'; BORD_DEFAULT = '#2e3d5e'
TREND_COLOR = '#4a7c59'

# =============================================================================
#  MONTH HELPERS
# =============================================================================
MONTH_FULL = ['January','February','March','April','May','June',
              'July','August','September','October','November','December']
MONTH_ABBR = ['Jan','Feb','Mar','Apr','May','Jun',
              'Jul','Aug','Sep','Oct','Nov','Dec']

def canonical_month(m):
    s = str(m).strip()
    for full in MONTH_FULL:
        if s.lower() == full.lower(): return full
    for abbr, full in zip(MONTH_ABBR, MONTH_FULL):
        if s.lower() == abbr.lower(): return full
    return None

def month_sort_key(ym):
    m, y = ym
    c   = canonical_month(m)
    idx = MONTH_FULL.index(c) if c else 99
    try:    return (int(y), idx)
    except: return (9999, idx)

def get_quarter(month_name):
    idx = MONTH_FULL.index(month_name) + 1 if month_name in MONTH_FULL else 0
    if idx in (1,2,3):    return "Q1 (Jan-Mar)"
    if idx in (4,5,6):    return "Q2 (Apr-Jun)"
    if idx in (7,8,9):    return "Q3 (Jul-Sep)"
    if idx in (10,11,12): return "Q4 (Oct-Dec)"
    return "Unknown"

def get_half(month_name):
    idx = MONTH_FULL.index(month_name) + 1 if month_name in MONTH_FULL else 0
    return "H1 (Jan-Jun)" if idx <= 6 else "H2 (Jul-Dec)"

# =============================================================================
#  DATABASE LOADERS
# =============================================================================
def load_mysql(host, port, user, password, database, query):
    if not MYSQL_AVAILABLE:
        st.error("mysql-connector-python is not installed. Run: pip install mysql-connector-python")
        return None
    try:
        conn = mysql.connector.connect(
            host=host, port=int(port),
            user=user, password=password,
            database=database,
            connection_timeout=15,
        )
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"MySQL connection error: {e}")
        return None

def load_snowflake(account, user, password, warehouse, database, schema, query):
    if not SNOWFLAKE_AVAILABLE:
        st.error("snowflake-connector-python is not installed. Run: pip install snowflake-connector-python")
        return None
    try:
        conn = snowflake.connector.connect(
            account=account, user=user, password=password,
            warehouse=warehouse, database=database, schema=schema,
        )
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Snowflake connection error: {e}")
        return None

def load_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        raw_bytes = uploaded_file.read()
        # Try encodings most common in Windows-exported CSVs
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1", "iso-8859-1"):
            try:
                return pd.read_csv(io.BytesIO(raw_bytes), encoding=enc)
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        # Last resort: chardet auto-detection
        try:
            import chardet
            detected = chardet.detect(raw_bytes)
            enc = detected.get("encoding") or "latin-1"
            st.info(f"ℹ️ Detected encoding: **{enc}** (confidence: {detected.get('confidence', 0):.0%})")
            return pd.read_csv(io.BytesIO(raw_bytes), encoding=enc)
        except ImportError:
            # chardet not installed — force latin-1 which never raises UnicodeDecodeError
            st.warning("⚠️ Could not auto-detect encoding. Falling back to latin-1.")
            return pd.read_csv(io.BytesIO(raw_bytes), encoding="latin-1")
    elif name.endswith((".xlsx", ".xls")):
        xls = pd.ExcelFile(uploaded_file)
        if len(xls.sheet_names) > 1:
            sheet = st.selectbox("Select worksheet", xls.sheet_names)
        else:
            sheet = xls.sheet_names[0]
        return pd.read_excel(uploaded_file, sheet_name=sheet)
    else:
        st.error("Unsupported file type. Upload .csv, .xlsx, or .xls")
        return None

# =============================================================================
#  SIDEBAR — DATA SOURCE
# =============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Data Source")
    src = st.radio(
        "Source",
        ["Upload File (CSV / Excel)", "MySQL", "Snowflake"],
        horizontal=False,
    )
    df_raw = None

    # ── Upload ────────────────────────────────────────────────────────────────
    if src == "Upload File (CSV / Excel)":
        uploaded = st.file_uploader(
            "📁 Drop or browse file",
            type=["csv", "xlsx", "xls"],
            help="CSV, Excel .xlsx or legacy .xls",
        )
        if uploaded:
            df_raw = load_file(uploaded)
            if df_raw is not None:
                st.session_state.df_raw         = df_raw
                st.session_state.source_label   = uploaded.name
                st.success(f"✅ Loaded {len(df_raw):,} rows")

    # ── MySQL ─────────────────────────────────────────────────────────────────
    elif src == "MySQL":
        with st.expander("🔐 MySQL Credentials", expanded=True):
            my_host     = st.text_input("Host",     value="localhost",         key="my_host")
            my_port     = st.text_input("Port",     value="3306",              key="my_port")
            my_user     = st.text_input("User",     value="root",              key="my_user")
            my_pass     = st.text_input("Password", value="",  type="password",key="my_pass")
            my_db       = st.text_input("Database", value="",                  key="my_db")
            my_query    = st.text_area(
                "SQL Query",
                value="SELECT * FROM your_table LIMIT 50000",
                height=90,
                key="my_query",
            )
        if st.button("🔄 Connect & Load", use_container_width=True):
            with st.spinner("Connecting to MySQL…"):
                df_raw = load_mysql(my_host, my_port, my_user, my_pass, my_db, my_query)
            if df_raw is not None:
                st.session_state.df_raw       = df_raw
                st.session_state.source_label = f"MySQL: {my_db}"
                st.success(f"✅ {len(df_raw):,} rows loaded")

    # ── Snowflake ─────────────────────────────────────────────────────────────
    elif src == "Snowflake":
        with st.expander("🔐 Snowflake Credentials", expanded=True):
            sf_account  = st.text_input("Account",   value="yourorg-youracccount", key="sf_acc")
            sf_user     = st.text_input("User",       value="",                    key="sf_user")
            sf_pass     = st.text_input("Password",   value="", type="password",   key="sf_pass")
            sf_wh       = st.text_input("Warehouse",  value="COMPUTE_WH",          key="sf_wh")
            sf_db       = st.text_input("Database",   value="",                    key="sf_db")
            sf_schema   = st.text_input("Schema",     value="PUBLIC",              key="sf_schema")
            sf_query    = st.text_area(
                "SQL Query",
                value="SELECT * FROM your_table LIMIT 50000",
                height=90,
                key="sf_query",
            )
        if st.button("🔄 Connect & Load", use_container_width=True):
            with st.spinner("Connecting to Snowflake…"):
                df_raw = load_snowflake(sf_account, sf_user, sf_pass, sf_wh, sf_db, sf_schema, sf_query)
            if df_raw is not None:
                st.session_state.df_raw       = df_raw
                st.session_state.source_label = f"Snowflake: {sf_db}.{sf_schema}"
                st.success(f"✅ {len(df_raw):,} rows loaded")

    if "df_raw" not in st.session_state:
        st.info("☝️ Load data to begin")
        st.stop()

    df_raw = st.session_state.df_raw.copy()
    df_raw.columns = df_raw.columns.str.strip()
    all_columns = df_raw.columns.tolist()

    # ── Column Mapping ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🏢 Column Mapping")

    def _norm(s): return str(s).lower().replace("_","").replace(" ","")
    all_norm = [_norm(c) for c in all_columns]

    def col_idx(*candidates, fallback=0):
        for name in candidates:
            n = _norm(name)
            if n in all_norm: return all_norm.index(n)
        return min(fallback, len(all_columns)-1)

    agency_id_col   = st.selectbox("Agency ID",          all_columns, index=col_idx("AGENCY_ID","Agency ID","AgencyID"))
    agency_name_col = st.selectbox("Agency Name",        all_columns, index=col_idx("AGENCY_NAME","Agency Name","AgencyName", fallback=min(1,len(all_columns)-1)))
    cert_type_col   = st.selectbox("Certification Type", all_columns, index=col_idx("FINAL_CERTTYPE","CERTIFICATION_TYPE","CertType", fallback=min(2,len(all_columns)-1)))
    month_col       = st.selectbox("Month",              all_columns, index=col_idx("MONTH_NAME","MONTHNAME","Month", fallback=min(3,len(all_columns)-1)))
    year_col        = st.selectbox("Year",               all_columns, index=col_idx("YEAR","Year", fallback=min(4,len(all_columns)-1)))
    count_col       = st.selectbox("Count",              all_columns, index=col_idx("RECORD_COUNT","RecordCount","Count", fallback=min(5,len(all_columns)-1)))

    # ── Optional Filters ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔍 Optional Filters")
    valid_status_col = next((c for c in all_columns if c.upper()=="VALID_CATEGORY_STATUS"), None)
    default_cat_col  = next((c for c in all_columns if c.upper()=="ISDEFAULTCATEGORY_X"),  None)

    if valid_status_col:
        vv = df_raw[valid_status_col].dropna().unique().tolist()
        sel_valid = st.multiselect("Valid Category Status", vv, default=vv)
    else:
        sel_valid = None

    if default_cat_col:
        dv = df_raw[default_cat_col].dropna().unique().tolist()
        sel_default = st.multiselect("IsDefault Category", dv, default=dv)
    else:
        sel_default = None

# =============================================================================
#  DATA PREP
# =============================================================================
df = df_raw.copy()
if sel_valid is not None and valid_status_col:
    df = df[df[valid_status_col].isin(sel_valid)]
if sel_default is not None and default_cat_col:
    df = df[df[default_cat_col].isin(sel_default)]

df[count_col] = pd.to_numeric(df[count_col], errors='coerce').fillna(0)
df[year_col]  = df[year_col].astype(str).str.strip()
df[month_col] = df[month_col].astype(str).str.strip()
df['_month_canon'] = df[month_col].apply(canonical_month)

periods_raw  = df[['_month_canon', year_col]].drop_duplicates().dropna(subset=['_month_canon'])
periods_list = sorted(
    [(r['_month_canon'], r[year_col]) for _, r in periods_raw.iterrows()],
    key=month_sort_key,
)
period_labels = [f"{m} {y}" for m, y in periods_list]

if not period_labels:
    st.error("No valid month periods found. Check your Month and Year column mapping."); st.stop()

# ── Period Selection ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📅 Period Selection")
    latest_label = st.selectbox("🎯 Current Period", period_labels, index=len(period_labels)-1)
    compare_options = [p for p in period_labels if p != latest_label]
    default_compare = [compare_options[-1]] if compare_options else []
    selected_compare_labels = st.multiselect(
        "🔁 Compare Period(s)", compare_options, default=default_compare,
    )
    if not selected_compare_labels:
        st.warning("⚠️ Select at least one compare period."); st.stop()

prev_label        = selected_compare_labels[0]
compare_label_str = ", ".join(selected_compare_labels)

def get_period_df(full_month_name, year):
    return df[(df['_month_canon'] == full_month_name) & (df[year_col] == year)]

latest_month_name, latest_year = latest_label.split(" ", 1)
prev_month_name,   prev_year   = prev_label.split(" ", 1)
df_latest = get_period_df(latest_month_name, latest_year)
df_prev   = get_period_df(prev_month_name,   prev_year)

def cert_sum_for_period(month_name, year):
    return get_period_df(month_name, year).groupby(cert_type_col)[count_col].sum()

# =============================================================================
#  AGGREGATIONS
# =============================================================================
agg_latest = df_latest.groupby([agency_id_col, agency_name_col])[count_col].sum().reset_index()
agg_prev   = df_prev.groupby([agency_id_col, agency_name_col])[count_col].sum().reset_index()
agg_latest.columns = [agency_id_col, agency_name_col, 'count_latest']
agg_prev.columns   = [agency_id_col, agency_name_col, 'count_prev']

agg_merged_kpi = pd.merge(agg_latest, agg_prev, on=[agency_id_col, agency_name_col], how='outer').fillna(0)
agg_merged_kpi['Net_Change'] = (agg_merged_kpi['count_latest'] - agg_merged_kpi['count_prev']).astype(int)
agg_merged_kpi['Pct_Change'] = np.where(
    agg_merged_kpi['count_prev'] > 0,
    ((agg_merged_kpi['Net_Change'] / agg_merged_kpi['count_prev']) * 100).round(1),
    np.nan,
)

df_compare_all    = pd.concat([get_period_df(p.split(" ",1)[0], p.split(" ",1)[1]) for p in selected_compare_labels])
agg_compare_all   = df_compare_all.groupby([agency_id_col, agency_name_col])[count_col].sum().reset_index()
agg_compare_all.columns = [agency_id_col, agency_name_col, 'count_compare']

latest_total  = int(agg_latest['count_latest'].sum())
compare_total = int(agg_compare_all['count_compare'].sum())
net_change    = latest_total - compare_total
pct_change    = float(net_change / compare_total * 100) if compare_total > 0 else 0.0
unique_latest  = int((agg_latest['count_latest'] >= 1).sum())
unique_compare = int((agg_compare_all['count_compare'] >= 1).sum())
unique_delta   = unique_latest - unique_compare

total_records    = int(len(df))
total_agencies   = int(df[agency_id_col].nunique())
total_cert_types = int(df[cert_type_col].nunique())

def delta_class(v): return "delta-pos" if v > 0 else ("delta-neg" if v < 0 else "delta-neu")
def delta_arrow(v): return "▲" if v > 0 else ("▼" if v < 0 else "─")

# =============================================================================
#  HEADER
# =============================================================================
st.markdown(f"""
<div class="dashboard-title">
  <h1>🏢 Monthly Source Categories Dashboard</h1>
  <div class="caption">
    Source: <b>{st.session_state.source_label}</b> &nbsp;|&nbsp;
    Records: <b>{total_records:,}</b> &nbsp;|&nbsp;
    Agencies: <b>{total_agencies:,}</b> &nbsp;|&nbsp;
    Cert Types: <b>{total_cert_types:,}</b> &nbsp;|&nbsp;
    Current: <b>{latest_label}</b> &nbsp;|&nbsp;
    Compare: <b>{compare_label_str}</b>
  </div>
</div>""", unsafe_allow_html=True)

# =============================================================================
#  KPI ROW
# =============================================================================
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f"""<div class="metric-card">
        <div class="label">Total Suppliers ({latest_label})</div>
        <div class="value">{latest_total:,}</div>
        <div class="{delta_class(net_change)}">{delta_arrow(net_change)} {abs(net_change):,} vs {compare_label_str}</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="metric-card">
        <div class="label">Period-over-Period Change</div>
        <div class="value">{pct_change:+.1f}%</div>
        <div class="{delta_class(net_change)}">{compare_total:,} → {latest_total:,}</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="metric-card">
        <div class="label">Unique Agency IDs (Count ≥ 1)</div>
        <div class="value">{unique_latest:,}</div>
        <div class="{delta_class(unique_delta)}">{delta_arrow(unique_delta)} {abs(unique_delta):,} vs {compare_label_str}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
#  CERT TYPE BREAKDOWN — SIDE-BY-SIDE PIVOT
# =============================================================================
st.markdown(
    f'<div class="section-header">📊 {cert_type_col.title()} Breakdown — Side-by-Side Comparison</div>',
    unsafe_allow_html=True,
)

grouping_mode = st.radio(
    "View by",
    ["Current vs Previous", "Monthly", "Quarterly", "Half-Yearly", "Yearly"],
    horizontal=True,
    key="breakdown_grouping",
)

def _bucket_label(m, y, mode):
    if mode == "Monthly":      return f"{m[:3]} {y}"
    if mode == "Quarterly":    return f"{y} {get_quarter(m)}"
    if mode == "Half-Yearly":  return f"{y} {get_half(m)}"
    if mode == "Yearly":       return str(y)
    return f"{m} {y}"

def build_pivot_side_by_side(mode, included_labels=None):
    bucket_data  = {}
    bucket_order = []
    for m, y in periods_list:
        full_label = f"{m} {y}"
        if included_labels is not None and full_label not in included_labels:
            continue
        bucket = _bucket_label(m, y, mode)
        if bucket not in bucket_data:
            bucket_data[bucket] = {}
            bucket_order.append(bucket)
        grp = get_period_df(m, y).groupby([agency_id_col, agency_name_col, cert_type_col])[count_col].sum()
        for (aid, aname, ctype), val in grp.items():
            key = (aid, aname, ctype)
            bucket_data[bucket][key] = bucket_data[bucket].get(key, 0) + int(val)

    if not bucket_order:
        return pd.DataFrame(), []

    all_keys = sorted(
        {k for bd in bucket_data.values() for k in bd},
        key=lambda k: (k[2], k[1]),
    )
    rows = []
    for key in all_keys:
        aid, aname, ctype = key
        row = {'Agency ID': aid, 'Agency Name': aname, 'Cert Type': ctype}
        for i, bucket in enumerate(bucket_order):
            cur_val = bucket_data[bucket].get(key, 0)
            row[bucket] = cur_val
            if i > 0:
                prev_bucket = bucket_order[i - 1]
                prev_val    = bucket_data[prev_bucket].get(key, 0)
                net         = cur_val - prev_val
                pct         = (net / prev_val * 100) if prev_val > 0 else None
                row[f"{prev_bucket}→{bucket} Chg"] = f"+{net:,}" if net > 0 else f"{net:,}"
                row[f"{prev_bucket}→{bucket} %"]   = f"{pct:+.2f}%" if pct is not None else ("New" if cur_val > 0 else "—")
        rows.append(row)

    if not rows:
        return pd.DataFrame(), []

    interleaved = []
    for i, bucket in enumerate(bucket_order):
        interleaved.append(bucket)
        if i > 0:
            pb = bucket_order[i-1]
            interleaved += [f"{pb}→{bucket} Chg", f"{pb}→{bucket} %"]

    final_cols = ['Agency ID', 'Agency Name', 'Cert Type'] + interleaved
    return pd.DataFrame(rows)[final_cols], bucket_order

if grouping_mode == "Current vs Previous":
    included_cvp = selected_compare_labels + [latest_label]
    pivot_result, bucket_order = build_pivot_side_by_side("Current vs Compare", included_labels=included_cvp)
else:
    pivot_result, bucket_order = build_pivot_side_by_side(grouping_mode)

if not pivot_result.empty:
    st.markdown(
        f'<div class="section-header" style="font-size:13px;">'
        f'📋 {cert_type_col} — {grouping_mode} | {len(bucket_order)} period(s)'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.info(
        f"🔍 **{len(pivot_result):,} rows** across "
        f"**{pivot_result['Agency Name'].nunique():,} agencies** and "
        f"**{pivot_result['Cert Type'].nunique():,} cert types** | "
        f"Periods: {' → '.join(bucket_order)}"
    )
    fc2, fc1 = st.columns(2)
    with fc1:
        cert_filter = st.multiselect("Filter by Cert Type", sorted(pivot_result['Cert Type'].unique()), key="piv_cert")
    with fc2:
        agency_filter = st.multiselect("Filter by Agency Name", sorted(pivot_result['Agency Name'].unique()), key="piv_agency")

    dp = pivot_result.copy()
    if agency_filter: dp = dp[dp['Agency Name'].isin(agency_filter)]
    if cert_filter:   dp = dp[dp['Cert Type'].isin(cert_filter)]

    def style_pivot(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        for col in df.columns:
            if col.endswith(' Chg'):
                for i, val in enumerate(df[col]):
                    try:
                        n = float(str(val).replace(',','').replace('+',''))
                        styles.iloc[i][col] = ('color: #2e7d32; font-weight: 600' if n > 0 else 'color: #c62828; font-weight: 600') if n != 0 else ''
                    except: pass
            elif col.endswith(' %'):
                for i, val in enumerate(df[col]):
                    try:
                        n = float(str(val).replace('%',''))
                        styles.iloc[i][col] = 'color: #2e7d32; font-style: italic' if n > 0 else ('color: #c62828; font-style: italic' if n < 0 else '')
                    except: pass
        return styles

    row_h  = min(600, max(300, len(dp) * 35 + 60))
    styled = dp.style.apply(style_pivot, axis=None)
    st.dataframe(styled, use_container_width=True, height=row_h)
    st.download_button(
        "⬇️ Download Side-by-Side Comparison",
        dp.to_csv(index=False),
        f"cert_sidebyside_{grouping_mode.lower().replace(' ','_')}.csv",
    )
else:
    st.warning("No data available for the selected mode/periods.")

st.markdown("---")

# =============================================================================
#  UNIQUE AGENCIES TREND
# =============================================================================
st.markdown('<div class="section-header">🏢 Unique Agency IDs per Period</div>', unsafe_allow_html=True)
trend_rows = []
for m, y in periods_list:
    agg = get_period_df(m, y).groupby(agency_id_col)[count_col].sum()
    trend_rows.append({'Period': f"{m} {y}", 'Unique_Agency_IDs': int((agg >= 1).sum())})
trend_df = pd.DataFrame(trend_rows)

fig_unique = go.Figure()
for _, row in trend_df.iterrows():
    is_l = row['Period'] == latest_label
    is_c = row['Period'] in selected_compare_labels
    fig_unique.add_trace(go.Bar(
        x=[row['Period']], y=[row['Unique_Agency_IDs']],
        marker=dict(
            color=BAR_LATEST if is_l else (BAR_COMPARE if is_c else BAR_DEFAULT),
            line=dict(color=BORD_LATEST if is_l else (BORD_COMPARE if is_c else BORD_DEFAULT), width=1.5),
        ),
        text=[f"{row['Unique_Agency_IDs']:,}"], textposition='outside',
        textfont=dict(size=10, color='#3a4d6e'), showlegend=False, name=row['Period'],
    ))
fig_unique.add_trace(go.Scatter(
    x=trend_df['Period'], y=trend_df['Unique_Agency_IDs'],
    mode='lines+markers', line=dict(color=TREND_COLOR, width=2),
    marker=dict(size=6, color=TREND_COLOR), name='Trend', showlegend=True,
))
fig_unique.update_layout(
    **CHART_TEMPLATE['layout'], height=360,
    yaxis_title='Unique Agency IDs', bargap=0.25,
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0)'),
    margin=dict(t=10, b=60, l=60, r=30),
)
fig_unique.update_xaxes(tickangle=35)
st.plotly_chart(fig_unique, use_container_width=True)

st.markdown("---")

# =============================================================================
#  MONTHLY TOTALS + TOP MOVERS
# =============================================================================
col1, col2 = st.columns([3, 2])
with col1:
    st.markdown('<div class="section-header">📈 Total Certifications per Period</div>', unsafe_allow_html=True)
    total_trend = [{'Period': f"{m} {y}", 'Total': int(get_period_df(m, y)[count_col].sum())} for m, y in periods_list]
    total_trend_df = pd.DataFrame(total_trend)

    fig_months = go.Figure()
    for _, row in total_trend_df.iterrows():
        is_l = row['Period'] == latest_label
        is_c = row['Period'] in selected_compare_labels
        fig_months.add_trace(go.Bar(
            x=[row['Period']], y=[row['Total']],
            marker=dict(
                color=BAR_LATEST if is_l else (BAR_COMPARE if is_c else BAR_DEFAULT),
                line=dict(color=BORD_LATEST if is_l else (BORD_COMPARE if is_c else BORD_DEFAULT), width=1.5),
            ),
            text=[f"{row['Total']:,}"], textposition='outside',
            textfont=dict(size=10, color='#3a4d6e'), showlegend=False, name=row['Period'],
        ))
    fig_months.add_trace(go.Scatter(
        x=total_trend_df['Period'], y=total_trend_df['Total'],
        mode='lines+markers', line=dict(color=TREND_COLOR, width=2),
        marker=dict(size=6, color=TREND_COLOR), name='Trend', yaxis='y2', showlegend=True,
    ))
    fig_months.update_layout(
        **CHART_TEMPLATE['layout'], height=400,
        yaxis2=dict(overlaying='y', side='right', showgrid=False, tickfont=dict(color=TREND_COLOR)),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0)'),
        bargap=0.25, margin=dict(t=10, b=60, l=50, r=50),
    )
    fig_months.update_xaxes(tickangle=35)
    st.plotly_chart(fig_months, use_container_width=True)

with col2:
    st.markdown('<div class="section-header">🔥 Top Agency Movers</div>', unsafe_allow_html=True)

    def _build_movers(subset, increasing=True):
        d = subset[[agency_id_col, agency_name_col, 'Net_Change', 'Pct_Change']].copy()
        d.columns = ['Agency ID', 'Agency Name', 'Net Δ', '% Δ']
        if increasing:
            d['Net Δ'] = d['Net Δ'].apply(lambda x: f"+{int(x):,}")
            d['% Δ']   = d['% Δ'].apply(lambda x: f"+{x:.1f}%" if pd.notna(x) else "New")
        else:
            d['Net Δ'] = d['Net Δ'].apply(lambda x: f"{int(x):,}")
            d['% Δ']   = d['% Δ'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
        return d.reset_index(drop=True)

    st.markdown("**🏆 Top 5 Increasing**")
    st.dataframe(_build_movers(agg_merged_kpi.nlargest(5, 'Net_Change'), True), height=195, use_container_width=True)
    st.markdown("**📉 Top 5 Decreasing**")
    st.dataframe(_build_movers(agg_merged_kpi.nsmallest(5, 'Net_Change'), False), height=195, use_container_width=True)

st.markdown("---")

# =============================================================================
#  DATA REPORT TABS
# =============================================================================
st.markdown('<div class="section-header">📋 Data Reports</div>', unsafe_allow_html=True)
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Period Totals", "🏢 Unique Agencies / Period", "🔄 All Agency Changes",
    f"📊 {cert_type_col} Breakdown", "🏆 Top Gainers", "📉 Top Losers", "💾 Full Dataset",
])

with tab1:
    t1_df = total_trend_df.copy()
    t1_df['PoP_Change'] = t1_df['Total'].diff().fillna(0).astype(int)
    t1_df['PoP_%']      = (t1_df['Total'].pct_change() * 100).round(1).fillna(0)
    st.dataframe(t1_df, use_container_width=True)
    st.download_button("⬇️ Download", t1_df.to_csv(index=False), "period_totals.csv")

with tab2:
    u_df = trend_df.copy()
    u_df['MoM_Change'] = u_df['Unique_Agency_IDs'].diff().fillna(0).astype(int)
    st.dataframe(u_df, use_container_width=True)
    st.download_button("⬇️ Download", u_df.to_csv(index=False), "unique_agencies_per_period.csv")
    st.markdown(f"**Active in {latest_label}**")
    active = df_latest.groupby([agency_id_col, agency_name_col])[count_col].sum().reset_index()
    active = active[active[count_col] >= 1].sort_values(count_col, ascending=False)
    st.dataframe(active, height=350, use_container_width=True)
    st.download_button("⬇️ Download Active", active.to_csv(index=False), "active_agencies.csv")
    st.markdown(f"**Inactive in {latest_label}** (count = 0)")
    inactive = df_latest.groupby([agency_id_col, agency_name_col])[count_col].sum().reset_index()
    inactive = inactive[inactive[count_col] <= 0]
    st.dataframe(inactive, height=300, use_container_width=True)
    st.download_button("⬇️ Download Inactive", inactive.to_csv(index=False), "inactive_agencies.csv")

with tab3:
    t3_df = agg_merged_kpi.copy()
    t3_df.columns = [agency_id_col, agency_name_col,
                     f'Count_{latest_label}', f'Count_{prev_label}', 'Net_Change', 'Pct_Change_%']
    t3_df = t3_df.sort_values('Net_Change', key=abs, ascending=False)
    st.dataframe(t3_df, height=400, use_container_width=True)
    st.download_button("⬇️ Download", t3_df.to_csv(index=False), "agency_changes.csv")

with tab4:
    cert_all = []
    for m, y in periods_list:
        s = cert_sum_for_period(m, y).reset_index()
        s.columns = [cert_type_col, f"{m} {y}"]
        cert_all.append(s)
    if cert_all:
        cert_pivot = reduce(lambda a, b: pd.merge(a, b, on=cert_type_col, how='outer'), cert_all).fillna(0)
        for c in cert_pivot.columns:
            if c != cert_type_col:
                cert_pivot[c] = cert_pivot[c].astype(int)
        if latest_label in cert_pivot.columns:
            cert_pivot = cert_pivot.sort_values(latest_label, ascending=False)
        t4_grp = st.selectbox("View level", ["Monthly (all periods)", "Quarterly", "Half-Yearly", "Yearly"], key="t4g")
        if t4_grp == "Monthly (all periods)":
            st.dataframe(cert_pivot, use_container_width=True)
            st.download_button("⬇️ Download", cert_pivot.to_csv(index=False), "cert_monthly.csv")
        else:
            g_mode = t4_grp.split(" ")[0]
            rows_agg = []
            for m, y in periods_list:
                glabel = (f"{y} {get_quarter(m)}" if g_mode == "Quarterly"
                          else (f"{y} {get_half(m)}" if g_mode == "Half-Yearly" else str(y)))
                for ct, val in cert_sum_for_period(m, y).items():
                    rows_agg.append({'Period': glabel, cert_type_col: ct, 'val': int(val)})
            if rows_agg:
                agg_wide = (
                    pd.DataFrame(rows_agg)
                    .groupby(['Period', cert_type_col])['val'].sum().reset_index()
                    .pivot_table(index=cert_type_col, columns='Period', values='val', aggfunc='sum', fill_value=0)
                    .reset_index()
                )
                agg_wide.columns.name = None
                st.dataframe(agg_wide, use_container_width=True)
                st.download_button("⬇️ Download", agg_wide.to_csv(index=False), f"cert_{t4_grp.lower().replace(' ','-')}.csv")

# Shared pivot for tabs 5 & 6
agg_base = df.groupby([agency_id_col, agency_name_col, cert_type_col, '_month_canon', year_col])[count_col].sum().reset_index()
agg_base['_period'] = agg_base['_month_canon'] + ' ' + agg_base[year_col]
pivot_compare = agg_base.pivot_table(
    index=[agency_id_col, agency_name_col, cert_type_col],
    columns='_period', values=count_col, fill_value=0,
).reset_index()
pivot_compare.columns.name = None

cols_needed = [c for c in [prev_label, latest_label] if c in pivot_compare.columns]
agg_cert_merged = pivot_compare[[agency_id_col, agency_name_col, cert_type_col] + cols_needed].copy()
if prev_label in agg_cert_merged.columns and latest_label in agg_cert_merged.columns:
    agg_cert_merged['Net_Change']  = agg_cert_merged[latest_label] - agg_cert_merged[prev_label]
    agg_cert_merged['Pct_Change_%'] = np.where(
        agg_cert_merged[prev_label] > 0,
        (agg_cert_merged['Net_Change'] / agg_cert_merged[prev_label] * 100).round(2),
        np.nan,
    )
    col_map = {
        agency_id_col: agency_id_col, agency_name_col: agency_name_col, cert_type_col: cert_type_col,
        latest_label: f'Count_{latest_label}', prev_label: f'Count_{prev_label}',
    }
else:
    agg_cert_merged['Net_Change'] = 0
    agg_cert_merged['Pct_Change_%'] = np.nan

with tab5:
    tg = agg_cert_merged.nlargest(20, 'Net_Change').copy()
    st.dataframe(tg, use_container_width=True)
    st.download_button("⬇️ Download", tg.to_csv(index=False), "top_gainers.csv")

with tab6:
    tl = agg_cert_merged.nsmallest(20, 'Net_Change').copy()
    st.dataframe(tl, use_container_width=True)
    st.download_button("⬇️ Download", tl.to_csv(index=False), "top_losers.csv")

with tab7:
    st.caption("Full dataset — one row per agency + cert type, all periods side-by-side with PoP change columns.")
    pivot_base = df.groupby([agency_id_col, agency_name_col, cert_type_col, '_month_canon', year_col])[count_col].sum().reset_index()
    pivot_base['_period'] = pivot_base['_month_canon'] + ' ' + pivot_base[year_col]
    agency_pivot = pivot_base.pivot_table(
        index=[agency_id_col, agency_name_col, cert_type_col],
        columns='_period', values=count_col, aggfunc='sum', fill_value=0,
    ).reset_index()
    agency_pivot.columns.name = None

    period_cols_present = [p for p in period_labels if p in agency_pivot.columns]
    agency_pivot = agency_pivot[[agency_id_col, agency_name_col, cert_type_col] + period_cols_present]

    def short_label(ps):
        parts = ps.split(" ", 1)
        return f"{parts[0][:3]}-{parts[1]}" if len(parts) > 1 else ps

    final_cols_data = {
        agency_id_col: agency_pivot[agency_id_col],
        agency_name_col: agency_pivot[agency_name_col],
        cert_type_col: agency_pivot[cert_type_col],
    }
    for i, p in enumerate(period_cols_present):
        final_cols_data[p] = agency_pivot[p].astype(int)
        if i > 0:
            pp  = period_cols_present[i - 1]
            net = agency_pivot[p].astype(int) - agency_pivot[pp].astype(int)
            pct = np.where(agency_pivot[pp] > 0, (net / agency_pivot[pp] * 100).round(2), np.nan)
            final_cols_data[f"{short_label(p)} Chg"]  = net
            final_cols_data[f"{short_label(p)} Chg%"] = pd.Series(pct).map(
                lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"
            )

    full_display = pd.DataFrame(final_cols_data).reset_index(drop=True)
    if len(period_cols_present) >= 2:
        lcc = f"{short_label(period_cols_present[-1])} Chg"
        if lcc in full_display.columns:
            full_display = full_display.sort_values(lcc, key=abs, ascending=False)

    # Filters
    f1, f2 = st.columns(2)
    with f1:
        fa = st.multiselect("Filter Agency", sorted(full_display[agency_name_col].unique()), key="t7_ag")
    with f2:
        fc = st.multiselect("Filter Cert Type", sorted(full_display[cert_type_col].unique()), key="t7_ct")
    disp = full_display.copy()
    if fa: disp = disp[disp[agency_name_col].isin(fa)]
    if fc: disp = disp[disp[cert_type_col].isin(fc)]

    st.info(f"📊 **{len(disp):,} rows** | **{disp[agency_name_col].nunique():,} agencies** | **{disp[cert_type_col].nunique():,} cert types**")
    st.dataframe(disp, height=480, use_container_width=True)
    st.download_button("⬇️ Download Full Data", disp.to_csv(index=False), "full_data.csv")
