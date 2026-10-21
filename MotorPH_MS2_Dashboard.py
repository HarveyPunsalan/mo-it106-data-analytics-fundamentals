# MotorPH Milestone 2 Dashboard
# Full MS2 submission
# Sales by Product Category, Inventory
# Data-quality report, Heritage deep-dive
# Dependencies: pandas, matplotlib
# Run: python3 MotorPH_MS2_Dashboard.py

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

PRODUCTS_FILE = "MotorPH_Product_List_Cleaned.csv"
SALES_FILE = "MotorPH_Sales_Cleaned.csv"

print("=" * 60)
print("MOTORPH MS2 DASHBOARD")
print("=" * 60)

# 1. LOAD CLEANED DATASETS
print()
print("Loading cleaned datasets...")
products = pd.read_csv(PRODUCTS_FILE)
sales = pd.read_csv(SALES_FILE)
print("Products loaded: " + str(len(products)) + " rows")
print("Sales loaded: " + str(len(sales)) + " rows")

# 2. DATA-QUALITY REPORT
print("-" * 60)
missing_p = products.isnull().sum().sum()
missing_s = sales.isnull().sum().sum()
print("[1] Missing values | products: " + str(missing_p) + " | sales: " + str(missing_s))
dup_p = products.duplicated().sum()
dup_s = sales.duplicated().sum()
print("[2] Duplicate rows | products: " + str(dup_p) + " | sales: " + str(dup_s))
prod_names = set(products["Product Name"])
unmatched = sorted(set(sales["Product"]) - prod_names)
print("[3] Unmatched product names in sales: " + str(len(unmatched)) + " -> " + str(unmatched))
sales["Computed Total"] = sales["Unit Price"] * sales["Quantity"]
mismatch = (sales["Computed Total"] != sales["Total"]).sum()
print("[4] Unit Price x Quantity != Total rows: " + str(mismatch))
sales["Date Parsed"] = pd.to_datetime(sales["Date"], errors="coerce")
unparseable = sales["Date Parsed"].isnull().sum()
print("[5] Unparseable dates: " + str(unparseable))
neg_qty = (sales["Quantity"] <= 0).sum()
neg_price = (sales["Unit Price"] <= 0).sum()
print("[6] Zero/negative Quantity: " + str(neg_qty) + " | Zero/negative Unit Price: " + str(neg_price))
quality_ok = (missing_p == 0 and missing_s == 0 and len(unmatched) == 0 and
              mismatch == 0 and unparseable == 0 and neg_qty == 0 and neg_price == 0)
print()
print("Quality gate passed: " + str(quality_ok))
merged = sales.merge(
    products[["Product Name", "Product Category", "Unit Price"]],
    left_on="Product", right_on="Product Name", how="left",
    suffixes=("", "_product_list"))
price_match = (merged["Unit Price"] == merged["Unit Price_product_list"]).all()
print("[7] Sales unit price matches product list price for every row: " + str(price_match))
print()
# 3. SECTION 1: MOTORPH OVERVIEW
print("-" * 60)
total_products = len(products)
total_categories = products["Product Category"].nunique()
total_units = merged["Quantity"].sum()
total_revenue = merged["Total"].sum()
date_min = merged["Date Parsed"].min().strftime("%b %d, %Y")
date_max = merged["Date Parsed"].max().strftime("%b %d, %Y")
n_txns = len(merged)
avg_order_value = total_revenue / n_txns
top_rev_cat = merged.groupby("Product Category")["Total"].sum().idxmax()
top_units_cat = merged.groupby("Product Category")["Quantity"].sum().idxmax()
print("Total Products: " + str(total_products))
print("Product Categories: " + str(total_categories))
print("Total Units Sold: " + str(total_units))
print("Total Revenue: ₱" + format(total_revenue, ",.0f"))
print("Transactions: " + str(n_txns))
print("Avg Order Value: ₱" + format(avg_order_value, ",.0f"))
print("Sales Period: " + date_min + " - " + date_max)
print("Top Category (Rev): " + top_rev_cat)
print("Top Category (Units): " + top_units_cat)
print()

