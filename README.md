# Dashboards by Tuhin Nandi

Interactive business dashboards built with **Streamlit**, **Pandas**, and **Plotly** for analysing Tally sales exports.  
Both dashboards ship with built-in demo data so they run out of the box — no CSV upload required to get started.

---

## 📦 Dashboards Included

### 1. `monthly_sales_dashboard.py` — Monthly Sales & Debtor-wise Analysis

A comprehensive monthly sales dashboard tailored for Tally sales exports with debtor-level drill-down.

**Features:**
- **KPI Cards:** Taxable Value · Invoice Value · Total GST · Active Debtors · Total Invoices
- **Top 10 Debtors** bar chart (horizontal)
- **Monthly Sales Trend** line chart (Taxable Value vs Invoice Value)
- **Debtor vs Month Heatmap** for quick pattern spotting
- **Sales by State** donut chart (auto-extracted from party name suffix, e.g. `_MH`)
- **Debtor Type Distribution** donut chart (MF Drs, Equity Drs, etc.)
- **GST Summary tab:** IGST vs CGST+SGST split by month, GST rate slab breakdown
- **Debtor-wise Monthly Breakdown** pivot table (downloadable)
- **GSTIN-wise analysis** with data-quality indicator (missing GSTIN count)
- **Customer Segmentation** — Repeat vs New customers
- **Drill-down tabs:** Year → Month → Debtor
- **Sidebar filters:** Year · Month · Debtor · State · Debtor Type
- **CSV download** for filtered data and the debtor breakdown table
- **Data Preview tab** with raw data and quality indicators

**Supported dataset columns (Tally export — primary format):**

| Column | Tally Header | Description |
|---|---|---|
| Date | Date | Transaction date (`DD-Mon-YY`, e.g. `01-Apr-25`) |
| Month | Month | Month label (e.g. `Apr25`) |
| Year | Year | 4-digit year |
| Party Name | PartyName | Debtor name (state code suffix auto-stripped, e.g. `_MH`) |
| Invoice Number | VoucherNo | Voucher / invoice reference |
| GSTIN | GSTIN | Party's GSTIN number |
| Taxable Value | TaxableValue | Taxable amount (₹) |
| IGST Amount | IGST | Integrated GST (empty for intra-state) |
| CGST Amount | CGST | Central GST (empty for inter-state) |
| SGST Amount | SGST | State GST (empty for inter-state) |
| Total GST | TotalGST | Sum of IGST/CGST/SGST |
| GST Rate (%) | GST Rate | GST rate as string `18%` — auto-parsed |
| Invoice Value | InvoiceValue | Taxable Value + Total GST |
| Debtor Type | DrsType | Debtor category (e.g. `MF Drs`) |

> **Backward compatibility:** The old format (`Party Name`, `Invoice Number`, `Sales Amount`, `GST Amount`, `State`) is still fully supported.

---

### 2. `sales_dashboard_analysis.py` — Party-wise, GST-wise & GSTIN Analysis

A CA-style professional dashboard for party, GST, and GSTIN reporting — ideal for GST return preparation.

**Features:**
- **KPI Cards:** Taxable Value · Invoice Value · Total GST · Avg GST Rate · Total Invoices · Active Debtors
- **Top Debtors by Taxable Value** bar chart
- **Invoice Value vs Taxable Value** monthly trend comparison
- **GST Rate Slab Distribution** pie chart
- **Monthly GST Collection Trend** (CGST / SGST / IGST components)
- **Inter-state vs Intra-state GST** grouped bar chart
- **GSTIN-wise Sales Summary** table with data-quality warning
- **Party-wise Sales Summary** with share %
- **GST Slab-wise Summary** table
- **Anomaly Detection** — flags invoices where effective tax % deviates from declared GST rate
- **Sidebar filters:** Year · Month · GST Rate · Party Name · Debtor Type · Item · HSN Code
- **CSV downloads:** Summary Table · Full line-item data · Anomalies

**Supported dataset columns (same Tally export as above):**

| Column | Tally Header | Description |
|---|---|---|
| Date | Date | Transaction date |
| Party Name | PartyName | Debtor / party name |
| Invoice Number | VoucherNo | Invoice reference |
| GSTIN | GSTIN | Party GSTIN |
| Taxable Value | TaxableValue | Taxable amount (₹) |
| IGST Amount | IGST | Integrated GST |
| CGST Amount | CGST | Central GST |
| SGST Amount | SGST | State GST |
| Total GST | TotalGST | Sum of all GST components |
| GST Rate (%) | GST Rate | Rate as `18%` string — auto-parsed |
| Invoice Value | InvoiceValue | Taxable + Total GST |
| Debtor Type | DrsType | Category (e.g. `MF Drs`) |

> Also supports the legacy item-level format with `Item Name`, `HSN Code`, `Quantity`, `Taxable Value`, `GST Rate (%)`, `CGST Amount`, `SGST Amount`, `IGST Amount`.

---

## 🧾 Tally Export Format Reference

The dashboards natively support the following 14-column Tally export layout:

| Col | Header | Example | Notes |
|---|---|---|---|
| A | **Date** | `01-Apr-25` | Day-first format |
| B | **Month** | `Apr25` | Auto-used for grouping |
| C | **Year** | `2025` | 4-digit |
| D | **PartyName** | `Baroda Bnp Paribas Mutual Fund_MH` | State code suffix auto-stripped |
| E | **VoucherNo** | `FIM/MF/001/25-26` | Used as Invoice Number |
| F | **GSTIN** | `27AAATB0509R1ZL` | GSTIN validation & analysis |
| G | **TaxableValue** | `76.11` | Numeric |
| H | **IGST** | `13.70` | Empty for intra-state transactions |
| I | **CGST** | _(empty)_ | Empty for inter-state transactions |
| J | **SGST** | _(empty)_ | Empty for inter-state transactions |
| K | **TotalGST** | `13.70` | IGST or CGST+SGST |
| L | **GST Rate** | `18%` | `%` sign stripped automatically |
| M | **InvoiceValue** | `89.81` | TaxableValue + TotalGST |
| N | **DrsType** | `MF Drs` | Debtor category filter |

**Key auto-processing steps:**
- `PartyName` suffix like `_MH` is extracted and mapped to the full state name (`Maharashtra`) in a `State` column
- `GST Rate` string (`18%`) is automatically parsed to numeric (`18`)
- Empty `CGST`/`SGST` cells (inter-state) are filled with `0`
- Empty `IGST` cells (intra-state) are filled with `0`

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
The file must contain the Tally export columns listed above (or the legacy format columns).  
If no file is uploaded, the dashboard automatically runs on realistic demo data matching the Tally format.

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
├── sales_dashboard_analysis.py  # Party / GST / GSTIN analysis dashboard
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

*Built by Tuhin Nandi — Dashboards for real business insights.*
