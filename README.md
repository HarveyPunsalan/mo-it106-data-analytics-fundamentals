# MotorPH Analytical Dashboard

**MO-IT106 Data Analytics Fundamentals, Milestone 2**

This project cleans the MotorPH product and sales data, checks it, computes the metrics, and builds a four-section dashboard in matplotlib.

## Dashboard sections

1. **MotorPH Overview**: products, categories, units sold, revenue, transactions, top category, top product.
2. **Sales Performance**: monthly revenue, top 5 products, revenue by client type.
3. **Sales by Product Category**: products and share, units sold, revenue.
4. **Inventory**: all 50 products with category, unit price, units sold, and revenue.

## Project structure

```text
.
├── data/
│   ├── raw/                 original MotorPH CSV files
│   └── cleaned/             cleaned products and sales files
├── scripts/
│   ├── MotorPH_Dataset_Preprocessing.py
│   └── MotorPH_MS2_Dashboard.py
├── outputs/
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

Install:

```text
python3 -m pip install -r requirements.txt
```

## How to run

From the project root:

```text
python3 scripts/MotorPH_Dataset_Preprocessing.py
python3 scripts/MotorPH_MS2_Dashboard.py
```

The first script rebuilds the cleaned CSVs from `data/raw/`. The second script runs the quality checks, computes the metrics, and writes the dashboard, inventory close-up, and QA report to `outputs/`.

## Data quality summary

- Raw sales rows: 1,000
- Cleaned sales rows: 991
- Out-of-period rows excluded: 1 (13 January 2025)
- Analyzed sales rows: 990
- Products: 50 in 17 categories
- Units sold: 17,534
- Revenue: ₱4,441,540,000
- Transactions: 990

The checks cover missing values, duplicates, unmatched product names, unit-price mismatches, invalid dates, and `Quantity × Unit Price = Total`. If a check fails, the dashboard script stops instead of producing a wrong chart.