# 4. SECTION 2: SALES PERFORMANCE
print("-" * 60)
merged["Month"] = merged["Date Parsed"].dt.to_period("M")
monthly = merged.groupby("Month").agg(
    revenue=("Total", "sum"), units=("Quantity", "sum"),
    transactions=("Product", "count")).sort_index()
print("Monthly performance (revenue / units / transactions):")
for m, r in monthly.iterrows():
    rev = r["revenue"]
    units = r["units"]
    txns = r["transactions"]
    print("  " + str(m) + ": ₱" + format(rev, ">12,.0f") + " | " + format(units, ">6,") + " units | " + format(txns, ">4") + " txns")
best_rev_month = monthly["revenue"].idxmax()
best_units_month = monthly["units"].idxmax()
print("  Best revenue month: " + str(best_rev_month) + " (₱" + format(monthly["revenue"].max(), ",.0f") + ")")
print("  Best units month: " + str(best_units_month) + " (" + str(monthly["units"].max()) + " units)")
print()
client_type = merged.groupby("Client Type").agg(
    revenue=("Total", "sum"), units=("Quantity", "sum")).sort_values("revenue", ascending=False)
print("By client type:")
for ct, r in client_type.iterrows():
    rev = r["revenue"]
    units = r["units"]
    print("  " + ct + ": ₱" + format(rev, ">12,.0f") + " | " + format(units, ">6,") + " units")
payment = merged.groupby("Payment")["Total"].sum().sort_values(ascending=False)
print("By payment method:")
for pm, rev in payment.items():
    print("  " + pm + ": ₱" + format(rev, ">12,.0f"))
print()

# 5. SECTION 3: SALES BY PRODUCT CATEGORY
print("-" * 60)
cat = merged.groupby("Product Category").agg(
    models=("Product Name", "nunique"),
    units=("Quantity", "sum"),
    revenue=("Total", "sum"),
    transactions=("Product", "count"))
cat["revenue_share"] = cat["revenue"] / total_revenue * 100
cat["units_share"] = cat["units"] / total_units * 100
cat["revenue_per_model"] = cat["revenue"] / cat["models"]
cat["units_per_model"] = cat["units"] / cat["models"]
cat["avg_selling_price"] = cat["revenue"] / cat["units"]
cat = cat.sort_values("revenue", ascending=False)
print("{:<14} {:>6} {:>7} {:>14} {:>7} {:>11}".format("Category", "Models", "Units", "Revenue", "Share", "Rev/Model"))
for c, r in cat.iterrows():
    print("{:<14} {:>6} {:>7,} ₱{:>12,.0f} {:>6.1f}% ₱{:>10,.0f}".format(
        c, r["models"], r["units"], r["revenue"], r["revenue_share"], r["revenue_per_model"]))
print("TOTAL                         " + str(total_products).rjust(6) + " " + str(total_units).rjust(7) + ", " + " ₱" + format(total_revenue, ">12,.0f") + " 100.0%")
print()
# 6. HERITAGE DEEP-DIVE
print("SECTION 3B: HERITAGE DEEP-DIVE (trace + normalization)")
print("-" * 60)
heritage_products = products[products["Product Category"] == "Heritage"]["Product Name"].tolist()
print("Heritage products: " + str(heritage_products))
h_sales = merged[merged["Product Category"] == "Heritage"]
h_trace = h_sales.groupby("Product").agg(
    units=("Quantity", "sum"), revenue=("Total", "sum"),
    transactions=("Product", "count"))
print(h_trace)
h_rev = h_sales["Total"].sum()
h_units = h_sales["Quantity"].sum()
h_models = len(heritage_products)
print("Heritage total revenue: ₱" + format(h_rev, ",.0f"))
print("Heritage total units: " + format(h_units, ","))
print("Heritage models: " + str(h_models))
print("Heritage revenue per model: ₱" + format(h_rev / h_models, ",.0f"))
print("Heritage units per model: " + format(h_units / h_models, ",.1f"))

