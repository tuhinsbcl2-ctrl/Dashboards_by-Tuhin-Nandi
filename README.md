# Dashboards by Tuhin Nandi

Interactive business dashboards built with **Streamlit**, **Pandas**, and **Plotly** for analysing Tally sales exports.  
Both dashboards ship with built-in demo data so they run out of the box — no CSV upload required to get started.

---

## 📦 Dashboards Included

### 1. `monthly_sales_dashboard.py` — Monthly Sales & Debtor-wise Analysis

A comprehensive monthly sales dashboard tailored for Tally sales exports with debtor-level drill-down.

**Features:**
- **KPI Cards:** Total Net Sales · Active Debtors · Top Debtor Sales · Top Debtor Share %
- **Top 10 Debtors** bar chart (horizontal)
- **Monthly Sales Trend** line chart
- **Debtor vs Month Heatmap** for quick pattern spotting
- **Sales by State** donut pie chart
- **Debtor-wise Monthly Breakdown** pivot table (downloadable)
- **Customer Segmentation** — Repeat vs New customers
- **Drill-down tabs:** Year → Month → Debtor
- **Sidebar filters:** Year · Month · Debtor · State
- **CSV download** for filtered data and the debtor breakdown table

**Expected dataset columns:**

| Column | Description |
|---|---|
| Date | Transaction date (DD-MM-YYYY or YYYY-MM-DD) |
| Party Name | Debtor / customer name |
| Invoice Number | Unique invoice reference |
| Sales Amount | Gross sales amount (₹) |
| GST Amount | GST charged (optional) |
| State | Place of supply / state |

---

### 2. `sales_dashboard_analysis.py` — Item-wise, HSN-wise & GST-wise Analysis

A CA-style professional dashboard for item, HSN, and GST reporting — ideal for GST return preparation.

**Features:**
- **KPI Cards:** Total Taxable Sales · Total GST · Avg GST Rate · Top HSN Share % · Total Invoices
- **Top Items by Sales** bar chart
- **HSN-wise Sales** bar chart
- **GST Rate Slab Distribution** pie chart
- **Monthly GST Collection Trend** (CGST / SGST / IGST components)
- **Top GST-Generating Items** bar chart
- **Item + HSN + GST Breakdown** table
- **GST Slab-wise Summary** table
- **Anomaly Detection** — flags invoices where effective tax % deviates from declared GST rate
- **Sidebar filters:** Year · Month · GST Rate · Item · HSN Code
- **CSV downloads:** HSN + Item Summary · Full line-item data · Anomalies

**Expected dataset columns:**

| Column | Description |
|---|---|
| Date | Transaction date |
| Invoice Number | Unique invoice reference |
| Party Name | Customer / party name |
| Item Name | Product / service name |
| HSN Code | HSN / SAC code |
| Quantity | Units sold |
| Taxable Value | Taxable amount (₹) |
| GST Rate (%) | Applicable GST rate |
| CGST Amount | Central GST (₹) |
| SGST Amount | State GST (₹) |
| IGST Amount | Integrated GST (₹) |

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Monthly Sales Dashboard

```bash
streamlit run monthly_sales_dashboard.py
```

### 3. Run the Sales & GST Analysis Dashboard

```bash
streamlit run sales_dashboard_analysis.py
```

Both dashboards will open in your default browser at `http://localhost:8501`.

---

## 📂 Upload Your Own Data

In the **sidebar** of each dashboard, use the **"Upload Tally CSV / Excel"** file-uploader to load your real data.  
The file must contain the columns listed in the dataset tables above.  
If no file is uploaded, the dashboard automatically runs on realistic demo data.

---

## 🛠 Tech Stack

| Library | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Dashboard UI & interactivity |
| [Pandas](https://pandas.pydata.org) | Data loading, transformation & aggregation |
| [Plotly](https://plotly.com/python) | Interactive charts |
| [NumPy](https://numpy.org) | Numerical operations & sample-data generation |
| [openpyxl](https://openpyxl.readthedocs.io) | Excel file reading (.xlsx) |

---

## 📁 Repository Structure

```
.
├── monthly_sales_dashboard.py   # Monthly Sales & Debtor-wise dashboard
├── sales_dashboard_analysis.py  # Item / HSN / GST analysis dashboard
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

*Built by Tuhin Nandi — Dashboards for real business insights.*
