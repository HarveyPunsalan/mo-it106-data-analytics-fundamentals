# MotorPH Data Analytics Project

**MO-IT106 Data Analytics Fundamentals**

This project cleans the MotorPH product and Q3 2025 sales data, checks data quality, computes descriptive and inferential statistics, and builds the dashboard and terminal assessment outputs.

## What it covers

1. **Data preparation**: rebuilds the cleaned product and sales files from the raw CSVs, with checks for missing values, duplicates, bad dates, unmatched product names, price mismatches, and `Quantity x Unit Price = Total`.
2. **Milestone 2 dashboard**: builds the four-section dashboard in matplotlib, the inventory close-up, and the QA report.
3. **Terminal assessment**: computes the product, sales, and inferential results used in the report: the four homework tests, monthly and category totals, and the unit and revenue rankings.

## Project structure

```text
.
├── data/
│   ├── raw/                 original MotorPH CSV files
│   └── cleaned/             cleaned products and sales files
├── scripts/
│   ├── MotorPH_Dataset_Preprocessing.py
│   ├── MotorPH_MS2_Dashboard.py
│   └── MotorPH_Terminal_Assessment_Analysis.py
├── outputs/
│   ├── MotorPH_Inferential_Charts.png
│   ├── MotorPH_Inferential_Results.txt
│   ├── MotorPH_MS2_Dashboard.png
│   ├── MotorPH_MS2_Inventory.png
│   └── MotorPH_MS2_QA.txt
├── .gitignore
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.13
- pandas 3.0.6
- matplotlib 3.11.2
- scipy 1.18.1

Install:

```text
python3 -m pip install -r requirements.txt
```

## How to run

From the project root:

```text
python3 scripts/MotorPH_Dataset_Preprocessing.py
python3 scripts/MotorPH_MS2_Dashboard.py
python3 scripts/MotorPH_Terminal_Assessment_Analysis.py
```

The first script rebuilds the cleaned CSVs from `data/raw/`. The second runs the quality checks, computes the dashboard metrics, and writes the dashboard, inventory close-up, and QA report to `outputs/`. The third re-runs the checks and writes the inferential results and the four-panel chart to `outputs/`.

## Data quality summary

- Raw sales rows: 1,000
- Cleaned sales rows: 991
- Out-of-period rows excluded: 1 (13 January 2025)
- Analyzed sales rows: 990
- Products: 50 in 17 categories
- Units sold: 17,534
- Revenue: ₱4,441,540,000
- Transactions: 990

The checks cover missing values, duplicates, unmatched product names, unit-price mismatches, invalid dates, and `Quantity x Unit Price = Total`. If a check fails, the scripts stop instead of producing a wrong chart or result.