rpm_rank = cat["revenue_per_model"].rank(ascending=False)
upm_rank = cat["units_per_model"].rank(ascending=False)
print()
print("Heritage rank by revenue per model: " + str(int(rpm_rank["Heritage"])) + " of " + str(len(cat)))
print("Heritage rank by units per model: " + str(int(upm_rank["Heritage"])) + " of " + str(len(cat)))
print("Heritage rank by total revenue: " + str(int(cat["revenue"].rank(ascending=False)["Heritage"])) + " of " + str(len(cat)))
print("Heritage rank by total units: " + str(int(cat["units"].rank(ascending=False)["Heritage"])) + " of " + str(len(cat)))
print()
print("Interpretation: Heritage stays top-tier after normalizing by model count,")
print("so the insight is driven by high unit price + steady demand.")
print()

# 7. SECTION 4: INVENTORY VIEW
print("-" * 60)
inv = products.groupby("Product Category").agg(
    models=("Product Name", "nunique"),
    min_price=("Unit Price", "min"),
    max_price=("Unit Price", "max"),
    avg_price=("Unit Price", "mean"),
    total_list_value=("Unit Price", "sum")).sort_values("models", ascending=False)
inv = inv.round(0)

print("{:<14} {:>6} {:>11} {:>11} {:>11} {:>13}".format("Category", "Models", "Min Price", "Max Price", "Avg Price", "List Value"))
for c, r in inv.iterrows():
    print("{:<14} {:>6} ₱{:>10,.0f} ₱{:>10,.0f} ₱{:>10,.0f} ₱{:>12,.0f}".format(
        c, r["models"], r["min_price"], r["max_price"], r["avg_price"], r["total_list_value"]))
print()
print("Total list value of all 50 models: ₱" + format(products["Unit Price"].sum(), ",.0f"))
print()

# 8. BUILD DASHBOARD FIGURE
print("Building dashboard figure...")
plt.rcParams["font.size"] = 9
fig = plt.figure(figsize=(16, 12))
gs = GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.35)

def section_title(ax, text):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=13,
            fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.5", fc="#1f77b4", ec="none"))

# Section 1: Overview metrics panel
ax1 = fig.add_subplot(gs[0, 0])
section_title(ax1, "MOTORPH OVERVIEW")
metric_lines = []
for k, v in [("Total Products", str(total_products)),
             ("Product Categories", str(total_categories)),
             ("Total Units Sold", str(total_units)),
             ("Total Revenue", "₱" + format(total_revenue, ",.0f")),
             ("Transactions", str(n_txns)),
             ("Avg Order Value", "₱" + format(avg_order_value, ",.0f")),
             ("Sales Period", date_min + " - " + date_max),
             ("Top Category (Rev)", top_rev_cat),
             ("Top Category (Units)", top_units_cat)]:
    metric_lines.append(k + ": " + v)
ax1.text(0.05, 0.92, "\n".join(metric_lines), transform=ax1.transAxes,
         fontsize=11, va="top", family="monospace")
ax1.axis("off")
# Section 2: Monthly revenue trend
ax2 = fig.add_subplot(gs[0, 1:])
months_str = [str(m) for m in monthly.index]
ax2.plot(range(len(monthly)), monthly["revenue"] / 1e6, marker="o", linewidth=2, color="#1f77b4")
ax2.set_xticks(range(len(monthly)))
ax2.set_xticklabels(months_str, rotation=45, ha="right")
ax2.set_ylabel("Revenue (million ₱)")
ax2.set_title("Monthly Revenue Trend (Sales Performance)")
ax2.grid(True, alpha=0.3)
for i, v in enumerate(monthly["revenue"] / 1e6):
    ax2.annotate(format(v, ",.0f") + "M", (i, v), textcoords="offset points", xytext=(0, 6),
                 ha="center", fontsize=7)

# Section 3a: Revenue by category
ax3 = fig.add_subplot(gs[1, 0])
cats_r = cat.sort_values("revenue", ascending=True)
ax3.barh(cats_r.index, cats_r["revenue"] / 1e6, color="#2ca02c")
ax3.set_xlabel("Revenue (million ₱)")
ax3.set_title("Revenue by Product Category")
for i, v in enumerate(cats_r["revenue"] / 1e6):
    ax3.annotate(format(v, ",.0f") + "M", (v, i), textcoords="offset points", xytext=(4, 0),
                 va="center", fontsize=7)

# Section 3b: Units by category
ax3b = fig.add_subplot(gs[1, 1])
cats_u = cat.sort_values("units", ascending=True)
ax3b.barh(cats_u.index, cats_u["units"], color="#17becf")
ax3b.set_xlabel("Units Sold")
ax3b.set_title("Units Sold by Product Category")
for i, v in enumerate(cats_u["units"]):
    ax3b.annotate(format(v, ","), (v, i), textcoords="offset points", xytext=(4, 0),
                  va="center", fontsize=7)

# Section 4a: Inventory models per category
ax4 = fig.add_subplot(gs[1, 2])
inv_s = inv.sort_values("models", ascending=True)
ax4.barh(inv_s.index, inv_s["models"], color="#d62728")
ax4.set_xlabel("Number of Models")
ax4.set_title("Inventory: Models per Category")
for i, v in enumerate(inv_s["models"]):
    ax4.annotate(str(v), (v, i), textcoords="offset points", xytext=(4, 0),
                 va="center", fontsize=8)

# Section 4b: Avg selling price by category
ax4b = fig.add_subplot(gs[2, 0])
cats_a = cat.sort_values("avg_selling_price", ascending=True)
ax4b.barh(cats_a.index, cats_a["avg_selling_price"] / 1000, color="#9467bd")
ax4b.set_xlabel("Avg Selling Price (thousand ₱)")
ax4b.set_title("Avg Selling Price by Category")
for i, v in enumerate(cats_a["avg_selling_price"] / 1000):
    ax4b.annotate(format(v, ",.0f") + "K", (v, i), textcoords="offset points", xytext=(4, 0),
                  va="center", fontsize=7)

# Insights panel
ax5 = fig.add_subplot(gs[2, 1:])
ax5.set_xlim(0, 1)
ax5.set_ylim(0, 1)
ax5.axis("off")
scooter_units = merged[merged["Product Category"] == "Scooter"]["Quantity"].sum()
insights = ("KEY INSIGHTS\n"
            "------------\n"
            "1. Scooter leads on count (" + str(total_categories) + " categories, 12 models) and units (" + format(scooter_units, ",") + ").\n"
            "2. Cruiser vs Sport: same model count (4), similar units, but Cruiser earns ₱" + format(cat.loc["Cruiser", "revenue"], ",.0f") + " vs Sport ₱" + format(cat.loc["Sport", "revenue"], ",.0f") + ".\n"
            "3. Heritage: " + format(h_units, ",") + " units but ₱" + format(h_rev, ",.0f") + " revenue - 4th in revenue from only " + str(h_models) + " models (₱" + format(h_rev / h_models, ",.0f") + "/model).\n"
            "4. Commuter: " + format(cat.loc["Commuter", "units"], ",") + " units but only ₱" + format(cat.loc["Commuter", "revenue"], ",.0f") + " - volume does not equal revenue.\n"
            "5. Restock by units + revenue, not model count.")
ax5.text(0.02, 0.98, insights, transform=ax5.transAxes, fontsize=10,
         va="top", family="monospace",
         bbox=dict(boxstyle="round,pad=0.5", fc="#f0f0f0", ec="#888888"))

fig.suptitle("MotorPH MS2 Dashboard - Overview \u2022 Sales Performance \u2022 Sales by Category \u2022 Inventory",
             fontsize=15, fontweight="bold", y=0.985)

OUT_PNG = "MotorPH_MS2_Dashboard.png"
fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
print("Saved dashboard: " + OUT_PNG)
print()
print("DEPENDENCIES: pandas, matplotlib (standard Milestone 1 stack).")
print("No new packages required. Re-run: python3 MotorPH_MS2_Dashboard.py")
print("=" * 60)
plt.show()
